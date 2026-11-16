# 2026 CCCNYC & CYO Nationals Analytics Suite

Comprehensive scouting, race simulation, school/club power analysis, and individual runner intelligence for the **20th Cross Country Coaches National Youth Championships (CCCNYC)** and **CYO National Championships** (**Saturday, November 21, 2026** at Elvin R. King Cross Country Course, Cedarville University, Cedarville, OH).

## Pages

- **`index.html` — Meet Hub**: Schedule & projected podiums across all 11 championship & B races (toggleable between **National Open** and **CYO National Championship** scoring), interactive Cedarville 1K–5K course elevation/terrain visualizer, 4-year historical benchmark charts (13,540 finishers from 2022–2025), and official entry-list registration hygiene audit.
- **`races.html` — 11-Race Simulator**: 10,000-trial Monte Carlo team displacement forecasts, P10–P90 score range fans, field pace distribution ridgelines, individual win/podium/All-American S-curves, pairwise head-to-head team win probability matrix, and a live **Coach's What-If Sandbox** (including hypothetical 5th-runner injection for incomplete squads).
- **`diocese.html` — Diocese of Pittsburgh Command Center**: Complete breakdown of all 63 Diocese entrants mapped to their **13 Catholic feeder schools**, Dual-Crown National Open vs. CYO National projections, 1–5 pack compression ladders & 6–7 displacer analysis, and single-year birth-age Top-25 All-American medal odds.
- **`clubs.html` — Clubs & Schools Power Index**: Program power index bubble chart across 55 organizations from 18 states + Bermuda, CYO National Cup omnium standings across Catholic dioceses/parishes, cross-division club × race rank heatmap, and interactive club roster inspector.
- **`runners.html` — 1,061-Runner Scouting**: Searchable/filterable table of every entrant, individual scouting dossiers with 2026 season pace trajectories & Cedarville CCCNYC history, **Single-Year Birth-Age #25 All-American Cutline Explorer** (`Ages 6..14`, `15–16`, `17–18`), and interactive **Head-to-Head Rivalry Density Comparator**.

## Data Pipeline & Methodology

1. **Entry List Reconciliation**: Parsed all 13 pages of `Entry_List__CYO.pdf` (`1,058` entries) and reconciled against the Saturday 10:00 PM official `Entry List.pdf` (`1,073` entries), flagging 11 swapped-name duplicate ghost rows (`Delta Hawks Racing`) and 1 dual-listed entrant (`1,061` true unique athletes) so phantom duplicates never distort team displacement scoring.
2. **Nationwide Empirical Performance Scraping (~93.5% Individual Coverage)**:
   - **100% (63/63) Diocese of Pittsburgh entrants** matched across 2026 Western PA meets (Smiley Miles OA results + RunSignup Diocesan Championship & invitational APIs, averaging 6.2 verified 2026 races per runner) and mapped to their 13 feeder schools.
   - **93.5% (992/1,061) unique national entrants** matched to direct verified individual race records across **MileSplit National API (`api/v1/athletes` + `/stats`)**, **112 RunSignup REST API race databases** (OH State, CCC Coaches East Regional, Lester Wright NJ, MI/IN/OH CYO, PA/IL/IN/KY/MD/MI youth invitationals), **227 Smiley Miles OA files**, **PAUSATF California**, **NTFXC Pennsylvania**, **Bullseye Running Maryland**, **MTEC Results Minnesota**, **Hilliard TC**, and **4 years of CCCNYC National Championship results (2022–2025, 13,540 finishers)**.
   - The remaining ~6.5% (primarily first-year 4–8 year old developmental entrants with no public race history) receive **Hierarchical Club × Single-Year Birth-Age Empirical Bayes priors**.
3. **Distance, Surface & Age-Progression Calibration**:
   - Calibrated the Oct 17, 2026 Pittsburgh Diocesan Championship (`#193936`) Developmental K–2 & 3–4 distance from mis-tagged `1.35 mi` to true `1.50 mi (2,414m)`.
   - Applied youth Riegel distance scaling, rubber-track-to-grass-XC surface conversion (`+5.2%` to `+7.5%`), and empirical single-age annual progression curves for returning veterans.
4. **10,000-Trial Monte Carlo Engine (`build_model.py`)**:
   - Correlated club-day form + individual race-day right-skewed variance across 10,000 simulated races per event.
   - Simultaneous **National Open** and **CYO National Championship** Rule B.5 team displacement scoring (top 5 score, 6–7 displace, Rule B.6 6th-runner tiebreaker) plus **Single-Year Birth-Age Top-25 All-American** tracking.

## Running Locally

From `c:\Users\j_t_v\XC`:

```powershell
python -m http.server 8765
```

Then open `http://localhost:8765/nationals/index.html`. To rebuild HTML shells after layout edits, run `python nationals/build_pages.py`.
