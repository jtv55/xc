/* ==========================================================================
   2026 CCCNYC & CYO Nationals — Interactive Actuals vs. Predictions Engine
   Renders Aquinas Academy, Diego & Marcela Victor, Western PA Hill-Strength,
   2,424-Runner Scatter, All-American Calibration, and 8/8 CYO Team Audit
   ========================================================================== */
(function () {
  if (document.body.dataset.page !== "results" || !window.CCCNYC_ACTUALS) return;

  const ACT = window.CCCNYC_ACTUALS;
  const SUM = ACT.summary;
  const ATHS = ACT.athletes;
  const EVENTS = ACT.events;
  const TEAMS = ACT.teams;
  const LOGS = ACT.season_logs;

  const AQ = ATHS.filter((a) => a.dop && a.sch === "Aquinas Academy").sort((a, b) => a.ev - b.ev || a.apl - b.apl);
  const DOP = ATHS.filter((a) => a.dop);
  const OTHER = ATHS.filter((a) => !a.dop);
  const diego = AQ.find((a) => a.n === "Diego Victor");
  const marcela = AQ.find((a) => a.n === "Marcela Victor");

  const tip = document.getElementById("d3Tooltip");
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmtClub = (tm, st) => {
    if (!tm || tm === "Unattached" || !st || st === "USA") return tm || "";
    const tag = st === "INTL" ? "BM" : st;
    return tm.endsWith(`(${tag})`) ? tm : `${tm} (${tag})`;
  };
  const fmtTime = (sec) => {
    const m = Math.floor(sec / 60);
    const r = sec - m * 60;
    return `${m}:${r < 10 ? "0" : ""}${r.toFixed(1)}`;
  };
  const fmtPace = (sec) => {
    let m = Math.floor(sec / 60);
    let s = Math.round(sec - m * 60);
    if (s === 60) { m += 1; s = 0; }
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };
  const paceSec = (t, distM) => t / (distM / 1609.344);

  function showTip(evt, html) {
    if (!tip) return;
    tip.innerHTML = html;
    tip.classList.add("show");
    const pad = 14;
    let x = evt.clientX + pad;
    let y = evt.clientY + pad;
    const rect = tip.getBoundingClientRect();
    if (x + rect.width > window.innerWidth - 10) x = evt.clientX - rect.width - pad;
    if (y + rect.height > window.innerHeight - 10) y = evt.clientY - rect.height - pad;
    tip.style.left = `${Math.max(8, x)}px`;
    tip.style.top = `${Math.max(8, y)}px`;
  }
  function hideTip() { if (tip) tip.classList.remove("show"); }

  // 1. KPI Strip
  document.getElementById("resKpis").innerHTML = `
    <div class="kpi kpi-dop">
      <div class="v">11 / 11</div>
      <div class="l">Aquinas Finishers</div>
      <div class="s">3 National All-Americans · 9/11 beat forecast</div>
    </div>
    <div class="kpi kpi-up">
      <div class="v">-24.0s</div>
      <div class="l">Aquinas Median Beat</div>
      <div class="s">vs. +8.6s Rest of Nation (32.6s WPA swing!)</div>
    </div>
    <div class="kpi kpi-cyo">
      <div class="v">8 / 8</div>
      <div class="l">CYO Champs Called</div>
      <div class="s">100% exact CYO team champion accuracy</div>
    </div>
    <div class="kpi kpi-gold">
      <div class="v">15 AAs</div>
      <div class="l">Pittsburgh CYO All-Americans</div>
      <div class="s">7/7 (&ge;50% locks) + 8 breakouts (vs 10.3 exp)</div>
    </div>
    <div class="kpi kpi-accent">
      <div class="v">r = 0.938</div>
      <div class="l">2,424-Runner Correlation</div>
      <div class="s">99.3% matched · Tier 1+ MAPE 4.23%</div>
    </div>
    <div class="kpi kpi-up">
      <div class="v">0.0877</div>
      <div class="l">All-American Brier Score</div>
      <div class="s">9 / 10 Pgh CYO squads won CYO Podiums!</div>
    </div>
  `;

  // 2. Diego & Marcela Interactive Season Pace Curves
  function renderSeasonCurve(elId, ath, colorMain, prLabel) {
    const box = document.getElementById(elId);
    if (!box || !ath) return;
    box.innerHTML = "";
    const races = (LOGS[ath.id] || []).map((r) => ({
      date: r.date.slice(5),
      meet: r.meet.replace("XC Meet ", "").replace("Dev Boys and Girls", "").replace("Dev Girls", "").replace("Dev Boys", "").replace("Pittsburgh Diocesan XC Championship", "Diocesan Champ").replace("Oakland Catholic XC Invitational", "Oakland Cath. 3K").replace("North Area XC Championships", "North Area").replace("Run for the Pumpkins XC", "Pumpkins XC").trim(),
      dist: r.dist_m,
      timeStr: r.time_str,
      pace: paceSec(r.time_sec, r.dist_m),
      pl: `#${r.place}/${r.field_size}`,
      isNat: false,
    }));
    races.push({
      date: "11-21",
      meet: "CCCNYC Nationals (Cedarville)",
      dist: ath.d,
      timeStr: ath.ats,
      pace: paceSec(ath.at, ath.d),
      pl: `Ov #${ath.apl}/${ath.af} · Age #${ath.aag}/${ath.aagf}`,
      isNat: true,
    });

    const W = Math.max(360, box.clientWidth || 480);
    const H = 235;
    const m = { t: 26, r: 62, b: 44, l: 46 };
    const predP = paceSec(ath.pt, ath.d);
    const p10P = paceSec(ath.p10, ath.d);
    const p90P = paceSec(ath.p90, ath.d);
    const allP = races.map((r) => r.pace).concat([predP, p10P, p90P]);
    const yMin = Math.floor((d3.min(allP) - 10) / 15) * 15;
    const yMax = Math.ceil((d3.max(allP) + 10) / 15) * 15;

    const svg = d3.select(box).append("svg").attr("viewBox", `0 0 ${W} ${H}`).style("width", "100%");
    const x = d3.scaleLinear().domain([0, races.length - 1]).range([m.l, W - m.r]);
    // Faster pace = HIGHER on chart
    const y = d3.scaleLinear().domain([yMin, yMax]).range([m.t, H - m.b]);

    // Grid
    const step = (yMax - yMin) <= 105 ? 15 : 30;
    for (let v = yMin; v <= yMax + 0.1; v += step) {
      svg.append("line").attr("x1", m.l).attr("x2", W - m.r).attr("y1", y(v)).attr("y2", y(v)).attr("stroke", "var(--border)").attr("stroke-dasharray", "2,3");
      svg.append("text").attr("x", m.l - 7).attr("y", y(v) + 3.5).attr("text-anchor", "end").attr("font-size", 10.5).style("font-family", "var(--font-mono)").attr("fill", "var(--muted)").text(fmtPace(v));
    }

    // P10-P90 Forecast band + dashed Pred line
    const xb = x(Math.max(0, races.length - 1.55));
    svg.append("rect").attr("x", xb).attr("y", y(p10P)).attr("width", W - m.r - xb + 6).attr("height", Math.max(4, y(p90P) - y(p10P))).attr("fill", "var(--accent)").attr("opacity", 0.12).attr("rx", 3);
    svg.append("line").attr("x1", m.l).attr("x2", W - m.r + 6).attr("y1", y(predP)).attr("y2", y(predP)).attr("stroke", "var(--accent)").attr("stroke-width", 1.3).attr("stroke-dasharray", "4,3");
    svg.append("text").attr("x", W - m.r + 9).attr("y", y(predP) + 3.5).attr("font-size", 10).style("font-family", "var(--font-mono)").attr("fill", "var(--accent)").text(`Pred ${fmtPace(predP)}`);
    svg.append("text").attr("x", m.l + 4).attr("y", m.t - 8).attr("font-size", 10).attr("font-weight", 600).attr("fill", "var(--up)").text("↑ Faster Mile Pace (min/mi)");

    const line = d3.line().x((_, i) => x(i)).y((d) => y(d.pace));
    svg.append("path").datum(races).attr("d", line).attr("fill", "none").attr("stroke", colorMain).attr("stroke-width", 2.4);

    races.forEach((r, i) => {
      const cx = x(i), cy = y(r.pace);
      const is3k = r.dist >= 2900 && !r.isNat;
      svg.append("circle")
        .attr("cx", cx).attr("cy", cy)
        .attr("r", r.isNat ? 6.5 : 4.5)
        .attr("fill", r.isNat ? "var(--up)" : (is3k ? "var(--cyo)" : colorMain))
        .attr("stroke", "var(--card)").attr("stroke-width", 1.8)
        .style("cursor", "pointer")
        .on("mousemove", (evt) => showTip(evt,
          `<b>${esc(ath.n)} · ${esc(r.meet)}</b><br>` +
          `Date: <span class="mono">${r.date}</span> · Distance: <span class="mono">${r.dist}m</span><br>` +
          `Time: <b class="mono">${r.timeStr}</b> (<b class="mono">${fmtPace(r.pace)}/mi</b>)<br>` +
          `Finish: <b class="mono">${r.pl}</b>` +
          (r.isNat ? `<br>vs. Forecast: <b class="mono" style="color:var(--up)">${ath.dt.toFixed(1)}s (${ath.dpl >= 0 ? "+" : ""}${ath.dpl.toFixed(0)} pl)</b>` : "")
        ))
        .on("mouseleave", hideTip);

      if (r.isNat) {
        svg.append("text").attr("x", cx + 4).attr("y", cy - 11).attr("text-anchor", "end").attr("font-size", 10.2).attr("font-weight", 700).attr("fill", "var(--up)").text(prLabel);
        svg.append("text").attr("x", cx + 9).attr("y", cy + 3.5).attr("font-size", 11).attr("font-weight", 700).style("font-family", "var(--font-mono)").attr("fill", "var(--up)").text(fmtPace(r.pace));
      } else {
        const dy = i % 2 === 0 ? -9 : 14;
        svg.append("text").attr("x", cx).attr("y", Math.min(H - m.b - 4, Math.max(m.t + 10, cy + dy))).attr("text-anchor", "middle").attr("font-size", 9.5).style("font-family", "var(--font-mono)").attr("fill", "var(--fg2)").text(fmtPace(r.pace));
      }

      svg.append("text").attr("x", cx).attr("y", H - m.b + 14).attr("text-anchor", "middle").attr("font-size", 9.5).style("font-family", "var(--font-mono)").attr("font-weight", r.isNat ? 700 : 400).attr("fill", r.isNat ? "var(--up)" : "var(--muted)").text(r.date);
      svg.append("text").attr("x", cx).attr("y", H - m.b + 26).attr("text-anchor", "middle").attr("font-size", 8.8).attr("fill", r.isNat ? "var(--up)" : "var(--muted)").text(r.meet.slice(0, 10));
    });
  }

  // 3. Aquinas Diverging Beat Bar Chart
  function renderAquinasBars() {
    const box = document.getElementById("aqBeatChart");
    if (!box) return;
    box.innerHTML = "";
    const rows = AQ.slice().sort((a, b) => a.dt - b.dt);
    const W = Math.max(420, box.clientWidth || 600);
    const rh = 27;
    const m = { t: 24, r: 95, b: 28, l: 175 };
    const H = m.t + m.b + rows.length * rh;
    const svg = d3.select(box).append("svg").attr("viewBox", `0 0 ${W} ${H}`).style("width", "100%");
    const x = d3.scaleLinear().domain([-58, 25]).range([m.l, W - m.r]);
    const y = d3.scaleBand().domain(rows.map((d) => d.n)).range([m.t, H - m.b]).padding(0.28);

    svg.append("g").attr("transform", `translate(0,${H - m.b})`).call(d3.axisBottom(x).ticks(7).tickFormat((d) => `${d > 0 ? "+" : ""}${d}s`))
      .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));

    svg.append("line").attr("x1", x(0)).attr("x2", x(0)).attr("y1", m.t).attr("y2", H - m.b).attr("stroke", "var(--muted)").attr("stroke-width", 1.3);
    svg.append("line").attr("x1", x(8.6)).attr("x2", x(8.6)).attr("y1", m.t).attr("y2", H - m.b).attr("stroke", "var(--accent)").attr("stroke-dasharray", "3,3");
    svg.append("text").attr("x", x(8.6) + 4).attr("y", m.t - 6).attr("font-size", 10).attr("fill", "var(--accent)").text("Rest of Nation (+8.6s)");
    svg.append("text").attr("x", m.l + 4).attr("y", m.t - 6).attr("font-size", 10).attr("font-weight", 700).attr("fill", "var(--up)").text("← Faster than Pre-Race Forecast");

    rows.forEach((a) => {
      const yy = y(a.n);
      const isV = a.n === "Diego Victor" || a.n === "Marcela Victor";
      const col = isV ? "var(--dop)" : (a.dt < 0 ? "var(--up)" : "var(--muted)");
      svg.append("text").attr("x", m.l - 8).attr("y", yy + y.bandwidth() / 2 + 4).attr("text-anchor", "end")
        .attr("font-size", 11.5).attr("font-weight", isV || a.aa ? 700 : 500).attr("fill", isV ? "var(--dop)" : "var(--fg)")
        .text(`${a.n}${a.aa ? " ★" : ""} (${a.evs})`);
      svg.append("rect")
        .attr("x", x(Math.min(0, a.dt))).attr("y", yy)
        .attr("width", Math.max(3, Math.abs(x(a.dt) - x(0)))).attr("height", y.bandwidth()).attr("rx", 3)
        .attr("fill", col).attr("opacity", 0.9).style("cursor", "pointer")
        .on("mousemove", (evt) => showTip(evt,
          `<b>${esc(a.n)} (${a.evs}, Age ${a.ag})</b><br>` +
          `Actual: <b class="mono">${a.ats}</b> (${a.ap}/mi) vs Pred <span class="mono">${a.pts}</span><br>` +
          `Delta: <b class="mono" style="color:${a.dt < 0 ? "var(--up)" : "var(--muted)"}">${a.dt > 0 ? "+" : ""}${a.dt.toFixed(1)}s</b><br>` +
          `Overall: <b class="mono">#${a.apl}/${a.af}</b> (Pred #${a.ppl.toFixed(0)}, ${a.dpl > 0 ? "+" : ""}${a.dpl.toFixed(0)} pl)<br>` +
          `Single-Year Age: <b class="mono">#${a.aag}/${a.aagf}</b> ${a.aa ? '<b style="color:var(--up)">★ ALL-AMERICAN!</b>' : ""}`
        ))
        .on("mouseleave", hideTip);

      const lx = a.dt < 0 ? x(a.dt) - 5 : x(a.dt) + 5;
      svg.append("text").attr("x", lx).attr("y", yy + y.bandwidth() / 2 + 4).attr("text-anchor", a.dt < 0 ? "end" : "start")
        .attr("font-size", 10.5).attr("font-weight", 700).style("font-family", "var(--font-mono)").attr("fill", col)
        .text(`${a.dt > 0 ? "+" : ""}${a.dt.toFixed(1)}s`);
      svg.append("text").attr("x", W - m.r + 8).attr("y", yy + y.bandwidth() / 2 + 4)
        .attr("font-size", 10.5).style("font-family", "var(--font-mono)").attr("fill", "var(--fg2)")
        .text(`${a.ats} (#${a.apl})`);
    });
  }

  // 4. Interactive 2,424-Runner Predicted vs. Actual Scatter
  let scatGroup = "ALL";
  let scatEvent = "ALL";

  function renderScatter() {
    const box = document.getElementById("pvaScatterChart");
    if (!box) return;
    box.innerHTML = "";
    const sub = ATHS.filter((a) => {
      if (scatEvent !== "ALL" && String(a.ev) !== scatEvent) return false;
      if (scatGroup === "AQ" && !(a.dop && a.sch === "Aquinas Academy")) return false;
      if (scatGroup === "DOP" && !a.dop) return false;
      if (scatGroup === "CYO" && !a.cyo) return false;
      if (scatGroup === "AA" && !a.aa) return false;
      return true;
    });

    const W = Math.max(380, box.clientWidth || 560);
    const H = 340;
    const m = { t: 22, r: 22, b: 42, l: 52 };
    const tMin = Math.max(180, (d3.min(sub, (d) => Math.min(d.pt, d.at)) || 420) - 30);
    const tMax = (d3.max(sub, (d) => Math.max(d.pt, d.at)) || 1500) + 30;

    const svg = d3.select(box).append("svg").attr("viewBox", `0 0 ${W} ${H}`).style("width", "100%");
    const x = d3.scaleLinear().domain([tMin, tMax]).range([m.l, W - m.r]);
    const y = d3.scaleLinear().domain([tMin, tMax]).range([H - m.b, m.t]);

    svg.append("g").attr("transform", `translate(0,${H - m.b})`).call(d3.axisBottom(x).ticks(6).tickFormat((d) => fmtTime(d).replace(/\.\d$/, "")))
      .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));
    svg.append("g").attr("transform", `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(6).tickFormat((d) => fmtTime(d).replace(/\.\d$/, "")))
      .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));

    svg.append("line").attr("x1", x(tMin)).attr("y1", y(tMin)).attr("x2", x(tMax)).attr("y2", y(tMax))
      .attr("stroke", "var(--fg2)").attr("stroke-width", 1.3).attr("stroke-dasharray", "5,4");
    svg.append("text").attr("x", W - m.r - 6).attr("y", H - m.b - 8).attr("text-anchor", "end").attr("font-size", 10.5).attr("font-weight", 600).attr("fill", "var(--up)").text("Below line = Beat Pre-Race Forecast");
    svg.append("text").attr("x", (m.l + W - m.r) / 2).attr("y", H - 6).attr("text-anchor", "middle").attr("font-size", 11).attr("fill", "var(--muted)").text("Pre-Race Predicted Finish Time");

    const distCol = { 1000: "#94a3b8", 2000: "#2b6cb0", 3000: "#0d7a47", 4000: "#7e57c2", 5000: "#d97706" };
    // Non-Aquinas first, Aquinas on top
    const bg = sub.filter((a) => !(a.dop && a.sch === "Aquinas Academy"));
    const fg = sub.filter((a) => a.dop && a.sch === "Aquinas Academy");

    const drawPts = (arr, isAq) => {
      svg.selectAll(isAq ? "circle.aq" : "circle.bg")
        .data(arr)
        .join("circle")
        .attr("cx", (d) => x(d.pt))
        .attr("cy", (d) => y(d.at))
        .attr("r", (d) => isAq ? ((d.n === "Diego Victor" || d.n === "Marcela Victor") ? 6 : 4.5) : (sub.length < 150 ? 4 : 2.3))
        .attr("fill", (d) => isAq ? "var(--dop)" : (distCol[d.d] || "#64748b"))
        .attr("opacity", isAq ? 0.96 : (sub.length < 150 ? 0.72 : 0.36))
        .attr("stroke", (d) => isAq ? ((d.n === "Diego Victor" || d.n === "Marcela Victor") ? "#f5b800" : "#ffffff") : "none")
        .attr("stroke-width", (d) => (d.n === "Diego Victor" || d.n === "Marcela Victor") ? 2 : 1)
        .style("cursor", "pointer")
        .on("mousemove", (evt, d) => showTip(evt,
          `<b>${esc(d.n)}</b> · ${esc(fmtClub(d.tm, d.st))}${d.sch ? ` (${esc(d.sch)})` : ""}<br>` +
          `Ev ${d.ev} (${d.evs}) · Age ${d.ag} · <span class="muted">${esc(d.tier)}</span><br>` +
          `Predicted: <span class="mono">${d.pts}</span> (#${d.ppl.toFixed(0)}) → Actual: <b class="mono">${d.ats}</b> (#${d.apl}/${d.af})<br>` +
          `Δt: <b class="mono" style="color:${d.dt < 0 ? "var(--up)" : "var(--warn)"}">${d.dt > 0 ? "+" : ""}${d.dt.toFixed(1)}s</b>` +
          (d.aag ? ` · Age Place: <b class="mono">#${d.aag}/${d.aagf}</b> ${d.aa ? '<b style="color:var(--up)">★AA</b>' : ""}` : "")
        ))
        .on("mouseleave", hideTip);
    };
    drawPts(bg, false);
    drawPts(fg, true);

    const medDt = d3.median(sub, (d) => d.dt) || 0;
    const mae = d3.mean(sub, (d) => Math.abs(d.dt)) || 0;
    const beatPct = sub.length ? (100 * sub.filter((d) => d.dt < 0).length / sub.length) : 0;
    document.getElementById("pvaScatterSo").innerHTML =
      `Showing <b>${sub.length.toLocaleString()} finishers</b> · Median Δt: <b class="mono">${medDt > 0 ? "+" : ""}${medDt.toFixed(1)}s</b> · MAE: <b class="mono">${mae.toFixed(1)}s</b> · Beat Forecast: <b class="mono">${beatPct.toFixed(1)}%</b> (Crimson dots = Aquinas Academy; Gold ring = Diego &amp; Marcela Victor).`;
  }

  // 5. Western PA Residual Density Chart
  function renderResidualChart() {
    const box = document.getElementById("wpaResidualChart");
    if (!box) return;
    box.innerHTML = "";
    const W = Math.max(360, box.clientWidth || 500);
    const H = 340;
    const m = { t: 28, r: 18, b: 42, l: 26 };
    const xs = d3.range(-100, 101, 2);
    const kde = (vals, bw) => xs.map((x0) => {
      let s = 0;
      for (let i = 0; i < vals.length; i++) {
        const u = (x0 - vals[i]) / bw;
        s += Math.exp(-0.5 * u * u);
      }
      return { x: x0, y: s / (vals.length * bw * Math.sqrt(2 * Math.PI)) };
    });
    const dNat = kde(OTHER.filter((a) => Math.abs(a.dt) <= 120).map((a) => a.dt), 14);
    const dDop = kde(DOP.filter((a) => Math.abs(a.dt) <= 120).map((a) => a.dt), 15);
    const dAq = kde(AQ.map((a) => a.dt), 16);
    const yMax = Math.max(d3.max(dNat, (d) => d.y), d3.max(dDop, (d) => d.y), d3.max(dAq, (d) => d.y)) * 1.15;

    const svg = d3.select(box).append("svg").attr("viewBox", `0 0 ${W} ${H}`).style("width", "100%");
    const x = d3.scaleLinear().domain([-100, 100]).range([m.l, W - m.r]);
    const y = d3.scaleLinear().domain([0, yMax]).range([H - m.b, m.t]);

    svg.append("g").attr("transform", `translate(0,${H - m.b})`).call(d3.axisBottom(x).ticks(8).tickFormat((d) => `${d > 0 ? "+" : ""}${d}s`))
      .call((g) => g.selectAll("text").attr("fill", "var(--muted)").style("font-family", "var(--font-mono)"));
    svg.append("line").attr("x1", x(0)).attr("x2", x(0)).attr("y1", m.t).attr("y2", H - m.b).attr("stroke", "var(--muted)").attr("stroke-width", 1.2);

    const area = d3.area().x((d) => x(d.x)).y0(H - m.b).y1((d) => y(d.y)).curve(d3.curveBasis);
    const line = d3.line().x((d) => x(d.x)).y((d) => y(d.y)).curve(d3.curveBasis);

    [
      { d: dNat, c: "#64748b", med: 8.6, lbl: "Rest of Nation (+8.6s)", ly: m.t + 14 },
      { d: dDop, c: "var(--cyo)", med: -18.7, lbl: "Pittsburgh CYO (-18.7s)", ly: m.t + 32 },
      { d: dAq, c: "var(--dop)", med: -24.0, lbl: "Aquinas Academy (-24.0s)", ly: m.t + 50 },
    ].forEach((s) => {
      svg.append("path").datum(s.d).attr("d", area).attr("fill", s.c).attr("opacity", 0.16);
      svg.append("path").datum(s.d).attr("d", line).attr("fill", "none").attr("stroke", s.c).attr("stroke-width", 2.2);
      svg.append("line").attr("x1", x(s.med)).attr("x2", x(s.med)).attr("y1", m.t).attr("y2", H - m.b).attr("stroke", s.c).attr("stroke-dasharray", "3,3");
      svg.append("text").attr("x", m.l + 8).attr("y", s.ly).attr("font-size", 11).attr("font-weight", 700).attr("fill", s.c).text(`● ${s.lbl}`);
    });
    svg.append("text").attr("x", (m.l + W - m.r) / 2).attr("y", H - 6).attr("text-anchor", "middle").attr("font-size", 11).attr("fill", "var(--muted)").text("Actual − Predicted Time (seconds) · Negative = Beat Forecast");
  }

  // 6. Pittsburgh CYO & 8-for-8 CYO Champions Table
  function renderCyoAuditTable() {
    const tb = document.getElementById("cyoAuditTableBody");
    if (!tb) return;
    const rows = [];
    [3, 4, 6, 7, 8, 9, 10, 11].forEach((evN) => {
      const evObj = EVENTS.find((e) => e.event_num === evN);
      const natDop = TEAMS.filter((t) => t.event_num === evN && t.is_dop && t.lens === "nat");
      const cyoDop = TEAMS.filter((t) => t.event_num === evN && t.is_dop && t.lens === "cyo");
      const cChamp = evObj && evObj.cyo_top3_act && evObj.cyo_top3_act[0] ? evObj.cyo_top3_act[0].team : "—";
      natDop.forEach((nt) => {
        const ct = cyoDop.find((c) => c.team === nt.team) || {};
        const badge = ct.act_rank === 1
          ? '<span class="badge b-up">CYO CHAMP!</span>'
          : (ct.act_rank && ct.act_rank <= 3 ? '<span class="badge b-cyo">CYO PODIUM</span>' : '<span class="badge b-muted">#4 CYO</span>');
        rows.push(`<tr>
          <td><b>${nt.event_short}</b></td>
          <td><span class="dop-txt"><b>${esc(fmtClub(nt.team, nt.state))}</b></span></td>
          <td class="num mono">#${nt.pred_rank.toFixed(1)} → <b style="color:var(--up)">#${nt.act_rank}</b> <span class="muted">(${nt.act_score} pts)</span></td>
          <td class="num mono">#${(ct.pred_rank || 0).toFixed(1)} → <b>#${ct.act_rank}</b> <span class="muted">(${ct.act_score} pts)</span></td>
          <td class="num">${badge}</td>
          <td><span style="color:var(--up);font-weight:700">✓</span> ${esc(cChamp)}</td>
        </tr>`);
      });
    });
    tb.innerHTML = rows.join("");
  }

  // 7. Searchable Actuals vs Predictions Table
  let tblScope = "AQ";
  let tblSearch = "";
  let tblEv = "ALL";

  function renderResultsTable() {
    const tb = document.getElementById("pvaTableBody");
    const sumEl = document.getElementById("pvaTableCount");
    if (!tb) return;
    const q = tblSearch.trim().toLowerCase();
    const list = ATHS.filter((a) => {
      if (tblEv !== "ALL" && String(a.ev) !== tblEv) return false;
      if (tblScope === "AQ" && !(a.dop && a.sch === "Aquinas Academy")) return false;
      if (tblScope === "DOP" && !a.dop) return false;
      if (tblScope === "AA" && !a.aa) return false;
      if (q && !(a.n.toLowerCase().includes(q) || a.tm.toLowerCase().includes(q) || a.sch.toLowerCase().includes(q))) return false;
      return true;
    }).sort((a, b) => a.ev - b.ev || a.apl - b.apl);

    sumEl.textContent = `Showing ${Math.min(list.length, 250).toLocaleString()} of ${list.length.toLocaleString()} matched finishers`;
    tb.innerHTML = list.slice(0, 250).map((a) => {
      const isV = a.n === "Diego Victor" || a.n === "Marcela Victor";
      const dtCol = a.dt < 0 ? "var(--up)" : "var(--muted)";
      return `<tr style="${isV ? "background:rgba(184,37,30,0.08)" : ""}">
        <td><b>${esc(a.n)}</b>${a.aa ? ' <span class="badge b-up">★AA</span>' : ""}</td>
        <td>${a.evs}</td>
        <td class="num mono">${a.ag}</td>
        <td>${a.dop ? `<span class="dop-txt">${esc(fmtClub(a.tm, a.st))}</span>` : esc(fmtClub(a.tm, a.st))}</td>
        <td class="muted">${esc(a.sch || "—")}</td>
        <td class="num mono muted">${a.pts}</td>
        <td class="num mono"><b>${a.ats}</b> (${a.ap})</td>
        <td class="num mono" style="color:${dtCol};font-weight:700">${a.dt > 0 ? "+" : ""}${a.dt.toFixed(1)}s</td>
        <td class="num mono">#${a.ppl.toFixed(0)} → <b>#${a.apl}</b>/${a.af}</td>
        <td class="num mono">${a.aag ? `<b>#${a.aag}</b>/${a.aagf}` : "—"}</td>
      </tr>`;
    }).join("");
  }

  // Wire controls
  const evOpts = `<option value="ALL">All 11 Events</option>` + EVENTS.map((e) => `<option value="${e.event_num}">Ev ${e.event_num} · ${e.name}</option>`).join("");
  const scEvSel = document.getElementById("scatEventSel");
  const tbEvSel = document.getElementById("tblEventSel");
  if (scEvSel) { scEvSel.innerHTML = evOpts; scEvSel.addEventListener("change", () => { scatEvent = scEvSel.value; renderScatter(); }); }
  if (tbEvSel) { tbEvSel.innerHTML = evOpts; tbEvSel.addEventListener("change", () => { tblEv = tbEvSel.value; renderResultsTable(); }); }

  document.querySelectorAll("#scatGroupPills button").forEach((b) => {
    b.addEventListener("click", () => {
      scatGroup = b.dataset.grp;
      document.querySelectorAll("#scatGroupPills button").forEach((x) => x.setAttribute("aria-pressed", x.dataset.grp === scatGroup));
      renderScatter();
    });
  });

  document.querySelectorAll("#tblScopePills button").forEach((b) => {
    b.addEventListener("click", () => {
      tblScope = b.dataset.scope;
      document.querySelectorAll("#tblScopePills button").forEach((x) => x.setAttribute("aria-pressed", x.dataset.scope === tblScope));
      renderResultsTable();
    });
  });

  const searchInp = document.getElementById("pvaSearchInp");
  if (searchInp) searchInp.addEventListener("input", () => { tblSearch = searchInp.value; renderResultsTable(); });

  // Initial render
  renderSeasonCurve("diegoPaceChart", diego, "#b8251e", "2K PR! (#9 Age-6 ★AA)");
  renderSeasonCurve("marcelaPaceChart", marcela, "#b8251e", "3K PR! (-24.0s / +35 pl)");
  renderAquinasBars();
  renderScatter();
  renderResidualChart();
  renderCyoAuditTable();
  renderResultsTable();

  window.addEventListener("resize", () => {
    renderSeasonCurve("diegoPaceChart", diego, "#b8251e", "2K PR! (#9 Age-6 ★AA)");
    renderSeasonCurve("marcelaPaceChart", marcela, "#b8251e", "3K PR! (-24.0s / +35 pl)");
    renderAquinasBars();
    renderScatter();
    renderResidualChart();
  });
})();
