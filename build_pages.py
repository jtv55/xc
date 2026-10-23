TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="claude:viewport-fit-sides" content="cover">
<title>Aquinas Academy XC · __TITLE__</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600&display=swap">
<link rel="stylesheet" href="styles.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
</head>
<body>

<nav class="sitenav" style="position:sticky;top:0;z-index:1000;background:var(--bg,Canvas);font:13px/1.4 system-ui,sans-serif;display:flex;flex-wrap:nowrap;white-space:nowrap;overflow-x:auto;scrollbar-width:none;gap:6px 14px;padding:10px max(16px,env(safe-area-inset-left,0px));border-bottom:1px solid #8884;align-items:center">
  <a href="index.html" data-tab="overall" __CUR_OVERALL__>Overall</a>
  <a href="schools.html" data-tab="schools" __CUR_SCHOOLS__>Schools</a>
  <a href="team.html" data-tab="team" __CUR_TEAM__>Aquinas Team</a>
  <a href="runners.html" data-tab="runners" __CUR_RUNNERS__>Runners</a>
  <span style="margin-left:auto;display:inline-flex;gap:8px;align-items:center">
    <button id="themeBtn" class="pill" style="font-size:11px;padding:1px 8px">Theme: auto</button>
  </span>
</nav>

<div class="wrap">
  <!-- Shared Global Division/Gender Filter Bar (used on Overall, Aquinas Team, Runners) -->
  <div class="ctl" id="globalFilters" style="margin-bottom:18px">
    <span class="ctl-label">Division</span>
    <button class="pill" data-scope="ALL" aria-pressed="true">All 4 divisions</button>
    <button class="pill" data-scope="HS Varsity (9-12)" aria-pressed="false">HS Varsity (9–12)</button>
    <button class="pill" data-scope="MS Varsity (7-8)" aria-pressed="false">MS Varsity (7–8)</button>
    <button class="pill" data-scope="Elementary JV (5-6)" aria-pressed="false">Elementary JV (5–6)</button>
    <button class="pill" data-scope="Developmental (K-4)" aria-pressed="false">Developmental (K–4)</button>
    <span class="ctl-label" style="margin-left:8px">Gender</span>
    <button class="pill" data-gend="ALL" aria-pressed="true">Both</button>
    <button class="pill" data-gend="Boys" aria-pressed="false">Boys</button>
    <button class="pill" data-gend="Girls" aria-pressed="false">Girls</button>
  </div>

  <!-- ======================================================================
       TAB 1: OVERALL
       ====================================================================== -->
  <div id="tab-overall" class="tab-pane __ACT_OVERALL__">
    <div class="eyebrow">Overall · 2026 season overview &amp; race calendar · Oct 23, 2026</div>
    <h1>2026 Cross Country Season Overview &amp; Race Calendar</h1>
    <p class="lede">All ten meets where Aquinas Academy competed in 2026 across High School WPIAL Class A (9–12) and K–8 Diocesan divisions. Explore the race calendar, winning teams and top-three podium finishers by division, course pace density ridgelines, and race S-curves.</p>

    <div class="kpis" id="kpisOverall"></div>

    <section>
      <h2>2026 season race calendar &amp; winners by division</h2>
      <p class="sub">Highlighted dates mark the ten 2026 meets on Smiley Miles. Click any highlighted calendar date (or meet pill) to filter the division tiles below, showing the winning school team and top 3 individual finishers for each division.</p>
      <div class="cal-months" id="calendarGrid"></div>
      <div class="ctl" id="calMeetPills"></div>
      <div id="meetDivisionTiles"></div>
    </section>

    <section>
      <h2>Pace density ridgelines across the 2026 season</h2>
      <p class="sub">Smooth kernel density waves showing where finisher mile paces cluster. Dashed vertical lines and peak labels mark each group's median pace.</p>
      <div class="ctl">
        <span class="ctl-label">Group ridges by</span>
        <button class="pill" data-rmode="meets" aria-pressed="true">10 Meets / Courses</button>
        <button class="pill" data-rmode="divisions" aria-pressed="false">Divisions &amp; Gender</button>
      </div>
      <div class="card">
        <div id="overallRidgeChart"></div>
        <p class="so" id="overallRidgeSo"></p>
      </div>
    </section>

    <section>
      <h2>Race rank vs. finish time S-curve &amp; passing leverage</h2>
      <p class="sub">Every finisher in the selected race plotted by Rank (horizontal) versus Finish Time (vertical). Flat plateaus reveal dense packs where shaving 15 seconds gains the most places.</p>
      <div class="ctl">
        <select id="raceSelect" class="sel" style="max-width:100%"></select>
        <button class="pill" id="onlyAqBtn" aria-pressed="true">Table below: Aquinas only</button>
      </div>
      <div class="two" style="margin-bottom:12px">
        <div class="card">
          <h3 id="scurveTitle">Rank vs. finish time S-curve</h3>
          <div id="raceChart"></div>
          <p class="so" id="race-so"></p>
        </div>
        <div class="card">
          <h3>What 15 seconds faster buys each Aquinas runner</h3>
          <div id="leverageChart"></div>
          <p class="so" id="leverage-so"></p>
        </div>
      </div>
      <div class="tablewrap">
        <table class="t">
          <thead>
            <tr>
              <th class="num">Place</th>
              <th class="num">Team #</th>
              <th>Runner</th>
              <th>Team</th>
              <th class="num">Gr</th>
              <th class="num">Bib</th>
              <th class="num">Time</th>
              <th class="num">Pace</th>
              <th class="num">Back</th>
              <th class="num">Field %</th>
              <th class="num">-15s Gains</th>
            </tr>
          </thead>
          <tbody id="raceTableBody"></tbody>
        </table>
      </div>
    </section>

    <section>
      <h2>What moved in 2026</h2>
      <div class="card" id="movesList"></div>
    </section>

    <section>
      <h2>Structured dataset downloads</h2>
      <div class="card">
        <div class="ctl" style="margin-bottom:0">
          <a class="pill" href="data/aquinas_2026_performances.csv" download>Download performances CSV (610 rows)</a>
          <a class="pill" href="data/aquinas_2026_team_scores.csv" download>Download team scores CSV (50 rows)</a>
          <a class="pill" href="data/aquinas_2026_full.json" download>Download full JSON dataset</a>
          <a class="pill" href="https://github.com/jtv55/xc" target="_blank" rel="noopener">GitHub repository (jtv55/xc)</a>
        </div>
      </div>
    </section>
  </div>

  <!-- ======================================================================
       TAB 2: SCHOOLS
       ====================================================================== -->
  <div id="tab-schools" class="tab-pane __ACT_SCHOOLS__">
    <div class="eyebrow">Schools · head-to-head matrix &amp; scoring composition · Oct 23, 2026</div>
    <h1>School Team Rankings Heatmap &amp; Scoring Runner Composition</h1>
    <p class="lede">Every school that competed in Aquinas Academy's races across the 2026 season. Filter by division and gender to compare team finish rankings across every meet, and click any cell to inspect the exact five runners whose points made up that school's team score.</p>

    <div class="ctl">
      <span class="ctl-label">Division</span>
      <button class="pill" data-sdiv="HS Varsity (9-12)" aria-pressed="false">HS Varsity (9–12)</button>
      <button class="pill" data-sdiv="MS Varsity (7-8)" aria-pressed="true">MS Varsity (7–8)</button>
      <button class="pill" data-sdiv="Elementary JV (5-6)" aria-pressed="false">Elementary JV (5–6)</button>
      <button class="pill" data-sdiv="Developmental (K-4)" aria-pressed="false">Developmental (K–4)</button>
      <span class="ctl-label" style="margin-left:8px">Gender</span>
      <button class="pill" data-sgend="Boys" aria-pressed="true">Boys</button>
      <button class="pill" data-sgend="Girls" aria-pressed="false">Girls</button>
    </div>

    <div class="note"><b>How to read this.</b> Rows are competing schools (sorted by average team finish rank); columns are the chronological races in the selected division. Cells show <b>#Rank (Team Points)</b>—where lower points win in cross country—or <b>Inc (n)</b> when a school had fewer than 5 finishers. Click any cell in the heatmap to load that school and race's runner-by-runner point composition below.</div>

    <section>
      <h2>Schools &times; races team ranking heatmap</h2>
      <div class="card">
        <div id="schoolsHeatmap"></div>
        <p class="so" id="schoolsHeatmapSo"></p>
      </div>
    </section>

    <section>
      <h2>Scoring runner composition: who contributed the points?</h2>
      <p class="sub">Selected race: <b id="compRaceTitle"></b>. Left: stacked horizontal bars showing how each school's #1 through #5 finishers added up to the team score. Right: runner-by-runner scoring breakdown for the selected school.</p>
      <div class="two">
        <div class="card">
          <h3>Stacked runner point contributions by school (#1 to #5 scorers)</h3>
          <div id="schoolStackedBars"></div>
          <p class="so">Each colored segment represents one of the school's 5 scoring runners (from #1 in blue on the left to #5 in orange on the right). Shorter total bar = lower team score = higher team finish.</p>
        </div>
        <div class="card">
          <div class="ctl" style="justify-content:space-between;margin-bottom:8px">
            <h3 style="margin:0">Runner scoring breakdown</h3>
            <select id="compSchoolSelect" class="sel"></select>
          </div>
          <div class="tablewrap">
            <table class="t">
              <thead>
                <tr>
                  <th>Role</th>
                  <th>Runner</th>
                  <th class="num">Gr</th>
                  <th class="num">OA Place</th>
                  <th class="num">Team Pts</th>
                  <th class="num">% of Score</th>
                  <th class="num">Time</th>
                  <th class="num">Pace</th>
                </tr>
              </thead>
              <tbody id="compSchoolTableBody"></tbody>
            </table>
          </div>
          <p class="so" id="compSchoolSummary"></p>
        </div>
      </div>
    </section>
  </div>

  <!-- ======================================================================
       TAB 3: AQUINAS TEAM
       ====================================================================== -->
  <div id="tab-team" class="tab-pane __ACT_TEAM__">
    <div class="eyebrow">Aquinas Team · pack analytics, ridgelines &amp; season progression · Oct 23, 2026</div>
    <h1>Aquinas Academy Team Analytics &amp; Pack Progression</h1>
    <p class="lede">Deep dive into Aquinas Academy's team performance across High School (9–12) and Youth Diocesan (K–8) squads: pace density waves, top-7 pack compression ladders, season-over-season pace gains, and official team scorecards.</p>

    <div class="kpis" id="kpisTeam"></div>

    <section>
      <h2>Aquinas Academy pace density ridgelines</h2>
      <p class="sub">Overlapping kernel density curves for Aquinas Academy finishers. Dashed vertical lines and peak labels mark each group's median mile pace.</p>
      <div class="ctl">
        <span class="ctl-label">View Aquinas ridges by</span>
        <button class="pill" data-trmode="divisions" aria-pressed="true">Squad Divisions &amp; Gender</button>
        <button class="pill" data-trmode="meets" aria-pressed="false">Meet-by-Meet Progression</button>
      </div>
      <div class="card">
        <div id="teamRidgeChart"></div>
        <p class="so" id="teamRidgeSo"></p>
      </div>
    </section>

    <section>
      <h2>The pack ladder: Aquinas top-7 split compression by meet</h2>
      <p class="sub">Each horizontal capsule spans Aquinas Academy's #1 through #5 scoring runners in mile pace, with dashed whiskers to #6 and #7 tiebreaker displacers.</p>
      <div class="card" style="margin-bottom:12px">
        <div id="ladderChart"></div>
        <p class="so">Shorter capsules indicate tighter pack running between #1 and #5; leftward shift across the season shows faster team pacing.</p>
      </div>
      <div class="two">
        <div class="card">
          <h3>Top-5 scoring average time by meet (minutes)</h3>
          <div id="size"></div>
        </div>
        <div class="card">
          <h3>1-to-5 scoring pack spread (seconds between #1 and #5)</h3>
          <div id="chg"></div>
        </div>
      </div>
    </section>

    <section>
      <h2>Did Aquinas pacing improve as the season progressed?</h2>
      <div class="two">
        <div class="card">
          <h3>Biggest individual pace drops after opener (sec/mile faster)</h3>
          <div id="paceDropChart"></div>
          <p class="so" id="pacedrop-so"></p>
        </div>
        <div class="card">
          <h3>Aquinas top-5 average pace trajectory across 2026</h3>
          <div id="seasonTrendChart"></div>
          <p class="so" id="seasontrend-so"></p>
        </div>
      </div>
    </section>

    <section>
      <h2>Course-by-course Aquinas pace distribution &amp; official scorecards</h2>
      <div class="card" style="margin-bottom:14px">
        <h3>Aquinas interquartile pace box plot by meet</h3>
        <div id="courseBoxChart"></div>
        <p class="so" id="course-so"></p>
      </div>
      <div class="tablewrap">
        <table class="t">
          <thead>
            <tr>
              <th>Date</th>
              <th>Meet</th>
              <th>Division</th>
              <th>Gender</th>
              <th class="num">Aquinas Finish</th>
              <th class="num">Points</th>
              <th class="num">Top-5 Total</th>
              <th class="num">Top-5 Avg</th>
              <th>Field &amp; Opponents (Top 4)</th>
              <th>Sheet</th>
            </tr>
          </thead>
          <tbody id="standingsBody"></tbody>
        </table>
      </div>
    </section>
  </div>

  <!-- ======================================================================
       TAB 4: RUNNERS
       ====================================================================== -->
  <div id="tab-runners" class="tab-pane __ACT_RUNNERS__">
    <div class="eyebrow">Runners · individual pacing, percentiles &amp; split logs · Oct 23, 2026</div>
    <h1>Aquinas Academy Individual Runner Profiles</h1>
    <p class="lede">Search any of the 115 Aquinas Academy runners by name to inspect their meet-by-meet mile pace bar chart, field percentile trajectory, where they fall in the overall pace distribution, and complete split log.</p>

    <div class="ctl">
      <input type="search" id="runnerSearch" class="search" placeholder="Search runner by name..." style="min-width:240px">
      <span class="ctl-label">Select runner</span>
      <select id="runnerSelectTop" class="sel"></select>
      <span class="ctl-label" style="margin-left:auto">Grid size</span>
      <button class="pill" data-limit="28" aria-pressed="true">Top 28</button>
      <button class="pill" data-limit="60" aria-pressed="false">Top 60</button>
      <button class="pill" data-limit="999" aria-pressed="false">All 115</button>
    </div>

    <section>
      <div class="card" id="prof" style="margin-bottom:14px"></div>
    </section>

    <section>
      <h2>Where does <span id="activeRunnerLabel">Isaac Vangura</span> fall in the distribution?</h2>
      <p class="sub">The golden rounded pill outline highlights the exact pace or finish-time bucket where the selected runner sits.</p>
      <div class="ctl">
        <span class="ctl-label">Bucket mode</span>
        <button class="pill" data-bmode="pace" aria-pressed="true">Mile pace buckets (min/M)</button>
        <button class="pill" data-bmode="time" aria-pressed="false">Finish time buckets</button>
        <span class="ctl-label" style="margin-left:6px">Compare against</span>
        <button class="pill" data-bpop="field" aria-pressed="true">Entire race field (all schools)</button>
        <button class="pill" data-bpop="aquinas" aria-pressed="false">Aquinas runners only</button>
      </div>
      <div class="card">
        <h3 id="distTitle">Where do you fall? Share of finishes by bucket</h3>
        <div id="distChart"></div>
        <p class="so" id="dist-so"></p>
      </div>
    </section>

    <section>
      <h2>Browse Aquinas runners</h2>
      <div class="grid4" id="cards"></div>
    </section>

    <section>
      <h2>Full roster landscape: field placement vs. mile pace</h2>
      <p class="sub">Every Aquinas runner positioned by average field percentile (horizontal) and personal-best XC pace (vertical, faster at top). Click any marker to load that runner's profile above.</p>
      <div class="card">
        <div id="map"></div>
        <div class="legend" id="leg"></div>
      </div>
    </section>
  </div>

  <p class="foot" id="foot"></p>
</div>

<script>window.DEFAULT_TAB = '__TAB_ID__';</script>
<script src="data/data.js"></script>
<script src="app.js"></script>
</body>
</html>
"""

pages = [
    ("index.html", "overall", "Overall · 2026 Season Analytics"),
    ("schools.html", "schools", "Schools · Team Rankings Heatmap & Scoring Composition"),
    ("team.html", "team", "Aquinas Team · Pack Analytics & Progression"),
    ("runners.html", "runners", "Runners · Individual Profiles & Pace Charts"),
]

for filename, tab_id, title in pages:
    html = TEMPLATE.replace("__TITLE__", title).replace("__TAB_ID__", tab_id)
    for t in ("overall", "schools", "team", "runners"):
        cur_key = f"__CUR_{t.upper()}__"
        act_key = f"__ACT_{t.upper()}__"
        html = html.replace(cur_key, 'aria-current="page"' if t == tab_id else "")
        html = html.replace(act_key, "active" if t == tab_id else "")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated {filename} (default tab: {tab_id})")
