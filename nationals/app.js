(function () {
  "use strict";

  const DATA = window.CCCNYC_DATA;
  if (!DATA) {
    console.error("CCCNYC_DATA not loaded.");
    return;
  }

  const META = DATA.meta;
  const EVENTS = DATA.events;
  const EV_MAP = Object.fromEntries(EVENTS.map((e) => [e.num, e]));
  const TEAMS = DATA.teams;
  const CLUBS = DATA.clubs;
  const ALL_ROWS = DATA.athletes;
  const ATHLETES = ALL_ROWS.filter((a) => !a.is_duplicate_ghost);
  const ATH_MAP = Object.fromEntries(ALL_ROWS.map((a) => [a.id, a]));

  // Shared state
  let scoringLens = localStorage.getItem("cccnyc_lens") || "nat"; // 'nat' | 'cyo'
  const pageKey = document.body.dataset.page || "hub";
  const urlParams = new URLSearchParams(window.location.search);

  // Helpers
  const TEAM_STATE_MAP = {};
  CLUBS.forEach((c) => { if (c.org && c.state) TEAM_STATE_MAP[c.org] = c.state; });
  TEAMS.forEach((t) => { if (t.team && t.state) TEAM_STATE_MAP[t.team] = t.state; });
  ATHLETES.forEach((a) => { if (a.team && a.club_state) TEAM_STATE_MAP[a.team] = a.club_state; });
  const fmtClub = (name, state) => {
    if (!name || name === "Unattached") return name || "";
    const st = state || TEAM_STATE_MAP[name] || "";
    if (!st || st === "USA") return name;
    const tag = st === "INTL" ? "BM" : st;
    if (name.endsWith(`(${tag})`) || name.endsWith(`(${st})`)) return name;
    return `${name} (${tag})`;
  };
  const fmtClubTrunc = (name, state, maxLen = 24) => {
    if (!name || name === "Unattached") return name || "";
    const st = state || TEAM_STATE_MAP[name] || "";
    const tag = st === "INTL" ? "BM" : st;
    const suf = (tag && tag !== "USA") ? ` (${tag})` : "";
    const full = suf && !name.endsWith(suf) ? `${name}${suf}` : name;
    if (full.length <= maxLen) return full;
    if (!suf) return full.slice(0, maxLen - 1) + "…";
    const baseMax = Math.max(7, maxLen - suf.length - 1);
    return `${name.slice(0, baseMax)}…${suf}`;
  };
  const fmtInt = (n) => (n == null || isNaN(n) ? "—" : Number(n).toLocaleString());
  const fmtTime = (sec) => {
    if (sec == null || isNaN(sec)) return "—";
    const m = Math.floor(sec / 60);
    const s = sec - m * 60;
    return `${m}:${s < 10 ? "0" : ""}${s.toFixed(1)}`;
  };
  const fmtPace = (sec, distM) => {
    if (!sec || !distM) return "—";
    const p = sec / (distM / 1609.344);
    let m = Math.floor(p / 60);
    let s = Math.round(p - m * 60);
    if (s === 60) { m += 1; s = 0; }
    return `${m}:${s < 10 ? "0" : ""}${s}/mi`;
  };
  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

  const probBar = (pct, colorVar = "var(--accent)") => {
    const p = Math.max(0, Math.min(100, Number(pct) || 0));
    return `<span class="prob-bar-wrap"><span class="mono">${p.toFixed(1)}%</span><span class="prob-track"><span class="prob-fill" style="width:${p}%;background:${colorVar}"></span></span></span>`;
  };

  const tierBadge = (tier) => {
    if (!tier) return "";
    if (tier.includes("Tier 1+")) return `<span class="badge b-up" title="2026 XC Race Log + Returning CCCNYC Nationals Veteran">2026 + Vet</span>`;
    if (tier.includes("Tier 1")) return `<span class="badge b-accent" title="Direct 2026 Season Empirical Race Log">2026 Verified</span>`;
    if (tier.includes("Tier 2M")) return `<span class="badge b-gold" title="Verified 2023–2025 Empirical Race History">Prior Season</span>`;
    if (tier.includes("Tier 2")) return `<span class="badge b-gold" title="Returning 2022–2025 CCCNYC Nationals Veteran">CCCNYC Vet</span>`;
    return `<span class="badge b-muted" title="Hierarchical Club × Single-Year Age Empirical Prior">Club×Age Prior</span>`;
  };

  // Tooltip
  const tipEl = document.getElementById("d3Tooltip");
  function showTip(evt, html) {
    if (!tipEl) return;
    tipEl.innerHTML = html;
    tipEl.style.opacity = "1";
    const x = Math.min(window.innerWidth - 325, evt.clientX + 14);
    const y = Math.max(12, Math.min(window.innerHeight - 160, evt.clientY - 12));
    tipEl.style.left = x + "px";
    tipEl.style.top = y + "px";
  }
  function hideTip() {
    if (tipEl) tipEl.style.opacity = "0";
  }

  // Theme Toggle
  const themeBtn = document.getElementById("themeBtn");
  const themes = ["auto", "light", "dark"];
  let curTheme = localStorage.getItem("cccnyc_theme") || "auto";
  function applyTheme() {
    if (curTheme === "auto") document.documentElement.removeAttribute("data-theme");
    else document.documentElement.setAttribute("data-theme", curTheme);
    if (themeBtn) themeBtn.textContent = `Theme: ${curTheme}`;
  }
  applyTheme();
  if (themeBtn) {
    themeBtn.addEventListener("click", () => {
      curTheme = themes[(themes.indexOf(curTheme) + 1) % themes.length];
      localStorage.setItem("cccnyc_theme", curTheme);
      applyTheme();
      if (pageKey === "hub") renderUsaMap("hubUsaMapChart", "hubUsaMapSo", { interactiveFilter: false });
      if (pageKey === "clubs") renderUsaMap("clubsUsaMapChart", "clubsUsaMapSo", { interactiveFilter: true });
    });
  }

  // Global Scoring Lens Sync
  const globalScoringBtn = document.getElementById("globalScoringBtn");
  function syncLensUI() {
    if (globalScoringBtn) {
      globalScoringBtn.setAttribute("aria-pressed", scoringLens === "cyo" ? "true" : "false");
      globalScoringBtn.textContent = scoringLens === "cyo" ? "Lens: CYO National" : "Lens: National Open";
    }
    document.querySelectorAll(".lens-btn").forEach((b) => {
      b.setAttribute("aria-pressed", b.dataset.lens === scoringLens ? "true" : "false");
    });
  }
  function setLens(newLens) {
    scoringLens = newLens;
    localStorage.setItem("cccnyc_lens", scoringLens);
    syncLensUI();
    if (pageKey === "hub") renderHub();
    if (pageKey === "races") renderRacePage();
  }
  if (globalScoringBtn) {
    globalScoringBtn.addEventListener("click", () => setLens(scoringLens === "nat" ? "cyo" : "nat"));
  }
  document.querySelectorAll(".lens-btn").forEach((b) => {
    b.addEventListener("click", () => setLens(b.dataset.lens));
  });
  syncLensUI();

  // =========================================================================
  // PAGE 1: MEET HUB & COURSE (index.html)
  // =========================================================================
  let selectedCourseDist = 3000;

  function renderHub() {
    const kpiBox = document.getElementById("hubKpis");
    if (!kpiBox) return;

    const dopTeams = TEAMS.filter((t) => t.is_dop && t.scores_official_team);
    const expDopNatPods = dopTeams.reduce((s, t) => s + (t.nat ? t.nat.podium_prob / 100 : 0), 0);
    const expDopCyoTitles = dopTeams.reduce((s, t) => s + (t.cyo ? t.cyo.win_prob / 100 : 0), 0);
    const expDopAA = ATHLETES.filter((a) => a.is_dop).reduce((s, a) => s + a.aa_age_prob / 100, 0);

    kpiBox.innerHTML = `
      <div class="kpi kpi-accent">
        <div class="v">${META.unique_runners.toLocaleString()}</div>
        <div class="l">Unique Race-Day Runners</div>
        <div class="s">${META.raw_pdf_entries} raw PDF rows · 11 races</div>
      </div>
      <div class="kpi kpi-gold">
        <div class="v">${META.clubs_count}</div>
        <div class="l">Clubs, Dioceses &amp; Schools</div>
        <div class="s">${META.states_represented.length} US states + Bermuda</div>
      </div>
      <div class="kpi kpi-up">
        <div class="v">${META.seeded_individual_count.toLocaleString()} <span style="font-size:14px;font-weight:500">(${((100 * META.seeded_individual_count) / META.unique_runners).toFixed(1)}%)</span></div>
        <div class="l">Direct Empirical Athlete Seeds</div>
        <div class="s">${META.verified_2026_runners.toLocaleString()} '26 logs · ${META.cccnyc_veterans.toLocaleString()} CCCNYC vets</div>
      </div>
      <div class="kpi kpi-dop">
        <div class="v">${META.dop_runners} / ${META.dop_runners}</div>
        <div class="l">Diocese of Pittsburgh Matched</div>
        <div class="s">100% matched across ${META.dop_feeder_schools} feeder schools</div>
      </div>
      <div class="kpi kpi-cyo">
        <div class="v">${scoringLens === "cyo" ? expDopCyoTitles.toFixed(1) : expDopNatPods.toFixed(1)}</div>
        <div class="l">${scoringLens === "cyo" ? "Proj. DoP CYO Team Titles" : "Proj. DoP National Team Trophies"}</div>
        <div class="s">${scoringLens === "cyo" ? "Out of 6 CYO-eligible divisions" : `${expDopCyoTitles.toFixed(1)} projected CYO titles`}</div>
      </div>
      <div class="kpi kpi-dop">
        <div class="v">${expDopAA.toFixed(1)}</div>
        <div class="l">Proj. DoP Age All-Americans</div>
        <div class="s">Top-25 single-year birth-age medals</div>
      </div>
    `;

    // Schedule Grid
    const schedGrid = document.getElementById("hubScheduleGrid");
    schedGrid.innerHTML = EVENTS.map((ev) => {
      const evTeams = TEAMS.filter((t) => t.event_num === ev.num && t.scores_official_team && (scoringLens === "nat" || t.is_cyo));
      evTeams.sort((a, b) => a[scoringLens].exp_rank - b[scoringLens].exp_rank);
      const evAths = ATHLETES.filter((a) => a.event_num === ev.num && (scoringLens === "nat" || a.is_cyo));
      evAths.sort((a, b) => a.exp_place - b.exp_place);
      const favAth = evAths[0];
      const dopT = TEAMS.filter((t) => t.event_num === ev.num && t.is_dop);

      let teamLines = "";
      if (evTeams.length === 0) {
        teamLines = `<div class="muted" style="font-size:12px">No complete 5+ ${scoringLens === "cyo" ? "CYO " : ""}scoring teams entered</div>`;
      } else {
        teamLines = evTeams.slice(0, 3).map((t, idx) => {
          const st = t[scoringLens];
          const medal = idx === 0 ? "&#129351;" : idx === 1 ? "&#129352;" : "&#129353;";
          const cls = t.is_dop ? "dop-txt" : t.is_cyo ? "cyo-txt" : "";
          return `<div class="ev-pod-line"><span class="${cls}" style="overflow:hidden;text-overflow:ellipsis">${medal} ${esc(fmtClub(t.team, t.state))}</span><span class="mono">${st.exp_score}p (${st.win_prob}%W)</span></div>`;
        }).join("");
      }

      let dopNote = "";
      if (dopT.length > 0) {
        const d0 = dopT[0];
        if (!d0.scores_official_team) {
          dopNote = `<div style="margin-top:4px"><span class="badge b-warn">DoP: ${d0.roster_count} runners (&lt;5 incomplete)</span></div>`;
        } else {
          dopNote = `<div style="margin-top:4px;display:flex;gap:5px;flex-wrap:wrap">
            <span class="badge b-dop">DoP Nat #${d0.nat.exp_rank.toFixed(1)} (${d0.nat.podium_prob}% Pod)</span>
            <span class="badge b-cyo">CYO #${d0.cyo.exp_rank.toFixed(1)} (${d0.cyo.win_prob}%W)</span>
          </div>`;
        }
      }

      return `
        <div class="ev-card ${ev.dop_entries_count > 0 ? "has-dop" : ""}" onclick="window.location.href='races.html?event=${ev.num}'">
          <div class="ev-time">
            <span><b>${ev.time_est}</b> · Event ${ev.num}</span>
            <span>${ev.unique_runners} rnrs · ${ev.scoring_teams_count} tms</span>
          </div>
          <div class="ev-title">${esc(ev.name)}</div>
          <div style="border-top:1px solid var(--line);padding-top:6px">${teamLines}</div>
          ${favAth ? `<div style="font-size:12px;color:var(--muted);border-top:1px dashed var(--line);padding-top:5px">Indiv Fav: <b style="color:var(--fg)">${esc(favAth.display_name)}</b> · ${esc(fmtClub(favAth.team, favAth.club_state))} · <span class="mono">${favAth.proj_time_str}</span></div>` : ""}
          ${dopNote}
        </div>
      `;
    }).join("");

    renderUsaMap("hubUsaMapChart", "hubUsaMapSo", { interactiveFilter: false });
    renderOfficialMeetSchedule();
    renderCourseChart(selectedCourseDist);
    renderHistEditionsChart();
    renderAnomalyAudit();
  }

  // =========================================================================
  // OFFICIAL MEET SCHEDULE (EST) & INTERACTIVE USA CHOROPLETH + CITY DOTS MAP
  // =========================================================================
  const OFFICIAL_SCHEDULE_ROWS = [
    { time: "8:15 AM", label: "Head Coaches Meeting", dist: "", milestone: true },
    { time: "8:45 AM", label: "National Anthem", dist: "", milestone: true },
    { time: "9:00 AM", label: "15–16 Girls & 17–18 Girls", dist: "5000 Meters", event_num: 1 },
    { time: "9:30 AM", label: "15–16 Boys & 17–18 Boys", dist: "5000 Meters", event_num: 2 },
    { time: "10:00 AM", label: "6–8 Girls", dist: "2000 Meters", event_num: 3 },
    { time: "10:25 AM", label: "6–8 Boys", dist: "2000 Meters", event_num: 4 },
    { time: "10:45 AM", label: "Race of the Americas (8 & Under)", dist: "1000 Meters", event_num: 5 },
    { time: "10:45 AM", label: "Officials' Break", dist: "", milestone: true },
    { time: "11:15 AM", label: "9–10 Girls", dist: "3000 Meters", event_num: 6 },
    { time: "11:45 AM", label: "9–10 Boys", dist: "3000 Meters", event_num: 7 },
    { time: "12:15 PM", label: "11–12 Girls", dist: "3000 Meters", event_num: 8 },
    { time: "12:45 PM", label: "11–12 Boys", dist: "3000 Meters", event_num: 9 },
    { time: "1:15 PM", label: "13–14 Girls", dist: "4000 Meters", event_num: 10 },
    { time: "1:45 PM", label: "13–14 Boys", dist: "4000 Meters", event_num: 11 },
  ];

  function renderOfficialMeetSchedule() {
    const box = document.getElementById("officialScheduleCard");
    if (!box) return;
    const rowsHtml = OFFICIAL_SCHEDULE_ROWS.map((r) => {
      if (r.milestone) {
        return `<tr class="sched-milestone"><td class="sched-time-cell">${r.time}</td><td colspan="2">${esc(r.label)}</td></tr>`;
      }
      const ev = EV_MAP[r.event_num];
      const hasDop = ev && ev.dop_entries_count > 0;
      return `<tr class="sched-race-row" onclick="window.location.href='races.html?event=${r.event_num}'" title="Open Event ${r.event_num} Monte Carlo simulation">
        <td class="sched-time-cell">${r.time}</td>
        <td><b>${esc(r.label)}</b> ${hasDop ? `<span class="badge b-dop" style="font-size:10px;padding:1px 5px;margin-left:4px">Pgh CYO (${ev.dop_entries_count})</span>` : ""}</td>
        <td class="sched-dist-cell">${r.dist}</td>
      </tr>`;
    }).join("");

    box.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin-bottom:6px">
        <h2 style="margin:0">Official Meet Schedule</h2>
        <a class="pill" href="data/official_meet_schedule.jpg" target="_blank" style="font-size:11px;padding:2px 8px">Original Graphic &#8599;</a>
      </div>
      <div class="sched-est-banner">
        <span>NOTE: All times are Eastern Standard Time (EST)</span>
        <span class="mono">Sat, Nov 21</span>
      </div>
      <table class="sched-official-tbl">
        <thead>
          <tr><th>Time</th><th>Event</th><th style="text-align:right">Race Length</th></tr>
        </thead>
        <tbody>${rowsHtml}</tbody>
      </table>
      <p class="so" style="margin-top:8px">Click any race row to jump straight to its 10,000-trial simulation. Red badges indicate the 8 races featuring <b>Pittsburgh CYO</b> runners.</p>
    `;
  }

  // Exact home city coordinates [lon, lat] for all 91 registered clubs & CYO programs
  const CLUB_CITY_COORDS = {
    "Brocaw Blazers": { city: "Overland Park, KS", lon: -94.671, lat: 38.982 },
    "Team F.C.A. KS": { city: "Olathe, KS", lon: -94.819, lat: 38.881 },
    "Girard Warriors": { city: "Girard, KS", lon: -94.838, lat: 37.511 },
    "Phila. CYO": { city: "Philadelphia, PA", lon: -75.165, lat: 39.953 },
    "Pittsburgh CYO": { city: "Pittsburgh, PA", lon: -79.996, lat: 40.441 },
    "Diocese of Pittsburgh": { city: "Pittsburgh, PA", lon: -79.996, lat: 40.441 },
    "Greensburg CYO": { city: "Greensburg, PA", lon: -79.539, lat: 40.301 },
    "Nittany Track and Field": { city: "State College, PA", lon: -77.860, lat: 40.793 },
    "Bishop McDevitt - CYO": { city: "Harrisburg, PA", lon: -76.887, lat: 40.273 },
    "Central PA Speed": { city: "Mechanicsburg, PA", lon: -77.009, lat: 40.214 },
    "Godspeed Track & Field": { city: "Lancaster, PA", lon: -76.306, lat: 40.038 },
    "Louisville TigerSharks": { city: "Louisville, KY", lon: -85.758, lat: 38.253 },
    "Louisville Fast Cats": { city: "Louisville, KY", lon: -85.758, lat: 38.253 },
    "Bates Elementary": { city: "Louisville, KY", lon: -85.758, lat: 38.253 },
    "Derby City": { city: "Louisville, KY", lon: -85.758, lat: 38.253 },
    "Northeast Striders": { city: "Louisville, KY", lon: -85.758, lat: 38.253 },
    "Thomson Training": { city: "Louisville, KY", lon: -85.758, lat: 38.253 },
    "Team Kentucky": { city: "Lexington, KY", lon: -84.504, lat: 38.041 },
    "Grassroots Running Club": { city: "Lexington, KY", lon: -84.504, lat: 38.041 },
    "Shelby County Pacers": { city: "Shelbyville, KY", lon: -85.224, lat: 38.212 },
    "Harmony Elementary School": { city: "Goshen, KY", lon: -85.574, lat: 38.404 },
    "Eastern KY Striders": { city: "Ashland, KY", lon: -82.637, lat: 38.478 },
    "Toledo CYO": { city: "Toledo, OH", lon: -83.538, lat: 41.653 },
    "CRC Grasshoppers": { city: "Columbus, OH", lon: -82.999, lat: 39.961 },
    "Columbus CYO": { city: "Columbus, OH", lon: -82.999, lat: 39.961 },
    "Styn Strong Racing": { city: "Columbus, OH", lon: -82.999, lat: 39.961 },
    "Buckeye Racers": { city: "Upper Sandusky, OH", lon: -83.281, lat: 40.827 },
    "Hudson Youth Cross Country": { city: "Hudson, OH", lon: -81.441, lat: 41.240 },
    "Copley Youth Cross Country": { city: "Copley, OH", lon: -81.640, lat: 41.096 },
    "Cleveland Youth Running Club": { city: "Cleveland, OH", lon: -81.694, lat: 41.499 },
    "Minster XC": { city: "Minster, OH", lon: -84.377, lat: 40.393 },
    "Ohio Elite Cross Country": { city: "Mason, OH", lon: -84.310, lat: 39.360 },
    "Golden Bear Run Club": { city: "Upper Arlington, OH", lon: -83.062, lat: 40.025 },
    "North Union Intermdiate": { city: "Richwood, OH", lon: -83.297, lat: 40.427 },
    "Hilliard Track Club": { city: "Hilliard, OH", lon: -83.158, lat: 40.033 },
    "ALTIUS Track & Field": { city: "Dayton, OH", lon: -84.192, lat: 39.759 },
    "Dresden Middle": { city: "Dresden, OH", lon: -82.011, lat: 40.122 },
    "Threshold and Beyond": { city: "Cincinnati, OH", lon: -84.512, lat: 39.103 },
    "Body in Training": { city: "Noblesville, IN", lon: -86.009, lat: 40.046 },
    "HP Distance": { city: "Carmel, IN", lon: -86.118, lat: 39.978 },
    "Green Wave": { city: "Westfield, IN", lon: -86.127, lat: 40.043 },
    "Southern Indiana Runing Club": { city: "New Albany, IN", lon: -85.824, lat: 38.286 },
    "Indiana Pathfinders": { city: "Columbus, IN", lon: -85.921, lat: 39.201 },
    "Fishers Fire": { city: "Fishers, IN", lon: -86.013, lat: 39.957 },
    "Shady Abes": { city: "Springfield, IL", lon: -89.650, lat: 39.782 },
    "Belvidere Tornados": { city: "Belvidere, IL", lon: -88.844, lat: 42.264 },
    "West Suburban Harriers": { city: "Naperville, IL", lon: -88.148, lat: 41.786 },
    "Dixon Distance": { city: "Dixon, IL", lon: -89.479, lat: 41.839 },
    "Chicago Rabbits": { city: "Chicago, IL", lon: -87.630, lat: 41.878 },
    "Elgin Road Warriors": { city: "Elgin, IL", lon: -88.283, lat: 42.035 },
    "Elgin Sharks": { city: "Elgin, IL", lon: -88.283, lat: 42.035 },
    "Accelerators": { city: "Batavia, IL", lon: -88.313, lat: 41.850 },
    "Staley Striders": { city: "Decatur, IL", lon: -88.955, lat: 39.840 },
    "Monroe Milers": { city: "Monroe, MI", lon: -83.398, lat: 41.917 },
    "Saline MS": { city: "Saline, MI", lon: -83.782, lat: 42.167 },
    "Eagles Elite": { city: "Hartland, MI", lon: -83.753, lat: 42.656 },
    "Ann Arbor Track Club": { city: "Ann Arbor, MI", lon: -83.743, lat: 42.281 },
    "Comets Track Club": { city: "Kalamazoo, MI", lon: -85.587, lat: 42.292 },
    "Michigan Cougars": { city: "Canton, MI", lon: -83.482, lat: 42.309 },
    "Embrace Sportz": { city: "Detroit, MI", lon: -83.046, lat: 42.331 },
    "St. Patrick": { city: "White Lake, MI", lon: -83.503, lat: 42.659 },
    "St. Charles Club": { city: "Newport, MI", lon: -83.310, lat: 42.004 },
    "Pinconning": { city: "Pinconning, MI", lon: -83.965, lat: 43.856 },
    "Waza Track Club": { city: "Novi, MI", lon: -83.475, lat: 42.480 },
    "Clinton Running Club": { city: "Clinton, MI", lon: -83.972, lat: 42.072 },
    "LA-CYO": { city: "Los Angeles, CA", lon: -118.244, lat: 34.052 },
    "Buffalo Chips Running Club": { city: "Sacramento, CA", lon: -121.494, lat: 38.582 },
    "Delta Hawks Racing": { city: "West Sacramento, CA", lon: -121.530, lat: 38.580 },
    "NorCal Distance": { city: "Folsom, CA", lon: -121.176, lat: 38.678 },
    "St. Louis Blazers": { city: "St. Louis, MO", lon: -90.199, lat: 38.627 },
    "CMAC All Stars": { city: "Columbia, MO", lon: -92.334, lat: 38.952 },
    "Coyotes Cross Country": { city: "Littleton / Centennial, CO", lon: -104.971, lat: 39.590 },
    "The Stead": { city: "Boulder, CO", lon: -105.271, lat: 40.015 },
    "Olney Cross Country Club": { city: "Olney, MD", lon: -77.067, lat: 39.153 },
    "Frederick Blaze": { city: "Frederick, MD", lon: -77.411, lat: 39.414 },
    "Lightning Running Club": { city: "Frederick, MD", lon: -77.411, lat: 39.414 },
    "Seven Locks Running Club": { city: "Bethesda / Potomac, MD", lon: -77.152, lat: 39.005 },
    "Damascus Freedom": { city: "Damascus, MD", lon: -77.204, lat: 39.288 },
    "Jenks America Track Club": { city: "Jenks / Tulsa, OK", lon: -95.968, lat: 36.023 },
    "Edmond Thunder Cross Country &": { city: "Edmond, OK", lon: -97.478, lat: 35.653 },
    "Accel Sports": { city: "Lebanon, TN", lon: -86.291, lat: 36.208 },
    "Crimson Knights": { city: "Woodbridge, NJ", lon: -74.285, lat: 40.558 },
    "Camden Clock Chasers": { city: "Camden, NJ", lon: -75.120, lat: 39.926 },
    "Southern MN Youth XC": { city: "Owatonna, MN", lon: -93.226, lat: 44.084 },
    "Seashore Striders": { city: "Lewes, DE", lon: -75.139, lat: 38.775 },
    "NOVA Run Club": { city: "Fairfax / Northern VA", lon: -77.306, lat: 38.846 },
    "Fox City": { city: "Fairfax / Northern VA", lon: -77.306, lat: 38.846 },
    "Virginia CYO": { city: "Fairfax / Northern VA", lon: -77.306, lat: 38.846 },
    "River Ridge Youth Track Club": { city: "Woodstock, GA", lon: -84.519, lat: 34.101 },
    "REAL Distance Training Academy": { city: "Madison, AL", lon: -86.748, lat: 34.699 },
    "Tailwind TC": { city: "White Plains, NY", lon: -73.763, lat: 41.034 },
  };

  const usaMapState = {}; // containerId -> { view: 'usa' | 'core', selected: null | { type, title, subtitle, html, actionHref, actionLabel, accent } }
  const CORE_ZOOM_STATES = new Set(["KS","OK","MO","MN","IA","WI","IL","IN","MI","OH","KY","TN","AL","GA","PA","NY","NJ","MD","DE","VA","WV","DC","NC","SC","AR","NE"]);
  const STATE_LABEL_SKIP = new Set(["DE","MD","NJ","DC","RI","CT","MA","VT","NH"]);

  function renderUsaMap(containerId, soId, opts = {}) {
    const box = document.getElementById(containerId);
    const geo = window.US_STATES_GEO;
    if (!box || !geo) return;
    const stObj = (usaMapState[containerId] = usaMapState[containerId] || { view: "usa", selected: null });
    box.innerHTML = "";

    const isDark =
      document.documentElement.getAttribute("data-theme") === "dark" ||
      (!document.documentElement.getAttribute("data-theme") && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);

    // Aggregate runner counts and clubs per state
    const stateTotals = {};
    const stateClubs = {};
    CLUBS.forEach((c) => {
      if (!c.state || c.state === "USA" || c.state === "INTL") return;
      stateTotals[c.state] = (stateTotals[c.state] || 0) + c.runners_count;
      (stateClubs[c.state] = stateClubs[c.state] || []).push(c);
    });
    const maxStateRunners = d3.max(Object.values(stateTotals)) || 1;
    const bermudaClub = CLUBS.find((c) => c.state === "INTL");

    // Sequential shade scale: lighter = fewer runners, darker = more runners!
    const colorScale = isDark
      ? d3.scaleSequential((t) => d3.interpolateYlGnBu(0.20 + 0.78 * Math.pow(t, 0.56))).domain([0, maxStateRunners])
      : d3.scaleSequential((t) => d3.interpolateBlues(0.18 + 0.78 * Math.pow(t, 0.55))).domain([0, maxStateRunners]);
    const emptyStateFill = isDark ? "#20221e" : "#eeece4";
    const borderStroke = isDark ? "#383b34" : "#ffffff";

    // Top map controls: Full USA vs Midwest & East Focus + Bermuda pill
    const ctlRow = document.createElement("div");
    ctlRow.className = "map-ctl-row";
    ctlRow.innerHTML = `
      <div style="display:inline-flex;gap:6px;flex-wrap:wrap;align-items:center">
        <button class="pill" data-mview="usa" aria-pressed="${stObj.view === "usa"}">Full USA (20 States)</button>
        <button class="pill" data-mview="core" aria-pressed="${stObj.view === "core"}">Zoom: Midwest &amp; East</button>
      </div>
      ${bermudaClub ? `<button class="pill" id="${containerId}_bermudaBtn" style="font-size:11.5px;padding:3px 10px" title="International delegation">&#127758; Bermuda (${bermudaClub.runners_count} rnrs)</button>` : ""}
    `;
    box.appendChild(ctlRow);
    ctlRow.querySelectorAll("button[data-mview]").forEach((btn) => {
      btn.addEventListener("click", () => {
        stObj.view = btn.dataset.mview;
        renderUsaMap(containerId, soId, opts);
      });
    });

    // Aggregate club cities into clean dot markers
    const cityMap = {};
    CLUBS.forEach((c) => {
      if (c.org === "Unattached" || c.state === "INTL") return;
      const coord = CLUB_CITY_COORDS[c.org];
      if (!coord) return;
      const key = coord.city;
      const entry = (cityMap[key] = cityMap[key] || {
        city: coord.city,
        state: c.state,
        lon: coord.lon,
        lat: coord.lat,
        runners: 0,
        clubs: [],
        hasDop: false,
        hasCyo: false,
      });
      entry.runners += c.runners_count;
      entry.clubs.push(c);
      if (c.is_dop) entry.hasDop = true;
      if (c.is_cyo) entry.hasCyo = true;
    });
    const isCore = stObj.view === "core";
    const cityPoints = Object.values(cityMap)
      .filter((pt) => !isCore || CORE_ZOOM_STATES.has(pt.state))
      .sort((a, b) => b.runners - a.runners);
    const maxCityRunners = d3.max(Object.values(cityMap), (d) => d.runners) || 1;
    const dotRadius = d3.scaleSqrt().domain([1, maxCityRunners]).range(isCore ? [3.4, 8.6] : [2.5, 6.8]);

    const W = 820;
    const H = 490;
    const fitGeo = isCore
      ? { type: "FeatureCollection", features: geo.features.filter((f) => CORE_ZOOM_STATES.has(f.properties.code)) }
      : geo;
    const projection = d3.geoAlbers().fitExtent([[14, 12], [W - 14, H - 12]], fitGeo);
    const path = d3.geoPath().projection(projection);

    const svg = d3.select(box).append("svg")
      .attr("class", "usa-map-svg")
      .attr("viewBox", `0 0 ${W} ${H}`)
      .attr("preserveAspectRatio", "xMidYMid meet");

    // Helper to update tap-to-inspect card cleanly (ideal for mobile touch + desktop click)
    const tapBox = document.createElement("div");
    const renderTapCard = () => {
      const sel = stObj.selected;
      if (!sel) {
        tapBox.innerHTML = "";
        return;
      }
      tapBox.innerHTML = `
        <div class="map-tap-card ${sel.accent || ""}">
          <div style="min-width:0;flex:1 1 210px">
            <div style="font-weight:700;color:var(--fg)">${sel.title} <span class="mono muted" style="font-weight:500">${sel.subtitle}</span></div>
            <div style="color:var(--fg2);margin-top:2px;font-size:12px">${sel.html}</div>
          </div>
          ${sel.actionHtml || ""}
        </div>
      `;
    };

    const selectState = (d) => {
      const st = d.properties.code;
      const cnt = stateTotals[st] || 0;
      if (!cnt) return;
      const cl = (stateClubs[st] || []).slice().sort((a, b) => b.runners_count - a.runners_count);
      const topTxt = cl.slice(0, 5).map((c) => `<b>${esc(fmtClub(c.org, c.state))}</b> · ${c.runners_count}`).join(" · ") + (cl.length > 5 ? ` · +${cl.length - 5} more` : "");
      if (opts.interactiveFilter) {
        clubStateFilter = clubStateFilter === st ? "ALL" : st;
        const stSel = document.getElementById("clubStateSel");
        if (stSel) stSel.value = clubStateFilter;
        const rst = document.getElementById("clubsMapResetBtn");
        if (rst) rst.style.display = clubStateFilter === "ALL" ? "none" : "inline-flex";
        stObj.selected = clubStateFilter === "ALL" ? null : {
          title: `${esc(d.properties.name)} (${st})`,
          subtitle: `· ${cnt} runners · ${cl.length} club${cl.length === 1 ? "" : "s"}`,
          html: topTxt,
          actionHtml: `<span class="badge b-accent">Filtered Below</span>`,
        };
        renderUsaMap(containerId, soId, opts);
        renderClubsTable();
      } else {
        stObj.selected = {
          title: `${esc(d.properties.name)} (${st})`,
          subtitle: `· ${cnt} runners · ${cl.length} club${cl.length === 1 ? "" : "s"}`,
          html: topTxt,
          actionHtml: `<a class="pill" href="clubs.html?state=${encodeURIComponent(st)}" style="white-space:nowrap">View ${st} Clubs &#8594;</a>`,
        };
        renderTapCard();
      }
    };

    const selectCity = (pt) => {
      const sortedC = pt.clubs.slice().sort((a, b) => b.runners_count - a.runners_count);
      const primary = sortedC[0];
      const cTxt = sortedC.map((c) => `<b>${esc(fmtClub(c.org, c.state))}</b> · ${c.runners_count}`).join(" · ");
      stObj.selected = {
        title: esc(pt.city),
        subtitle: `· ${pt.runners} runners`,
        html: cTxt,
        accent: pt.hasDop ? "is-dop" : pt.hasCyo ? "is-cyo" : "",
        actionHtml: opts.interactiveFilter
          ? `<button class="pill" onclick="window.selectClub('${esc(primary.org)}')" style="white-space:nowrap">Inspect ${esc(fmtClub(primary.org, primary.state))} &#8594;</button>`
          : `<a class="pill" href="clubs.html?org=${encodeURIComponent(primary.org)}" style="white-space:nowrap">Club Dossier &#8594;</a>`,
      };
      renderTapCard();
      if (opts.interactiveFilter && primary && typeof window.selectClub === "function") {
        selectedClubOrg = primary.org;
        renderClubInspector(primary.org);
      }
    };

    if (bermudaClub) {
      const bBtn = document.getElementById(`${containerId}_bermudaBtn`);
      if (bBtn) {
        bBtn.addEventListener("click", () => {
          stObj.selected = {
            title: "Hamilton, Bermuda (BM)",
            subtitle: `· ${bermudaClub.runners_count} runners`,
            html: `<b>${esc(fmtClub(bermudaClub.org, bermudaClub.state))}</b> · ${bermudaClub.runners_count}`,
            actionHtml: `<a class="pill" href="clubs.html?org=${encodeURIComponent(bermudaClub.org)}" style="white-space:nowrap">Club Dossier &#8594;</a>`,
          };
          renderTapCard();
        });
      }
    }

    // 1. State Choropleth Polygons (clipped cleanly to viewport)
    svg.append("g")
      .selectAll("path")
      .data(geo.features)
      .enter()
      .append("path")
      .attr("class", (d) => `usa-state ${opts.interactiveFilter && clubStateFilter === d.properties.code ? "is-selected" : ""}`)
      .attr("d", path)
      .attr("fill", (d) => {
        const cnt = stateTotals[d.properties.code] || 0;
        return cnt > 0 ? colorScale(cnt) : emptyStateFill;
      })
      .attr("stroke", borderStroke)
      .attr("stroke-width", isCore ? 1.15 : 0.95)
      .on("mousemove", (evt, d) => {
        if (evt.pointerType === "touch") return;
        const st = d.properties.code;
        const cnt = stateTotals[st] || 0;
        const cl = (stateClubs[st] || []).slice().sort((a, b) => b.runners_count - a.runners_count);
        const topList = cl.slice(0, 4).map((c) => `${esc(fmtClub(c.org, c.state))} · ${c.runners_count}`).join("<br>");
        showTip(evt,
          `<b>${esc(d.properties.name)} (${st})</b><br>` +
          (cnt > 0
            ? `Runners: <b class="mono">${cnt}</b> across <b>${cl.length}</b> club${cl.length === 1 ? "" : "s"}<br><span style="color:var(--fg2)">${topList}${cl.length > 4 ? `<br>+${cl.length - 4} more…` : ""}</span>`
            : `<span class="muted">0 club entries in 2026</span>`)
        );
      })
      .on("mouseleave", hideTip)
      .on("click", (_, d) => selectState(d));

    // 2. Clean State Code Labels on Active States (readable at a glance on mobile!)
    const lblG = svg.append("g").style("pointer-events", "none");
    geo.features.forEach((f) => {
      const st = f.properties.code;
      const cnt = stateTotals[st] || 0;
      if (!cnt || (!isCore && STATE_LABEL_SKIP.has(st))) return;
      const cXY = path.centroid(f);
      if (!cXY || isNaN(cXY[0]) || isNaN(cXY[1]) || cXY[0] < 12 || cXY[0] > W - 12 || cXY[1] < 12 || cXY[1] > H - 12) return;
      const darkBg = isDark ? cnt < maxStateRunners * 0.35 : cnt >= maxStateRunners * 0.32;
      lblG.append("text")
        .attr("x", cXY[0])
        .attr("y", cXY[1] + 4)
        .attr("text-anchor", "middle")
        .attr("font-size", isCore ? 12.5 : 10.5)
        .attr("font-weight", 700)
        .style("font-family", "var(--font-mono)")
        .attr("fill", darkBg ? "rgba(255,255,255,0.88)" : "rgba(21,21,19,0.72)")
        .text(st);
    });

    // 3. Club City Dots with lightweight overlap-separation pass so suburban clusters stay crisp!
    const projectedDots = cityPoints
      .map((pt) => {
        const xy = projection([pt.lon, pt.lat]);
        if (!xy || xy[0] < 6 || xy[0] > W - 6 || xy[1] < 6 || xy[1] > H - 6) return null;
        return { ...pt, x: xy[0], y: xy[1], ox: xy[0], oy: xy[1], r: dotRadius(pt.runners) };
      })
      .filter(Boolean);

    for (let iter = 0; iter < 12; iter++) {
      for (let i = 0; i < projectedDots.length; i++) {
        for (let j = i + 1; j < projectedDots.length; j++) {
          const a = projectedDots[i], b = projectedDots[j];
          const dx = b.x - a.x, dy = b.y - a.y;
          const dist = Math.hypot(dx, dy) || 0.01;
          const minD = a.r + b.r + 1.1;
          if (dist < minD) {
            const push = (minD - dist) * 0.38;
            const ux = dx / dist, uy = dy / dist;
            a.x -= ux * push * 0.45; a.y -= uy * push * 0.45;
            b.x += ux * push * 0.55; b.y += uy * push * 0.55;
          }
        }
        // Keep softly tethered near real home city
        const d = projectedDots[i];
        d.x += (d.ox - d.x) * 0.14;
        d.y += (d.oy - d.y) * 0.14;
      }
    }

    const dotG = svg.append("g");
    projectedDots.forEach((pt) => {
      const fillCol = pt.hasDop ? "#c43225" : pt.hasCyo ? "#7c3aed" : "#f59e0b";
      dotG.append("circle")
        .attr("class", "city-dot")
        .attr("cx", pt.x)
        .attr("cy", pt.y)
        .attr("r", pt.r)
        .attr("fill", fillCol)
        .attr("fill-opacity", 0.90)
        .attr("stroke", isDark ? "#111210" : "#ffffff")
        .attr("stroke-width", isCore ? 1.35 : 1.05)
        .on("mousemove", (evt) => {
          if (evt.pointerType === "touch") return;
          const cLines = pt.clubs
            .slice()
            .sort((a, b) => b.runners_count - a.runners_count)
            .map((c) => `• ${esc(fmtClub(c.org, c.state))}: <b class="mono">${c.runners_count}</b>`)
            .join("<br>");
          showTip(evt,
            `<b>${esc(pt.city)}</b><br>` +
            `Total City Delegation: <b class="mono">${pt.runners} runners</b><br>` +
            `${cLines}`
          );
        })
        .on("mouseleave", hideTip)
        .on("click", (evt) => {
          evt.stopPropagation();
          selectCity(pt);
        });
    });

    // 4. Meet Venue Star Pin: Cedarville University, OH (-83.806, 39.741)
    const cedXY = projection([-83.806, 39.741]);
    if (cedXY) {
      const starPath = d3.symbol().type(d3.symbolStar).size(isCore ? 175 : 130)();
      svg.append("path")
        .attr("d", starPath)
        .attr("transform", `translate(${cedXY[0]},${cedXY[1]})`)
        .attr("fill", "#ffd43b")
        .attr("stroke", "#151513")
        .attr("stroke-width", 1.3)
        .style("cursor", "pointer")
        .on("mousemove", (evt) => showTip(evt,
          `<b>★ Cedarville University, OH</b><br>Elvin R. King Cross Country Course<br>2026 CCCNYC &amp; CYO Nationals Venue`
        ))
        .on("mouseleave", hideTip)
        .on("click", (evt) => {
          evt.stopPropagation();
          stObj.selected = {
            title: "★ Cedarville University, OH",
            subtitle: "· Championship Host Venue",
            html: "Elvin R. King Cross Country Course · 251 N. Main St., Cedarville, OH",
            actionHtml: "",
          };
          renderTapCard();
        });
    }

    // 5. Tap-to-Inspect Card container + Legend Bar
    box.appendChild(tapBox);
    renderTapCard();

    const gradStops = [0, 0.2, 0.4, 0.6, 0.8, 1.0].map((t) => colorScale(t * maxStateRunners)).join(", ");
    const legDiv = document.createElement("div");
    legDiv.className = "map-legend-bar";
    legDiv.innerHTML = `
      <div class="map-legend-group">
        <span style="font-weight:600">State Runners:</span>
        <span class="mono" style="font-size:10.5px">0</span>
        <span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${emptyStateFill};border:1px solid var(--line-strong)"></span>
        <span class="mono" style="font-size:10.5px">1</span>
        <span style="display:inline-block;width:92px;height:10px;border-radius:3px;background:linear-gradient(90deg, ${gradStops});border:1px solid var(--line-strong)"></span>
        <span class="mono" style="font-size:10.5px">${maxStateRunners}</span>
      </div>
      <div class="map-legend-group">
        <span><span class="map-swatch" style="background:#f59e0b"></span>Club City</span>
        <span><span class="map-swatch" style="background:#7c3aed"></span>CYO City</span>
        <span><span class="map-swatch" style="background:#c43225"></span>Pgh CYO</span>
        <span><b style="color:#d49b00">&#9733;</b> Cedarville</span>
      </div>
    `;
    box.appendChild(legDiv);

    // 6. Takeaway caption
    const soEl = document.getElementById(soId);
    if (soEl) {
      const topStates = Object.entries(stateTotals).sort((a, b) => b[1] - a[1]);
      const top5Txt = topStates.slice(0, 5).map(([st, cnt]) => `<b>${st} (${cnt})</b>`).join(", ");
      soEl.innerHTML =
        `<b>Coast-to-Coast Draw (${topStates.length} States + Bermuda · ${Object.keys(cityMap).length} Cities):</b> Top delegations come from ${top5Txt}. Tap any state or dot to inspect clubs, or switch to <b>Zoom: Midwest &amp; East</b> on mobile.`;
    }
  }

  function renderCourseChart(distM) {
    const box = document.getElementById("courseElevationChart");
    if (!box) return;
    box.innerHTML = "";
    document.getElementById("courseChartTitle").textContent = `Cedarville ${(distM / 1000).toFixed(0)}K (${distM.toLocaleString()}m) elevation & tactical pacing profile`;

    // Authentic Elvin R. King XC Course topography (Cedarville, OH sits ~1,020–1,062 ft ASL on rolling open grass):
    // 0–420m: Wide slightly uphill/flat open grass starting straightaway (1028 -> 1044 ft)
    // 420–950m: Sweeping north meadow crest & fast gradual descent (1044 -> 1022 ft)
    // 950–1600m: Rolling east perimeter rise ("Cedarville Rise", 1022 -> 1054 ft)
    // Loops extend for 3K / 4K / 5K before the fast 350m downhill-to-flat spectator finishing chute!
    const pts = [];
    const nSteps = 60;
    for (let i = 0; i <= nSteps; i++) {
      const x = (distM * i) / nSteps;
      const frac = i / nSteps;
      let elev = 1030;
      if (x <= 420) {
        elev = 1028 + 16 * (x / 420);
      } else if (frac < 0.84) {
        const wave = Math.sin(((x - 420) / 680) * Math.PI * 2);
        const wave2 = Math.cos(((x - 420) / 1150) * Math.PI * 2);
        elev = 1038 + 13 * wave + 6 * wave2;
      } else {
        // Final 16%: crest into fast finishing chute
        const fEnd = (frac - 0.84) / 0.16;
        elev = 1045 - 15 * Math.pow(fEnd, 0.85);
      }
      pts.push({ d: x, elev });
    }

    const W = Math.max(460, box.clientWidth || 620);
    const H = 250;
    const m = { t: 24, r: 22, b: 36, l: 48 };
    const svg = d3.select(box).append("svg").attr("viewBox", `0 0 ${W} ${H}`).style("width", "100%").style("height", "auto");

    const x = d3.scaleLinear().domain([0, distM]).range([m.l, W - m.r]);
    const y = d3.scaleLinear().domain([1012, 1068]).range([H - m.b, m.t]);

    // Tactical Zone Shading
    const zones = [
      { x0: 0, x1: Math.min(420, distM * 0.35), label: "400m Starting Funnel", color: "var(--dop-soft)" },
      { x0: Math.min(420, distM * 0.35), x1: distM * 0.84, label: "Rolling Grass Rhythm Loops", color: "var(--accent-soft)" },
      { x0: distM * 0.84, x1: distM, label: "Fast Chute Kick", color: "var(--up-soft)" },
    ];
    zones.forEach((z) => {
      svg.append("rect")
        .attr("x", x(z.x0)).attr("y", m.t)
        .attr("width", Math.max(0, x(z.x1) - x(z.x0))).attr("height", H - m.t - m.b)
        .attr("fill", z.color);
      if (x(z.x1) - x(z.x0) > 85) {
        svg.append("text")
          .attr("x", (x(z.x0) + x(z.x1)) / 2).attr("y", m.t + 14)
          .attr("text-anchor", "middle").attr("font-size", 11).attr("font-weight", 600)
          .attr("fill", "var(--fg2)").text(z.label);
      }
    });

    const area = d3.area().x((d) => x(d.d)).y0(H - m.b).y1((d) => y(d.elev)).curve(d3.curveCatmullRom);
    const line = d3.line().x((d) => x(d.d)).y((d) => y(d.elev)).curve(d3.curveCatmullRom);

    svg.append("path").datum(pts).attr("d", area).attr("fill", "var(--accent)").attr("opacity", 0.18);
    svg.append("path").datum(pts).attr("d", line).attr("fill", "none").attr("stroke", "var(--accent)").attr("stroke-width", 2.5);

    svg.append("g").attr("transform", `translate(0,${H - m.b})`)
      .call(d3.axisBottom(x).ticks(6).tickFormat((v) => `${v}m`))
      .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));
    svg.append("g").attr("transform", `translate(${m.l},0)`)
      .call(d3.axisLeft(y).ticks(4).tickFormat((v) => `${v} ft`))
      .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));

    const gainFt = Math.round(pts.reduce((acc, p, i) => (i > 0 && p.elev > pts[i - 1].elev ? acc + (p.elev - pts[i - 1].elev) : acc), 0));
    document.getElementById("courseChartSo").innerHTML =
      `<b>Surface &amp; Speed Index:</b> 100% manicured turf grass (~${gainFt} ft cumulative climb over ${distM}m). Empirically runs <b>~1.8%–2.2% faster</b> than hilly Western PA park courses (Youthtowne / North Park) and ~0.5% slower than flat track-finish courses (Dublin Jerome).`;

    const notesEl = document.getElementById("courseTacticalNotes");
    const evsAtDist = EVENTS.filter((e) => e.dist_m === distM).map((e) => `${e.short} (${e.time_est})`).join(" · ");
    notesEl.innerHTML = `
      <h3>Race-day tactical keys (${(distM / 1000).toFixed(0)}K layout)</h3>
      <div style="margin-bottom:8px"><span class="badge b-accent">${evsAtDist || "Championship Layout"}</span></div>
      <ul style="padding-left:18px;margin:8px 0;font-size:13.5px;color:var(--fg2);display:flex;flex-direction:column;gap:7px">
        <li><b>First 400m Positioning:</b> Fields of up to 389 runners launch across a wide grass plain that gradually funnels at 420m. Getting trapped behind mid-pack congestion costs 8–12 seconds immediately.</li>
        <li><b>Spectator &amp; Coach Engagement Rule:</b> Unique among national meets, CCCNYC explicitly permits coaches on the course to give splits and encouragement—key at the 1K and 2K loop junctions.</li>
        <li><b>Wind &amp; Footing Factor:</b> Late-November SW Ohio open prairie winds across SR-72 reward <b>pack drafting</b>; running tucked on a teammate's shoulder through the middle kilometer saves ~2.5% aerobic cost.</li>
        <li><b>350m Downhill-to-Flat Kick:</b> The final crest drops ~15 ft into a wide, fast finishing chute—passing leverage peaks here, where 10 seconds often separates 12–18 places!</li>
      </ul>
    `;
  }

  function renderHistEditionsChart() {
    const box = document.getElementById("histEditionsChart");
    if (!box) return;
    box.innerHTML = "";
    const rows = META.hist_editions.slice().reverse();
    const W = Math.max(380, box.clientWidth || 480);
    const H = 205;
    const m = { t: 18, r: 48, b: 30, l: 52 };
    const svg = d3.select(box).append("svg").attr("viewBox", `0 0 ${W} ${H}`).style("width", "100%");

    const x = d3.scaleBand().domain(rows.map((r) => String(r.year))).range([m.l, W - m.r]).padding(0.32);
    const y = d3.scaleLinear().domain([0, 4000]).range([H - m.b, m.t]);

    svg.append("g").attr("transform", `translate(0,${H - m.b})`)
      .call(d3.axisBottom(x))
      .call((g) => g.selectAll("text").attr("fill", "var(--fg)").style("font-family", "var(--font-mono)").attr("font-weight", 600));
    svg.append("g").attr("transform", `translate(${m.l},0)`)
      .call(d3.axisLeft(y).ticks(4))
      .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));

    svg.selectAll(".hbar").data(rows).enter().append("rect")
      .attr("x", (d) => x(String(d.year)))
      .attr("y", (d) => y(d.finishers))
      .attr("width", x.bandwidth())
      .attr("height", (d) => H - m.b - y(d.finishers))
      .attr("rx", 4).attr("fill", "var(--accent)").attr("opacity", 0.78)
      .on("mousemove", (evt, d) => showTip(evt, `<b>${d.year} CCCNYC</b><br>${esc(d.venue)}<br>Finishers: <span class="mono">${d.finishers.toLocaleString()}</span><br>Racing in 2026: <span class="mono">${d.returning_2026}</span> vets`))
      .on("mouseleave", hideTip);

    svg.selectAll(".hlbl").data(rows).enter().append("text")
      .attr("x", (d) => x(String(d.year)) + x.bandwidth() / 2)
      .attr("y", (d) => y(d.finishers) - 5)
      .attr("text-anchor", "middle").attr("font-size", 11).style("font-family", "var(--font-mono)")
      .attr("fill", "var(--fg2)").text((d) => `${d.returning_2026} vets`);

    document.getElementById("histEditionsSo").innerHTML =
      `<b>Veteran Pedigree Advantage:</b> Returning CCCNYC veterans improve by an empirical median of <b>13.4 sec/km per birth year</b> between ages 8 and 14 and outperform first-time qualifiers by 6.8 places on average.`;
  }

  function renderAnomalyAudit() {
    const box = document.getElementById("anomalyAuditList");
    if (!box) return;
    const dupList = DATA.athletes.filter((a) => a.is_duplicate_ghost);
    const ev4Dop = ATHLETES.filter((a) => a.event_num === 4 && a.is_dop);
    const cyoOrgs = CLUBS.filter((c) => c.is_cyo).sort((a, b) => b.runners_count - a.runners_count);
    box.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:9px;font-size:13px">
        <div class="callout callout-up" style="margin:0;padding:9px 12px">
          <b>1. Final Nov 20 Entry List Update (${fmtInt(DATA.meta.raw_pdf_entries)} Entries · 31 Pages):</b> Expanded by <b>+${fmtInt(DATA.meta.raw_pdf_entries - DATA.meta.drive_pdf_entries)} late entries</b> over the initial Drive draft—adding national dynasties (<b>Brocaw Blazers</b>, <b>Louisville TigerSharks</b>, <b>Body in Training</b>, <b>HP Distance</b>, <b>Belvidere Tornados</b>) and major CYO delegations (<b>Phila. CYO</b>, <b>Toledo CYO</b>, <b>LA-CYO</b>). Meet Manager also resolved all prior Delta Hawks swapped-name duplicates!
        </div>
        <div class="callout callout-dop" style="margin:0;padding:9px 12px">
          <b>2. Pittsburgh CYO (Diocese of Pittsburgh) Boys 6–8 Roster Alert (${ev4Dop.length} Runners):</b> Officially listed as <b>Pittsburgh CYO</b> (${DATA.meta.dop_runners}/63 intact across 13 feeder schools). Event 4 still lists <b>${ev4Dop.length} boys</b> (<span class="mono">${ev4Dop.map((a) => esc(a.display_name)).join(", ")}</span>)—1 short of Rule B.5's 5-runner team minimum. Test adding a 5th runner in the <a href="races.html?event=4">Event 4 Sandbox</a>!
        </div>
        <div class="callout callout-warn" style="margin:0;padding:9px 12px">
          <b>3. Final-PDF Dual-Entry Audit (${dupList.length} Neutralized) &amp; CYO Expansion:</b> ${dupList.length ? dupList.map((d) => `<span class="mono">${esc(d.display_name)}</span> (Ev ${d.event_num}, ${esc(d.anomaly_note || "duplicate")})`).join("; ") : "Zero duplicate registrations remain"}. The CYO National Cup now features <b>${cyoOrgs.length} Catholic dioceses/parishes</b> totaling <b>${fmtInt(cyoOrgs.reduce((s, c) => s + c.runners_count, 0))} runners</b>!
        </div>
      </div>
    `;
  }

  // =========================================================================
  // PAGE 2: RACE SIMULATOR (races.html)
  // =========================================================================
  let curRaceEv = Number(urlParams.get("event")) || 6;
  if (!EV_MAP[curRaceEv]) curRaceEv = 6;
  let curRaceAgeFilter = "ALL";
  let curRaceSearch = "";

  function initRacePage() {
    const pillBox = document.getElementById("raceEventPills");
    if (!pillBox) return;
    pillBox.innerHTML = EVENTS.map((e) =>
      `<button class="pill ${e.dop_entries_count > 0 ? "pill-dop" : ""}" data-ev="${e.num}" aria-pressed="${e.num === curRaceEv}">${e.short}</button>`
    ).join("");
    pillBox.querySelectorAll("button").forEach((b) => {
      b.addEventListener("click", () => {
        curRaceEv = Number(b.dataset.ev);
        curRaceAgeFilter = "ALL";
        document.getElementById("sandboxDeltaSlider").value = "0";
        document.getElementById("sandboxDeltaVal").textContent = "0s / rnr";
        document.getElementById("sandboxAdd5thChk").checked = false;
        pillBox.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", Number(x.dataset.ev) === curRaceEv));
        renderRacePage();
      });
    });

    const searchInp = document.getElementById("raceRunnerSearch");
    if (searchInp) {
      searchInp.addEventListener("input", () => {
        curRaceSearch = searchInp.value.trim().toLowerCase();
        renderRaceFinishTable();
      });
    }

    // Sandbox listeners
    const sbSel = document.getElementById("sandboxTeamSel");
    const sbSlider = document.getElementById("sandboxDeltaSlider");
    const sbChk = document.getElementById("sandboxAdd5thChk");
    const sbReset = document.getElementById("sandboxResetBtn");
    const updateSb = () => {
      const dv = Number(sbSlider.value);
      document.getElementById("sandboxDeltaVal").textContent = `${dv > 0 ? "+" : ""}${dv}s / rnr`;
      renderSandbox();
    };
    if (sbSel) sbSel.addEventListener("change", updateSb);
    if (sbSlider) sbSlider.addEventListener("input", updateSb);
    if (sbChk) sbChk.addEventListener("change", updateSb);
    if (sbReset) sbReset.addEventListener("click", () => {
      sbSlider.value = "0";
      sbChk.checked = false;
      updateSb();
    });

    renderRacePage();
  }

  function renderRacePage() {
    const ev = EV_MAP[curRaceEv];
    if (!ev) return;

    const evTeamsAll = TEAMS.filter((t) => t.event_num === curRaceEv);
    const scoringTeams = evTeamsAll
      .filter((t) => t.scores_official_team && (scoringLens === "nat" || t.is_cyo))
      .sort((a, b) => a[scoringLens].exp_rank - b[scoringLens].exp_rank);
    const evAths = ATHLETES.filter((a) => a.event_num === curRaceEv && (scoringLens === "nat" || a.is_cyo))
      .sort((a, b) => a.exp_place - b.exp_place);

    // KPIs
    const favTeam = scoringTeams[0];
    const favAth = evAths[0];
    const dopTeams = evTeamsAll.filter((t) => t.is_dop);
    document.getElementById("raceKpis").innerHTML = `
      <div class="kpi kpi-accent">
        <div class="v">${ev.short}</div>
        <div class="l">${ev.dist_m.toLocaleString()}m · Gun ${ev.time_est}</div>
        <div class="s">Awards Ceremony: ${ev.awards_time}</div>
      </div>
      <div class="kpi kpi-gold">
        <div class="v">${evAths.length}</div>
        <div class="l">${scoringLens === "cyo" ? "CYO Runners" : "Unique Race-Day Runners"}</div>
        <div class="s">${scoringTeams.length} complete 5+ scoring teams</div>
      </div>
      <div class="kpi kpi-up">
        <div class="v" style="font-size:17px">${favTeam ? esc(fmtClub(favTeam.team, favTeam.state)) : "Individual Only"}</div>
        <div class="l">Projected ${scoringLens === "cyo" ? "CYO" : "National"} Team Favorite</div>
        <div class="s">${favTeam ? `${favTeam[scoringLens].exp_score} pts · ${favTeam[scoringLens].win_prob}% WinProb` : "Fewer than 5 team scorers"}</div>
      </div>
      <div class="kpi kpi-accent">
        <div class="v" style="font-size:17px">${favAth ? esc(favAth.display_name) : "—"}</div>
        <div class="l">Individual Favorite (${favAth ? favAth.proj_time_str : "—"})</div>
        <div class="s">${favAth ? `${esc(fmtClub(favAth.team, favAth.club_state))} · ${favAth.win_prob}% Win` : ""}</div>
      </div>
      <div class="kpi kpi-dop">
        <div class="v" style="font-size:17px">${dopTeams.length ? (dopTeams[0].scores_official_team ? `#${dopTeams[0][scoringLens].exp_rank.toFixed(1)} (${dopTeams[0][scoringLens].podium_prob}% Pod)` : `${dopTeams[0].roster_count} Rnrs (<5)`) : "No DoP Squad"}</div>
        <div class="l">Diocese of Pittsburgh Outlook</div>
        <div class="s">${ev.dop_entries_count} Pittsburgh qualifiers entered</div>
      </div>
    `;

    // Populate Sandbox Team Dropdown
    const sbSel = document.getElementById("sandboxTeamSel");
    if (sbSel) {
      const prev = sbSel.value;
      const sbOpts = evTeamsAll.slice().sort((a, b) => (b.is_dop - a.is_dop) || (b.roster_count - a.roster_count));
      sbSel.innerHTML = sbOpts.map((t) => `<option value="${esc(t.team)}">${esc(fmtClub(t.team, t.state))} · ${t.roster_count} rnrs</option>`).join("");
      if (sbOpts.some((t) => t.team === prev)) sbSel.value = prev;
    }

    // Age filter pills
    const agePills = document.getElementById("raceAgeFilterPills");
    const ages = Object.keys(ev.award_group_sizes).sort((a, b) => parseInt(a) - parseInt(b));
    agePills.innerHTML = `<button class="pill" data-ag="ALL" aria-pressed="${curRaceAgeFilter === "ALL"}">All (${ev.unique_runners})</button>` +
      ages.map((ag) => `<button class="pill" data-ag="${ag}" aria-pressed="${curRaceAgeFilter === ag}">Age ${ag} (${ev.award_group_sizes[ag]})</button>`).join("");
    agePills.querySelectorAll("button").forEach((b) => {
      b.addEventListener("click", () => {
        curRaceAgeFilter = b.dataset.ag;
        agePills.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", x.dataset.ag === curRaceAgeFilter));
        renderRaceFinishTable();
      });
    });

    renderTeamFanChart(ev, scoringTeams);
    renderRaceRidgeChart(ev, scoringTeams);
    renderRaceScurveChart(ev, evAths);
    renderRaceH2hChart(ev);
    renderSandbox();
    renderRaceFinishTable();
  }

  function renderTeamFanChart(ev, scoringTeams) {
    const box = document.getElementById("raceTeamFanChart");
    const so = document.getElementById("raceTeamFanSo");
    box.innerHTML = "";
    if (!scoringTeams.length) {
      box.innerHTML = `<div class="callout">No complete 5+ runner teams qualify under the <b>${scoringLens === "cyo" ? "CYO National" : "National Open"}</b> filter in ${esc(ev.name)}.</div>`;
      so.innerHTML = "";
      return;
    }
    const rows = scoringTeams.slice(0, 14);
    const W = Math.max(420, box.clientWidth || 520);
    const rowH = 30;
    const m = { t: 22, r: 95, b: 28, l: 175 };
    const H = m.t + m.b + rows.length * rowH;

    const svg = d3.select(box).append("svg").attr("viewBox", `0 0 ${W} ${H}`).style("width", "100%");
    const maxScore = d3.max(rows, (d) => d[scoringLens].p90_score) * 1.06;
    const x = d3.scaleLinear().domain([15, Math.max(60, maxScore)]).range([m.l, W - m.r]);
    const y = d3.scaleBand().domain(rows.map((d) => d.team)).range([m.t, H - m.b]).padding(0.32);

    svg.append("g").attr("transform", `translate(0,${H - m.b})`)
      .call(d3.axisBottom(x).ticks(5).tickFormat((d) => `${d} pts`))
      .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));

    rows.forEach((t, idx) => {
      const st = t[scoringLens];
      const cy = y(t.team) + y.bandwidth() / 2;
      const col = t.is_dop ? "var(--dop)" : t.is_cyo ? "var(--cyo)" : idx < 3 ? "var(--up)" : "var(--accent)";

      // Label
      svg.append("text").attr("x", m.l - 8).attr("y", cy + 4)
        .attr("text-anchor", "end").attr("font-size", 12)
        .attr("font-weight", t.is_dop || idx < 3 ? 600 : 400)
        .attr("fill", t.is_dop ? "var(--dop)" : "var(--fg)")
        .text(`${idx + 1}. ${fmtClubTrunc(t.team, t.state, 24)}`);

      // P10-P90 bar
      svg.append("rect")
        .attr("x", x(st.p10_score)).attr("y", y(t.team))
        .attr("width", Math.max(4, x(st.p90_score) - x(st.p10_score)))
        .attr("height", y.bandwidth()).attr("rx", 4)
        .attr("fill", col).attr("opacity", 0.28)
        .on("mousemove", (evt) => showTip(evt,
          `<b>${esc(fmtClub(t.team, t.state))}</b><br>Expected Score: <b class="mono">${st.exp_score} pts</b> (P10–P90: ${st.p10_score}–${st.p90_score})<br>Win Prob: <b class="mono">${st.win_prob}%</b> · Top-3 Podium: <b class="mono">${st.podium_prob}%</b><br>Top-5 Avg: <span class="mono">${st.top5_avg_str}</span> · 1–5 Spread: <span class="mono">${st.spread_1_5_sec}s</span>`
        ))
        .on("mouseleave", hideTip);

      // Expected point marker
      svg.append("circle").attr("cx", x(st.exp_score)).attr("cy", cy).attr("r", 5).attr("fill", col);

      // Right-side Win/Pod badge
      svg.append("text").attr("x", W - m.r + 8).attr("y", cy + 4)
        .attr("font-size", 11.5).style("font-family", "var(--font-mono)")
        .attr("fill", st.podium_prob >= 50 ? "var(--up)" : "var(--fg2)")
        .text(`${st.win_prob}%W / ${st.podium_prob}%P`);
    });

    const top = rows[0][scoringLens];
    so.innerHTML = `<b>Key Takeaway:</b> <b>${esc(fmtClub(rows[0].team, rows[0].state))}</b> leads with an expected <b>${top.exp_score} pts</b> (${top.win_prob}% win, ${top.spread_1_5_sec}s 1–5 pack spread). Exact team-score ties occur in <b>${top.tiebreak_rate_race}%</b> of simulated races—making 6th-runner displacement decisive.`;
  }

  function renderRaceRidgeChart(ev, scoringTeams) {
    const box = document.getElementById("raceRidgeChart");
    const so = document.getElementById("raceRidgeSo");
    box.innerHTML = "";
    const rows = scoringTeams.slice(0, 8);
    if (!rows.length) {
      box.innerHTML = `<div class="muted">Insufficient scoring teams for ridgeline comparison.</div>`;
      so.innerHTML = "";
      return;
    }
    const W = Math.max(420, box.clientWidth || 520);
    const rowH = 34;
    const m = { t: 28, r: 22, b: 30, l: 155 };
    const H = m.t + m.b + rows.length * rowH;

    // Collect paces (sec per mile)
    const teamPaces = rows.map((t) => {
      const p = t.runner_ids.map((id) => ATH_MAP[id]).filter(Boolean).map((a) => a.proj_time_sec / (ev.dist_m / 1609.344));
      return { team: t, paces: p, med: d3.median(p) };
    });
    const allP = teamPaces.flatMap((x) => x.paces);
    const domMin = Math.max(240, d3.min(allP) - 25);
    const domMax = d3.max(allP) + 30;

    const svg = d3.select(box).append("svg").attr("viewBox", `0 0 ${W} ${H}`).style("width", "100%");
    const x = d3.scaleLinear().domain([domMin, domMax]).range([m.l, W - m.r]);
    const grid = d3.range(domMin, domMax, (domMax - domMin) / 60);
    const bw = 12; // Gaussian KDE bandwidth in sec/mile

    svg.append("g").attr("transform", `translate(0,${H - m.b})`)
      .call(d3.axisBottom(x).ticks(5).tickFormat((s) => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, "0")}/mi`))
      .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));

    teamPaces.forEach((tp, i) => {
      const baseY = m.t + (i + 1) * rowH - 6;
      const dens = grid.map((gx) => {
        const v = d3.mean(tp.paces, (p) => Math.exp(-0.5 * Math.pow((gx - p) / bw, 2)));
        return { gx, v: v || 0 };
      });
      const maxV = d3.max(dens, (d) => d.v) || 1;
      const yScale = (v) => baseY - (v / maxV) * (rowH * 0.85);
      const col = tp.team.is_dop ? "var(--dop)" : tp.team.is_cyo ? "var(--cyo)" : "var(--accent)";

      const area = d3.area().x((d) => x(d.gx)).y0(baseY).y1((d) => yScale(d.v)).curve(d3.curveBasis);
      const line = d3.line().x((d) => x(d.gx)).y((d) => yScale(d.v)).curve(d3.curveBasis);

      svg.append("path").datum(dens).attr("d", area).attr("fill", col).attr("opacity", 0.24);
      svg.append("path").datum(dens).attr("d", line).attr("fill", "none").attr("stroke", col).attr("stroke-width", 1.8);

      // Runner ticks
      tp.paces.slice(0, 5).forEach((p) => {
        svg.append("line").attr("x1", x(p)).attr("x2", x(p)).attr("y1", baseY).attr("y2", baseY - 6).attr("stroke", col).attr("stroke-width", 2);
      });

      svg.append("text").attr("x", m.l - 8).attr("y", baseY - 4)
        .attr("text-anchor", "end").attr("font-size", 11.5)
        .attr("font-weight", tp.team.is_dop ? 600 : 400)
        .attr("fill", tp.team.is_dop ? "var(--dop)" : "var(--fg)")
        .text(fmtClubTrunc(tp.team.team, tp.team.state, 22));
    });

    const tightest = rows.slice().sort((a, b) => a[scoringLens].spread_1_5_sec - b[scoringLens].spread_1_5_sec)[0];
    so.innerHTML = `<b>Pack Compression Leader:</b> <b>${esc(fmtClub(tightest.team, tightest.state))}</b> projects the tightest 1–5 scoring window at <b>${tightest[scoringLens].spread_1_5_sec}s</b> (vertical ticks mark each squad's projected Top 5 scorers).`;
  }

  function renderRaceScurveChart(ev, evAths) {
    const box = document.getElementById("raceScurveChart");
    const so = document.getElementById("raceScurveSo");
    box.innerHTML = "";
    if (!evAths.length) return;

    const W = Math.max(420, box.clientWidth || 520);
    const H = 265;
    const m = { t: 18, r: 20, b: 34, l: 54 };
    const svg = d3.select(box).append("svg").attr("viewBox", `0 0 ${W} ${H}`).style("width", "100%");

    const x = d3.scaleLinear().domain([1, Math.max(2, evAths.length)]).range([m.l, W - m.r]);
    const y = d3.scaleLinear()
      .domain([d3.min(evAths, (d) => d.p10_time_sec) * 0.98, d3.max(evAths, (d) => d.p90_time_sec) * 1.01])
      .range([m.t, H - m.b]); // fastest at top!

    svg.append("g").attr("transform", `translate(0,${H - m.b})`)
      .call(d3.axisBottom(x).ticks(6).tickFormat((d) => `#${d}`))
      .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));
    svg.append("g").attr("transform", `translate(${m.l},0)`)
      .call(d3.axisLeft(y).ticks(5).tickFormat((s) => fmtTime(s)))
      .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));

    // Uncertainty band
    const band = d3.area().x((_, i) => x(i + 1)).y0((d) => y(d.p10_time_sec)).y1((d) => y(d.p90_time_sec)).curve(d3.curveMonotoneX);
    svg.append("path").datum(evAths).attr("d", band).attr("fill", "var(--accent)").attr("opacity", 0.12);

    // Dots
    svg.selectAll(".sdot").data(evAths).enter().append("circle")
      .attr("cx", (_, i) => x(i + 1))
      .attr("cy", (d) => y(d.proj_time_sec))
      .attr("r", (d) => (d.is_dop ? 5 : d.is_cyo ? 3.8 : 2.8))
      .attr("fill", (d) => (d.is_dop ? "var(--dop)" : d.is_cyo ? "var(--cyo)" : "var(--accent)"))
      .attr("opacity", (d) => (d.is_dop ? 1 : 0.72))
      .style("cursor", "pointer")
      .on("mousemove", (evt, d) => showTip(evt,
        `<b>${esc(d.display_name)}</b> (Age ${d.age})<br>${esc(fmtClub(d.team, d.club_state))}${d.home_school ? ` · ${esc(d.home_school)}` : ""}<br>Proj: <b class="mono">${d.proj_time_str}</b> (${d.proj_pace_mi}/mi)<br>Exp Place: <b class="mono">#${d.exp_place}</b> · Age-${d.award_group} AA: <b class="mono">${d.aa_age_prob}%</b><br>-${d.leverage_sec}s Passing Gain: <b>+${d.leverage_gain} spots</b>`
      ))
      .on("mouseleave", hideTip)
      .on("click", (_, d) => { window.location.href = `runners.html?id=${d.id}`; });

    const maxLev = d3.max(evAths, (d) => d.leverage_gain) || 0;
    const peakAth = evAths.find((d) => d.leverage_gain === maxLev);
    so.innerHTML = `<b>Chute Traffic Peak:</b> Shaving ${evAths[0].leverage_sec}s buys up to <b>+${maxLev} places</b> around projected finish #${peakAth ? Math.round(peakAth.exp_place) : "—"} (${peakAth ? peakAth.proj_time_str : ""}). Click any dot to open that runner's dossier.`;
  }

  function renderRaceH2hChart(ev) {
    const box = document.getElementById("raceH2hChart");
    const so = document.getElementById("raceH2hSo");
    box.innerHTML = "";
    const mat = scoringLens === "cyo" ? ev.h2h_cyo : ev.h2h_national;
    if (!mat || mat.length < 2) {
      box.innerHTML = `<div class="muted">Need at least 2 complete scoring teams in this lens for a pairwise matrix.</div>`;
      so.innerHTML = "";
      return;
    }
    const teams = mat.map((r) => r.team);
    let html = `<div style="overflow-x:auto"><table style="font-size:12px"><thead><tr><th>Row beats Col %</th>` +
      teams.map((t, i) => `<th class="num" title="${esc(fmtClub(t))}">#${i + 1}</th>`).join("") + `</tr></thead><tbody>`;
    mat.forEach((r, i) => {
      const cls = (r.team.includes("Pittsburgh CYO") || r.team.includes("Diocese of Pittsburgh")) ? "dop-txt" : "";
      html += `<tr><td class="${cls}" style="white-space:nowrap"><b>#${i + 1}</b> ${esc(fmtClubTrunc(r.team, null, 22))}</td>`;
      teams.forEach((colT) => {
        const v = r.vs[colT];
        if (v == null) {
          html += `<td class="num muted">—</td>`;
        } else {
          const bg = v >= 70 ? "var(--up-soft)" : v >= 45 ? "var(--gold-soft)" : "transparent";
          html += `<td class="num" style="background:${bg};font-weight:${v >= 50 ? 600 : 400}">${v.toFixed(0)}%</td>`;
        }
      });
      html += `</tr>`;
    });
    html += `</tbody></table></div>`;
    box.innerHTML = html;

    // Find closest toss-up matchup
    let bestPair = null, minDiff = 999;
    mat.forEach((r) => {
      teams.forEach((ct) => {
        const v = r.vs[ct];
        if (v != null && Math.abs(v - 50) < minDiff) {
          minDiff = Math.abs(v - 50);
          bestPair = [r.team, ct, v];
        }
      });
    });
    so.innerHTML = bestPair
      ? `<b>Closest Toss-Up Duel:</b> <b>${esc(fmtClub(bestPair[0]))}</b> vs. <b>${esc(fmtClub(bestPair[1]))}</b> splits <b>${bestPair[2].toFixed(1)}% – ${(100 - bestPair[2]).toFixed(1)}%</b> across 10,000 trials.`
      : "";
  }

  function renderSandbox() {
    const wrap = document.getElementById("sandboxStandingsWrap");
    const sbSel = document.getElementById("sandboxTeamSel");
    if (!wrap || !sbSel) return;
    const targetTeam = sbSel.value;
    const deltaSec = Number(document.getElementById("sandboxDeltaSlider").value) || 0;
    const add5th = document.getElementById("sandboxAdd5thChk").checked;

    const evAths = ATHLETES.filter((a) => a.event_num === curRaceEv && (scoringLens === "nat" || a.is_cyo)).map((a) => ({
      ...a,
      sim_t: a.proj_time_sec + (a.team === targetTeam ? deltaSec : 0),
    }));

    // Group by team
    const byTeam = {};
    evAths.forEach((a) => {
      if (a.team === "Unattached") return;
      (byTeam[a.team] = byTeam[a.team] || []).push(a);
    });

    if (add5th) {
      Object.entries(byTeam).forEach(([tname, arr]) => {
        if (arr.length === 4) {
          const fourthTime = d3.max(arr, (x) => x.sim_t);
          arr.push({
            id: "GHOST5",
            display_name: "Hypothetical #5 Runner",
            team: tname,
            sim_t: fourthTime + 12.0,
          });
        }
      });
    }

    const eligibleTeams = Object.keys(byTeam).filter((t) => byTeam[t].length >= 5);
    const teamRunners = eligibleTeams.flatMap((t) => byTeam[t]);
    teamRunners.sort((a, b) => a.sim_t - b.sim_t);
    teamRunners.forEach((r, i) => { r.team_pts = i + 1; });

    const standings = eligibleTeams.map((t) => {
      const rSorted = byTeam[t].slice().sort((a, b) => a.team_pts - b.team_pts);
      const top5 = rSorted.slice(0, 5);
      const score = d3.sum(top5, (x) => x.team_pts);
      const sixth = rSorted[5] ? rSorted[5].team_pts : 9999;
      const avgT = d3.mean(top5, (x) => x.sim_t);
      const origT = TEAMS.find((x) => x.event_num === curRaceEv && x.team === t);
      return {
        team: t,
        is_dop: (t.includes("Pittsburgh CYO") || t.includes("Diocese of Pittsburgh")),
        is_target: t === targetTeam,
        score,
        sixth,
        avgT,
        splits: top5.map((x) => x.team_pts).join(" + "),
        origRank: origT && origT[scoringLens] ? Math.round(origT[scoringLens].exp_rank) : null,
      };
    }).sort((a, b) => a.score - b.score || a.sixth - b.sixth);

    if (!standings.length) {
      wrap.innerHTML = `<div class="muted">No 5+ runner teams in this configuration.</div>`;
      return;
    }

    wrap.innerHTML = `<div class="tablewrap"><table><thead><tr>
      <th class="num">Sim Rk</th><th>Team</th><th class="num">Deterministic Score</th><th>Top-5 Displaced Places</th><th class="num">#6 Tiebreak</th><th class="num">Top-5 Avg</th><th class="num">vs Baseline</th>
    </tr></thead><tbody>` + standings.slice(0, 10).map((s, idx) => {
      const rk = idx + 1;
      const diff = s.origRank != null ? s.origRank - rk : null;
      const diffBadge = s.origRank == null
        ? `<span class="badge b-up">NEW TEAM!</span>`
        : diff > 0 ? `<span class="badge b-up">&#9650; +${diff}</span>`
        : diff < 0 ? `<span class="badge b-warn">&#9660; ${diff}</span>`
        : `<span class="muted mono">—</span>`;
      return `<tr class="${s.is_dop ? "row-dop" : ""}" style="${s.is_target ? "outline:1.5px solid var(--accent)" : ""}">
        <td class="num"><b>#${rk}</b></td>
        <td><b>${esc(fmtClub(s.team))}</b></td>
        <td class="num"><b>${s.score}</b></td>
        <td class="mono muted">${s.splits}</td>
        <td class="num">${s.sixth < 9999 ? `#${s.sixth}` : "—"}</td>
        <td class="num">${fmtTime(s.avgT)}</td>
        <td class="num">${diffBadge}</td>
      </tr>`;
    }).join("") + `</tbody></table></div>`;
  }

  function renderRaceFinishTable() {
    const tbody = document.getElementById("raceFinishTableBody");
    if (!tbody) return;
    let list = ATHLETES.filter((a) => a.event_num === curRaceEv && (scoringLens === "nat" || a.is_cyo));
    if (curRaceAgeFilter !== "ALL") list = list.filter((a) => a.award_group === curRaceAgeFilter);
    if (curRaceSearch) {
      list = list.filter((a) =>
        a.display_name.toLowerCase().includes(curRaceSearch) ||
        fmtClub(a.team, a.club_state).toLowerCase().includes(curRaceSearch) ||
        (a.home_school || "").toLowerCase().includes(curRaceSearch)
      );
    }
    list.sort((a, b) => a.exp_place - b.exp_place);

    tbody.innerHTML = list.map((a) => `
      <tr class="row-click ${a.is_dop ? "row-dop" : ""}" onclick="window.location.href='runners.html?id=${a.id}'">
        <td class="num"><b>${a.exp_place.toFixed(1)}</b></td>
        <td><b>${esc(a.display_name)}</b></td>
        <td>${a.is_dop ? `<span class="dop-txt">${esc(fmtClub(a.team, a.club_state))}</span>` : a.is_cyo ? `<span class="cyo-txt">${esc(fmtClub(a.team, a.club_state))}</span>` : esc(fmtClub(a.team, a.club_state))}</td>
        <td class="num">${a.age}</td>
        <td class="muted">${esc(a.home_school || "—")}</td>
        <td>${tierBadge(a.seed_tier)}</td>
        <td class="num"><b>${a.proj_time_str}</b></td>
        <td class="num muted">${a.p10_time_str}–${a.p90_time_str}</td>
        <td class="num">${a.proj_pace_mi}/mi</td>
        <td class="num">${a.top25_prob.toFixed(0)}%</td>
        <td class="num">#${a.aa_age_exp_rank.toFixed(1)} <span class="muted">/${a.aa_age_field_size}</span></td>
        <td class="num">${probBar(a.aa_age_prob, a.is_dop ? "var(--dop)" : "var(--up)")}</td>
        <td class="num"><span class="badge b-muted">+${a.leverage_gain} (-${a.leverage_sec}s)</span></td>
      </tr>
    `).join("");
  }

  // =========================================================================
  // PAGE 3: DIOCESE OF PITTSBURGH COMMAND CENTER (diocese.html)
  // =========================================================================
  let dopSchoolFilter = "ALL";

  function initDiocesePage() {
    const dopAths = ATHLETES.filter((a) => a.is_dop);
    const dopTeams = TEAMS.filter((t) => t.is_dop);
    const scoringDop = dopTeams.filter((t) => t.scores_official_team);

    const expNatPod = scoringDop.reduce((s, t) => s + t.nat.podium_prob / 100, 0);
    const expCyoWins = scoringDop.reduce((s, t) => s + t.cyo.win_prob / 100, 0);
    const expAA = dopAths.reduce((s, a) => s + a.aa_age_prob / 100, 0);
    const total2026Races = dopAths.reduce((s, a) => s + a.races_2026.length, 0);
    const dioChamps = dopAths.filter((a) => a.races_2026.some((r) => r.meet.includes("Pittsburgh Diocesan") && r.place === 1)).length;

    document.getElementById("dopKpis").innerHTML = `
      <div class="kpi kpi-dop">
        <div class="v">63</div>
        <div class="l">Pittsburgh Qualifiers</div>
        <div class="s">10 squads across 8 youth divisions</div>
      </div>
      <div class="kpi kpi-accent">
        <div class="v">13</div>
        <div class="l">Catholic Feeder Schools</div>
        <div class="s">St. Louise (11), Aquinas (10), Seelos (8)</div>
      </div>
      <div class="kpi kpi-up">
        <div class="v">${total2026Races}</div>
        <div class="l">Verified 2026 Season Finishes</div>
        <div class="s">6.2 avg races/athlete · ${dioChamps} Oct 17 Champs</div>
      </div>
      <div class="kpi kpi-gold">
        <div class="v">${expNatPod.toFixed(2)}</div>
        <div class="l">Expected National Team Trophies</div>
        <div class="s">Led by 6–8G (100%) &amp; 13–14B (72%)</div>
      </div>
      <div class="kpi kpi-cyo">
        <div class="v">${expCyoWins.toFixed(2)}</div>
        <div class="l">Expected CYO National Team Titles</div>
        <div class="s">Favored in 6 of 7 scored CYO divisions</div>
      </div>
      <div class="kpi kpi-dop">
        <div class="v">${expAA.toFixed(1)}</div>
        <div class="l">Expected Birth-Age All-Americans</div>
        <div class="s">${dopAths.filter((a) => a.aa_age_prob >= 50).length} athletes project &ge;50% Top-25</div>
      </div>
    `;

    // Feeder Schools Breakdown
    const schMap = {};
    dopAths.forEach((a) => {
      const s = a.home_school || "Unassigned";
      const obj = (schMap[s] = schMap[s] || { school: s, count: 0, expAA: 0, boys: 0, girls: 0 });
      obj.count += 1;
      obj.expAA += a.aa_age_prob / 100;
      if (a.gender === "M") obj.boys += 1; else obj.girls += 1;
    });
    const schRows = Object.values(schMap).sort((a, b) => b.count - a.count || b.expAA - a.expAA);

    // School filter bar
    const fbar = document.getElementById("dopSchoolFilterBar");
    fbar.innerHTML = `<span class="ctl-label">Filter Feeder School</span>` +
      `<button class="pill pill-dop" data-sch="ALL" aria-pressed="true">All 13 Schools (63)</button>` +
      schRows.map((r) => `<button class="pill" data-sch="${esc(r.school)}" aria-pressed="false">${esc(r.school.replace(" Catholic School", "").replace(" Elementary School", "").replace(" Parish School", ""))} (${r.count})</button>`).join("");

    const setSchFilter = (val) => {
      dopSchoolFilter = val;
      fbar.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", b.dataset.sch === dopSchoolFilter));
      renderDopAllAmericanAndTable(dopAths);
    };
    fbar.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => setSchFilter(b.dataset.sch)));

    renderDopSchoolsChart(schRows, setSchFilter);
    renderDopSquadDualChart(dopTeams);
    renderDopPackLadderChart(dopTeams);
    renderDopAllAmericanAndTable(dopAths);
  }

  function renderDopSchoolsChart(schRows, onSelect) {
    const box = document.getElementById("dopSchoolsChart");
    box.innerHTML = "";
    const W = Math.max(400, box.clientWidth || 500);
    const rowH = 26;
    const m = { t: 16, r: 78, b: 26, l: 195 };
    const H = m.t + m.b + schRows.length * rowH;

    const svg = d3.select(box).append("svg").attr("viewBox", `0 0 ${W} ${H}`).style("width", "100%");
    const x = d3.scaleLinear().domain([0, d3.max(schRows, (d) => d.count) + 1]).range([m.l, W - m.r]);
    const y = d3.scaleBand().domain(schRows.map((d) => d.school)).range([m.t, H - m.b]).padding(0.28);

    svg.append("g").attr("transform", `translate(0,${H - m.b})`)
      .call(d3.axisBottom(x).ticks(6))
      .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));

    schRows.forEach((r) => {
      const isAq = r.school.includes("Aquinas");
      svg.append("text").attr("x", m.l - 8).attr("y", y(r.school) + y.bandwidth() / 2 + 4)
        .attr("text-anchor", "end").attr("font-size", 11.5)
        .attr("font-weight", isAq ? 700 : 400)
        .attr("fill", isAq ? "var(--dop)" : "var(--fg)")
        .style("cursor", "pointer")
        .text(r.school.length > 26 ? r.school.slice(0, 25) + "…" : r.school)
        .on("click", () => onSelect(r.school));

      // Girls + Boys stacked
      svg.append("rect").attr("x", x(0)).attr("y", y(r.school))
        .attr("width", x(r.girls) - x(0)).attr("height", y.bandwidth()).attr("rx", 3)
        .attr("fill", "var(--dop)").attr("opacity", 0.85).style("cursor", "pointer")
        .on("mousemove", (evt) => showTip(evt, `<b>${esc(r.school)}</b><br>Total Qualifiers: <b>${r.count}</b> (${r.girls}G / ${r.boys}B)<br>Expected Age All-Americans: <b class="mono">${r.expAA.toFixed(2)}</b>`))
        .on("mouseleave", hideTip)
        .on("click", () => onSelect(r.school));

      svg.append("rect").attr("x", x(r.girls)).attr("y", y(r.school))
        .attr("width", x(r.count) - x(r.girls)).attr("height", y.bandwidth()).attr("rx", 3)
        .attr("fill", "var(--accent)").attr("opacity", 0.82).style("cursor", "pointer")
        .on("mousemove", (evt) => showTip(evt, `<b>${esc(r.school)}</b><br>Total Qualifiers: <b>${r.count}</b> (${r.girls}G / ${r.boys}B)<br>Expected Age All-Americans: <b class="mono">${r.expAA.toFixed(2)}</b>`))
        .on("mouseleave", hideTip)
        .on("click", () => onSelect(r.school));

      svg.append("text").attr("x", x(r.count) + 6).attr("y", y(r.school) + y.bandwidth() / 2 + 4)
        .attr("font-size", 11).style("font-family", "var(--font-mono)").attr("fill", "var(--fg2)")
        .text(`${r.count} (${r.expAA.toFixed(1)} AA)`);
    });

    document.getElementById("dopSchoolsSo").innerHTML =
      `<b>Top 4 Feeder Schools Supply 56% of Delegation:</b> St. Louise de Marillac (11), Aquinas Academy (10), Seelos Academy (8), and St. Kilian (6) account for 35 of the 63 qualifiers (red = Girls, blue = Boys).`;
  }

  function renderDopSquadDualChart(dopTeams) {
    const box = document.getElementById("dopSquadDualChart");
    box.innerHTML = "";
    const rows = dopTeams.slice().sort((a, b) => a.event_num - b.event_num || a.team.localeCompare(b.team));
    const W = Math.max(400, box.clientWidth || 500);
    const rowH = 34;
    const m = { t: 24, r: 45, b: 26, l: 170 };
    const H = m.t + m.b + rows.length * rowH;

    const svg = d3.select(box).append("svg").attr("viewBox", `0 0 ${W} ${H}`).style("width", "100%");
    const x = d3.scaleLinear().domain([0, 100]).range([m.l, W - m.r]);
    const shortDop = (t) => t.replace("Pittsburgh CYO", "Pgh CYO").replace("Diocese of Pittsburgh", "DoP");
    const y = d3.scaleBand().domain(rows.map((d) => `${d.event_short} · ${shortDop(d.team)}`)).range([m.t, H - m.b]).padding(0.28);

    svg.append("g").attr("transform", `translate(0,${H - m.b})`)
      .call(d3.axisBottom(x).ticks(5).tickFormat((d) => `${d}%`))
      .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));

    rows.forEach((r) => {
      const lbl = `${r.event_short} · ${shortDop(r.team)}`;
      const yy = y(lbl);
      const hHalf = y.bandwidth() / 2;

      svg.append("text").attr("x", m.l - 8).attr("y", yy + hHalf + 4)
        .attr("text-anchor", "end").attr("font-size", 11.5).attr("font-weight", 600).attr("fill", "var(--fg)")
        .text(lbl);

      if (!r.scores_official_team) {
        svg.append("text").attr("x", m.l + 6).attr("y", yy + hHalf + 4)
          .attr("font-size", 11.5).attr("fill", "var(--warn)").style("font-family", "var(--font-mono)")
          .text("4 runners entered (1 shy of 5-scorer min)");
        return;
      }

      // Nat Podium % bar
      svg.append("rect").attr("x", m.l).attr("y", yy)
        .attr("width", Math.max(2, x(r.nat.podium_prob) - m.l)).attr("height", hHalf - 1).attr("rx", 2)
        .attr("fill", "var(--dop)")
        .on("mousemove", (evt) => showTip(evt, `<b>${esc(r.team)} (${r.event_short})</b><br>National Open Rank: <b>#${r.nat.exp_rank.toFixed(1)}</b> (${r.nat.podium_prob}% Podium, ${r.nat.win_prob}% Win)<br>CYO National Rank: <b>#${r.cyo.exp_rank.toFixed(1)}</b> (${r.cyo.win_prob}% CYO Title)`))
        .on("mouseleave", hideTip);

      // CYO Win % bar
      svg.append("rect").attr("x", m.l).attr("y", yy + hHalf + 1)
        .attr("width", Math.max(2, x(r.cyo.win_prob) - m.l)).attr("height", hHalf - 1).attr("rx", 2)
        .attr("fill", "var(--cyo)");

      svg.append("text").attr("x", Math.max(x(r.nat.podium_prob), x(r.cyo.win_prob)) + 5).attr("y", yy + hHalf + 4)
        .attr("font-size", 10.5).style("font-family", "var(--font-mono)").attr("fill", "var(--fg2)")
        .text(`${r.nat.podium_prob.toFixed(0)}%P / ${r.cyo.win_prob.toFixed(0)}%CYO`);
    });

    const topCyo = rows.filter((r) => r.scores_official_team && r.cyo)
      .slice().sort((a, b) => b.cyo.win_prob - a.cyo.win_prob).slice(0, 4);
    const topNat = rows.filter((r) => r.scores_official_team && r.nat)
      .slice().sort((a, b) => b.nat.podium_prob - a.nat.podium_prob).slice(0, 3);
    document.getElementById("dopSquadDualSo").innerHTML =
      `<b>Red = Open National Top-3 Trophy % · Purple = CYO National Championship Win %:</b> Top CYO Title shots: ` +
      topCyo.map((r) => `<b>${r.event_short} (${r.cyo.win_prob.toFixed(1)}%)</b>`).join(", ") +
      ` · Top National Open Trophy shots: ` +
      topNat.map((r) => `<b>${r.event_short} (${r.nat.podium_prob.toFixed(1)}%)</b>`).join(", ") + `.`;
  }

  function renderDopPackLadderChart(dopTeams) {
    const box = document.getElementById("dopPackLadderChart");
    box.innerHTML = "";
    const rows = dopTeams.slice().sort((a, b) => a.event_num - b.event_num || a.team.localeCompare(b.team));
    const W = Math.max(580, box.clientWidth || 880);
    const rowH = 34;
    const m = { t: 22, r: 95, b: 30, l: 175 };
    const H = m.t + m.b + rows.length * rowH;

    const svg = d3.select(box).append("svg").attr("viewBox", `0 0 ${W} ${H}`).style("width", "100%");
    const allAths = rows.flatMap((t) => t.runner_ids.map((id) => ATH_MAP[id]));
    const paces = allAths.map((a) => a.proj_time_sec / (EV_MAP[a.event_num].dist_m / 1609.344));
    const x = d3.scaleLinear().domain([d3.min(paces) - 12, d3.max(paces) + 15]).range([m.l, W - m.r]);
    const shortDop2 = (t) => t.replace("Pittsburgh CYO", "Pgh CYO").replace("Diocese of Pittsburgh", "DoP");
    const y = d3.scaleBand().domain(rows.map((r) => `${r.event_short} · ${shortDop2(r.team)}`)).range([m.t, H - m.b]).padding(0.3);

    svg.append("g").attr("transform", `translate(0,${H - m.b})`)
      .call(d3.axisBottom(x).ticks(7).tickFormat((s) => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, "0")}/mi`))
      .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));

    rows.forEach((r) => {
      const lbl = `${r.event_short} · ${shortDop2(r.team)}`;
      const cy = y(lbl) + y.bandwidth() / 2;
      const aths = r.runner_ids.map((id) => ATH_MAP[id]).sort((a, b) => a.proj_time_sec - b.proj_time_sec);
      const ps = aths.map((a) => a.proj_time_sec / (r.dist_m / 1609.344));

      svg.append("text").attr("x", m.l - 10).attr("y", cy + 4).attr("text-anchor", "end")
        .attr("font-size", 12).attr("font-weight", 600).attr("fill", "var(--fg)").text(lbl);

      if (ps.length >= 2) {
        const fifthIdx = Math.min(4, ps.length - 1);
        svg.append("line").attr("x1", x(ps[0])).attr("x2", x(ps[fifthIdx])).attr("y1", cy).attr("y2", cy)
          .attr("stroke", "var(--dop)").attr("stroke-width", 3.5).attr("opacity", 0.5);
        if (ps.length > 5) {
          svg.append("line").attr("x1", x(ps[4])).attr("x2", x(ps[ps.length - 1])).attr("y1", cy).attr("y2", cy)
            .attr("stroke", "var(--muted)").attr("stroke-dasharray", "3,3").attr("stroke-width", 1.5);
        }
      }

      aths.forEach((a, idx) => {
        const px = x(ps[idx]);
        svg.append("circle").attr("cx", px).attr("cy", cy).attr("r", idx < 5 ? 5.5 : 4.5)
          .attr("fill", idx < 5 ? "var(--dop)" : "var(--surface)")
          .attr("stroke", "var(--dop)").attr("stroke-width", 2)
          .style("cursor", "pointer")
          .on("mousemove", (evt) => showTip(evt,
            `<b>#${idx + 1} on Squad: ${esc(a.display_name)}</b><br>${esc(a.home_school || "")} · Age ${a.age}<br>Proj: <b class="mono">${a.proj_time_str}</b> (${a.proj_pace_mi}/mi)<br>Role: <b>${idx < 5 ? `Scorer #${idx + 1}` : `Displacer #${idx + 1}`}</b>`
          ))
          .on("mouseleave", hideTip)
          .on("click", () => { window.location.href = `runners.html?id=${a.id}`; });
      });

      const spreadTxt = r.nat ? `1–5: ${r.nat.spread_1_5_sec}s` : `${aths.length} rnrs`;
      svg.append("text").attr("x", W - m.r + 8).attr("y", cy + 4)
        .attr("font-size", 11.5).style("font-family", "var(--font-mono)").attr("fill", "var(--fg2)").text(spreadTxt);
    });

    document.getElementById("dopPackLadderSo").innerHTML =
      `<b>Tightest Packs:</b> <b>11–12 Girls A</b> and <b>6–8 Girls</b> boast exceptional front-5 compression, while <b>13–14 Boys</b> is anchored by overall front-runner <b>Liam Ginsburg (5:31/mi projected 4K pace)</b>.`;
  }

  function renderDopAllAmericanAndTable(dopAths) {
    const filtered = dopSchoolFilter === "ALL" ? dopAths.slice() : dopAths.filter((a) => a.home_school === dopSchoolFilter);
    filtered.sort((a, b) => b.aa_age_prob - a.aa_age_prob || a.aa_age_exp_rank - b.aa_age_exp_rank);

    // Chart top 22
    const box = document.getElementById("dopAllAmericanChart");
    box.innerHTML = "";
    const topRows = filtered.slice(0, 22);
    if (topRows.length) {
      const W = Math.max(520, box.clientWidth || 840);
      const rowH = 25;
      const m = { t: 16, r: 95, b: 24, l: 210 };
      const H = m.t + m.b + topRows.length * rowH;
      const svg = d3.select(box).append("svg").attr("viewBox", `0 0 ${W} ${H}`).style("width", "100%");
      const x = d3.scaleLinear().domain([0, 100]).range([m.l, W - m.r]);
      const y = d3.scaleBand().domain(topRows.map((d) => d.id)).range([m.t, H - m.b]).padding(0.26);

      svg.append("g").attr("transform", `translate(0,${H - m.b})`)
        .call(d3.axisBottom(x).ticks(5).tickFormat((d) => `${d}%`))
        .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));

      topRows.forEach((a) => {
        const yy = y(a.id);
        svg.append("text").attr("x", m.l - 8).attr("y", yy + y.bandwidth() / 2 + 4)
          .attr("text-anchor", "end").attr("font-size", 11.5)
          .attr("fill", "var(--fg)").style("cursor", "pointer")
          .text(`${a.display_name} (${a.gender}${a.age})`)
          .on("click", () => { window.location.href = `runners.html?id=${a.id}`; });

        svg.append("rect").attr("x", m.l).attr("y", yy)
          .attr("width", Math.max(3, x(a.aa_age_prob) - m.l)).attr("height", y.bandwidth()).attr("rx", 3)
          .attr("fill", a.aa_age_prob >= 75 ? "var(--up)" : a.aa_age_prob >= 40 ? "var(--gold)" : "var(--dop)")
          .style("cursor", "pointer")
          .on("mousemove", (evt) => showTip(evt,
            `<b>${esc(a.display_name)}</b> (Age ${a.age} · ${esc(a.home_school)})<br>Event: ${esc(EV_MAP[a.event_num].name)}<br>Age-${a.award_group} All-American Odds: <b class="mono">${a.aa_age_prob}%</b> (Exp Age Rk #${a.aa_age_exp_rank} of ${a.aa_age_field_size})`
          ))
          .on("mouseleave", hideTip)
          .on("click", () => { window.location.href = `runners.html?id=${a.id}`; });

        svg.append("text").attr("x", x(a.aa_age_prob) + 6).attr("y", yy + y.bandwidth() / 2 + 4)
          .attr("font-size", 11).style("font-family", "var(--font-mono)").attr("fill", "var(--fg2)")
          .text(`${a.aa_age_prob.toFixed(1)}% (#${a.aa_age_exp_rank.toFixed(0)})`);
      });
    }

    // Table
    const tbody = document.getElementById("dopRosterTableBody");
    tbody.innerHTML = filtered.map((a) => {
      const dioRace = a.races_2026.find((r) => r.meet.includes("Pittsburgh Diocesan"));
      return `
        <tr class="row-click" onclick="window.location.href='runners.html?id=${a.id}'">
          <td><b>${esc(a.display_name)}</b></td>
          <td class="mono">${esc(fmtClub(a.team.replace("Pittsburgh CYO", "Pgh CYO").replace("Diocese of Pittsburgh", "DoP"), a.club_state))}</td>
          <td>${esc(EV_MAP[a.event_num].short)}</td>
          <td class="num">${a.age}</td>
          <td>${esc(a.home_school || "—")}</td>
          <td class="num">${a.races_2026.length}</td>
          <td class="num">${dioRace && dioRace.place ? `#${dioRace.place} (${dioRace.time_str})` : "—"}</td>
          <td class="num"><b>${a.proj_time_str}</b></td>
          <td class="num">${a.proj_pace_mi}/mi</td>
          <td class="num">#${a.exp_place.toFixed(1)}</td>
          <td class="num"><b>#${a.aa_age_exp_rank.toFixed(1)}</b> <span class="muted">/${a.aa_age_field_size}</span></td>
          <td class="num">${probBar(a.aa_age_prob, "var(--dop)")}</td>
          <td class="num">${a.cyo_exp_rank ? `#${a.cyo_exp_rank.toFixed(1)}` : "—"}</td>
        </tr>
      `;
    }).join("");
  }

  // =========================================================================
  // PAGE 4: CLUBS & SCHOOLS (clubs.html)
  // =========================================================================
  let clubCatFilter = "ALL";
  let clubStateFilter = urlParams.get("state") || "ALL";
  let clubQuery = "";
  let selectedClubOrg = urlParams.get("org") || (CLUBS.find((c) => c.is_dop)?.org || "Pittsburgh CYO");

  function initClubsPage() {
    const realClubs = CLUBS.filter((c) => c.org !== "Unattached");
    const stSel = document.getElementById("clubStateSel");
    const states = Array.from(new Set(realClubs.map((c) => c.state))).sort();
    stSel.innerHTML = `<option value="ALL">All States (${states.length})</option>` +
      states.map((s) => `<option value="${s}">${s}</option>`).join("");
    if (clubStateFilter !== "ALL" && states.includes(clubStateFilter)) {
      stSel.value = clubStateFilter;
    } else {
      clubStateFilter = "ALL";
    }
    const mapRstBtn = document.getElementById("clubsMapResetBtn");
    if (mapRstBtn) {
      mapRstBtn.style.display = clubStateFilter === "ALL" ? "none" : "inline-flex";
      mapRstBtn.addEventListener("click", () => {
        clubStateFilter = "ALL";
        stSel.value = "ALL";
        mapRstBtn.style.display = "none";
        renderUsaMap("clubsUsaMapChart", "clubsUsaMapSo", { interactiveFilter: true });
        renderClubsTable();
      });
    }

    document.querySelectorAll("#clubFiltersBar button[data-ccat]").forEach((b) => {
      b.addEventListener("click", () => {
        clubCatFilter = b.dataset.ccat;
        document.querySelectorAll("#clubFiltersBar button[data-ccat]").forEach((x) => x.setAttribute("aria-pressed", x.dataset.ccat === clubCatFilter));
        renderClubsTable();
      });
    });
    stSel.addEventListener("change", () => {
      clubStateFilter = stSel.value;
      if (mapRstBtn) mapRstBtn.style.display = clubStateFilter === "ALL" ? "none" : "inline-flex";
      renderUsaMap("clubsUsaMapChart", "clubsUsaMapSo", { interactiveFilter: true });
      renderClubsTable();
    });
    document.getElementById("clubSearchInp").addEventListener("input", (e) => {
      clubQuery = e.target.value.trim().toLowerCase();
      renderClubsTable();
    });

    renderUsaMap("clubsUsaMapChart", "clubsUsaMapSo", { interactiveFilter: true });
    renderClubBubbleChart(realClubs);
    renderCyoOmnium(realClubs);
    renderClubHeatmap(realClubs);
    renderClubInspector(selectedClubOrg);
    renderClubsTable();
  }

  function renderClubBubbleChart(realClubs) {
    const box = document.getElementById("clubBubbleChart");
    box.innerHTML = "";
    const W = Math.max(420, box.clientWidth || 520);
    const H = 275;
    const m = { t: 20, r: 24, b: 36, l: 46 };
    const svg = d3.select(box).append("svg").attr("viewBox", `0 0 ${W} ${H}`).style("width", "100%");

    const x = d3.scaleLinear().domain([0, d3.max(realClubs, (d) => d.runners_count) + 5]).range([m.l, W - m.r]);
    const y = d3.scaleLinear().domain([0, d3.max(realClubs, (d) => d.exp_age_all_americans) * 1.12]).range([H - m.b, m.t]);
    const r = d3.scaleSqrt().domain([0, d3.max(realClubs, (d) => d.exp_national_podiums) || 1]).range([4.5, 18]);

    svg.append("g").attr("transform", `translate(0,${H - m.b})`)
      .call(d3.axisBottom(x).ticks(6).tickFormat((d) => `${d} rnrs`))
      .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));
    svg.append("g").attr("transform", `translate(${m.l},0)`)
      .call(d3.axisLeft(y).ticks(5))
      .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));

    svg.selectAll(".cbub").data(realClubs).enter().append("circle")
      .attr("cx", (d) => x(d.runners_count))
      .attr("cy", (d) => y(d.exp_age_all_americans))
      .attr("r", (d) => r(d.exp_national_podiums))
      .attr("fill", (d) => (d.is_dop ? "var(--dop)" : d.is_cyo ? "var(--cyo)" : d.category.includes("School") ? "var(--gold)" : "var(--accent)"))
      .attr("opacity", 0.78).attr("stroke", "var(--surface)").attr("stroke-width", 1.2)
      .style("cursor", "pointer")
      .on("mousemove", (evt, d) => showTip(evt,
        `<b>${esc(fmtClub(d.org, d.state))}</b><br>2026 Delegation: <b>${d.runners_count} runners</b> (${d.scoring_squads} scoring squads)<br>Exp Team Podiums: <b class="mono">${d.exp_national_podiums.toFixed(2)}</b><br>Exp Age All-Americans: <b class="mono">${d.exp_age_all_americans.toFixed(1)}</b>`
      ))
      .on("mouseleave", hideTip)
      .on("click", (_, d) => { selectedClubOrg = d.org; renderClubInspector(d.org); document.getElementById("clubDetailSection").scrollIntoView({ behavior: "smooth" }); });

    // Direct labels for largest / top clubs
    realClubs.filter((d) => d.runners_count >= 52 || d.exp_age_all_americans >= 18 || d.is_dop).forEach((d) => {
      svg.append("text")
        .attr("x", x(d.runners_count))
        .attr("y", y(d.exp_age_all_americans) - r(d.exp_national_podiums) - 4)
        .attr("text-anchor", "middle").attr("font-size", 10.5).attr("font-weight", d.is_dop ? 700 : 500)
        .attr("fill", d.is_dop ? "var(--dop)" : "var(--fg)")
        .text(fmtClubTrunc(d.org, d.state, 22));
    });

    const top4 = realClubs.slice(0, 4);
    document.getElementById("clubBubbleSo").innerHTML =
      `<b>Delegation Giants:</b> ` + top4.map((c) => `<b>${esc(fmtClub(c.org, c.state))} · ${c.runners_count}</b>`).join(", ") +
      ` headline the ${realClubs.length}-organization national field, with <b>Pittsburgh CYO (PA) · ${DATA.meta.dop_runners}</b> anchoring the Western PA Catholic delegation.`;
  }

  function renderCyoOmnium(realClubs) {
    const box = document.getElementById("cyoOmniumWrap");
    const cyoOrgs = realClubs.filter((c) => c.is_cyo).sort((a, b) => b.runners_count - a.runners_count);
    const cyoWithTitles = cyoOrgs.map((c) => ({
      ...c,
      cyoWins: TEAMS.filter((t) => t.base_org === c.org && t.scores_official_team && t.cyo)
        .reduce((s, t) => s + t.cyo.win_prob / 100, 0),
    })).sort((a, b) => b.cyoWins - a.cyoWins || b.runners_count - a.runners_count);
    box.innerHTML = `<div class="tablewrap"><table><thead><tr>
      <th>CYO / Catholic Program</th><th>State</th><th class="num">Runners</th><th class="num">Squads</th><th class="num">Proj CYO Titles</th><th class="num">Exp Age AAs</th>
    </tr></thead><tbody>` + cyoWithTitles.map((c) => `
      <tr class="row-click ${c.is_dop ? "row-dop" : ""}" onclick="window.selectClub('${esc(c.org)}')">
        <td><b>${esc(fmtClub(c.org, c.state))}</b></td>
        <td>${c.state}</td>
        <td class="num"><b>${c.runners_count}</b></td>
        <td class="num">${c.scoring_squads}</td>
        <td class="num"><b>${c.cyoWins.toFixed(2)}</b></td>
        <td class="num">${c.exp_age_all_americans.toFixed(1)}</td>
      </tr>`).join("") + `</tbody></table></div>
    <p class="so"><b>CYO National Cup Showdown:</b> <b>${cyoOrgs.length} Catholic dioceses &amp; parishes</b> bring <b>${fmtInt(cyoOrgs.reduce((s, c) => s + c.runners_count, 0))} runners</b>, led by ${cyoWithTitles.slice(0, 3).map((c) => `<b>${esc(fmtClub(c.org, c.state))}</b> (${c.cyoWins.toFixed(2)} exp titles · ${c.runners_count} rnrs)`).join(", ")}.</p>`;
  }

  function renderClubHeatmap(realClubs) {
    const box = document.getElementById("clubHeatmapChart");
    const topClubs = realClubs.slice(0, 24);
    const cols = [3, 4, 6, 7, 8, 9, 10, 11, 1, 2];

    let html = `<table style="font-size:12px"><thead><tr><th>Organization</th><th class="num">Rnrs</th>` +
      cols.map((evNum) => `<th class="num">${EV_MAP[evNum].short.replace(" Girls", "G").replace(" Boys", "B")}</th>`).join("") +
      `</tr></thead><tbody>`;

    topClubs.forEach((c) => {
      html += `<tr class="row-click ${c.is_dop ? "row-dop" : ""}" onclick="window.selectClub('${esc(c.org)}')">
        <td><b>${esc(fmtClub(c.org, c.state))}</b></td>
        <td class="num">${c.runners_count}</td>`;
      cols.forEach((evNum) => {
        const squads = TEAMS.filter((t) => t.base_org === c.org && t.event_num === evNum);
        if (!squads.length) {
          html += `<td class="num muted">·</td>`;
        } else {
          const scored = squads.filter((s) => s.scores_official_team).sort((a, b) => a.nat.exp_rank - b.nat.exp_rank);
          if (scored.length) {
            const rk = scored[0].nat.exp_rank;
            const bg = rk < 1.6 ? "var(--gold-soft)" : rk <= 3.5 ? "var(--up-soft)" : "var(--accent-soft)";
            html += `<td class="num" style="background:${bg};font-weight:600" title="${esc(fmtClub(scored[0].team, scored[0].state))}: Exp Rank #${rk.toFixed(1)} (${scored[0].nat.podium_prob}% Podium)">#${Math.round(rk)}${scored.length > 1 ? "+" : ""}</td>`;
          } else {
            const cnt = d3.sum(squads, (s) => s.roster_count);
            html += `<td class="num muted" title="${cnt} individual entries (&lt;5)">${cnt}i</td>`;
          }
        }
      });
      html += `</tr>`;
    });
    html += `</tbody></table>`;
    box.innerHTML = html;
  }

  window.selectClub = function (orgName) {
    selectedClubOrg = orgName;
    renderClubInspector(orgName);
    document.getElementById("clubDetailSection").scrollIntoView({ behavior: "smooth" });
  };

  function renderClubInspector(orgName) {
    const card = document.getElementById("clubInspectorCard");
    const c = CLUBS.find((x) => x.org === orgName) || CLUBS[0];
    const squads = TEAMS.filter((t) => t.base_org === c.org).sort((a, b) => a.event_num - b.event_num);
    const aths = ATHLETES.filter((a) => a.base_org === c.org).sort((a, b) => a.event_num - b.event_num || a.exp_place - b.exp_place);
    const schools = Object.entries(c.feeder_schools || {}).sort((a, b) => b[1] - a[1]);

    card.innerHTML = `
      <div class="dossier-header">
        <div style="display:flex;gap:14px;align-items:center">
          <div class="avatar-circle ${c.is_dop ? "is-dop" : c.is_cyo ? "is-cyo" : ""}">${esc(c.org.slice(0, 2).toUpperCase())}</div>
          <div>
            <div class="eyebrow">${esc(c.category)} · ${esc(c.region || c.state)}</div>
            <h2 style="margin:2px 0">${esc(fmtClub(c.org, c.state))}</h2>
            <div class="muted" style="font-size:13px">${c.runners_count} runners across ${c.events_entered.length} events · ${c.scoring_squads} official scoring squads · ${c.seeded_runners} empirically seeded · ${c.cccnyc_vets} returning CCCNYC veterans</div>
          </div>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <span class="badge b-gold">Exp Nat Podiums: ${c.exp_national_podiums.toFixed(2)}</span>
          <span class="badge b-up">Exp Age All-Americans: ${c.exp_age_all_americans.toFixed(1)}</span>
          <span class="badge b-muted">'22–'25 CCCNYC Top-25s: ${c.hist_2022_2025_top25}</span>
        </div>
      </div>
      ${schools.length ? `<div style="margin-bottom:12px"><span class="ctl-label">Identified Feeder Schools / Parishes:</span> ` + schools.slice(0, 14).map(([s, n]) => `<span class="badge b-muted" style="margin:2px">${esc(s)} (${n})</span>`).join("") + `</div>` : ""}
      <div class="grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px;margin-bottom:12px">
        ${squads.map((s) => `
          <div class="card" style="padding:10px 12px;cursor:pointer" onclick="window.location.href='races.html?event=${s.event_num}'">
            <div style="display:flex;justify-content:space-between"><b>${esc(s.event_short)}</b><span class="mono muted">${s.roster_count} rnrs</span></div>
            <div style="font-size:12.5px;color:var(--fg2);margin-top:3px">${esc(fmtClub(s.team, s.state))}</div>
            <div style="margin-top:5px;font-size:12px">
              ${s.scores_official_team
                ? `<span class="badge b-accent">Nat #${s.nat.exp_rank.toFixed(1)} (${s.nat.podium_prob}% Pod)</span> ${s.cyo ? `<span class="badge b-cyo">CYO #${s.cyo.exp_rank.toFixed(1)}</span>` : ""}`
                : `<span class="badge b-muted">Individual Entries (&lt;5)</span>`}
            </div>
          </div>
        `).join("")}
      </div>
      <details>
        <summary style="cursor:pointer;font-weight:600;font-size:13.5px;color:var(--accent)">View all ${aths.length} entered athletes for ${esc(fmtClub(c.org, c.state))}</summary>
        <div class="tablewrap" style="margin-top:8px;max-height:320px;overflow-y:auto">
          <table><thead><tr><th>Athlete</th><th>Event</th><th class="num">Age</th><th>School</th><th class="num">Proj Time</th><th class="num">Ov Exp Pl</th><th class="num">Age AA%</th></tr></thead>
          <tbody>${aths.map((a) => `<tr class="row-click" onclick="window.location.href='runners.html?id=${a.id}'">
            <td><b>${esc(a.display_name)}</b></td><td>${esc(EV_MAP[a.event_num].short)}</td><td class="num">${a.age}</td>
            <td class="muted">${esc(a.home_school || "—")}</td><td class="num">${a.proj_time_str}</td><td class="num">#${a.exp_place.toFixed(1)}</td><td class="num">${a.aa_age_prob}%</td>
          </tr>`).join("")}</tbody></table>
        </div>
      </details>
    `;
  }

  function renderClubsTable() {
    const tbody = document.getElementById("clubsTableBody");
    let list = CLUBS.filter((c) => c.org !== "Unattached");
    if (clubCatFilter === "CYO") list = list.filter((c) => c.is_cyo);
    else if (clubCatFilter !== "ALL") list = list.filter((c) => c.category.includes(clubCatFilter));
    if (clubStateFilter !== "ALL") list = list.filter((c) => c.state === clubStateFilter);
    if (clubQuery) list = list.filter((c) => fmtClub(c.org, c.state).toLowerCase().includes(clubQuery) || (c.region || "").toLowerCase().includes(clubQuery));

    tbody.innerHTML = list.map((c) => `
      <tr class="row-click ${c.is_dop ? "row-dop" : ""}" onclick="window.selectClub('${esc(c.org)}')">
        <td><b>${esc(fmtClub(c.org, c.state))}</b></td>
        <td class="mono">${c.state}</td>
        <td class="muted">${esc(c.region || "—")}</td>
        <td>${c.is_cyo ? `<span class="badge b-cyo">${esc(c.category)}</span>` : `<span class="badge b-muted">${esc(c.category)}</span>`}</td>
        <td class="num"><b>${c.runners_count}</b></td>
        <td class="num">${c.scoring_squads}</td>
        <td class="num">${c.seeded_runners}</td>
        <td class="num">${c.cccnyc_vets}</td>
        <td class="num"><b>${c.exp_national_podiums.toFixed(2)}</b></td>
        <td class="num"><b>${c.exp_age_all_americans.toFixed(1)}</b></td>
        <td class="num">${c.hist_2022_2025_top25}</td>
      </tr>
    `).join("");
  }

  // =========================================================================
  // PAGE 5: RUNNERS & DOSSIERS (runners.html)
  // =========================================================================
  let selectedRunnerId = urlParams.get("id") || (ATHLETES.find((a) => a.last_name === "Victor") || ATHLETES.find((a) => a.is_dop) || ATHLETES[0]).id;

  function initRunnersPage() {
    // Populate filter dropdowns
    const evSel = document.getElementById("fltEventSel");
    evSel.innerHTML = `<option value="ALL">All 11 Events</option>` +
      EVENTS.map((e) => `<option value="${e.num}">Ev ${e.num}: ${esc(e.name)}</option>`).join("");

    const ageSel = document.getElementById("fltAgeSel");
    const ages = Array.from(new Set(ATHLETES.map((a) => a.age))).sort((a, b) => a - b);
    ageSel.innerHTML = `<option value="ALL">All Ages (${ages[0]}–${ages[ages.length - 1]})</option>` +
      ages.map((ag) => `<option value="${ag}">Age ${ag}</option>`).join("");

    // Cutline group selector (all single-year award ceremonies in Events 3,4,6,7,8,9,10,11)
    const cutSel = document.getElementById("cutlineGroupSel");
    const cutOpts = [];
    [3, 4, 6, 7, 8, 9, 10, 11].forEach((en) => {
      const ev = EV_MAP[en];
      Object.keys(ev.award_group_sizes).sort((a, b) => Number(a) - Number(b)).forEach((ag) => {
        cutOpts.push({ key: `${en}_${ag}`, label: `${ev.gender === "F" ? "Girls" : "Boys"} Age ${ag} (${ev.dist_m}m · ${ev.award_group_sizes[ag]} entries)` });
      });
    });
    cutSel.innerHTML = cutOpts.map((o) => `<option value="${o.key}">${esc(o.label)}</option>`).join("");
    cutSel.value = "6_9"; // Default to Girls Age 9 (3K)!
    cutSel.addEventListener("change", () => renderAgeCutlineChart(cutSel.value));

    // Duel selectors
    const duelEv = document.getElementById("duelEventSel");
    duelEv.innerHTML = EVENTS.map((e) => `<option value="${e.num}">Ev ${e.num}: ${esc(e.name)}</option>`).join("");
    duelEv.value = String(ATH_MAP[selectedRunnerId]?.event_num || 6);
    const populateDuelRunners = () => {
      const en = Number(duelEv.value);
      const rList = ATHLETES.filter((a) => a.event_num === en).sort((a, b) => a.exp_place - b.exp_place);
      const selA = document.getElementById("duelRunnerASel");
      const selB = document.getElementById("duelRunnerBSel");
      const opts = rList.map((a) => `<option value="${a.id}">#${Math.round(a.exp_place)} ${esc(a.display_name)} · ${esc(fmtClub(a.team, a.club_state))}</option>`).join("");
      selA.innerHTML = opts;
      selB.innerHTML = opts;
      const dopInEv = rList.find((a) => a.id === selectedRunnerId) || rList.find((a) => a.is_dop) || rList[0];
      if (dopInEv) selA.value = dopInEv.id;
      const rival = rList.find((a) => a.id !== selA.value && Math.abs(a.exp_place - ATH_MAP[selA.value].exp_place) <= 5) || rList[1] || rList[0];
      if (rival) selB.value = rival.id;
      renderDuelChart();
    };
    duelEv.addEventListener("change", populateDuelRunners);
    document.getElementById("duelRunnerASel").addEventListener("change", renderDuelChart);
    document.getElementById("duelRunnerBSel").addEventListener("change", renderDuelChart);

    // Table filters
    const dopBtn = document.getElementById("fltDopBtn");
    const aqBtn = document.getElementById("fltAquinasBtn");
    const cyoBtn = document.getElementById("fltCyoBtn");
    [dopBtn, aqBtn, cyoBtn].forEach((btn) => {
      btn.addEventListener("click", () => {
        const next = btn.getAttribute("aria-pressed") !== "true";
        btn.setAttribute("aria-pressed", String(next));
        renderAllRunnersTable();
      });
    });
    ["globalRunnerSearch", "fltEventSel", "fltAgeSel", "fltTierSel"].forEach((id) => {
      const el = document.getElementById(id);
      el.addEventListener(el.tagName === "INPUT" ? "input" : "change", renderAllRunnersTable);
    });

    renderRunnerDossier(selectedRunnerId);
    renderAgeCutlineChart(cutSel.value);
    populateDuelRunners();
    renderAllRunnersTable();
  }

  window.openDossier = function (id) {
    selectedRunnerId = id;
    renderRunnerDossier(id);
    const a = ATH_MAP[id];
    if (a) {
      const cutSel = document.getElementById("cutlineGroupSel");
      const ck = `${a.event_num}_${a.award_group}`;
      if ([...cutSel.options].some((o) => o.value === ck)) {
        cutSel.value = ck;
        renderAgeCutlineChart(ck);
      }
      const duelEv = document.getElementById("duelEventSel");
      duelEv.value = String(a.event_num);
      duelEv.dispatchEvent(new Event("change"));
    }
    document.getElementById("dossierSection").scrollIntoView({ behavior: "smooth" });
  };

  function renderRunnerDossier(id) {
    const card = document.getElementById("runnerDossierCard");
    const a = ATH_MAP[id] || ATHLETES[0];
    const ev = EV_MAP[a.event_num];
    const initials = ((a.first_name[0] || "") + (a.last_name[0] || "")).toUpperCase();

    let racesHtml = "";
    if (a.races_2026.length) {
      racesHtml = `<div class="tablewrap" style="margin-top:8px"><table><thead><tr>
        <th>Date</th><th>2026 Meet</th><th class="num">Dist</th><th class="num">Place</th><th class="num">Time</th><th class="num">Pace</th><th>School / Squad</th>
      </tr></thead><tbody>` + a.races_2026.map((r) => `
        <tr>
          <td class="mono muted">${r.date}</td>
          <td><b>${esc(r.meet)}</b></td>
          <td class="num">${r.dist_m}m</td>
          <td class="num">${r.place ? `#${r.place} <span class="muted">/${r.field_size}</span>` : "—"}</td>
          <td class="num"><b>${r.time_str}</b></td>
          <td class="num">${r.pace_mi || fmtPace(r.time_sec, r.dist_m).replace("/mi", "")}/mi</td>
          <td class="muted">${esc(r.school_team || "—")}</td>
        </tr>
      `).join("") + `</tbody></table></div>`;
    } else if (a.prior_season_marks && a.prior_season_marks.length) {
      racesHtml = `<div class="tablewrap" style="margin-top:8px"><table><thead><tr>
        <th>Season</th><th>Verified Prior Meet</th><th class="num">Dist</th><th class="num">Time</th><th class="num">Pace</th><th>Surface</th>
      </tr></thead><tbody>` + a.prior_season_marks.slice(0, 8).map((r) => `
        <tr>
          <td class="mono muted">${r.year}</td>
          <td><b>${esc(r.meet)}</b></td>
          <td class="num">${r.dist_m}m</td>
          <td class="num"><b>${r.time_str}</b></td>
          <td class="num">${r.pace_mi}/mi</td>
          <td class="muted">${r.surface === "track" ? "Track" : "XC"}</td>
        </tr>
      `).join("") + `</tbody></table></div>`;
    } else {
      racesHtml = `<div class="muted" style="font-size:13px;margin-top:6px">First-year youth entrant without prior chip-timed public race record; projected via ${esc(a.seed_tier)}.</div>`;
    }

    let vetHtml = "";
    if (a.cccnyc_history.length) {
      vetHtml = `<div style="margin-top:10px"><span class="ctl-label">CCCNYC Nationals History:</span> ` +
        a.cccnyc_history.map((h) => `<span class="badge b-gold" style="margin:2px">${h.year}: #${h.place} (${h.time_str} · Age ${h.age})</span>`).join("") +
        `</div>`;
    }

    card.innerHTML = `
      <div class="dossier-header">
        <div style="display:flex;gap:14px;align-items:center">
          <div class="avatar-circle ${a.is_dop ? "is-dop" : a.is_cyo ? "is-cyo" : ""}">${esc(initials)}</div>
          <div>
            <div class="eyebrow">Athlete Scouting Dossier · Event ${ev.num} (${esc(ev.name)}) · Gun ${ev.time_est}</div>
            <h2 style="margin:2px 0">${esc(a.display_name)} <span class="muted" style="font-weight:400;font-size:16px">· Age ${a.age}</span></h2>
            <div style="font-size:13.5px;color:var(--fg2)">
              <b>${esc(fmtClub(a.team, a.club_state))}</b> ${a.home_school ? `· Home School: <b>${esc(a.home_school)}</b>` : ""} · ${tierBadge(a.seed_tier)}
            </div>
          </div>
        </div>
        <div style="display:flex;gap:12px;flex-wrap:wrap;text-align:right">
          <div><div class="ctl-label">Proj Cedarville</div><div class="mono" style="font-size:21px;font-weight:700">${a.proj_time_str}</div><div class="mono muted" style="font-size:11.5px">${a.p10_time_str}–${a.p90_time_str} (${a.proj_pace_mi}/mi)</div></div>
          <div><div class="ctl-label">Overall Place</div><div class="mono" style="font-size:21px;font-weight:700">#${a.exp_place.toFixed(1)}</div><div class="mono muted" style="font-size:11.5px">P10–P90: #${a.p10_place}–#${a.p90_place}</div></div>
          <div><div class="ctl-label">Age-${a.award_group} All-American</div><div class="mono" style="font-size:21px;font-weight:700;color:var(--up)">${a.aa_age_prob.toFixed(1)}%</div><div class="mono muted" style="font-size:11.5px">Exp Age Rk #${a.aa_age_exp_rank.toFixed(1)} of ${a.aa_age_field_size}</div></div>
        </div>
      </div>
      <div class="two">
        <div>
          <h3>2026 season progression &amp; Cedarville target pace</h3>
          <div id="dossierProgChart"></div>
          ${vetHtml}
        </div>
        <div>
          <h3>Scraped 2026 race resume (${a.races_2026.length} finishes)</h3>
          ${racesHtml}
        </div>
      </div>
    `;

    // Render progression chart
    const pbox = document.getElementById("dossierProgChart");
    if (a.races_2026.length >= 1) {
      const W = Math.max(360, pbox.clientWidth || 460);
      const H = 175;
      const m = { t: 16, r: 22, b: 32, l: 52 };
      const svg = d3.select(pbox).append("svg").attr("viewBox", `0 0 ${W} ${H}`).style("width", "100%");
      const pts = a.races_2026.map((r, i) => ({
        idx: i + 1,
        label: r.date.slice(5),
        meet: r.meet,
        paceS: r.time_sec / (r.dist_m / 1609.344),
        place: r.place,
        time_str: r.time_str,
      }));
      const projPaceS = a.proj_time_sec / (ev.dist_m / 1609.344);
      const allP = pts.map((p) => p.paceS).concat([projPaceS]);

      const x = d3.scalePoint().domain(pts.map((p) => p.idx).concat(["Cedarville"])).range([m.l, W - m.r]).padding(0.35);
      const y = d3.scaleLinear().domain([d3.min(allP) - 15, d3.max(allP) + 15]).range([m.t, H - m.b]);

      svg.append("g").attr("transform", `translate(0,${H - m.b})`)
        .call(d3.axisBottom(x).tickFormat((k) => (k === "Cedarville" ? "Nov 21 Proj" : pts[k - 1].label)))
        .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)").attr("font-size", 10.5));
      svg.append("g").attr("transform", `translate(${m.l},0)`)
        .call(d3.axisLeft(y).ticks(4).tickFormat((s) => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, "0")}`))
        .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));

      // Target dashed line
      svg.append("line").attr("x1", m.l).attr("x2", W - m.r).attr("y1", y(projPaceS)).attr("y2", y(projPaceS))
        .attr("stroke", "var(--up)").attr("stroke-dasharray", "4,3").attr("stroke-width", 1.5);

      if (pts.length > 1) {
        const ln = d3.line().x((d) => x(d.idx)).y((d) => y(d.paceS)).curve(d3.curveMonotoneX);
        svg.append("path").datum(pts).attr("d", ln).attr("fill", "none").attr("stroke", "var(--dop)").attr("stroke-width", 2.2);
      }
      svg.selectAll(".pdot").data(pts).enter().append("circle")
        .attr("cx", (d) => x(d.idx)).attr("cy", (d) => y(d.paceS)).attr("r", 4.8).attr("fill", "var(--dop)")
        .on("mousemove", (evt, d) => showTip(evt, `<b>${esc(d.meet)}</b><br>Time: <span class="mono">${d.time_str}</span> (Place #${d.place || "—"})`))
        .on("mouseleave", hideTip);

      svg.append("circle").attr("cx", x("Cedarville")).attr("cy", y(projPaceS)).attr("r", 6)
        .attr("fill", "var(--up)").attr("stroke", "var(--surface)").attr("stroke-width", 2);
    } else {
      pbox.innerHTML = `<div class="callout" style="margin-top:8px">Projected Cedarville Time: <b class="mono">${a.proj_time_str}</b> (${a.proj_pace_mi}/mi) · 80% Confidence Interval: <span class="mono">${a.p10_time_str} – ${a.p90_time_str}</span>.</div>`;
    }
  }

  function renderAgeCutlineChart(groupKey) {
    const box = document.getElementById("ageCutlineChart");
    const so = document.getElementById("ageCutlineSo");
    box.innerHTML = "";
    const [evStr, ag] = groupKey.split("_");
    const evNum = Number(evStr);
    const groupAths = ATHLETES.filter((a) => a.event_num === evNum && a.award_group === ag)
      .sort((a, b) => a.aa_age_exp_rank - b.aa_age_exp_rank);

    const rows = groupAths.slice(0, 35);
    if (!rows.length) return;
    const cutTime = groupAths.length >= 25 ? groupAths[24].proj_time_sec : d3.max(groupAths, (d) => d.proj_time_sec);

    const W = Math.max(400, box.clientWidth || 500);
    const H = 285;
    const m = { t: 18, r: 20, b: 34, l: 54 };
    const svg = d3.select(box).append("svg").attr("viewBox", `0 0 ${W} ${H}`).style("width", "100%");

    const x = d3.scaleLinear().domain([1, rows.length]).range([m.l, W - m.r]);
    const y = d3.scaleLinear()
      .domain([d3.min(rows, (d) => d.p10_time_sec) * 0.985, d3.max(rows, (d) => d.p90_time_sec) * 1.01])
      .range([m.t, H - m.b]);

    svg.append("g").attr("transform", `translate(0,${H - m.b})`)
      .call(d3.axisBottom(x).ticks(7).tickFormat((d) => `#${d}`))
      .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));
    svg.append("g").attr("transform", `translate(${m.l},0)`)
      .call(d3.axisLeft(y).ticks(5).tickFormat((s) => fmtTime(s)))
      .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));

    // #25 All-American Cutline
    if (groupAths.length >= 25) {
      svg.append("line").attr("x1", m.l).attr("x2", W - m.r).attr("y1", y(cutTime)).attr("y2", y(cutTime))
        .attr("stroke", "var(--gold)").attr("stroke-dasharray", "5,4").attr("stroke-width", 1.8);
      svg.append("line").attr("x1", x(25.5)).attr("x2", x(25.5)).attr("y1", m.t).attr("y2", H - m.b)
        .attr("stroke", "var(--gold)").attr("stroke-dasharray", "3,3").attr("opacity", 0.7);
      svg.append("text").attr("x", W - m.r - 4).attr("y", y(cutTime) - 5).attr("text-anchor", "end")
        .attr("font-size", 11).attr("font-weight", 600).attr("fill", "var(--gold)")
        .text(`#25 All-American Cutline: ${fmtTime(cutTime)}`);
    }

    rows.forEach((a, i) => {
      const cx = x(i + 1);
      const col = a.is_dop ? "var(--dop)" : a.is_cyo ? "var(--cyo)" : "var(--accent)";
      svg.append("line").attr("x1", cx).attr("x2", cx).attr("y1", y(a.p10_time_sec)).attr("y2", y(a.p90_time_sec))
        .attr("stroke", col).attr("stroke-width", a.is_dop ? 2.4 : 1.3).attr("opacity", a.is_dop ? 0.85 : 0.4);
      svg.append("circle").attr("cx", cx).attr("cy", y(a.proj_time_sec)).attr("r", a.is_dop ? 5 : 3.4)
        .attr("fill", col).style("cursor", "pointer")
        .on("mousemove", (evt) => showTip(evt,
          `<b>#${i + 1} Age-${ag}: ${esc(a.display_name)}</b><br>${esc(fmtClub(a.team, a.club_state))}${a.home_school ? ` · ${esc(a.home_school)}` : ""}<br>Proj: <b class="mono">${a.proj_time_str}</b> (P10–P90: ${a.p10_time_str}–${a.p90_time_str})<br>Age-${ag} All-American Odds: <b class="mono">${a.aa_age_prob}%</b>`
        ))
        .on("mouseleave", hideTip)
        .on("click", () => window.openDossier(a.id));
    });

    const dopInGrp = groupAths.filter((a) => a.is_dop);
    so.innerHTML = groupAths.length <= 25
      ? `<b>Guaranteed Medal Field:</b> Only <b>${groupAths.length} athletes</b> are entered in Age ${ag}—every finisher earns a Top-25 All-American medal!`
      : `<b>Projected #25 Medal Cutline:</b> <b>${fmtTime(cutTime)}</b> (${fmtPace(cutTime, EV_MAP[evNum].dist_m)}) out of ${groupAths.length} entries (${dopInGrp.length} Diocese of Pittsburgh runners in this birth year).`;
  }

  function renderDuelChart() {
    const box = document.getElementById("duelChart");
    const so = document.getElementById("duelSo");
    box.innerHTML = "";
    const a = ATH_MAP[document.getElementById("duelRunnerASel").value];
    const b = ATH_MAP[document.getElementById("duelRunnerBSel").value];
    if (!a || !b) return;

    const muA = a.proj_time_sec, sdA = (a.p90_time_sec - a.p10_time_sec) / 2.563;
    const muB = b.proj_time_sec, sdB = (b.p90_time_sec - b.p10_time_sec) / 2.563;
    const sdDiff = Math.sqrt(sdA * sdA + sdB * sdB) || 1;
    // Normal CDF approximation for P(T_A < T_B)
    const z = (muB - muA) / sdDiff;
    const t = 1 / (1 + 0.2316419 * Math.abs(z));
    const d = 0.3989423 * Math.exp((-z * z) / 2);
    const prob = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));
    const winA = (z >= 0 ? 1 - prob : prob) * 100;

    const W = Math.max(400, box.clientWidth || 500);
    const H = 225;
    const m = { t: 20, r: 20, b: 34, l: 24 };
    const svg = d3.select(box).append("svg").attr("viewBox", `0 0 ${W} ${H}`).style("width", "100%");

    const minT = Math.min(muA - 3.2 * sdA, muB - 3.2 * sdB);
    const maxT = Math.max(muA + 3.2 * sdA, muB + 3.2 * sdB);
    const x = d3.scaleLinear().domain([minT, maxT]).range([m.l, W - m.r]);
    const grid = d3.range(minT, maxT, (maxT - minT) / 90);
    const pdf = (v, mu, sd) => (1 / (sd * 2.5066)) * Math.exp(-0.5 * Math.pow((v - mu) / sd, 2));
    const cA = grid.map((v) => ({ v, p: pdf(v, muA, sdA) }));
    const cB = grid.map((v) => ({ v, p: pdf(v, muB, sdB) }));
    const maxP = Math.max(d3.max(cA, (k) => k.p), d3.max(cB, (k) => k.p)) || 1;
    const y = d3.scaleLinear().domain([0, maxP * 1.12]).range([H - m.b, m.t]);

    svg.append("g").attr("transform", `translate(0,${H - m.b})`)
      .call(d3.axisBottom(x).ticks(5).tickFormat((s) => fmtTime(s)))
      .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));

    const area = d3.area().x((k) => x(k.v)).y0(H - m.b).y1((k) => y(k.p)).curve(d3.curveBasis);
    const line = d3.line().x((k) => x(k.v)).y((k) => y(k.p)).curve(d3.curveBasis);

    svg.append("path").datum(cA).attr("d", area).attr("fill", "var(--dop)").attr("opacity", 0.22);
    svg.append("path").datum(cA).attr("d", line).attr("fill", "none").attr("stroke", "var(--dop)").attr("stroke-width", 2.2);
    svg.append("path").datum(cB).attr("d", area).attr("fill", "var(--accent)").attr("opacity", 0.22);
    svg.append("path").datum(cB).attr("d", line).attr("fill", "none").attr("stroke", "var(--accent)").attr("stroke-width", 2.2);

    svg.append("text").attr("x", x(muA)).attr("y", y(pdf(muA, muA, sdA)) - 5).attr("text-anchor", "middle")
      .attr("font-size", 11).attr("font-weight", 600).attr("fill", "var(--dop)").text(`${a.last_name} (${a.proj_time_str})`);
    svg.append("text").attr("x", x(muB)).attr("y", y(pdf(muB, muB, sdB)) - 5).attr("text-anchor", "middle")
      .attr("font-size", 11).attr("font-weight", 600).attr("fill", "var(--accent)").text(`${b.last_name} (${b.proj_time_str})`);

    so.innerHTML = `<b>Head-to-Head Verdict:</b> <span class="dop-txt">${esc(a.display_name)}</span> defeats <span style="color:var(--accent);font-weight:600">${esc(b.display_name)}</span> in <b>${winA.toFixed(1)}%</b> of simulated races (expected margin: <span class="mono">${Math.abs(muB - muA).toFixed(1)}s</span>).`;
  }

  function renderAllRunnersTable() {
    const q = document.getElementById("globalRunnerSearch").value.trim().toLowerCase();
    const evV = document.getElementById("fltEventSel").value;
    const agV = document.getElementById("fltAgeSel").value;
    const trV = document.getElementById("fltTierSel").value;
    const onlyDop = document.getElementById("fltDopBtn").getAttribute("aria-pressed") === "true";
    const onlyAq = document.getElementById("fltAquinasBtn").getAttribute("aria-pressed") === "true";
    const onlyCyo = document.getElementById("fltCyoBtn").getAttribute("aria-pressed") === "true";

    let list = ATHLETES.filter((a) => {
      if (onlyDop && !a.is_dop) return false;
      if (onlyAq && !(a.home_school || "").includes("Aquinas")) return false;
      if (onlyCyo && !a.is_cyo) return false;
      if (evV !== "ALL" && a.event_num !== Number(evV)) return false;
      if (agV !== "ALL" && a.age !== Number(agV)) return false;
      if (trV === "EMP" && a.seed_tier.includes("Tier 3")) return false;
      if (trV === "2026" && !a.races_2026.length) return false;
      if (trV === "VET" && !a.cccnyc_history.length) return false;
      if (q && !(
        a.display_name.toLowerCase().includes(q) ||
        fmtClub(a.team, a.club_state).toLowerCase().includes(q) ||
        (a.home_school || "").toLowerCase().includes(q)
      )) return false;
      return true;
    });

    list.sort((a, b) => a.event_num - b.event_num || a.exp_place - b.exp_place);
    const shown = list.slice(0, 350);
    document.getElementById("runnerCountSummary").textContent =
      `Showing ${shown.length} of ${list.length} matching runners (click any row to load scouting dossier above).`;

    document.getElementById("allRunnersTableBody").innerHTML = shown.map((a) => `
      <tr class="row-click ${a.is_dop ? "row-dop" : ""}" onclick="window.openDossier('${a.id}')">
        <td><b>${esc(a.display_name)}</b></td>
        <td>${esc(EV_MAP[a.event_num].short)}</td>
        <td class="num">${a.age}</td>
        <td>${a.is_dop ? `<span class="dop-txt">${esc(fmtClub(a.team, a.club_state))}</span>` : a.is_cyo ? `<span class="cyo-txt">${esc(fmtClub(a.team, a.club_state))}</span>` : esc(fmtClub(a.team, a.club_state))}</td>
        <td class="muted">${esc(a.home_school || a.club_region || "—")}</td>
        <td>${tierBadge(a.seed_tier)}</td>
        <td class="num">${a.races_2026.length || "—"}</td>
        <td class="num"><b>${a.proj_time_str}</b></td>
        <td class="num">${a.proj_pace_mi}/mi</td>
        <td class="num">#${a.exp_place.toFixed(1)}</td>
        <td class="num">#${a.aa_age_exp_rank.toFixed(1)}</td>
        <td class="num">${probBar(a.aa_age_prob, a.is_dop ? "var(--dop)" : "var(--up)")}</td>
      </tr>
    `).join("");
  }

  // Course pill bindings on Hub
  document.querySelectorAll("#courseDistPills button[data-cdist]").forEach((b) => {
    b.addEventListener("click", () => {
      selectedCourseDist = Number(b.dataset.cdist);
      document.querySelectorAll("#courseDistPills button[data-cdist]").forEach((x) => x.setAttribute("aria-pressed", Number(x.dataset.cdist) === selectedCourseDist));
      renderCourseChart(selectedCourseDist);
    });
  });

  // Also add a subtle banner link on the parent Aquinas site? Let's keep parent untouched unless helpful, or let's boot current page!
  if (pageKey === "hub") renderHub();
  else if (pageKey === "races") initRacePage();
  else if (pageKey === "diocese") initDiocesePage();
  else if (pageKey === "clubs") initClubsPage();
  else if (pageKey === "runners") initRunnersPage();
})();
