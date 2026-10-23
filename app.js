/* Shared chart helpers (d3 v7 is loaded by the page). Colors come from CSS variables so dark mode works. */
const VZ = (() => {
  const cs = () => getComputedStyle(document.documentElement);
  const css = (v, fb) => (cs().getPropertyValue(v) || fb || '#888').trim();
  const pal = () => ({
    fg: css('--fg'), fg2: css('--fg2'), muted: css('--muted'), line: css('--line'), soft: css('--soft'), bg: css('--bg'), surface: css('--surface'),
    up: css('--up'), down: css('--down'), warn: css('--warn'), accent: css('--accent'),
    gen: css('--r-gen'), fuel: css('--r-fuel'), wire: css('--r-wire'), equip: css('--r-equip'), load: css('--r-load')
  });
  let tipEl;
  function tip() {
    if (!tipEl) {
      tipEl = document.createElement('div');
      tipEl.style.cssText = 'position:fixed;pointer-events:none;z-index:50;background:var(--surface);color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:6px 9px;font-size:12px;line-height:1.35;max-width:290px;box-shadow:0 2px 10px rgba(0,0,0,.15);display:none';
      document.body.appendChild(tipEl);
    }
    return {
      show(html, ev) {
        tipEl.innerHTML = html; tipEl.style.display = 'block';
        const x = Math.min(ev.clientX + 14, innerWidth - 300), y = Math.min(ev.clientY + 14, innerHeight - 110);
        tipEl.style.left = x + 'px'; tipEl.style.top = y + 'px';
      },
      hide() { tipEl.style.display = 'none'; }
    };
  }
  function svg(el, w, h, m = { t: 12, r: 12, b: 28, l: 40 }) {
    if (!el) return null;
    const root = d3.select(el); root.selectAll('*').remove();
    const s = root.append('svg').attr('viewBox', `0 0 ${w} ${h}`).attr('class', 'chart').style('width', '100%').style('height', 'auto').attr('role', 'img');
    const g = s.append('g').attr('transform', `translate(${m.l},${m.t})`);
    return { svg: s, g, w, h, iw: w - m.l - m.r, ih: h - m.t - m.b, m };
  }
  function axisStyle(sel) {
    const p = pal();
    sel.selectAll('text').attr('fill', p.fg2).style('font-size', '11px');
    sel.selectAll('path,line').attr('stroke', p.line);
    return sel;
  }
  return { pal, tip, svg, axisStyle, css };
})();

const RAW = window.AQUINAS_XC_DATA;
const el = id => document.getElementById(id);
const tip = VZ.tip();
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

const CATS = ['HS Varsity (9-12)', 'MS Varsity (7-8)', 'Elementary JV (5-6)', 'Developmental (K-4)'];
const cvar = ['--k1', '--k2', '--k3', '--k4'];
const SYM = [d3.symbolCircle, d3.symbolSquare, d3.symbolDiamond, d3.symbolTriangle];
const cc = c => {
  const idx = CATS.indexOf(c);
  return getComputedStyle(document.documentElement).getPropertyValue(cvar[idx >= 0 ? idx : 0]).trim();
};

function fmtSec(sec) {
  if (sec == null || isNaN(sec)) return '—';
  const sign = sec < 0 ? '-' : '';
  const abs = Math.abs(sec);
  const m = Math.floor(abs / 60);
  const s = (abs - m * 60).toFixed(2).padStart(5, '0');
  return `${sign}${m}:${s}`;
}

function fmtPaceSec(sec) {
  if (sec == null || isNaN(sec)) return '—';
  const m = Math.floor(sec / 60);
  const s = Math.round(sec - m * 60);
  return `${m}:${String(s).padStart(2, '0')}/M`;
}

function parsePaceSec(paceStr) {
  if (!paceStr) return null;
  const m = paceStr.match(/(\d+):(\d+)/);
  if (!m) return null;
  return parseInt(m[1], 10) * 60 + parseInt(m[2], 10);
}

function initials(name) {
  const parts = String(name).trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

const ATHLETES = RAW.athletes.map((a, idx) => {
  const pSec = a.pr_pace_seconds || parsePaceSec(a.pr_pace) || 420;
  return {
    ...a,
    id: `ath_${idx}`,
    ab: initials(a.name),
    cat: a.division,
    pace_min: +(pSec / 60).toFixed(2)
  };
});

let state = {
  tab: window.DEFAULT_TAB || 'overall',
  scope: 'ALL',
  gend: 'ALL',
  calMeetId: 'ALL',
  ridgeMode: 'meets',
  teamRidgeMode: 'divisions',
  schoolDiv: 'MS Varsity (7-8)',
  schoolGend: 'Boys',
  selectedSchoolCell: null, // { race_id, team }
  selAth: (ATHLETES.find(a => a.name === 'Isaac Vangura') || ATHLETES[0]).id,
  bucketMode: 'pace',
  bucketPop: 'field',
  offCats: new Set(),
  search: '',
  cardLimit: 28,
  raceId: null,
  onlyAq: true
};

function matchFilter(item) {
  if (state.scope !== 'ALL' && item.division !== state.scope) return false;
  if (state.gend !== 'ALL' && item.gender !== state.gend) return false;
  return true;
}

function getSelectedAthlete() {
  const pool = ATHLETES.filter(matchFilter);
  let found = pool.find(a => a.id === state.selAth);
  if (!found && pool.length) {
    found = pool.slice().sort((a, b) => (b.avg_percentile + b.races_count * 6) - (a.avg_percentile + a.races_count * 6))[0];
    state.selAth = found.id;
  }
  return found || ATHLETES[0];
}

/* Gaussian Kernel Density Estimator for Ridgeline Charts (Uploaded Image 3) */
function computeKDE(values, grid, bandwidth) {
  const n = values.length;
  if (!n) return grid.map(x => [x, 0]);
  return grid.map(x => {
    let sum = 0;
    for (let i = 0; i < n; i++) {
      const u = (x - values[i]) / bandwidth;
      sum += Math.exp(-0.5 * u * u) / (2.5066282746 * bandwidth);
    }
    return [x, sum / n];
  });
}

function drawRidgelineChart(containerEl, seriesList, xDomain, xLabel, soEl, soHtml) {
  if (!containerEl) return;
  const P = VZ.pal();
  if (!seriesList.length) {
    containerEl.innerHTML = '<div class="sub">No data for current filter.</div>';
    return;
  }
  const rowStep = 42;
  const overlap = 48; // peak height above baseline
  const h = seriesList.length * rowStep + 76;
  const o = VZ.svg(containerEl, 900, h, { t: 36, r: 165, b: 42, l: 36 }), g = o.g;

  const x = d3.scaleLinear().domain(xDomain).range([0, o.iw]);
  const grid = d3.range(xDomain[0], xDomain[1] + 0.05, 0.08);
  const bw = 0.28;

  // Subtle vertical background gridlines like Uploaded Image 3
  x.ticks(7).forEach(tk => {
    g.append('line')
      .attr('x1', x(tk)).attr('x2', x(tk)).attr('y1', 0).attr('y2', o.ih)
      .attr('stroke', P.line).attr('stroke-opacity', 0.45);
  });

  // Compute KDE for each series
  const computed = seriesList.map(s => {
    const density = computeKDE(s.values, grid, bw);
    const maxD = d3.max(density, d => d[1]) || 1;
    // Find peak around median
    const med = d3.median(s.values);
    // Evaluate density at median
    const medD = computeKDE(s.values, [med], bw)[0][1];
    return { ...s, density, maxD, med, medD };
  });

  // Draw from top to bottom so lower ridges overlap cleanly (just like Image 3!)
  computed.forEach((s, idx) => {
    const baseY = (idx + 1) * rowStep;
    const yScale = d3.scaleLinear().domain([0, s.maxD]).range([0, overlap]);

    const areaGen = d3.area()
      .curve(d3.curveBasis)
      .x(d => x(d[0]))
      .y0(baseY)
      .y1(d => baseY - yScale(d[1]));

    const lineGen = d3.line()
      .curve(d3.curveBasis)
      .x(d => x(d[0]))
      .y(d => baseY - yScale(d[1]));

    const rg = g.append('g')
      .style('cursor', 'pointer')
      .on('mousemove', e => tip.show(`<b>${esc(s.label)}</b><br>Median pace: <b>${fmtPaceSec(s.med * 60)}</b><br>Sample size: ${s.values.length} finishes<br>Fastest: ${fmtPaceSec(d3.min(s.values) * 60)} · 90th: ${fmtPaceSec(d3.quantile(s.values.slice().sort(d3.ascending), 0.9) * 60)}`, e))
      .on('mouseleave', tip.hide);

    // Baseline
    rg.append('line')
      .attr('x1', 0).attr('x2', o.iw + 155)
      .attr('y1', baseY).attr('y2', baseY)
      .attr('stroke', s.color).attr('stroke-width', 1.2).attr('stroke-opacity', 0.65);

    // Filled KDE wave
    rg.append('path')
      .datum(s.density)
      .attr('d', areaGen)
      .attr('fill', s.color)
      .attr('fill-opacity', 0.76);

    // Crisp top curve stroke
    rg.append('path')
      .datum(s.density)
      .attr('d', lineGen)
      .attr('fill', 'none')
      .attr('stroke', s.color)
      .attr('stroke-width', 2.2);

    // Vertical dashed line at median/peak (matching Image 3!)
    const peakY = baseY - yScale(s.medD);
    rg.append('line')
      .attr('x1', x(s.med)).attr('x2', x(s.med))
      .attr('y1', baseY).attr('y2', peakY)
      .attr('stroke', '#141413')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 1.3)
      .attr('stroke-dasharray', '3 2');

    // Bold callout value right above the peak with halo (matching Image 3!)
    const valTxt = fmtPaceSec(s.med * 60).replace('/M', '');
    rg.append('text')
      .attr('x', x(s.med)).attr('y', peakY - 4)
      .attr('text-anchor', 'middle')
      .attr('fill', P.fg)
      .attr('stroke', P.surface).attr('stroke-width', 3).attr('paint-order', 'stroke')
      .style('font-family', 'var(--font-mono)').style('font-size', '11px').style('font-weight', '600')
      .text(valTxt);

    // Right-aligned series name in matching color (matching Image 3!)
    rg.append('text')
      .attr('x', o.iw + 148).attr('y', baseY - 6)
      .attr('text-anchor', 'end')
      .attr('fill', s.color)
      .style('font-size', '12.5px').style('font-weight', '600')
      .text(s.label);
  });

  const ax = g.append('g').attr('transform', `translate(0,${o.ih})`).call(d3.axisBottom(x).ticks(7).tickFormat(d => fmtPaceSec(d * 60)).tickSize(3));
  VZ.axisStyle(ax);
  g.append('text')
    .attr('x', o.iw / 2).attr('y', o.ih + 34)
    .attr('text-anchor', 'middle').attr('fill', P.fg).style('font-size', '12.5px').style('font-weight', '600')
    .text(xLabel);

  if (soEl && soHtml) soEl.innerHTML = soHtml;
}

/* ============================================================================
   TAB 1: OVERALL (Calendar + Division Winner & Top-3 Tiles + Ridgeline + S-Curve)
   ============================================================================ */
function renderOverallTab() {
  const perfs = RAW.performances.filter(matchFilter);
  const races = RAW.races.filter(r => state.scope === 'ALL' ? true : (r.division === state.scope || (r.is_1m && state.scope !== 'HS Varsity (9-12)')))
    .filter(r => state.gend === 'ALL' || r.gender === state.gend);
  const teams = RAW.team_standings.filter(matchFilter);
  const meetsCount = new Set(races.map(r => r.meet_id)).size;
  const athletesCount = new Set(perfs.map(p => p.name)).size;
  const teamWins = teams.filter(t => t.aquinas_position === 1).length;
  const teamPodiums = teams.filter(t => typeof t.aquinas_position === 'number' && t.aquinas_position <= 3).length;
  const top10s = perfs.filter(p => p.overall_place <= 10).length;
  const indivWins = perfs.filter(p => p.overall_place === 1).length;

  if (el('kpisOverall')) {
    el('kpisOverall').innerHTML = `
      <div class="kpi"><div class="v">${meetsCount} <span style="font-size:14px;color:var(--muted)">/ ${races.length}</span></div><div class="l">Meets / race sections</div></div>
      <div class="kpi"><div class="v">${perfs.length}</div><div class="l">Aquinas race finishes</div></div>
      <div class="kpi"><div class="v">${athletesCount}</div><div class="l">Aquinas student runners</div></div>
      <div class="kpi"><div class="v up">${teamWins} <span style="font-size:14px;color:var(--muted)">(${teamPodiums} top-3)</span></div><div class="l">Aquinas 1st-place team wins</div></div>
      <div class="kpi"><div class="v">${top10s} <span style="font-size:14px;color:var(--muted)">(${indivWins} wins)</span></div><div class="l">Aquinas top-10 finishes</div></div>
    `;
  }

  // 1. Render August, September, October 2026 Calendar Strip
  renderSeasonCalendar();

  // 2. Render Meet Division Tiles (Team Who Won by Division + Top 3 Runners by Division)
  renderCalendarMeetTiles();

  // 3. Render Ridgeline Pace Density Chart across all 10 Meets (Uploaded Image 3)
  renderOverallRidgeline();

  // 4. Render Rank vs Finish Time S-Curve & Passing Leverage
  renderSCurveAndLeverage();

  // 5. Render What Moved Timeline
  renderMoves();
}

function renderSeasonCalendar() {
  const calEl = el('calendarGrid');
  if (!calEl) return;

  const meetsByDate = {};
  RAW.meets.forEach(m => {
    if (!meetsByDate[m.date]) meetsByDate[m.date] = [];
    meetsByDate[m.date].push(m);
  });

  // 2026 calendar months: Aug 2026 (starts Sat=6), Sep 2026 (starts Tue=2), Oct 2026 (starts Thu=4)
  const months = [
    { name: 'August 2026', ym: '2026-08', days: 31, startDow: 6 },
    { name: 'September 2026', ym: '2026-09', days: 30, startDow: 2 },
    { name: 'October 2026', ym: '2026-10', days: 31, startDow: 4 }
  ];
  const dows = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];

  calEl.innerHTML = months.map(m => {
    let cells = dows.map(d => `<div class="cal-dow">${d}</div>`).join('');
    for (let e = 0; e < m.startDow; e++) cells += `<div class="cal-day empty">.</div>`;
    for (let d = 1; d <= m.days; d++) {
      const iso = `${m.ym}-${String(d).padStart(2, '0')}`;
      const mList = meetsByDate[iso];
      if (mList && mList.length) {
        const isAct = mList.some(mt => state.calMeetId === mt.meet_id) || state.calMeetId === `DATE:${iso}`;
        const titleTxt = mList.map(mt => `${mt.meet_name} (${mt.location})`).join(' + ');
        const targetId = mList.length === 1 ? mList[0].meet_id : `DATE:${iso}`;
        cells += `<div class="cal-day has-meet ${isAct ? 'active-meet' : ''}" data-meet="${targetId}" title="${esc(titleTxt)}">${d}</div>`;
      } else {
        cells += `<div class="cal-day">${d}</div>`;
      }
    }
    return `<div class="cal-month"><div class="cal-month-title">${m.name}</div><div class="cal-grid">${cells}</div></div>`;
  }).join('');

  // Populate meet filter pills
  const pillBar = el('calMeetPills');
  if (pillBar) {
    pillBar.innerHTML = `<button class="pill" data-cmeet="ALL" aria-pressed="${state.calMeetId === 'ALL'}">All ${RAW.meets.length} meets</button>` +
      RAW.meets.map(m => `<button class="pill" data-cmeet="${m.meet_id}" aria-pressed="${state.calMeetId === m.meet_id}">${esc(m.short_name)} (${m.date.slice(5)})</button>`).join('');
  }
}

function renderCalendarMeetTiles() {
  const wrap = el('meetDivisionTiles');
  if (!wrap) return;

  let races = RAW.races.filter(r => state.scope === 'ALL' ? true : r.division === state.scope)
    .filter(r => state.gend === 'ALL' || r.gender === state.gend);
  if (state.calMeetId !== 'ALL') {
    if (state.calMeetId.startsWith('DATE:')) {
      const targetDate = state.calMeetId.slice(5);
      races = races.filter(r => r.date === targetDate);
    } else {
      races = races.filter(r => r.meet_id === state.calMeetId);
    }
  }

  // Group races by meet chronologically
  const byMeet = d3.groups(races, r => r.meet_id);
  if (!byMeet.length) {
    wrap.innerHTML = '<div class="card"><div class="sub">No races match the selected division/meet filter.</div></div>';
    return;
  }

  wrap.innerHTML = byMeet.map(([mId, mRaces]) => {
    const first = mRaces[0];
    const tilesHtml = mRaces.map(r => {
      const winTeam = r.winning_school;
      const aqSum = r.aquinas_team_summary;
      const col = cc(r.division === 'All Youth (1M)' ? 'MS Varsity (7-8)' : r.division);

      let teamBannerHtml = '';
      if (winTeam) {
        const aqWon = winTeam.is_aquinas;
        const aqNote = !aqWon && aqSum
          ? `<span class="mono" style="font-size:11px;color:var(--fg2)">Aquinas: ${typeof aqSum.position === 'number' ? '#' + aqSum.position + ' (' + aqSum.points + 'p)' : 'Inc.'}</span>`
          : `<span class="mono up" style="font-size:11px;font-weight:600">&#9733; Aquinas Won</span>`;
        teamBannerHtml = `
          <div class="winner-banner ${aqWon ? 'aq-won' : ''}">
            <div>
              <span style="color:var(--muted);font-size:11px;text-transform:uppercase;font-family:var(--font-mono)">Team Winner:</span>
              <b style="margin-left:4px">${esc(winTeam.team)}</b>
              <span class="mono" style="font-size:11.5px;color:var(--fg2)">(${winTeam.points} pts · ${esc(winTeam.avg_time || '')} avg)</span>
            </div>
            ${aqNote}
          </div>
        `;
      } else {
        teamBannerHtml = `
          <div class="winner-banner">
            <span style="color:var(--muted);font-size:11.5px">Individual race / no team scoring (${r.total_finishers} finishers)</span>
          </div>
        `;
      }

      const top3Html = (r.top3_runners || []).map((ru, i) => `
        <div class="podium-row">
          <span class="medal medal-${i + 1}">#${ru.place}</span>
          <span style="min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
            <b style="${ru.is_aquinas ? 'color:var(--up)' : ''}">${esc(ru.name)}</b>
            <span style="color:var(--muted);font-size:11.5px">· ${esc(ru.team)}</span>
          </span>
          <span class="mono" style="font-size:12px">${esc(ru.time)}</span>
        </div>
      `).join('');

      // If Aquinas didn't have a runner in the top 3, show top Aquinas finisher right underneath
      const hasAqInTop3 = (r.top3_runners || []).some(ru => ru.is_aquinas);
      const topAq = r.aquinas_runners[0];
      const extraAqHtml = (!hasAqInTop3 && topAq) ? `
        <div class="podium-row" style="border-top:1px dashed var(--line);padding-top:4px;margin-top:2px">
          <span class="medal" style="color:var(--up)">#${topAq.place}</span>
          <span style="min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
            <b style="color:var(--up)">${esc(topAq.name)}</b>
            <span style="color:var(--muted);font-size:11.5px">· Top Aquinas</span>
          </span>
          <span class="mono" style="font-size:12px">${esc(topAq.time)}</span>
        </div>
      ` : '';

      return `
        <div class="div-tile">
          <div class="div-tile-head">
            <span class="div-tile-title"><span class="dot" style="background:${col};margin-right:6px"></span>${esc(r.sub_division || r.division)} · ${esc(r.gender)}</span>
            <a href="${esc(r.source_url)}" target="_blank" rel="noopener" class="mono" style="font-size:11px">${r.total_finishers} finishers &nearr;</a>
          </div>
          ${teamBannerHtml}
          <div class="podium-list">
            ${top3Html}
            ${extraAqHtml}
          </div>
        </div>
      `;
    }).join('');

    return `
      <div class="card" style="margin-bottom:14px">
        <div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px;margin-bottom:10px">
          <div>
            <span class="eyebrow">${esc(first.date)} · ${esc(first.location)}</span>
            <h3 style="font-size:17px;margin-top:2px">${esc(first.meet_name)}</h3>
          </div>
          <span class="chip">${mRaces.length} division races</span>
        </div>
        <div class="meet-tiles-grid">${tilesHtml}</div>
      </div>
    `;
  }).join('');
}

function renderOverallRidgeline() {
  const ridgePalette = [
    '#1588e8', '#f03e6b', '#333b48', '#146cb8', '#2eb85c',
    '#e8cf4d', '#555d69', '#cb333b', '#8d929c', '#7c52cc'
  ];

  if (state.ridgeMode === 'meets') {
    const byMeet = d3.groups(RAW.races.filter(r => state.scope === 'ALL' ? true : r.division === state.scope).filter(r => state.gend === 'ALL' || r.gender === state.gend), r => r.meet_short);
    const series = byMeet.map(([mName, mRaces]) => {
      const vals = [];
      mRaces.forEach(r => {
        r.all_runners.forEach(ru => {
          const p = (ru.pace_seconds || parsePaceSec(ru.pace)) / 60;
          if (p && p >= 4.8 && p <= 12.5) vals.push(p);
        });
      });
      return { label: mName, values: vals, med: d3.median(vals) || 99 };
    }).filter(s => s.values.length >= 5).sort((a, b) => a.med - b.med);

    series.forEach((s, i) => { s.color = ridgePalette[i % ridgePalette.length]; });
    drawRidgelineChart(
      el('overallRidgeChart'),
      series,
      [4.8, 12.0],
      'Mile Pace (minutes per mile, faster on left)',
      el('overallRidgeSo'),
      `Stacked kernel density ridgelines sorted by median mile pace across all finishers. Dashed vertical lines and peak labels mark each meet's median pace (fastest field median: <b>${series[0] ? esc(series[0].label) + ' at ' + fmtPaceSec(series[0].med * 60) : '—'}</b>).`
    );
  } else {
    // By Division & Gender
    const combos = [];
    CATS.forEach(div => {
      ['Boys', 'Girls'].forEach(g => {
        if (state.scope !== 'ALL' && state.scope !== div) return;
        if (state.gend !== 'ALL' && state.gend !== g) return;
        const vals = [];
        RAW.races.filter(r => r.division === div && r.gender === g).forEach(r => {
          r.all_runners.forEach(ru => {
            const p = (ru.pace_seconds || parsePaceSec(ru.pace)) / 60;
            if (p && p >= 4.8 && p <= 12.5) vals.push(p);
          });
        });
        if (vals.length >= 5) {
          combos.push({ label: `${div.replace(' (9-12)', ' 9-12').replace(' (7-8)', ' 7-8').replace('Elementary ', '').replace('Developmental', 'Dev')} ${g}`, values: vals, med: d3.median(vals) || 99 });
        }
      });
    });
    combos.sort((a, b) => a.med - b.med);
    combos.forEach((s, i) => { s.color = ridgePalette[i % ridgePalette.length]; });
    drawRidgelineChart(
      el('overallRidgeChart'),
      combos,
      [4.8, 12.0],
      'Mile Pace (minutes per mile, faster on left)',
      el('overallRidgeSo'),
      `Comparing mile-pace distributions across every division and gender from fastest median at the top to developing divisions below.`
    );
  }
}

/* ============================================================================
   TAB 2: SCHOOLS (Schools × Races Heatmap + Runner Scoring Composition)
   ============================================================================ */
function renderSchoolsTab() {
  const heatEl = el('schoolsHeatmap');
  if (!heatEl) return;

  const P = VZ.pal();
  const races = RAW.races.filter(r => !r.is_1m && r.division === state.schoolDiv && r.gender === state.schoolGend)
    .sort((a, b) => a.date.localeCompare(b.date));

  if (!races.length) {
    heatEl.innerHTML = '<div class="sub">No races found for this division and gender.</div>';
    return;
  }

  // Collect all schools that competed in this division + gender
  const schoolStats = {};
  races.forEach(r => {
    (r.school_teams || []).forEach(st => {
      if (!schoolStats[st.team]) {
        schoolStats[st.team] = {
          team: st.team,
          is_aquinas: st.is_aquinas,
          scored_races: 0,
          total_races: 0,
          wins: 0,
          positions: [],
          byRace: {}
        };
      }
      const s = schoolStats[st.team];
      s.total_races++;
      s.byRace[r.race_id] = st;
      if (typeof st.position === 'number') {
        s.scored_races++;
        s.positions.push(st.position);
        if (st.position === 1) s.wins++;
      }
    });
  });

  // Sort schools: scored schools first by best avg position & wins, then unscored schools
  const schools = Object.values(schoolStats).sort((a, b) => {
    if (a.scored_races > 0 && b.scored_races === 0) return -1;
    if (a.scored_races === 0 && b.scored_races > 0) return 1;
    if (a.scored_races > 0 && b.scored_races > 0) {
      const avgA = d3.mean(a.positions), avgB = d3.mean(b.positions);
      if (Math.abs(avgA - avgB) > 0.15) return avgA - avgB;
      return b.scored_races - a.scored_races;
    }
    return b.total_races - a.total_races;
  });

  // Ensure default selected cell is Aquinas in the most recent race (or first available)
  if (!state.selectedSchoolCell || !races.some(r => r.race_id === state.selectedSchoolCell.race_id)) {
    const lastRace = races[races.length - 1];
    state.selectedSchoolCell = { race_id: lastRace.race_id, team: 'Aquinas Academy' };
  }

  // Render D3 Matrix Heatmap: Rows = Schools, Columns = Races
  const rowH = 32;
  const h = schools.length * rowH + 74;
  const o = VZ.svg(heatEl, 900, h, { t: 54, r: 90, b: 16, l: 175 }), g = o.g;

  const x = d3.scaleBand().domain(races.map(r => r.race_id)).range([0, o.iw]).padding(0.08);
  const y = d3.scaleBand().domain(schools.map(s => s.team)).range([0, o.ih]).padding(0.12);

  // Rank color scale (#1 = gold/emerald, #2 = blue, #3 = teal, higher = muted slate)
  const rankColor = pos => {
    if (pos === 1) return '#12b886';
    if (pos === 2) return '#2185d5';
    if (pos === 3) return '#15aabf';
    if (pos === 4) return '#eab308';
    if (pos === 5) return '#f59f00';
    if (typeof pos === 'number') return '#e8590c';
    return P.soft;
  };

  // Column headers (Meet names & dates)
  const colHeaderFont = x.bandwidth() < 78 ? '10px' : '11.5px';
  races.forEach(r => {
    const cx = x(r.race_id) + x.bandwidth() / 2;
    const shortHdr = x.bandwidth() < 78
      ? r.meet_short.replace('Invite', '').replace('Champs', 'Ch.').replace('Classic', '').replace('Foundation', 'PIAA').replace('Catholic', 'Cath.').replace('Youthtowne Clash', 'Youthtowne').replace('Aquinas Home', 'Aquinas').trim()
      : r.meet_short;
    g.append('text')
      .attr('x', cx).attr('y', -24).attr('text-anchor', 'middle')
      .attr('fill', P.fg).style('font-size', colHeaderFont).style('font-weight', '600')
      .text(shortHdr);
    g.append('text')
      .attr('x', cx).attr('y', -9).attr('text-anchor', 'middle')
      .attr('fill', P.muted).style('font-family', 'var(--font-mono)').style('font-size', '10px')
      .text(r.date.slice(5));
  });

  // Right column header: Avg Rank / Wins
  g.append('text')
    .attr('x', o.iw + 44).attr('y', -14).attr('text-anchor', 'middle')
    .attr('fill', P.muted).style('font-family', 'var(--font-mono)').style('font-size', '10.5px')
    .text('AVG / W');

  schools.forEach(s => {
    const ry = y(s.team);
    // School row label
    g.append('text')
      .attr('x', -10).attr('y', ry + y.bandwidth() / 2 + 4)
      .attr('text-anchor', 'end')
      .attr('fill', s.is_aquinas ? P.up : P.fg)
      .style('font-size', '12px')
      .style('font-weight', s.is_aquinas ? '700' : '500')
      .text(s.is_aquinas ? '★ ' + s.team : s.team);

    // Summary on right
    const avgTxt = s.scored_races ? `#${d3.mean(s.positions).toFixed(1)} (${s.wins}W)` : `Inc. (${s.total_races}r)`;
    g.append('text')
      .attr('x', o.iw + 44).attr('y', ry + y.bandwidth() / 2 + 4)
      .attr('text-anchor', 'middle')
      .attr('fill', s.is_aquinas ? P.up : P.fg2)
      .style('font-family', 'var(--font-mono)').style('font-size', '11px')
      .text(avgTxt);

    races.forEach(r => {
      const cx = x(r.race_id);
      const cell = s.byRace[r.race_id];
      const isSel = state.selectedSchoolCell && state.selectedSchoolCell.race_id === r.race_id && state.selectedSchoolCell.team === s.team;

      if (!cell) {
        // Did not compete
        g.append('rect')
          .attr('x', cx).attr('y', ry).attr('width', x.bandwidth()).attr('height', y.bandwidth())
          .attr('rx', 4).attr('fill', P.soft).attr('fill-opacity', 0.35);
        g.append('text')
          .attr('x', cx + x.bandwidth() / 2).attr('y', ry + y.bandwidth() / 2 + 4)
          .attr('text-anchor', 'middle').attr('fill', P.muted).style('font-size', '10px').text('—');
        return;
      }

      const isScored = typeof cell.position === 'number';
      const bg = rankColor(cell.position);
      const cellG = g.append('g')
        .style('cursor', 'pointer')
        .on('click', () => {
          state.selectedSchoolCell = { race_id: r.race_id, team: s.team };
          renderSchoolsTab();
        })
        .on('mousemove', e => {
          const compLines = (cell.composition || []).slice(0, 5).map(c =>
            `#${c.team_rank} ${esc(c.name)}: <b>${c.scoring_points != null ? c.scoring_points + ' pts' : '#' + c.overall_place + ' OA'}</b> (${esc(c.time)})`
          ).join('<br>');
          tip.show(`<b>${esc(s.team)} at ${esc(r.meet_short)}</b><br>${isScored ? 'Rank <b>#' + cell.position + '</b> · <b>' + cell.points + ' pts</b> (' + esc(cell.avg_time) + ' avg)' : 'Incomplete team (' + cell.finishers_count + ' finishers)'}<hr style="border:0;border-top:1px solid var(--line);margin:4px 0">${compLines}`, e);
        })
        .on('mouseleave', tip.hide);

      cellG.append('rect')
        .attr('x', cx).attr('y', ry).attr('width', x.bandwidth()).attr('height', y.bandwidth())
        .attr('rx', 4)
        .attr('fill', bg)
        .attr('fill-opacity', isScored ? 0.85 : 0.65)
        .attr('stroke', isSel ? P.fg : (s.is_aquinas ? '#e5c058' : 'none'))
        .attr('stroke-width', isSel ? 2.4 : (s.is_aquinas ? 1.5 : 0));

      const labelTxt = isScored ? `#${cell.position} (${cell.points}p)` : `Inc (${cell.finishers_count})`;
      cellG.append('text')
        .attr('x', cx + x.bandwidth() / 2).attr('y', ry + y.bandwidth() / 2 + 4)
        .attr('text-anchor', 'middle')
        .attr('fill', isScored ? '#ffffff' : P.muted)
        .style('font-family', 'var(--font-mono)')
        .style('font-size', x.bandwidth() < 85 ? '10px' : '11px')
        .style('font-weight', isScored ? '600' : '400')
        .text(labelTxt);
    });
  });

  const aqStat = schoolStats['Aquinas Academy'];
  if (el('schoolsHeatmapSo')) {
    el('schoolsHeatmapSo').innerHTML = aqStat
      ? `Across ${races.length} races in <b>${esc(state.schoolDiv)} ${esc(state.schoolGend)}</b>, <b>Aquinas Academy</b> recorded <b>${aqStat.wins} first-place team win${aqStat.wins === 1 ? '' : 's'}</b> and an average team finish of <b>#${aqStat.positions.length ? d3.mean(aqStat.positions).toFixed(1) : '—'}</b>. Click any cell in the matrix to inspect how each runner's points built the team score below.`
      : '';
  }

  // Render the Runner Point Composition Stacked Bar Chart & Detail Table for the selected race & school!
  renderSchoolCompositionPanel(races);
}

function renderSchoolCompositionPanel(races) {
  const P = VZ.pal();
  const selRace = races.find(r => r.race_id === (state.selectedSchoolCell && state.selectedSchoolCell.race_id)) || races[races.length - 1];
  const selTeamName = (state.selectedSchoolCell && state.selectedSchoolCell.team) || 'Aquinas Academy';

  if (el('compRaceTitle')) {
    el('compRaceTitle').textContent = `${selRace.meet_name} — ${selRace.division} ${selRace.gender} (${selRace.date})`;
  }

  const scoredTeams = (selRace.school_teams || []).filter(s => s.scored);
  const stackEl = el('schoolStackedBars');
  if (stackEl) {
    if (!scoredTeams.length) {
      stackEl.innerHTML = '<div class="sub">No schools fielded 5+ runners for full team scoring in this race.</div>';
    } else {
      const rowH = 34;
      const h = scoredTeams.length * rowH + 44;
      const o = VZ.svg(stackEl, 520, h, { t: 10, r: 58, b: 28, l: 150 }), g = o.g;
      const y = d3.scaleBand().domain(scoredTeams.map(s => `#${s.position} ${s.team}`)).range([0, o.ih]).padding(0.26);
      const maxPts = d3.max(scoredTeams, s => s.points) || 100;
      const x = d3.scaleLinear().domain([0, maxPts * 1.12]).range([0, o.iw]);

      const rankColors = ['#1d6fd6', '#15aabf', '#12b886', '#eab308', '#f76707'];

      scoredTeams.forEach(s => {
        const rowLbl = `#${s.position} ${s.team}`;
        const ry = y(rowLbl);
        let cumX = 0;
        s.composition.slice(0, 5).forEach((ru, idx) => {
          const pts = ru.scoring_points || 0;
          const w = Math.max(2, x(pts));
          g.append('rect')
            .attr('x', x(cumX)).attr('y', ry).attr('width', w - 1).attr('height', y.bandwidth())
            .attr('fill', rankColors[idx]).attr('rx', 2).attr('opacity', s.team === selTeamName ? 0.95 : 0.72)
            .style('cursor', 'pointer')
            .on('click', () => { state.selectedSchoolCell = { race_id: selRace.race_id, team: s.team }; renderSchoolsTab(); })
            .on('mousemove', e => tip.show(`<b>${esc(s.team)} · Scorer #${idx + 1}</b><br>Runner: <b>${esc(ru.name)}</b> (Gr ${ru.grade})<br>Scoring Points Added: <b>+${pts} pts</b> (#${ru.overall_place} overall)<br>Time: ${esc(ru.time)} (${esc(ru.pace)})`, e))
            .on('mouseleave', tip.hide);

          if (w > 22) {
            g.append('text')
              .attr('x', x(cumX) + w / 2).attr('y', ry + y.bandwidth() / 2 + 4)
              .attr('text-anchor', 'middle').attr('fill', '#fff')
              .style('font-family', 'var(--font-mono)').style('font-size', '10px').style('font-weight', '600')
              .text(`+${pts}`);
          }
          cumX += pts;
        });

        g.append('text')
          .attr('x', x(s.points) + 6).attr('y', ry + y.bandwidth() / 2 + 4)
          .attr('fill', s.is_aquinas ? P.up : P.fg).style('font-family', 'var(--font-mono)').style('font-size', '11px').style('font-weight', '600')
          .text(`${s.points}p`);
      });

      const yAx = g.append('g').call(d3.axisLeft(y).tickSize(0));
      VZ.axisStyle(yAx);
      VZ.axisStyle(g.append('g').attr('transform', `translate(0,${o.ih})`).call(d3.axisBottom(x).ticks(5).tickFormat(d => d + ' pts')));
    }
  }

  // Right card: Detailed Runner Composition Table for the selected School (or Aquinas if selected school didn't run)
  let focusSchool = (selRace.school_teams || []).find(s => s.team === selTeamName)
    || (selRace.school_teams || []).find(s => s.is_aquinas)
    || (selRace.school_teams || [])[0];

  if (el('compSchoolSelect')) {
    el('compSchoolSelect').innerHTML = (selRace.school_teams || []).map(s =>
      `<option value="${esc(s.team)}" ${focusSchool && s.team === focusSchool.team ? 'selected' : ''}>${esc(s.team)} (${typeof s.position === 'number' ? '#' + s.position + ' · ' + s.points + ' pts' : 'Inc. · ' + s.finishers_count + ' runners'})</option>`
    ).join('');
  }

  if (focusSchool && el('compSchoolTableBody')) {
    const totPts = focusSchool.points || 0;
    el('compSchoolTableBody').innerHTML = focusSchool.composition.map(c => {
      const isScorer = c.team_rank <= 5 && focusSchool.scored;
      const share = (isScorer && totPts > 0 && c.scoring_points) ? Math.round(100 * c.scoring_points / totPts) + '%' : '—';
      const roleTxt = c.team_rank <= 5
        ? (focusSchool.scored ? `Scorer #${c.team_rank}` : `Runner #${c.team_rank} (<5 team)`)
        : `Displacer #${c.team_rank}*`;
      const ptsTxt = isScorer ? `+${c.scoring_points} pts` : (c.displacer_points ? `(${c.displacer_points}*)` : '—');
      return `
        <tr class="${isScorer ? '' : 'hl'}">
          <td class="mono">${roleTxt}</td>
          <td><b>${esc(c.name)}</b></td>
          <td class="num">${c.grade}</td>
          <td class="num">#${c.overall_place}</td>
          <td class="num"><b>${ptsTxt}</b></td>
          <td class="num">${share}</td>
          <td class="num">${esc(c.time)}</td>
          <td class="num">${esc(c.pace)}</td>
        </tr>
      `;
    }).join('');

    if (el('compSchoolSummary')) {
      el('compSchoolSummary').innerHTML = focusSchool.scored
        ? `<b>${esc(focusSchool.team)}</b> finished <b>#${focusSchool.position}</b> with <b>${focusSchool.points} points</b> (top-5 total time ${esc(focusSchool.total_time)}, average ${esc(focusSchool.avg_time)}). Runners #1–#5 add to the team score; runners #6 and #7 do not add to ${esc(focusSchool.team)}'s points but push trailing opponents' scores higher.`
        : `<b>${esc(focusSchool.team)}</b> fielded ${focusSchool.finishers_count} runner${focusSchool.finishers_count === 1 ? '' : 's'} in this race (5 required for a team score).`;
    }
  }
}

/* ============================================================================
   TAB 3: AQUINAS TEAM (Team Ridgeline + Pack Ladder + Season Gains + Scorecards)
   ============================================================================ */
function renderTeamTab() {
  const perfs = RAW.performances.filter(matchFilter);
  const teams = RAW.team_standings.filter(matchFilter);
  const teamWins = teams.filter(t => t.aquinas_position === 1).length;
  const teamPodiums = teams.filter(t => typeof t.aquinas_position === 'number' && t.aquinas_position <= 3).length;
  const allMultiAth = ATHLETES.filter(matchFilter).filter(a => a.best_gain_sec != null);
  const improvedAth = allMultiAth.filter(a => a.best_gain_sec < 0);

  if (el('kpisTeam')) {
    el('kpisTeam').innerHTML = `
      <div class="kpi"><div class="v up">${teamWins}</div><div class="l">1st-place team championships</div></div>
      <div class="kpi"><div class="v">${teamPodiums} <span style="font-size:14px;color:var(--muted)">/ ${teams.filter(t => typeof t.aquinas_position === 'number').length}</span></div><div class="l">Top-3 team podiums</div></div>
      <div class="kpi"><div class="v">${perfs.filter(p => p.overall_place <= 10).length}</div><div class="l">Aquinas top-10 finishes</div></div>
      <div class="kpi"><div class="v up">${improvedAth.length}/${allMultiAth.length}</div><div class="l">Runners faster after opener</div></div>
    `;
  }

  // 1. Aquinas Ridgeline Density Chart (Divisions vs Meets toggle)
  const ridgePalette = ['#1588e8', '#f03e6b', '#2eb85c', '#e8cf4d', '#146cb8', '#cb333b', '#333b48', '#7c52cc'];
  if (state.teamRidgeMode === 'divisions') {
    const series = [];
    CATS.forEach(div => {
      ['Boys', 'Girls'].forEach(g => {
        if (state.scope !== 'ALL' && state.scope !== div) return;
        if (state.gend !== 'ALL' && state.gend !== g) return;
        const vals = RAW.performances
          .filter(p => p.division === div && p.gender === g && p.pace_seconds)
          .map(p => p.pace_seconds / 60)
          .filter(v => v >= 4.8 && v <= 12.5);
        if (vals.length >= 4) {
          series.push({
            label: `${div.replace(' (9-12)', ' 9-12').replace(' (7-8)', ' 7-8').replace('Elementary ', '').replace('Developmental', 'Dev')} ${g}`,
            values: vals,
            med: d3.median(vals) || 99
          });
        }
      });
    });
    series.sort((a, b) => a.med - b.med);
    series.forEach((s, i) => { s.color = ridgePalette[i % ridgePalette.length]; });
    drawRidgelineChart(
      el('teamRidgeChart'),
      series,
      [4.8, 12.0],
      'Aquinas Academy Mile Pace (min/mile, faster on left)',
      el('teamRidgeSo'),
      `Aquinas Academy pace distributions by squad, ordered from fastest median squad at the top to developing K–4 squads below.`
    );
  } else {
    const byMeet = d3.groups(RAW.performances.filter(matchFilter).filter(p => p.pace_seconds), p => p.meet_short);
    const series = byMeet.map(([mName, list]) => {
      const vals = list.map(p => p.pace_seconds / 60).filter(v => v >= 4.8 && v <= 12.5);
      return { label: mName, values: vals, med: d3.median(vals) || 99 };
    }).filter(s => s.values.length >= 4).sort((a, b) => a.med - b.med);
    series.forEach((s, i) => { s.color = ridgePalette[i % ridgePalette.length]; });
    drawRidgelineChart(
      el('teamRidgeChart'),
      series,
      [4.8, 12.0],
      'Aquinas Academy Mile Pace (min/mile, faster on left)',
      el('teamRidgeSo'),
      `Aquinas Academy's team-wide pace distribution at each meet of the 2026 season, sorted from fastest median meet to toughest course.`
    );
  }

  // 2. Pack Ladder + Top-5 Avg + 1-to-5 Spread
  renderPackLadderAndTeamCharts();

  // 3. Season Pacing Improvement Charts
  renderSeasonProgression();

  // 4. Course Box Plot & Team Standings Ledger
  renderCourseBoxChart(getSelectedAthlete());
  renderStandings();
}

/* ============================================================================
   TAB 4: RUNNERS (Clean Names, Search, Individual Pace Bar Charts, Where Do You Fall, Map)
   ============================================================================ */
function renderRunnersTab() {
  const ath = getSelectedAthlete();
  renderWhereDoYouFall();
  renderCardsAndProf();
  renderMap();
}

/* SHARED CHART RENDERERS */
function renderWhereDoYouFall() {
  if (!el('distChart')) return;
  const P = VZ.pal();
  const ath = getSelectedAthlete();
  if (el('activeRunnerLabel')) el('activeRunnerLabel').textContent = ath.name;

  // Populate runner dropdown with JUST the runner's clean name!
  const poolAth = ATHLETES.filter(matchFilter).slice().sort((a, b) => a.name.localeCompare(b.name));
  if (el('runnerSelectTop')) {
    el('runnerSelectTop').innerHTML = poolAth.map(a =>
      `<option value="${a.id}" ${a.id === ath.id ? 'selected' : ''}>${esc(a.name)}</option>`
    ).join('');
  }

  const targetDiv = state.scope !== 'ALL' ? state.scope : ath.division;
  let buckets = [];
  if (state.bucketMode === 'pace') {
    const edges = [0, 330, 360, 390, 420, 450, 480, 510, 540, 570, 600, 660, 720, 9999];
    const labels = [
      '< 5:30/M', '5:30–6:00', '6:00–6:30', '6:30–7:00', '7:00–7:30',
      '7:30–8:00', '8:00–8:30', '8:30–9:00', '9:00–9:30', '9:30–10:00',
      '10:00–11:00', '11:00–12:00', '> 12:00/M'
    ];
    buckets = labels.map((l, i) => ({ label: l, min: edges[i], max: edges[i + 1], count: 0 }));
  } else {
    let edges, labels;
    if (targetDiv === 'HS Varsity (9-12)') {
      edges = [0, 1020, 1110, 1200, 1290, 1380, 1470, 1560, 1650, 1740, 1860, 99999];
      labels = ['< 17:00', '17:00–18:30', '18:30–20:00', '20:00–21:30', '21:30–23:00', '23:00–24:30', '24:30–26:00', '26:00–27:30', '27:30–29:00', '29:00–31:00', '> 31:00'];
    } else if (targetDiv === 'Developmental (K-4)') {
      edges = [0, 480, 525, 570, 615, 660, 705, 750, 810, 870, 960, 99999];
      labels = ['< 8:00', '8:00–8:45', '8:45–9:30', '9:30–10:15', '10:15–11:00', '11:00–11:45', '11:45–12:30', '12:30–13:30', '13:30–14:30', '14:30–16:00', '> 16:00'];
    } else {
      edges = [0, 660, 720, 780, 840, 900, 960, 1020, 1080, 1170, 1260, 99999];
      labels = ['< 11:00', '11:00–12:00', '12:00–13:00', '13:00–14:00', '14:00–15:00', '15:00–16:00', '16:00–17:00', '17:00–18:00', '18:00–19:30', '19:30–21:00', '> 21:00'];
    }
    buckets = labels.map((l, i) => ({ label: l, min: edges[i], max: edges[i + 1], count: 0 }));
  }

  const values = [];
  RAW.races.forEach(r => {
    if (state.bucketMode === 'time' && (r.division !== targetDiv || r.is_1m)) return;
    if (state.bucketMode === 'pace' && state.scope !== 'ALL' && r.division !== state.scope) return;
    if (state.gend !== 'ALL' && r.gender !== state.gend) return;
    const list = state.bucketPop === 'aquinas' ? r.aquinas_runners : r.all_runners;
    list.forEach(runner => {
      const val = state.bucketMode === 'pace' ? (runner.pace_seconds || parsePaceSec(runner.pace)) : runner.time_seconds;
      if (val != null) values.push(val);
    });
  });

  values.forEach(v => {
    const b = buckets.find(bk => v >= bk.min && v < bk.max);
    if (b) b.count++;
  });

  const totalN = Math.max(1, d3.sum(buckets, b => b.count));
  buckets.forEach(b => { b.pct = (100 * b.count / totalN); });

  const athPRVal = state.bucketMode === 'pace' ? ath.pr_pace_seconds : ath.pr_seconds;
  const athAvgVal = state.bucketMode === 'pace' ? ath.avg_pace_seconds : ath.avg_seconds;

  const spectrum = [
    '#1d6fd6', '#2185d5', '#15aabf', '#12b886', '#82c91e',
    '#eab308', '#f59f00', '#f76707', '#e8590c', '#f59f00',
    '#eab308', '#12b886', '#2185d5'
  ];

  const h = buckets.length * 26 + 38;
  const o = VZ.svg(el('distChart'), 520, h, { t: 10, r: 74, b: 26, l: 86 }), g = o.g;
  const y = d3.scaleBand().domain(buckets.map(b => b.label)).range([0, o.ih]).padding(0.32);
  const maxPct = Math.max(15, d3.max(buckets, b => b.pct) || 20);
  const x = d3.scaleLinear().domain([0, maxPct * 1.12]).range([0, o.iw]);

  x.ticks(4).forEach(tk => {
    g.append('line').attr('x1', x(tk)).attr('x2', x(tk)).attr('y1', 0).attr('y2', o.ih).attr('stroke', P.line).attr('stroke-dasharray', '2 2');
  });

  buckets.forEach((b, i) => {
    const isPR = athPRVal != null && athPRVal >= b.min && athPRVal < b.max;
    const isAvg = athAvgVal != null && athAvgVal >= b.min && athAvgVal < b.max;
    const isHi = isPR || isAvg;
    const barW = Math.max(4, x(b.pct));
    const col = spectrum[i % spectrum.length];

    if (isHi) {
      g.append('rect')
        .attr('x', -6).attr('y', y(b.label) - 3.5)
        .attr('width', barW + 12).attr('height', y.bandwidth() + 7)
        .attr('rx', 7).attr('fill', 'none').attr('stroke', '#e5c058').attr('stroke-width', 2.2);
    }

    g.append('rect')
      .attr('x', 0).attr('y', y(b.label)).attr('width', barW).attr('height', y.bandwidth())
      .attr('rx', 4).attr('fill', col)
      .on('mousemove', e => tip.show(`<b>Bucket: ${esc(b.label)}</b><br>${b.count} finishes (${b.pct.toFixed(1)}% of ${totalN})<br>${isPR ? '&#9733; <b>' + esc(ath.name) + ' PR (' + (state.bucketMode === 'pace' ? ath.pr_pace : ath.pr_time) + ')</b><br>' : ''}${isAvg ? '&#9679; <b>' + esc(ath.name) + ' Season Avg</b>' : ''}`, e))
      .on('mouseleave', tip.hide);

    const tagTxt = isPR && isAvg ? ' (PR & Avg)' : isPR ? ' (PR)' : isAvg ? ' (Avg)' : '';
    g.append('text')
      .attr('x', barW + (isHi ? 10 : 6)).attr('y', y(b.label) + y.bandwidth() / 2 + 4)
      .attr('fill', isHi ? '#e5c058' : P.fg)
      .style('font-size', '11px').style('font-weight', isHi ? '600' : '500').style('font-family', 'var(--font-mono)')
      .text(`${Math.round(b.pct)}%${tagTxt}`);
  });

  const yAxis = g.append('g').call(d3.axisLeft(y).tickSize(0));
  VZ.axisStyle(yAxis);
  yAxis.selectAll('text').style('font-family', 'var(--font-mono)').style('font-size', '11px').each(function(d) {
    const b = buckets.find(bk => bk.label === d);
    if (b && ((athPRVal >= b.min && athPRVal < b.max) || (athAvgVal >= b.min && athAvgVal < b.max))) {
      d3.select(this).attr('fill', '#e5c058').style('font-weight', '600');
    }
  });
  VZ.axisStyle(g.append('g').attr('transform', `translate(0,${o.ih})`).call(d3.axisBottom(x).ticks(4).tickFormat(d => d + '%').tickSize(3)));

  if (el('distTitle')) {
    el('distTitle').textContent = state.bucketMode === 'pace'
      ? `Where do you fall? Mile pace distribution (N = ${totalN})`
      : `Where do you fall? ${targetDiv} finish times (N = ${totalN})`;
  }
  const fasterCount = values.filter(v => v < (athPRVal || 99999)).length;
  const topShare = ((fasterCount / totalN) * 100).toFixed(1);
  if (el('dist-so')) {
    el('dist-so').innerHTML = `<b>${esc(ath.name)}</b>'s personal best (<b>${esc(ath.pr_time)}</b>, <b>${esc(ath.pr_pace)}</b>) places in the top <b>${topShare}%</b> of all ${totalN} finishes in this view.`;
  }
}

function renderCourseBoxChart(ath) {
  if (!el('courseBoxChart')) return;
  const P = VZ.pal();
  const perfs = RAW.performances.filter(matchFilter).filter(p => p.pace_seconds != null);
  const byMeet = d3.groups(perfs, d => d.short_meet_name);
  const meetStats = byMeet.map(([mName, list]) => {
    const vals = list.map(d => d.pace_seconds / 60).sort(d3.ascending);
    const athRun = list.find(d => d.name === ath.name);
    return {
      meet: mName,
      date: list[0].date,
      q25: d3.quantile(vals, 0.25),
      med: d3.quantile(vals, 0.50),
      q75: d3.quantile(vals, 0.75),
      min: vals[0],
      max: vals[vals.length - 1],
      n: vals.length,
      athPace: athRun ? athRun.pace_seconds / 60 : null,
      athTime: athRun ? athRun.time : null
    };
  }).sort((a, b) => a.date.localeCompare(b.date));

  const h = Math.max(260, meetStats.length * 28 + 36);
  const o = VZ.svg(el('courseBoxChart'), 520, h, { t: 10, r: 24, b: 28, l: 142 }), g = o.g;
  const y = d3.scaleBand().domain(meetStats.map(d => d.meet)).range([0, o.ih]).padding(0.35);
  const minP = Math.max(4.5, (d3.min(meetStats, d => d.min) || 5.5) - 0.3);
  const maxP = Math.min(13.0, (d3.max(meetStats, d => d.max) || 10.5) + 0.3);
  const x = d3.scaleLinear().domain([minP, maxP]).range([0, o.iw]);

  meetStats.forEach(d => {
    const cy = y(d.meet) + y.bandwidth() / 2;
    g.append('line').attr('x1', x(d.min)).attr('x2', x(d.max)).attr('y1', cy).attr('y2', cy).attr('stroke', P.line).attr('stroke-width', 1.5);
    g.append('rect')
      .attr('x', x(d.q25)).attr('y', y(d.meet))
      .attr('width', Math.max(3, x(d.q75) - x(d.q25))).attr('height', y.bandwidth())
      .attr('fill', P.accent).attr('fill-opacity', 0.28).attr('stroke', P.accent).attr('rx', 3)
      .on('mousemove', e => tip.show(`<b>${esc(d.meet)}</b> (${d.n} Aquinas finishes)<br>Fastest: ${fmtPaceSec(d.min * 60)} · Median: <b>${fmtPaceSec(d.med * 60)}</b> · 75th: ${fmtPaceSec(d.q75 * 60)}`, e))
      .on('mouseleave', tip.hide);
    g.append('line').attr('x1', x(d.med)).attr('x2', x(d.med)).attr('y1', y(d.meet)).attr('y2', y(d.meet) + y.bandwidth()).attr('stroke', P.fg).attr('stroke-width', 2);
  });

  VZ.axisStyle(g.append('g').call(d3.axisLeft(y).tickSize(0)));
  VZ.axisStyle(g.append('g').attr('transform', `translate(0,${o.ih})`).call(d3.axisBottom(x).ticks(5).tickFormat(d => fmtPaceSec(d * 60))));

  const fastestCourse = meetStats.slice().sort((a, b) => a.med - b.med)[0];
  const toughestCourse = meetStats.slice().sort((a, b) => b.med - a.med)[0];
  if (el('course-so') && fastestCourse && toughestCourse) {
    el('course-so').innerHTML = `Shaded boxes span the middle 50% (25th–75th percentile) of Aquinas paces at each meet; vertical bars mark the team median. Fastest median course: <b>${esc(fastestCourse.meet)}</b> (${fmtPaceSec(fastestCourse.med * 60)}); toughest course: <b>${esc(toughestCourse.meet)}</b> (${fmtPaceSec(toughestCourse.med * 60)}).`;
  }
}

function renderCardsAndProf() {
  if (!el('cards') || !el('prof')) return;
  let list = ATHLETES.filter(matchFilter);
  if (state.search) {
    list = list.filter(a => a.name.toLowerCase().includes(state.search));
  }
  list = list.slice().sort((a, b) => (b.avg_percentile + b.races_count * 6) - (a.avg_percentile + a.races_count * 6));

  const f = getSelectedAthlete();
  const shown = list.slice(0, state.cardLimit);
  // Runner cards show JUST their clean name as the bold title!
  el('cards').innerHTML = shown.map(a => `
    <button class="fc" data-id="${a.id}" aria-pressed="${a.id === f.id}">
      <span class="mono-b" style="background:${cc(a.cat)}">${esc(a.ab)}</span>
      <span style="min-width:0">
        <b>${esc(a.name)}</b>
        <span>${esc(a.division)}</span>
        <span class="mono">${esc(a.pr_time)} · ${esc(a.pr_pace)}</span>
      </span>
    </button>
  `).join('');

  el('cards').onclick = e => {
    const b = e.target.closest('[data-id]');
    if (b) {
      state.selAth = b.dataset.id;
      renderRunnersTab();
      el('prof').scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  };

  const xcRaces = f.races.filter(r => !r.is_1m);
  const firstXC = xcRaces[0];
  const facts = [
    `Division: ${f.division} (Grade ${f.grade_or_age}). Personal-best XC time: ${f.pr_time} (${f.pr_pace}) at ${f.pr_meet}.`,
    `Completed ${f.races_count} race${f.races_count > 1 ? 's' : ''} in 2026, placing as high as #${f.best_place} overall (${f.top_10_finishes} top-10 finishes) with a ${f.avg_percentile}% mean field percentile.`
  ];
  if (f.best_gain_sec != null && firstXC) {
    facts.push(`Pacing progression: opened the XC season at ${firstXC.pace} (${firstXC.short_meet_name}) and reached ${f.pr_pace} (${f.best_gain_sec <= 0 ? Math.abs(f.best_gain_sec) + ' sec/mile faster' : '+' + f.best_gain_sec + ' sec/mile'}).`);
  }

  const rowsHtml = f.races.map((r, idx) => {
    const prev = idx > 0 ? f.races[idx - 1] : null;
    const pDelta = (prev && r.pace_seconds && prev.pace_seconds) ? (r.pace_seconds - prev.pace_seconds) : null;
    const pDeltaStr = pDelta == null ? '—' : (pDelta <= 0 ? `<span class="up">${pDelta}s/M</span>` : `<span class="down">+${pDelta}s/M</span>`);
    return `
      <tr>
        <td class="mono">${esc(r.date)}</td>
        <td><b>${esc(r.short_meet_name)}</b>${r.is_1m ? ' <span class="chip">1 Mile</span>' : ''}</td>
        <td class="num">#${r.overall_place} <span style="color:var(--muted)">/ ${r.total_finishers}</span></td>
        <td class="num">#${r.team_rank}</td>
        <td class="num"><b>${esc(r.time)}</b></td>
        <td class="num"><b>${esc(r.pace)}</b></td>
        <td class="num">${pDeltaStr}</td>
        <td class="num">${r.percentile}%</td>
        <td><a href="${esc(r.source_url)}" target="_blank" rel="noopener">HTML</a></td>
      </tr>
    `;
  }).join('');

  el('prof').innerHTML = `
    <div class="prof">
      <span class="mono-b" style="background:${cc(f.cat)}">${esc(f.ab)}</span>
      <div style="min-width:0">
        <h3>${esc(f.name)}</h3>
        <div class="meta">${esc(f.division)} · ${esc(f.gender)} · Grade ${f.grade_or_age} · ${f.races_count} races · XC PR ${esc(f.pr_time)} (${esc(f.pr_pace)})</div>
        <ul>${facts.map(t => `<li>${esc(t)}</li>`).join('')}</ul>
        <div class="two" style="margin:12px 0">
          <div class="card" style="padding:12px;background:var(--bg)">
            <h3 style="font-size:13.5px">Meet-by-meet mile pace (green = faster than prior race)</h3>
            <div id="indivPaceBars"></div>
          </div>
          <div class="card" style="padding:12px;background:var(--bg)">
            <h3 style="font-size:13.5px">Field percentile trajectory (100% = top of race field)</h3>
            <div id="indivPctChart"></div>
          </div>
        </div>
        <div class="tablewrap">
          <table class="t">
            <thead>
              <tr><th>Date</th><th>Meet</th><th class="num">Overall</th><th class="num">Aquinas #</th><th class="num">Time</th><th class="num">Pace</th><th class="num">Pace &Delta;</th><th class="num">Field %</th><th>Sheet</th></tr>
            </thead>
            <tbody>${rowsHtml}</tbody>
          </table>
        </div>
      </div>
    </div>
  `;

  renderIndividualProfileCharts(f);
}

function renderIndividualProfileCharts(f) {
  const P = VZ.pal();
  const races = f.races.filter(r => r.pace_seconds != null);
  if (!races.length) return;

  const o1 = VZ.svg(el('indivPaceBars'), 420, 210, { t: 22, r: 14, b: 48, l: 48 }), g1 = o1.g;
  const labels = races.map(r => r.meet_short || r.short_meet_name.replace(/ \(.*\)/, ''));
  const x1 = d3.scaleBand().domain(labels).range([0, o1.iw]).padding(0.28);
  const minP = Math.max(240, (d3.min(races, r => r.pace_seconds) || 360) - 35);
  const maxP = (d3.max(races, r => r.pace_seconds) || 480) + 25;
  const y1 = d3.scaleLinear().domain([minP, maxP]).range([o1.ih, 0]);

  if (f.avg_pace_seconds) {
    g1.append('line')
      .attr('x1', 0).attr('x2', o1.iw)
      .attr('y1', y1(f.avg_pace_seconds)).attr('y2', y1(f.avg_pace_seconds))
      .attr('stroke', P.muted).attr('stroke-dasharray', '3 3');
  }

  races.forEach((r, i) => {
    const lbl = labels[i];
    const prev = i > 0 ? races[i - 1] : null;
    const improved = prev && r.pace_seconds <= prev.pace_seconds;
    const isBest = r.pace_seconds === d3.min(races, d => d.pace_seconds);
    const barCol = isBest ? '#e5c058' : (improved ? P.up : cc(f.cat));
    const bx = x1(lbl), bw = x1.bandwidth(), by = y1(r.pace_seconds), bh = o1.ih - by;

    g1.append('rect')
      .attr('x', bx).attr('y', by).attr('width', bw).attr('height', Math.max(4, bh))
      .attr('fill', barCol).attr('rx', 3).attr('opacity', 0.88)
      .on('mousemove', e => tip.show(`<b>${esc(f.name)}</b><br>${esc(r.short_meet_name)}<br>Pace: <b>${esc(r.pace)}</b> (${esc(r.time)})<br>Place: #${r.overall_place} of ${r.total_finishers} (${r.percentile}%)`, e))
      .on('mouseleave', tip.hide);

    g1.append('text')
      .attr('x', bx + bw / 2).attr('y', by - 5)
      .attr('text-anchor', 'middle').attr('fill', isBest ? '#e5c058' : P.fg2)
      .style('font-size', '10px').style('font-family', 'var(--font-mono)').style('font-weight', isBest ? '600' : '400')
      .text(r.pace.replace('/M', ''));
  });

  const ax1 = g1.append('g').attr('transform', `translate(0,${o1.ih})`).call(d3.axisBottom(x1).tickSize(3));
  VZ.axisStyle(ax1);
  ax1.selectAll('text').attr('transform', 'rotate(-22)').style('text-anchor', 'end').style('font-size', '10px');
  VZ.axisStyle(g1.append('g').call(d3.axisLeft(y1).ticks(4).tickFormat(d => fmtPaceSec(d).replace('/M', ''))));

  const o2 = VZ.svg(el('indivPctChart'), 420, 210, { t: 22, r: 14, b: 48, l: 44 }), g2 = o2.g;
  const x2 = d3.scalePoint().domain(labels).range([18, o2.iw - 18]);
  const y2 = d3.scaleLinear().domain([0, 105]).range([o2.ih, 0]);

  g2.append('line').attr('x1', 0).attr('x2', o2.iw).attr('y1', y2(50)).attr('y2', y2(50)).attr('stroke', P.line).attr('stroke-dasharray', '3 3');

  const lineGen = d3.line().x((d, i) => x2(labels[i])).y(d => y2(d.percentile));
  g2.append('path').datum(races).attr('fill', 'none').attr('stroke', cc(f.cat)).attr('stroke-width', 2.2).attr('d', lineGen);

  races.forEach((r, i) => {
    const cx = x2(labels[i]), cy = y2(r.percentile);
    g2.append('circle')
      .attr('cx', cx).attr('cy', cy).attr('r', 5)
      .attr('fill', cc(f.cat)).attr('stroke', P.surface).attr('stroke-width', 1.5)
      .on('mousemove', e => tip.show(`<b>${esc(f.name)}</b><br>${esc(r.short_meet_name)}<br>Field Percentile: <b>${r.percentile}%</b><br>Overall Place: #${r.overall_place} of ${r.total_finishers}`, e))
      .on('mouseleave', tip.hide);
    g2.append('text')
      .attr('x', cx).attr('y', cy - 8).attr('text-anchor', 'middle').attr('fill', P.fg2)
      .style('font-size', '10px').style('font-family', 'var(--font-mono)')
      .text(Math.round(r.percentile) + '%');
  });

  const ax2 = g2.append('g').attr('transform', `translate(0,${o2.ih})`).call(d3.axisBottom(x2).tickSize(3));
  VZ.axisStyle(ax2);
  ax2.selectAll('text').attr('transform', 'rotate(-22)').style('text-anchor', 'end').style('font-size', '10px');
  VZ.axisStyle(g2.append('g').call(d3.axisLeft(y2).ticks(4).tickFormat(d => d + '%')));
}

function renderSeasonProgression() {
  if (!el('paceDropChart')) return;
  const P = VZ.pal();
  const gainers = ATHLETES.filter(matchFilter)
    .filter(a => a.best_gain_sec != null && a.best_gain_sec < 0)
    .sort((a, b) => a.best_gain_sec - b.best_gain_sec)
    .slice(0, 16);

  const h1 = Math.max(260, gainers.length * 22 + 34);
  const o1 = VZ.svg(el('paceDropChart'), 520, h1, { t: 8, r: 62, b: 24, l: 138 }), g1 = o1.g;
  const y1 = d3.scaleBand().domain(gainers.map(d => d.name)).range([0, o1.ih]).padding(0.28);
  const maxDrop = Math.max(30, d3.max(gainers, d => Math.abs(d.best_gain_sec)) || 60);
  const x1 = d3.scaleLinear().domain([0, maxDrop * 1.1]).range([0, o1.iw]);

  gainers.forEach(d => {
    const drop = Math.abs(d.best_gain_sec);
    const xcRaces = d.races.filter(r => !r.is_1m);
    const opener = xcRaces[0];
    g1.append('rect')
      .attr('y', y1(d.name)).attr('height', y1.bandwidth())
      .attr('width', x1(drop)).attr('fill', cc(d.division)).attr('rx', 3).attr('opacity', 0.85)
      .on('mousemove', e => tip.show(`<b>${esc(d.name)}</b><br>Pace drop: <b>-${drop} sec/mile</b><br>Opener: ${opener ? opener.pace + ' (' + opener.short_meet_name + ')' : '—'}<br>Best XC: <b>${esc(d.pr_pace)}</b> (${esc(d.pr_meet)})`, e))
      .on('mouseleave', tip.hide);

    g1.append('text')
      .attr('x', x1(drop) + 5).attr('y', y1(d.name) + y1.bandwidth() / 2 + 4)
      .attr('fill', P.up).style('font-size', '11px').style('font-family', 'var(--font-mono)').style('font-weight', '600')
      .text(`-${drop}s/M`);
  });

  VZ.axisStyle(g1.append('g').call(d3.axisLeft(y1).tickSize(0)));
  VZ.axisStyle(g1.append('g').attr('transform', `translate(0,${o1.ih})`).call(d3.axisBottom(x1).ticks(5).tickFormat(d => `-${d}s/M`)));

  const allMulti = ATHLETES.filter(matchFilter).filter(a => a.best_gain_sec != null);
  const impCount = allMulti.filter(a => a.best_gain_sec < 0).length;
  const medDrop = gainers.length ? Math.round(d3.median(gainers, d => Math.abs(d.best_gain_sec))) : 0;
  if (el('pacedrop-so')) {
    el('pacedrop-so').innerHTML = allMulti.length
      ? `<b>${impCount} of ${allMulti.length}</b> multi-race runners (${Math.round(100 * impCount / allMulti.length)}%) ran a faster mile pace later in the season than in their opener, with top improvers shaving a median of <b>${medDrop} seconds per mile</b>.`
      : '';
  }

  const o2 = VZ.svg(el('seasonTrendChart'), 520, h1, { t: 16, r: 24, b: 54, l: 52 }), g2 = o2.g;
  const xcPerfs = RAW.performances.filter(matchFilter).filter(p => !p.is_1m && p.pace_seconds != null);
  const meetOrder = Array.from(new Set(xcPerfs.map(p => p.meet_short)));
  const x2 = d3.scalePoint().domain(meetOrder).range([12, o2.iw - 12]);
  const minY = Math.max(5.0, (d3.min(xcPerfs, p => p.pace_seconds / 60) || 5.5) - 0.2);
  const maxY = Math.min(11.5, (d3.max(xcPerfs, p => p.pace_seconds / 60) || 9.5) + 0.2);
  const y2 = d3.scaleLinear().domain([maxY, minY]).range([o2.ih, 0]);

  CATS.forEach(div => {
    const divPerfs = xcPerfs.filter(p => p.division === div);
    if (!divPerfs.length) return;
    const pts = meetOrder.map(m => {
      const mList = divPerfs.filter(p => p.meet_short === m);
      if (!mList.length) return null;
      const sorted = mList.map(p => p.pace_seconds / 60).sort(d3.ascending);
      const top5Avg = d3.mean(sorted.slice(0, 5));
      return { meet: m, pace: top5Avg, n: mList.length };
    }).filter(Boolean);

    if (pts.length >= 2) {
      const line = d3.line().x(d => x2(d.meet)).y(d => y2(d.pace));
      g2.append('path').datum(pts).attr('fill', 'none').attr('stroke', cc(div)).attr('stroke-width', 2.4).attr('d', line);
    }
    pts.forEach(pt => {
      g2.append('circle')
        .attr('cx', x2(pt.meet)).attr('cy', y2(pt.pace)).attr('r', 5)
        .attr('fill', cc(div)).attr('stroke', P.surface).attr('stroke-width', 1.5)
        .on('mousemove', e => tip.show(`<b>${esc(div)}</b><br>${esc(pt.meet)}<br>Top-5 Avg Pace: <b>${fmtPaceSec(pt.pace * 60)}</b> (${pt.n} runners)`, e))
        .on('mouseleave', tip.hide);
    });
  });

  const ax2 = g2.append('g').attr('transform', `translate(0,${o2.ih})`).call(d3.axisBottom(x2).tickSize(3));
  VZ.axisStyle(ax2);
  ax2.selectAll('text').attr('transform', 'rotate(-25)').style('text-anchor', 'end').style('font-size', '10px');
  VZ.axisStyle(g2.append('g').call(d3.axisLeft(y2).ticks(6).tickFormat(d => fmtPaceSec(d * 60))));

  if (el('seasontrend-so')) {
    el('seasontrend-so').innerHTML = `Upward movement means faster mile pace. Every Aquinas division peaked in October: <b>HS Varsity</b> reached <b>6:04/M</b> at the TSTCA Championship Tune-Up; <b>MS Varsity (7–8)</b> improved from 6:50/M at Seelos #1 to <b>6:29/M</b> at Seelos #2.`;
  }
}

function renderSCurveAndLeverage() {
  if (!el('raceChart')) return;
  const races = RAW.races.filter(r => state.scope === 'ALL' ? true : r.division === state.scope)
    .filter(r => state.gend === 'ALL' || r.gender === state.gend);
  const sel = el('raceSelect');
  if (!races.length) {
    sel.innerHTML = '<option>No races match filter</option>';
    return;
  }
  if (!state.raceId || !races.some(r => r.race_id === state.raceId)) {
    const tstcaBoys = races.find(r => r.race_id.includes('tstca') && r.gender === 'Boys');
    state.raceId = (tstcaBoys || races[races.length - 1]).race_id;
  }

  sel.innerHTML = races.map(r => `
    <option value="${esc(r.race_id)}" ${r.race_id === state.raceId ? 'selected' : ''}>
      ${esc(r.date)} · ${esc(r.short_meet_name)} — ${esc(r.division)} ${esc(r.gender)} (${r.aquinas_finishers_count} Aquinas / ${r.total_finishers} total)
    </option>
  `).join('');

  const race = races.find(r => r.race_id === state.raceId) || races[0];
  if (el('scurveTitle')) {
    el('scurveTitle').textContent = `${race.short_meet_name} — ${race.division} ${race.gender} (Rank vs. Time)`;
  }

  const P = VZ.pal();
  const o = VZ.svg(el('raceChart'), 520, 320, { t: 16, r: 22, b: 38, l: 56 }), g = o.g;

  const x = d3.scaleLinear().domain([1, Math.max(race.total_finishers, 5)]).range([0, o.iw]);
  const minT = (d3.min(race.all_runners, d => d.time_seconds) || 600) / 60;
  const maxT = (d3.max(race.all_runners, d => d.time_seconds) || 1500) / 60;
  const y = d3.scaleLinear().domain([minT * 0.96, maxT * 1.03]).range([o.ih, 0]);

  x.ticks(6).forEach(tk => {
    g.append('line').attr('x1', x(tk)).attr('x2', x(tk)).attr('y1', 0).attr('y2', o.ih).attr('stroke', P.line).attr('stroke-opacity', 0.6);
  });
  y.ticks(7).forEach(tk => {
    g.append('line').attr('x1', 0).attr('x2', o.iw).attr('y1', y(tk)).attr('y2', y(tk)).attr('stroke', P.line).attr('stroke-opacity', 0.6);
  });

  VZ.axisStyle(g.append('g').attr('transform', `translate(0,${o.ih})`).call(d3.axisBottom(x).ticks(6).tickSize(3)));
  VZ.axisStyle(g.append('g').call(d3.axisLeft(y).ticks(7).tickFormat(d => fmtSec(d * 60).replace(/\.\d+$/, '')).tickSize(3)));

  g.append('text').attr('x', o.iw / 2).attr('y', o.ih + 32).attr('text-anchor', 'middle').attr('fill', P.fg2).style('font-size', '12px').text('Rank (1 = race winner)');
  g.append('text').attr('transform', 'rotate(-90)').attr('x', -o.ih / 2).attr('y', -44).attr('text-anchor', 'middle').attr('fill', P.fg2).style('font-size', '12px').text('Finish Time (mm:ss)');

  const col = cc(race.division === 'All Youth (1M)' ? 'MS Varsity (7-8)' : race.division);
  const calcGain15 = r => {
    const targetSec = r.time_seconds - 15;
    const newPlace = race.all_runners.filter(other => other.time_seconds < targetSec).length + 1;
    return Math.max(0, r.place - newPlace);
  };

  race.all_runners.filter(r => !r.is_aquinas).forEach(r => {
    g.append('circle')
      .attr('cx', x(r.place)).attr('cy', y(r.time_seconds / 60)).attr('r', 3.4)
      .attr('fill', 'none').attr('stroke', P.accent).attr('stroke-width', 1.2).attr('stroke-opacity', 0.55)
      .on('mousemove', e => tip.show(`<b>${esc(r.name)}</b> (Rank #${r.place})<br>${esc(r.team)} · Gr ${r.grade_or_age}<br>Time: <b>${esc(r.time)}</b> (${esc(r.pace)})`, e))
      .on('mouseleave', tip.hide);
  });

  race.all_runners.filter(r => r.is_aquinas).forEach((r, idx) => {
    const gain15 = calcGain15(r);
    const gg = g.append('g').attr('transform', `translate(${x(r.place)},${y(r.time_seconds / 60)})`).style('cursor', 'pointer')
      .on('mousemove', e => tip.show(`<b>${esc(r.name)}</b> (Rank #${r.place}, Aquinas #${idx + 1})<br>Time: <b>${esc(r.time)}</b> (${esc(r.pace)})<br>Shaving 15s passes <b>${gain15} runner${gain15 === 1 ? '' : 's'}</b>`, e))
      .on('mouseleave', tip.hide);
    gg.append('circle').attr('r', 6).attr('fill', '#e5c058').attr('stroke', '#991b1b').attr('stroke-width', 2);
    if (idx < 7) {
      gg.append('text').attr('y', -9).attr('text-anchor', 'middle').attr('fill', P.fg).style('font-size', '10px').style('font-weight', '600').text(r.name.split(' ').slice(-1)[0]);
    }
  });

  const topAq = race.aquinas_runners[0];
  if (el('race-so') && topAq) {
    el('race-so').innerHTML = `Open blue circles trace the full race S-curve; gold circles mark Aquinas finishers. Top Aquinas finisher: <b>${esc(topAq.name)}</b> (#${topAq.place}, ${esc(topAq.time)}).`;
  }

  // Right chart: 15-Second Passing Leverage Bar Chart (using JUST the runner's clean name!)
  const aqWithGain = race.aquinas_runners.map((r, i) => ({
    ...r,
    aqRank: i + 1,
    gain15: calcGain15(r),
    gain30: Math.max(0, r.place - (race.all_runners.filter(o => o.time_seconds < r.time_seconds - 30).length + 1))
  })).slice(0, 14);

  const o2 = VZ.svg(el('leverageChart'), 520, 320, { t: 12, r: 64, b: 28, l: 138 }), g2 = o2.g;
  const y2 = d3.scaleBand().domain(aqWithGain.map(d => d.name)).range([0, o2.ih]).padding(0.28);
  const maxG = Math.max(5, d3.max(aqWithGain, d => d.gain15) || 10);
  const x2 = d3.scaleLinear().domain([0, maxG * 1.18]).range([0, o2.iw]);

  aqWithGain.forEach(d => {
    g2.append('rect')
      .attr('y', y2(d.name)).attr('height', y2.bandwidth())
      .attr('width', Math.max(3, x2(d.gain15))).attr('fill', d.aqRank <= 5 ? col : P.muted).attr('rx', 3).attr('opacity', 0.85)
      .on('mousemove', e => tip.show(`<b>${esc(d.name)}</b> (Currently #${d.place}, ${esc(d.time)})<br><b>-15 seconds</b> moves up <b>+${d.gain15} places</b><br><b>-30 seconds</b> moves up <b>+${d.gain30} places</b>`, e))
      .on('mouseleave', tip.hide);

    g2.append('text')
      .attr('x', x2(d.gain15) + 5).attr('y', y2(d.name) + y2.bandwidth() / 2 + 4)
      .attr('fill', P.fg2).style('font-size', '11px').style('font-family', 'var(--font-mono)')
      .text(`+${d.gain15} pl`);
  });

  VZ.axisStyle(g2.append('g').call(d3.axisLeft(y2).tickSize(0)));
  VZ.axisStyle(g2.append('g').attr('transform', `translate(0,${o2.ih})`).call(d3.axisBottom(x2).ticks(5).tickFormat(d => '+' + d)));

  const top5TotalGain = d3.sum(aqWithGain.slice(0, 5), d => d.gain15);
  if (el('leverage-so')) {
    el('leverage-so').innerHTML = `If Aquinas Academy's top-5 scorers each ran <b>15 seconds faster</b> in this race, they would pass a combined <b>${top5TotalGain} opponent finishers</b>.`;
  }

  const rows = state.onlyAq ? race.aquinas_runners : race.all_runners;
  let aqRank = 0;
  if (el('raceTableBody')) {
    el('raceTableBody').innerHTML = rows.map(r => {
      if (r.is_aquinas) aqRank++;
      const back = r.place === 1 ? '0:00.00' : '+' + fmtSec(r.time_seconds - race.winner_time_seconds);
      const pct = (100 * (race.total_finishers - r.place) / Math.max(1, race.total_finishers - 1)).toFixed(1);
      const g15 = calcGain15(r);
      return `
        <tr class="${r.is_aquinas && !state.onlyAq ? 'hl' : ''}">
          <td class="num">#${r.place}</td>
          <td class="num">${r.is_aquinas ? '#' + aqRank : '—'}</td>
          <td><b>${esc(r.name)}</b></td>
          <td>${esc(r.team)}</td>
          <td class="num">${r.grade_or_age}</td>
          <td class="num">${r.bib}</td>
          <td class="num"><b>${esc(r.time)}</b></td>
          <td class="num">${esc(r.pace)}</td>
          <td class="num" style="color:var(--muted)">${back}</td>
          <td class="num">${pct}%</td>
          <td class="num up">${g15 > 0 ? '+' + g15 + ' pl' : '—'}</td>
        </tr>
      `;
    }).join('');
  }
}

function renderPackLadderAndTeamCharts() {
  if (!el('ladderChart')) return;
  const P = VZ.pal();
  const races = RAW.races.filter(r => state.scope === 'ALL' ? true : r.division === state.scope)
    .filter(r => state.gend === 'ALL' || r.gender === state.gend)
    .filter(r => !r.is_1m && r.aquinas_runners.length >= 5);

  const labelOf = d => `${d.meet_short} · ${d.division.replace(' (9-12)', '').replace(' (7-8)', '').replace(' (5-6)', '').replace(' (K-4)', '').replace('Elementary ', '').replace('Developmental', 'Dev')} ${d.gender[0]}`;

  const L = races.slice().sort((a, b) => a.date.localeCompare(b.date) || a.division.localeCompare(b.division));
  const hLad = Math.max(260, L.length * 24 + 40);
  const oL = VZ.svg(el('ladderChart'), 900, hLad, { t: 12, r: 40, b: 32, l: 185 }), gL = oL.g;
  const yL = d3.scaleBand().domain(L.map(labelOf)).range([0, oL.ih]).padding(0.34);

  const allTop7Paces = L.flatMap(r => r.aquinas_runners.slice(0, 7).map(x => (x.pace_seconds || parsePaceSec(x.pace)) / 60)).filter(Boolean);
  const minP = Math.max(4.8, (d3.min(allTop7Paces) || 5.3) - 0.25);
  const maxP = Math.min(11.5, (d3.max(allTop7Paces) || 9.5) + 0.25);
  const xL = d3.scaleLinear().domain([minP, maxP]).range([0, oL.iw]);

  xL.ticks(7).forEach(tk => {
    gL.append('line').attr('x1', xL(tk)).attr('x2', xL(tk)).attr('y1', 0).attr('y2', oL.ih).attr('stroke', P.line).attr('stroke-dasharray', '2 2');
  });

  L.forEach(r => {
    const lbl = labelOf(r);
    const cy = yL(lbl) + yL.bandwidth() / 2;
    const top7 = r.aquinas_runners.slice(0, 7).map((x, idx) => ({
      ...x,
      rank: idx + 1,
      pMin: (x.pace_seconds || parsePaceSec(x.pace)) / 60
    })).filter(x => x.pMin);

    if (top7.length >= 5) {
      const p1 = top7[0].pMin, p5 = top7[4].pMin, pLast = top7[top7.length - 1].pMin;
      const col = cc(r.division);
      if (top7.length > 5) {
        gL.append('line').attr('x1', xL(p5)).attr('x2', xL(pLast)).attr('y1', cy).attr('y2', cy).attr('stroke', col).attr('stroke-width', 1.6).attr('stroke-dasharray', '3 2');
      }
      gL.append('rect')
        .attr('x', xL(p1)).attr('y', yL(lbl))
        .attr('width', Math.max(4, xL(p5) - xL(p1))).attr('height', yL.bandwidth())
        .attr('rx', yL.bandwidth() / 2).attr('fill', col).attr('fill-opacity', 0.28).attr('stroke', col).attr('stroke-width', 1.5)
        .on('mousemove', e => tip.show(`<b>${esc(r.short_meet_name)} · ${esc(r.division)} ${esc(r.gender)}</b><br>1–5 Spread: <b>${fmtSec(r.aquinas_1_to_5_spread_seconds)}</b><br>#1: ${esc(top7[0].name)} (${top7[0].pace})<br>#5: ${esc(top7[4].name)} (${top7[4].pace})`, e))
        .on('mouseleave', tip.hide);

      top7.forEach(runner => {
        gL.append('circle')
          .attr('cx', xL(runner.pMin)).attr('cy', cy).attr('r', runner.rank <= 5 ? 4.2 : 3.2)
          .attr('fill', runner.rank <= 5 ? col : P.surface).attr('stroke', col).attr('stroke-width', 1.5)
          .on('mousemove', e => tip.show(`<b>${esc(runner.name)}</b> (Aquinas #${runner.rank})<br>${esc(r.short_meet_name)}<br>Time: <b>${esc(runner.time)}</b> (${esc(runner.pace)}) · Place #${runner.place}`, e))
          .on('mouseleave', tip.hide);
      });
    }
  });

  VZ.axisStyle(gL.append('g').call(d3.axisLeft(yL).tickSize(0)));
  VZ.axisStyle(gL.append('g').attr('transform', `translate(0,${oL.ih})`).call(d3.axisBottom(xL).ticks(7).tickFormat(d => fmtPaceSec(d * 60))));

  const D = races.slice().sort((a, b) => a.aquinas_top5_avg_seconds - b.aquinas_top5_avg_seconds).slice(0, 16);
  const h1 = Math.max(260, D.length * 22 + 34);
  const o1 = VZ.svg(el('size'), 520, h1, { t: 6, r: 58, b: 24, l: 175 }), g1 = o1.g;
  const y1 = d3.scaleBand().domain(D.map(labelOf)).range([0, o1.ih]).padding(0.28);
  const x1 = d3.scaleLinear().domain([0, d3.max(D, d => d.aquinas_top5_avg_seconds / 60) || 25]).nice().range([0, o1.iw]);

  D.forEach(d => {
    const lbl = labelOf(d);
    const mins = d.aquinas_top5_avg_seconds / 60;
    g1.append('rect')
      .attr('y', y1(lbl)).attr('height', y1.bandwidth())
      .attr('width', x1(mins)).attr('fill', cc(d.division)).attr('rx', 3).attr('opacity', 0.85)
      .on('mousemove', e => tip.show(`<b>${esc(d.short_meet_name)}</b><br>${esc(d.division)} ${esc(d.gender)}<br>Top-5 Avg: <b>${fmtSec(d.aquinas_top5_avg_seconds)}</b>`, e))
      .on('mouseleave', tip.hide);
    g1.append('text')
      .attr('x', x1(mins) + 5).attr('y', y1(lbl) + y1.bandwidth() / 2 + 4)
      .attr('fill', P.fg2).style('font-size', '11px').style('font-family', 'var(--font-mono)')
      .text(fmtSec(d.aquinas_top5_avg_seconds));
  });
  VZ.axisStyle(g1.append('g').call(d3.axisLeft(y1).tickSize(0)));
  VZ.axisStyle(g1.append('g').attr('transform', `translate(0,${o1.ih})`).call(d3.axisBottom(x1).ticks(5).tickFormat(d => d + 'm')));

  const S = races.filter(r => r.aquinas_1_to_5_spread_seconds != null).sort((a, b) => a.aquinas_1_to_5_spread_seconds - b.aquinas_1_to_5_spread_seconds).slice(0, 16);
  const h2 = Math.max(260, S.length * 22 + 34);
  const o2 = VZ.svg(el('chg'), 520, h2, { t: 6, r: 58, b: 24, l: 175 }), g2 = o2.g;
  const y2 = d3.scaleBand().domain(S.map(labelOf)).range([0, o2.ih]).padding(0.28);
  const x2 = d3.scaleLinear().domain([0, d3.max(S, d => d.aquinas_1_to_5_spread_seconds) || 180]).nice().range([0, o2.iw]);

  S.forEach(d => {
    const lbl = labelOf(d);
    const sp = d.aquinas_1_to_5_spread_seconds;
    g2.append('rect')
      .attr('y', y2(lbl)).attr('height', y2.bandwidth())
      .attr('width', x2(sp)).attr('fill', cc(d.division)).attr('rx', 3).attr('opacity', 0.85)
      .on('mousemove', e => tip.show(`<b>${esc(d.short_meet_name)}</b><br>${esc(d.division)} ${esc(d.gender)}<br>1-to-5 Pack Spread: <b>${fmtSec(sp)}</b> (${sp.toFixed(1)}s)<br>#1: ${esc(d.aquinas_runners[0].name)} (${d.aquinas_runners[0].time})<br>#5: ${esc(d.aquinas_runners[4].name)} (${d.aquinas_runners[4].time})`, e))
      .on('mouseleave', tip.hide);
    g2.append('text')
      .attr('x', x2(sp) + 5).attr('y', y2(lbl) + y2.bandwidth() / 2 + 4)
      .attr('fill', P.fg2).style('font-size', '11px').style('font-family', 'var(--font-mono)')
      .text(sp.toFixed(1) + 's');
  });
  VZ.axisStyle(g2.append('g').call(d3.axisLeft(y2).tickSize(0)));
  VZ.axisStyle(g2.append('g').attr('transform', `translate(0,${o2.ih})`).call(d3.axisBottom(x2).ticks(5).tickFormat(d => d + 's')));
}

function renderMap() {
  if (!el('map')) return;
  const P = VZ.pal();
  const o = VZ.svg(el('map'), 900, 450, { t: 18, r: 36, b: 44, l: 64 }), g = o.g;
  const pool = ATHLETES.filter(matchFilter).filter(a => !state.offCats.has(a.cat) && a.pace_min >= 4.5 && a.pace_min <= 13.5);

  const x = d3.scaleLinear().domain([0, 102]).range([0, o.iw]);
  const yMin = d3.min(pool, d => d.pace_min) || 5.0;
  const yMax = d3.max(pool, d => d.pace_min) || 11.0;
  const y = d3.scaleLinear().domain([Math.min(12.0, yMax + 0.4), Math.max(4.8, yMin - 0.35)]).range([o.ih, 0]);

  g.append('line').attr('x1', x(50)).attr('x2', x(50)).attr('y1', 0).attr('y2', o.ih).attr('stroke', P.line);
  const midPace = (y.domain()[0] + y.domain()[1]) / 2;
  g.append('line').attr('x1', 0).attr('x2', o.iw).attr('y1', y(midPace)).attr('y2', y(midPace)).attr('stroke', P.line);

  [
    ['Fast pace, deep field', 8, 14, 'start'],
    ['Front-pack & fast pace', o.iw - 8, 14, 'end'],
    ['Developing pace & pack', 8, o.ih - 8, 'start'],
    ['High placement, tactical course', o.iw - 8, o.ih - 8, 'end']
  ].forEach(([t, a, b, an]) =>
    g.append('text').attr('x', a).attr('y', b).attr('text-anchor', an).attr('fill', P.muted).style('font-size', '11.5px').style('letter-spacing', '.03em').text(t.toUpperCase())
  );

  VZ.axisStyle(g.append('g').attr('transform', `translate(0,${o.ih})`).call(d3.axisBottom(x).ticks(6).tickFormat(d => d + '%').tickSize(3)));
  VZ.axisStyle(g.append('g').call(d3.axisLeft(y).ticks(6).tickFormat(d => fmtPaceSec(d * 60)).tickSize(3)));

  g.append('text').attr('x', o.iw / 2).attr('y', o.ih + 36).attr('text-anchor', 'middle').attr('fill', P.fg2).style('font-size', '12px').text('Average field percentile across 2026 races (100% = top of field)');
  g.append('text').attr('transform', 'rotate(-90)').attr('x', -o.ih / 2).attr('y', -48).attr('text-anchor', 'middle').attr('fill', P.fg2).style('font-size', '12px').text('Personal-best XC pace (min/mile, faster at top)');

  const rs = d3.scaleSqrt().domain([1, 7]).range([5.5, 14]);
  const selAth = getSelectedAthlete();
  const topLabelSet = new Set(
    pool.slice().sort((a, b) => (b.avg_percentile * 1.2 + b.races_count * 5) - (a.avg_percentile * 1.2 + a.races_count * 5)).slice(0, 18).map(d => d.id)
  );
  topLabelSet.add(selAth.id);

  pool.slice().sort((a, b) => b.races_count - a.races_count).forEach(a => {
    const px = x(a.avg_percentile), py = y(a.pace_min), r = rs(a.races_count);
    const ci = Math.max(0, CATS.indexOf(a.cat)), col = cc(a.cat);
    const gg = g.append('g').attr('transform', `translate(${px},${py})`).style('cursor', 'pointer')
      .on('click', () => { state.selAth = a.id; renderRunnersTab(); el('prof').scrollIntoView({ block: 'nearest', behavior: 'smooth' }); })
      .on('mousemove', e => tip.show(`<b>${esc(a.name)}</b><br>${esc(a.division)} · ${esc(a.gender)} Gr ${a.grade_or_age}<br>PR: <b>${esc(a.pr_time)}</b> (${esc(a.pr_pace)}) at ${esc(a.pr_meet)}<br>Avg field pct: <b>${a.avg_percentile}%</b> · ${a.races_count} races`, e))
      .on('mouseleave', tip.hide);

    const sz = Math.PI * r * r;
    gg.append('path')
      .attr('d', d3.symbol().type(SYM[ci % SYM.length]).size(sz)())
      .attr('fill', col)
      .attr('fill-opacity', a.races_count >= 2 ? 0.78 : 0.48)
      .attr('stroke', P.surface)
      .attr('stroke-width', 1.5);

    if (a.id === selAth.id) {
      gg.append('path')
        .attr('d', d3.symbol().type(SYM[ci % SYM.length]).size(sz * 1.85 + 150)())
        .attr('fill', 'none').attr('stroke', '#e5c058').attr('stroke-width', 2.2);
    }
    if (topLabelSet.has(a.id)) {
      gg.append('text')
        .attr('y', r + 11)
        .attr('text-anchor', 'middle')
        .attr('fill', a.id === selAth.id ? P.fg : P.fg2)
        .style('font-size', '10.5px')
        .style('font-weight', a.id === selAth.id ? '600' : '400')
        .text(a.name);
    }
  });

  if (el('leg')) {
    el('leg').innerHTML = CATS.map((c, i) =>
      `<button data-c="${c}" aria-pressed="${!state.offCats.has(c)}"><svg viewBox="-8 -8 16 16"><path d="${d3.symbol().type(SYM[i % SYM.length]).size(120)()}" fill="${cc(c)}"/></svg>${c} (${ATHLETES.filter(a => a.cat === c && matchFilter(a)).length})</button>`
    ).join('') + '<span>Click a division to hide or show it.</span>';

    el('leg').onclick = e => {
      const b = e.target.closest('[data-c]');
      if (b) {
        state.offCats.has(b.dataset.c) ? state.offCats.delete(b.dataset.c) : state.offCats.add(b.dataset.c);
        renderMap();
      }
    };
  }
}

function renderMoves() {
  if (!el('movesList')) return;
  const milestones = [
    ['Aug 25, 2026', 'Aquinas opens the Diocesan season at Seelos Pine Park with 1st-place team wins in Developmental Girls (47 pts) and MS Varsity Girls (15 pts), plus 2nd in MS Varsity Boys and Dev Boys.', 'Seelos #1'],
    ['Aug 29, 2026', 'At the 14-team Blessed Trinity (BTA) Invitational at Hartwood Acres, Aquinas Developmental Girls take 1st of 12 teams (50 pts) and Developmental Boys place 2nd of 14 teams.', 'BTA Invite'],
    ['Sep 4, 2026', 'St. Kilian Invitational in Mars: Developmental Girls win their third straight team title (25 pts) while JV Boys and Dev Boys both finish 2nd.', 'St. Kilian'],
    ['Sep 10, 2026', 'St. Al Twilight Harvest Home 1 Mile in Allison Park: 52 Aquinas K–8 runners test their flat-mile speed, led by 8th-graders John Austin (5:18.93) and Zach Guillen (5:45.44) for the boys and Rosa Yuo (6:27.93) and Kat Barnett (6:28.34) for the girls.', 'Harvest Home 1M'],
    ['Sep 12, 2026', '24th Annual Red, White & Blue Classic at White Oak Park (Class 1A): Aquinas High School Boys place 3rd of 13 teams (74 pts) behind freshman Isaac Vangura (10th, 17:14.2), Max Predis (11th, 17:28.8), and Andrew Deem (13th, 17:46.7). HS Girls place 6th (164 pts) led by freshman Alexandra Robinson (27th, 23:38.8).', 'RWB Classic'],
    ['Sep 12, 2026', 'Oakland Catholic XC Invitational at Youthtowne: Aquinas MS Varsity Girls win 1st place team (39 pts), MS Varsity Boys take 2nd (48 pts, led by John Austin #4 in 11:02.20), and Elementary JV Girls place 2nd (55 pts).', 'Oakland Catholic'],
    ['Sep 18, 2026', 'Youthtowne Clash: Aquinas sweeps 1st place in both 3rd–4th Grade Boys (1st of 10 teams) and Girls (1st of 6), takes 2nd of 9 in Jr High Boys (11:49 avg), and races High School Varsity 5K led by Isaac Vangura (11th, 17:15.45) and Andrew Deem (25th, 17:49.28).', 'Youthtowne Clash'],
    ['Sep 24, 2026', 'Home course dominance at the Aquinas & Holy Cross Meet in Allison Park: Aquinas wins 5 of 6 team divisions (MS Varsity Boys & Girls, JV Boys, and Developmental Boys & Girls).', 'Aquinas Home'],
    ['Sep 26, 2026', '20th PIAA Foundation XC Invitational in Hershey, PA (State Championship Course): Aquinas High School Boys finish 6th in Pennsylvania Class 1A (215 pts) led by Isaac Vangura (15th, 17:16.5), Andrew Deem (30th, 17:57.1), and Roman Spagnolo (44th, 18:28.9). Alexandra Robinson places 42nd (22:02.4) in Class 1A Girls.', 'PIAA Foundation'],
    ['Sep 29, 2026', 'WPIAL Class A Tri-Meet at Avonworth: Isaac Vangura (1st overall, 19:02.10) and Andrew Deem (2nd, 19:02.19) go 1–2 as Aquinas HS Boys defeat both Avonworth (22–34) and Neighborhood Academy (18–43). HS Girls defeat Neighborhood Academy (15–50).', 'Avonworth Tri'],
    ['Oct 2, 2026', 'North Area Diocesan XC Championships at North Park: Aquinas captures four North Area Championship banners — MS Varsity Boys (1st, 35 pts), Elementary JV Boys (1st, 43 pts), and Developmental Boys & Girls (both 1st of 8 teams).', 'North Area Champs'],
    ['Oct 6, 2026', 'WPIAL A/AA Section 4 XC Championships at Chatham University Eden Hall: Freshman Isaac Vangura runs 16:54.07 (7th overall against 1A/2A competition) to break the 5-year-old Aquinas Academy 5K school record (17:05) and become the first Crusader under 17 minutes.', 'WPIAL Sec 4'],
    ['Oct 6, 2026', 'Seelos "Second Chance" Meet: MS Varsity Boys score 27 pts (places 2, 4, 6, 7, 8 led by John Austin 11:04.26 and Zach Guillen 11:17.78) to win the team title; MS Varsity Girls, JV Boys, and Dev Girls also take 1st.', 'Seelos #2'],
    ['Oct 10, 2026', 'Run for the Pumpkins XC Invitational at Youthtowne: Aquinas Developmental Girls capture 1st place team (36 pts, led by Cora Donahue #4 in 10:33.34 and Emily Edwards #5 in 10:42.54) while Developmental Boys place 4th of 10 teams.', 'Pumpkins XC'],
    ['Oct 17, 2026', 'Pittsburgh Diocesan Cross Country Championships at Youthtowne: Aquinas wins three Diocesan Team Championships — Elementary JV Boys (1st, 37 pts, led by Noah Malone #2 in 10:55.62), Developmental Girls 3–4 (1st, 59 pts, led by Cora Donahue #3 in 11:07.56, and 1st in Combined Dev Girls), and Developmental Boys K–2 (1st, 45 pts, led by Individual Diocesan Champion Linus Gruber #1 in 10:26.48) — plus Diocesan Runner-Up trophies in both MS Varsity Girls (2nd, 33 pts, Kat Barnett #6) and MS Varsity Boys (2nd, 58 pts, John Austin #4 in 10:10.66).', 'Diocesan Champ'],
    ['Oct 22, 2026', 'TSTCA Championship Tune-Up at White Oak Park (Class A): Freshman Isaac Vangura lowers his own school record to 16:41.76 (3rd overall, 5:23/M), Andrew Deem runs 17:24.98 (8th), Roman Spagnolo runs 17:35.22 (10th), and Giancarlo Josephs runs 18:31.26 (19th). Aquinas Boys tie Neshannock at 59 points (2nd of 10 teams, 1 point behind South Side\'s 58, with the fastest top-5 total time in Class A at 1:30:18.09). Aquinas Girls place 5th of 10 teams (118 pts).', 'TSTCA Class A']
  ];
  el('movesList').innerHTML = milestones.map(m =>
    `<div class="tl2"><div class="w">${esc(m[0])}</div><div>${esc(m[1])} <span class="chip">${esc(m[2])}</span></div></div>`
  ).join('');
}

function renderStandings() {
  if (!el('standingsBody')) return;
  const list = RAW.team_standings.filter(matchFilter);
  el('standingsBody').innerHTML = list.map(s => {
    const pos = s.aquinas_position;
    const posCls = pos === 1 ? 'up' : (typeof pos === 'number' && pos <= 3 ? 'warn' : '');
    const posTxt = typeof pos === 'number' ? `#${pos} / ${s.scored_teams_count}` : (pos || 'Inc.');
    const opps = s.teams.filter(t => typeof t.position === 'number').slice(0, 4).map(t =>
      t.is_aquinas ? `<b>${t.position}. ${esc(t.team)} (${t.points})</b>` : `${t.position}. ${esc(t.team)} (${t.points})`
    ).join(' · ');
    const sub = s.matchup ? ` <span class="chip">${esc(s.matchup)}</span>` : '';
    return `
      <tr>
        <td class="mono">${esc(s.date)}</td>
        <td><b>${esc(s.short_meet_name)}</b>${sub}</td>
        <td>${esc(s.division)}</td>
        <td>${esc(s.gender)}</td>
        <td class="num ${posCls}"><b>${posTxt}</b></td>
        <td class="num">${s.aquinas_points != null ? s.aquinas_points : '—'}</td>
        <td class="num">${esc(s.aquinas_total_time || '—')}</td>
        <td class="num">${esc(s.aquinas_avg_time || '—')}</td>
        <td style="color:var(--fg2)">${opps || 'Less than 5 finishers'}</td>
        <td><a href="${esc(s.source_url)}" target="_blank" rel="noopener">HTML</a></td>
      </tr>
    `;
  }).join('');
}

function switchTab(tabId, pushUrl = true) {
  state.tab = tabId;
  document.querySelectorAll('.sitenav a[data-tab]').forEach(a => {
    if (a.dataset.tab === tabId) a.setAttribute('aria-current', 'page');
    else a.removeAttribute('aria-current');
  });
  document.querySelectorAll('.tab-pane').forEach(p => {
    p.classList.toggle('active', p.id === `tab-${tabId}`);
  });

  // Show/hide global filter bar (Schools tab has its own dedicated division/gender heatmap selector)
  if (el('globalFilters')) {
    el('globalFilters').style.display = (tabId === 'schools') ? 'none' : 'flex';
  }

  if (pushUrl) {
    const fileMap = { overall: 'index.html', schools: 'schools.html', team: 'team.html', runners: 'runners.html' };
    try { history.pushState({ tab: tabId }, '', fileMap[tabId] || 'index.html'); } catch (e) {}
  }
  window.scrollTo({ top: 0, behavior: 'instant' });
  renderActiveTab();
}

function renderActiveTab() {
  if (state.tab === 'overall') renderOverallTab();
  else if (state.tab === 'schools') renderSchoolsTab();
  else if (state.tab === 'team') renderTeamTab();
  else if (state.tab === 'runners') renderRunnersTab();
}

function initEvents() {
  // Header ribbon tab switching
  document.querySelectorAll('.sitenav a[data-tab]').forEach(a => {
    a.addEventListener('click', e => {
      e.preventDefault();
      switchTab(a.dataset.tab, true);
    });
  });

  window.addEventListener('popstate', e => {
    if (e.state && e.state.tab) switchTab(e.state.tab, false);
  });

  // Global division & gender filters
  if (el('globalFilters')) {
    el('globalFilters').addEventListener('click', e => {
      const sc = e.target.closest('[data-scope]');
      if (sc) {
        el('globalFilters').querySelectorAll('[data-scope]').forEach(b => b.setAttribute('aria-pressed', 'false'));
        sc.setAttribute('aria-pressed', 'true');
        state.scope = sc.dataset.scope;
        renderActiveTab();
      }
      const gd = e.target.closest('[data-gend]');
      if (gd) {
        el('globalFilters').querySelectorAll('[data-gend]').forEach(b => b.setAttribute('aria-pressed', 'false'));
        gd.setAttribute('aria-pressed', 'true');
        state.gend = gd.dataset.gend;
        renderActiveTab();
      }
    });
  }

  // Calendar click & meet pill click
  document.addEventListener('click', e => {
    const calDay = e.target.closest('[data-meet]');
    if (calDay) {
      const mId = calDay.dataset.meet;
      state.calMeetId = (state.calMeetId === mId) ? 'ALL' : mId;
      renderSeasonCalendar();
      renderCalendarMeetTiles();
    }
    const cPill = e.target.closest('[data-cmeet]');
    if (cPill) {
      state.calMeetId = cPill.dataset.cmeet;
      renderSeasonCalendar();
      renderCalendarMeetTiles();
    }
    const rMode = e.target.closest('[data-rmode]');
    if (rMode) {
      document.querySelectorAll('[data-rmode]').forEach(b => b.setAttribute('aria-pressed', 'false'));
      rMode.setAttribute('aria-pressed', 'true');
      state.ridgeMode = rMode.dataset.rmode;
      renderOverallRidgeline();
    }
    const trMode = e.target.closest('[data-trmode]');
    if (trMode) {
      document.querySelectorAll('[data-trmode]').forEach(b => b.setAttribute('aria-pressed', 'false'));
      trMode.setAttribute('aria-pressed', 'true');
      state.teamRidgeMode = trMode.dataset.trmode;
      renderTeamTab();
    }
    const sDiv = e.target.closest('[data-sdiv]');
    if (sDiv) {
      document.querySelectorAll('[data-sdiv]').forEach(b => b.setAttribute('aria-pressed', 'false'));
      sDiv.setAttribute('aria-pressed', 'true');
      state.schoolDiv = sDiv.dataset.sdiv;
      state.selectedSchoolCell = null;
      renderSchoolsTab();
    }
    const sGend = e.target.closest('[data-sgend]');
    if (sGend) {
      document.querySelectorAll('[data-sgend]').forEach(b => b.setAttribute('aria-pressed', 'false'));
      sGend.setAttribute('aria-pressed', 'true');
      state.schoolGend = sGend.dataset.sgend;
      state.selectedSchoolCell = null;
      renderSchoolsTab();
    }
  });

  if (el('compSchoolSelect')) {
    el('compSchoolSelect').addEventListener('change', e => {
      if (state.selectedSchoolCell) {
        state.selectedSchoolCell.team = e.target.value;
        renderSchoolsTab();
      }
    });
  }

  if (el('runnerSelectTop')) {
    el('runnerSelectTop').addEventListener('change', e => {
      state.selAth = e.target.value;
      renderRunnersTab();
    });
  }

  document.querySelectorAll('[data-bmode]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-bmode]').forEach(b => b.setAttribute('aria-pressed', 'false'));
      btn.setAttribute('aria-pressed', 'true');
      state.bucketMode = btn.dataset.bmode;
      renderWhereDoYouFall();
    });
  });

  document.querySelectorAll('[data-bpop]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-bpop]').forEach(b => b.setAttribute('aria-pressed', 'false'));
      btn.setAttribute('aria-pressed', 'true');
      state.bucketPop = btn.dataset.bpop;
      renderWhereDoYouFall();
    });
  });

  if (el('runnerSearch')) {
    el('runnerSearch').addEventListener('input', e => {
      state.search = e.target.value.trim().toLowerCase();
      // If searching and matches exist, auto-select top match
      const matches = ATHLETES.filter(matchFilter).filter(a => a.name.toLowerCase().includes(state.search));
      if (state.search && matches.length) {
        state.selAth = matches[0].id;
      }
      renderRunnersTab();
    });
  }

  document.querySelectorAll('[data-limit]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-limit]').forEach(b => b.setAttribute('aria-pressed', 'false'));
      btn.setAttribute('aria-pressed', 'true');
      state.cardLimit = parseInt(btn.dataset.limit, 10);
      renderCardsAndProf();
    });
  });

  if (el('raceSelect')) {
    el('raceSelect').addEventListener('change', e => {
      state.raceId = e.target.value;
      renderSCurveAndLeverage();
    });
  }

  if (el('onlyAqBtn')) {
    el('onlyAqBtn').addEventListener('click', () => {
      state.onlyAq = !state.onlyAq;
      el('onlyAqBtn').setAttribute('aria-pressed', String(state.onlyAq));
      el('onlyAqBtn').textContent = state.onlyAq ? 'Table below: Aquinas only' : 'Table below: Full race field';
      renderSCurveAndLeverage();
    });
  }

  const modes = ['auto', 'dark', 'light'];
  let mIdx = 0;
  if (el('themeBtn')) {
    el('themeBtn').addEventListener('click', () => {
      mIdx = (mIdx + 1) % modes.length;
      const m = modes[mIdx];
      if (m === 'auto') document.documentElement.removeAttribute('data-theme');
      else document.documentElement.setAttribute('data-theme', m);
      el('themeBtn').textContent = `Theme: ${m}`;
      renderActiveTab();
    });
  }

  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => renderActiveTab());
}

initEvents();
switchTab(state.tab, false);
if (el('foot')) {
  el('foot').innerHTML = 'Sources: Official 2026 timing results across 16 meets from Miles of Smiles Timing Services (<a href="https://www.smileymiles.com/2026%20Results.html" target="_blank" rel="noopener">smileymiles.com</a>), Wolf Creek Race Management &amp; RunSignup (<a href="https://runsignup.com/Race/Results/193936" target="_blank" rel="noopener">Diocesan Championship</a>, <a href="https://runsignup.com/Race/Results/191674" target="_blank" rel="noopener">Oakland Catholic Invite</a>, <a href="https://runsignup.com/Race/Results/193469" target="_blank" rel="noopener">Run for the Pumpkins</a>), Runner\'s High (<a href="https://www.runhigh.com/2026RESULTS/R092626DE.html" target="_blank" rel="noopener">PIAA Foundation Invite</a>), and PA MileSplit (<a href="https://pa.milesplit.com" target="_blank" rel="noopener">Red, White &amp; Blue Classic &amp; WPIAL Section 4 Championships</a>).';
}
