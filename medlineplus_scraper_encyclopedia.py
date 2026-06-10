#!/usr/bin/env python3
"""
MedlinePlus Medical Encyclopedia Scraper
=========================================
Production-grade async Playwright scraper.

Features
--------
• 3 parallel browser tabs — staggered alphabet assignment
    Worker 1 → A, D, G, J, …
    Worker 2 → B, E, H, K, …
    Worker 3 → C, F, I, L, …
• Dynamic section extraction (no hard-coded keys)
• Checkpoint every 25 articles (per worker) → checkpoint.json
• Exponential-backoff retries  (3 attempts max)
• Blocks images / fonts / analytics for speed
• Graceful SIGINT / SIGTERM shutdown (finishes current article)
• Resume: skips already-completed URLs on restart

Output files
------------
articles.jsonl   — one JSON document per line
checkpoint.json  — progress + failed URLs
errors.json      — per-article failure log
scraper.log      — full debug log

Usage
-----
    pip install playwright
    playwright install chromium
    python medlineplus_scraper.py
"""

import asyncio
import json
import logging
import re
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import async_playwright, BrowserContext, Page

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

BASE_URL         = "https://medlineplus.gov/ency/"
ALPHABETS        = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["0-9"]

NUM_WORKERS      = 3
CHECKPOINT_EVERY = 25       # Checkpoint per worker after this many articles
MAX_RETRIES      = 3
BACKOFF_BASE     = 2.0      # seconds; delay = BACKOFF_BASE ** attempt
POLITE_DELAY     = 0.30     # seconds between consecutive article requests

OUTPUT_FILE      = Path("articles.jsonl")
CHECKPOINT_FILE  = Path("checkpoint.json")
ERRORS_FILE      = Path("errors.json")
LOG_FILE         = Path("scraper.log")

# Resource types to block (bandwidth + speed)
BLOCKED_RES_TYPES = {"image", "media", "font", "stylesheet"}

# Third-party domains to block
BLOCKED_URL_PARTS = [
    "google-analytics", "googletagmanager", "doubleclick",
    "facebook.net", "twitter.com", "pinterest.com",
    "addthis.com", "hotjar.com",
]

# ═══════════════════════════════════════════════════════════════════════════════
# Logging
# ═══════════════════════════════════════════════════════════════════════════════

def _make_logger() -> logging.Logger:
    fmt = "%(asctime)s [%(levelname)-8s] %(message)s"
    logger = logging.getLogger("mplus")
    logger.setLevel(logging.DEBUG)

    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(logging.Formatter(fmt, "%H:%M:%S"))

    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(fmt))

    logger.addHandler(sh)
    logger.addHandler(fh)
    return logger

log = _make_logger()

# ═══════════════════════════════════════════════════════════════════════════════
# Shared async state  (single event loop — cooperative, no real concurrency)
# ═══════════════════════════════════════════════════════════════════════════════

_write_lock      = asyncio.Lock()
_checkpoint_lock = asyncio.Lock()
_errors_lock     = asyncio.Lock()
_shutdown        = False   # Flipped to True on SIGINT / SIGTERM

# ═══════════════════════════════════════════════════════════════════════════════
# I / O helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _load_checkpoint_sync() -> dict:
    """Read checkpoint from disk (called once before async loop starts)."""
    if CHECKPOINT_FILE.exists():
        try:
            cp = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
            log.info(
                f"Checkpoint loaded: {len(cp.get('completed_articles', []))} done, "
                f"{len(cp.get('failed_articles', []))} failed"
            )
            return cp
        except Exception as exc:
            log.warning(f"Corrupt checkpoint — starting fresh: {exc}")
    return {"completed_articles": [], "failed_articles": [], "last_saved": ""}


async def _save_checkpoint(cp: dict) -> None:
    """Write checkpoint to disk, guarded by lock."""
    async with _checkpoint_lock:
        cp["last_saved"] = datetime.now().isoformat()
        CHECKPOINT_FILE.write_text(
            json.dumps(cp, indent=2, ensure_ascii=False), encoding="utf-8"
        )


async def _write_article(article: dict) -> None:
    """Append one article JSON line to the output file."""
    async with _write_lock:
        with OUTPUT_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(article, ensure_ascii=False) + "\n")


async def _log_error(entry: dict) -> None:
    """Append an error entry to errors.json."""
    async with _errors_lock:
        errs: list = []
        if ERRORS_FILE.exists():
            try:
                errs = json.loads(ERRORS_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        errs.append(entry)
        ERRORS_FILE.write_text(
            json.dumps(errs, indent=2, ensure_ascii=False), encoding="utf-8"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# URL utilities
# ═══════════════════════════════════════════════════════════════════════════════

def alpha_index_url(alpha: str) -> str:
    """Return the full URL for a given alphabet index page."""
    return f"{BASE_URL}encyclopedia_{alpha}.htm"


def resolve_href(href: str) -> str:
    """
    Convert a relative href (from the index page) to an absolute URL.

    Examples
    --------
    'article/003640.htm'           → 'https://medlineplus.gov/ency/article/003640.htm'
    'patientinstructions/000823.htm' → 'https://medlineplus.gov/ency/patientinstructions/...'
    '/ency/article/003640.htm'     → 'https://medlineplus.gov/ency/article/003640.htm'
    """
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return "https://medlineplus.gov" + href
    # Strip leading './' or '../' combinations
    return BASE_URL + href.lstrip("./")


def extract_article_id(url: str) -> str:
    """Extract the numeric / alphanumeric ID from the article URL."""
    m = re.search(r"/(\w[\w-]*)\.htm", url)
    return m.group(1) if m else ""


def infer_article_type(url: str) -> str:
    if "/article/" in url:
        return "article"
    if "/patientinstructions/" in url:
        return "patient_instructions"
    return "other"


# ═══════════════════════════════════════════════════════════════════════════════
# Work distribution
# ═══════════════════════════════════════════════════════════════════════════════

def distribute_alphabets(alphabets: List[str], n_workers: int) -> List[List[str]]:
    """
    Staggered round-robin:
      Worker 0 → index 0, 3, 6, … → A, D, G, J, …
      Worker 1 → index 1, 4, 7, … → B, E, H, K, …
      Worker 2 → index 2, 5, 8, … → C, F, I, L, …
    """
    buckets: List[List[str]] = [[] for _ in range(n_workers)]
    for idx, alpha in enumerate(alphabets):
        buckets[idx % n_workers].append(alpha)
    return buckets


# ═══════════════════════════════════════════════════════════════════════════════
# Browser page factory
# ═══════════════════════════════════════════════════════════════════════════════

async def make_page(ctx: BrowserContext) -> Page:
    """
    Create a new page and attach an aggressive resource-blocking route.
    Blocks images, media, fonts, stylesheets, and known analytics domains
    to reduce bandwidth and improve speed.
    """
    page = await ctx.new_page()

    async def route_handler(route, request):
        rtype = request.resource_type
        rurl  = request.url
        if rtype in BLOCKED_RES_TYPES or any(p in rurl for p in BLOCKED_URL_PARTS):
            await route.abort()
        else:
            await route.continue_()

    await page.route("**/*", route_handler)
    return page


# ═══════════════════════════════════════════════════════════════════════════════
# JavaScript payloads  (evaluated inside the browser context)
# ═══════════════════════════════════════════════════════════════════════════════

# Extracts all <a> links from the #index <ul> on an alphabet page.
_JS_INDEX = """
() => Array.from(document.querySelectorAll('#index li a')).map(a => ({
    href : a.getAttribute('href') || '',
    title: a.textContent.trim()
}))
"""

# Extracts the full article data from a single article page.
# Returns: { title, summary, sections, images, related_topics }
#
# Ignored sections (per spec):
#   • References
#   • Review Date …
#   • Learn how to cite
#
# Special-cased sections:
#   • Images          → list of { src, alt, href, caption }
#   • Related MedlinePlus Health Topics → captured in related_topics, NOT sections
#
# Sidebar (.side-section) is IGNORED except for the Images side-section.
_JS_ARTICLE = r"""
() => {
    /* ── helpers ──────────────────────────────────────────────────────────── */

    function toAbsImg(src) {
        if (!src) return '';
        if (src.startsWith('//')) return 'https:' + src;
        return src;
    }

    /**
     * Extract structured image data from a container element that holds
     * an <ul class="img-grid"> or similar list of thumbnail images.
     */
    function extractImages(container) {
        const out = [];
        container.querySelectorAll('li').forEach(li => {
            const img = li.querySelector('img');
            const a   = li.querySelector('a');
            if (!img || !a) return;
            out.push({
                src    : toAbsImg(img.getAttribute('src')),
                alt    : img.getAttribute('alt') || '',
                href   : a.getAttribute('href') || '',
                caption: a.textContent.trim()
            });
        });
        return out;
    }

    /**
     * Parse a generic section body into a structured object.
     * Always includes `text` (full inner text).
     * Also includes `paragraphs` and `items` when present.
     */
    function parseSectionBody(body) {
        const text  = body.innerText.trim();
        const paras = Array.from(body.querySelectorAll('p'))
                          .map(p => p.innerText.trim()).filter(Boolean);
        const items = Array.from(body.querySelectorAll('li'))
                          .map(li => li.innerText.trim()).filter(Boolean);

        const result = { text };
        if (paras.length) result.paragraphs = paras;
        if (items.length) result.items      = items;
        return result;
    }

    /* ── title ──────────────────────────────────────────────────────────────── */
    const h1El = document.querySelector('h1[itemprop="name"], h1.with-also, h1');
    const title = h1El ? h1El.textContent.trim() : '';

    /* ── summary ──────────────────────────────────────────────────────────── */
    const sumEl   = document.querySelector('#ency_summary');
    const summary = sumEl ? sumEl.innerText.trim() : '';

    /* ── sections from div.main ───────────────────────────────────────────── */
    const sections      = {};   // { sectionTitle → content }
    let   imagesList    = [];
    let   relatedTopics = [];

    const mainDiv = document.querySelector('div.main');
    if (mainDiv) {
        Array.from(mainDiv.children).forEach(child => {
            if (child.tagName !== 'SECTION') return;

            const h2El = child.querySelector('.section-title h2');
            if (!h2El) return;
            const rawTitle = h2El.textContent.trim();

            /* ── skip unwanted sections ────────────────────────────────────── */
            if (/^References$/i.test(rawTitle))       return;
            if (/^Review Date/i.test(rawTitle))       return;
            if (/Learn how to cite/i.test(rawTitle))  return;
            if (/^Citation$/i.test(rawTitle))         return;

            const body = child.querySelector('.section-body');
            if (!body) return;

            /* ── images section ──────────────────────────────────────────── */
            if (/^Images$/i.test(rawTitle)) {
                imagesList = extractImages(body);
                sections[rawTitle] = imagesList;
                return;
            }

            /* ── related health topics section ─────────────────────────── */
            if (/Related MedlinePlus/i.test(rawTitle)) {
                relatedTopics = Array.from(body.querySelectorAll('a')).map(a => ({
                    url  : a.getAttribute('href') || '',
                    title: a.textContent.trim()
                }));
                /* Captured in related_topics field — not added to sections */
                return;
            }

            /* ── generic section ────────────────────────────────────────── */
            sections[rawTitle] = parseSectionBody(body);
        });
    }

    /* ── sidebar: only keep Images side-section (per spec) ─────────────── */
    const sideAside = document.querySelector('div.side aside');
    if (sideAside) {
        sideAside.querySelectorAll('.side-section').forEach(ss => {
            const h2 = ss.querySelector('.section-header h2');
            if (h2 && /^Images$/i.test(h2.textContent.trim())) {
                extractImages(ss).forEach(img => {
                    /* De-duplicate by src */
                    if (!imagesList.some(i => i.src === img.src)) {
                        imagesList.push(img);
                    }
                });
            }
        });
    }

    return {
        title,
        summary,
        sections,
        images        : imagesList,
        related_topics: relatedTopics
    };
}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# Page-level scraping functions (with retry + exponential backoff)
# ═══════════════════════════════════════════════════════════════════════════════

async def fetch_links(page: Page, alpha: str) -> List[Dict[str, str]]:
    """
    Navigate to the alphabet index page and return a list of article dicts:
      { url, title, alpha }
    Retries up to MAX_RETRIES with exponential backoff.
    """
    url = alpha_index_url(alpha)
    last_exc: Optional[Exception] = None

    for attempt in range(MAX_RETRIES):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_selector("#index", timeout=15_000)

            raw: list = await page.evaluate(_JS_INDEX)
            links = [
                {
                    "url"  : resolve_href(r["href"]),
                    "title": r["title"],
                    "alpha": alpha,
                }
                for r in raw
                if r.get("href")
            ]
            log.info(f"[{alpha}] {len(links)} articles found")
            return links

        except Exception as exc:
            last_exc = exc
            delay = BACKOFF_BASE ** attempt
            log.warning(
                f"[{alpha}] link-fetch attempt {attempt + 1}/{MAX_RETRIES} failed: "
                f"{exc} — retry in {delay:.0f}s"
            )
            await asyncio.sleep(delay)

    log.error(f"[{alpha}] Giving up on link-fetch after {MAX_RETRIES} attempts: {last_exc}")
    return []


async def fetch_article(page: Page, url: str) -> Optional[Dict[str, Any]]:
    """
    Navigate to a single article page and extract structured data.
    Returns a dict on success, None after MAX_RETRIES failures.
    """
    last_exc: Optional[Exception] = None

    for attempt in range(MAX_RETRIES):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_selector("#d-article, article", timeout=15_000)

            data: dict = await page.evaluate(_JS_ARTICLE)
            return data

        except Exception as exc:
            last_exc = exc
            delay = BACKOFF_BASE ** attempt
            log.warning(
                f"  Article attempt {attempt + 1}/{MAX_RETRIES} failed ({url}): "
                f"{exc} — retry in {delay:.0f}s"
            )
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(delay)

    log.error(f"  Giving up on article after {MAX_RETRIES} attempts: {url} — {last_exc}")
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Worker coroutine
# ═══════════════════════════════════════════════════════════════════════════════

async def worker(
    wid     : int,
    alphas  : List[str],
    ctx     : BrowserContext,
    cp      : dict,
    done_set: set,
) -> None:
    """
    Processes a subset of alphabets assigned by the staggered distribution.
    Each worker owns a single reused Playwright page.

    On completion / error / shutdown the checkpoint is always flushed to disk.
    """
    global _shutdown

    page       = await make_page(ctx)
    since_ckpt = 0   # Articles processed since last checkpoint save

    try:
        for alpha in alphas:
            if _shutdown:
                log.info(f"[W{wid}] Shutdown requested — stopping before {alpha}")
                break

            log.info(f"[W{wid}] ── Processing alphabet: {alpha} ──")
            links = await fetch_links(page, alpha)

            if not links:
                log.warning(f"[W{wid}][{alpha}] No links found — skipping")
                continue

            for lnk in links:
                if _shutdown:
                    break

                url = lnk["url"]

                # ── Resume: skip already-completed URLs ──────────────────────
                if url in done_set:
                    log.debug(f"[W{wid}] skip (done): {url}")
                    continue

                log.info(f"[W{wid}][{alpha}] → {lnk['title']}")

                # ── Scrape article ───────────────────────────────────────────
                data = await fetch_article(page, url)

                if data is not None:
                    article: Dict[str, Any] = {
                        "id"            : extract_article_id(url),
                        "title"         : data.get("title") or lnk["title"],
                        "type"          : infer_article_type(url),
                        "source"        : "MedlinePlus",
                        "source_url"    : url,
                        "alphabet"      : alpha,
                        "summary"       : data.get("summary", ""),
                        "sections"      : data.get("sections", {}),
                        "images"        : data.get("images", []),
                        "related_topics": data.get("related_topics", []),
                        "scraped_at"    : datetime.now().isoformat(),
                    }

                    await _write_article(article)

                    # ── Update shared checkpoint state ───────────────────────
                    async with _checkpoint_lock:
                        cp["completed_articles"].append(url)
                        done_set.add(url)

                    since_ckpt += 1

                    # ── Save checkpoint every CHECKPOINT_EVERY articles ───────
                    if since_ckpt >= CHECKPOINT_EVERY:
                        await _save_checkpoint(cp)
                        since_ckpt = 0
                        log.info(
                            f"[W{wid}] ✓ checkpoint — "
                            f"{len(cp['completed_articles'])} articles total"
                        )

                else:
                    # ── Permanent failure (after all retries) ────────────────
                    log.error(f"[W{wid}] FAILED: {url}")
                    await _log_error({
                        "url"      : url,
                        "title"    : lnk["title"],
                        "alpha"    : alpha,
                        "worker"   : wid,
                        "timestamp": datetime.now().isoformat(),
                    })
                    async with _checkpoint_lock:
                        if url not in cp["failed_articles"]:
                            cp["failed_articles"].append(url)

                # Be polite to the server
                await asyncio.sleep(POLITE_DELAY)

    finally:
        # Always flush on exit — even on shutdown / unhandled exception
        if since_ckpt > 0:
            await _save_checkpoint(cp)
        await page.close()
        log.info(
            f"[W{wid}] finished — "
            f"completed={len(cp['completed_articles'])}, "
            f"failed={len(cp['failed_articles'])}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

async def main() -> None:
    global _shutdown

    log.info("══════════════════════════════════════════════════════")
    log.info("  MedlinePlus Medical Encyclopedia Scraper")
    log.info(f"  Workers : {NUM_WORKERS}  |  Checkpoint every : {CHECKPOINT_EVERY} articles")
    log.info(f"  Retries : {MAX_RETRIES}  |  Backoff base     : {BACKOFF_BASE}s")
    log.info("══════════════════════════════════════════════════════")

    # Load checkpoint (synchronous — before async loop)
    cp       = _load_checkpoint_sync()
    done_set = set(cp["completed_articles"])

    # Distribute alphabets across workers
    buckets = distribute_alphabets(ALPHABETS, NUM_WORKERS)
    for i, b in enumerate(buckets):
        log.info(f"  Worker {i + 1}: {b}")
    log.info("──────────────────────────────────────────────────────")

    # ── Graceful shutdown on SIGINT / SIGTERM ──────────────────────────────
    def _on_signal(*_):
        global _shutdown
        if not _shutdown:
            log.warning("  ⚠  Interrupt received — stopping after current articles …")
            _shutdown = True

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _on_signal)
        except (ValueError, OSError):
            pass  # Not supported on all platforms / threads

    # ── Launch browser ─────────────────────────────────────────────────────
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--blink-settings=imagesEnabled=false",  # Extra: disable images at engine level
            ],
        )

        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/New_York",
            # Don't load images at browser level either
            java_script_enabled=True,
        )

        # Spawn one task per worker
        tasks = [
            asyncio.create_task(
                worker(wid=i + 1, alphas=buckets[i], ctx=ctx, cp=cp, done_set=done_set),
                name=f"worker-{i + 1}",
            )
            for i in range(NUM_WORKERS)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, r in enumerate(results):
            if isinstance(r, Exception):
                log.error(f"Worker {i + 1} raised an unhandled exception: {r!r}")

        await ctx.close()
        await browser.close()

    # ── Final checkpoint flush ─────────────────────────────────────────────
    await _save_checkpoint(cp)

    log.info("══════════════════════════════════════════════════════")
    log.info(f"  Completed : {len(cp['completed_articles'])} articles")
    log.info(f"  Failed    : {len(cp['failed_articles'])} articles")
    log.info(f"  Output    : {OUTPUT_FILE}")
    log.info(f"  Checkpoint: {CHECKPOINT_FILE}")
    log.info(f"  Errors    : {ERRORS_FILE}")
    log.info("══════════════════════════════════════════════════════")


if __name__ == "__main__":
    asyncio.run(main())
