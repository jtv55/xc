import os

SITE_DIR = r"c:\Users\j_t_v\XC\nationals"

NAV_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>2026 CCCNYC &amp; CYO Nationals · __PAGE_TITLE__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="styles.css?v=20261121-raceday">
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
</head>
<body data-page="__PAGE_KEY__">

<nav class="sitenav">
  <span class="nav-brand">&#9670; CCCNYC / CYO '26</span>
  <a href="index.html" __CUR_HUB__>Meet Hub &amp; Course</a>
  <a href="results.html" __CUR_RESULTS__>Actuals vs. Pred</a>
  <a href="races.html" __CUR_RACES__>Race Simulator (11)</a>
  <a href="diocese.html" __CUR_DIOCESE__>Pittsburgh CYO (64)</a>
  <a href="clubs.html" __CUR_CLUBS__>Schools &amp; Clubs (91)</a>
  <a href="runners.html" __CUR_RUNNERS__>Runners &amp; Dossiers (2,617)</a>
  <span class="nav-right">
    <button id="globalScoringBtn" class="pill pill-cyo" aria-pressed="false" title="Toggle between Full National Open scoring and CYO Catholic/Diocesan scoring">Lens: National Open</button>
    <button id="themeBtn" class="pill" style="font-size:11.5px;padding:3px 9px">Theme: auto</button>
    <a href="../index.html" class="pill" style="font-size:11.5px;padding:3px 9px" title="Aquinas Academy 2026 XC Season Analytics">&#8599; Aquinas '26</a>
  </span>
</nav>

<div class="wrap">
__BODY__

  <footer class="foot">
    <div>
      <b>2026 Cross Country Coaches National Youth Championships (20th Edition) &amp; CYO Nationals</b> · Saturday, Nov 21, 2026 · Elvin R. King XC Course, Cedarville University, OH.<br>
      Updated from the official <a href="data/pdfs/Entry_List_Final_Nov20.pdf" target="_blank">Final Entry List PDF (Nov 20 + Nov 21 late add · 2,618 entries)</a>, cross-referenced against 2,227 empirical race histories (85.1% overall · 90.2% ages 9–14) across 20 states + Bermuda (10,000 Monte Carlo trials per race).
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:flex-start">
      <a class="pill" href="data/cccnyc_2026_runner_predictions.csv" download>Runner Predictions CSV</a>
      <a class="pill" href="data/cccnyc_2026_team_predictions.csv" download>Team Predictions CSV</a>
      <a class="pill" href="data/cccnyc_2026_master.json" download>Full Master JSON</a>
    </div>
  </footer>
</div>

<div id="d3Tooltip" class="d3-tip"></div>
<script src="data/data.js?v=20261121-raceday"></script>
<script src="data/us_states_geo.js?v=20261121-raceday"></script>
<script src="app.js?v=20261121-raceday"></script>__EXTRA_SCRIPTS__
</body>
</html>
"""

HUB_BODY = """
  <div class="hero">
    <div class="eyebrow">20th Annual National Youth XC &amp; CYO Championships · Pre-Race Final Forecast (Nov 21, 2026) · Cedarville, OH</div>
    <h1>2026 CCCNYC &amp; CYO National Championship Intelligence</h1>
    <p class="lede">Pre-race analytical forecast, 10,000-trial Monte Carlo simulation engine, and scouting database for today's 2,617-runner national championship at Cedarville University's Elvin R. King Cross Country Course. Switch anytime between <b>National Open Scoring</b> (all 91 organizations) and <b>CYO National Championship Scoring</b> (10 Catholic diocesan &amp; parish programs).</p>
    <div class="ctl" style="margin-bottom:0">
      <a class="pill pill-dop" aria-pressed="true" href="results.html">2026 Actuals vs. Predictions &amp; Aquinas Breakdown &#8594;</a>
      <a class="pill pill-cyo" href="data/pdfs/Aquinas_Academy_2026_CCCNYC_Post_Race_Report.pdf" target="_blank">Download Aquinas Academy Post-Race PDF (6 Pages)</a>
      <a class="pill" href="diocese.html">Pittsburgh CYO Command Center (64 Runners) &#8594;</a>
      <a class="pill" href="races.html">11-Race Simulator &#8594;</a>
      <a class="pill" href="data/pdfs/Pittsburgh_CYO_2026_CCCNYC_Race_Day_Packet.pdf" target="_blank">Pre-Race Briefing PDF (15 Pages)</a>
    </div>
  </div>

  <div class="kpis" id="hubKpis"></div>

  <section>
    <div class="split-60-40">
      <div class="card">
        <h2>National field footprint · runners by state &amp; club home cities</h2>
        <p class="sub">Darker states represent larger athlete delegations across all 20 US states (+ Bermuda inset); dots mark the home cities of all 91 clubs &amp; CYO programs (sized by runners). Hover any state or city dot for details, or click to explore.</p>
        <div class="usa-map-wrap" id="hubUsaMapChart"></div>
        <p class="so" id="hubUsaMapSo"></p>
      </div>
      <div class="card" id="officialScheduleCard"></div>
    </div>
  </section>

  <section>
    <h2>Saturday race-day schedule &amp; Monte Carlo projected podiums</h2>
    <p class="sub">All times Eastern Standard Time (Saturday, Nov 21, 2026). Note that CCCNYC awards <b>Top 3 Teams</b> per race plus <b>Top 25 Individual All-Americans per single birth-year age</b> (Ages 6, 7, 8, 9, 10, 11, 12, 13, 14, 15–16, and 17–18). Click any race card to open its full simulation.</p>
    <div class="ctl">
      <span class="ctl-label">Scoring Lens</span>
      <button class="pill lens-btn" data-lens="nat" aria-pressed="true">National Open Field (All 91 Organizations)</button>
      <button class="pill pill-cyo lens-btn" data-lens="cyo" aria-pressed="false">CYO National Championship (10 Catholic / Diocesan Programs)</button>
    </div>
    <div class="sched-grid" id="hubScheduleGrid"></div>
  </section>

  <section>
    <h2>Elvin R. King Cross Country Course · terrain, tactical splits &amp; official maps</h2>
    <p class="sub">Opened in 2006 on 150 acres of dedicated rolling grass at Cedarville University (host of NCAA DII Midwest Regionals, Atlantic-10, All-Ohio Intercollegiate, and NAIA/NCCAA Championships). Unlike tight wooded park courses, Cedarville features a massive 400m+ open grass starting straightaway before narrowing into rolling mid-race loops.</p>
    <div class="ctl" id="courseDistPills">
      <span class="ctl-label">Course Layout</span>
      <button class="pill" data-cdist="2000" aria-pressed="false">2K (Ages 6–8)</button>
      <button class="pill" data-cdist="3000" aria-pressed="true">3K (Ages 9–12)</button>
      <button class="pill" data-cdist="4000" aria-pressed="false">4K (Ages 13–14)</button>
      <button class="pill" data-cdist="5000" aria-pressed="false">5K (Ages 15–18)</button>
      <span style="margin-left:auto;display:inline-flex;gap:6px;flex-wrap:wrap">
        <a class="pill" href="data/pdfs/Cedarville_Course_1K_Map.pdf" target="_blank">1K Map PDF</a>
        <a class="pill" href="data/pdfs/Cedarville_Course_2K_Map.pdf" target="_blank">2K Map PDF</a>
        <a class="pill" href="data/pdfs/Cedarville_Course_3K_Map.pdf" target="_blank">3K Map PDF</a>
        <a class="pill" href="data/pdfs/Cedarville_Course_4K_Map.pdf" target="_blank">4K Map PDF</a>
        <a class="pill" href="data/pdfs/Cedarville_Course_5K_Map.pdf" target="_blank">5K Map PDF</a>
      </span>
    </div>
    <div class="split-60-40">
      <div class="card">
        <h3 id="courseChartTitle">Cedarville 3,000m elevation &amp; tactical pacing profile</h3>
        <div id="courseElevationChart"></div>
        <p class="so" id="courseChartSo"></p>
      </div>
      <div class="card" id="courseTacticalNotes"></div>
    </div>
  </section>

  <section>
    <div class="two">
      <div class="card">
        <h2>CCCNYC 4-year championship history &amp; returning veterans</h2>
        <p class="sub">13,540 historical finishes parsed from 2022–2025 CCCNYC archives. <b>Over 960 athletes</b> entered tomorrow are returning CCCNYC veterans with prior national championship finishes.</p>
        <div id="histEditionsChart"></div>
        <p class="so" id="histEditionsSo"></p>
      </div>
      <div class="card">
        <h2>Entry list forensic audit &amp; registration anomalies</h2>
        <p class="sub">Automated forensic cross-checks of the initial Drive draft (1,058 rows) vs the Final Nov 20 <code class="mono">Entry List.pdf</code> (+ Nov 21 late add · 2,618 entries) uncovered critical roster expansions and scoring impacts cleaned in our simulation:</p>
        <div id="anomalyAuditList"></div>
      </div>
    </div>
  </section>
"""

RACES_BODY = """
  <div class="eyebrow">10,000-Trial Monte Carlo Engine · Team Score Fans, Ridgelines, S-Curves &amp; What-If Sandbox</div>
  <h1>Race-by-Race Simulator &amp; Tactical Breakdown</h1>
  <p class="lede">Select any of the 11 championship races to inspect team win &amp; trophy probabilities, scoring pack mile-pace ridgelines, full-field rank-vs-time S-curves, pairwise head-to-head matrices, and an interactive Coach's What-If Sandbox.</p>

  <div class="ctl-bar">
    <span class="ctl-label">Select Race</span>
    <div id="raceEventPills" style="display:flex;flex-wrap:wrap;gap:5px"></div>
    <span class="ctl-label" style="margin-left:auto">Scoring Mode</span>
    <button class="pill lens-btn" data-lens="nat" aria-pressed="true">National Open</button>
    <button class="pill pill-cyo lens-btn" data-lens="cyo" aria-pressed="false">CYO National</button>
  </div>

  <div class="kpis" id="raceKpis"></div>

  <section>
    <div class="two">
      <div class="card">
        <h2 id="teamFanTitle">Projected team score distribution (P10–P90) &amp; trophy odds</h2>
        <p class="sub">Official XC displacement scoring (only Complete 5+ runner clubs assign points; 6th runner breaks ties). Bars span 10th-to-90th percentile simulated team scores.</p>
        <div id="raceTeamFanChart"></div>
        <p class="so" id="raceTeamFanSo"></p>
      </div>
      <div class="card">
        <h2>Team mile-pace density ridgelines</h2>
        <p class="sub">Projected Cedarville mile-pace curves across scoring squads. Tighter, left-shifted waves indicate faster front-running packs and superior 1–5 compression.</p>
        <div id="raceRidgeChart"></div>
        <p class="so" id="raceRidgeSo"></p>
      </div>
    </div>
  </section>

  <section>
    <div class="two">
      <div class="card">
        <h2 id="scurveRaceTitle">Projected finish S-curve &amp; traffic density</h2>
        <p class="sub">Every runner plotted by Expected Place (X) vs Projected Finish Time (Y) with P10–P90 uncertainty whiskers. Red dots highlight Diocese of Pittsburgh; purple dots mark other CYO runners.</p>
        <div id="raceScurveChart"></div>
        <p class="so" id="raceScurveSo"></p>
      </div>
      <div class="card">
        <h2 id="h2hMatrixTitle">Pairwise head-to-head team win matrix</h2>
        <p class="sub">Probability (%) that the <b>Row Team</b> defeats the <b>Column Team</b> across 10,000 simulated races (including 6th-runner tiebreakers).</p>
        <div id="raceH2hChart"></div>
        <p class="so" id="raceH2hSo"></p>
      </div>
    </div>
  </section>

  <section>
    <h2>Coach's Interactive "What-If" Tactical Sandbox</h2>
    <p class="sub">Test how a race-day pack surge (e.g., shaving 12 seconds per runner off a team's projection) or adding a 5th scorer to an incomplete 4-runner roster shifts the official XC team standings in real time.</p>
    <div class="card">
      <div class="ctl" style="gap:10px 16px">
        <div>
          <span class="ctl-label">Target Team</span>
          <select id="sandboxTeamSel" class="sel"></select>
        </div>
        <div style="display:flex;align-items:center;gap:8px">
          <span class="ctl-label">Pack Time Delta</span>
          <input type="range" id="sandboxDeltaSlider" class="range-slider" min="-30" max="30" step="1" value="0">
          <span id="sandboxDeltaVal" class="badge b-accent mono" style="min-width:56px;text-align:center">0s / rnr</span>
        </div>
        <label style="display:inline-flex;align-items:center;gap:6px;font-size:13px;cursor:pointer">
          <input type="checkbox" id="sandboxAdd5thChk">
          <span>Simulate 5th scorer if roster has 4 runners</span>
        </label>
        <button class="pill" id="sandboxResetBtn">Reset Sandbox</button>
      </div>
      <div id="sandboxStandingsWrap"></div>
    </div>
  </section>

  <section>
    <div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:10px;margin-bottom:8px">
      <div>
        <h2 id="raceRosterHeading">Complete projected finish order &amp; single-year All-American odds</h2>
        <p class="sub" style="margin-bottom:0">Click any athlete row to open their full 2026 season &amp; CCCNYC scouting dossier.</p>
      </div>
      <div class="ctl" style="margin-bottom:0">
        <span class="ctl-label">Filter Award Age</span>
        <div id="raceAgeFilterPills" style="display:inline-flex;gap:4px"></div>
        <input type="search" id="raceRunnerSearch" class="search" placeholder="Filter runner or club...">
      </div>
    </div>
    <div class="tablewrap">
      <table>
        <thead>
          <tr>
            <th class="num">Proj Pl</th>
            <th>Runner</th>
            <th>Team</th>
            <th class="num">Age</th>
            <th>Home School</th>
            <th>Seed Tier</th>
            <th class="num">Proj Time</th>
            <th class="num">P10–P90 Band</th>
            <th class="num">Pace</th>
            <th class="num">Ov Top-25%</th>
            <th class="num">Age Rk</th>
            <th class="num">Age AA Top-25%</th>
            <th class="num">Passing Lev</th>
          </tr>
        </thead>
        <tbody id="raceFinishTableBody"></tbody>
      </table>
    </div>
  </section>
"""

DIOCESE_BODY = """
  <div class="hero">
    <div class="eyebrow">Pittsburgh CYO (Diocese of Pittsburgh) · 64 Qualifiers · 13 Catholic Feeder Schools · 10 Complete Scoring Squads · 100% 2026 Season Matched</div>
    <h1>Pittsburgh CYO (Diocese of Pittsburgh) Command Center</h1>
    <p class="lede">Every single one of the <b>64 Diocese of Pittsburgh athletes</b> (officially listed as <b>Pittsburgh CYO</b>, including late race-day Boys 6–8 addition <b>Diego Victor</b>) was matched to their complete 2026 Western PA Cross Country season resume (averaging 6.2 races per athlete) and Oct 17 Diocesan Championship split—unlocking exact parish feeder pipelines, 10 complete scoring squads across all 8 youth divisions, CYO title odds against Philadelphia, Toledo, LA &amp; Columbus CYO, and single-year birth-age All-American projections.</p>
    <div class="ctl" style="margin-bottom:0">
      <a class="pill pill-dop" aria-pressed="true" href="results.html">View 2026 Actuals vs. Predictions (15 Pgh CYO All-Americans!) &#8594;</a>
      <a class="pill pill-cyo" href="data/pdfs/Aquinas_Academy_2026_CCCNYC_Post_Race_Report.pdf" target="_blank">Download Aquinas Academy Post-Race PDF (6 Pages) &#8599;</a>
      <a class="pill" href="data/pdfs/Pittsburgh_CYO_2026_CCCNYC_Race_Day_Packet.pdf" target="_blank">Pre-Race Briefing PDF (15 Pages) &#8599;</a>
    </div>
  </div>

  <div class="kpis" id="dopKpis"></div>

  <div class="callout callout-dop">
    <b>Empirical Course Calibration Discovery (Oct 17 Diocesan Championship):</b> Cross-checking Smiley Miles regular-season paces against RunSignup <code class="mono">#193936</code> revealed that while JV &amp; Varsity were timed at their true ~2,800m distance, the Developmental K–2 &amp; 3–4 races were configured in timer software at 1.35 mi (2,173m) despite running a true <b>1.50-mile (2,414m)</b> course—artificially inflating reported Developmental paces by ~44 sec/mile. Correcting Developmental to 2,414m aligned every athlete's Oct 17 pace within 2–3 seconds of their North Area, Seelos, and Aquinas Academy marks!
  </div>

  <section>
    <div class="two">
      <div class="card">
        <h2>Feeder Catholic school pipeline (all 64 qualifiers)</h2>
        <p class="sub">13 Pittsburgh Diocesan elementary/middle schools comprise the 2026 national squad, co-led by <b>St. Louise de Marillac (11)</b> and <b>Aquinas Academy (11)</b>, followed by <b>Blessed Francis Seelos (8)</b> and <b>St. Kilian (6)</b>. Click any bar or school pill below to filter.</p>
        <div id="dopSchoolsChart"></div>
        <p class="so" id="dopSchoolsSo"></p>
      </div>
      <div class="card">
        <h2>Dual-crown squad outlook: National Podium % vs. CYO Title %</h2>
        <p class="sub">Comparison of all 10 complete scoring Pittsburgh CYO rosters across all 8 youth divisions in both the Open National Field and CYO National Championship scoring.</p>
        <div id="dopSquadDualChart"></div>
        <p class="so" id="dopSquadDualSo"></p>
      </div>
    </div>
  </section>

  <section>
    <h2>Diocese squad pack compression &amp; 6th-runner displacer ladders</h2>
    <p class="sub">Projected mile pace of runners #1 through #8 on each Diocese of Pittsburgh roster. Solid circles mark the Top-5 scorers; hollow circles mark #6–#8 tiebreaker displacers.</p>
    <div class="card">
      <div id="dopPackLadderChart"></div>
      <p class="so" id="dopPackLadderSo"></p>
    </div>
  </section>

  <section>
    <h2>Single-year birth-age All-American medal board (Top 25 by age)</h2>
    <p class="sub">Because CCCNYC awards Top-25 All-American medals separately for each birth year (Ages 6, 7, 8, 9, 10, 11, 12, 13, 14), younger runners in two-year brackets (Ages 7, 9, 11, 13) compete against peers their exact age.</p>
    <div class="ctl" id="dopSchoolFilterBar"></div>
    <div class="card" style="margin-bottom:16px">
      <div id="dopAllAmericanChart"></div>
    </div>
    <div class="tablewrap">
      <table>
        <thead>
          <tr>
            <th>Runner</th>
            <th>Squad</th>
            <th>Event</th>
            <th class="num">Age</th>
            <th>Home Catholic School</th>
            <th class="num">2026 Races</th>
            <th class="num">Oct 17 Dio Pl</th>
            <th class="num">Proj Cedarville</th>
            <th class="num">Proj Pace</th>
            <th class="num">Ov Exp Pl</th>
            <th class="num">Age-Grp Rk</th>
            <th class="num">Age AA Top-25%</th>
            <th class="num">CYO Rk</th>
          </tr>
        </thead>
        <tbody id="dopRosterTableBody"></tbody>
      </table>
    </div>
  </section>
"""

CLUBS_BODY = """
  <div class="eyebrow">91 Clubs, Dioceses &amp; Schools · 20 States + Bermuda · Cross-Division Power Matrix</div>
  <h1>Schools, Clubs &amp; CYO National Cup Standings</h1>
  <p class="lede">Analyze every organization competing at Cedarville—from national youth dynasties (<b>Brocaw Blazers</b>, <b>Louisville TigerSharks</b>, <b>Body in Training</b>, <b>HP Distance</b>, <b>Team Kentucky</b>, <b>Shady Abes</b>, <b>Buckeye Racers</b>, <b>CRC Grasshoppers</b>, <b>Belvidere Tornados</b>) to the 10 Catholic diocesan &amp; parish programs battling for the CYO National Cup (<b>Phila. CYO</b>, <b>Toledo CYO</b>, <b>Pittsburgh CYO</b>, <b>LA-CYO</b>, <b>Columbus CYO</b>).</p>

  <div class="ctl-bar" id="clubFiltersBar">
    <span class="ctl-label">Category</span>
    <button class="pill" data-ccat="ALL" aria-pressed="true">All 91 Organizations</button>
    <button class="pill pill-cyo" data-ccat="CYO" aria-pressed="false">CYO / Catholic Only (10)</button>
    <button class="pill" data-ccat="Youth Club" aria-pressed="false">Youth Clubs</button>
    <button class="pill" data-ccat="School" aria-pressed="false">School Teams</button>
    <span class="ctl-label" style="margin-left:8px">State</span>
    <select id="clubStateSel" class="sel"><option value="ALL">All States (20+)</option></select>
    <input type="search" id="clubSearchInp" class="search" placeholder="Search club or city..." style="margin-left:auto">
  </div>

  <section>
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px">
        <div>
          <h2>USA runner density &amp; club home cities map</h2>
          <p class="sub" style="margin-bottom:6px">States are shaded darker by total runner count; dots mark club &amp; CYO home cities across the country (★ = Cedarville, OH venue). Click any state to filter the directory below, or click any city dot to inspect its club.</p>
        </div>
        <button class="pill" id="clubsMapResetBtn" style="display:none">Clear State Filter</button>
      </div>
      <div class="usa-map-wrap" id="clubsUsaMapChart"></div>
      <p class="so" id="clubsUsaMapSo"></p>
    </div>
  </section>

  <section>
    <div class="two">
      <div class="card">
        <h2>National program power landscape</h2>
        <p class="sub">Delegation Size (horizontal) vs. Expected Single-Year Age All-Americans (vertical); bubble radius reflects Expected National Team Podiums.</p>
        <div id="clubBubbleChart"></div>
        <p class="so" id="clubBubbleSo"></p>
      </div>
      <div class="card">
        <h2>CYO National Cup omnium projection</h2>
        <p class="sub">Aggregate head-to-head comparison across all 10 Catholic / CYO programs entered in 2026 (<code class="mono">Entry_List_Final_Nov20.pdf</code>).</p>
        <div id="cyoOmniumWrap"></div>
      </div>
    </div>
  </section>

  <section>
    <h2>Cross-division team presence &amp; projected finish rank heatmap</h2>
    <p class="sub">Top 24 multi-squad organizations across the 8 primary youth championship divisions (6–8 through 13–14) plus 15–18 5K. Numbered cells show projected team finish rank (gold = 1st, green = Top 3 Podium); <code class="mono">i</code> denotes individual entries (&lt;5 runners). Click any club row to inspect its full delegation below.</p>
    <div class="card" style="overflow-x:auto">
      <div id="clubHeatmapChart"></div>
    </div>
  </section>

  <section id="clubDetailSection">
    <div class="dossier-card" id="clubInspectorCard"></div>
  </section>

  <section>
    <h2>Complete 91-organization directory &amp; 2022–2025 CCCNYC pedigree</h2>
    <div class="tablewrap">
      <table>
        <thead>
          <tr>
            <th>Organization</th>
            <th>State</th>
            <th>Region / City</th>
            <th>Type</th>
            <th class="num">2026 Runners</th>
            <th class="num">Scoring Squads</th>
            <th class="num">Emp. Seeded</th>
            <th class="num">'22–'25 Vets</th>
            <th class="num">Exp. Team Podiums</th>
            <th class="num">Exp. Age All-Americans</th>
            <th class="num">'22–'25 CCCNYC Top-25s</th>
          </tr>
        </thead>
        <tbody id="clubsTableBody"></tbody>
      </table>
    </div>
  </section>
"""

RUNNERS_BODY = """
  <div class="eyebrow">2,617 Unique Entrants · Individual Scouting Dossiers, Age-Group Cutlines &amp; Rivalry Duels</div>
  <h1>Runner Scouting Database &amp; All-American Cutlines</h1>
  <p class="lede">Inspect individual Monte Carlo projections, scraped 2026 season race logs, 2022–2025 CCCNYC veteran resumes, single-year birth-age All-American medal cutlines, and head-to-head probability duels for every athlete in the meet.</p>

  <section id="dossierSection">
    <div class="dossier-card" id="runnerDossierCard"></div>
  </section>

  <section>
    <div class="two">
      <div class="card">
        <h2>Single-year birth-age All-American Top-25 cutline explorer</h2>
        <p class="sub">Select any single-year award ceremony to see the Top 35 contenders' P10–P90 projected finish ranges relative to the dashed <b>#25 All-American Medal Cutline</b>.</p>
        <div class="ctl">
          <span class="ctl-label">Award Ceremony</span>
          <select id="cutlineGroupSel" class="sel"></select>
        </div>
        <div id="ageCutlineChart"></div>
        <p class="so" id="ageCutlineSo"></p>
      </div>
      <div class="card">
        <h2>Head-to-head runner duel &amp; density comparator</h2>
        <p class="sub">Pick any two athletes in the same race to compute exact win probability <code class="mono">P(A beats B)</code>, expected time gap, and overlapping finish-time distributions.</p>
        <div class="ctl">
          <select id="duelEventSel" class="sel"></select>
        </div>
        <div class="ctl">
          <select id="duelRunnerASel" class="sel" style="max-width:48%"></select>
          <span class="mono muted">vs</span>
          <select id="duelRunnerBSel" class="sel" style="max-width:48%"></select>
        </div>
        <div id="duelChart"></div>
        <p class="so" id="duelSo"></p>
      </div>
    </div>
  </section>

  <section>
    <h2>Search &amp; filter all 2,617 national entrants</h2>
    <div class="ctl-bar">
      <input type="search" id="globalRunnerSearch" class="search" placeholder="Search name, club, or feeder school..." style="min-width:230px">
      <select id="fltEventSel" class="sel"><option value="ALL">All 11 Events</option></select>
      <select id="fltAgeSel" class="sel"><option value="ALL">All Ages (1–18)</option></select>
      <select id="fltTierSel" class="sel">
        <option value="ALL">All Seed Tiers</option>
        <option value="EMP">Verified Empirical (2026 / Vet)</option>
        <option value="2026">2026 Race Log Verified</option>
        <option value="VET">CCCNYC Returning Veteran</option>
      </select>
      <button class="pill pill-dop" id="fltDopBtn" aria-pressed="false">Pittsburgh CYO (64)</button>
      <button class="pill" id="fltAquinasBtn" aria-pressed="false">Aquinas Academy (11)</button>
      <button class="pill pill-cyo" id="fltCyoBtn" aria-pressed="false">All CYO (490)</button>
    </div>
    <p class="sub" id="runnerCountSummary"></p>
    <div class="tablewrap">
      <table>
        <thead>
          <tr>
            <th>Runner</th>
            <th>Event</th>
            <th class="num">Age</th>
            <th>Club / Team</th>
            <th>Home School / City</th>
            <th>Seed Source</th>
            <th class="num">'26 Races</th>
            <th class="num">Proj Time</th>
            <th class="num">Pace</th>
            <th class="num">Ov Exp Pl</th>
            <th class="num">Age Rk</th>
            <th class="num">Age AA%</th>
          </tr>
        </thead>
        <tbody id="allRunnersTableBody"></tbody>
      </table>
    </div>
  </section>
"""

RESULTS_BODY = """
  <div class="hero">
    <div class="eyebrow">Official FinishTiming Results (Meet #10720716) vs. Frozen Pre-Race Snapshot (pre-race-2026-11-21)</div>
    <h1>2026 Cedarville Actuals vs. Predictions &amp; Aquinas Academy Breakdown</h1>
    <p class="lede">Auditing our 10,000-trial pre-race Monte Carlo forecast against all <b>2,441 official Cedarville finishers</b> (<b>2,424 matched · 99.3%</b>). Highlighting <b>Aquinas Academy's 11/11 finishers</b> (3 National All-Americans, <b>-24.0s</b> median beat!), <b>Diego Victor's #9 Age-6 All-American medal &amp; CYO Trophy finish</b>, <b>Marcela Victor's -24.0s / +35-place 3K breakthrough</b>, and our <b>8-for-8 (100%) CYO National Team Champion</b> call!</p>
    <div class="ctl" style="margin-bottom:0">
      <a class="pill pill-dop" aria-pressed="true" href="data/pdfs/Aquinas_Academy_2026_CCCNYC_Post_Race_Report.pdf" target="_blank">Download Aquinas Academy Post-Race PDF Report (6 Pages) &#8599;</a>
      <a class="pill" href="https://finishtiming.trackscoreboard.com/meets/10720716/events" target="_blank">Official FinishTiming Results &#8599;</a>
      <a class="pill" href="data/actuals_2026/predicted_vs_actual_2026.json" download>Download Full Actuals vs. Pred JSON</a>
    </div>
  </div>

  <div class="kpis" id="resKpis"></div>

  <section>
    <h2>Diego &amp; Marcela Victor — 2026 season progression into Cedarville Nationals</h2>
    <p class="sub">Hover any meet dot to inspect exact date, distance, time, pace, and finish. Green circle marks today's Cedarville National Championship PR; dashed blue line shows our frozen pre-race forecast with P10–P90 band.</p>
    <div class="two">
      <div class="card">
        <h3>Diego Victor (Age 6 · Boys 6–8 2K) · <span class="dop-txt">#9 National All-American!</span></h3>
        <p class="sub"><b>9:22.4 (7:33/mi)</b> · <b>-23.9s faster than forecast</b> · <b>-18.5s 2K PR</b> · Age-6 <b>#9 / 36</b> (#3 CYO Age-6) · Completed Pittsburgh CYO's 5-runner squad for a <b>56–56 tie for 2nd / #3 CYO Trophy!</b></p>
        <div id="diegoPaceChart"></div>
      </div>
      <div class="card">
        <h3>Marcela Victor (Age 9 · Girls 9–10 3K) · <span style="color:var(--up)">-24.0s &amp; +35-Place Surge!</span></h3>
        <p class="sub"><b>14:37.7 (7:51/mi)</b> · <b>-24.0s faster than forecast</b> · <b>-1:05.3 3K PR</b> (vs 15:43 Sept 12) · Ov <b>#144 / 244</b> (up +35.1 places!) · Age-9 <b>#57 / 104</b> (#14 CYO Age-9) · Displaced Toledo A #5–7!</p>
        <div id="marcelaPaceChart"></div>
      </div>
    </div>
  </section>

  <section>
    <h2>Aquinas Academy (all 11 finishers) — forecast beat chart</h2>
    <p class="sub">Negative bars = ran <b>faster</b> than our pre-race projection. Notice how 9 of 11 Aquinas runners crushed their forecast by a median of <b>-24.0 seconds</b> while the rest of the nation ran <b>+8.6s slower</b>! Hover any bar for full Pred vs. Actual breakdown.</p>
    <div class="card">
      <div id="aqBeatChart"></div>
    </div>
  </section>

  <section>
    <div class="two">
      <div class="card">
        <h2>All 2,424 matched finishers · predicted vs. actual scatter</h2>
        <div class="ctl" id="scatGroupPills" style="margin-bottom:8px">
          <button class="pill" data-grp="ALL" aria-pressed="true">All 2,424</button>
          <button class="pill pill-dop" data-grp="AQ" aria-pressed="false">Aquinas (11)</button>
          <button class="pill pill-dop" data-grp="DOP" aria-pressed="false">Pgh CYO (63)</button>
          <button class="pill pill-cyo" data-grp="CYO" aria-pressed="false">All CYO</button>
          <button class="pill" data-grp="AA" aria-pressed="false">All-Americans</button>
          <select id="scatEventSel" class="sel" style="margin-left:auto"></select>
        </div>
        <div id="pvaScatterChart"></div>
        <p class="so" id="pvaScatterSo"></p>
      </div>
      <div class="card">
        <h2>The Western PA hill-strength effect · residual density</h2>
        <p class="sub">Comparing Actual minus Predicted finish times (seconds) across the Rest of the Nation (<b>+8.6s</b>), Pittsburgh CYO (<b>-18.7s</b>), and Aquinas Academy (<b>-24.0s</b>) — a <b>32.6-second swing</b> proving Western PA's hilly XC courses forged fast grass racers!</p>
        <div id="wpaResidualChart"></div>
      </div>
    </div>
  </section>

  <section>
    <h2>8-for-8 CYO National Champions &amp; all 10 Pittsburgh CYO squads</h2>
    <p class="sub">Every single one of Pittsburgh CYO's 10 squads beat its National Open rank projection, 9 of 10 earned CYO National Top-3 Podiums (including 2 CYO National Championships!), and our pre-race model nailed <b>8 of 8 CYO National Team Champions</b>.</p>
    <div class="tablewrap">
      <table>
        <thead>
          <tr>
            <th>Division</th>
            <th>Pittsburgh CYO Squad</th>
            <th class="num">National Open (Pred &#8594; Act)</th>
            <th class="num">CYO National (Pred &#8594; Act)</th>
            <th class="num">CYO Result</th>
            <th>CYO Champion (Pred = Act)</th>
          </tr>
        </thead>
        <tbody id="cyoAuditTableBody"></tbody>
      </table>
    </div>
  </section>

  <section>
    <h2>Searchable Predicted vs. Actual results explorer</h2>
    <div class="ctl-bar">
      <div id="tblScopePills" style="display:inline-flex;gap:5px;flex-wrap:wrap">
        <button class="pill pill-dop" data-scope="AQ" aria-pressed="true">Aquinas Academy (11)</button>
        <button class="pill pill-dop" data-scope="DOP" aria-pressed="false">Pittsburgh CYO (63)</button>
        <button class="pill" data-scope="AA" aria-pressed="false">All-Americans</button>
        <button class="pill" data-scope="ALL" aria-pressed="false">All 2,424 Finishers</button>
      </div>
      <select id="tblEventSel" class="sel"></select>
      <input type="search" id="pvaSearchInp" class="search" placeholder="Search runner, club, or school..." style="margin-left:auto">
    </div>
    <p class="sub" id="pvaTableCount"></p>
    <div class="tablewrap">
      <table>
        <thead>
          <tr>
            <th>Runner</th>
            <th>Race</th>
            <th class="num">Age</th>
            <th>Club / Team</th>
            <th>School</th>
            <th class="num">Pred Time</th>
            <th class="num">Act Time (Pace)</th>
            <th class="num">Δt</th>
            <th class="num">Overall Pl</th>
            <th class="num">Age Pl</th>
          </tr>
        </thead>
        <tbody id="pvaTableBody"></tbody>
      </table>
    </div>
  </section>
"""

pages = [
    ("index.html", "hub", "Meet Hub & Predictions", HUB_BODY, ""),
    ("results.html", "results", "2026 Actuals vs. Predictions & Aquinas Breakdown", RESULTS_BODY,
     '\n<script src="data/actuals_2026/actuals_data.js?v=20261121-actuals"></script>\n<script src="results.js?v=20261121-actuals"></script>'),
    ("races.html", "races", "Race Simulator (11 Divisions)", RACES_BODY, ""),
    ("diocese.html", "diocese", "Diocese of Pittsburgh Command Center", DIOCESE_BODY, ""),
    ("clubs.html", "clubs", "Schools, Clubs & CYO Standings", CLUBS_BODY, ""),
    ("runners.html", "runners", "Runner Scouting Dossiers", RUNNERS_BODY, ""),
]

for fname, key, title, body, extra in pages:
    html = (
        NAV_TEMPLATE
        .replace("__PAGE_TITLE__", title)
        .replace("__PAGE_KEY__", key)
        .replace("__CUR_HUB__", 'aria-current="page"' if key == "hub" else "")
        .replace("__CUR_RESULTS__", 'aria-current="page"' if key == "results" else "")
        .replace("__CUR_RACES__", 'aria-current="page"' if key == "races" else "")
        .replace("__CUR_DIOCESE__", 'aria-current="page"' if key == "diocese" else "")
        .replace("__CUR_CLUBS__", 'aria-current="page"' if key == "clubs" else "")
        .replace("__CUR_RUNNERS__", 'aria-current="page"' if key == "runners" else "")
        .replace("__BODY__", body)
        .replace("__EXTRA_SCRIPTS__", extra)
    )
    with open(os.path.join(SITE_DIR, fname), "w", encoding="utf-8") as f:
        f.write(html)
    print("Generated", fname)
