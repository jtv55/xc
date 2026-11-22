import html as html_mod
import json
import math
import pathlib
import subprocess
import numpy as np

BASE = pathlib.Path(r"c:\Users\j_t_v\XC\nationals")
PVA_FP = BASE / "data" / "actuals_2026" / "predicted_vs_actual_2026.json"
PRE_FP = BASE / "data" / "snapshots" / "pre_race_20261121" / "cccnyc_2026_master_prerace.json"
OUT_HTML = pathlib.Path(r"C:\Users\j_t_v\.gemini\antigravity\brain\fd1d52a6-9fa9-45a6-a634-3e07b1681514\scratch\aquinas_postrace_report.html")
OUT_PDF = BASE / "data" / "pdfs" / "Aquinas_Academy_2026_CCCNYC_Post_Race_Report.pdf"

pva = json.loads(PVA_FP.read_text(encoding="utf-8"))
pre = json.loads(PRE_FP.read_text(encoding="utf-8"))
pre_map = {a["id"]: a for a in pre["athletes"]}

SUMMARY = pva["summary"]
ATHS = pva["athletes"]
EVENTS = pva["events"]
TEAMS = pva["teams"]
TIER_STATS = pva["tier_stats"]

AQ = sorted(
    [a for a in ATHS if a["is_dop"] and a["home_school"] == "Aquinas Academy"],
    key=lambda x: (x["event_num"], x["act_place"]),
)
DOP = [a for a in ATHS if a["is_dop"]]
OTHER = [a for a in ATHS if not a["is_dop"]]

diego = next(a for a in AQ if a["display_name"] == "Diego Victor")
marcela = next(a for a in AQ if a["display_name"] == "Marcela Victor")

TOTAL_PAGES = 15  # P1 Cover, P2 Slopegraph & Team Summary, P3-P13 All 11 Aquinas Kids, P14 Calibration, P15 AA & CYO Honor Roll

def esc(s):
    return html_mod.escape(str("" if s is None else s))

def fmt_time(sec):
    if sec is None or math.isnan(sec):
        return "—"
    mn = int(sec // 60)
    rem = sec - mn * 60
    return f"{mn}:{rem:04.1f}"

def fmt_pace_s(pace_sec):
    mn = int(pace_sec // 60)
    sc = int(round(pace_sec - mn * 60))
    if sc == 60:
        mn += 1
        sc = 0
    return f"{mn}:{sc:02d}"

def pace_sec(time_sec, dist_m):
    return time_sec / (dist_m / 1609.344)

def short_meet(m):
    return (
        m.replace("XC Meet ", "")
        .replace("Developmental ", "Dev ")
        .replace("Dev Boys and Girls", "")
        .replace("Dev Girls", "")
        .replace("Dev Boys", "")
        .replace("DEV Boys and Girls", "")
        .replace("JV Boys and Girls", "")
        .replace("JV Boys", "")
        .replace("JV Girls", "")
        .replace("Varsity Boys and Girls", "")
        .replace("Varsity Boys", "")
        .replace("Varsity Girls", "")
        .replace("3rd and 4th Boys and Girls", "")
        .replace("Pittsburgh Diocesan XC Championship", "Diocesan Champ")
        .replace("Oakland Catholic XC Invitational", "Oakland Cath. 3K")
        .replace("North Area XC Championships", "North Area")
        .replace("Run for the Pumpkins XC", "Pumpkins XC")
        .replace("Aquinas XC", "Aquinas Invite")
        .replace("St Kilian XC", "St. Kilian")
        .replace("Seelos XC", "Seelos")
        .replace("Youthtowne", "Youthtowne")
        .replace("BTA", "BTA Invite")
        .strip()
    )

def short_school(s):
    if not s:
        return "—"
    return (
        s.replace(" Catholic School", "")
        .replace(" Elementary School", "")
        .replace(" Parish School", "")
        .replace(" School", "")
        .replace("Blessed Francis Seelos Academy", "Seelos Academy")
        .replace("St. Louise de Marillac", "St. Louise")
        .replace("South Hills Catholic Academy", "South Hills Cath.")
        .replace("John F. Kennedy", "JFK Catholic")
        .replace("Guardian Angel Academy", "Guardian Angel")
    )

# ==============================================================================
# SVG 1: AQUINAS ACADEMY TIME BEAT DIVERGING BAR CHART (PAGE 1)
# ==============================================================================
def build_aq_diverging_svg(W=735, H=212):
    rows = sorted(AQ, key=lambda a: a["time_err_sec"])
    ml, mr, mt, mb = 148, 84, 20, 26
    pw, ph = W - ml - mr, H - mt - mb
    xmin, xmax = -58.0, 24.0
    def sx(v): return ml + (v - xmin) / (xmax - xmin) * pw
    rh = ph / len(rows)
    x0 = sx(0.0)
    x_nat = sx(8.6)

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;height:auto">']
    parts.append(f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="#faf8f3" rx="3"/>')
    for v in [-50, -40, -30, -20, -10, 0, 10, 20]:
        xv = sx(v)
        col = "#9aa0ab" if v == 0 else "#e7e3d9"
        sw = "1.2" if v == 0 else "0.7"
        parts.append(f'<line x1="{xv:.1f}" y1="{mt}" x2="{xv:.1f}" y2="{H-mb}" stroke="{col}" stroke-width="{sw}"/>')
        lbl = f"{v:+d}s" if v != 0 else "0s (Forecast)"
        parts.append(f'<text x="{xv:.1f}" y="{H-mb+13}" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="7.4" fill="#646a76">{lbl}</text>')

    parts.append(f'<line x1="{x_nat:.1f}" y1="{mt}" x2="{x_nat:.1f}" y2="{H-mb}" stroke="#64748b" stroke-width="1.0" stroke-dasharray="3,2.5"/>')
    parts.append(f'<text x="{x_nat+3:.1f}" y="{mt-5}" font-family="IBM Plex Sans,sans-serif" font-size="6.8" font-weight="600" fill="#475569">Rest of Nation Median (+8.6s)</text>')
    parts.append(f'<text x="{ml+4}" y="{mt-5}" font-family="IBM Plex Sans,sans-serif" font-size="6.8" font-weight="700" fill="#0d7a47">&#8592; Ran FASTER than Pre-Race Forecast</text>')

    for i, a in enumerate(rows):
        yc = mt + (i + 0.5) * rh
        bh = rh * 0.62
        err = a["time_err_sec"]
        col = "#0d7a47" if err < 0 else "#8b929e"
        bx = sx(min(0, err))
        bw = max(2.0, abs(sx(err) - x0))
        parts.append(f'<rect x="{bx:.1f}" y="{yc-bh/2:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="2.5" fill="{col}" opacity="0.92"/>')
        nm_col = "#172030"
        fw = "700" if a["act_is_aa"] else "600"
        star = " ★" if a["act_is_aa"] else ""
        parts.append(f'<text x="{ml-6}" y="{yc+2.6:.1f}" text-anchor="end" font-family="IBM Plex Sans,sans-serif" font-size="7.7" font-weight="{fw}" fill="{nm_col}">{esc(a["display_name"])}{star} <tspan fill="#6f7582" font-size="6.8" font-weight="400">({a["event_short"]})</tspan></text>')
        pl_txt = f"{a['place_err']:+.0f} pl" if a["place_err"] != 0 else "0 pl"
        if err < 0:
            parts.append(f'<text x="{bx-4:.1f}" y="{yc+2.5:.1f}" text-anchor="end" font-family="IBM Plex Mono,monospace" font-size="7.2" font-weight="700" fill="{col}">{err:+.1f}s</text>')
            parts.append(f'<text x="{W-mr+6}" y="{yc+2.5:.1f}" font-family="IBM Plex Mono,monospace" font-size="6.9" fill="#475569">{a["act_time_str"]} ({pl_txt})</text>')
        else:
            parts.append(f'<text x="{bx+bw+4:.1f}" y="{yc+2.5:.1f}" font-family="IBM Plex Mono,monospace" font-size="7.2" font-weight="700" fill="{col}">{err:+.1f}s</text>')
            parts.append(f'<text x="{W-mr+6}" y="{yc+2.5:.1f}" font-family="IBM Plex Mono,monospace" font-size="6.9" fill="#475569">{a["act_time_str"]} ({pl_txt})</text>')

    parts.append("</svg>")
    return "".join(parts)

# ==============================================================================
# SVG: INDIVIDUAL 2026 SEASON PACE PROGRESSION CURVE (WORKS FOR ALL 11 KIDS!)
# ==============================================================================
def build_season_pace_svg(ath_pair, nat_badge_lbl=None, color_main="#b8251e", W=455, H=218):
    pre_a = pre_map[ath_pair["id"]]
    races = sorted(pre_a["races_2026"], key=lambda r: r["date"])
    pts = []
    for r in races:
        pts.append({
            "date": r["date"][5:],
            "label": short_meet(r["meet"]),
            "pace": pace_sec(r["time_sec"], r["dist_m"]),
            "time_str": r["time_str"],
            "dist_m": r["dist_m"],
            "is_nat": False,
        })
    nat_pace = pace_sec(ath_pair["act_time_sec"], ath_pair["dist_m"])
    pred_pace = pace_sec(ath_pair["pred_time_sec"], ath_pair["dist_m"])
    p10_pace = pace_sec(ath_pair["p10_time_sec"], ath_pair["dist_m"])
    p90_pace = pace_sec(ath_pair["p90_time_sec"], ath_pair["dist_m"])
    pts.append({
        "date": "11-21",
        "label": "Cedarville",
        "pace": nat_pace,
        "time_str": ath_pair["act_time_str"],
        "dist_m": ath_pair["dist_m"],
        "is_nat": True,
    })

    ml, mr, mt, mb = 44, 60, 22, 42
    pw, ph = W - ml - mr, H - mt - mb
    all_p = [p["pace"] for p in pts] + [pred_pace, p10_pace, p90_pace]
    ymin = math.floor((min(all_p) - 10) / 15) * 15
    ymax = math.ceil((max(all_p) + 10) / 15) * 15
    if ymax - ymin < 45:
        ymin -= 15
        ymax += 15
    def sy(p): return mt + (p - ymin) / (ymax - ymin) * ph
    def sx(i): return ml + (i / max(1, len(pts) - 1)) * pw

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;height:auto">']
    parts.append(f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="#faf8f3" rx="3"/>')

    # P10-P90 Forecast Band on right side
    x_band = sx(max(0, len(pts) - 1.55))
    parts.append(f'<rect x="{x_band:.1f}" y="{sy(p10_pace):.1f}" width="{W-mr-x_band+4:.1f}" height="{max(3, sy(p90_pace)-sy(p10_pace)):.1f}" fill="#132c54" opacity="0.09" rx="2"/>')
    parts.append(f'<line x1="{ml}" y1="{sy(pred_pace):.1f}" x2="{W-mr+4}" y2="{sy(pred_pace):.1f}" stroke="#132c54" stroke-width="1.0" stroke-dasharray="4,3" opacity="0.65"/>')
    pred_ly = sy(pred_pace) + 2.5
    nat_ly = sy(nat_pace) + 2.5
    if abs(pred_ly - nat_ly) < 10:
        pred_ly = nat_ly + (10 if pred_pace >= nat_pace else -10)
    parts.append(f'<text x="{W-mr+7}" y="{pred_ly:.1f}" font-family="IBM Plex Mono,monospace" font-size="6.7" font-weight="600" fill="#132c54">Pred {fmt_pace_s(pred_pace)}</text>')

    step = 15 if (ymax - ymin) <= 105 else 30
    v = ymin
    while v <= ymax + 0.1:
        yv = sy(v)
        parts.append(f'<line x1="{ml}" y1="{yv:.1f}" x2="{W-mr}" y2="{yv:.1f}" stroke="#e6e2d8" stroke-width="0.65"/>')
        parts.append(f'<text x="{ml-6}" y="{yv+2.5:.1f}" text-anchor="end" font-family="IBM Plex Mono,monospace" font-size="7.1" fill="#646a76">{fmt_pace_s(v)}</text>')
        v += step
    parts.append(f'<text x="{ml+4}" y="{mt-6}" font-family="IBM Plex Sans,sans-serif" font-size="6.8" font-weight="600" fill="#0d7a47">&#8593; Faster Mile Pace (min/mi)</text>')

    poly = " ".join(f"{sx(i):.1f},{sy(p['pace']):.1f}" for i, p in enumerate(pts))
    parts.append(f'<polyline points="{poly}" fill="none" stroke="{color_main}" stroke-width="2.1" stroke-linejoin="round"/>')

    nat_dist = ath_pair["dist_m"]
    for i, p in enumerate(pts):
        cx, cy = sx(i), sy(p["pace"])
        if p["is_nat"]:
            nat_col = "#0d7a47" if ath_pair["time_err_sec"] <= 3 else "#132c54"
            tag = nat_badge_lbl or (f"{nat_dist//1000}K PR!" if ath_pair["time_err_sec"] < 0 else "Nationals")
            prev_p = pts[i - 1]["pace"] if i > 0 else p["pace"]
            tag_dy = 15 if p["pace"] > prev_p + 2 else -10
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5.5" fill="{nat_col}" stroke="#ffffff" stroke-width="1.6"/>')
            parts.append(f'<text x="{cx+7:.1f}" y="{cy+2.5:.1f}" font-family="IBM Plex Mono,monospace" font-size="7.6" font-weight="700" fill="{nat_col}">{fmt_pace_s(p["pace"])}/mi</text>')
            parts.append(f'<text x="{cx+2:.1f}" y="{cy+tag_dy:.1f}" text-anchor="end" font-family="IBM Plex Sans,sans-serif" font-size="6.8" font-weight="700" fill="{nat_col}" paint-order="stroke" stroke="#faf8f3" stroke-width="2.8">{esc(tag)}</text>')
        else:
            is_same_dist = (abs(p["dist_m"] - nat_dist) <= 150) and nat_dist >= 3000
            fill = "#5b359a" if is_same_dist else color_main
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3.3" fill="{fill}" stroke="#ffffff" stroke-width="1.1"/>')
            prev_p = pts[i - 1]["pace"] if i > 0 else p["pace"]
            next_p = pts[i + 1]["pace"] if i < len(pts) - 1 else p["pace"]
            is_faster_peak = (p["pace"] <= prev_p and p["pace"] <= next_p)
            dy = -8 if is_faster_peak else 13
            if i == 0:
                dy = 13 if next_p < p["pace"] else -8
            if cy + dy < mt + 9: dy = 13
            if cy + dy > H - mb - 4: dy = -8
            parts.append(f'<text x="{cx:.1f}" y="{cy+dy:.1f}" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="6.4" fill="#334155" paint-order="stroke" stroke="#faf8f3" stroke-width="2.5">{fmt_pace_s(p["pace"])}</text>')

        parts.append(f'<text x="{cx:.1f}" y="{H-mb+11}" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="6.2" font-weight="{"700" if p["is_nat"] else "400"}" fill="{"#0d7a47" if p["is_nat"] else "#646a76"}">{p["date"]}</text>')
        short_l = p["label"][:10]
        parts.append(f'<text x="{cx:.1f}" y="{H-mb+21}" text-anchor="middle" font-family="IBM Plex Sans,sans-serif" font-size="5.8" font-weight="{"700" if p["is_nat"] else "400"}" fill="{"#0d7a47" if p["is_nat"] else "#6f7582"}">{esc(short_l)}</text>')

    parts.append("</svg>")
    return "".join(parts)

# ==============================================================================
# SVG: SINGLE-YEAR AGE LEADERBOARD STRIP (FOR ALL-AMERICANS: LINUS, DIEGO, NOAH)
# ==============================================================================
def build_age_leaderboard_svg(ath_pair, W=265, H=218):
    ev_num = ath_pair["event_num"]
    ag = ath_pair["age"]
    peers = sorted([a for a in ATHS if a["event_num"] == ev_num and a["age"] == ag and a["act_age_place"]], key=lambda x: x["act_age_place"])
    # Pick Top 12 (or Top 10 + runner's window if ranked 11..25)
    rk = ath_pair["act_age_place"]
    if rk <= 12:
        show = peers[:12]
    else:
        show = peers[:4] + peers[max(4, rk - 5):min(len(peers), rk + 3)]
        show = show[:12]

    cut25_rec = next((a for a in peers if a["act_age_place"] == 25), peers[-1])
    cut25 = cut25_rec["act_time_sec"]

    ml, mr, mt, mb = 104, 46, 18, 22
    pw, ph = W - ml - mr, H - mt - mb
    times_all = [a["act_time_sec"] for a in show] + [a["pred_time_sec"] for a in show if a["pred_time_sec"] < cut25 + 60] + [cut25]
    tmin = math.floor((min(times_all) - 10) / 15) * 15
    tmax = math.ceil((max(max(a["act_time_sec"] for a in show), cut25) + 12) / 15) * 15
    def sx(t): return ml + (min(tmax, max(tmin, t)) - tmin) / max(1, (tmax - tmin)) * pw
    rh = ph / len(show)

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;height:auto">']
    parts.append(f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="#faf8f3" rx="3"/>')
    step = 30 if (tmax - tmin) <= 150 else 60
    t = math.ceil(tmin / step) * step
    while t <= tmax - 5:
        xv = sx(t)
        parts.append(f'<line x1="{xv:.1f}" y1="{mt}" x2="{xv:.1f}" y2="{H-mb}" stroke="#e7e3d9" stroke-width="0.7"/>')
        parts.append(f'<text x="{xv:.1f}" y="{H-mb+12}" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="6.4" fill="#646a76">{fmt_time(t)[:-2]}</text>')
        t += step

    xcut = sx(cut25)
    parts.append(f'<line x1="{xcut:.1f}" y1="{mt}" x2="{xcut:.1f}" y2="{H-mb}" stroke="#0d7a47" stroke-width="1.1" stroke-dasharray="3,2"/>')
    parts.append(f'<text x="{min(W-mr-2, xcut-2):.1f}" y="{mt-4}" text-anchor="end" font-family="IBM Plex Mono,monospace" font-size="6.3" font-weight="700" fill="#0d7a47">#25 AA Cut {cut25_rec["act_time_str"]}</text>')

    for i, a in enumerate(show):
        yc = mt + (i + 0.5) * rh
        is_me = (a["id"] == ath_pair["id"])
        if is_me:
            parts.append(f'<rect x="2" y="{yc-rh*0.48:.1f}" width="{W-4}" height="{rh*0.96:.1f}" fill="#fdf2f1" rx="2"/>')
        xa = sx(a["act_time_sec"])
        xp = sx(a["pred_time_sec"])
        parts.append(f'<line x1="{xp:.1f}" y1="{yc:.1f}" x2="{xa:.1f}" y2="{yc:.1f}" stroke="{"#b8251e" if is_me else "#94a3b8"}" stroke-width="{"1.7" if is_me else "0.9"}" opacity="0.75"/>')
        parts.append(f'<circle cx="{xp:.1f}" cy="{yc:.1f}" r="2.1" fill="#ffffff" stroke="{"#b8251e" if is_me else "#94a3b8"}" stroke-width="1.0"/>')
        parts.append(f'<circle cx="{xa:.1f}" cy="{yc:.1f}" r="{"3.6" if is_me else "2.6"}" fill="{"#b8251e" if is_me else ("#5b359a" if a["is_cyo"] else "#132c54")}"/>')
        toks = a["display_name"].split()
        fn_i = toks[0][0]
        ln_s = toks[-2] if (len(toks) >= 3 and toks[-1].rstrip(".").lower() in ("jr", "sr", "ii", "iii", "iv")) else toks[-1]
        nm = f"#{a['act_age_place']} {a['display_name']} ★" if is_me else f"#{a['act_age_place']} {fn_i}. {ln_s}"
        if len(nm) > 19 and not is_me: nm = nm[:18] + "…"
        parts.append(f'<text x="{ml-5}" y="{yc+2.4:.1f}" text-anchor="end" font-family="IBM Plex Sans,sans-serif" font-size="6.8" font-weight="{"700" if is_me else "500"}" fill="{"#b8251e" if is_me else "#172030"}">{esc(nm)}</text>')
        parts.append(f'<text x="{W-mr+5}" y="{yc+2.4:.1f}" font-family="IBM Plex Mono,monospace" font-size="6.7" font-weight="{"700" if is_me else "400"}" fill="{"#b8251e" if is_me else "#475569"}">{a["act_time_str"]}</text>')

    parts.append("</svg>")
    return "".join(parts)

# ==============================================================================
# SVG: EVENT PACK S-CURVE & PLACE SURGE VISUAL (FOR EVERY RACE!)
# ==============================================================================
def build_event_pack_svg(ath_pair, W=265, H=218):
    ev_num = ath_pair["event_num"]
    ev_aths = sorted([a for a in ATHS if a["event_num"] == ev_num], key=lambda x: x["act_place"])
    ml, mr, mt, mb = 36, 12, 22, 28
    pw, ph = W - ml - mr, H - mt - mb
    n = len(ev_aths)
    ts = [a["act_time_sec"] for a in ev_aths]
    p02, p98 = float(np.percentile(ts, 1)), float(np.percentile(ts, 98))
    ymin = math.floor((p02 - 20) / 60) * 60
    ymax = math.ceil((p98 + 20) / 60) * 60
    def sx(pl): return ml + (pl - 1) / max(1, n - 1) * pw
    def sy(t): return H - mb - (min(ymax, max(ymin, t)) - ymin) / max(1, ymax - ymin) * ph

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;height:auto">']
    parts.append(f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="#faf8f3" rx="3"/>')
    step = 60 if (ymax - ymin) <= 300 else 120
    t = ymin + step
    while t < ymax:
        yv = sy(t)
        parts.append(f'<line x1="{ml}" y1="{yv:.1f}" x2="{W-mr}" y2="{yv:.1f}" stroke="#e7e3d9" stroke-width="0.7"/>')
        parts.append(f'<text x="{ml-4}" y="{yv+2.4:.1f}" text-anchor="end" font-family="IBM Plex Mono,monospace" font-size="6.4" fill="#646a76">{fmt_time(t)[:-2]}</text>')
        t += step
    for frac in [0, 0.25, 0.5, 0.75, 1.0]:
        pl = max(1, int(round(1 + frac * (n - 1))))
        xv = sx(pl)
        parts.append(f'<text x="{xv:.1f}" y="{H-mb+11}" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="6.3" fill="#646a76">#{pl}</text>')
    parts.append(f'<text x="{ml+pw/2:.1f}" y="{H-4}" text-anchor="middle" font-family="IBM Plex Sans,sans-serif" font-size="6.4" fill="#646a76">Actual Finish Place ({n} Finishers · {ath_pair["event_short"]})</text>')

    # Field dots
    for a in ev_aths:
        if a["is_dop"] and a["home_school"] == "Aquinas Academy":
            continue
        cx, cy = sx(a["act_place"]), sy(a["act_time_sec"])
        col = "#7e57c2" if a["is_cyo"] else "#cbd5e1"
        r = 1.5 if a["is_cyo"] else 1.1
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{col}" opacity="0.78"/>')

    # Pred -> Act jump arrow for target runner
    xp, yp = sx(ath_pair["pred_place"]), sy(ath_pair["pred_time_sec"])
    xa, ya = sx(ath_pair["act_place"]), sy(ath_pair["act_time_sec"])
    parts.append(f'<line x1="{xp:.1f}" y1="{yp:.1f}" x2="{xa:.1f}" y2="{ya:.1f}" stroke="#b8251e" stroke-width="1.8" stroke-dasharray="3,2"/>')
    parts.append(f'<circle cx="{xp:.1f}" cy="{yp:.1f}" r="3.3" fill="#ffffff" stroke="#b8251e" stroke-width="1.3"/>')

    # Clean collision-free legend strip in top-left of Pack Surge plot for Aquinas teammates + Pred callout below curve!
    pred_lbl_x = min(W - mr - 4, max(ml + 8, xp + 5))
    pred_anc = "start" if xp < W - mr - 78 else "end"
    if pred_anc == "end":
        pred_lbl_x = min(W - mr - 4, xp - 2)
    pred_lbl_y = min(H - mb - 4, yp + 16)
    parts.append(f'<line x1="{xp:.1f}" y1="{yp+3:.1f}" x2="{xp:.1f}" y2="{pred_lbl_y-6:.1f}" stroke="#94a3b8" stroke-width="0.7"/>')
    parts.append(f'<text x="{pred_lbl_x:.1f}" y="{pred_lbl_y:.1f}" text-anchor="{pred_anc}" font-family="IBM Plex Mono,monospace" font-size="6.1" fill="#475569" paint-order="stroke" stroke="#faf8f3" stroke-width="2.8">Pred #{ath_pair["pred_place"]:.0f} ({ath_pair["pred_time_str"]})</text>')

    # Aquinas teammates in this event (cleanly plotted in green, listed neatly in top-left legend box so ZERO text overlaps on curve!)
    aq_ev = [a for a in ev_aths if a["is_dop"] and a["home_school"] == "Aquinas Academy"]
    teammates = [a for a in aq_ev if a["id"] != ath_pair["id"]]
    for a in teammates:
        cx, cy = sx(a["act_place"]), sy(a["act_time_sec"])
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3.2" fill="#0d7a47" stroke="#ffffff" stroke-width="1.1"/>')
    if teammates:
        parts.append(f'<rect x="{ml+5}" y="{mt+4}" width="108" height="{12 + 10*len(teammates)}" rx="3" fill="#ffffff" stroke="#d8d4c8" stroke-width="0.7" opacity="0.94"/>')
        parts.append(f'<text x="{ml+10}" y="{mt+13}" font-family="IBM Plex Sans,sans-serif" font-size="6.0" font-weight="700" fill="#0d7a47">Aquinas Teammates (●)</text>')
        for ti, a in enumerate(teammates):
            ln = a["display_name"].split()[-1]
            parts.append(f'<text x="{ml+10}" y="{mt+23 + ti*10}" font-family="IBM Plex Mono,monospace" font-size="5.9" fill="#334155">{a["display_name"].split()[0][0]}. {ln}: #{a["act_place"]} ({a["act_time_str"]})</text>')

    # Target runner big crimson circle + clean upper callout
    parts.append(f'<circle cx="{xa:.1f}" cy="{ya:.1f}" r="4.6" fill="#b8251e" stroke="#ffffff" stroke-width="1.4"/>')
    dt_s = f"{ath_pair['time_err_sec']:+.0f}s"
    anc_m = "end" if xa > ml + pw * 0.56 else "start"
    lx_m = xa - 5 if anc_m == "end" else xa + 5
    ly_m = max(mt + 18, ya - 18)
    parts.append(f'<line x1="{xa:.1f}" y1="{ya-4:.1f}" x2="{xa:.1f}" y2="{ly_m+3:.1f}" stroke="#b8251e" stroke-width="0.9"/>')
    parts.append(f'<text x="{lx_m:.1f}" y="{ly_m:.1f}" text-anchor="{anc_m}" font-family="IBM Plex Sans,sans-serif" font-size="6.9" font-weight="700" fill="#b8251e" paint-order="stroke" stroke="#faf8f3" stroke-width="3.0">{ath_pair["display_name"].split()[0][0]}. {ath_pair["display_name"].split()[-1]} #{ath_pair["act_place"]} ({dt_s})</text>')

    parts.append("</svg>")
    return "".join(parts)

# ==============================================================================
# SVG: AQUINAS PLACE SURGE SLOPEGRAPH (PAGE 2)
# ==============================================================================
def build_aq_slope_svg(W=735, H=255):
    rows = sorted(AQ, key=lambda a: a["act_place"] / a["act_field_size"])
    ml, mr, mt, mb = 44, 44, 24, 20
    pw, ph = W - ml - mr, H - mt - mb
    x_l, x_r = ml + 150, W - mr - 170
    def sy(pct): return mt + pct * ph

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;height:auto">']
    parts.append(f'<rect x="{x_l}" y="{mt}" width="{x_r-x_l}" height="{ph}" fill="#faf8f3" rx="3"/>')
    parts.append(f'<line x1="{x_l}" y1="{mt}" x2="{x_l}" y2="{H-mb}" stroke="#cbd5e1" stroke-width="1.2"/>')
    parts.append(f'<line x1="{x_r}" y1="{mt}" x2="{x_r}" y2="{H-mb}" stroke="#132c54" stroke-width="1.4"/>')
    parts.append(f'<text x="{x_l}" y="{mt-8}" text-anchor="middle" font-family="IBM Plex Sans,sans-serif" font-size="7.8" font-weight="700" fill="#475569">PRE-RACE FORECAST PERCENTILE</text>')
    parts.append(f'<text x="{x_r}" y="{mt-8}" text-anchor="middle" font-family="IBM Plex Sans,sans-serif" font-size="7.8" font-weight="700" fill="#132c54">ACTUAL CEDARVILLE FINISH PERCENTILE</text>')

    for pct in [0.0, 0.25, 0.50, 0.75, 1.0]:
        yv = sy(pct)
        parts.append(f'<line x1="{x_l}" y1="{yv:.1f}" x2="{x_r}" y2="{yv:.1f}" stroke="#e7e3d9" stroke-width="0.65"/>')
        lbl = f"Top {int(pct*100)}%" if pct > 0 else "#1"
        parts.append(f'<text x="{(x_l+x_r)/2:.1f}" y="{yv-2:.1f}" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="6.4" fill="#94a3b8">{lbl}</text>')

    pts_l, pts_r = [], []
    for a in rows:
        pl_pct = min(0.96, max(0.03, a["pred_place"] / a["act_field_size"]))
        ac_pct = min(0.96, max(0.03, a["act_place"] / a["act_field_size"]))
        pts_l.append([sy(pl_pct), a])
        pts_r.append([sy(ac_pct), a])

    def spread(arr, min_gap=16.5):
        arr.sort(key=lambda x: x[0])
        for _ in range(18):
            for i in range(1, len(arr)):
                if arr[i][0] - arr[i - 1][0] < min_gap:
                    mid = 0.5 * (arr[i][0] + arr[i - 1][0])
                    arr[i - 1][0] = mid - min_gap / 2
                    arr[i][0] = mid + min_gap / 2
            for item in arr:
                item[0] = max(mt + 5, min(H - mb - 5, item[0]))
        return {item[1]["id"]: item[0] for item in arr}

    yl_lbl = spread([list(x) for x in pts_l])
    yr_lbl = spread([list(x) for x in pts_r])

    for a in rows:
        pl_pct = min(0.96, max(0.03, a["pred_place"] / a["act_field_size"]))
        ac_pct = min(0.96, max(0.03, a["act_place"] / a["act_field_size"]))
        y1, y2 = sy(pl_pct), sy(ac_pct)
        improved = a["act_place"] < a["pred_place"]
        col = "#0d7a47" if improved else "#64748b"
        sw = "2.1" if a["act_is_aa"] else "1.4"
        parts.append(f'<line x1="{x_l}" y1="{y1:.1f}" x2="{x_r}" y2="{y2:.1f}" stroke="{col}" stroke-width="{sw}" opacity="0.88"/>')
        parts.append(f'<circle cx="{x_l}" cy="{y1:.1f}" r="3.0" fill="#ffffff" stroke="{col}" stroke-width="1.3"/>')
        parts.append(f'<circle cx="{x_r}" cy="{y2:.1f}" r="3.6" fill="{col}" stroke="#ffffff" stroke-width="1.0"/>')
        ly1, ly2 = yl_lbl[a["id"]], yr_lbl[a["id"]]
        star = " ★AA" if a["act_is_aa"] else ""
        parts.append(f'<text x="{x_l-8}" y="{ly1+2.6:.1f}" text-anchor="end" font-family="IBM Plex Sans,sans-serif" font-size="7.5" font-weight="{"700" if a["act_is_aa"] else "500"}" fill="#334155">{esc(a["display_name"])} <tspan font-family="IBM Plex Mono,monospace" fill="#646a76">#{a["pred_place"]:.0f}</tspan></text>')
        parts.append(f'<text x="{x_r+8}" y="{ly2+2.6:.1f}" font-family="IBM Plex Sans,sans-serif" font-size="7.5" font-weight="{"700" if a["act_is_aa"] else "600"}" fill="{col}">#{a["act_place"]}/{a["act_field_size"]} {esc(a["display_name"])}{star} <tspan font-family="IBM Plex Mono,monospace" font-size="6.8">({a["place_err"]:+.0f})</tspan></text>')

    parts.append("</svg>")
    return "".join(parts)

# ==============================================================================
# SVG: NATIONAL SCATTER, RESIDUAL KDE, & AA CALIBRATION (PAGES 14 & 15)
# ==============================================================================
def build_national_scatter_svg(W=370, H=252):
    ml, mr, mt, mb = 40, 14, 22, 32
    pw, ph = W - ml - mr, H - mt - mb
    tmin, tmax = 240.0, 1620.0
    def sx(t): return ml + (min(tmax, max(tmin, t)) - tmin) / (tmax - tmin) * pw
    def sy(t): return H - mb - (min(tmax, max(tmin, t)) - tmin) / (tmax - tmin) * ph
    dist_col = {1000: "#94a3b8", 2000: "#2b6cb0", 3000: "#0d7a47", 4000: "#7e57c2", 5000: "#d97706"}

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;height:auto">']
    parts.append(f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="#faf8f3" rx="3"/>')
    for m in [5, 10, 15, 20, 25]:
        t = m * 60.0
        xv, yv = sx(t), sy(t)
        parts.append(f'<line x1="{xv:.1f}" y1="{mt}" x2="{xv:.1f}" y2="{H-mb}" stroke="#e7e3d9" stroke-width="0.6"/>')
        parts.append(f'<line x1="{ml}" y1="{yv:.1f}" x2="{W-mr}" y2="{yv:.1f}" stroke="#e7e3d9" stroke-width="0.6"/>')
        parts.append(f'<text x="{xv:.1f}" y="{H-mb+11}" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="6.8" fill="#646a76">{m}:00</text>')
        parts.append(f'<text x="{ml-5}" y="{yv+2.4:.1f}" text-anchor="end" font-family="IBM Plex Mono,monospace" font-size="6.8" fill="#646a76">{m}:00</text>')

    parts.append(f'<line x1="{sx(tmin):.1f}" y1="{sy(tmin):.1f}" x2="{sx(tmax):.1f}" y2="{sy(tmax):.1f}" stroke="#132c54" stroke-width="1.2" stroke-dasharray="4,3"/>')
    parts.append(f'<text x="{sx(1450):.1f}" y="{sy(1510):.1f}" font-family="IBM Plex Sans,sans-serif" font-size="6.6" font-weight="700" fill="#132c54" text-anchor="end">Perfect Forecast (y = x)</text>')
    parts.append(f'<text x="{W-mr-4}" y="{H-mb-6}" text-anchor="end" font-family="IBM Plex Sans,sans-serif" font-size="6.5" font-weight="600" fill="#0d7a47">Below line = Ran FASTER than Forecast</text>')

    for a in ATHS:
        if a["is_dop"] and a["home_school"] == "Aquinas Academy": continue
        parts.append(f'<circle cx="{sx(a["pred_time_sec"]):.1f}" cy="{sy(a["act_time_sec"]):.1f}" r="1.15" fill="{dist_col.get(a["dist_m"], "#64748b")}" opacity="0.32"/>')
    for a in AQ:
        parts.append(f'<circle cx="{sx(a["pred_time_sec"]):.1f}" cy="{sy(a["act_time_sec"]):.1f}" r="3.2" fill="#b8251e" stroke="#ffffff" stroke-width="1.0"/>')

    parts.append(f'<text x="{ml+pw/2:.1f}" y="{H-4}" text-anchor="middle" font-family="IBM Plex Sans,sans-serif" font-size="7.0" fill="#475569">Pre-Race Predicted Time (min) · Overall r = 0.938 (n = 2,424)</text>')
    parts.append(f'<text x="11" y="{mt+ph/2:.1f}" text-anchor="middle" transform="rotate(-90 11 {mt+ph/2:.1f})" font-family="IBM Plex Sans,sans-serif" font-size="7.0" fill="#475569">Actual Cedarville Time (min)</text>')
    parts.append("</svg>")
    return "".join(parts)

def build_residual_kde_svg(W=350, H=252):
    ml, mr, mt, mb = 22, 16, 28, 34
    pw, ph = W - ml - mr, H - mt - mb
    xs = np.linspace(-100, 100, 120)
    def sx(v): return ml + (v + 100.0) / 200.0 * pw
    def kde(vals, bw):
        arr = np.array(vals, dtype=float)
        dens = np.zeros_like(xs)
        for v in arr: dens += np.exp(-0.5 * ((xs - v) / bw) ** 2)
        return dens / (len(arr) * bw * math.sqrt(2 * math.pi))

    d_nat = kde([a["time_err_sec"] for a in OTHER if -120 <= a["time_err_sec"] <= 120], 14.0)
    d_dop = kde([a["time_err_sec"] for a in DOP if -120 <= a["time_err_sec"] <= 120], 15.0)
    d_aq = kde([a["time_err_sec"] for a in AQ], 16.0)
    ymax = max(float(d_nat.max()), float(d_dop.max()), float(d_aq.max())) * 1.15
    def sy(y): return H - mb - (y / ymax) * ph

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;height:auto">']
    parts.append(f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="#faf8f3" rx="3"/>')
    for v in [-80, -60, -40, -20, 0, 20, 40, 60, 80]:
        xv = sx(v)
        parts.append(f'<line x1="{xv:.1f}" y1="{mt}" x2="{xv:.1f}" y2="{H-mb}" stroke="{"#94a3b8" if v==0 else "#e7e3d9"}" stroke-width="{"1.2" if v==0 else "0.6"}"/>')
        parts.append(f'<text x="{xv:.1f}" y="{H-mb+11}" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="6.8" fill="#646a76">{v:+d}s</text>')
    def area_path(dens, col, fill_op, sw):
        pts = [f"{sx(x):.1f},{sy(y):.1f}" for x, y in zip(xs, dens)]
        return f'<path d="M{sx(xs[0]):.1f},{H-mb:.1f} L{" L".join(pts)} L{sx(xs[-1]):.1f},{H-mb:.1f} Z" fill="{col}" opacity="{fill_op}"/><path d="M{" L".join(pts)}" fill="none" stroke="{col}" stroke-width="{sw}"/>'
    parts.append(area_path(d_nat, "#475569", "0.14", "1.6"))
    parts.append(area_path(d_dop, "#5b359a", "0.16", "1.8"))
    parts.append(area_path(d_aq, "#b8251e", "0.20", "2.1"))
    for med, col, lbl, y_off in [
        (8.6, "#475569", "Rest of Nation: +8.6s", mt + 14),
        (-18.7, "#5b359a", "Pittsburgh CYO: -18.7s", mt + 28),
        (-24.0, "#b8251e", "Aquinas Academy: -24.0s", mt + 42),
    ]:
        xm = sx(med)
        parts.append(f'<line x1="{xm:.1f}" y1="{mt}" x2="{xm:.1f}" y2="{H-mb}" stroke="{col}" stroke-width="1.1" stroke-dasharray="3,2"/>')
        parts.append(f'<text x="{ml+8}" y="{y_off}" font-family="IBM Plex Sans,sans-serif" font-size="7.2" font-weight="700" fill="{col}">● {lbl}</text>')
    parts.append(f'<text x="{ml+pw/2:.1f}" y="{H-4}" text-anchor="middle" font-family="IBM Plex Sans,sans-serif" font-size="7.0" fill="#475569">Actual − Predicted Time (sec) · Negative = Beat Forecast</text>')
    parts.append(f'<text x="{ml+4}" y="{mt-7}" font-family="IBM Plex Sans,sans-serif" font-size="7.0" font-weight="700" fill="#b8251e">32.6s Western PA Hill-Strength Swing vs. National Field!</text>')
    parts.append("</svg>")
    return "".join(parts)

def build_aa_calibration_svg(W=350, H=205):
    aa = [a for a in ATHS if a["event_num"] not in (1, 2, 5) and a["act_age_place"] is not None]
    buckets = [(0, 10), (10, 25), (25, 50), (50, 75), (75, 90), (90, 101)]
    pts = []
    for lo, hi in buckets:
        sub = [a for a in aa if lo <= a["pred_aa_prob"] < hi]
        if sub:
            pts.append((float(np.mean([a["pred_aa_prob"] for a in sub])), 100.0 * float(np.mean([1.0 if a["act_is_aa"] else 0.0 for a in sub])), len(sub)))
    ml, mr, mt, mb = 42, 18, 22, 32
    pw, ph = W - ml - mr, H - mt - mb
    def sx(v): return ml + (v / 100.0) * pw
    def sy(v): return H - mb - (v / 100.0) * ph
    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;height:auto">']
    parts.append(f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="#faf8f3" rx="3"/>')
    for v in [0, 25, 50, 75, 100]:
        xv, yv = sx(v), sy(v)
        parts.append(f'<line x1="{xv:.1f}" y1="{mt}" x2="{xv:.1f}" y2="{H-mb}" stroke="#e7e3d9" stroke-width="0.65"/>')
        parts.append(f'<line x1="{ml}" y1="{yv:.1f}" x2="{W-mr}" y2="{yv:.1f}" stroke="#e7e3d9" stroke-width="0.65"/>')
        parts.append(f'<text x="{xv:.1f}" y="{H-mb+11}" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="6.8" fill="#646a76">{v}%</text>')
        parts.append(f'<text x="{ml-5}" y="{yv+2.4:.1f}" text-anchor="end" font-family="IBM Plex Mono,monospace" font-size="6.8" fill="#646a76">{v}%</text>')
    parts.append(f'<line x1="{sx(0):.1f}" y1="{sy(0):.1f}" x2="{sx(100):.1f}" y2="{sy(100):.1f}" stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="4,3"/>')
    parts.append(f'<polyline points="{" ".join(f"{sx(p):.1f},{sy(a):.1f}" for p, a, _ in pts)}" fill="none" stroke="#132c54" stroke-width="2.1"/>')
    for p, a, n in pts:
        cx, cy = sx(p), sy(a)
        r = 3.2 + 2.4 * math.sqrt(n / 1451.0)
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="#0d7a47" stroke="#ffffff" stroke-width="1.2"/>')
        if p < 5: lx, ly, anc = cx + 6, cy - 8, "start"
        elif a >= p: lx, ly, anc = cx - 4, cy - 9, "middle"
        else: lx, ly, anc = cx + 6, cy + 14, "middle"
        lx = min(W - mr - 24, max(ml + 18, lx))
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anc}" font-family="IBM Plex Mono,monospace" font-size="6.4" font-weight="700" fill="#132c54" paint-order="stroke" stroke="#faf8f3" stroke-width="3">{a:.0f}% <tspan fill="#646a76" font-weight="400">(n={n})</tspan></text>')
    parts.append(f'<text x="{ml+4}" y="{mt-7}" font-family="IBM Plex Sans,sans-serif" font-size="7.0" font-weight="700" fill="#132c54">Brier Score = {SUMMARY["aa_brier_score"]:.4f} · 7/7 (100%) Pgh CYO ≥50% Locks Won AA!</text>')
    parts.append(f'<text x="{ml+pw/2:.1f}" y="{H-4}" text-anchor="middle" font-family="IBM Plex Sans,sans-serif" font-size="7.0" fill="#475569">Pre-Race Predicted All-American Top-25 Probability</text>')
    parts.append(f'<text x="11" y="{mt+ph/2:.1f}" text-anchor="middle" transform="rotate(-90 11 {mt+ph/2:.1f})" font-family="IBM Plex Sans,sans-serif" font-size="7.0" fill="#475569">Actual Top-25 Hit Rate</text>')
    parts.append("</svg>")
    return "".join(parts)

# ==============================================================================
# BUILD INDIVIDUAL KEEPSAKE PAGES FOR ALL 11 AQUINAS ACADEMY RUNNERS (PAGES 3–13)
# ==============================================================================
PROFILES = {
    "Linus Gruber": {
        "subtitle": "National Bronze Medalist (#3 Age-7) & Boys 6–8 Anchor",
        "kicker": "★ #3 IN THE NATION FOR AGE 7 (BRONZE MEDAL) · #2 CYO AGE-7 · DIOCESAN CHAMPION",
        "headline": "Blasted 6:33/mi Pace to Claim #3 in America for Age 7!",
        "copy": "Capping a dominant 2nd-grade season that included winning the Oct 17 Pittsburgh Diocesan Championship (#1/83), <b>Linus Gruber</b> unleashed an electric <b>8:08.582 (6:33/mi)</b> at Cedarville — crushing our 8:38.7 projection by <b>30.1 seconds</b> and surging 17.4 places to <b>#30/220 overall</b> and <b>#3 of 64 Age-7 boys in the nation</b>! He anchored Aquinas's 1–2 punch with Diego Victor to lead Pittsburgh CYO Boys 6–8 to a <b>56–56 tie for 2nd / #3 CYO National Trophy</b>.",
        "boxes": [("#3 / 64", "Age-7 National (★AA)", "g"), ("-30.1s", "Faster Than Forecast", "g"), ("6:33/mi", "2K PR (-1:09/mi Drop)", "r"), ("#5 / 55", "CYO Overall (#3 Team)", "")],
        "right_mode": "leaderboard",
        "pace_sub": "-1:09/mi season drop (7:42 → 6:33)!",
        "nat_tag": "2K PR!",
        "log_sub": "Oct 17 Diocesan Champion (#1/83) → Cedarville National Bronze!",
        "callouts": [
            ("green", "<b>National Podium Pedigree:</b> Finished <b>56.7 seconds ahead</b> of the official Age-7 All-American #25 cutline (9:05.3), #2 among all CYO 7-year-olds nationwide, and beat 90 of the 120 older 8-year-old boys in Event 4!"),
            ("", "<b>Season-Long Rocket Trajectory:</b> Opened on Aug 25 at Seelos in 9:33.50 (7:42/mi), broke 7:00/mi to win Diocesans (6:58/mi), then shaved another <b>25 sec/mi</b> off on Cedarville's grass to hit <b>6:33/mi</b>!"),
            ("crimson", "<b>2027 Age-8 Outlook:</b> Returning as an 8-year-old next fall with sub-6:35/mi speed already in hand puts Linus squarely in the hunt for an <b>Overall Event 4 National Championship medal</b> in 2027!"),
        ],
    },
    "Diego Victor": {
        "subtitle": "National All-American (#9 Age-6) & CYO Podium Closer",
        "kicker": "★ TOP-10 SINGLE-YEAR NATIONAL ALL-AMERICAN · #3 CYO AGE-6 BRONZE · 5TH-MAN HERO",
        "headline": "Joined Late. Ran an 18.5-Second 2K PR. Delivered a CYO Trophy.",
        "copy": "Added as Pittsburgh CYO's vital 5th runner in Boys 6–8, 6-year-old <b>Diego Victor</b> ran the race of his life on Cedarville's grass: <b>9:22.369 (7:33/mi)</b> — smashing our 9:46.3 pre-race projection by <b>23.9 seconds</b> and beating his previous 2K PR (9:40.86 at Seelos #2) by <b>18.5 seconds</b>! He finished <b>#9 in the nation</b> among Age-6 boys (within 0.7 places of our #8.3 forecast and just 6.4s shy of #7!) and completed Pittsburgh CYO's 5-boy scoring squad for a <b>56–56 tie for 2nd / #3 CYO National Trophy</b>.",
        "boxes": [("#9 / 36", "Age-6 National (★AA)", "r"), ("-23.9s", "Faster Than Forecast", "g"), ("7:33/mi", "2K PR (vs 7:52 Pred)", ""), ("#3 CYO", "56-Pt Team Trophy!", "r")],
        "right_mode": "leaderboard",
        "pace_sub": "-1:22/mi season drop (8:55 → 7:33)!",
        "nat_tag": "2K PR!",
        "log_sub": 'Entered at FinishTiming as "Victor Diego" (Bib verified)',
        "extra_ev4_team": True,
        "callouts": [
            ("crimson", "<b>Diego's Scouting Breakdown:</b><br><br><b>• Pinpoint Place Calibration:</b> Pre-race model projected Overall <b>#131.1</b> &amp; Age-6 <b>#8.3</b>; Diego ran Overall <b>#133 / 220</b> (+1.9 pl) &amp; Age-6 <b>#9 / 36</b> (+0.7 pl) — beating #4-seeded Hampton Hill (Grassroots KY, 9:30.5) by 8.1 seconds!<br><br><b>• Massive Margin Over #25 Cutline:</b> Finished <b>1:17.3 ahead</b> of the official Age-6 All-American #25 cutline (10:39.7).<br><br><b>• 1st-Grade Upside:</b> Dropping from 8:55/mi (Aug 25) to 7:33/mi (Nov 21) sets Diego up as a top-5 Age-7 national contender in 2027!"),
        ],
    },
    "Cora Donahue": {
        "subtitle": "+51-Place National Surge & #3 CYO Podium Scorer",
        "kicker": "10-RACE IRONWOMAN · -32.1s BEAT · -1:04.2 3K PR · #6 CYO AGE-9",
        "headline": "Faster Per Mile Over 3K Than Her 1.5-Mile Diocesan Podium!",
        "copy": "Leading all Aquinas Academy 9–10 girls on the national stage, 3rd-grader <b>Cora Donahue</b> hammered <b>13:46.892 (7:24/mi)</b> — beating our 14:19.0 pre-race projection by <b>32.1 seconds</b>, surging an astonishing <b>+51.3 overall places</b> (#136.3 &#8594; #85/244), and slashing <b>1:04.2</b> off her Sept 12 Oakland Catholic 3K (14:51.14)! She finished <b>#30/104 Age-9</b> (just 7.7 seconds shy of National All-American!) and scored #2 for <b>Pittsburgh CYO A's #3 CYO Podium (69 pts)</b>.",
        "boxes": [("-32.1s", "Faster Than Forecast", "g"), ("+51.3 pl", "Ov Surge (#136→#85)", "g"), ("#30 / 104", "Age-9 (#6 CYO Age-9)", "r"), ("#3 CYO", "Pgh A (1 pt from #2!)", "")],
        "right_mode": "pack",
        "pace_sub": "-1:06/mi drop · Purple = 3K",
        "nat_tag": "3K PR!",
        "log_sub": "11 races total · Purple rows = full 3,000m distance",
        "callouts": [
            ("green", "<b>Remarkable Distance Resilience:</b> At Oct 17 Diocesans (1.50 mi), Cora took #3/107 at <b>7:25/mi</b>. Stepping up 600m to a full 3,000m at Cedarville, she ran <b>7:24/mi</b> — actually <i>accelerating</i> her mile pace over 25% more distance!"),
            ("", "<b>Pittsburgh CYO A Team Anchor:</b> As Pittsburgh CYO A's #2 scorer (#13 CYO overall), Cora helped Pgh CYO A finish <b>#7 in the Nation</b> (up 6 spots from #12.8 pred) and <b>#3 CYO Podium (69 pts)</b> — just <b>1 point</b> behind #2 Toledo CYO A (68 pts)!"),
            ("crimson", "<b>2027 Age-10 All-American Lock:</b> Missing the Age-9 #25 AA cutline (13:39.2) by just <b>7.7 seconds</b> puts Cora right at the front of the 2027 Age-10 National All-American board!"),
        ],
    },
    "Angela Gallagher": {
        "subtitle": "+38-Place Surge & Pittsburgh CYO B Top-3 Scorer",
        "kicker": "CONSISTENCY MACHINE · -17.9s BEAT · -12.2s 3K PR · #9 CYO AGE-9",
        "headline": "Sub-7:35/mi 3K Breakthrough — 38 Places Ahead of Forecast!",
        "copy": "Fresh off a remarkably consistent fall where she placed top-7 in six straight Western PA meets, 4th-grader <b>Angela Gallagher</b> delivered her fastest 3K of the year at Cedarville: <b>14:04.23 (7:33/mi)</b> — beating our 14:22.2 projection by <b>17.9 seconds</b>, vaulting <b>+38.3 overall places</b> (#142.3 &#8594; #104/244), and improving <b>12.2 seconds</b> over her strong Sept 12 Oakland Catholic 3K (14:16.40)! She placed <b>#38/104 Age-9</b> and <b>#9 CYO Age-9</b>.",
        "boxes": [("-17.9s", "Faster Than Forecast", "g"), ("+38.3 pl", "Ov Surge (#142→#104)", "g"), ("7:33/mi", "3K PR (-12.2s drop)", "r"), ("#19 / 52", "CYO (#4 Team 77 pts)", "")],
        "right_mode": "pack",
        "pace_sub": "Rock-steady 7:30s all season · Purple = 3K",
        "nat_tag": "3K PR!",
        "log_sub": "Top-10 in every single 2026 Western PA race!",
        "callouts": [
            ("green", "<b>Built for Championship 3K Racing:</b> Running 7:33/mi at Cedarville was <b>12 sec/mi faster</b> than her Oct 17 Diocesan pace (7:45/mi) despite running 600 meters farther — proving her aerobic strength shines on fast courses!"),
            ("", "<b>Powering Pittsburgh CYO B's Tight Pack:</b> Scoring #3 for Pittsburgh CYO B (#19 CYO overall), Angela helped Pgh B post a razor-tight <b>0:48 1–5 spread</b> for <b>#4 CYO (77 pts)</b> and <b>#13 Nationally</b> (4 spots ahead of forecast!)."),
            ("crimson", "<b>2027 Age-10 Outlook:</b> With a 14:04 3K PR already logged as a 9-year-old, typical 1-year CCCNYC maturation (~35–40s) projects Angela straight into the low-13:20s next fall — prime Age-10 All-American territory!"),
        ],
    },
    "Marcela Victor": {
        "subtitle": "24-Second Breakthrough & +35-Place National Surge",
        "kicker": "MASSIVE 3K PERSONAL BEST · 1:05.3 FASTER THAN PRIOR 3K · +35.1 PLACES AHEAD OF FORECAST",
        "headline": "1:17/Mile Season Transformation Capped by a Sub-8:00/mi 3K!",
        "copy": "Stepping up to the 3,000m national championship distance as a 9-year-old 3rd-grader, <b>Marcela Victor</b> blasted <b>14:37.64 (7:51/mi)</b> — beating our 15:01.7 pre-race forecast by <b>24.0 seconds</b>, surging <b>+35.1 overall places</b> (#179.1 &#8594; #144/244) and <b>+15.9 Age-9 places</b> (#72.9 &#8594; #57/104), and obliterating her earlier Sept 12 Oakland Catholic 3K (15:42.96) by <b>1:05.3</b>! Running as Pittsburgh CYO B's #6 displacer (#28 CYO / #14 CYO Age-9), she directly displaced Toledo CYO A's #5–#7 runners.",
        "boxes": [("-24.0s", "Faster Than Forecast", "g"), ("+35.1 pl", "Ov Surge (#179→#144)", "g"), ("-1:05.3", "3K Season PR Drop!", "r"), ("#57 / 104", "Age-9 (#14 CYO Age-9)", "")],
        "right_mode": "pack",
        "pace_sub": "-1:17/mi drop · Purple = 3K",
        "nat_tag": "3K PR!",
        "log_sub": "Purple rows = full 3,000m championship distance",
        "callouts": [
            ("green", "<b>Endurance Leap (2K &#8594; 3K):</b> At the Oct 17 Diocesan Championship (1.50 mi), Marcela ran <b>7:45/mi</b>. Adding a full extra 600 meters at Cedarville Nationals, she held <b>7:51/mi</b> — only <b>6 sec/mi</b> of fade over 25% more distance (far stronger endurance than the typical 18–22 sec/mi youth 9-year-old fade!)."),
            ("", "<b>Pittsburgh CYO B Team Impact:</b> Pittsburgh CYO B finished <b>#4 in CYO (77 pts)</b> — just <b>8 points behind Pittsburgh CYO A (#3 CYO Podium, 69 pts)</b> and crushing #5 Phila. CYO White (151 pts) &amp; #6 LA-CYO A (152 pts) by 74+ points! Marcela's #25 CYO team-score spot displaced Toledo CYO A's 5th–7th runners (27–28–29)."),
            ("crimson", "<b>2027 Age-10 Outlook:</b> Returning CCCNYC veterans improve a median <b>13.4 sec/km (~40s over 3K)</b> from age 9 to age 10 — putting Marcela on a ~13:55–14:00 3K trajectory next fall!"),
        ],
    },
    "Noah Malone": {
        "subtitle": "Breakout National All-American (#14 Age-11) & +70-Place Surge!",
        "kicker": "★ NATIONAL ALL-AMERICAN (#14 AGE-11 / 160) · #2 CYO AGE-11 · BIGGEST AQUINAS PLACE SURGE (+70.1 PL!)",
        "headline": "From 27% Underdog Odds to #14 in the Nation in 11:33.1!",
        "copy": "Delivering the biggest upset breakout of Aquinas Academy's entire meet, 6th-grader <b>Noah Malone</b> flew across Cedarville's 3K in <b>11:33.07 (6:12/mi)</b> — crushing our 11:59.5 projection by <b>26.4 seconds</b> and skyrocketing <b>+70.1 overall places</b> (#130.1 &#8594; #60/373) in the deepest race of the entire championship! Carrying just 26.9% pre-race All-American odds, Noah smashed through to <b>#14/160 Age-11 National All-American</b> and <b>#2 CYO Age-11</b>!",
        "boxes": [("#14 / 160", "Age-11 National (★AA)", "g"), ("+70.1 pl", "Biggest Place Surge!", "g"), ("6:12/mi", "3K PR (-26.4s Beat)", "r"), ("#2 CYO", "Silver & #6 National!", "")],
        "right_mode": "leaderboard",
        "pace_sub": "-1:19/mi season drop (7:31 → 6:12)!",
        "nat_tag": "3K PR!",
        "log_sub": "Purple rows = 3,000m · Runner-up in 3 straight Oct meets!",
        "callouts": [
            ("green", "<b>Massive All-American Breakthrough:</b> Finished <b>9.2 seconds ahead</b> of the official Age-11 All-American #25 cutline (11:42.3) and improved <b>43.0 seconds</b> over his Sept 12 Oakland Catholic 3K (12:16.08) and <b>21.9s</b> over his Oct 10 Pumpkins 3K!"),
            ("", "<b>Pittsburgh CYO 11–12B Silver Medal Engine:</b> Placing <b>#9 CYO overall</b>, Noah led Pittsburgh CYO Boys 11–12 to a stunning <b>#6 in the Nation</b> (jumping 6+ places over our #12.3 forecast!) and <b>#2 CYO Silver (51 pts)</b> behind Phila. CYO Red!"),
            ("crimson", "<b>2027 Age-12 Outlook:</b> Dropping from 7:31/mi in early September to 6:12/mi in November shows massive aerobic upside — Noah projects as a sub-11:00 top-10 national contender in Boys 11–12 next year!"),
        ],
    },
    "Joey Edwards": {
        "subtitle": "Pinpoint Model Precision & CYO Silver Team Contributor",
        "kicker": "#2 CYO SILVER TEAM · #6 NATIONAL SQUAD · PINPOINT PLACE ACCURACY (+1.3 PLACES!)",
        "headline": "Finished #156 of 373 — Within 1.3 Places of Forecast on CYO Silver Squad!",
        "copy": "Completing a breakout 6th-grade campaign where he shaved nearly a full minute per mile from August (7:22/mi) to his #4/85 finish at Diocesans (6:23/mi), <b>Joey Edwards</b> battled the meet's largest field (373 boys!) to finish <b>12:31.32 (6:43/mi)</b> — landing at <b>#156/373 overall</b> (literally <b>1.3 places</b> from our #154.7 forecast!) and <b>#23/67 CYO</b>, helping Pittsburgh CYO Boys 11–12 win <b>CYO Silver (#2)</b> and <b>#6 in the Nation</b>!",
        "boxes": [("12:31.3", "6:43/mi (3K Nationals)", ""), ("#156 / 373", "vs #154.7 Pred (+1.3!)", "g"), ("#23 / 67", "CYO Overall (Beat #25)", "g"), ("#2 CYO", "Silver & #6 National!", "r")],
        "right_mode": "pack",
        "pace_sub": "-0:59/mi peak drop (Aug → Dio) · Purple = 3K",
        "nat_tag": "Nationals",
        "log_sub": "8 regular-season meets + Cedarville (largest field: 373 boys!)",
        "callouts": [
            ("green", "<b>Beat CYO Forecast in the Meet's Deepest Race:</b> Event 9 Boys 11–12 was the single largest race at Cedarville (373 finishers, 41 teams). Joey beat his pre-race CYO rank forecast (#25.1 &#8594; <b>#23</b>) and finished well inside the top half of the nation!"),
            ("", "<b>59-Second/Mile Season Surge:</b> Started the fall at 7:22/mi (Seelos) and 7:10/mi (Oakland Catholic 3K, 13:21.66) — his 12:31.32 at Cedarville was still <b>50.3 seconds faster</b> than his September 3K!"),
            ("crimson", "<b>Moving Up to 4K in 2027:</b> With 8 hard 2.8K–3K races already under his belt (including a 12:08 3K PR at Pumpkins and #4 at Diocesans), Joey enters 7th-grade Varsity 4K next fall with major championship experience!"),
        ],
    },
    "Katalina Barnett": {
        "subtitle": "-50.5s Biggest Aquinas Beat & Sub-7:00/mi 4K Breakthrough!",
        "kicker": "BIGGEST TIME BEAT ON AQUINAS (-50.5s!) · SUB-7:00/MI OVER 4,000m · #2 CYO SILVER TEAM",
        "headline": "Stepped Up 1,000 Meters to 4K — And Ran FASTER Per Mile (6:57/mi)!",
        "copy": "Delivering the single biggest time beat of any Aquinas Academy runner at Cedarville, 7th-grader <b>Katalina Barnett</b> conquered the 4,000m championship course in <b>17:15.34 (6:57/mi)</b> — obliterating our 18:05.8 pre-race forecast by <b>50.5 seconds</b> and surging <b>+58.4 overall places</b> (#178.4 &#8594; #120/235)! She led all three Aquinas 13–14 girls, took <b>#14/38 CYO</b> (#9 CYO Age-13), and powered Pittsburgh CYO Girls 13–14 to <b>CYO National Silver (#2, 51 pts)</b>!",
        "boxes": [("-50.5s", "Biggest Aquinas Beat!", "g"), ("+58.4 pl", "Ov Surge (#178→#120)", "g"), ("6:57/mi", "Sub-7:00/mi Over 4K!", "r"), ("#2 CYO", "Silver Team (#14 CYO)", "")],
        "right_mode": "pack",
        "pace_sub": "-0:55/mi season drop (7:52 → 6:57/mi 4K!)",
        "nat_tag": "4K PR!",
        "log_sub": "First 4,000m race was faster per mile than EVERY 3K all fall!",
        "callouts": [
            ("green", "<b>Defied Riegel Fatigue Scaling:</b> Katalina's fastest regular-season pace was <b>7:00/mi</b> over 2,800m at Diocesans (#6/64). Adding <b>1,200 extra meters</b> at Cedarville, she ran <b>6:57/mi</b> — proving she is a true distance grinder!"),
            ("", "<b>#2 CYO Silver Medal Scorer:</b> As a core top-4 scorer for Pittsburgh CYO Girls 13–14 (#14 CYO, #9 CYO Age-13), Katalina helped Pittsburgh finish <b>#2 CYO Silver (51 pts)</b> behind Phila. CYO Black and beat its National forecast by 3 spots!"),
            ("crimson", "<b>2027 Age-14 Outlook:</b> Jumping +37.6 spots in Age-13 (#110.6 &#8594; #73/148) in her very first 4K signals a huge 8th-grade senior jump — targeting mid-16:00s and top-35 Age-14 national status next fall!"),
        ],
    },
    "Ciara McBride": {
        "subtitle": "-32.5s Beat, +43-Place Surge & CYO Silver Team Scorer",
        "kicker": "-32.5s FASTER THAN FORECAST · +43.2 OVERALL PLACES · #2 CYO SILVER TEAM",
        "headline": "Dropped Over a Minute Per Mile This Fall — Then Crushed Her First 4K!",
        "copy": "Pairing with teammate Katalina Barnett to give Aquinas Academy a ferocious 7th-grade 4K punch, <b>Ciara McBride</b> clocked <b>17:42.79 (7:08/mi)</b> at Cedarville — smashing our 18:15.3 projection by <b>32.5 seconds</b> and surging <b>+43.2 overall places</b> (#183.2 &#8594; #140/235)! Finishing <b>#19/38 CYO</b> and climbing <b>+26.9 Age-13 places</b> (#113.9 &#8594; #87/148), Ciara locked down crucial scoring points for <b>Pittsburgh CYO Girls 13–14's #2 CYO Silver finish</b>!",
        "boxes": [("-32.5s", "Faster Than Forecast", "g"), ("+43.2 pl", "Ov Surge (#183→#140)", "g"), ("7:08/mi", "4K Debut (-1:01/mi!)", "r"), ("#2 CYO", "Silver Team (#19 CYO)", "")],
        "right_mode": "pack",
        "pace_sub": "-1:01/mi drop (8:09 St. Kilian → 7:08 4K!)",
        "nat_tag": "4K PR!",
        "log_sub": "Huge late-season surge: 7:23 → 7:11 → 7:02 → 7:08 (4K!)",
        "callouts": [
            ("green", "<b>Elite 4K Conversion:</b> Held <b>7:08/mi</b> across 4,000 meters — within just <b>6 sec/mi</b> of her 2,800m Diocesan PR (7:02/mi, #8/64) and faster per mile than her 3K races at Oakland Catholic, North Area, Seelos, and Pumpkins!"),
            ("", "<b>Pack Running With Katalina:</b> Ciara and Katalina finished within 27 seconds of each other (#120 &amp; #140 overall; #14 &amp; #19 CYO), giving Pittsburgh CYO Girls 13–14 a super tight <b>1:04 1–5 spread</b> for CYO Silver!"),
            ("crimson", "<b>2027 Age-14 Outlook:</b> Dropping a full minute per mile in one season while still in 7th grade sets Ciara up to smash 17:00 for 4K as an 8th-grade leader next fall!"),
        ],
    },
    "Charlotte Austin": {
        "subtitle": "Closest Time Bullseye (+2.7s / 0.24%) & CYO Silver Team Senior",
        "kicker": "CLOSEST TIME PREDICTION ON AQUINAS (0.24% ERROR!) · +12.6 PLACES · #2 CYO SILVER TEAM",
        "headline": "9-Race Ironwoman Caps 8th Grade With a 0.24% Bullseye & CYO Silver!",
        "copy": "Running every single meet on the Aquinas Academy calendar from Aug 25 through Cedarville Nationals (10 races total!), 8th-grader <b>Charlotte Austin</b> posted <b>18:53.34 (7:36/mi)</b> over 4,000m — landing within <b>+2.7 seconds (0.24%)</b> of our 18:50.7 pre-race model projection (the most precise individual forecast on Aquinas!) while still outperforming her place forecast by <b>+12.6 overall spots</b> (#205.6 &#8594; #193/235) on Pittsburgh CYO's <b>#2 CYO Silver</b> Girls 13–14 squad!",
        "boxes": [("18:53.3", "7:36/mi (4K Nationals)", ""), ("+2.7s", "0.24% Model Bullseye!", "g"), ("+12.6 pl", "Ov Surge (#206→#193)", "g"), ("#2 CYO", "Silver Team (Age #74)", "r")],
        "right_mode": "pack",
        "pace_sub": "10 races total · Consistent mid-7:20s–7:40s all fall",
        "nat_tag": "4K Finish",
        "log_sub": "Ran all 9 regular-season meets + Cedarville 4K Nationals!",
        "callouts": [
            ("green", "<b>Beat Place Forecast on Tougher 4K Field:</b> While the national 13–14 Girls field ran +14.1s slower than projections, Charlotte held right on her predicted pace (+2.7s), letting her pass <b>12.6 runners</b> down the stretch (#206 &#8594; #193) and finish #74/87 Age-14!"),
            ("", "<b>Season Consistency & Leadership:</b> Took #2/15 at the Aquinas Invite, #14/53 at Oakland Catholic (7:21/mi), and #18/64 at Diocesans — anchoring a veteran 3-girl Aquinas 13–14 group that helped Pittsburgh CYO claim CYO Silver!"),
            ("crimson", "<b>High School 5K Ready (2027):</b> Completing all 10 races including a disciplined 4K National Championship finish gives Charlotte a rock-solid aerobic foundation stepping up to high school 5K XC next year!"),
        ],
    },
    "John Austin": {
        "subtitle": "Sub-6:00/mi 4K Flyer & CYO NATIONAL TEAM CHAMPION!",
        "kicker": "★ CYO NATIONAL TEAM CHAMPION (23 PTS) · SUB-6:00/MI OVER 4,000m (5:53/MI) · #8 CYO · #6 NATIONAL TEAM",
        "headline": "5:53/mi Across 4K to Power Pittsburgh CYO to the National CYO Crown!",
        "copy": "Capping a dominant 8th-grade season where he finished top-4 in every single Western PA meet, <b>John Austin</b> stepped up 1,200 meters to the 4,000m championship distance and blazed <b>14:37.860 (5:53/mi)</b> — beating our 14:50.4 projection by <b>12.5 seconds</b> and surging <b>+31.7 overall places</b> (#110.7 &#8594; #79/307)! He placed <b>#8/56 CYO</b> (<b>#5 CYO Age-14</b>) as a vital top-5 scorer on Pittsburgh CYO's runaway <b>CYO National Champion (23 pts)</b> and <b>#6-in-the-Nation</b> squad!",
        "boxes": [("#1 CYO", "NATIONAL CHAMP (23p)!", "g"), ("5:53/mi", "Sub-6:00/mi Over 4K!", "r"), ("-12.5s", "Faster Than Forecast", "g"), ("+31.7 pl", "Ov #79 · CYO #8!", "")],
        "right_mode": "pack",
        "pace_sub": "Sub-6:00/mi machine · Held 5:53/mi across 4,000m!",
        "nat_tag": "4K PR!",
        "log_sub": "Top-4 in EVERY 2026 meet → CYO National Team Champion!",
        "callouts": [
            ("green", "<b>Remarkable 4K Speed Endurance:</b> Ran <b>5:51/mi</b> over 2,800m at Diocesans (#4/108) and held <b>5:53/mi</b> over 4,000m at Cedarville — barely <b>2 seconds per mile</b> of fade across 43% more distance!"),
            ("", "<b>CYO National Championship Dominance:</b> Pittsburgh CYO Boys 13–14 crushed the CYO field with just <b>23 points</b> (avg 14:11, 1:02 spread) and finished <b>#6 in the entire United States (184 pts)</b> — beating their #8.3 national projection!"),
            ("crimson", "<b>High School 5K Launchpad (2027):</b> Holding 5:53/mi for 4K translates cleanly to a <b>~18:25–18:45 freshman 5K</b> right out of the gate — John enters high school XC as a bona fide varsity-ready distance runner!"),
        ],
    },
}

def build_runner_page(a, idx_1_to_11, page_num):
    prof = PROFILES[a["display_name"]]
    pre_a = pre_map[a["id"]]
    grade_str = f"Gr. {pre_a.get('grade')}" if pre_a.get("grade") else ""
    races = sorted(pre_a["races_2026"], key=lambda r: r["date"])

    # Right chart: leaderboard for All-Americans, pack S-curve for others
    if prof["right_mode"] == "leaderboard":
        right_title = f"Age-{a['age']} National Leaderboard ({a['dist_m']//1000}K)"
        right_sub = "○ Pred &#8594; ● Act"
        right_svg = build_age_leaderboard_svg(a)
    else:
        right_title = f"Ev {a['event_num']} {a['event_short']} Pack Surge"
        right_sub = "Aquinas Highlighted"
        right_svg = build_event_pack_svg(a)

    # Race log rows
    log_rows = []
    for r in races:
        same_d = (abs(r["dist_m"] - a["dist_m"]) <= 150) and a["dist_m"] >= 3000
        st = ' style="background:#f5f2fa"' if same_d else ""
        log_rows.append(
            f'<tr{st}><td class="mono nw">{r["date"][5:]}</td><td>{esc(short_meet(r["meet"]))}</td>'
            f'<td class="num mono">{r["dist_m"]}m</td><td class="num mono">{r["time_str"]}</td>'
            f'<td class="num mono">{r["pace_mi"]}/mi</td><td class="num mono nw">#{r["place"]}/{r["field_size"]}</td></tr>'
        )
    nat_fin_txt = f"Age #{a['act_age_place']}/{a['act_age_field_size']} ★AA" if a["act_is_aa"] else f"Ov #{a['act_place']} · Age #{a['act_age_place']}"
    pace_tag = f" ({prof['nat_tag']})" if "PR" in prof["nat_tag"] else ""
    log_rows.append(
        f'<tr class="row-victor"><td class="mono nw b">11-21</td><td class="b dop-txt">CCCNYC Nationals ({a["dist_m"]//1000}K)</td>'
        f'<td class="num mono b">{a["dist_m"]}m</td><td class="num mono b dop-txt">{a["act_time_exact"]}</td>'
        f'<td class="num mono b up-txt nw">{a["act_pace_mi"]}/mi{pace_tag}</td><td class="num mono b nw">{nat_fin_txt}</td></tr>'
    )

    # Optional Boys 6-8 5-runner team table on Diego's page!
    extra_team_block = ""
    if prof.get("extra_ev4_team"):
        ev4_dop = sorted([x for x in ATHS if x["event_num"] == 4 and x["is_dop"]], key=lambda x: x["act_place"])
        tr_list = []
        for ti, x in enumerate(ev4_dop, 1):
            is_aq = (x["home_school"] == "Aquinas Academy")
            cls = ' class="row-aa"' if is_aq else ""
            tr_list.append(
                f'<tr{cls}><td class="num mono b">#{ti}</td>'
                f'<td class="b">{esc(x["display_name"])}</td>'
                f'<td>{esc(short_school(x["home_school"]))}</td>'
                f'<td class="num mono">{x["age"]}</td>'
                f'<td class="num mono muted">{x["pred_time_str"]}</td>'
                f'<td class="num mono b">{x["act_time_str"]} ({x["act_pace_mi"]})</td>'
                f'<td class="num mono up-txt b">{x["time_err_sec"]:+.1f}s</td>'
                f'<td class="num mono">#{x["act_place"]} / CYO #{x["act_cyo_place"]}</td>'
                f'<td class="num mono b">#{x["act_age_place"]}/{x["act_age_field_size"]} {"★" if x["act_is_aa"] else ""}</td></tr>'
            )
        extra_team_block = f"""
  <div class="ed-sec">
    <div class="sec-bar navy">
      <span>The 5th-Man Hero Effect: Pittsburgh CYO Boys 6–8 Tied for 2nd in CYO (56–56) &amp; Won #3 Trophy!</span>
      <span class="sec-sub">Without Diego's late addition, Pgh CYO had 4 boys (incomplete) — with Diego, they crushed #4 Toledo CYO B by 59 pts!</span>
    </div>
    <table>
      <thead>
        <tr>
          <th class="num">Team #</th><th>Runner</th><th>Feeder School</th><th class="num">Age</th>
          <th class="num">Pred Time</th><th class="num">Actual (Pace)</th><th class="num">Δt</th>
          <th class="num">Ov / CYO</th><th class="num">Age Place</th>
        </tr>
      </thead>
      <tbody>{"".join(tr_list)}</tbody>
    </table>
  </div>"""

    # Hero 4 metric boxes
    hb_boxes = "".join(
        f'<div class="hb-box {cls}"><div class="v">{v}</div><div class="l">{l}</div></div>'
        for v, l, cls in prof["boxes"]
    )
    # Callouts
    callouts_html = "".join(f'<div class="callout {cls}">{txt}</div>' for cls, txt in prof["callouts"])
    log_tbl_class = ' class="tbl-tight"' if len(races) >= 9 else ""
    hdr_right_top = f'{a["act_time_str"]} ({a["act_pace_mi"]}/mi) · Age #{a["act_age_place"]}/{a["act_age_field_size"]}' if a["act_is_aa"] else f'{a["act_time_str"]} ({a["act_pace_mi"]}/mi) · Ov #{a["act_place"]}/{a["act_field_size"]}'

    return f"""
<!-- PAGE {page_num}: AQUINAS KEEPSAKE #{idx_1_to_11} — {a["display_name"].upper()} -->
<div class="page">
  <div class="pg-hdr">
    <div>
      <div class="eyebrow">AQUINAS ACADEMY KEEPSAKE DOSSIER #{idx_1_to_11} OF 11 · EVENT {a["event_num"]} · {a["event_name"].upper()}</div>
      <h1>{esc(a["display_name"])} (Age {a["age"]}) — {esc(prof["subtitle"])}</h1>
    </div>
    <div class="hdr-meta">
      <div class="mono b dop-txt">{hdr_right_top}</div>
      <div class="muted">Aquinas Academy ({grade_str}) · {esc(a["team"])}</div>
    </div>
  </div>

  <div class="hero-banner">
    <div>
      <div class="hb-kicker">{prof["kicker"]}</div>
      <div class="hb-title">{prof["headline"]}</div>
      <div class="hb-copy">{prof["copy"]}</div>
    </div>
    <div class="hb-metrics">{hb_boxes}</div>
  </div>

  <div class="split-62-38 ed-sec">
    <div>
      <div class="sec-bar subtle">
        <span>{esc(a["display_name"].split()[0])}'s Complete {len(races)+1}-Race 2026 Pace Progression</span>
        <span class="sec-sub">{prof["pace_sub"]}</span>
      </div>
      {build_season_pace_svg(a, nat_badge_lbl=prof["nat_tag"], color_main="#b8251e")}
    </div>
    <div>
      <div class="sec-bar subtle">
        <span>{right_title}</span>
        <span class="sec-sub">{right_sub}</span>
      </div>
      {right_svg}
    </div>
  </div>
  {extra_team_block}
  <div class="split-62-38">
    <div>
      <div class="sec-bar {"subtle" if extra_team_block else "navy"}">
        <span>{esc(a["display_name"])} · Complete {len(races)+1}-Race 2026 XC Log</span>
        <span class="sec-sub">{prof["log_sub"]}</span>
      </div>
      <table{log_tbl_class}>
        <thead><tr><th>Date</th><th>Meet</th><th class="num">Dist</th><th class="num">Time</th><th class="num">Pace</th><th class="num">Finish</th></tr></thead>
        <tbody>{"".join(log_rows)}</tbody>
      </table>
    </div>
    <div style="display:flex;flex-direction:column;gap:6px">
      {callouts_html}
    </div>
  </div>

  <div class="pfoot">
    <span>{esc(a["display_name"])} (Age {a["age"]} · Aquinas Academy · {esc(a["team"])}) · Official FinishTiming Time: {a["act_time_exact"]}</span>
    <span class="mono">Page {page_num} of {TOTAL_PAGES}</span>
  </div>
</div>"""

# ==============================================================================
# BUILD SHARED TABLES FOR PAGES 1, 2, 14, 15
# ==============================================================================
aq_table_rows = []
for idx, a in enumerate(AQ, 1):
    row_cls = ' class="row-aa"' if a["act_is_aa"] else ""
    dt_cls = "up-txt b" if a["time_err_sec"] < 0 else "muted"
    pl_cls = "up-txt b" if a["place_err"] < 0 else "muted"
    badge = '<span class="pill-aa">★ ALL-AMERICAN</span>' if a["act_is_aa"] else (
        '<span class="pill-cyo">CYO Champ Team</span>' if a["event_num"] == 11 else (
            '<span class="pill-surge">-50.5s Beat!</span>' if a["time_err_sec"] <= -45 else (
                f'<span class="pill-surge">+{abs(a["place_err"]):.0f} Pl Surge</span>' if a["place_err"] <= -35 else f'<span class="muted">Page {idx+2}</span>'
            )
        )
    )
    aq_table_rows.append(
        f'<tr{row_cls}>'
        f'<td class="b">{esc(a["display_name"])} <span class="muted mono" style="font-size:6.3pt">(p.{idx+2})</span></td>'
        f'<td class="nw">{a["event_short"]}</td>'
        f'<td class="num mono">{a["age"]}</td>'
        f'<td class="num mono muted">{a["pred_time_str"]}</td>'
        f'<td class="num mono b">{a["act_time_str"]}</td>'
        f'<td class="num mono {dt_cls}">{a["time_err_sec"]:+.1f}s</td>'
        f'<td class="num mono">{a["act_pace_mi"]}/mi</td>'
        f'<td class="num mono">#{a["pred_place"]:.0f} &#8594; <b class="{pl_cls}">#{a["act_place"]}</b></td>'
        f'<td class="num mono">#{a["act_cyo_place"]}</td>'
        f'<td class="num mono b">#{a["act_age_place"]}/{a["act_age_field_size"]}</td>'
        f'<td class="num">{badge}</td>'
        f'</tr>'
    )

# Page 2: Aquinas 5-Division Team Hardware Table
aq_div_rows = []
for ev_n, div_lbl, runners_txt, team_res in [
    (4,  "Ev 4 · Boys 6–8 2K",    "Linus Gruber (#3 Age-7 ★AA), Diego Victor (#9 Age-6 ★AA)", "Pittsburgh CYO: <b>#3 CYO Trophy (56–56 tie for 2nd!)</b> · #11 Nat (Pred #12.9)"),
    (6,  "Ev 6 · Girls 9–10 3K",  "Cora Donahue (A, #85), Angela Gallagher (B, #104), Marcela Victor (B, #144)", "Pgh CYO A: <b>#3 CYO Podium (69p)</b> · #7 Nat | Pgh CYO B: <b>#4 CYO (77p)</b> · #13 Nat"),
    (9,  "Ev 9 · Boys 11–12 3K",  "Noah Malone (#14 Age-11 ★AA, +70 pl), Joey Edwards (#156, +1.3 pl acc.)", "Pittsburgh CYO: <b>#2 CYO Silver (51p)</b> · <b>#6 in the Nation!</b> (Pred #12.3)"),
    (10, "Ev 10 · Girls 13–14 4K","Katalina Barnett (-50.5s!), Ciara McBride (-32.5s), Charlotte Austin (+2.7s)", "Pittsburgh CYO: <b>#2 CYO Silver (51p)</b> · #15 Nat (Pred #17.9)"),
    (11, "Ev 11 · Boys 13–14 4K", "John Austin (14:37.9, 5:53/mi, #8 CYO, #5 CYO Age-14)", "Pittsburgh CYO: <b>★ CYO NATIONAL CHAMPIONS (23p!)</b> · <b>#6 Nat!</b> (Pred #8.3)"),
]:
    aq_div_rows.append(f'<tr><td class="b nw">{div_lbl}</td><td>{runners_txt}</td><td>{team_res}</td></tr>')

# Page 14: Tier & Event Calibration tables
tier_order = [
    "Tier 1+ (2026 + CCCNYC Vet)", "Tier 1 (2026 Empirical)", "Tier 2 (CCCNYC Veteran)",
    "Tier 2M (Prior Season Empirical)", "Tier 3 (Club × Age Prior)",
]
tier_rows_html = [
    f'<tr><td class="b">{esc(t)}</td><td class="num mono">{TIER_STATS[t]["n"]}</td>'
    f'<td class="num mono">{TIER_STATS[t]["median_bias_sec"]:+.1f}s</td>'
    f'<td class="num mono">{TIER_STATS[t]["median_abs_sec"]:.1f}s</td>'
    f'<td class="num mono">{TIER_STATS[t]["mae_sec"]:.1f}s</td>'
    f'<td class="num mono b">{TIER_STATS[t]["mape_pct"]:.2f}%</td>'
    f'<td class="num mono">{TIER_STATS[t]["p10_p90_cov"]:.1f}%</td></tr>'
    for t in tier_order if t in TIER_STATS
]
ev_cal_rows = [
    f'<tr><td class="b">Ev {es["event_num"]} · {es["short"]}</td>'
    f'<td class="num mono">{es["matched_finishers"]}/{es["actual_finishers"]}</td>'
    f'<td class="num mono">{es["median_time_bias_sec"]:+.1f}s</td>'
    f'<td class="num mono">{es["median_abs_err_sec"]:.1f}s</td>'
    f'<td class="num mono">{es["mape_pct"]:.2f}%</td>'
    f'<td class="num mono b">{es["time_r"]:.3f}</td>'
    f'<td class="num mono">{es["p10_p90_coverage_pct"]:.1f}%</td></tr>'
    for es in EVENTS if es["event_num"] != 5
]

# Page 15: All 10 Pgh CYO Squads + 15 All-Americans
dop_squad_rows = []
for ev_n in [3, 4, 6, 7, 8, 9, 10, 11]:
    ev_nat = [t for t in TEAMS if t["event_num"] == ev_n and t["is_dop"] and t["lens"] == "nat"]
    ev_cyo = {t["team"]: t for t in TEAMS if t["event_num"] == ev_n and t["is_dop"] and t["lens"] == "cyo"}
    es = next(e for e in EVENTS if e["event_num"] == ev_n)
    cyo_champ_act = es["cyo_top3_act"][0]["team"].replace("Philadelphia ", "Phila. ").replace("Diocese of Pittsburgh CYO", "Pittsburgh CYO") if es["cyo_top3_act"] else "—"
    for nt in ev_nat:
        ct = ev_cyo.get(nt["team"], {})
        c_rk = ct.get("act_rank")
        pod_badge = '<span class="pill-aa">CYO CHAMP!</span>' if c_rk == 1 else ('<span class="pill-cyo">CYO PODIUM</span>' if c_rk and c_rk <= 3 else '<span class="muted">#4 CYO</span>')
        dop_squad_rows.append(
            f'<tr><td class="b">{nt["event_short"]}</td>'
            f'<td class="b dop-txt">{esc(nt["team"])}</td>'
            f'<td class="num mono">#{nt["pred_rank"]:.1f} &#8594; <b class="up-txt">#{nt["act_rank"]}</b> <span class="muted">({nt["act_score"]}p)</span></td>'
            f'<td class="num mono">#{ct.get("pred_rank",0):.1f} &#8594; <b class="b">#{c_rk}</b> <span class="muted">({ct.get("act_score")}p)</span></td>'
            f'<td class="num">{pod_badge}</td>'
            f'<td style="font-size:6.8pt"><span class="up-txt b">✓</span> {esc(cyo_champ_act)}</td></tr>'
        )

dop_aa_list = sorted([a for a in DOP if a["act_is_aa"]], key=lambda x: (x["act_age_place"], x["event_num"]))
aa_pills_html = [
    f'<span class="{"aa-badge aa-aq" if a["home_school"] == "Aquinas Academy" else "aa-badge"}"><b>#{a["act_age_place"]}</b> {esc(a["display_name"])} '
    f'<span class="mono" style="font-size:6.5pt">(Age {a["age"]} · {a["act_time_str"]} · {esc(short_school(a["home_school"]))})</span></span>'
    for a in dop_aa_list
]

# Build all 11 individual runner pages (Pages 3..13)
runner_pages_html = [build_runner_page(a, i, i + 2) for i, a in enumerate(AQ, 1)]

html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Aquinas Academy · 2026 CCCNYC Nationals Complete Keepsake Post-Race Report (15 Pages)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap">
<style>
@page {{ size: letter portrait; margin: 0.36in 0.42in 0.36in 0.42in; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: "IBM Plex Sans", -apple-system, Segoe UI, sans-serif;
  color: #172030;
  background: #ffffff;
  font-size: 8.1pt;
  line-height: 1.32;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}
.page {{
  page-break-after: always;
  display: flex;
  flex-direction: column;
  min-height: 10.22in;
}}
.page:last-child {{ page-break-after: auto; }}
.mono {{ font-family: "IBM Plex Mono", Consolas, monospace; font-variant-numeric: tabular-nums; }}
.num {{ text-align: right; }}
.b {{ font-weight: 700; }}
.nw {{ white-space: nowrap; }}
.muted {{ color: #646a76; }}
.dop-txt {{ color: #b8251e; }}
.up-txt {{ color: #0d7a47; }}
.cyo-txt {{ color: #5b359a; }}

.masthead {{
  background: linear-gradient(135deg, #102446 0%, #1a3768 65%, #2b1d3d 100%);
  color: #ffffff;
  border-radius: 6px;
  padding: 13px 16px 12px;
  border-bottom: 3.5px solid #b8251e;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 12px;
  margin-bottom: 9px;
}}
.mh-eyebrow {{ font-family: "IBM Plex Mono", monospace; font-size: 7.0pt; letter-spacing: 0.11em; text-transform: uppercase; color: #f3c44d; font-weight: 600; margin-bottom: 3px; }}
.masthead h1 {{ font-family: "Fraunces", Georgia, serif; font-size: 18pt; line-height: 1.08; font-weight: 700; color: #ffffff; margin-bottom: 3px; }}
.mh-sub {{ font-size: 7.7pt; color: #dbe5f3; }}
.mh-date {{ text-align: right; border-left: 1px solid rgba(255,255,255,0.22); padding-left: 12px; flex-shrink: 0; }}
.mh-date .big {{ font-family: "Fraunces", Georgia, serif; font-size: 11.2pt; font-weight: 700; color: #ffffff; }}
.mh-date .sm {{ font-family: "IBM Plex Mono", monospace; font-size: 6.8pt; color: #c7d5ea; margin-top: 2px; }}

.pg-hdr {{ display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 2px solid #132c54; padding-bottom: 5px; margin-bottom: 8px; gap: 10px; }}
.pg-hdr .eyebrow {{ font-family: "IBM Plex Mono", monospace; font-size: 6.8pt; letter-spacing: 0.09em; text-transform: uppercase; color: #b8251e; font-weight: 700; }}
.pg-hdr h1 {{ font-family: "Fraunces", Georgia, serif; font-size: 14.0pt; line-height: 1.12; color: #132c54; font-weight: 700; margin-top: 1px; }}
.pg-hdr .hdr-meta {{ text-align: right; font-size: 7.4pt; flex-shrink: 0; }}

.kpi-strip {{ display: grid; grid-template-columns: repeat(6, 1fr); background: #f7f5ef; border-top: 1px solid #dbd6ca; border-bottom: 1.5px solid #132c54; padding: 6px 2px; margin-bottom: 9px; }}
.kpi-cell {{ text-align: center; padding: 0 4px; border-right: 1px solid #ddd8cc; }}
.kpi-cell:last-child {{ border-right: none; }}
.kpi-cell .v {{ font-family: "IBM Plex Mono", monospace; font-size: 12.2pt; font-weight: 700; color: #132c54; line-height: 1.12; }}
.kpi-cell.dop .v {{ color: #b8251e; }}
.kpi-cell.up .v {{ color: #0d7a47; }}
.kpi-cell.cyo .v {{ color: #5b359a; }}
.kpi-cell .l {{ font-size: 6.4pt; text-transform: uppercase; letter-spacing: 0.05em; color: #5f6673; font-weight: 600; margin-top: 2px; }}

.hero-banner {{
  background: linear-gradient(135deg, #fdf3f2 0%, #f8f6f0 100%);
  border: 1px solid #e7c6c3;
  border-left: 4.5px solid #b8251e;
  border-radius: 5px;
  padding: 8px 12px;
  margin-bottom: 9px;
  display: grid;
  grid-template-columns: 1.38fr 1fr;
  gap: 10px;
  align-items: center;
}}
.hb-kicker {{ font-family: "IBM Plex Mono", monospace; font-size: 6.6pt; font-weight: 700; color: #b8251e; text-transform: uppercase; letter-spacing: 0.07em; }}
.hb-title {{ font-family: "Fraunces", Georgia, serif; font-size: 13.4pt; color: #132c54; font-weight: 700; line-height: 1.15; margin: 2px 0 3px; }}
.hb-copy {{ font-size: 7.6pt; color: #2b3444; line-height: 1.33; }}
.hb-metrics {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 5px; }}
.hb-box {{ background: #ffffff; border: 1px solid #e3ded2; border-radius: 4px; padding: 5px 6px; text-align: center; }}
.hb-box .v {{ font-family: "IBM Plex Mono", monospace; font-size: 10.8pt; font-weight: 700; color: #132c54; }}
.hb-box.g .v {{ color: #0d7a47; }}
.hb-box.r .v {{ color: #b8251e; }}
.hb-box .l {{ font-size: 6.1pt; color: #646a76; text-transform: uppercase; letter-spacing: 0.03em; margin-top: 1px; }}

.ed-sec {{ margin-bottom: 8px; }}
.sec-bar {{ display: flex; justify-content: space-between; align-items: baseline; padding: 3.5px 8px; border-radius: 3px; font-size: 7.8pt; font-weight: 700; margin-bottom: 4px; gap: 6px; }}
.sec-bar.navy {{ background: #132c54; color: #ffffff; }}
.sec-bar.crimson {{ background: #b8251e; color: #ffffff; }}
.sec-bar.subtle {{ background: #f2efe7; color: #132c54; border-left: 3px solid #132c54; }}
.sec-bar .sec-sub {{ font-weight: 400; font-size: 6.8pt; opacity: 0.88; text-align: right; }}

.split-62-38 {{ display: grid; grid-template-columns: 62% 36.5%; gap: 1.5%; align-items: start; }}
.split-50-50 {{ display: grid; grid-template-columns: 49.2% 49.2%; gap: 1.6%; align-items: start; }}

table {{ width: 100%; border-collapse: collapse; font-size: 7.25pt; }}
table.tbl-tight {{ font-size: 6.95pt; }}
table.tbl-tight td {{ padding: 2.4px 4.5px; }}
th {{
  text-align: left;
  font-family: "IBM Plex Mono", monospace;
  font-size: 6.3pt;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #555c69;
  padding: 3.3px 5px;
  border-bottom: 1.4px solid #132c54;
  background: #f7f5ef;
}}
td {{ padding: 3.1px 5px; border-bottom: 1px solid #ece8de; vertical-align: middle; }}
tr.row-victor td {{ background: #fdf1f0; }}
tr.row-aa td {{ background: #f3faf6; }}

.pill-aa {{ display: inline-block; background: #0d7a47; color: #ffffff; font-family: "IBM Plex Mono", monospace; font-size: 6.1pt; font-weight: 700; padding: 1.5px 5px; border-radius: 99px; white-space: nowrap; }}
.pill-cyo {{ display: inline-block; background: #5b359a; color: #ffffff; font-family: "IBM Plex Mono", monospace; font-size: 6.1pt; font-weight: 700; padding: 1.5px 5px; border-radius: 99px; white-space: nowrap; }}
.pill-surge {{ display: inline-block; background: #e8f5ee; color: #0d7a47; border: 1px solid #b2dfc5; font-family: "IBM Plex Mono", monospace; font-size: 6.1pt; font-weight: 700; padding: 1px 5px; border-radius: 99px; white-space: nowrap; }}

.callout {{ background: #f7f5ef; border-left: 3.5px solid #132c54; padding: 6px 8.5px; border-radius: 3px; font-size: 7.3pt; line-height: 1.32; color: #263040; }}
.callout.crimson {{ background: #fdf3f2; border-left-color: #b8251e; }}
.callout.green {{ background: #f2faf5; border-left-color: #0d7a47; }}

.aa-badge {{ display: inline-block; background: #f6f4ee; border: 1px solid #dcd7ca; border-radius: 4px; padding: 2.5px 6px; margin: 2px 3px 2px 0; font-size: 7.0pt; }}
.aa-badge.aa-aq {{ background: #fdf1f0; border-color: #e2a4a0; color: #8c1a15; }}

.pfoot {{ margin-top: auto; padding-top: 5px; border-top: 1px solid #d8d4c8; display: flex; justify-content: space-between; font-size: 6.9pt; color: #717782; }}
</style>
</head>
<body>

<!-- PAGE 1: COVER & AQUINAS ACADEMY EXECUTIVE SCORECARD -->
<div class="page">
  <div class="masthead">
    <div>
      <div class="mh-eyebrow">2026 CCCNYC &amp; CYO National Championships · Complete 15-Page Keepsake Post-Race Dossier</div>
      <h1>Aquinas Academy · Cedarville Actuals vs. Predictions</h1>
      <div class="mh-sub">Individual Keepsake Pages for All 11 Aquinas Runners (Pages 3–13) · Frozen Forecast Audited Against <b>2,424 / 2,441 (99.3%)</b> Official Finishers</div>
    </div>
    <div class="mh-date">
      <div class="big">Nov 21, 2026</div>
      <div class="sm">Cedarville Univ. · OH<br>Elvin R. King XC Course</div>
    </div>
  </div>

  <div class="kpi-strip">
    <div class="kpi-cell dop"><div class="v">11 / 11</div><div class="l">Aquinas Finishers</div></div>
    <div class="kpi-cell up"><div class="v">3</div><div class="l">Aquinas All-Americans</div></div>
    <div class="kpi-cell up"><div class="v">9 / 11</div><div class="l">Beat Time Forecast</div></div>
    <div class="kpi-cell dop"><div class="v">-24.0s</div><div class="l">Aquinas Median Δt</div></div>
    <div class="kpi-cell cyo"><div class="v">8 / 8</div><div class="l">CYO Champs Called</div></div>
    <div class="kpi-cell"><div class="v">r = 0.938</div><div class="l">2,424-Runner Corr.</div></div>
  </div>

  <div class="ed-sec">
    <div class="sec-bar crimson">
      <span>Aquinas Academy · Complete 11-Runner Predicted vs. Actual Scorecard (Page Index Included)</span>
      <span class="sec-sub">Negative Δt = Ran FASTER than Pre-Race Forecast · ★ = Single-Year National All-American (Top 25)</span>
    </div>
    <table>
      <thead>
        <tr>
          <th>Runner (Dossier Pg)</th><th>Race</th><th class="num">Age</th><th class="num">Pred Time</th><th class="num">Act Time</th>
          <th class="num">Δt</th><th class="num">Act Pace</th><th class="num">Ov Place</th><th class="num">CYO Pl</th>
          <th class="num">Age Place</th><th class="num">Headline</th>
        </tr>
      </thead>
      <tbody>{"".join(aq_table_rows)}</tbody>
    </table>
  </div>

  <div class="ed-sec">
    <div class="sec-bar subtle">
      <span>Aquinas Academy Forecast Beat Chart (Actual − Predicted Seconds)</span>
      <span class="sec-sub">Aquinas beat forecasts by a median of -24.0s while the rest of the nation ran +8.6s slower (32.6s Western PA advantage!)</span>
    </div>
    {build_aq_diverging_svg()}
  </div>

  <div class="callout green">
    <b>Headline Takeaway — Western PA Hills Built Cedarville Flyers:</b> While the non-Pittsburgh national field (2,361 finishers) averaged <b>+8.6s slower</b> than pre-race projections, all 11 Aquinas Academy runners crushed expectations by a median of <b>-24.0 seconds</b> and <b>+29.1 overall places</b>! Aquinas produced <b>3 Single-Year National All-Americans</b> (<b>Linus Gruber</b> #3 Age-7 Bronze, <b>Diego Victor</b> #9 Age-6, <b>Noah Malone</b> #14 Age-11), a <b>CYO National Team Champion</b> (<b>John Austin</b>, 13–14B), and helped <b>9 of 10 Pittsburgh CYO squads</b> reach the CYO National Podium!
  </div>

  <div class="pfoot">
    <span>Aquinas Academy &amp; Pittsburgh CYO · 2026 CCCNYC Keepsake Post-Race Report · Official Source: FinishTiming Meet #10720716</span>
    <span class="mono">Page 1 of {TOTAL_PAGES}</span>
  </div>
</div>

<!-- PAGE 2: AQUINAS PLACE-SURGE SLOPEGRAPH & 5-DIVISION TEAM HARDWARE SUMMARY -->
<div class="page">
  <div class="pg-hdr">
    <div>
      <div class="eyebrow">AQUINAS ACADEMY SCHOOL-WIDE PERFORMANCE · CO-#1 PITTSBURGH CYO FEEDER SCHOOL (11 / 64 RUNNERS)</div>
      <h1>Aquinas Place-Surge Slopegraph &amp; 5-Division Hardware Summary</h1>
    </div>
    <div class="hdr-meta">
      <div class="mono b up-txt">9 / 11 Beat Time · 9 / 11 Beat Place</div>
      <div class="muted">Avg Place Gain: +29.1 spots per runner</div>
    </div>
  </div>

  <div class="ed-sec">
    <div class="sec-bar subtle">
      <span>Pre-Race Forecast Percentile &#8594; Actual Cedarville Finish Percentile (All 11 Aquinas Academy Runners)</span>
      <span class="sec-sub">Upward-sloping lines = beat forecast percentile · Green = Beat forecast · ★AA = National All-American</span>
    </div>
    {build_aq_slope_svg()}
  </div>

  <div class="ed-sec">
    <div class="sec-bar navy">
      <span>Aquinas Academy Impact Across All 5 Championship Divisions &amp; CYO Hardware Won</span>
      <span class="sec-sub">Aquinas runners contributed to 1 CYO Championship, 2 CYO Silvers, and 2 CYO Bronze Trophies!</span>
    </div>
    <table>
      <thead><tr><th style="width:145px">Championship Race</th><th>Aquinas Academy Qualifiers</th><th>Pittsburgh CYO Squad Result</th></tr></thead>
      <tbody>{"".join(aq_div_rows)}</tbody>
    </table>
  </div>

  <div class="split-50-50">
    <div class="callout green">
      <b>Punched Well Above School Size:</b><br>
      Aquinas Academy supplied <b>17.2%</b> of Pittsburgh CYO's 64-runner delegation (tied with St. Louise de Marillac at 11 runners each) — yet earned <b>20% of Pittsburgh CYO's All-Americans (3 of 15)</b>, including Pittsburgh's <b>highest-placing individual boy in any race</b> (Linus Gruber, #3 Age-7 in America!) and the <b>essential 5th-man scorer</b> who unlocked the Boys 6–8 CYO Trophy (Diego Victor)!
    </div>
    <div class="callout crimson">
      <b>Inside Pages 3–13 (Individual Keepsake Dossiers):</b><br>
      Every Aquinas runner has a dedicated full-page dossier in race order: <b>Linus Gruber (p.3)</b>, <b>Diego Victor (p.4)</b>, <b>Cora Donahue (p.5)</b>, <b>Angela Gallagher (p.6)</b>, <b>Marcela Victor (p.7)</b>, <b>Noah Malone (p.8)</b>, <b>Joey Edwards (p.9)</b>, <b>Katalina Barnett (p.10)</b>, <b>Ciara McBride (p.11)</b>, <b>Charlotte Austin (p.12)</b>, and <b>John Austin (p.13)</b> — followed by the National Calibration &amp; CYO Audit (p.14–15).
    </div>
  </div>

  <div class="pfoot">
    <span>Aquinas Academy (Gibsonia, PA) · 2026 CCCNYC &amp; CYO Nationals Complete Keepsake Report</span>
    <span class="mono">Page 2 of {TOTAL_PAGES}</span>
  </div>
</div>

{"".join(runner_pages_html)}

<!-- PAGE 14: NATIONAL MODEL CALIBRATION — 2,424 FINISHERS -->
<div class="page">
  <div class="pg-hdr">
    <div>
      <div class="eyebrow">PRE-RACE VS. ACTUAL MODEL AUDIT · FROZEN SNAPSHOT COMMIT 4EBF0F1</div>
      <h1>National Calibration: 2,424 Matched Finishers &amp; The Western PA Effect</h1>
    </div>
    <div class="hdr-meta">
      <div class="mono b">MAPE: 5.32% · MedAE: 29.5s</div>
      <div class="muted">Tier 1+ MAPE: 4.23% (MedAE 24.5s)</div>
    </div>
  </div>

  <div class="split-50-50 ed-sec">
    <div>
      <div class="sec-bar subtle">
        <span>Predicted vs. Actual Finish Time (All 2,424 Runners)</span>
        <span class="sec-sub">Crimson = Aquinas Academy (11)</span>
      </div>
      {build_national_scatter_svg()}
    </div>
    <div>
      <div class="sec-bar subtle">
        <span>Residual Error Density: Western PA vs. Nation</span>
        <span class="sec-sub">Act − Pred (sec)</span>
      </div>
      {build_residual_kde_svg()}
    </div>
  </div>

  <div class="ed-sec">
    <div class="sec-bar navy">
      <span>Model Accuracy Breakdown by Pre-Race Seed Tier</span>
      <span class="sec-sub">Empirical 2026 + Veteran seeds cut error in HALF compared to unseeded Tier 3 club priors!</span>
    </div>
    <table>
      <thead>
        <tr>
          <th>Pre-Race Seed Tier</th><th class="num">Matched (n)</th><th class="num">Median Bias</th>
          <th class="num">Median Abs Err</th><th class="num">Mean Abs Err</th><th class="num">MAPE</th><th class="num">P10–P90 Cov</th>
        </tr>
      </thead>
      <tbody>{"".join(tier_rows_html)}</tbody>
    </table>
  </div>

  <div class="ed-sec">
    <div class="sec-bar subtle">
      <span>Event-by-Event Calibration (All 10 Championship Divisions · Excl. 1K Open)</span>
      <span class="sec-sub">2K ran ~17.5s faster; 3K/4K ran ~14s slower nationally — while Pittsburgh CYO ran fast everywhere!</span>
    </div>
    <table>
      <thead>
        <tr>
          <th>Event</th><th class="num">Matched</th><th class="num">Median Bias</th><th class="num">MedAE</th>
          <th class="num">MAPE</th><th class="num">Pearson r</th><th class="num">P10–P90 Cov</th>
        </tr>
      </thead>
      <tbody>{"".join(ev_cal_rows)}</tbody>
    </table>
  </div>

  <div class="pfoot">
    <span>Model Audit: Frozen Pre-Race Snapshot (pre-race-2026-11-21) vs. Official FinishTiming Results (2,424 / 2,441 matched)</span>
    <span class="mono">Page 14 of {TOTAL_PAGES}</span>
  </div>
</div>

<!-- PAGE 15: ALL-AMERICAN RELIABILITY, 8/8 CYO CHAMPIONS & PITTSBURGH CYO HONOR ROLL -->
<div class="page">
  <div class="pg-hdr">
    <div>
      <div class="eyebrow">PROBABILITY CALIBRATION &amp; CYO NATIONAL CUP HARDWARE AUDIT</div>
      <h1>All-American Reliability, 8-for-8 CYO Champs &amp; Pittsburgh CYO Honor Roll</h1>
    </div>
    <div class="hdr-meta">
      <div class="mono b up-txt">8 / 8 CYO Champs · 15 Pgh CYO AAs</div>
      <div class="muted">9 / 10 Pgh CYO Squads on CYO Podium</div>
    </div>
  </div>

  <div class="split-50-50 ed-sec">
    <div>
      <div class="sec-bar subtle">
        <span>All-American Top-25 Calibration Curve (n = 2,207)</span>
        <span class="sec-sub">Predicted % vs Actual Hit Rate</span>
      </div>
      {build_aa_calibration_svg()}
    </div>
    <div style="display:flex;flex-direction:column;gap:6px">
      <div class="callout green">
        <b>Historic CYO Team Prediction Accuracy (8 / 8 = 100%):</b><br>
        Our pre-race Monte Carlo simulation predicted the <b>exact CYO National Champion in all 8 scored divisions</b> — Pittsburgh CYO (6–8G &amp; 13–14B), Toledo CYO A (6–8B), Phila. CYO Black (9–10G &amp; 13–14G), Phila. CYO White (9–10B), and Phila. CYO Red (11–12G &amp; 11–12B)!
      </div>
      <div class="callout crimson">
        <b>Pittsburgh CYO Outperformed Across the Board:</b><br>
        • <b>10 / 10 squads</b> beat their projected National Open rank!<br>
        • <b>9 / 10 squads</b> earned CYO National Top-3 Podiums (2 Titles, 4 Silvers, 3 Bronzes)!<br>
        • <b>7 / 7 (100%)</b> Pittsburgh CYO runners with &ge;50% pre-race AA odds won medals — plus <b>8 surprise breakouts</b> = <b>15 Total All-Americans</b> (vs 10.3 expected)!
      </div>
      <div class="callout">
        <b>Next-Year Model Calibration Upgrades:</b><br>
        (1) Add a regional <b>Western PA hilly-course conversion factor (-18s to -24s)</b> for Smiley Miles / Diocesan marks; (2) widen youth race-day variance slightly so P10–P90 coverage rises from 63.5% to 80%.
      </div>
    </div>
  </div>

  <div class="ed-sec">
    <div class="sec-bar navy">
      <span>All 10 Pittsburgh CYO Squads · Predicted vs. Actual National &amp; CYO Standings</span>
      <span class="sec-sub">Right column confirms 8 / 8 CYO National Team Champions predicted accurately!</span>
    </div>
    <table>
      <thead>
        <tr>
          <th>Division</th><th>Pittsburgh CYO Squad</th><th class="num">National (Pred &#8594; Act)</th>
          <th class="num">CYO (Pred &#8594; Act)</th><th class="num">CYO Result</th><th>CYO Champ (Pred = Act)</th>
        </tr>
      </thead>
      <tbody>{"".join(dop_squad_rows)}</tbody>
    </table>
  </div>

  <div class="ed-sec">
    <div class="sec-bar crimson">
      <span>2026 Pittsburgh CYO National All-American Honor Roll (15 Medalists · Crimson = Aquinas Academy)</span>
      <span class="sec-sub">Ranked by Single-Year Birth-Age National Finish (Top 25 earn All-American honors)</span>
    </div>
    <div style="margin-top:3px">{"".join(aa_pills_html)}</div>
  </div>

  <div class="pfoot">
    <span>Aquinas Academy &amp; Pittsburgh CYO · 2026 CCCNYC Post-Race Report · Live Results: jtv55.github.io/xc/nationals/results.html</span>
    <span class="mono">Page 15 of {TOTAL_PAGES}</span>
  </div>
</div>

</body>
</html>
"""

OUT_HTML.write_text(html_doc, encoding="utf-8")
print(f"Wrote 15-page Aquinas Keepsake HTML: {OUT_HTML} ({len(html_doc):,} bytes)")

edge_exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
cmd = [
    edge_exe,
    "--headless=new",
    "--disable-gpu",
    "--no-pdf-header-footer",
    f"--print-to-pdf={OUT_PDF}",
    OUT_HTML.as_uri(),
]
subprocess.run(cmd, check=True)
print(f"Generated 15-page Aquinas Keepsake PDF: {OUT_PDF} ({OUT_PDF.stat().st_size:,} bytes)")
