# 2026 CCCNYC & CYO Nationals Analytics Suite

Comprehensive scouting, race simulation, school/club power analysis, and individual runner intelligence for the **20th Cross Country Coaches National Youth Championships (CCCNYC)** and **CYO National Championships** (**Saturday, November 21, 2026** at Elvin R. King Cross Country Course, Cedarville University, Cedarville, OH).

## Pages

- **`index.html` — Meet Hub**: Official Eastern Standard Time race-day schedule (including Coaches Meeting, National Anthem, Officials' Break & original graphic), interactive **USA Choropleth & Club Home Cities Map** (darker states = more runners, city dots for all 91 clubs + Bermuda inset & Cedarville venue pin), projected podiums across all 11 championship races (toggleable between **National Open** and **CYO National Championship** scoring), interactive Cedarville 1K–5K course elevation/terrain visualizer, 4-year historical benchmark charts (13,540 finishers from 2022–2025), and official Nov 20 entry-list forensic audit.
- **`races.html` — 11-Race Simulator**: 10,000-trial Monte Carlo team displacement forecasts, P10–P90 score range fans, field pace distribution ridgelines, individual win/podium/All-American S-curves, pairwise head-to-head team win probability matrix, and a live **Coach's What-If Sandbox** (including hypothetical 5th-runner injection for incomplete squads).
- **`diocese.html` — Pittsburgh CYO (Diocese of Pittsburgh) Command Center**: Complete breakdown of all 64 Pittsburgh CYO entrants mapped to their **13 Catholic feeder schools**, Dual-Crown National Open vs. CYO National projections across all **10 complete scoring squads**, 1–5 pack compression ladders & 6–7 displacer analysis, and single-year birth-age Top-25 All-American medal odds.
- **`clubs.html` — Schools & Clubs Power Index**: Program power index bubble chart across **91 organizations** from **20 US states + Bermuda**, CYO National Cup omnium standings across **10 Catholic diocesan & parish programs (490 runners)**, cross-division club × race rank heatmap, and interactive club roster inspector.
- **`runners.html` — 2,617-Runner Scouting**: Searchable/filterable table of every entrant, individual scouting dossiers with 2026 season pace trajectories & CCCNYC veteran history, **Single-Year Birth-Age #25 All-American Cutline Explorer** (`Ages 6..14`, `15–16`, `17–18`), and interactive **Head-to-Head Rivalry Density Comparator**.

## Data Pipeline & Methodology

1. **Final Entry List Reconciliation (Nov 20 + Nov 21 Late Add)**: Parsed all 31 pages of the official `Entry List.pdf` plus late Boys 6–8 addition Diego Victor (`2,618` raw entries → `2,617` unique runners after neutralizing 1 dual-listed entry in Event 2), mapping all **91 clubs/dioceses** and **10 CYO programs** (`Pittsburgh CYO` 64/64 intact, 10/10 complete scoring squads).
2. **Nationwide Empirical Performance Coverage (`2,227 / 2,617 = 85.1%` overall; `90.2%` across Ages 9–14)**:
   - **100% (`64/64`) Pittsburgh CYO entrants** matched across 2026 Western PA meets (Smiley Miles OA results + RunSignup Diocesan Championship & invitational APIs, averaging 6.2 verified 2026 races per runner) and mapped to their 13 Catholic feeder schools.
   - **2,227 unique national entrants** tied directly to verified individual race results across:
     - **220+ RunSignup REST API 2025–2026 XC databases** (including strict zero-false-positive age+state+initial matching for privacy-masked minor results across CO, NJ, MD, MI, IN, IL, OH, VA, MO, OK)
     - **20 Indiana Midwest Championship & Mudsock Youth XC PDFs** (`abtiming.com` public archives)
     - **21 Official 2026 KHSAA Kentucky Regional Championship files** (`khsaa.org`)
     - **17 Brocaw Blazers & Missouri Valley Regional PDFs (2024–2026)** (`brocawblazers.org`)
     - **53 Missouri TRXC Timing 2025–2026 MS/HS race pages** (`trxctiming.com`)
     - **10 Oklahoma OSSAA 2026 State & Regional PDFs** (`ohstrack.com`)
     - **LA-CYO 2026 Finals (Nov 15) & Semifinals (Nov 8)** (`extramiletiming`)
     - **227 Smiley Miles OA files**, **PAUSATF California**, **earlier MileSplit verified athlete histories**, and **4 years of CCCNYC National Championship results (2022–2025, 13,540 finishers)**.
   - The remaining `14.9%` (`390` runners — over one-third of whom are ages 3–8 developmental beginners with no public timing history) receive calibrated **Hierarchical Club × Single-Year Birth-Age Empirical Bayes priors**.
3. **Distance, Surface & Age-Progression Calibration**:
   - Calibrated the Oct 17, 2026 Pittsburgh Diocesan Championship (`#193936`) Developmental K–2 & 3–4 distance from mis-tagged `1.35 mi` to true `1.50 mi (2,414m)`.
   - Applied youth Riegel distance scaling, rubber-track-to-grass-XC surface conversion, and empirical single-age annual progression curves for returning veterans, passing a strict physiological pace floor check (`0` outliers across all 2,617 runners).
4. **10,000-Trial Monte Carlo Engine (`build_model.py`)**:
   - Correlated club-day form + individual race-day right-skewed variance across 10,000 simulated races per event.
   - Simultaneous **National Open** and **CYO National Championship** Rule B.5 team displacement scoring (top 5 score, 6–7 displace, Rule B.6 6th-runner tiebreaker) plus **Single-Year Birth-Age Top-25 All-American** tracking.

## Running Locally

From `c:\Users\j_t_v\XC`:

```powershell
python -m http.server 8765
```

Then open `http://localhost:8765/nationals/index.html`. To rebuild HTML shells after layout edits, run `python nationals/build_pages.py`.
