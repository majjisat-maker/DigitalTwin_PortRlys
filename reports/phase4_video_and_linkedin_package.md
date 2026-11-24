# Phase 4 — YouTube & LinkedIn Package
## "I Built a Digital Twin of a Port Rail Siding"

**Channel:** Satish Majji | Beyond the Obvious (@BeyondTheObviousSM)
**Format:** 3 parts of about 5 minutes each. Each part works on its own. Publish them as one long video with chapters, or as 3 separate videos.
**Narration:** your own voice, recorded on phone. Script in simple English, short sentences.
**Rule for all footage:** only anonymised material. No company, port, customer or station names on screen.

---

## A. Recording plan (what to screen-record)

Record at **1920 × 1080**, browser zoom **110%**, mouse movements slow. Record each scene as a separate clip and name it by scene number (S1-01, S1-02 …).

| Scene | What to record | Source |
|---|---|---|
| S1-01 | Title card: "₹1.46 crore. One month. One rail siding." (white text on dark) | Make in Clipchamp |
| S1-02 | Chart: *Loading costs almost 3x more demurrage than unloading* | `outputs/charts/08_demurrage_inward_vs_outward.png` |
| S1-03 | Simple text slide: "Free time → clock → demurrage" (see script) | Make in Clipchamp |
| S1-04 | Slab table from Phase 1 report, section 2 | `reports/phase1_baseline_report.md` (open in GitHub view) |
| S1-05 | Chart: *Arrivals by hour* | `01_arrivals_by_hour.png` |
| S1-06 | Chart: *Outward over free time by mode* | `07_outward_over_free_by_mode.png` |
| S1-07 | Chart: *Tippler vs manual* | `03_unload_time_manual_vs_tippler.png` |
| S1-08 | Chart: *Clustering vs demurrage* | `02_clustering_vs_demurrage.png` |
| S2-01 | Title card: "What is a digital twin?" | Make in Clipchamp |
| S2-02 | Simple diagram slide: Rake → Wait → Point → Work → Draw-out → Demurrage | Make in Clipchamp (boxes and arrows) |
| S2-03 | Scroll slowly through `rake_twin_sim.py`, the "life of one rake" section | Code editor or GitHub |
| S2-04 | Calibration table (Phase 2 report, section 2) | `reports/phase2_simulation_report.md` |
| S2-05 | Chart: *Validation* | `09_validation.png` |
| S3-01 | Dashboard home, untouched (blue info box visible) | Live dashboard |
| S3-02 | Move **Loading speed** to 115 → Run the twin | Live dashboard |
| S3-03 | Reset loading. Move **Pre-placement time saved** to 30 → Run | Live dashboard |
| S3-04 | Reset. Move **Tippler speed** to 125 → Run | Live dashboard |
| S3-05 | Open **Resources**, set **Locos** to 5 → Run | Live dashboard |
| S3-06 | Combined: tippler 125, loading 115, placement 30, even arrivals on → Run | Live dashboard |
| S3-07 | Chart: *What each change is worth* | `10_scenario_savings.png` |
| S3-08 | "How the twin works" tab → scroll to *Honest limits* | Live dashboard |
| S3-09 | End card: "Satish Majji \| Beyond the Obvious · @BeyondTheObviousSM" | Make in Clipchamp |

> Tip: before recording S3, reset all sliders to default. Wait until the numbers finish loading before you move the mouse again.

---

## B. Pronunciation guide

| Word | Say it like |
|---|---|
| demurrage | deh-**MUR**-ij |
| tippler | **TIP**-ler |
| simulation | sim-yoo-**LAY**-shun |
| SimPy | **SIM**-pie |
| Streamlit | **STREAM**-lit |
| calibrate / calibration | **KAL**-i-brate / kal-i-**BRAY**-shun |
| validation | val-i-**DAY**-shun |
| scenario | se-**NAH**-ree-oh |
| lakh / crore | lakh / crore (as usual) |

**Marks used in the script:**
`[pause]` = stop for one second · **bold** = say this word a little stronger · `/` = small breath

---

## C. Narration script

Speaking speed: slow and calm, about 110–120 words a minute.

---

### PART 1 — "₹1.46 Crore in One Month" (about 5:00)

**S1-01 · 0:00–0:25 · Hook**
> One rail siding. / One month. [pause]
> **One crore and forty-six lakh rupees** in demurrage. [pause]
> That is the money a port siding paid in July 2025, / just for keeping railway wagons too long.
> In this video, / I will show you where that money went. [pause]
> And then I will build a **digital twin** / to find out which fix is worth the most.

**S1-02 · 0:25–1:10 · The big picture**
> On screen, you see two bars. [pause]
> The blue bar is **unloading**. / These are loaded rakes that come in. / Their demurrage was **38 lakh rupees**.
> The orange bar is **loading**. / These are rakes that we fill and send out. / Their demurrage was **107 lakh rupees**.
> So loading cost almost **three times** more than unloading. [pause]
> Most people look at the unloading side first. / The data says: / **look at loading**.

**S1-03 · 1:10–1:50 · What is demurrage?**
> Let me explain demurrage in a simple way. [pause]
> When the railway hands over a rake, / a clock starts.
> The siding gets some **free time**. / For unloading, it is six and a half hours. / For most loading, it is five and a half hours.
> If the rake is drawn out after the free time, / the siding pays demurrage. [pause]
> Every extra hour is rounded up / to a full hour.

**S1-04 · 1:50–2:25 · The slab rule**
> This table shows the rate. [pause]
> The base rate is **one hundred fifty rupees** / per wagon / per hour.
> After six hours, / the rate goes up by ten percent. / After twelve hours, / by twenty-five percent. / After one day, / by fifty percent.
> So a few **long delays** / cost much more / than many short ones. [pause]
> I rebuilt this rule from the data. / My calculation matched the site's bills / **to the rupee**.

**S1-05 · 2:25–2:55 · Arrivals**
> This chart shows when inward rakes arrived. / Each bar is one hour of the day.
> You can see rakes come **all day and all night**. / There is no quiet hour. [pause]
> In July, / about **eight rakes a day** came in for unloading.

**S1-06 · 2:55–3:40 · Loading problem**
> Now look at loading. [pause]
> Each bar shows / what share of rakes went over free time, / for each loading method.
> The silo: / 77 percent. / Manual loading: / 81 percent.
> And the wagon loader: / **100 percent**. [pause]
> Every single wagon-loader rake paid demurrage.
> Why? / Because the wagon loader takes about **six hours** to load a rake. / The free time is only five and a half hours. [pause]
> The rake is late / before anything even goes wrong.

**S1-07 · 3:40–4:20 · The tippler**
> This chart compares two ways of unloading. [pause]
> Blue is **manual** unloading. / Orange is the **wagon tippler**, / a machine that turns each wagon upside down.
> The tippler is rated for **24 wagons an hour**. / That means a full rake / in about two and a half hours.
> In July, / it did about **ten wagons an hour**. [pause]
> That is around **one third** of its rated speed. / Manual unloading was actually faster.

**S1-08 · 4:20–5:00 · Clustering + close**
> Last chart for this part. [pause]
> Each bar groups rakes / by how many other rakes / arrived in the six hours before them.
> A rake that came alone / paid less than one hour of demurrage on average.
> A rake that came after three or more others / paid about **three times more**. [pause]
> So the problem is not busy days. / The problem is rakes arriving **close together**.
> Now we know **where** the money goes. [pause]
> In the next part, / I will build a digital twin / to test **what fixes it**.

---

### PART 2 — "Building the Digital Twin" (about 5:00)

**S2-01 · 0:00–0:30 · Hook**
> What if you could test a new idea / without touching the real yard? [pause]
> No risk. / No cost. / No waiting for next month.
> That is what a **digital twin** does. [pause]
> In this part, / I will show you how I built one, / and how I proved it is correct.

**S2-02 · 0:30–1:45 · How it works**
> A digital twin is a copy of the yard / inside the computer. [pause]
> Look at the boxes on screen.
> First, / a rake **arrives**. / In my model, / every rake arrives at its **real July time**.
> Then it does the steps before placement: / examination, / weighment, / line clearing.
> Then it **waits** for its working point. / There is only **one tippler**. / There are a few manual lines, / a silo, / and a wagon loader.
> If the point is busy, / the rake waits in a queue. / Just like real life. [pause]
> It also needs a **loco** / to be placed / and to be drawn out.
> Then the work is done, / unloading or loading.
> The time for each job / is picked at random / from the **real July times**.
> And many inward rakes / are loaded again for the return trip. / So in the model, / the outward rake can start / only when its inward rake is empty. [pause]
> At the end, / the model calculates demurrage / with the real slab rule.

**S2-03 · 1:45–2:30 · The code**
> This is the code. / It is written in Python, / with a tool called **SimPy**.
> Every line has a plain-English note. / For example: / "Ask for the point, / and wait until it is free."
> I play the whole month / **one hundred times**. [pause]
> Why one hundred? / Because work times change every day. / One run is one possible July. / One hundred runs show the **normal range**.

**S2-04 · 2:30–3:50 · Calibration**
> My first model did not match reality. [pause]
> The tippler queue became too long. / And too many rakes went over free time.
> So I looked deeper into the data. / I found **two things**. [pause]
> One. / The records show up to three rakes / placed at the tippler **at the same time**. / But there is only one tippler. / So part of the recorded tippler time / is finishing work / that does not stop the next rake. / In the model, / I set this to **seventy percent**.
> Two. / Many inward rakes are recorded / at **exactly** six and a half hours, / the free-time limit. / Almost none are recorded under it. [pause]
> This means rakes that finished early / were written down at the limit. / So the real work / is about **fifteen percent faster** / than the records show.
> These two settings / are called **calibration**.

**S2-05 · 3:50–5:00 · Validation + close**
> Now the important test. / Does the twin match July? [pause]
> Grey bars are the **actual** demurrage. / Blue bars are the **twin**. / The black lines show the range / across one hundred runs.
> Inward: / actual 38 lakh. / Twin: 39 lakh.
> Outward: / actual 107 lakh. / Twin: 113 lakh.
> Whole yard: / actual 146 lakh. / Twin: 152 lakh. [pause]
> Every measure is within **five percent**. / And every real value sits inside the twin's range.
> So the twin is ready. [pause]
> In the next part, / I will change the yard / and see / how much money each change saves.

---

### PART 3 — "What Is Each Fix Worth?" (about 5:00)

**S3-01 · 0:00–0:35 · Hook + dashboard**
> Faster tippler? / Faster loading? / More locos? [pause]
> Every manager has a favourite fix. / Today, / the twin will tell us / what each one is **really worth**.
> This is the dashboard I built. / On the left, / you can change the yard. / On the right, / you see the result.
> Right now, / it shows July as it happened: / about **150 lakh rupees** of demurrage a month.

**S3-02 · 0:35–1:20 · Faster loading**
> First test. / I make loading **fifteen percent faster**. / Then I press "Run the twin". [pause]
> The twin plays July again, / fifty times.
> Look at the top. / Demurrage drops by about **twenty lakh rupees** a month.
> And the share of outward rakes over free time / goes down by about five points. [pause]
> This is the **biggest single saving**.

**S3-03 · 1:20–2:00 · Quicker placement**
> Second test. / I put loading back. / Now I save **thirty minutes** / in the steps before placement. / That means faster examination, / weighment / and line clearing. [pause]
> The saving is about **eighteen lakh rupees** a month.
> And this one needs **no new machine**. / Only better planning and coordination.

**S3-04 · 2:00–2:35 · Faster tippler**
> Third test. / I make the tippler **twenty-five percent faster**. [pause]
> The saving is about **eight lakh** a month. / It helps unloading only. / Fewer inward rakes go over free time.

**S3-05 · 2:35–3:05 · Fewer locos**
> Now a stress test. / What if only **five locos** are working, / instead of nine? [pause]
> Look. / The demurrage **hardly changes**.
> So locos are **not** the bottleneck here. / Buying more locos / would not reduce demurrage.

**S3-06 · 3:05–3:45 · All together**
> Now I combine the changes. / Tippler twenty-five percent faster. / Loading fifteen percent faster. / Thirty minutes saved before placement. / And arrivals spread evenly. [pause]
> Demurrage falls / from about **150** / to about **108 lakh rupees** a month.
> That is around **forty-four lakh** a month. / About **five crore rupees** a year. [pause]
> Almost **one third** of the bill.

**S3-07 · 3:45–4:15 · Summary chart**
> This chart shows the full list. [pause]
> Loading speed and placement time / are worth the most.
> The tippler helps, / but less.
> More locos / and spreading arrivals / show almost nothing / in this version of the model.

**S3-08 · 4:15–4:45 · Honest limits**
> I want to be honest about the limits. [pause]
> The model does not yet include **route conflicts**: / shared lines, / hand-operated points, / and level crossings. / That is probably how bunched rakes really cause delay. / It will be my next version.
> Also, / this is one month of data. / The savings are **estimates**, / not promises.

**S3-09 · 4:45–5:00 · Close**
> The lesson is simple. [pause]
> Do not start with the machine you want to buy. / Start with the **data**. / Then test the idea / in a twin.
> The code and the dashboard / are linked in the description.
> I am Satish Majji. / This is **Beyond the Obvious**. / Thank you for watching.

---

## D. Audio alignment sheet

Record each segment as a **separate audio file**, named as below, so the editor can sync it to the matching clip.

| Audio file | Scene clip | Start | End | Duration |
|---|---|---|---|---|
| P1_S01.m4a | S1-01 | 0:00 | 0:25 | 0:25 |
| P1_S02.m4a | S1-02 | 0:25 | 1:10 | 0:45 |
| P1_S03.m4a | S1-03 | 1:10 | 1:50 | 0:40 |
| P1_S04.m4a | S1-04 | 1:50 | 2:25 | 0:35 |
| P1_S05.m4a | S1-05 | 2:25 | 2:55 | 0:30 |
| P1_S06.m4a | S1-06 | 2:55 | 3:40 | 0:45 |
| P1_S07.m4a | S1-07 | 3:40 | 4:20 | 0:40 |
| P1_S08.m4a | S1-08 | 4:20 | 5:00 | 0:40 |
| P2_S01.m4a | S2-01 | 0:00 | 0:30 | 0:30 |
| P2_S02.m4a | S2-02 | 0:30 | 1:45 | 1:15 |
| P2_S03.m4a | S2-03 | 1:45 | 2:30 | 0:45 |
| P2_S04.m4a | S2-04 | 2:30 | 3:50 | 1:20 |
| P2_S05.m4a | S2-05 | 3:50 | 5:00 | 1:10 |
| P3_S01.m4a | S3-01 | 0:00 | 0:35 | 0:35 |
| P3_S02.m4a | S3-02 | 0:35 | 1:20 | 0:45 |
| P3_S03.m4a | S3-03 | 1:20 | 2:00 | 0:40 |
| P3_S04.m4a | S3-04 | 2:00 | 2:35 | 0:35 |
| P3_S05.m4a | S3-05 | 2:35 | 3:05 | 0:30 |
| P3_S06.m4a | S3-06 | 3:05 | 3:45 | 0:40 |
| P3_S07.m4a | S3-07 | 3:45 | 4:15 | 0:30 |
| P3_S08.m4a | S3-08 | 4:15 | 4:45 | 0:30 |
| P3_S09.m4a | S3-09 | 4:45 | 5:00 | 0:15 |

If your voice runs longer than the clip, slow the screen clip in Clipchamp or hold the last frame. Do not speed up your voice.

---

## E. YouTube publishing kit

**Title options**
1. I Built a Digital Twin of a Port Rail Siding — Here's What It Found
2. ₹1.46 Crore of Demurrage in One Month: A Digital Twin Finds the Fix
3. Where Does Rail Demurrage Really Come From? (Real Data + Digital Twin)

**Thumbnail:** dark background, big text **"₹1.46 CRORE / 1 MONTH"**, small text "Digital twin finds the fix", the orange-vs-blue bar chart on the right.

**Description**
> One port rail siding paid ₹1.46 crore in demurrage in a single month. I took the real (anonymised) data for July 2025, with 251 inward and 365 outward rakes, found where the time goes, and built a digital twin to test which fixes are worth the most.
>
> 🔹 Live dashboard: [Streamlit link]
> 🔹 Code and reports: [GitHub link]
>
> Chapters:
> 0:00 ₹1.46 crore in one month
> 1:10 What is demurrage?
> 2:55 Why loading is the real problem
> 3:40 The tippler at one-third speed
> 4:20 Clustered arrivals
> 5:00 What is a digital twin?
> 7:30 Calibration: what the data was hiding
> 8:50 Does the twin match reality?
> 10:00 Testing fixes on the dashboard
> 13:05 All fixes combined
> 14:15 Honest limits
>
> All customer, station and site names are anonymised.
> Satish Majji | Beyond the Obvious, industrial rail and bulk logistics.

**Tags:** digital twin, railway operations, demurrage, rake turnaround, bulk logistics, port logistics, wagon tippler, simulation, SimPy, Python for engineers, supply chain, industrial railway

---

## F. LinkedIn package

### F1. 90-second cut (native LinkedIn video)

Use these clips in order. Re-use your recorded audio; no new recording is needed.

| Order | Clip | Audio | Approx. length |
|---|---|---|---|
| 1 | S1-01 | P1_S01 | 0:25 |
| 2 | S1-02 | P1_S02 (first 3 sentences + last 2) | 0:25 |
| 3 | S2-05 | P2_S05 (from "Grey bars…" to "…within five percent") | 0:20 |
| 4 | S3-06 | P3_S06 | 0:30 |
| 5 | S3-09 | Last 2 lines of P3_S09 | 0:10 |

Add burned-in captions in Clipchamp. Most LinkedIn viewers watch without sound.

### F2. Post text

> One rail siding. One month. ₹1.46 crore in demurrage.
>
> I took one month of real (anonymised) data from a port rail siding: 251 inward rakes and 365 outward rakes. Then I built a digital twin of the yard in Python.
>
> Three things stood out:
>
> 1️⃣ Loading, not unloading, drives the bill. Outward demurrage was almost 3x inward. Every single wagon-loader rake went over free time.
>
> 2️⃣ The wagon tippler worked at about one-third of its rated speed.
>
> 3️⃣ More locos would not help. Even with 5 locos instead of 9, demurrage barely changed.
>
> The twin matches the real month within 5%. Testing fixes in it shows that faster loading plus 30 minutes saved before placement are worth the most. All changes together cut demurrage by about ₹44 lakh a month.
>
> The lesson: don't start with the machine you want to buy. Start with the data, then test the idea in a twin.
>
> 🔗 Try the live dashboard: [link]
> 🎥 Full walkthrough: [link]
>
> #DigitalTwin #RailOperations #BulkLogistics #SupplyChain #Demurrage #IndustrialRailway

### F3. Profile: Featured section and Projects

**Featured → Add link** (dashboard), title:
> Rake Turnaround Digital Twin: Port Rail Siding (July 2025)

**Projects → Add project**
> **Rake Turnaround Digital Twin** · Python, SimPy, Streamlit
> Built a validated simulation of a port rail siding from one month of real operations data (616 rakes). Decoded the demurrage contract and matched site billing to the rupee. The twin reproduces actual demurrage within ±5% and shows that 15% faster loading (≈₹20 lakh/month) and 30 minutes quicker pre-placement (≈₹18 lakh/month) are the biggest levers, while extra locos add nothing.

---

## G. Before you publish: checklist

- [ ] No company, port, customer or station name in any frame (check code-scroll and chart titles)
- [ ] Only files from `rake-twin-phase3.zip` uploaded to GitHub, **never** the PRIVATE zip
- [ ] Streamlit and GitHub links pasted into the README, YouTube description and LinkedIn post
- [ ] Captions added for the LinkedIn cut
- [ ] End card with channel name on every part
