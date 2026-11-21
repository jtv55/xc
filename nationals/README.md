# 2026 CCCNYC & CYO Nationals Analytics Suite

Comprehensive scouting, race simulation, school/club power analysis, and individual runner intelligence for the **20th Cross Country Coaches National Youth Championships (CCCNYC)** and **CYO National Championships** (**Saturday, November 21, 2026** at Elvin R. King Cross Country Course, Cedarville University, Cedarville, OH).

> **Dashboard Scope Note:** The web dashboard filters out the young tier (**ages 8 & under** — Events 3, 4, and 5) at the presentation layer in `app.js` to focus cleanly on the **8 Ages 9–18 championship divisions (`2,133` unique runners · `88.4%` empirically seeded · `90` organizations · `54` Pittsburgh CYO qualifiers across `8` complete squads)**. No underlying data has been deleted: all 11 events and 2,616 unique entrants remain preserved intact in `build_model.py`, `data/data.js`, `data/cccnyc_2026_master.json`, the CSV exports, and all 6 PDFs.

## Pages

- **`index.html` — Meet Hub**: Schedule & projected podiums across the **8 Ages 9–18 championship races** (toggleable between **National Open** and **CYO National Championship** scoring), interactive Cedarville 3K–5K course elevation/terrain visualizer, 4-year historical benchmark charts (13,540 finishers from 2022–2025), and official Nov 20 entry-list forensic audit.
- **`races.html` — 8-Race Simulator**: 10,000-trial Monte Carlo team displacement forecasts, P10–P90 score range fans, field pace distribution ridgelines, individual win/podium/All-American S-curves, pairwise head-to-head team win probability matrix, and a live **Coach's What-If Sandbox**.
- **`diocese.html` — Pittsburgh CYO (Diocese of Pittsburgh) Command Center**: Complete breakdown of all **54 Ages 9–14 Pittsburgh CYO entrants** (`8` complete 6–8 runner scoring squads) mapped to their **13 Catholic feeder schools**, Dual-Crown National Open vs. CYO National projections, 1–5 pack compression ladders & 6–7 displacer analysis, and single-year birth-age Top-25 All-American medal odds.
- **`clubs.html` — Schools & Clubs Power Index**: Program power index bubble chart across **90 Ages 9–18 organizations** from **19 US states + Bermuda**, CYO National Cup omnium standings across **10 Catholic diocesan & parish programs (366 runners)**, cross-division club × race rank heatmap, and interactive club roster inspector.
- **`runners.html` — 2,133-Runner Scouting**: Searchable/filterable table of every Ages 9–18 entrant, individual scouting dossiers with 2026 season pace trajectories & CCCNYC veteran history, **Single-Year Birth-Age #25 All-American Cutline Explorer** (`Ages 9..14`), and interactive **Head-to-Head Rivalry Density Comparator**.

## Data Pipeline & Methodology

1. **Final Entry List Reconciliation (Nov 20)**: Parsed all 31 pages of the official `Entry List.pdf` (`2,617` total rows → `2,616` unique runners; `2,133` unique runners in the Ages 9–18 dashboard view after neutralizing 1 dual-listed entry in Event 2).
2. **Nationwide Empirical Performance Coverage**:
   - **Ages 9–18 Dashboard View:** **`1,886 / 2,133` (`88.4%`)** directly tied to verified individual race histories (`1,588` with 2026 race logs + `878` returning CCCNYC veterans); **`90.2%`** across core youth championship Ages 9–14.
   - **Full 11-Event Underlying Archive:** **`2,226 / 2,616` (`85.1%`)** empirically seeded (`63/63 = 100%` Pittsburgh CYO overall; `54/54 = 100%` in Ages 9–14).
   - Sources include **220+ RunSignup REST API 2025–2026 XC databases** (with strict age+state+initial matching for privacy-masked minor results), **20 Indiana Midwest Championship & Mudsock Youth XC PDFs**, **21 Official 2026 KHSAA Kentucky Regional files**, **17 Brocaw Blazers & Missouri Valley Regional PDFs (2024–2026)**, **53 Missouri TRXC Timing race pages**, **10 Oklahoma OSSAA 2026 State & Regional PDFs**, **LA-CYO 2026 Finals & Semifinals**, **227 Smiley Miles OA files**, **PAUSATF California**, verified MileSplit athlete histories, and **4 years of CCCNYC National Championship results (2022–2025, 13,540 finishers)**.
3. **10,000-Trial Monte Carlo Engine (`build_model.py`)**:
   - Correlated club-day form + individual race-day right-skewed variance across 10,000 simulated races per event, with simultaneous **National Open** and **CYO National Championship** Rule B.5 team displacement scoring and **Single-Year Birth-Age Top-25 All-American** tracking.

## Running Locally

From `c:\Users\j_t_v\XC`:

```powershell
python -m http.server 8765
```

Then open `http://localhost:8765/nationals/index.html`. To rebuild HTML shells after layout edits, run `python nationals/build_pages.py`.
