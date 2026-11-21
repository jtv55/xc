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
<link rel="stylesheet" href="styles.css?v=20261120-v4">
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
</head>
<body data-page="__PAGE_KEY__">

<nav class="sitenav">
  <span class="nav-brand">&#9670; CCCNYC / CYO '26</span>
  <a href="index.html" __CUR_HUB__>Meet Hub &amp; Course</a>
  <a href="races.html" __CUR_RACES__>Race Simulator (8)</a>
  <a href="diocese.html" __CUR_DIOCESE__>Pittsburgh CYO (54)</a>
  <a href="clubs.html" __CUR_CLUBS__>Schools &amp; Clubs (90)</a>
  <a href="runners.html" __CUR_RUNNERS__>Runners &amp; Dossiers (2,133)</a>
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
      Dashboard scoped to <b>Ages 9–18 (8 championship races · 2,133 runners · 1,886 / 88.4% empirical seeds)</b> from the official <a href="data/pdfs/Entry_List_Final_Nov20.pdf" target="_blank">Final Entry List PDF (Nov 20)</a>; full 11-event archive preserved in downloadable CSV/JSON exports (10,000 Monte Carlo trials per race).
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:flex-start">
      <a class="pill" href="data/cccnyc_2026_runner_predictions.csv" download>Runner Predictions CSV</a>
      <a class="pill" href="data/cccnyc_2026_team_predictions.csv" download>Team Predictions CSV</a>
      <a class="pill" href="data/cccnyc_2026_master.json" download>Full Master JSON</a>
    </div>
  </footer>
</div>

<div id="d3Tooltip" class="d3-tip"></div>
<script src="data/data.js?v=20261120-v4"></script>
<script src="app.js?v=20261120-v4"></script>
</body>
</html>
"""

HUB_BODY = """
  <div class="hero">
    <div class="eyebrow">20th Annual National Youth XC &amp; CYO Championships · Ages 9–18 Championship View · Race Day Nov 21, 2026 · Cedarville, OH</div>
    <h1>2026 CCCNYC &amp; CYO National Championship Intelligence</h1>
    <p class="lede">Final race-eve analytical preview, 10,000-trial Monte Carlo simulation engine, and scouting database for tomorrow's <b>2,133-runner Ages 9–18 national championship</b> (8 championship divisions; young tier ages 8 &amp; under filtered out of the dashboard) at Cedarville University's Elvin R. King Cross Country Course. Switch anytime between <b>National Open Scoring</b> (all 90 organizations) and <b>CYO National Championship Scoring</b> (10 Catholic diocesan &amp; parish programs).</p>
    <div class="ctl" style="margin-bottom:0">
      <a class="pill pill-dop" aria-pressed="true" href="diocese.html">Explore Pittsburgh CYO Command Center (54 Runners) &#8594;</a>
      <a class="pill" href="races.html">Interactive 8-Race Simulator &amp; Coach's Sandbox &#8594;</a>
      <a class="pill" href="runners.html">Search All 2,133 Athlete Scouting Dossiers &#8594;</a>
      <a class="pill" href="data/pdfs/Entry_List_Final_Nov20.pdf" target="_blank">View Final Entry List PDF (31 Pages)</a>
    </div>
  </div>

  <div class="kpis" id="hubKpis"></div>

  <section>
    <h2>Saturday race-day schedule &amp; Monte Carlo projected podiums</h2>
    <p class="sub">All times Eastern Standard Time (Saturday, Nov 21, 2026). Showing all <b>8 championship divisions (Ages 9–18)</b>. Note that CCCNYC awards <b>Top 3 Teams</b> per race plus <b>Top 25 Individual All-Americans per birth-year award group</b> (Ages 9, 10, 11, 12, 13, 14, 15–16, and 17–18). Click any race card to open its full simulation.</p>
    <div class="ctl">
      <span class="ctl-label">Scoring Lens</span>
      <button class="pill lens-btn" data-lens="nat" aria-pressed="true">National Open Field (All 90 Organizations)</button>
      <button class="pill pill-cyo lens-btn" data-lens="cyo" aria-pressed="false">CYO National Championship (10 Catholic / Diocesan Programs)</button>
    </div>
    <div class="sched-grid" id="hubScheduleGrid"></div>
  </section>

  <section>
    <h2>Elvin R. King Cross Country Course · terrain, tactical splits &amp; official maps</h2>
    <p class="sub">Opened in 2006 on 150 acres of dedicated rolling grass at Cedarville University (host of NCAA DII Midwest Regionals, Atlantic-10, All-Ohio Intercollegiate, and NAIA/NCCAA Championships). Unlike tight wooded park courses, Cedarville features a massive 400m+ open grass starting straightaway before narrowing into rolling mid-race loops.</p>
    <div class="ctl" id="courseDistPills">
      <span class="ctl-label">Course Layout</span>
      <button class="pill" data-cdist="3000" aria-pressed="true">3K (Ages 9–12)</button>
      <button class="pill" data-cdist="4000" aria-pressed="false">4K (Ages 13–14)</button>
      <button class="pill" data-cdist="5000" aria-pressed="false">5K (Ages 15–18)</button>
      <span style="margin-left:auto;display:inline-flex;gap:6px;flex-wrap:wrap">
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
        <p class="sub">13,540 historical finishes parsed from 2022–2025 CCCNYC archives. <b>878 Ages 9–18 athletes</b> entered tomorrow are returning CCCNYC veterans with prior national championship finishes.</p>
        <div id="histEditionsChart"></div>
        <p class="so" id="histEditionsSo"></p>
      </div>
      <div class="card">
        <h2>Entry list forensic audit &amp; registration anomalies</h2>
        <p class="sub">Automated forensic cross-checks of the initial Drive draft vs the Final Nov 20 <code class="mono">Entry List.pdf</code> (filtered to Ages 9–18 for this dashboard; full 2,617-row archive intact in exports):</p>
        <div id="anomalyAuditList"></div>
      </div>
    </div>
  </section>
"""

RACES_BODY = """
  <div class="eyebrow">10,000-Trial Monte Carlo Engine · Ages 9–18 (8 Championship Races) · Team Score Fans, Ridgelines &amp; Sandbox</div>
  <h1>Race-by-Race Simulator &amp; Tactical Breakdown</h1>
  <p class="lede">Select any of the 8 Ages 9–18 championship races to inspect team win &amp; trophy probabilities, scoring pack mile-pace ridgelines, full-field rank-vs-time S-curves, pairwise head-to-head matrices, and an interactive Coach's What-If Sandbox.</p>

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
        <p class="sub">Every runner plotted by Expected Place (X) vs Projected Finish Time (Y) with P10–P90 uncertainty whiskers. Red dots highlight Pittsburgh CYO; purple dots mark other CYO runners.</p>
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
    <div class="eyebrow">Pittsburgh CYO (Diocese of Pittsburgh) · Ages 9–14 View · 54 Qualifiers · 8 Complete Squads · 13 Catholic Feeder Schools · 100% Matched</div>
    <h1>Pittsburgh CYO (Diocese of Pittsburgh) Command Center</h1>
    <p class="lede">Every single one of the <b>54 Ages 9–14 Pittsburgh CYO athletes</b> (8 complete 6–8 runner scoring squads across 9–10, 11–12, and 13–14 divisions; ages 8 &amp; under filtered out of the dashboard) was matched to their complete 2026 Western PA Cross Country season resume and Oct 17 Diocesan Championship split—unlocking exact parish feeder pipelines, A/B squad compression ladders, CYO title odds against Philadelphia, Toledo, LA &amp; Columbus CYO, and single-year birth-age All-American projections.</p>
  </div>

  <div class="kpis" id="dopKpis"></div>

  <div class="callout callout-dop">
    <b>Empirical Course Calibration Discovery (Oct 17 Diocesan Championship):</b> Cross-checking Smiley Miles regular-season paces against RunSignup <code class="mono">#193936</code> revealed that while JV &amp; Varsity were timed at their true ~2,800m distance, the Developmental 3rd–4th grade race (including our 9–10 age-group runners) was configured in timer software at 1.35 mi (2,173m) despite running a true <b>1.50-mile (2,414m)</b> course—artificially inflating reported paces by ~44 sec/mile. Correcting Developmental to 2,414m aligned every athlete's Oct 17 pace within 2–3 seconds of their North Area, Seelos, and Aquinas Academy marks!
  </div>

  <section>
    <div class="two">
      <div class="card">
        <h2>Feeder Catholic school pipeline (54 Ages 9–14 qualifiers)</h2>
        <p class="sub">All 13 Pittsburgh Diocesan elementary/middle schools remain represented in the Ages 9–14 delegation, led by <b>St. Louise de Marillac (11)</b>, <b>Aquinas Academy (9)</b>, <b>Blessed Francis Seelos (8)</b>, and <b>St. Kilian (6)</b>. Click any bar or school pill below to filter.</p>
        <div id="dopSchoolsChart"></div>
        <p class="so" id="dopSchoolsSo"></p>
      </div>
      <div class="card">
        <h2>Dual-crown squad outlook: National Podium % vs. CYO Title %</h2>
        <p class="sub">Comparison of all 8 complete scoring Pittsburgh CYO rosters (Ages 9–10 through 13–14) in both the Open National Field and CYO National Championship scoring.</p>
        <div id="dopSquadDualChart"></div>
        <p class="so" id="dopSquadDualSo"></p>
      </div>
    </div>
  </section>

  <section>
    <h2>Diocese squad pack compression &amp; 6th-runner displacer ladders</h2>
    <p class="sub">Projected mile pace of runners #1 through #8 on each Pittsburgh CYO roster. Solid circles mark the Top-5 scorers; hollow circles mark #6–#8 tiebreaker displacers.</p>
    <div class="card">
      <div id="dopPackLadderChart"></div>
      <p class="so" id="dopPackLadderSo"></p>
    </div>
  </section>

  <section>
    <h2>Single-year birth-age All-American medal board (Top 25 by age)</h2>
    <p class="sub">Because CCCNYC awards Top-25 All-American medals separately for each birth year (Ages 9, 10, 11, 12, 13, 14), younger runners in two-year brackets (Ages 9, 11, 13) compete against peers their exact age.</p>
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
  <div class="eyebrow">90 Clubs, Dioceses &amp; Schools (Ages 9–18 View) · 19 States + Bermuda · Cross-Division Power Matrix</div>
  <h1>Schools, Clubs &amp; CYO National Cup Standings</h1>
  <p class="lede">Analyze every Ages 9–18 organization competing at Cedarville—from national youth dynasties (<b>Brocaw Blazers</b>, <b>Louisville TigerSharks</b>, <b>Body in Training</b>, <b>HP Distance</b>, <b>Team Kentucky</b>, <b>Shady Abes</b>, <b>Buckeye Racers</b>, <b>CRC Grasshoppers</b>, <b>Belvidere Tornados</b>) to the 10 Catholic diocesan &amp; parish programs battling for the CYO National Cup (<b>Phila. CYO</b>, <b>Toledo CYO</b>, <b>Pittsburgh CYO</b>, <b>LA-CYO</b>, <b>Columbus CYO</b>).</p>

  <div class="ctl-bar" id="clubFiltersBar">
    <span class="ctl-label">Category</span>
    <button class="pill" data-ccat="ALL" aria-pressed="true">All 90 Organizations</button>
    <button class="pill pill-cyo" data-ccat="CYO" aria-pressed="false">CYO / Catholic Only (10)</button>
    <button class="pill" data-ccat="Youth Club" aria-pressed="false">Youth Clubs</button>
    <button class="pill" data-ccat="School" aria-pressed="false">School Teams</button>
    <span class="ctl-label" style="margin-left:8px">State</span>
    <select id="clubStateSel" class="sel"><option value="ALL">All States (19+)</option></select>
    <input type="search" id="clubSearchInp" class="search" placeholder="Search club or city..." style="margin-left:auto">
  </div>

  <section>
    <div class="two">
      <div class="card">
        <h2>National program power landscape</h2>
        <p class="sub">Delegation Size (horizontal) vs. Expected Single-Year Age All-Americans (vertical); bubble radius reflects Expected National Team Podiums (Ages 9–18 divisions).</p>
        <div id="clubBubbleChart"></div>
        <p class="so" id="clubBubbleSo"></p>
      </div>
      <div class="card">
        <h2>CYO National Cup omnium projection</h2>
        <p class="sub">Aggregate head-to-head comparison across all 10 Catholic / CYO programs in Ages 9–18 divisions (<code class="mono">Entry_List_Final_Nov20.pdf</code>).</p>
        <div id="cyoOmniumWrap"></div>
      </div>
    </div>
  </section>

  <section>
    <h2>Cross-division team presence &amp; projected finish rank heatmap</h2>
    <p class="sub">Top 24 multi-squad organizations across the 6 core youth championship divisions (9–10 through 13–14) plus 15–18 5K. Numbered cells show projected team finish rank (gold = 1st, green = Top 3 Podium); <code class="mono">i</code> denotes individual entries (&lt;5 runners). Click any club row to inspect its full delegation below.</p>
    <div class="card" style="overflow-x:auto">
      <div id="clubHeatmapChart"></div>
    </div>
  </section>

  <section id="clubDetailSection">
    <div class="dossier-card" id="clubInspectorCard"></div>
  </section>

  <section>
    <h2>Complete 90-organization directory &amp; 2022–2025 CCCNYC pedigree</h2>
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
  <div class="eyebrow">2,133 Unique Entrants (Ages 9–18 View) · Individual Scouting Dossiers, Age-Group Cutlines &amp; Rivalry Duels</div>
  <h1>Runner Scouting Database &amp; All-American Cutlines</h1>
  <p class="lede">Inspect individual Monte Carlo projections, scraped 2026 season race logs, 2022–2025 CCCNYC veteran resumes, single-year birth-age All-American medal cutlines, and head-to-head probability duels for every Ages 9–18 athlete in the meet.</p>

  <section id="dossierSection">
    <div class="dossier-card" id="runnerDossierCard"></div>
  </section>

  <section>
    <div class="two">
      <div class="card">
        <h2>Single-year birth-age All-American Top-25 cutline explorer</h2>
        <p class="sub">Select any single-year award ceremony (Ages 9–14) to see the Top 35 contenders' P10–P90 projected finish ranges relative to the dashed <b>#25 All-American Medal Cutline</b>.</p>
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
    <h2>Search &amp; filter all 2,133 Ages 9–18 national entrants</h2>
    <div class="ctl-bar">
      <input type="search" id="globalRunnerSearch" class="search" placeholder="Search name, club, or feeder school..." style="min-width:230px">
      <select id="fltEventSel" class="sel"><option value="ALL">All 8 Events</option></select>
      <select id="fltAgeSel" class="sel"><option value="ALL">All Ages (9–18)</option></select>
      <select id="fltTierSel" class="sel">
        <option value="ALL">All Seed Tiers</option>
        <option value="EMP">Verified Empirical (2026 / Vet)</option>
        <option value="2026">2026 Race Log Verified</option>
        <option value="VET">CCCNYC Returning Veteran</option>
      </select>
      <button class="pill pill-dop" id="fltDopBtn" aria-pressed="false">Pittsburgh CYO (54)</button>
      <button class="pill" id="fltAquinasBtn" aria-pressed="false">Aquinas Academy (9)</button>
      <button class="pill pill-cyo" id="fltCyoBtn" aria-pressed="false">All CYO (366)</button>
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

pages = [
    ("index.html", "hub", "Meet Hub & Predictions", HUB_BODY),
    ("races.html", "races", "Race Simulator (8 Divisions)", RACES_BODY),
    ("diocese.html", "diocese", "Pittsburgh CYO Command Center", DIOCESE_BODY),
    ("clubs.html", "clubs", "Schools, Clubs & CYO Standings", CLUBS_BODY),
    ("runners.html", "runners", "Runner Scouting Dossiers", RUNNERS_BODY),
]

for fname, key, title, body in pages:
    html = (
        NAV_TEMPLATE
        .replace("__PAGE_TITLE__", title)
        .replace("__PAGE_KEY__", key)
        .replace("__CUR_HUB__", 'aria-current="page"' if key == "hub" else "")
        .replace("__CUR_RACES__", 'aria-current="page"' if key == "races" else "")
        .replace("__CUR_DIOCESE__", 'aria-current="page"' if key == "diocese" else "")
        .replace("__CUR_CLUBS__", 'aria-current="page"' if key == "clubs" else "")
        .replace("__CUR_RUNNERS__", 'aria-current="page"' if key == "runners" else "")
        .replace("__BODY__", body)
    )
    with open(os.path.join(SITE_DIR, fname), "w", encoding="utf-8") as f:
        f.write(html)
    print("Generated", fname)
