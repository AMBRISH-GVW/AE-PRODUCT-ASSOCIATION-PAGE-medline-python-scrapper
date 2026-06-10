# TASK: Build Production-Grade MedlinePlus Encyclopedia Scraper

## Task Overview
Build a Python + Playwright (async) web scraper that:
1. Scrap parallely in 3 different windows
2. For each alphabet, searches a website
3. Iterates through every search result, opens each one's detail page, scrapes structured data from multiple tabs, then navigates back
4. Writes all collected data to a json file with checkpointing and error recovery

---

## Tech Stack
- **Language:** Python 3.10+
- **Browser automation:** `playwright` (async API), Chromium already installed
- **Output:** json
- No other third-party libraries

---
## Concurrency Requirements

### Overview
- Run **3 browser tabs/pages in parallel**
- Process **alphabet pages concurrently**

### Work Distribution

Each worker processes a subset of pages in a staggered pattern:

- **Worker 1**  
  A, D, G, J, ...

- **Worker 2**  
  B, E, H, K, ...

- **Worker 3**  
  C, F, I, L, ...

### Notes
- Ensures balanced workload distribution
- Maximizes parallel processing efficiency
- Reduces total execution time

## Website

the websites will be from A TO Z and '0-9'
**URL:**

https://medlineplus.gov/ency/encyclopedia_A.htm
https://medlineplus.gov/ency/encyclopedia_B.htm
https://medlineplus.gov/ency/encyclopedia_C.htm
till
https://medlineplus.gov/ency/encyclopedia_Z.htm
and 
https://medlineplus.gov/ency/encyclopedia_0-9.htm


---

## Step-by-Step Scraping Flow

this is how it will be when you go to the page https://medlineplus.gov/ency/encyclopedia_A.htm



```html

      </nav><div class="page-info"><div class="page-title"><a name="start" id="start">
    </a><h1 class="with-also">Medical Encyclopedia: A</h1>
    </div><div class="page-actions"><div class="share-buttons" style=""><span><a target="EmailWin" class="email_icon" title="Email this page to a friend" href="mailto:?subject=Medical%20Encyclopedia%3A%20A%3A%20MedlinePlusLock&amp;body=I%20found%20this%20information%20on%20MedlinePlus.gov%20and%20I'd%20like%20to%20share%20it%20with%20you%3A%0A%0Ahttps%3A%2F%2Fmedlineplus.gov%2Fency%2Fencyclopedia_A.htm%3Futm_source%3Demail%26utm_medium%3Dshare%26utm_campaign%3Dmplus_share%0A%0AMedlinePlus%20(https%3A%2F%2Fmedlineplus.gov)%3A%20Trusted%20Health%20Information%20for%20you%0A%0ATo%20get%20updates%20by%20email%20when%20new%20information%20becomes%20available%20on%20MedlinePlus%2C%20sign%20up%20at%20https%3A%2F%2Fmedlineplus.gov%2Flistserv.html."><img alt="Email this page to a friend" class="share-icon" src="//medlineplus.gov/images/i_share_email.png"></a></span> <span><a class="share-facebook" title="Facebook" href="#"><img alt="Facebook" class="share-icon" src="//medlineplus.gov/images/i_share_fb.png"></a></span> <span><a class="share-twitter" title="X" href="#"><img alt="X" class="share-icon" src="//medlineplus.gov/images/i_share_twitter.png"></a></span> <span><a class="share-pinterest" title="Pinterest" href="#"><img alt="Pinterest" class="share-icon" src="//medlineplus.gov/images/i_share_pinterest.png"></a></span> </div></div>
    <noscript>
          <span class="js-disabled-message">To use the sharing features on this page, please enable JavaScript.</span>
          </noscript></div><ul id="index"><li class="g-m"><a href="patientinstructions/000823.htm">A guide to clinical trials for cancer</a></li><li><a href="patientinstructions/000921.htm">A guide to help children understand cancer </a></li><li class="g-m"><a href="patientinstructions/000868.htm">A guide to herbal remedies</a></li><li><a href="article/003640.htm">A1C test</a></li><li class="break g-5 g-m"><a href="article/001654.htm">Aarskog syndrome</a></li><li><a href="article/001662.htm">Aase syndrome</a></li><li class="g-m"><a href="article/003122.htm">Abdomen - swollen</a></li><li><a href="article/000162.htm">Abdominal aortic aneurysm</a></li><li class="g-m"><a href="article/007392.htm">Abdominal aortic aneurysm repair - open</a></li><li class="break g-5"><a href="patientinstructions/000240.htm">Abdominal aortic aneurysm repair - open - discharge </a></li><li class="g-m"><a href="article/003123.htm">Abdominal bloating</a></li><li><a href="article/003789.htm">Abdominal CT scan</a></li><li class="g-m"><a href="article/002928.htm">Abdominal exploration</a></li><li><a href="article/003938.htm">Abdominal girth</a></li><li class="break g-5 g-m"><a href="article/003274.htm">Abdominal mass</a></li><li><a href="article/003796.htm">Abdominal MRI scan</a></li><li class="g-m"><a href="article/003120.htm">Abdominal pain</a></li><li><a href="article/007504.htm">Abdominal pain - children under age 12</a></li><li class="g-m"><a href="patientinstructions/000054.htm">Abdominal radiation - discharge</a></li><li class="break g-5"><a href="article/003136.htm">Abdominal rigidity</a></li><li class="g-m"><a href="article/003137.htm">Abdominal sounds</a></li><li><a href="article/003896.htm">Abdominal tap </a></li><li class="g-m"><a href="article/000047.htm">Abdominal thrusts</a></li><li><a href="article/003777.htm">Abdominal ultrasound</a></li><li class="break g-5 g-m"><a href="article/003841.htm">Abdominal wall fat pad biopsy</a></li><li><a href="article/002978.htm">Abdominal wall surgery</a></li>
          
          
          # it will be going till last term
          
          
          <li><a href="article/002218.htm">Autoinoculation</a></li><li class="g-m"><a href="article/002729.htm">Automatic dishwasher soap poisoning</a></li><li class="break g-5"><a href="article/001431.htm">Autonomic dysreflexia</a></li><li class="g-m"><a href="article/000776.htm">Autonomic neuropathy</a></li><li><a href="article/002049.htm">Autosomal dominant</a></li><li class="g-m"><a href="article/000465.htm">Autosomal dominant tubulointerstitial kidney disease</a></li><li><a href="article/002052.htm">Autosomal recessive</a></li><li class="break g-5 g-m"><a href="article/007263.htm">Avian influenza</a></li><li><a href="article/000940.htm">Avoidant personality disorder</a></li><li class="g-m"><a href="article/000689.htm">Axillary nerve dysfunction</a></li></ul><div class="side"><aside></aside></div></div></article>
```


what you need to do is that, you need to open each of the article link in new tab, and scrap all the data to be mentioned below in json format and return back here to the main url for eg: https://medlineplus.gov/ency/encyclopedia_A.htm and then continue with the next
all these to be noted first the number of articles first and checkpointed throughout the process
---

### Step 2 — what will be in the article page?

for eg, https://medlineplus.gov/ency/article/003122.htm

this page  will contain
```html
<article><div id="d-article"><div class="page-info"><div class="page-title"><a name="start" id="start">
    </a><h1 class="with-also" itemprop="name">Abdomen - swollen</h1>
        </div><div class="page-actions"><div class="share-buttons" style=""><span><a target="EmailWin" class="email_icon" title="Email this page to a friend" href="mailto:?subject=Abdomen%20-%20swollen%3A%20MedlinePlus%20Medical%20EncyclopediaLock&amp;body=I%20found%20this%20information%20on%20MedlinePlus.gov%20and%20I'd%20like%20to%20share%20it%20with%20you%3A%0A%0Ahttps%3A%2F%2Fmedlineplus.gov%2Fency%2Farticle%2F003122.htm%3Futm_source%3Demail%26utm_medium%3Dshare%26utm_campaign%3Dmplus_share%0A%0AMedlinePlus%20(https%3A%2F%2Fmedlineplus.gov)%3A%20Trusted%20Health%20Information%20for%20you%0A%0ATo%20get%20updates%20by%20email%20when%20new%20information%20becomes%20available%20on%20MedlinePlus%2C%20sign%20up%20at%20https%3A%2F%2Fmedlineplus.gov%2Flistserv.html."><img alt="Email this page to a friend" class="share-icon" src="//medlineplus.gov/images/i_share_email.png"></a></span> <span><a class="mplus_print" title="Print" href="#"><img alt="Print" class="share-icon" src="//medlineplus.gov/images/i_share_print.png"></a></span> <span><a class="share-facebook" title="Facebook" href="#"><img alt="Facebook" class="share-icon" src="//medlineplus.gov/images/i_share_fb.png"></a></span> <span><a class="share-twitter" title="X" href="#"><img alt="X" class="share-icon" src="//medlineplus.gov/images/i_share_twitter.png"></a></span> <span><a class="share-pinterest" title="Pinterest" href="#"><img alt="Pinterest" class="share-icon" src="//medlineplus.gov/images/i_share_pinterest.png"></a></span> </div></div>
        <noscript>
          <span class="js-disabled-message">To use the sharing features on this page, please enable JavaScript.</span>
          </noscript></div><div class="main"><div id="ency_summary"><p>A swollen abdomen is when your belly area is bigger than usual.</p></div><section><div class="section"><div class="section-header"><div class="section-title"><h2>Causes</h2></div><div class="section-button"><button type="submit" aria-controls="section-1" role="button" title="Expand Section" aria-pressed="false" tabindex="0"><span class="icon icon-section-action">
                  </span><span class="hide-offscreen">Expand Section</span></button></div><div class="sm-live-area hide-offscreen" aria-live="polite">
              </div></div><div class="section-body" id="section-1"><p>Abdominal swelling, or distention, is more often caused by overeating than by a serious illness. This problem also can be caused by:</p><ul><li>Air swallowing (a nervous habit)</li><li>Buildup of fluid in the abdomen (this can be a sign of a serious medical problem)</li><li>Gas in the intestines from eating foods that are high in fiber (such as fruits and vegetables)</li><li><a test="test" href="./000246.htm">Irritable bowel syndrome</a></li><li><a test="test" href="./000276.htm">Lactose intolerance</a></li><li><a test="test" href="./001504.htm">Ovarian cyst or cancer</a></li><li>Partial <a test="test" href="./000260.htm">bowel blockage</a></li><li>Pregnancy</li><li><a test="test" href="./001505.htm">Premenstrual syndrome</a> (PMS)</li><li><a test="test" href="./000914.htm">Uterine fibroids</a></li><li><a test="test" href="./003084.htm">Weight gain</a></li></ul></div></div></section><section><div class="section"><div class="section-header"><div class="section-title"><h2>Home Care</h2></div><div class="section-button"><button type="submit" aria-controls="section-2" role="button" title="Expand Section" aria-pressed="false" tabindex="0"><span class="icon icon-section-action">
                  </span><span class="hide-offscreen">Expand Section</span></button></div><div class="sm-live-area hide-offscreen" aria-live="polite">
              </div></div><div class="section-body" id="section-2"><p>A swollen abdomen that is caused by eating a heavy meal will go away when you digest the food. Eating smaller amounts will help prevent swelling.</p><p>For a swollen abdomen caused by swallowing air:</p><ul><li>Avoid carbonated beverages.</li><li>Avoid chewing gum or sucking on candies.</li><li>Avoid drinking through a straw or sipping the surface of a hot beverage.</li><li>Eat slowly. </li></ul><p>For a swollen abdomen caused by <a test="test" href="./000299.htm">malabsorption</a>, try changing your diet and limiting milk. Talk to your health care provider.</p><p>For irritable bowel syndrome:</p><ul><li>Decrease emotional <a test="test" href="./003211.htm">stress</a>.</li><li>Increase dietary <a test="test" href="./002470.htm">fiber</a>.</li><li>Talk to your provider.</li></ul><p>For a swollen abdomen due to other causes, follow the treatment prescribed by your provider.</p></div></div></section><section><div class="section"><div class="section-header"><div class="section-title"><h2>When to Contact a Medical Professional</h2></div><div class="section-button"><button type="submit" aria-controls="section-3" role="button" title="Expand Section" aria-pressed="false" tabindex="0"><span class="icon icon-section-action">
                  </span><span class="hide-offscreen">Expand Section</span></button></div><div class="sm-live-area hide-offscreen" aria-live="polite">
              </div></div><div class="section-body" id="section-3"><p>Contact your provider if:</p><ul><li>The abdominal swelling is getting worse and does not go away.</li><li>The swelling occurs with other unexplained symptoms.</li><li>Your abdomen is tender to the touch.</li><li>You have a high fever.</li><li>You have severe diarrhea or bloody stools.</li><li>You are unable to eat or drink for more than 6 to 8 hours. </li></ul></div></div></section><section><div class="section"><div class="section-header"><div class="section-title"><h2>What to Expect at Your Office Visit</h2></div><div class="section-button"><button type="submit" aria-controls="section-4" role="button" title="Expand Section" aria-pressed="false" tabindex="0"><span class="icon icon-section-action">
                  </span><span class="hide-offscreen">Expand Section</span></button></div><div class="sm-live-area hide-offscreen" aria-live="polite">
              </div></div><div class="section-body" id="section-4"><p>Your provider will perform a physical exam and ask questions about your medical history, such as when the problem began and when it occurs.</p><p>The provider will also ask about other symptoms you may be having, such as: </p><ul><li>Absent menstrual period</li><li><a test="test" href="./003126.htm">Diarrhea</a></li><li>Excessive <a test="test" href="./003088.htm">fatigue</a></li><li><a test="test" href="./003124.htm">Excessive gas</a> or <a test="test" href="./003080.htm">belching</a></li><li>Irritability</li><li>Vomiting</li><li>Weight gain or loss</li></ul><p>Tests that may be done include:</p><ul><li><a test="test" href="./003789.htm">Abdominal and pelvic CT scan</a></li><li><a test="test" href="./003777.htm">Abdominal and pelvic ultrasound</a></li><li>Blood tests</li><li><a test="test" href="./003886.htm">Colonoscopy</a></li><li><a test="test" href="./003888.htm">Esophagogastroduodenoscopy</a> (EGD)</li><li><a test="test" href="./003896.htm">Paracentesis</a></li><li><a test="test" href="./003885.htm">Sigmoidoscopy</a></li><li>Stool analysis</li><li>Urine tests</li><li><a test="test" href="./003815.htm">X-rays of the chest or abdomen</a></li></ul></div></div></section><section><div class="section"><div class="section-header"><div class="section-title"><h2>Alternative Names</h2></div><div class="section-button"><button type="submit" aria-controls="section-Alt" role="button" title="Expand Section" aria-pressed="false" tabindex="0"><span class="icon icon-section-action">
        </span><span class="hide-offscreen">Expand Section</span></button></div><div class="sm-live-area hide-offscreen" aria-live="polite">
    </div></div><div class="section-body" id="section-Alt"><p>Swollen belly; Swelling in the abdomen; Abdominal distention; Distended abdomen </p></div></div></section><section><div class="section sec-mb"><div class="section-header"><div class="section-title"><h2>Images</h2></div><div class="section-button"><button type="submit" aria-controls="section-tnails" role="button" title="Expand Section" aria-pressed="false" tabindex="0"><span class="icon icon-section-action">
              </span><span class="hide-offscreen">Expand Section</span></button></div><div class="sm-live-area hide-offscreen" aria-live="polite">
          </div></div><div name="Images" class="section-body" id="section-tnails"><ul class="img-grid group">
    <li class="thum-1"><img src="//medlineplus.gov/ency/images/ency/tnails/17108t.jpg" alt="Ovarian cysts" title="Ovarian cysts" class="side-img"><a href="../imagepages/17108.htm">Ovarian cysts</a></li>
    <li class="thum-2"><img src="//medlineplus.gov/ency/images/ency/tnails/17064t.jpg" alt="Fibroid tumors" title="Fibroid tumors" class="side-img"><a href="../imagepages/17064.htm">Fibroid tumors</a></li><li style="clear:both;"></li>
    </ul></div></div></section><section><div class="section"><div class="section-header"><div class="section-title"><h2>References</h2></div><div class="section-button"><button type="submit" aria-controls="section-Ref" role="button" title="Expand Section" aria-pressed="false" tabindex="0"><span class="icon icon-section-action">
        </span><span class="hide-offscreen">Expand Section</span></button></div><div class="sm-live-area hide-offscreen" aria-live="polite">
    </div></div><div class="section-body" id="section-Ref"><p>Ball JW, Dains JE, Flynn JA, Solomon BS, Stewart RW. Abdomen. In: Ball JW, Dains JE, Flynn JA, Solomon BS, Stewart RW, eds. <em>Seidel's Guide to Physical Examination</em>. 10th ed. Philadelphia, PA: Elsevier; 2023:chap 18.</p><p>Landmann A, Bonds M, Postier R. Acute abdomen. In: Townsend CM Jr, Beauchamp RD, Evers BM, Mattox KL, eds. <em>Sabiston Textbook of Surgery</em>. 21st ed. St Louis, MO: Elsevier; 2022:chap 46.</p><p>McQuaid KR. Approach to the patient with gastrointestinal disease. In: Goldman L, Cooney KA, eds. <em>Goldman-Cecil Medicine</em>. 27th ed. Philadelphia, PA: Elsevier; 2024:chap 118.</p></div></div></section>
    <section><div class="section"><div class="section-header"><div class="section-title"><h2>Review Date 10/9/2024</h2></div><div class="section-button"><button type="submit" aria-controls="section-version" role="button" title="Expand Section" aria-pressed="false" tabindex="0"><span class="icon icon-section-action">
          </span><span class="hide-offscreen">Expand Section</span></button></div><div class="sm-live-area hide-offscreen" aria-live="polite">
      </div></div>
    <div id="section-version" class="section-body"><p>Updated by: Linda J. Vorvick, MD, Clinical Professor, Department of Family Medicine, UW Medicine, School of Medicine, University of Washington, Seattle, WA. Also reviewed by David C. Dugdale, MD, Medical Director, Brenda Conaway, Editorial Director, and the A.D.A.M. Editorial team.  </p>
    </div></div></section><section><div class="section ency-citation"><div class="section-header"><div class="section-title ency-citation"><div id="citation-how-to"><button><span>Learn how to cite this page</span></button></div></div><div class="sm-live-area hide-offscreen" aria-live="polite">
          </div></div></div></section><section><div class="section sec-mb"><div class="section-header"><div class="section-title"><h2>Related MedlinePlus Health Topics</h2></div><div class="section-button"><button type="submit" aria-controls="section-mtp" role="button" title="Expand Section" aria-pressed="false" tabindex="0"><span class="icon icon-section-action">
                </span><span class="hide-offscreen">Expand Section</span></button></div><div class="sm-live-area hide-offscreen" aria-live="polite">
            </div></div><div name="Related MedlinePlus Health Topics" class="section-body" id="section-mtp"><ul class="side-nav"><li><a href="https://medlineplus.gov/edema.html">Edema</a></li>
    
    
    </ul></div></div></section></div><div class="side"><aside><section><div class="side-section"><div class="section-header"><h2>Related MedlinePlus Health Topics</h2></div><div class="section-body"><ul class="side-nav"><li><a href="https://medlineplus.gov/edema.html">Edema</a></li>
    
    
    </ul></div></div></section><section><div class="side-section"><div class="section-header"><h2>Images</h2></div><div class="section-body"><ul class="img-grid group">
    <li class="thum-1"><img src="//medlineplus.gov/ency/images/ency/tnails/17108t.jpg" alt="Ovarian cysts" title="Ovarian cysts" class="side-img"><a href="../imagepages/17108.htm">Ovarian cysts</a></li>
    <li class="thum-2"><img src="//medlineplus.gov/ency/images/ency/tnails/17064t.jpg" alt="Fibroid tumors" title="Fibroid tumors" class="side-img"><a href="../imagepages/17064.htm">Fibroid tumors</a></li><li style="clear:both;"></li>
    </ul></div></div></section></aside></div></div></article>
```

---

### Step 3 — scrap everything including the images url if available

**do not create a static key value pair, it must be dynamic**

**please ignore References and Review Date 10/30/2024 and all the class="side-section" except images in the class="side-section"**

---
## Extraction Rules

### General Principles
- Perform **dynamic extraction** based on the page content
- Do **not rely on fixed or predefined section names**

### Flexibility
- The **page structure may vary**
- Identify sections, headings, and data **at runtime**
- Adapt to different layouts, nesting, and formats

### Guidelines
- Detect headings using semantic cues (e.g., HTML tags, font size, patterns)
- Extract content relative to detected structure rather than fixed positions
- Handle missing, reordered, or additional sections gracefully




## Output Format

One JSON object per article.

Example:

{
"id": "000686",
"title": "Sciatica",
"source": "MedlinePlus",
"source_url": "...",
"summary": "...",
"sections": {
...
},
"images": [...],
"related_topics": [...]
}

## Checkpointing

Every 25 articles:

Save:

checkpoint.json

Contains:

{
"completed_articles": [],
"failed_articles": [],
"last_saved": ""
}

## Output Files

articles.jsonl

One JSON document per line.

checkpoint.json

errors.json

## Error Handling

Retry failed page:

3 times

with exponential backoff.

Log failures.

Continue execution.

Never stop entire run because of one article.

## Performance

Use Playwright async.

Use asyncio.Queue.

Use worker pattern.

Avoid loading images/css/fonts when possible.

Block unnecessary requests.

Implement graceful shutdown.

Generate complete production-ready code.

## Checkpointing & Resume

Save a JSON checkpoint file (`scraper_checkpoint.json`) after **every individual result row** is appended:
```json
{ "prod_idx": 42, "item_idx": 2 }
```

On startup, if the checkpoint file exists, skip products before `prod_idx` and skip items before `item_idx` within the resume product. Load the existing CSV rows back into memory so the final write is cumulative.

Flush the CSV to disk after **every product** completes (not just at the end) so data is safe if the script is interrupted.

---
