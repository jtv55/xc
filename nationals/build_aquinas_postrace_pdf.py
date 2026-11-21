import html as html_mod
import json
import math
import pathlib
import subprocess
import numpy as np

BASE = pathlib.Path(r"c:\Users\j_t_v\XC\nationals")
PVA_FP = BASE / "data" / "actuals_2026" / "predicted_vs_actual_2026.json"
PRE_FP = BASE / "data" / "snapshots" / "pre_race_20261121" / "cccnyc_2026_master_prerace.json"
RAW_DIR = BASE / "data" / "actuals_2026" / "raw"
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
    # Grid lines
    for v in [-50, -40, -30, -20, -10, 0, 10, 20]:
        xv = sx(v)
        col = "#9aa0ab" if v == 0 else "#e7e3d9"
        sw = "1.2" if v == 0 else "0.7"
        parts.append(f'<line x1="{xv:.1f}" y1="{mt}" x2="{xv:.1f}" y2="{H-mb}" stroke="{col}" stroke-width="{sw}"/>')
        lbl = f"{v:+d}s" if v != 0 else "0s (Forecast)"
        parts.append(f'<text x="{xv:.1f}" y="{H-mb+13}" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="7.4" fill="#646a76">{lbl}</text>')

    # Rest-of-nation median bias line (+8.6s)
    parts.append(f'<line x1="{x_nat:.1f}" y1="{mt}" x2="{x_nat:.1f}" y2="{H-mb}" stroke="#64748b" stroke-width="1.0" stroke-dasharray="3,2.5"/>')
    parts.append(f'<text x="{x_nat+3:.1f}" y="{mt-5}" font-family="IBM Plex Sans,sans-serif" font-size="6.8" font-weight="600" fill="#475569">Rest of Nation Median (+8.6s)</text>')
    parts.append(f'<text x="{ml+4}" y="{mt-5}" font-family="IBM Plex Sans,sans-serif" font-size="6.8" font-weight="700" fill="#0d7a47">&#8592; Ran FASTER than Pre-Race Forecast</text>')

    for i, a in enumerate(rows):
        yc = mt + (i + 0.5) * rh
        bh = rh * 0.62
        err = a["time_err_sec"]
        is_v = a["display_name"] in ("Diego Victor", "Marcela Victor")
        col = "#b8251e" if is_v else ("#0d7a47" if err < 0 else "#8b929e")
        bx = sx(min(0, err))
        bw = max(2.0, abs(sx(err) - x0))
        if is_v:
            parts.append(f'<rect x="2" y="{yc-rh*0.48:.1f}" width="{W-4}" height="{rh*0.96:.1f}" fill="#fdf2f1" rx="2"/>')
        parts.append(f'<rect x="{bx:.1f}" y="{yc-bh/2:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="2.5" fill="{col}" opacity="0.92"/>')
        nm_col = "#b8251e" if is_v else "#172030"
        fw = "700" if is_v or a["act_is_aa"] else "600"
        star = " ★" if a["act_is_aa"] else ""
        parts.append(f'<text x="{ml-6}" y="{yc+2.6:.1f}" text-anchor="end" font-family="IBM Plex Sans,sans-serif" font-size="7.7" font-weight="{fw}" fill="{nm_col}">{esc(a["display_name"])}{star} <tspan fill="#6f7582" font-size="6.8" font-weight="400">({a["event_short"]})</tspan></text>')
        # Value label
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
# SVG 2 & 5: INDIVIDUAL 2026 SEASON PACE PROGRESSION CURVE (DIEGO & MARCELA)
# ==============================================================================
def build_season_pace_svg(ath_pair, color_main="#b8251e", W=455, H=218):
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
        "label": "Cedarville Nat.",
        "pace": nat_pace,
        "time_str": ath_pair["act_time_str"],
        "dist_m": ath_pair["dist_m"],
        "is_nat": True,
    })

    ml, mr, mt, mb = 44, 58, 22, 42
    pw, ph = W - ml - mr, H - mt - mb
    all_p = [p["pace"] for p in pts] + [pred_pace, p10_pace, p90_pace]
    ymin = math.floor((min(all_p) - 10) / 15) * 15
    ymax = math.ceil((max(all_p) + 10) / 15) * 15
    # Faster pace = HIGHER on chart (y=mt is faster ymin, y=H-mb is slower ymax!)
    def sy(p): return mt + (p - ymin) / (ymax - ymin) * ph
    def sx(i): return ml + (i / max(1, len(pts) - 1)) * pw

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;height:auto">']
    parts.append(f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="#faf8f3" rx="3"/>')

    # P10-P90 Forecast Band on right quarter
    x_band = sx(len(pts) - 1.55)
    parts.append(f'<rect x="{x_band:.1f}" y="{sy(p10_pace):.1f}" width="{W-mr-x_band+4:.1f}" height="{sy(p90_pace)-sy(p10_pace):.1f}" fill="#132c54" opacity="0.09" rx="2"/>')
    parts.append(f'<line x1="{ml}" y1="{sy(pred_pace):.1f}" x2="{W-mr+4}" y2="{sy(pred_pace):.1f}" stroke="#132c54" stroke-width="1.0" stroke-dasharray="4,3" opacity="0.65"/>')
    parts.append(f'<text x="{W-mr+7}" y="{sy(pred_pace)+2.5:.1f}" font-family="IBM Plex Mono,monospace" font-size="6.8" font-weight="600" fill="#132c54">Pred {fmt_pace_s(pred_pace)}</text>')

    # Horizontal gridlines (every 15s or 30s)
    step = 15 if (ymax - ymin) <= 105 else 30
    v = ymin
    while v <= ymax + 0.1:
        yv = sy(v)
        parts.append(f'<line x1="{ml}" y1="{yv:.1f}" x2="{W-mr}" y2="{yv:.1f}" stroke="#e6e2d8" stroke-width="0.65"/>')
        parts.append(f'<text x="{ml-6}" y="{yv+2.5:.1f}" text-anchor="end" font-family="IBM Plex Mono,monospace" font-size="7.2" fill="#646a76">{fmt_pace_s(v)}</text>')
        v += step
    parts.append(f'<text x="{ml+4}" y="{mt-6}" font-family="IBM Plex Sans,sans-serif" font-size="6.8" font-weight="600" fill="#0d7a47">&#8593; Faster Mile Pace (min/mi)</text>')

    # Season line + area
    poly = " ".join(f"{sx(i):.1f},{sy(p['pace']):.1f}" for i, p in enumerate(pts))
    parts.append(f'<polyline points="{poly}" fill="none" stroke="{color_main}" stroke-width="2.1" stroke-linejoin="round"/>')

    # Points & annotations
    for i, p in enumerate(pts):
        cx, cy = sx(i), sy(p["pace"])
        if p["is_nat"]:
            nat_tag = "2K PR!" if ath_pair["dist_m"] == 2000 else "3K PR!"
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5.5" fill="#0d7a47" stroke="#ffffff" stroke-width="1.6"/>')
            parts.append(f'<text x="{cx+7:.1f}" y="{cy+2.5:.1f}" font-family="IBM Plex Mono,monospace" font-size="7.8" font-weight="700" fill="#0d7a47">{fmt_pace_s(p["pace"])}/mi</text>')
            parts.append(f'<text x="{cx:.1f}" y="{cy-9:.1f}" text-anchor="middle" font-family="IBM Plex Sans,sans-serif" font-size="7.0" font-weight="700" fill="#0d7a47">{nat_tag}</text>')
        else:
            is_3k = (p["dist_m"] >= 2900)
            fill = "#5b359a" if is_3k else color_main
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3.4" fill="{fill}" stroke="#ffffff" stroke-width="1.1"/>')
            # Place label above local peaks and below local valleys so it never crosses the red line!
            prev_p = pts[i - 1]["pace"] if i > 0 else p["pace"]
            next_p = pts[i + 1]["pace"] if i < len(pts) - 1 else p["pace"]
            is_faster_peak = (p["pace"] <= prev_p and p["pace"] <= next_p)
            dy = -8 if is_faster_peak else 13
            if i == 0:
                dy = 13 if next_p < p["pace"] else -8
            if cy + dy < mt + 9: dy = 13
            if cy + dy > H - mb - 4: dy = -8
            parts.append(f'<text x="{cx:.1f}" y="{cy+dy:.1f}" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="6.5" fill="#334155" paint-order="stroke" stroke="#faf8f3" stroke-width="2.5">{fmt_pace_s(p["pace"])}</text>')
        # X-axis labels
        parts.append(f'<text x="{cx:.1f}" y="{H-mb+11}" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="6.4" font-weight="{"700" if p["is_nat"] else "400"}" fill="{"#0d7a47" if p["is_nat"] else "#646a76"}">{p["date"]}</text>')
        short_l = p["label"][:11]
        parts.append(f'<text x="{cx:.1f}" y="{H-mb+21}" text-anchor="middle" font-family="IBM Plex Sans,sans-serif" font-size="6.0" font-weight="{"700" if p["is_nat"] else "400"}" fill="{"#0d7a47" if p["is_nat"] else "#6f7582"}">{esc(short_l)}</text>')

    parts.append("</svg>")
    return "".join(parts)

# ==============================================================================
# SVG 3: DIEGO AGE-6 NATIONAL LEADERBOARD & CUTLINE STRIP (PAGE 2)
# ==============================================================================
def build_diego_age6_svg(W=265, H=218):
    a6 = sorted([a for a in ATHS if a["event_num"] == 4 and a["age"] == 6 and a["act_age_place"]], key=lambda x: x["act_age_place"])
    top = a6[:12]
    ml, mr, mt, mb = 104, 48, 18, 22
    pw, ph = W - ml - mr, H - mt - mb
    tmin, tmax = 470.0, 655.0  # 7:50 to 10:55
    def sx(t): return ml + (t - tmin) / (tmax - tmin) * pw
    rh = ph / len(top)

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;height:auto">']
    parts.append(f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="#faf8f3" rx="3"/>')
    for t in [480, 540, 600, 640]:
        xv = sx(t)
        parts.append(f'<line x1="{xv:.1f}" y1="{mt}" x2="{xv:.1f}" y2="{H-mb}" stroke="#e7e3d9" stroke-width="0.7"/>')
        parts.append(f'<text x="{xv:.1f}" y="{H-mb+12}" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="6.6" fill="#646a76">{fmt_time(t)[:-2]}</text>')

    # Actual #25 AA Cutline (10:39.7 = 639.7s)
    xcut = sx(639.7)
    parts.append(f'<line x1="{xcut:.1f}" y1="{mt}" x2="{xcut:.1f}" y2="{H-mb}" stroke="#0d7a47" stroke-width="1.1" stroke-dasharray="3,2"/>')
    parts.append(f'<text x="{xcut-2:.1f}" y="{mt-4}" text-anchor="end" font-family="IBM Plex Mono,monospace" font-size="6.4" font-weight="700" fill="#0d7a47">#25 AA Cut 10:39.7</text>')

    for i, a in enumerate(top):
        yc = mt + (i + 0.5) * rh
        is_d = (a["display_name"] == "Diego Victor")
        if is_d:
            parts.append(f'<rect x="2" y="{yc-rh*0.48:.1f}" width="{W-4}" height="{rh*0.96:.1f}" fill="#fdf2f1" rx="2"/>')
        xa = sx(a["act_time_sec"])
        xp = sx(min(tmax, a["pred_time_sec"]))
        # Arrow from pred to act
        parts.append(f'<line x1="{xp:.1f}" y1="{yc:.1f}" x2="{xa:.1f}" y2="{yc:.1f}" stroke="{"#b8251e" if is_d else "#94a3b8"}" stroke-width="{"1.6" if is_d else "0.9"}" opacity="0.7"/>')
        parts.append(f'<circle cx="{xp:.1f}" cy="{yc:.1f}" r="2.1" fill="#ffffff" stroke="{"#b8251e" if is_d else "#94a3b8"}" stroke-width="1.0"/>')
        parts.append(f'<circle cx="{xa:.1f}" cy="{yc:.1f}" r="{"3.6" if is_d else "2.7"}" fill="{"#b8251e" if is_d else ("#5b359a" if a["is_cyo"] else "#132c54")}"/>')
        nm = f"#{a['act_age_place']} {a['display_name'].split()[0][0]}. {a['display_name'].split()[-1]}"
        if is_d: nm = "#9 Diego Victor ★"
        parts.append(f'<text x="{ml-5}" y="{yc+2.4:.1f}" text-anchor="end" font-family="IBM Plex Sans,sans-serif" font-size="7.0" font-weight="{"700" if is_d else "500"}" fill="{"#b8251e" if is_d else "#172030"}">{esc(nm)}</text>')
        parts.append(f'<text x="{W-mr+5}" y="{yc+2.4:.1f}" font-family="IBM Plex Mono,monospace" font-size="6.8" font-weight="{"700" if is_d else "400"}" fill="{"#b8251e" if is_d else "#475569"}">{a["act_time_str"]}</text>')

    parts.append("</svg>")
    return "".join(parts)

# ==============================================================================
# SVG 6: MARCELA EVENT 6 FIELD PACK & PLACE SURGE VISUAL (PAGE 3)
# ==============================================================================
def build_marcela_pack_svg(W=265, H=218):
    ev6 = sorted([a for a in ATHS if a["event_num"] == 6], key=lambda x: x["act_place"])
    ml, mr, mt, mb = 36, 12, 22, 28
    pw, ph = W - ml - mr, H - mt - mb
    n = len(ev6)
    ymin, ymax = 680.0, 1140.0  # 11:20 to 19:00
    def sx(pl): return ml + (pl - 1) / max(1, n - 1) * pw
    def sy(t): return H - mb - (min(ymax, max(ymin, t)) - ymin) / (ymax - ymin) * ph

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;height:auto">']
    parts.append(f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="#faf8f3" rx="3"/>')
    for t in [720, 840, 960, 1080]:
        yv = sy(t)
        parts.append(f'<line x1="{ml}" y1="{yv:.1f}" x2="{W-mr}" y2="{yv:.1f}" stroke="#e7e3d9" stroke-width="0.7"/>')
        parts.append(f'<text x="{ml-4}" y="{yv+2.4:.1f}" text-anchor="end" font-family="IBM Plex Mono,monospace" font-size="6.6" fill="#646a76">{fmt_time(t)[:-2]}</text>')
    for pl in [1, 60, 120, 180, 240]:
        xv = sx(pl)
        parts.append(f'<text x="{xv:.1f}" y="{H-mb+11}" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="6.5" fill="#646a76">#{pl}</text>')
    parts.append(f'<text x="{ml+pw/2:.1f}" y="{H-4}" text-anchor="middle" font-family="IBM Plex Sans,sans-serif" font-size="6.6" fill="#646a76">Actual Finish Place (244 Finishers · Girls 9–10 3K)</text>')

    # Actual S-curve dots
    for a in ev6:
        cx, cy = sx(a["act_place"]), sy(a["act_time_sec"])
        if a["home_school"] == "Aquinas Academy" and a["is_dop"]:
            continue
        col = "#7e57c2" if a["is_cyo"] else "#cbd5e1"
        r = 1.6 if a["is_cyo"] else 1.2
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{col}" opacity="0.8"/>')

    # Highlight Marcela's Predicted -> Actual jump arrow!
    mx_p, my_p = sx(marcela["pred_place"]), sy(marcela["pred_time_sec"])
    mx_a, my_a = sx(marcela["act_place"]), sy(marcela["act_time_sec"])
    parts.append(f'<line x1="{mx_p:.1f}" y1="{my_p:.1f}" x2="{mx_a:.1f}" y2="{my_a:.1f}" stroke="#b8251e" stroke-width="1.8" stroke-dasharray="3,2"/>')
    parts.append(f'<circle cx="{mx_p:.1f}" cy="{my_p:.1f}" r="3.4" fill="#ffffff" stroke="#b8251e" stroke-width="1.3"/>')
    parts.append(f'<text x="{mx_p+3:.1f}" y="{my_p+11:.1f}" font-family="IBM Plex Mono,monospace" font-size="6.4" fill="#646a76">Pred #179 (15:02)</text>')

    # Aquinas trio dots + labels
    aq6 = [a for a in ev6 if a["is_dop"] and a["home_school"] == "Aquinas Academy"]
    offsets = {
        "Cora Donahue": (-8, -14, "C. Donahue #85"),
        "Angela Gallagher": (-8, 15, "A. Gallagher #104"),
        "Marcela Victor": (-12, -16, "M. Victor #144 (-24s!)"),
    }
    for a in aq6:
        cx, cy = sx(a["act_place"]), sy(a["act_time_sec"])
        is_m = (a["display_name"] == "Marcela Victor")
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{"4.6" if is_m else "3.3"}" fill="{"#b8251e" if is_m else "#0d7a47"}" stroke="#ffffff" stroke-width="1.3"/>')
        dx, dy, lbl = offsets[a["display_name"]]
        parts.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx+dx:.1f}" y2="{cy+dy+(3 if dy<0 else -5):.1f}" stroke="{"#b8251e" if is_m else "#0d7a47"}" stroke-width="0.8"/>')
        anc = "end" if is_m else "middle"
        parts.append(f'<text x="{cx+dx:.1f}" y="{cy+dy:.1f}" text-anchor="{anc}" font-family="IBM Plex Sans,sans-serif" font-size="6.8" font-weight="700" fill="{"#b8251e" if is_m else "#0d7a47"}">{lbl}</text>')

    parts.append("</svg>")
    return "".join(parts)

# ==============================================================================
# SVG 7: AQUINAS PLACE SURGE SLOPEGRAPH (PAGE 4)
# ==============================================================================
def build_aq_slope_svg(W=735, H=200):
    rows = sorted(AQ, key=lambda a: a["act_place"] / a["act_field_size"])
    ml, mr, mt, mb = 44, 44, 24, 20
    pw, ph = W - ml - mr, H - mt - mb
    x_l, x_r = ml + 145, W - mr - 165
    # Map percentile (0% = 1st place at top, 100% = last at bottom)
    def sy(pct): return mt + pct * ph

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;height:auto">']
    parts.append(f'<rect x="{x_l}" y="{mt}" width="{x_r-x_l}" height="{ph}" fill="#faf8f3" rx="3"/>')
    parts.append(f'<line x1="{x_l}" y1="{mt}" x2="{x_l}" y2="{H-mb}" stroke="#cbd5e1" stroke-width="1.2"/>')
    parts.append(f'<line x1="{x_r}" y1="{mt}" x2="{x_r}" y2="{H-mb}" stroke="#132c54" stroke-width="1.4"/>')
    parts.append(f'<text x="{x_l}" y="{mt-8}" text-anchor="middle" font-family="IBM Plex Sans,sans-serif" font-size="7.6" font-weight="700" fill="#475569">PRE-RACE FORECAST PERCENTILE</text>')
    parts.append(f'<text x="{x_r}" y="{mt-8}" text-anchor="middle" font-family="IBM Plex Sans,sans-serif" font-size="7.6" font-weight="700" fill="#132c54">ACTUAL CEDARVILLE FINISH PERCENTILE</text>')

    for pct in [0.0, 0.25, 0.50, 0.75, 1.0]:
        yv = sy(pct)
        parts.append(f'<line x1="{x_l}" y1="{yv:.1f}" x2="{x_r}" y2="{yv:.1f}" stroke="#e7e3d9" stroke-width="0.65"/>')
        lbl = f"Top {int(pct*100)}%" if pct > 0 else "#1"
        parts.append(f'<text x="{(x_l+x_r)/2:.1f}" y="{yv-2:.1f}" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="6.2" fill="#94a3b8">{lbl}</text>')

    # De-collide left and right labels vertically
    pts_l, pts_r = [], []
    for a in rows:
        pl_pct = min(0.96, max(0.03, a["pred_place"] / a["act_field_size"]))
        ac_pct = min(0.96, max(0.03, a["act_place"] / a["act_field_size"]))
        pts_l.append([sy(pl_pct), a])
        pts_r.append([sy(ac_pct), a])

    def spread(arr, min_gap=13.5):
        arr.sort(key=lambda x: x[0])
        for _ in range(15):
            for i in range(1, len(arr)):
                if arr[i][0] - arr[i - 1][0] < min_gap:
                    mid = 0.5 * (arr[i][0] + arr[i - 1][0])
                    arr[i - 1][0] = mid - min_gap / 2
                    arr[i][0] = mid + min_gap / 2
            for item in arr:
                item[0] = max(mt + 4, min(H - mb - 4, item[0]))
        return {item[1]["id"]: item[0] for item in arr}

    yl_lbl = spread([list(x) for x in pts_l])
    yr_lbl = spread([list(x) for x in pts_r])

    for a in rows:
        pl_pct = min(0.96, max(0.03, a["pred_place"] / a["act_field_size"]))
        ac_pct = min(0.96, max(0.03, a["act_place"] / a["act_field_size"]))
        y1, y2 = sy(pl_pct), sy(ac_pct)
        improved = a["act_place"] < a["pred_place"]
        is_v = a["display_name"] in ("Diego Victor", "Marcela Victor")
        col = "#b8251e" if is_v else ("#0d7a47" if improved else "#94a3b8")
        sw = "2.1" if is_v or a["act_is_aa"] else "1.3"
        parts.append(f'<line x1="{x_l}" y1="{y1:.1f}" x2="{x_r}" y2="{y2:.1f}" stroke="{col}" stroke-width="{sw}" opacity="0.85"/>')
        parts.append(f'<circle cx="{x_l}" cy="{y1:.1f}" r="2.8" fill="#ffffff" stroke="{col}" stroke-width="1.3"/>')
        parts.append(f'<circle cx="{x_r}" cy="{y2:.1f}" r="3.4" fill="{col}" stroke="#ffffff" stroke-width="1.0"/>')
        ly1, ly2 = yl_lbl[a["id"]], yr_lbl[a["id"]]
        star = " ★AA" if a["act_is_aa"] else ""
        parts.append(f'<text x="{x_l-7}" y="{ly1+2.5:.1f}" text-anchor="end" font-family="IBM Plex Sans,sans-serif" font-size="7.1" font-weight="{"700" if is_v else "500"}" fill="{"#b8251e" if is_v else "#334155"}">{esc(a["display_name"])} <tspan font-family="IBM Plex Mono,monospace" fill="#646a76">#{a["pred_place"]:.0f}</tspan></text>')
        parts.append(f'<text x="{x_r+7}" y="{ly2+2.5:.1f}" font-family="IBM Plex Sans,sans-serif" font-size="7.1" font-weight="{"700" if is_v or a["act_is_aa"] else "600"}" fill="{col}">#{a["act_place"]}/{a["act_field_size"]} {esc(a["display_name"].split()[0][0] + ". " + a["display_name"].split()[-1])}{star} <tspan font-family="IBM Plex Mono,monospace" font-size="6.5">({a["place_err"]:+.0f})</tspan></text>')

    parts.append("</svg>")
    return "".join(parts)

# ==============================================================================
# SVG 8: 2,424-RUNNER PREDICTED VS. ACTUAL SCATTER PLOT (PAGE 5)
# ==============================================================================
def build_national_scatter_svg(W=370, H=252):
    ml, mr, mt, mb = 40, 14, 22, 32
    pw, ph = W - ml - mr, H - mt - mb
    tmin, tmax = 240.0, 1620.0  # 4:00 to 27:00
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

    # Perfect y=x diagonal + +-10% band
    parts.append(f'<line x1="{sx(tmin):.1f}" y1="{sy(tmin):.1f}" x2="{sx(tmax):.1f}" y2="{sy(tmax):.1f}" stroke="#132c54" stroke-width="1.2" stroke-dasharray="4,3"/>')
    parts.append(f'<text x="{sx(1450):.1f}" y="{sy(1510):.1f}" font-family="IBM Plex Sans,sans-serif" font-size="6.6" font-weight="700" fill="#132c54" text-anchor="end">Perfect Forecast (y = x)</text>')
    parts.append(f'<text x="{W-mr-4}" y="{H-mb-6}" text-anchor="end" font-family="IBM Plex Sans,sans-serif" font-size="6.5" font-weight="600" fill="#0d7a47">Below line = Ran FASTER than Forecast</text>')

    # Plot all non-Aquinas points first (subsampled visually? No, 2,413 tiny dots is super crisp in vector SVG!)
    for a in ATHS:
        if a["is_dop"] and a["home_school"] == "Aquinas Academy":
            continue
        cx, cy = sx(a["pred_time_sec"]), sy(a["act_time_sec"])
        col = dist_col.get(a["dist_m"], "#64748b")
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="1.15" fill="{col}" opacity="0.32"/>')

    # Overlay Aquinas Academy in bold crimson & Victor family in gold-ringed crimson!
    for a in AQ:
        cx, cy = sx(a["pred_time_sec"]), sy(a["act_time_sec"])
        is_v = a["display_name"] in ("Diego Victor", "Marcela Victor")
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{"4.1" if is_v else "2.8"}" fill="#b8251e" stroke="{"#f5b800" if is_v else "#ffffff"}" stroke-width="{"1.5" if is_v else "0.9"}"/>')

    # Label Diego & Marcela
    dx, dy = sx(diego["pred_time_sec"]), sy(diego["act_time_sec"])
    mx, my = sx(marcela["pred_time_sec"]), sy(marcela["act_time_sec"])
    parts.append(f'<text x="{dx+6:.1f}" y="{dy+10:.1f}" font-family="IBM Plex Sans,sans-serif" font-size="6.9" font-weight="700" fill="#b8251e">Diego (-24s)</text>')
    parts.append(f'<text x="{mx+6:.1f}" y="{my+9:.1f}" font-family="IBM Plex Sans,sans-serif" font-size="6.9" font-weight="700" fill="#b8251e">Marcela (-24s)</text>')

    parts.append(f'<text x="{ml+pw/2:.1f}" y="{H-4}" text-anchor="middle" font-family="IBM Plex Sans,sans-serif" font-size="7.0" fill="#475569">Pre-Race Predicted Time (min) · Overall r = 0.938 (n = 2,424)</text>')
    parts.append(f'<text x="11" y="{mt+ph/2:.1f}" text-anchor="middle" transform="rotate(-90 11 {mt+ph/2:.1f})" font-family="IBM Plex Sans,sans-serif" font-size="7.0" fill="#475569">Actual Cedarville Time (min)</text>')
    parts.append("</svg>")
    return "".join(parts)

# ==============================================================================
# SVG 9: WESTERN PA HILL-STRENGTH RESIDUAL DENSITY COMPARISON (PAGE 5)
# ==============================================================================
def build_residual_kde_svg(W=350, H=252):
    ml, mr, mt, mb = 22, 16, 28, 34
    pw, ph = W - ml - mr, H - mt - mb
    xs = np.linspace(-100, 100, 120)
    def sx(v): return ml + (v + 100.0) / 200.0 * pw

    def kde(vals, bw):
        arr = np.array(vals, dtype=float)
        dens = np.zeros_like(xs)
        for v in arr:
            dens += np.exp(-0.5 * ((xs - v) / bw) ** 2)
        dens /= (len(arr) * bw * math.sqrt(2 * math.pi))
        return dens

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
        d_fill = f"M{sx(xs[0]):.1f},{H-mb:.1f} L" + " L".join(pts) + f" L{sx(xs[-1]):.1f},{H-mb:.1f} Z"
        d_line = "M" + " L".join(pts)
        return f'<path d="{d_fill}" fill="{col}" opacity="{fill_op}"/><path d="{d_line}" fill="none" stroke="{col}" stroke-width="{sw}"/>'

    parts.append(area_path(d_nat, "#475569", "0.14", "1.6"))
    parts.append(area_path(d_dop, "#5b359a", "0.16", "1.8"))
    parts.append(area_path(d_aq, "#b8251e", "0.20", "2.1"))

    # Median markers
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

# ==============================================================================
# SVG 10: ALL-AMERICAN RELIABILITY CALIBRATION CURVE (PAGE 6)
# ==============================================================================
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
    poly = " ".join(f"{sx(p):.1f},{sy(a):.1f}" for p, a, _ in pts)
    parts.append(f'<polyline points="{poly}" fill="none" stroke="#132c54" stroke-width="2.1"/>')
    for p, a, n in pts:
        cx, cy = sx(p), sy(a)
        r = 3.2 + 2.4 * math.sqrt(n / 1451.0)
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="#0d7a47" stroke="#ffffff" stroke-width="1.2"/>')
        if p < 5:
            lx, ly, anc = cx + 6, cy - 8, "start"
        elif a >= p:
            lx, ly, anc = cx - 4, cy - 9, "middle"
        else:
            lx, ly, anc = cx + 6, cy + 14, "middle"
        lx = min(W - mr - 24, max(ml + 18, lx))
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anc}" font-family="IBM Plex Mono,monospace" font-size="6.4" font-weight="700" fill="#132c54" paint-order="stroke" stroke="#faf8f3" stroke-width="3">{a:.0f}% <tspan fill="#646a76" font-weight="400">(n={n})</tspan></text>')

    parts.append(f'<text x="{ml+4}" y="{mt-7}" font-family="IBM Plex Sans,sans-serif" font-size="7.0" font-weight="700" fill="#132c54">Brier Score = {SUMMARY["aa_brier_score"]:.4f} · 7/7 (100%) Pgh CYO ≥50% Locks Won AA!</text>')
    parts.append(f'<text x="{ml+pw/2:.1f}" y="{H-4}" text-anchor="middle" font-family="IBM Plex Sans,sans-serif" font-size="7.0" fill="#475569">Pre-Race Predicted All-American Top-25 Probability</text>')
    parts.append(f'<text x="11" y="{mt+ph/2:.1f}" text-anchor="middle" transform="rotate(-90 11 {mt+ph/2:.1f})" font-family="IBM Plex Sans,sans-serif" font-size="7.0" fill="#475569">Actual Top-25 Hit Rate</text>')
    parts.append("</svg>")
    return "".join(parts)

# ==============================================================================
# BUILD TABLES & SECTIONS
# ==============================================================================
# Page 1: Aquinas 11-runner table
aq_table_rows = []
for a in AQ:
    is_v = a["display_name"] in ("Diego Victor", "Marcela Victor")
    row_cls = ' class="row-victor"' if is_v else (' class="row-aa"' if a["act_is_aa"] else "")
    dt_cls = "up-txt b" if a["time_err_sec"] < 0 else "muted"
    pl_cls = "up-txt b" if a["place_err"] < 0 else "muted"
    badge = '<span class="pill-aa">★ ALL-AMERICAN</span>' if a["act_is_aa"] else (
        '<span class="pill-cyo">CYO Champ Team</span>' if a["event_num"] == 11 else (
            '<span class="pill-surge">-50.5s Beat!</span>' if a["time_err_sec"] <= -45 else (
                '<span class="pill-surge">+35 Pl Surge</span>' if a["display_name"] == "Marcela Victor" else '<span class="muted">—</span>'
            )
        )
    )
    aq_table_rows.append(
        f'<tr{row_cls}>'
        f'<td class="b {"dop-txt" if is_v else ""}">{esc(a["display_name"])}</td>'
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

# Page 2: Diego's 5-runner Boys 6-8 team table + Diego's 7-race log
ev4_dop = sorted([a for a in ATHS if a["event_num"] == 4 and a["is_dop"]], key=lambda x: x["act_place"])
ev4_team_rows = []
for idx, a in enumerate(ev4_dop, 1):
    is_d = (a["display_name"] == "Diego Victor")
    is_aq = (a["home_school"] == "Aquinas Academy")
    cls = ' class="row-victor"' if is_d else (' class="row-aa"' if is_aq else "")
    ev4_team_rows.append(
        f'<tr{cls}><td class="num mono b">#{idx}</td>'
        f'<td class="b {"dop-txt" if is_d else ""}">{esc(a["display_name"])}</td>'
        f'<td>{esc(short_school(a["home_school"]))}</td>'
        f'<td class="num mono">{a["age"]}</td>'
        f'<td class="num mono muted">{a["pred_time_str"]}</td>'
        f'<td class="num mono b">{a["act_time_str"]} ({a["act_pace_mi"]})</td>'
        f'<td class="num mono up-txt b">{a["time_err_sec"]:+.1f}s</td>'
        f'<td class="num mono">#{a["act_place"]} / CYO #{a["act_cyo_place"]}</td>'
        f'<td class="num mono b">#{a["act_age_place"]}/{a["act_age_field_size"]} {"★" if a["act_is_aa"] else ""}</td></tr>'
    )

diego_races = sorted(pre_map[diego["id"]]["races_2026"], key=lambda r: r["date"])
diego_log_rows = []
for r in diego_races:
    diego_log_rows.append(
        f'<tr><td class="mono nw">{r["date"][5:]}</td><td>{esc(short_meet(r["meet"]))}</td>'
        f'<td class="num mono">{r["dist_m"]}m</td><td class="num mono">{r["time_str"]}</td>'
        f'<td class="num mono">{r["pace_mi"]}/mi</td><td class="num mono nw">#{r["place"]}/{r["field_size"]}</td></tr>'
    )
diego_log_rows.append(
    f'<tr class="row-victor"><td class="mono nw b">11-21</td><td class="b dop-txt">CCCNYC Nationals (Cedarville)</td>'
    f'<td class="num mono b">2000m</td><td class="num mono b dop-txt">{diego["act_time_exact"]}</td>'
    f'<td class="num mono b up-txt nw">{diego["act_pace_mi"]}/mi (PR!)</td><td class="num mono b nw">Age #9/36 ★AA</td></tr>'
)

# Page 3: Marcela's 10-race log
marcela_races = sorted(pre_map[marcela["id"]]["races_2026"], key=lambda r: r["date"])
marcela_log_rows = []
for r in marcela_races:
    is_3k = r["dist_m"] >= 2900
    cls = ' style="background:#f5f2fa"' if is_3k else ""
    marcela_log_rows.append(
        f'<tr{cls}><td class="mono nw">{r["date"][5:]}</td><td>{esc(short_meet(r["meet"]))}</td>'
        f'<td class="num mono">{r["dist_m"]}m</td><td class="num mono">{r["time_str"]}</td>'
        f'<td class="num mono">{r["pace_mi"]}/mi</td><td class="num mono nw">#{r["place"]}/{r["field_size"]}</td></tr>'
    )
marcela_log_rows.append(
    f'<tr class="row-victor"><td class="mono nw b">11-21</td><td class="b dop-txt">CCCNYC Nationals (Cedarville 3K)</td>'
    f'<td class="num mono b">3000m</td><td class="num mono b dop-txt">{marcela["act_time_exact"]}</td>'
    f'<td class="num mono b up-txt nw">{marcela["act_pace_mi"]}/mi (3K PR!)</td><td class="num mono b nw">Ov #144 · Age #57</td></tr>'
)

# Page 4: Other 9 Aquinas spotlight cards
other_aq = [a for a in AQ if a["display_name"] not in ("Diego Victor", "Marcela Victor")]
spot_notes = {
    "Linus Gruber": "<b>#3 in the Nation for Age 7 (National Bronze)!</b> Blasted 6:33/mi pace (30.1s ahead of forecast) and #2 among all CYO 7-year-olds to anchor Pittsburgh CYO Boys 6–8's 56-point tie for 2nd.",
    "Cora Donahue": "<b>+51.3-Place National Surge!</b> Dropped 32.1s off forecast (7:24/mi) to lead all Aquinas 9–10 girls at #85/244 (#13 CYO, Age-9 #30/104 — just 5 spots shy of All-American) for #3 CYO Podium Pgh A.",
    "Angela Gallagher": "<b>+38.3-Place Surge!</b> Crushed forecast by 17.9s (7:33/mi) to finish #104/244 (#19 CYO, Age-9 #38/104) as a key top-3 scorer for Pittsburgh CYO B (#4 CYO, 77 pts).",
    "Noah Malone": "<b>BREAKOUT ALL-AMERICAN (#14 Age-11 / 160)!</b> Jumped <b>+70.1 overall places</b> from #130 forecast to #60/373 in 11:33.1 (6:12/mi, -26.4s, #2 CYO Age-11) — largest place beat on Aquinas!",
    "Joey Edwards": "<b>Pinpoint Model Accuracy!</b> Finished #156/373 vs #154.7 predicted (+1.3 places!) and #23 CYO in 12:31.4 (6:43/mi), helping Pittsburgh CYO Boys 11–12 capture CYO Silver (#2) & #6 Nationally.",
    "Katalina Barnett": "<b>Biggest Time Beat on Aquinas (-50.5s)!</b> Broke 7:00/mi across 4,000m (17:15.4, 6:57/mi) to jump +58.4 places (#120/235, #14 CYO) and power Pittsburgh CYO Girls 13–14 to CYO Silver (#2).",
    "Ciara McBride": "<b>+43.2-Place Surge!</b> Beat forecast by 32.5s (17:42.8, 7:08/mi) to finish #140/235 (#19 CYO) right behind Katalina on Pittsburgh CYO's CYO National Runner-Up 13–14 Girls squad.",
    "Charlotte Austin": "<b>Closest Time Bullseye on Aquinas (+2.7s / 0.24%)!</b> Ran 18:53.4 vs 18:50.7 projected and still moved up +12.6 places (#193/235, Age-14 #74/87) as a steady senior leader on CYO Silver 13–14G.",
    "John Austin": "<b>CYO NATIONAL TEAM CHAMPION (23 pts)!</b> Ran sub-6:00/mi across 4K (14:37.9, 5:53/mi, -12.5s) to climb +31.7 places to #79/307, #8 CYO & #5 CYO Age-14 on Pittsburgh's #6-in-the-Nation squad!",
}
spot_cards_html = []
for a in other_aq:
    tag = '<span class="pill-aa">★ ALL-AMERICAN</span>' if a["act_is_aa"] else (
        '<span class="pill-cyo">CYO CHAMPION</span>' if a["event_num"] == 11 else f'<span class="pill-muted">{a["event_short"]}</span>'
    )
    spot_cards_html.append(f"""
    <div class="spot-card {"spot-aa" if a["act_is_aa"] else ""}">
      <div class="spot-top">
        <div class="nw"><span class="b" style="font-size:8.4pt">{esc(a["display_name"])}</span> <span class="muted" style="font-size:6.8pt">Age {a["age"]} · {a["event_short"]}</span></div>
        {tag}
      </div>
      <div class="spot-stats mono">
        <span>Act <b>{a["act_time_str"]}</b> ({a["act_pace_mi"]}/mi)</span>
        <span>Pred {a["pred_time_str"]} (<b class="{"up-txt" if a["time_err_sec"]<0 else "muted"}">{a["time_err_sec"]:+.1f}s</b>)</span>
        <span>Ov <b>#{a["act_place"]}</b> · Age <b>#{a["act_age_place"]}/{a["act_age_field_size"]}</b></span>
      </div>
      <div class="spot-note">{spot_notes[a["display_name"]]}</div>
    </div>""")

# Page 5: Tier & Event Calibration tables
tier_order = [
    "Tier 1+ (2026 + CCCNYC Vet)",
    "Tier 1 (2026 Empirical)",
    "Tier 2 (CCCNYC Veteran)",
    "Tier 2M (Prior Season Empirical)",
    "Tier 3 (Club × Age Prior)",
]
tier_rows_html = []
for t in tier_order:
    if t not in TIER_STATS: continue
    st = TIER_STATS[t]
    tier_rows_html.append(
        f'<tr><td class="b">{esc(t)}</td><td class="num mono">{st["n"]}</td>'
        f'<td class="num mono">{st["median_bias_sec"]:+.1f}s</td>'
        f'<td class="num mono">{st["median_abs_sec"]:.1f}s</td>'
        f'<td class="num mono">{st["mae_sec"]:.1f}s</td>'
        f'<td class="num mono b">{st["mape_pct"]:.2f}%</td>'
        f'<td class="num mono">{st["p10_p90_cov"]:.1f}%</td></tr>'
    )

ev_cal_rows = []
for es in EVENTS:
    if es["event_num"] == 5: continue
    ev_cal_rows.append(
        f'<tr><td class="b">Ev {es["event_num"]} · {es["short"]}</td>'
        f'<td class="num mono">{es["matched_finishers"]}/{es["actual_finishers"]}</td>'
        f'<td class="num mono">{es["median_time_bias_sec"]:+.1f}s</td>'
        f'<td class="num mono">{es["median_abs_err_sec"]:.1f}s</td>'
        f'<td class="num mono">{es["mape_pct"]:.2f}%</td>'
        f'<td class="num mono b">{es["time_r"]:.3f}</td>'
        f'<td class="num mono">{es["p10_p90_coverage_pct"]:.1f}%</td></tr>'
    )

# Page 6: 8-for-8 CYO Champions + 10 Pittsburgh CYO Squads + 15 Pittsburgh CYO All-Americans
dop_squad_rows = []
for ev_n in [3, 4, 6, 7, 8, 9, 10, 11]:
    ev_nat = [t for t in TEAMS if t["event_num"] == ev_n and t["is_dop"] and t["lens"] == "nat"]
    ev_cyo = {t["team"]: t for t in TEAMS if t["event_num"] == ev_n and t["is_dop"] and t["lens"] == "cyo"}
    es = next(e for e in EVENTS if e["event_num"] == ev_n)
    cyo_champ_pred = es["cyo_top3_pred"][0]["team"] if es["cyo_top3_pred"] else "—"
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
aa_pills_html = []
for a in dop_aa_list:
    is_aq = (a["home_school"] == "Aquinas Academy")
    cls = "aa-badge aa-aq" if is_aq else "aa-badge"
    aa_pills_html.append(
        f'<span class="{cls}"><b>#{a["act_age_place"]}</b> {esc(a["display_name"])} '
        f'<span class="mono" style="font-size:6.5pt">(Age {a["age"]} · {a["act_time_str"]} · {esc(short_school(a["home_school"]))})</span></span>'
    )

# Assemble 6-Page Editorial HTML
html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Aquinas Academy · 2026 CCCNYC Nationals Post-Race Report &amp; Model Audit</title>
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

/* Masthead */
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
.mh-eyebrow {{
  font-family: "IBM Plex Mono", monospace;
  font-size: 7.0pt;
  letter-spacing: 0.11em;
  text-transform: uppercase;
  color: #f3c44d;
  font-weight: 600;
  margin-bottom: 3px;
}}
.masthead h1 {{
  font-family: "Fraunces", Georgia, serif;
  font-size: 18pt;
  line-height: 1.08;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 3px;
}}
.mh-sub {{ font-size: 7.7pt; color: #dbe5f3; }}
.mh-date {{ text-align: right; border-left: 1px solid rgba(255,255,255,0.22); padding-left: 12px; flex-shrink: 0; }}
.mh-date .big {{ font-family: "Fraunces", Georgia, serif; font-size: 11.2pt; font-weight: 700; color: #ffffff; }}
.mh-date .sm {{ font-family: "IBM Plex Mono", monospace; font-size: 6.8pt; color: #c7d5ea; margin-top: 2px; }}

/* Interior Page Header */
.pg-hdr {{
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  border-bottom: 2px solid #132c54;
  padding-bottom: 5px;
  margin-bottom: 8px;
}}
.pg-hdr .eyebrow {{
  font-family: "IBM Plex Mono", monospace;
  font-size: 6.9pt;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: #b8251e;
  font-weight: 700;
}}
.pg-hdr h1 {{
  font-family: "Fraunces", Georgia, serif;
  font-size: 14.5pt;
  line-height: 1.12;
  color: #132c54;
  font-weight: 700;
  margin-top: 1px;
}}
.pg-hdr .hdr-meta {{ text-align: right; font-size: 7.4pt; flex-shrink: 0; }}

/* KPI Strip */
.kpi-strip {{
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  background: #f7f5ef;
  border-top: 1px solid #dbd6ca;
  border-bottom: 1.5px solid #132c54;
  padding: 6px 2px;
  margin-bottom: 9px;
}}
.kpi-cell {{ text-align: center; padding: 0 4px; border-right: 1px solid #ddd8cc; }}
.kpi-cell:last-child {{ border-right: none; }}
.kpi-cell .v {{ font-family: "IBM Plex Mono", monospace; font-size: 12.2pt; font-weight: 700; color: #132c54; line-height: 1.12; }}
.kpi-cell.dop .v {{ color: #b8251e; }}
.kpi-cell.up .v {{ color: #0d7a47; }}
.kpi-cell.cyo .v {{ color: #5b359a; }}
.kpi-cell .l {{ font-size: 6.4pt; text-transform: uppercase; letter-spacing: 0.05em; color: #5f6673; font-weight: 600; margin-top: 2px; }}

/* Spotlight Hero Banner (Diego & Marcela) */
.hero-banner {{
  background: linear-gradient(135deg, #fdf3f2 0%, #f8f6f0 100%);
  border: 1px solid #e7c6c3;
  border-left: 4.5px solid #b8251e;
  border-radius: 5px;
  padding: 8px 12px;
  margin-bottom: 9px;
  display: grid;
  grid-template-columns: 1.35fr 1fr;
  gap: 10px;
  align-items: center;
}}
.hb-kicker {{ font-family: "IBM Plex Mono", monospace; font-size: 6.8pt; font-weight: 700; color: #b8251e; text-transform: uppercase; letter-spacing: 0.08em; }}
.hb-title {{ font-family: "Fraunces", Georgia, serif; font-size: 14pt; color: #132c54; font-weight: 700; line-height: 1.15; margin: 2px 0 3px; }}
.hb-copy {{ font-size: 7.7pt; color: #2b3444; line-height: 1.34; }}
.hb-metrics {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 5px; }}
.hb-box {{ background: #ffffff; border: 1px solid #e3ded2; border-radius: 4px; padding: 5px 7px; text-align: center; }}
.hb-box .v {{ font-family: "IBM Plex Mono", monospace; font-size: 11pt; font-weight: 700; color: #132c54; }}
.hb-box.g .v {{ color: #0d7a47; }}
.hb-box.r .v {{ color: #b8251e; }}
.hb-box .l {{ font-size: 6.3pt; color: #646a76; text-transform: uppercase; letter-spacing: 0.04em; margin-top: 1px; }}

/* Section Bars */
.ed-sec {{ margin-bottom: 8px; }}
.sec-bar {{
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 3.5px 8px;
  border-radius: 3px;
  font-size: 7.9pt;
  font-weight: 700;
  margin-bottom: 4px;
}}
.sec-bar.navy {{ background: #132c54; color: #ffffff; }}
.sec-bar.crimson {{ background: #b8251e; color: #ffffff; }}
.sec-bar.subtle {{ background: #f2efe7; color: #132c54; border-left: 3px solid #132c54; }}
.sec-bar .sec-sub {{ font-weight: 400; font-size: 6.9pt; opacity: 0.88; }}

/* Split Grids */
.split-62-38 {{ display: grid; grid-template-columns: 62% 36.5%; gap: 1.5%; align-items: start; }}
.split-50-50 {{ display: grid; grid-template-columns: 49.2% 49.2%; gap: 1.6%; align-items: start; }}
.spot-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }}
.spot-card {{ background: #faf9f5; border: 1px solid #e4e0d5; border-radius: 4px; padding: 6px 7px; }}
.spot-card.spot-aa {{ background: #f2faf5; border-color: #a9dec0; border-left: 3px solid #0d7a47; }}
.spot-top {{ display: flex; justify-content: space-between; align-items: center; gap: 4px; margin-bottom: 3px; }}
.spot-stats {{ display: flex; flex-wrap: wrap; gap: 6px; font-size: 6.8pt; color: #334155; padding: 3px 0; border-top: 1px solid #e6e2d8; border-bottom: 1px solid #e6e2d8; margin-bottom: 3px; }}
.spot-note {{ font-size: 6.9pt; color: #2b3444; line-height: 1.28; }}

/* Tables */
table {{ width: 100%; border-collapse: collapse; font-size: 7.3pt; }}
th {{
  text-align: left;
  font-family: "IBM Plex Mono", monospace;
  font-size: 6.4pt;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #555c69;
  padding: 3.5px 5px;
  border-bottom: 1.4px solid #132c54;
  background: #f7f5ef;
}}
td {{ padding: 3.2px 5px; border-bottom: 1px solid #ece8de; vertical-align: middle; }}
tr.row-victor td {{ background: #fdf1f0; }}
tr.row-aa td {{ background: #f3faf6; }}

/* Pills */
.pill-aa {{ display: inline-block; background: #0d7a47; color: #ffffff; font-family: "IBM Plex Mono", monospace; font-size: 6.2pt; font-weight: 700; padding: 1.5px 5px; border-radius: 99px; white-space: nowrap; }}
.pill-cyo {{ display: inline-block; background: #5b359a; color: #ffffff; font-family: "IBM Plex Mono", monospace; font-size: 6.2pt; font-weight: 700; padding: 1.5px 5px; border-radius: 99px; white-space: nowrap; }}
.pill-surge {{ display: inline-block; background: #e8f5ee; color: #0d7a47; border: 1px solid #b2dfc5; font-family: "IBM Plex Mono", monospace; font-size: 6.2pt; font-weight: 700; padding: 1px 5px; border-radius: 99px; white-space: nowrap; }}
.pill-muted {{ display: inline-block; background: #eeeae0; color: #475569; font-family: "IBM Plex Mono", monospace; font-size: 6.2pt; font-weight: 600; padding: 1px 5px; border-radius: 99px; }}

.callout {{
  background: #f7f5ef;
  border-left: 3.5px solid #132c54;
  padding: 6px 9px;
  border-radius: 3px;
  font-size: 7.4pt;
  line-height: 1.33;
  color: #263040;
}}
.callout.crimson {{ background: #fdf3f2; border-left-color: #b8251e; }}
.callout.green {{ background: #f2faf5; border-left-color: #0d7a47; }}

.aa-badge {{
  display: inline-block;
  background: #f6f4ee;
  border: 1px solid #dcd7ca;
  border-radius: 4px;
  padding: 2.5px 6px;
  margin: 2px 3px 2px 0;
  font-size: 7.0pt;
}}
.aa-badge.aa-aq {{ background: #fdf1f0; border-color: #e2a4a0; color: #8c1a15; }}

.pfoot {{
  margin-top: auto;
  padding-top: 5px;
  border-top: 1px solid #d8d4c8;
  display: flex;
  justify-content: space-between;
  font-size: 6.9pt;
  color: #717782;
}}
</style>
</head>
<body>

<!-- PAGE 1: COVER & AQUINAS ACADEMY EXECUTIVE SCORECARD -->
<div class="page">
  <div class="masthead">
    <div>
      <div class="mh-eyebrow">2026 CCCNYC &amp; CYO National Championships · Official Post-Race Calibration &amp; School Dossier</div>
      <h1>Aquinas Academy · Cedarville Actuals vs. Predictions</h1>
      <div class="mh-sub">Frozen Pre-Race Snapshot (<span class="mono">pre-race-2026-11-21</span>) Audited Against Official FinishTiming Results · <b>2,424 / 2,441 (99.3%)</b> Matched</div>
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
      <span>Aquinas Academy · Complete 11-Runner Predicted vs. Actual Scorecard</span>
      <span class="sec-sub">Negative Δt = Ran FASTER than Pre-Race Forecast · ★ = Single-Year National All-American (Top 25)</span>
    </div>
    <table>
      <thead>
        <tr>
          <th>Runner</th><th>Race</th><th class="num">Age</th><th class="num">Pred Time</th><th class="num">Act Time</th>
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
      <span class="sec-sub">Aquinas beat forecasts by a median of -24.0s while the rest of the nation ran +8.6s slower (a 32.6s Western PA advantage!)</span>
    </div>
    {build_aq_diverging_svg()}
  </div>

  <div class="callout green">
    <b>Headline Takeaway — Western PA Hills Built Cedarville Flyers:</b> While the non-Pittsburgh national field (2,361 finishers) averaged <b>+8.6s slower</b> than pre-race projections, all 11 Aquinas Academy runners crushed expectations by a median of <b>-24.0 seconds</b> and <b>+29.1 overall places</b>! Aquinas produced <b>3 Single-Year National All-Americans</b> (<b>Linus Gruber</b> #3 Age-7 Bronze, <b>Diego Victor</b> #9 Age-6, <b>Noah Malone</b> #14 Age-11), a <b>CYO National Team Champion</b> (<b>John Austin</b>, 13–14B), and helped <b>9 of 10 Pittsburgh CYO squads</b> reach the CYO National Podium!
  </div>

  <div class="pfoot">
    <span>Aquinas Academy &amp; Pittsburgh CYO · 2026 CCCNYC Post-Race Report · Official Source: FinishTiming Meet #10720716</span>
    <span class="mono">Page 1 of 6</span>
  </div>
</div>

<!-- PAGE 2: DEEP DIVE #1 — DIEGO VICTOR -->
<div class="page">
  <div class="pg-hdr">
    <div>
      <div class="eyebrow">INDIVIDUAL PERFORMANCE DEEP DIVE #1 · EVENT 4 · BOYS 6–8 2,000 METERS</div>
      <h1>Diego Victor (Age 6) — National All-American &amp; CYO Podium Closer</h1>
    </div>
    <div class="hdr-meta">
      <div class="mono b dop-txt">9:22.4 (7:33/mi) · Age #9 / 36</div>
      <div class="muted">Aquinas Academy (Gr. 1) · Pittsburgh CYO</div>
    </div>
  </div>

  <div class="hero-banner">
    <div>
      <div class="hb-kicker">★ Top-10 Single-Year National All-American · #3 CYO Age-6 Bronze</div>
      <div class="hb-title">Joined Late. Ran a 18.5-Second 2K PR. Delivered a CYO Trophy.</div>
      <div class="hb-copy">
        Added as Pittsburgh CYO's vital 5th runner in Boys 6–8, 6-year-old <b>Diego Victor</b> ran the race of his life on Cedarville's grass: <b>9:22.369 (7:33/mi)</b> — smashing our 9:46.3 pre-race projection by <b>23.9 seconds</b> and beating his previous 2K PR (9:40.86 at Seelos #2) by <b>18.5 seconds</b>! He finished <b>#9 in the nation</b> among Age-6 boys (within 0.7 places of our #8.3 forecast and just 6.4s shy of #7!) and completed Pittsburgh CYO's 5-boy scoring squad for a <b>56–56 tie for 2nd / #3 CYO National Trophy</b>.
      </div>
    </div>
    <div class="hb-metrics">
      <div class="hb-box r"><div class="v">#9 / 36</div><div class="l">Age-6 National (★AA)</div></div>
      <div class="hb-box g"><div class="v">-23.9s</div><div class="l">Faster Than Forecast</div></div>
      <div class="hb-box"><div class="v">7:33/mi</div><div class="l">2K PR (vs 7:52 Pred)</div></div>
      <div class="hb-box r"><div class="v">#3 CYO</div><div class="l">56-Pt Team Trophy!</div></div>
    </div>
  </div>

  <div class="split-62-38 ed-sec">
    <div>
      <div class="sec-bar subtle">
        <span>Diego's Complete 2026 Pace Progression (Aug 25 &#8594; Nov 21 Nationals)</span>
        <span class="sec-sub">-1:22/mi season drop!</span>
      </div>
      {build_season_pace_svg(diego, "#b8251e")}
    </div>
    <div>
      <div class="sec-bar subtle">
        <span>Age-6 National Top 12 (2K)</span>
        <span class="sec-sub">○ Pred &#8594; ● Act</span>
      </div>
      {build_diego_age6_svg()}
    </div>
  </div>

  <div class="ed-sec">
    <div class="sec-bar navy">
      <span>The 5th-Man Hero Effect: Pittsburgh CYO Boys 6–8 Tied for 2nd in CYO (56–56) &amp; Won #3 Trophy!</span>
      <span class="sec-sub">Without Diego's late addition, Pgh CYO had 4 boys (incomplete) — with Diego, they crushed #4 Toledo CYO B by 59 pts (56 vs 115)!</span>
    </div>
    <table>
      <thead>
        <tr>
          <th class="num">Team #</th><th>Runner</th><th>Feeder School</th><th class="num">Age</th>
          <th class="num">Pred Time</th><th class="num">Actual (Pace)</th><th class="num">Δt</th>
          <th class="num">Ov / CYO</th><th class="num">Age Place</th>
        </tr>
      </thead>
      <tbody>{"".join(ev4_team_rows)}</tbody>
    </table>
  </div>

  <div class="split-62-38">
    <div>
      <div class="sec-bar subtle"><span>Diego Victor · Complete 7-Race 2026 XC Log</span><span class="sec-sub">Entered at FinishTiming as "Victor Diego" (Bib verified)</span></div>
      <table>
        <thead><tr><th>Date</th><th>Meet</th><th class="num">Dist</th><th class="num">Time</th><th class="num">Pace</th><th class="num">Finish</th></tr></thead>
        <tbody>{"".join(diego_log_rows)}</tbody>
      </table>
    </div>
    <div class="callout crimson" style="align-self:stretch">
      <b>Diego's Scouting Breakdown:</b><br><br>
      <b>• Pinpoint Place Calibration:</b> Pre-race model projected Overall <b>#131.1</b> &amp; Age-6 <b>#8.3</b>; Diego ran Overall <b>#133 / 220</b> (+1.9 pl) &amp; Age-6 <b>#9 / 36</b> (+0.7 pl) — beating #4-seeded Hampton Hill (Grassroots KY, 9:30.5) by 8.1 seconds!<br><br>
      <b>• Massive Margin Over #25 Cutline:</b> Finished <b>1:17.3 ahead</b> of the official Age-6 All-American #25 cutline (10:39.7).<br><br>
      <b>• 1st-Grade Upside:</b> Dropping from 8:55/mi (Aug 25) to 7:33/mi (Nov 21) in one fall sets Diego up as a top-5 Age-7 national contender in 2027!
    </div>
  </div>

  <div class="pfoot">
    <span>Diego Victor (Age 6 · Aquinas Academy · Pittsburgh CYO) · Official FinishTiming Time: 9:22.369</span>
    <span class="mono">Page 2 of 6</span>
  </div>
</div>

<!-- PAGE 3: DEEP DIVE #2 — MARCELA VICTOR -->
<div class="page">
  <div class="pg-hdr">
    <div>
      <div class="eyebrow">INDIVIDUAL PERFORMANCE DEEP DIVE #2 · EVENT 6 · GIRLS 9–10 3,000 METERS</div>
      <h1>Marcela Victor (Age 9) — 24-Second Breakthrough &amp; 35-Place Surge</h1>
    </div>
    <div class="hdr-meta">
      <div class="mono b dop-txt">14:37.7 (7:51/mi) · Ov #144 / 244</div>
      <div class="muted">Aquinas Academy (Gr. 3) · Pittsburgh CYO B</div>
    </div>
  </div>

  <div class="hero-banner">
    <div>
      <div class="hb-kicker">Massive 3K Personal Best · 1:05.3 Faster Than Prior 3K · +35.1 Places Ahead of Forecast</div>
      <div class="hb-title">1:17/Mile Season Transformation Capped by a Sub-8:00/mi 3K!</div>
      <div class="hb-copy">
        Stepping up to the 3,000m national championship distance as a 9-year-old 3rd-grader, <b>Marcela Victor</b> blasted <b>14:37.64 (7:51/mi)</b> — beating our 15:01.7 pre-race forecast by <b>24.0 seconds</b>, surging <b>+35.1 overall places</b> (#179.1 &#8594; #144/244) and <b>+15.9 Age-9 places</b> (#72.9 &#8594; #57/104), and obliterating her earlier Sept 12 Oakland Catholic 3K (15:42.96) by <b>1:05.3</b>! Running as Pittsburgh CYO B's #6 displacer (#28 CYO / #14 CYO Age-9), she directly displaced Toledo CYO A's #5–#7 runners.
      </div>
    </div>
    <div class="hb-metrics">
      <div class="hb-box g"><div class="v">-24.0s</div><div class="l">Faster Than Forecast</div></div>
      <div class="hb-box g"><div class="v">+35.1 pl</div><div class="l">Ov Surge (#179&#8594;#144)</div></div>
      <div class="hb-box r"><div class="v">-1:05.3</div><div class="l">3K Season PR Drop!</div></div>
      <div class="hb-box"><div class="v">#57 / 104</div><div class="l">Age-9 (#14 CYO Age-9)</div></div>
    </div>
  </div>

  <div class="split-62-38 ed-sec">
    <div>
      <div class="sec-bar subtle">
        <span>Marcela's Complete 10-Race 2026 Pace Progression (Aug 25 &#8594; Nov 21)</span>
        <span class="sec-sub">-1:17/mi drop · Purple = 3K</span>
      </div>
      {build_season_pace_svg(marcela, "#b8251e")}
    </div>
    <div>
      <div class="sec-bar subtle">
        <span>Ev 6 Girls 9–10 3K Pack Surge</span>
        <span class="sec-sub">Aquinas Trio Highlighted</span>
      </div>
      {build_marcela_pack_svg()}
    </div>
  </div>

  <div class="split-62-38">
    <div>
      <div class="sec-bar navy">
        <span>Marcela Victor · Complete 10-Race 2026 XC Season Log</span>
        <span class="sec-sub">Purple rows = full 3,000m championship distance</span>
      </div>
      <table>
        <thead><tr><th>Date</th><th>Meet</th><th class="num">Dist</th><th class="num">Time</th><th class="num">Pace</th><th class="num">Finish</th></tr></thead>
        <tbody>{"".join(marcela_log_rows)}</tbody>
      </table>
    </div>
    <div style="display:flex;flex-direction:column;gap:7px">
      <div class="callout green">
        <b>Endurance Leap (2K &#8594; 3K):</b><br>
        At the Oct 17 Diocesan Championship (1.50 mi), Marcela ran <b>7:45/mi</b>. Adding a full extra 600 meters at Cedarville Nationals, she held <b>7:51/mi</b> — only <b>6 sec/mi</b> of fade over 25% more distance (far stronger endurance than the typical 18–22 sec/mi youth 9-year-old fade!).
      </div>
      <div class="callout">
        <b>Pittsburgh CYO B Team Impact:</b><br>
        Pittsburgh CYO B finished <b>#4 in CYO (77 pts)</b> — just <b>8 points behind Pittsburgh CYO A (#3 CYO Podium, 69 pts)</b> and crushing #5 Phila. CYO White (151 pts) &amp; #6 LA-CYO A (152 pts) by 74+ points! Marcela's #25 CYO team-score spot displaced Toledo CYO A's 5th–7th runners (27–28–29).
      </div>
      <div class="callout crimson">
        <b>2027 Age-10 Outlook:</b><br>
        Returning CCCNYC veterans improve a median <b>13.4 sec/km (~40s over 3K)</b> from age 9 to age 10 — putting Marcela on a ~13:55–14:00 3K trajectory next fall!
      </div>
    </div>
  </div>

  <div class="pfoot">
    <span>Marcela Victor (Age 9 · Aquinas Academy · Pittsburgh CYO B) · Official FinishTiming Time: 14:37.64</span>
    <span class="mono">Page 3 of 6</span>
  </div>
</div>

<!-- PAGE 4: ALL 11 AQUINAS CRUSADERS — SLOPEGRAPH & 9 TEAMMATE SPOTLIGHTS -->
<div class="page">
  <div class="pg-hdr">
    <div>
      <div class="eyebrow">AQUINAS ACADEMY FULL DELEGATION · 11 OF 11 FINISHERS · CO-#1 PITTSBURGH CYO FEEDER SCHOOL</div>
      <h1>Aquinas Place-Surge Slopegraph &amp; Teammate Breakdowns</h1>
    </div>
    <div class="hdr-meta">
      <div class="mono b up-txt">9 / 11 Beat Time · 9 / 11 Beat Place</div>
      <div class="muted">Avg Place Gain: +29.1 spots per runner</div>
    </div>
  </div>

  <div class="ed-sec">
    <div class="sec-bar subtle">
      <span>Pre-Race Forecast Percentile &#8594; Actual Cedarville Finish Percentile (All 11 Aquinas Academy Runners)</span>
      <span class="sec-sub">Upward-sloping lines = outperformed forecast percentile · Crimson = Victor siblings · Green = Beat forecast</span>
    </div>
    {build_aq_slope_svg()}
  </div>

  <div class="ed-sec">
    <div class="sec-bar navy">
      <span>Individual Race Recaps · Aquinas Academy's 9 Other Cedarville Qualifiers</span>
      <span class="sec-sub">Green cards = Single-Year National All-Americans (Linus Gruber #3 Age-7, Noah Malone #14 Age-11)</span>
    </div>
    <div class="spot-grid">
      {"".join(spot_cards_html)}
    </div>
  </div>

  <div class="callout">
    <b>School-Wide Dominance Across All 5 Age Brackets:</b> Aquinas Academy sent qualifiers to 5 different national championship races (6–8B, 9–10G, 11–12B, 13–14G, 13–14B) and brought home <b>3 National All-American medals</b> (20% of Pittsburgh CYO's 15 total AAs from just 17% of the roster!), <b>1 CYO National Team Title</b> (John Austin, 13–14B), <b>2 CYO Silver Team Finishes</b> (11–12B, 13–14G), and <b>2 CYO Bronze Team Trophies</b> (6–8B, 9–10G A)!
  </div>

  <div class="pfoot">
    <span>Aquinas Academy (Gibsonia, PA) · 2026 CCCNYC &amp; CYO Nationals Post-Race Dossier</span>
    <span class="mono">Page 4 of 6</span>
  </div>
</div>

<!-- PAGE 5: NATIONAL MODEL CALIBRATION — 2,424 FINISHERS -->
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
        <span class="sec-sub">Crimson = Aquinas (★ Victor)</span>
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
      <span class="sec-sub">2K ran ~17.5s faster than historical venues; 3K/4K ran ~14s slower nationally — while Pittsburgh CYO ran fast everywhere!</span>
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
    <span class="mono">Page 5 of 6</span>
  </div>
</div>

<!-- PAGE 6: ALL-AMERICAN RELIABILITY, 8/8 CYO CHAMPIONS & PITTSBURGH CYO HONOR ROLL -->
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
    <span class="mono">Page 6 of 6</span>
  </div>
</div>

</body>
</html>
"""

OUT_HTML.write_text(html_doc, encoding="utf-8")
print(f"Wrote Aquinas Post-Race HTML: {OUT_HTML} ({len(html_doc):,} bytes)")

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
print(f"Generated Aquinas Post-Race PDF: {OUT_PDF} ({OUT_PDF.stat().st_size:,} bytes)")
