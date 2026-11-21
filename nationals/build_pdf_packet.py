import html as html_mod
import json
import math
import pathlib
import re
import subprocess

BASE = pathlib.Path(r"c:\Users\j_t_v\XC\nationals")
MASTER_FP = BASE / "data" / "cccnyc_2026_master.json"
GEO_FP = BASE / "data" / "us_states_geo.js"
APP_JS_FP = BASE / "app.js"
OUT_HTML = pathlib.Path(r"C:\Users\j_t_v\.gemini\antigravity\brain\fd1d52a6-9fa9-45a6-a634-3e07b1681514\scratch\pittsburgh_cyo_packet.html")
OUT_PDF = BASE / "data" / "pdfs" / "Pittsburgh_CYO_2026_CCCNYC_Race_Day_Packet.pdf"

data = json.loads(MASTER_FP.read_text(encoding="utf-8"))
geo_raw = GEO_FP.read_text(encoding="utf-8")
geo = json.loads(geo_raw[len("window.US_STATES_GEO = "):].rstrip().rstrip(";"))

app_txt = APP_JS_FP.read_text(encoding="utf-8")
m_cc = re.search(r"const CLUB_CITY_COORDS = \{(.*?)\n  \};", app_txt, re.S)
CLUB_CITY_COORDS = {}
for m in re.finditer(r'"([^"]+)":\s*\{\s*city:\s*"([^"]+)",\s*lon:\s*([-\d.]+),\s*lat:\s*([-\d.]+)\s*\}', m_cc.group(1)):
    CLUB_CITY_COORDS[m.group(1)] = {"city": m.group(2), "lon": float(m.group(3)), "lat": float(m.group(4))}

META = data["meta"]
EVENTS = {e["num"]: e for e in data["events"]}
TEAMS = data["teams"]
CLUBS = data["clubs"]
ATHLETES = [a for a in data["athletes"] if not a["is_duplicate_ghost"]]
ATH_MAP = {a["id"]: a for a in ATHLETES}

TEAM_STATE = {}
for c in CLUBS:
    if c.get("org") and c.get("state"):
        TEAM_STATE[c["org"]] = c["state"]
for t in TEAMS:
    if t.get("team") and t.get("state"):
        TEAM_STATE[t["team"]] = t["state"]
for a in ATHLETES:
    if a.get("team") and a.get("club_state"):
        TEAM_STATE[a["team"]] = a["club_state"]

def esc(s):
    return html_mod.escape(str("" if s is None else s))

def fmt_club(name, state=None):
    if not name or name == "Unattached":
        return name or ""
    st = state or TEAM_STATE.get(name, "")
    if not st or st == "USA":
        return name
    tag = "BM" if st == "INTL" else st
    if name.endswith(f"({tag})") or name.endswith(f"({st})"):
        return name
    return f"{name} ({tag})"

def smart_club_name(name, state=None, max_len=27):
    """Readable editorial club formatting — clean abbreviations before any ellipsis!"""
    if not name or name == "Unattached":
        return name or ""
    clean = (
        name.replace("Cross Country", "XC")
        .replace("Running Club", "RC")
        .replace("Track Club", "TC")
        .replace("Runing Club", "RC")
        .replace("Elementary School", "Elem.")
        .replace("Elementary", "Elem.")
        .replace("Training Academy", "Academy")
        .replace("Louisville Tigersharks", "Louisville TigerSharks")
    )
    full = fmt_club(clean, state)
    if len(full) <= max_len:
        return full
    st = state or TEAM_STATE.get(name, "")
    tag = "BM" if st == "INTL" else st
    suf = f" ({tag})" if (tag and tag != "USA") else ""
    base = clean
    if not suf:
        return base[:max_len - 1] + "…"
    base_max = max(8, max_len - len(suf) - 1)
    return f"{base[:base_max].rstrip()}…{suf}"

def fmt_time(sec):
    if sec is None:
        return "—"
    mn = int(sec // 60)
    rem = sec - mn * 60
    return f"{mn}:{rem:04.1f}"

def fmt_pace(sec, dist_m):
    if not sec or not dist_m:
        return "—"
    p = sec / (dist_m / 1609.344)
    mn = int(p // 60)
    sc = int(round(p - mn * 60))
    if sc == 60:
        mn += 1
        sc = 0
    return f"{mn}:{sc:02d}/mi"

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
        .replace("South Hills Catholic Academy", "South Hills Catholic")
        .replace("John F. Kennedy", "JFK Catholic")
        .replace("Guardian Angel Academy", "Guardian Angel")
    )

def medal_badge(rank):
    cls = {1: "m-gold", 2: "m-silver", 3: "m-bronze"}.get(rank, "m-slate")
    return f'<span class="medal {cls}">{rank}</span>'

# ==============================================================================
# 1. EDITORIAL VECTOR USA CHOROPLETH + CLUB CITIES SVG (CENSUS 10m LOWER-48)
# ==============================================================================
def build_usa_map_svg(W=560, H=340):
    phi1, phi2, phi0, lon0 = map(math.radians, (29.5, 45.5, 38.7, -96.0))
    n = 0.5 * (math.sin(phi1) + math.sin(phi2))
    C = math.cos(phi1) ** 2 + 2.0 * n * math.sin(phi1)
    rho0 = math.sqrt(C - 2.0 * n * math.sin(phi0)) / n

    def raw_proj(lon, lat):
        th = n * (math.radians(lon) - lon0)
        rho = math.sqrt(max(1e-9, C - 2.0 * n * math.sin(math.radians(lat)))) / n
        return rho * math.sin(th), -(rho0 - rho * math.cos(th))

    xs, ys = [], []
    for f in geo["features"]:
        polys = [f["geometry"]["coordinates"]] if f["geometry"]["type"] == "Polygon" else f["geometry"]["coordinates"]
        for poly in polys:
            for pt in poly[0]:
                px, py = raw_proj(pt[0], pt[1])
                xs.append(px); ys.append(py)
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    pad_x, pad_y = 8, 8
    scale = min((W - 2 * pad_x) / (maxx - minx), (H - 2 * pad_y) / (maxy - miny))
    ox = (W - (maxx - minx) * scale) / 2.0 - minx * scale
    oy = (H - (maxy - miny) * scale) / 2.0 - miny * scale

    def proj(lon, lat):
        px, py = raw_proj(lon, lat)
        return px * scale + ox, py * scale + oy

    st_tot = {}
    for c in CLUBS:
        if c["state"] not in ("USA", "INTL"):
            st_tot[c["state"]] = st_tot.get(c["state"], 0) + c["runners_count"]
    max_st = max(st_tot.values()) if st_tot else 1

    # Sophisticated slate-navy editorial sequential scale (light mist -> deep championship navy)
    NAVY_RAMP = [
        (225, 234, 244),
        (190, 211, 232),
        (146, 181, 216),
        (98, 146, 194),
        (56, 108, 165),
        (29, 73, 128),
        (19, 44, 84),
    ]
    def state_fill(cnt):
        if cnt <= 0:
            return "#f1efe8"
        t = (cnt / max_st) ** 0.56
        idx_f = min(len(NAVY_RAMP) - 1, max(0.0, t * (len(NAVY_RAMP) - 1)))
        i0 = int(math.floor(idx_f))
        i1 = min(len(NAVY_RAMP) - 1, i0 + 1)
        frac = idx_f - i0
        r = int(round(NAVY_RAMP[i0][0] + frac * (NAVY_RAMP[i1][0] - NAVY_RAMP[i0][0])))
        g = int(round(NAVY_RAMP[i0][1] + frac * (NAVY_RAMP[i1][1] - NAVY_RAMP[i0][1])))
        b = int(round(NAVY_RAMP[i0][2] + frac * (NAVY_RAMP[i1][2] - NAVY_RAMP[i0][2])))
        return f"rgb({r},{g},{b})"

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;height:auto">']

    # 1. State Polygons
    centroids = {}
    for f in geo["features"]:
        st = f["properties"]["code"]
        cnt = st_tot.get(st, 0)
        fill = state_fill(cnt)
        polys = [f["geometry"]["coordinates"]] if f["geometry"]["type"] == "Polygon" else f["geometry"]["coordinates"]
        d_cmds = []
        best_area, best_c = -1, None
        for poly in polys:
            for ri, ring in enumerate(poly):
                pts = [proj(p[0], p[1]) for p in ring]
                if not pts:
                    continue
                d_cmds.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
                if ri == 0 and len(pts) >= 4:
                    a2 = cx = cy = 0.0
                    for i in range(len(pts) - 1):
                        x0, y0 = pts[i]; x1, y1 = pts[i + 1]
                        cr = x0 * y1 - x1 * y0
                        a2 += cr; cx += (x0 + x1) * cr; cy += (y0 + y1) * cr
                    if abs(a2) > best_area and abs(a2) > 1e-3:
                        best_area = abs(a2)
                        best_c = (cx / (3.0 * a2), cy / (3.0 * a2))
        if best_c:
            centroids[st] = best_c
        parts.append(f'<path d="{"".join(d_cmds)}" fill="{fill}" stroke="#ffffff" stroke-width="0.9"/>')

    # 2. Clean State Labels ONLY on spacious states (skip dense dot-covered OH/IN/IL/MI/MD/NJ/DE/OK/TN so zero dots cover text!)
    spacious_labels = {
        "CA": (-4, 4), "CO": (0, 12), "KS": (-6, 3), "MO": (0, 10),
        "MN": (-3, -4), "AL": (0, 8), "GA": (4, 8), "VA": (4, 6), "NY": (2, -5),
    }
    for st, (dx, dy) in spacious_labels.items():
        if st not in centroids or not st_tot.get(st):
            continue
        cx, cy = centroids[st]
        cnt = st_tot[st]
        txt_col = "#ffffff" if cnt >= max_st * 0.28 else "#2c3542"
        parts.append(
            f'<text x="{cx + dx:.1f}" y="{cy + dy:.1f}" text-anchor="middle" font-family="IBM Plex Mono,Consolas,monospace" '
            f'font-size="8.5" font-weight="700" fill="{txt_col}" opacity="0.88">{st}</text>'
        )

    # 3. City Dots with gentle collision separation
    city_map = {}
    for c in CLUBS:
        if c["org"] == "Unattached" or c["state"] == "INTL":
            continue
        cc = CLUB_CITY_COORDS.get(c["org"])
        if not cc:
            continue
        e = city_map.setdefault(cc["city"], {
            "city": cc["city"], "lon": cc["lon"], "lat": cc["lat"],
            "runners": 0, "has_dop": False, "has_cyo": False
        })
        e["runners"] += c["runners_count"]
        if c["is_dop"]: e["has_dop"] = True
        if c["is_cyo"]: e["has_cyo"] = True

    max_city = max(e["runners"] for e in city_map.values())
    dots = []
    for e in sorted(city_map.values(), key=lambda x: -x["runners"]):
        px, py = proj(e["lon"], e["lat"])
        r = 2.1 + 3.4 * math.sqrt(e["runners"] / max_city)
        dots.append({**e, "x": px, "y": py, "ox": px, "oy": py, "r": r})

    for _ in range(14):
        for i in range(len(dots)):
            for j in range(i + 1, len(dots)):
                a, b = dots[i], dots[j]
                dx, dy = b["x"] - a["x"], b["y"] - a["y"]
                dist = math.hypot(dx, dy) or 0.01
                min_d = a["r"] + b["r"] + 0.8
                if dist < min_d:
                    push = (min_d - dist) * 0.38
                    ux, uy = dx / dist, dy / dist
                    a["x"] -= ux * push * 0.45; a["y"] -= uy * push * 0.45
                    b["x"] += ux * push * 0.55; b["y"] += uy * push * 0.55
            d = dots[i]
            d["x"] += (d["ox"] - d["x"]) * 0.14
            d["y"] += (d["oy"] - d["y"]) * 0.14

    for d in dots:
        col = "#b8251e" if d["has_dop"] else ("#5b359a" if d["has_cyo"] else "#d98200")
        parts.append(
            f'<circle cx="{d["x"]:.1f}" cy="{d["y"]:.1f}" r="{d["r"]:.1f}" '
            f'fill="{col}" fill-opacity="0.92" stroke="#ffffff" stroke-width="0.85"/>'
        )

    # 4. Cedarville Venue Star Pin
    cx, cy = proj(-83.806, 39.741)
    star_pts = []
    for k in range(10):
        ang = math.radians(-90 + k * 36)
        rad = 6.0 if k % 2 == 0 else 2.6
        star_pts.append(f"{cx + rad * math.cos(ang):.1f},{cy + rad * math.sin(ang):.1f}")
    parts.append(f'<polygon points="{" ".join(star_pts)}" fill="#f5c518" stroke="#132238" stroke-width="1.0"/>')

    # 5. Clean Bermuda inset badge
    bx, by = W - 104, H - 38
    parts.append(f'<rect x="{bx}" y="{by}" width="96" height="30" rx="5" fill="#f8f6f0" stroke="#cbc6b8" stroke-dasharray="2.5,2"/>')
    parts.append(f'<circle cx="{bx + 13}" cy="{by + 15}" r="3.2" fill="#d98200" stroke="#ffffff" stroke-width="0.9"/>')
    parts.append(f'<text x="{bx + 22}" y="{by + 13}" font-family="IBM Plex Sans,Segoe UI,sans-serif" font-size="8.2" font-weight="700" fill="#132238">Bermuda (BM)</text>')
    parts.append(f'<text x="{bx + 22}" y="{by + 24}" font-family="IBM Plex Mono,Consolas,monospace" font-size="7.3" fill="#6b6962">2 rnrs · INTL</text>')

    parts.append("</svg>")
    grad_css = ", ".join(state_fill(int(max_st * f)) for f in [0.02, 0.2, 0.45, 0.72, 1.0])
    top_states = sorted(st_tot.items(), key=lambda x: -x[1])
    return "".join(parts), grad_css, max_st, len(city_map), top_states

# ==============================================================================
# 2. EDITORIAL ALL-AMERICAN LIKELIHOOD CHART (TRACK RAILS + ZERO LINE OVERLAP!)
# ==============================================================================
def build_dop_aa_chart_svg(dop_aths, W=740, H=432):
    rows = sorted(dop_aths, key=lambda a: (-a["aa_age_prob"], a["aa_age_exp_rank"]))[:26]
    m_l, m_r, m_t, m_b = 266, 128, 12, 22
    row_h = (H - m_t - m_b) / len(rows)
    bar_max_w = W - m_l - m_r

    def sx(p):
        return m_l + (p / 100.0) * bar_max_w

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;height:auto">']

    # Subtle vertical gridlines behind everything
    for tick in (0, 25, 50, 75, 100):
        tx = sx(tick)
        col = "#c43225" if tick == 50 else "#e6e3da"
        dash = ' stroke-dasharray="3,2.5"' if tick == 50 else ""
        op = "0.55" if tick == 50 else "1"
        parts.append(f'<line x1="{tx:.1f}" y1="{m_t}" x2="{tx:.1f}" y2="{H - m_b}" stroke="{col}" stroke-width="0.9" opacity="{op}"{dash}/>')
        parts.append(f'<text x="{tx:.1f}" y="{H - 7}" text-anchor="middle" font-family="IBM Plex Mono,Consolas,monospace" font-size="8.2" font-weight="{"700" if tick == 50 else "400"}" fill="{"#b8251e" if tick == 50 else "#6b6962"}">{tick}%</text>')

    for i, a in enumerate(rows):
        y_row = m_t + i * row_h
        bh = max(7.2, row_h - 5.2)
        y0 = y_row + (row_h - bh) / 2.0
        yc = y0 + bh / 2.0
        ev_s = EVENTS[a["event_num"]]["short"].replace(" Girls", "G").replace(" Boys", "B")
        prob = a["aa_age_prob"]
        col = "#0d7a47" if prob >= 50 else ("#b8251e" if prob >= 20 else "#8a8880")

        # Full-width subtle track rail behind bar
        parts.append(f'<rect x="{sx(0):.1f}" y="{y0:.1f}" width="{bar_max_w:.1f}" height="{bh:.1f}" rx="{bh/2:.1f}" fill="#f1efe8"/>')

        # Left label: Name + Age/Race + School
        lbl = f'{a["display_name"]}'
        meta_s = f'Age {a["age"]} · {ev_s} · {short_school(a.get("home_school"))}'
        parts.append(
            f'<text x="{m_l - 8}" y="{yc + 2.9:.1f}" text-anchor="end" font-family="IBM Plex Sans,Segoe UI,sans-serif" '
            f'font-size="8.4" font-weight="{"700" if prob >= 50 else "600"}" fill="#132238">{esc(lbl)} '
            f'<tspan font-weight="400" font-size="7.7" fill="#6b6962">({esc(meta_s)})</tspan></text>'
        )

        # Rounded bar fill
        bw = max(3.5, sx(prob) - sx(0))
        parts.append(f'<rect x="{sx(0):.1f}" y="{y0:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="{bh/2:.1f}" fill="{col}" opacity="0.90"/>')

        # Value label inside a crisp white knockout pill so the 50% dashed line NEVER slices through text!
        rk_txt = f'{prob:.1f}%  · Age #{a["aa_age_exp_rank"]:.1f}/{a["aa_age_field_size"]}'
        txt_x = sx(prob) + 5
        pill_w = len(rk_txt) * 4.9 + 6
        parts.append(f'<rect x="{txt_x - 2.5:.1f}" y="{yc - 5.4:.1f}" width="{pill_w:.1f}" height="10.8" rx="2.5" fill="#ffffff" opacity="0.92"/>')
        parts.append(
            f'<text x="{txt_x:.1f}" y="{yc + 2.8:.1f}" font-family="IBM Plex Mono,Consolas,monospace" '
            f'font-size="7.9" font-weight="{"700" if prob >= 50 else "500"}" fill="{"#0a5f37" if prob >= 50 else "#132238"}">{rk_txt}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)

# ==============================================================================
# 3. EDITORIAL S-CURVE & TRAFFIC DENSITY (SEPARATE LEADER & LABEL LAYERS!)
# ==============================================================================
def build_scurve_svg(ev_num, ev_aths, W=740, H=270):
    aths = sorted(ev_aths, key=lambda a: a["exp_place"])
    n_tot = len(aths)
    m_l, m_r, m_t, m_b = 50, 18, 14, 36

    t_vals = [a["proj_time_sec"] for a in aths]
    dop_ts = [a["proj_time_sec"] for a in aths if a["is_dop"]]
    ymin = min(a["p10_time_sec"] for a in aths) * 0.985
    p98_t = sorted(t_vals)[min(len(t_vals) - 1, int(len(t_vals) * 0.985))]
    ymax = max(p98_t * 1.03, (max(dop_ts) * 1.08 if dop_ts else p98_t * 1.03))

    plot_w = W - m_l - m_r
    plot_h = H - m_t - m_b
    dens_h = 32.0

    def sx(pl):
        return m_l + ((pl - 1) / max(1, n_tot - 1)) * plot_w

    def sy(t):
        tc = min(ymax, max(ymin, t))
        return m_t + plot_h - ((tc - ymin) / max(1e-6, ymax - ymin)) * plot_h

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;height:auto">']
    parts.append(f'<rect x="{m_l}" y="{m_t}" width="{plot_w}" height="{plot_h}" fill="#faf9f5" stroke="#dedad0" stroke-width="0.8"/>')

    span = ymax - ymin
    step = 60 if span > 260 else (30 if span > 110 else 15)
    tcur = math.ceil(ymin / step) * step
    while tcur <= ymax:
        yy = sy(tcur)
        parts.append(f'<line x1="{m_l}" y1="{yy:.1f}" x2="{W - m_r}" y2="{yy:.1f}" stroke="#eae7de" stroke-width="0.7"/>')
        parts.append(f'<text x="{m_l - 6}" y="{yy + 3:.1f}" text-anchor="end" font-family="IBM Plex Mono,Consolas,monospace" font-size="8.2" fill="#6b6962">{fmt_time(tcur)[:-2]}</text>')
        tcur += step

    x_step = 50 if n_tot > 260 else (25 if n_tot > 120 else 20)
    for pl in [1] + list(range(x_step, n_tot + 1, x_step)):
        xx = sx(pl)
        parts.append(f'<line x1="{xx:.1f}" y1="{m_t}" x2="{xx:.1f}" y2="{H - m_b}" stroke="#efece3" stroke-width="0.7"/>')
        parts.append(f'<text x="{xx:.1f}" y="{H - m_b + 12}" text-anchor="middle" font-family="IBM Plex Mono,Consolas,monospace" font-size="8.2" fill="#6b6962">#{pl}</text>')
    parts.append(f'<text x="{m_l + plot_w / 2:.1f}" y="{H - 5}" text-anchor="middle" font-family="IBM Plex Sans,Segoe UI,sans-serif" font-size="8" fill="#6b6962">Expected Overall Finish Place (1 to {n_tot})  ·  Bottom bars = pack traffic density (runners per 10s window)</text>')

    # Traffic density histogram
    n_bins = 30
    bin_w = plot_w / n_bins
    bin_dens = []
    for bi in range(n_bins):
        i0 = int(bi * n_tot / n_bins)
        i1 = max(i0 + 1, int((bi + 1) * n_tot / n_bins))
        med_t = aths[(i0 + i1) // 2]["proj_time_sec"]
        bin_dens.append(sum(1 for a in aths if abs(a["proj_time_sec"] - med_t) <= 5.0))
    max_d = max(bin_dens) or 1
    for bi, cnt_10s in enumerate(bin_dens):
        bh = (cnt_10s / max_d) * dens_h
        parts.append(f'<rect x="{m_l + bi * bin_w:.1f}" y="{H - m_b - bh:.1f}" width="{max(1, bin_w - 1):.1f}" height="{bh:.1f}" fill="#132238" opacity="0.11"/>')

    # P10-P90 band
    upper = " ".join(f"{sx(a['exp_place']):.1f},{sy(a['p90_time_sec']):.1f}" for a in aths)
    lower = " ".join(f"{sx(a['exp_place']):.1f},{sy(a['p10_time_sec']):.1f}" for a in reversed(aths))
    parts.append(f'<polygon points="{upper} {lower}" fill="#1d5bbf" opacity="0.09"/>')

    # Field dots
    for a in aths:
        if a["is_dop"]:
            continue
        xx, yy = sx(a["exp_place"]), sy(a["proj_time_sec"])
        if a["is_cyo"]:
            parts.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="2.6" fill="#5b359a" opacity="0.72"/>')
        else:
            parts.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="1.8" fill="#8b8980" opacity="0.46"/>')

    # Top 3 Overall Gold Stars
    for a in aths[:3]:
        xx, yy = sx(a["exp_place"]), sy(a["proj_time_sec"])
        spts = [f"{xx + (5.2 if k % 2 == 0 else 2.2) * math.cos(math.radians(-90 + k * 36)):.1f},{yy + (5.2 if k % 2 == 0 else 2.2) * math.sin(math.radians(-90 + k * 36)):.1f}" for k in range(10)]
        parts.append(f'<polygon points="{" ".join(spts)}" fill="#f5c518" stroke="#132238" stroke-width="0.85"/>')

    # Separate layers so leader lines NEVER cross over runner label boxes!
    dop_in_ev = [a for a in aths if a["is_dop"]]
    leader_layer = []
    marker_layer = []
    label_layer = []
    placed_boxes = []

    for idx_d, a in enumerate(dop_in_ev):
        xx, yy = sx(a["exp_place"]), sy(a["proj_time_sec"])
        y10, y90 = sy(a["p10_time_sec"]), sy(a["p90_time_sec"])
        leader_layer.append(f'<line x1="{xx:.1f}" y1="{y10:.1f}" x2="{xx:.1f}" y2="{y90:.1f}" stroke="#b8251e" stroke-width="1.15" opacity="0.60"/>')
        r_d = 4.4
        dpts = f"{xx:.1f},{yy - r_d:.1f} {xx + r_d:.1f},{yy:.1f} {xx:.1f},{yy + r_d:.1f} {xx - r_d:.1f},{yy:.1f}"
        marker_layer.append(f'<polygon points="{dpts}" fill="#b8251e" stroke="#ffffff" stroke-width="1.0"/>')

        short_nm = f'{a["first_name"][0]}. {a["last_name"]} (#{round(a["exp_place"])})'
        lbl_w = len(short_nm) * 4.6 + 7
        cand_offsets = [
            (-lbl_w / 2 - 4, -15), (7, 15), (-lbl_w / 2 - 4, -29), (7, 29),
            (-lbl_w - 8, -4), (9, -15), (-lbl_w / 2, -43), (9, 43),
            (-lbl_w - 8, 15), (10, -29), (-lbl_w / 2, -57), (10, 57),
            (-lbl_w - 12, -43), (16, -43), (-lbl_w / 2, -71), (10, 71),
            (20, -57), (-lbl_w - 12, 29),
        ]
        if idx_d % 2 == 1:
            cand_offsets = [
                (7, 15), (-lbl_w / 2 - 4, -15), (7, 29), (-lbl_w / 2 - 4, -29),
                (9, -15), (-lbl_w - 8, 15), (9, 43), (-lbl_w / 2, -43),
                (10, 57), (-lbl_w / 2, -57), (10, 71), (-lbl_w / 2, -71),
                (16, -43), (-lbl_w - 12, -43), (20, -57), (-lbl_w - 12, 29),
            ]
        best_pos = None
        for ox, oy in cand_offsets:
            lx = min(W - m_r - lbl_w - 2, max(m_l + 2, xx + ox))
            ly = min(H - m_b - 10, max(m_t + 12, yy + oy))
            box = (lx - 2, ly - 9.5, lx + lbl_w + 2, ly + 3)
            if not any(not (box[2] < b[0] or box[0] > b[2] or box[3] < b[1] or box[1] > b[3]) for b in placed_boxes):
                best_pos = (lx, ly, box)
                break
        if not best_pos:
            lx = min(W - m_r - lbl_w - 2, max(m_l + 2, xx + 6))
            ly = min(H - m_b - 10, max(m_t + 12, yy - 15 - (idx_d % 5) * 13))
            best_pos = (lx, ly, (lx - 2, ly - 9.5, lx + lbl_w + 2, ly + 3))
        lx, ly, b_rect = best_pos
        placed_boxes.append(b_rect)
        leader_layer.append(f'<line x1="{xx:.1f}" y1="{yy:.1f}" x2="{lx + lbl_w / 2:.1f}" y2="{ly - 3:.1f}" stroke="#b8251e" stroke-width="0.65" opacity="0.50"/>')
        label_layer.append(f'<rect x="{lx - 2:.1f}" y="{ly - 8.6:.1f}" width="{lbl_w + 1:.1f}" height="11" rx="2.5" fill="#ffffff" stroke="#b8251e" stroke-width="0.55"/>')
        label_layer.append(f'<text x="{lx + 1.5:.1f}" y="{ly:.1f}" font-family="IBM Plex Sans,Segoe UI,sans-serif" font-size="7.6" font-weight="700" fill="#9e1e18">{esc(short_nm)}</text>')

    parts.extend(leader_layer)
    parts.extend(marker_layer)
    parts.extend(label_layer)

    # Clean floating legend pill
    parts.append(f'<rect x="{m_l + 6}" y="{m_t + 6}" width="316" height="17" rx="3.5" fill="#ffffff" opacity="0.94" stroke="#dedad0" stroke-width="0.6"/>')
    parts.append(f'<polygon points="{m_l+15},{m_t+10} {m_l+19},{m_t+14.5} {m_l+15},{m_t+19} {m_l+11},{m_t+14.5}" fill="#b8251e"/>')
    parts.append(f'<text x="{m_l + 23}" y="{m_t + 17.5}" font-family="IBM Plex Sans,Segoe UI,sans-serif" font-size="7.8" font-weight="700" fill="#9e1e18">Pittsburgh CYO ({len(dop_in_ev)})</text>')
    parts.append(f'<circle cx="{m_l + 112}" cy="{m_t + 14.5}" r="2.7" fill="#5b359a"/>')
    parts.append(f'<text x="{m_l + 118}" y="{m_t + 17.5}" font-family="IBM Plex Sans,Segoe UI,sans-serif" font-size="7.8" fill="#4a4944">Other CYO</text>')
    parts.append(f'<circle cx="{m_l + 169}" cy="{m_t + 14.5}" r="2.1" fill="#8b8980"/>')
    parts.append(f'<text x="{m_l + 175}" y="{m_t + 17.5}" font-family="IBM Plex Sans,Segoe UI,sans-serif" font-size="7.8" fill="#4a4944">National Field</text>')
    parts.append(f'<text x="{m_l + 238}" y="{m_t + 17.5}" font-family="IBM Plex Sans,Segoe UI,sans-serif" font-size="7.8" font-weight="700" fill="#b98000">&#9733; Top 3 Overall</text>')

    parts.append("</svg>")
    return "".join(parts)

# ==============================================================================
# 4. EDITORIAL TEAM MILE-PACE DENSITY RIDGELINE CHART (RICH, SPACIOUS WAVES)
# ==============================================================================
def build_ridgeline_svg(ev_num, W=460, H=235):
    ev = EVENTS[ev_num]
    dist_m = ev["dist_m"]
    scoring = sorted(
        [t for t in TEAMS if t["event_num"] == ev_num and t["scores_official_team"]],
        key=lambda t: t["nat"]["exp_rank"],
    )
    if not scoring:
        return '<div class="muted" style="padding:18px;text-align:center">No complete 5+ scoring teams</div>'

    chosen, seen_t = [], set()
    def add_t(t):
        if t["team"] not in seen_t and len(chosen) < 7:
            seen_t.add(t["team"]); chosen.append(t)
    for t in scoring[:4]: add_t(t)
    cyo_s = sorted([t for t in scoring if t["is_cyo"]], key=lambda t: t["cyo"]["exp_rank"])
    for t in cyo_s[:2]: add_t(t)
    for t in scoring:
        if t["is_dop"]: add_t(t)
    for t in scoring[4:]: add_t(t)
    chosen.sort(key=lambda t: t["nat"]["exp_rank"])

    team_paces, all_p = [], []
    for t in chosen:
        ps = sorted([ATH_MAP[rid]["proj_time_sec"] / (dist_m / 1609.344) for rid in t["runner_ids"] if rid in ATH_MAP])
        if ps:
            team_paces.append((t, ps))
            all_p.extend(ps[:7])

    p_min = max(240.0, min(all_p) - 20.0)
    p_max = max(all_p) + 24.0
    m_l, m_r, m_t, m_b = 152, 12, 18, 22
    plot_w = W - m_l - m_r
    n_rows = len(team_paces)
    row_step = (H - m_t - m_b) / max(1, n_rows)
    ridge_h = min(32.0, row_step * 1.48)

    def sx(p):
        return m_l + ((p - p_min) / max(1e-6, p_max - p_min)) * plot_w

    def fmt_p_lbl(ps):
        mn = int(ps // 60); sc = int(round(ps - mn * 60))
        if sc == 60: mn += 1; sc = 0
        return f"{mn}:{sc:02d}"

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;height:auto">']
    parts.append(f'<rect x="{m_l}" y="{m_t - 4}" width="{plot_w}" height="{H - m_t - m_b + 4}" fill="#faf9f5" rx="3"/>')

    span = p_max - p_min
    step = 60 if span > 210 else (30 if span > 95 else 15)
    tcur = math.ceil(p_min / step) * step
    while tcur <= p_max:
        xx = sx(tcur)
        parts.append(f'<line x1="{xx:.1f}" y1="{m_t - 4}" x2="{xx:.1f}" y2="{H - m_b}" stroke="#e8e4da" stroke-width="0.7"/>')
        parts.append(f'<text x="{xx:.1f}" y="{H - 7}" text-anchor="middle" font-family="IBM Plex Mono,Consolas,monospace" font-size="7.8" fill="#6b6962">{fmt_p_lbl(tcur)}/mi</text>')
        tcur += step

    grid_n = 60
    xs_pace = [p_min + (p_max - p_min) * (i / (grid_n - 1)) for i in range(grid_n)]
    bw = max(9.0, (p_max - p_min) * 0.054)

    for idx, (t, ps) in enumerate(team_paces):
        y_base = m_t + (idx + 0.86) * row_step
        col = "#b8251e" if t["is_dop"] else ("#5b359a" if t["is_cyo"] else ("#0d7a47" if idx == 0 else "#25589c"))
        pts_use = ps[:7]
        dens = [sum(math.exp(-0.5 * ((xv - p) / bw) ** 2) for p in pts_use) for xv in xs_pace]
        dmax = max(dens) or 1.0
        poly_pts = [f"{sx(xs_pace[0]):.1f},{y_base:.1f}"]
        line_pts = []
        for xv, dv in zip(xs_pace, dens):
            xx = sx(xv); yy = y_base - (dv / dmax) * ridge_h
            poly_pts.append(f"{xx:.1f},{yy:.1f}"); line_pts.append(f"{xx:.1f},{yy:.1f}")
        poly_pts.append(f"{sx(xs_pace[-1]):.1f},{y_base:.1f}")

        parts.append(f'<line x1="{m_l}" y1="{y_base:.1f}" x2="{W - m_r}" y2="{y_base:.1f}" stroke="#dbd7cc" stroke-width="0.75"/>')
        parts.append(f'<polygon points="{" ".join(poly_pts)}" fill="{col}" fill-opacity="0.22"/>')
        parts.append(f'<polyline points="{" ".join(line_pts)}" fill="none" stroke="{col}" stroke-width="1.5"/>')
        for p5 in ps[:5]:
            tx = sx(p5)
            parts.append(f'<line x1="{tx:.1f}" y1="{y_base - 5:.1f}" x2="{tx:.1f}" y2="{y_base + 1.5:.1f}" stroke="{col}" stroke-width="1.5"/>')

        lbl = smart_club_name(t["team"], t["state"], 25)
        fw = "700" if (t["is_dop"] or idx == 0) else "500"
        tcol = "#9e1e18" if t["is_dop"] else ("#5b359a" if t["is_cyo"] else "#132238")
        parts.append(
            f'<text x="{m_l - 7}" y="{y_base - 2:.1f}" text-anchor="end" font-family="IBM Plex Sans,Segoe UI,sans-serif" '
            f'font-size="7.9" font-weight="{fw}" fill="{tcol}">{esc(lbl)}</text>'
        )

    parts.append(f'<text x="{W - m_r}" y="10" text-anchor="end" font-family="IBM Plex Sans,Segoe UI,sans-serif" font-size="7.3" fill="#6b6962">&#8592; Faster Pace  |  Ticks = Top-5 Scorers</text>')
    parts.append("</svg>")
    return "".join(parts)

# ==============================================================================
# 5. ASSEMBLE EDITORIAL 15-PAGE PUBLICATION HTML
# ==============================================================================
TOTAL_PAGES = 15
usa_svg, grad_css, max_st, n_cities, top_states = build_usa_map_svg()
dop_all = [a for a in ATHLETES if a["is_dop"]]
dop_aa_svg = build_dop_aa_chart_svg(dop_all)
dop_teams_all = [t for t in TEAMS if t["is_dop"]]
dop_scoring = [t for t in dop_teams_all if t["scores_official_team"]]
exp_cyo_titles = sum(t["cyo"]["win_prob"] / 100.0 for t in dop_scoring if t.get("cyo"))
exp_aa_tot = sum(a["aa_age_prob"] / 100.0 for a in dop_all)

# Top 10 States mini-bar sidebar next to USA Map on Page 1!
STATE_NAMES = {
    "OH": "Ohio", "KY": "Kentucky", "IN": "Indiana", "IL": "Illinois", "PA": "Pennsylvania",
    "MI": "Michigan", "KS": "Kansas", "CA": "California", "MO": "Missouri", "CO": "Colorado",
}
top_st_bars = []
for st, cnt in top_states[:10]:
    pct = 100.0 * cnt / max_st
    bar_col = "#b8251e" if st == "PA" else "#1c4980"
    top_st_bars.append(
        f'<div class="st-row">'
        f'<span class="mono b" style="width:22px;color:{"#b8251e" if st=="PA" else "#132238"}">{st}</span>'
        f'<div class="st-rail"><div class="st-fill" style="width:{pct:.1f}%;background:{bar_col}"></div></div>'
        f'<span class="mono num" style="width:26px;font-weight:600">{cnt}</span>'
        f'</div>'
    )

# Page 1 Official Schedule (EST)
OFFICIAL_SCHED = [
    ("8:15 AM", "Head Coaches Meeting", "", None),
    ("8:45 AM", "National Anthem", "", None),
    ("9:00 AM", "15–16 Girls & 17–18 Girls", "5,000m", 1),
    ("9:30 AM", "15–16 Boys & 17–18 Boys", "5,000m", 2),
    ("10:00 AM", "6–8 Girls", "2,000m", 3),
    ("10:25 AM", "6–8 Boys", "2,000m", 4),
    ("10:45 AM", "Race of the Americas (8 & Under) · Officials' Break", "1,000m", 5),
    ("11:15 AM", "9–10 Girls", "3,000m", 6),
    ("11:45 AM", "9–10 Boys", "3,000m", 7),
    ("12:15 PM", "11–12 Girls", "3,000m", 8),
    ("12:45 PM", "11–12 Boys", "3,000m", 9),
    ("1:15 PM", "13–14 Girls", "4,000m", 10),
    ("1:45 PM", "13–14 Boys", "4,000m", 11),
]
sched_rows_html = []
for tm, lbl, dist, en in OFFICIAL_SCHED:
    if en is None:
        sched_rows_html.append(f'<tr class="row-mile"><td class="mono b">{tm}</td><td colspan="3">{lbl}</td></tr>')
    else:
        ev = EVENTS[en]
        has_d = ev["dop_entries_count"] > 0
        cls = ' class="row-dop"' if has_d else ""
        badge = f'<span class="badge-dop">Pgh CYO · {ev["dop_entries_count"]}</span>' if has_d else f'<span class="muted">{ev["unique_runners"]} rnrs</span>'
        sched_rows_html.append(
            f'<tr{cls}><td class="mono b">{tm}</td><td><b>Ev {en}</b> · {lbl}</td><td class="mono num">{dist}</td><td class="num">{badge}</td></tr>'
        )

# Page 2: Squad Outlook + 13 Feeder Schools
squad_rows_html = []
for t in sorted(dop_teams_all, key=lambda x: (x["event_num"], x["team"])):
    ev = EVENTS[t["event_num"]]
    if t["scores_official_team"]:
        nat_s = f'#{t["nat"]["exp_rank"]:.1f} ({t["nat"]["exp_score"]:.0f} pts · {t["nat"]["podium_prob"]:.0f}% Pod)'
        cyo_s = f'#{t["cyo"]["exp_rank"]:.1f} ({t["cyo"]["exp_score"]:.0f} pts · <b class="{"dop-txt" if t["cyo"]["win_prob"]>=50 else ""}">{t["cyo"]["win_prob"]:.1f}% Win</b>)'
    else:
        nat_s = f'Incomplete ({t["roster_count"]}/5)'
        cyo_s = "Incomplete (<5)"
    squad_rows_html.append(
        f'<tr><td class="mono">{ev["time_est"]}</td><td class="b">{ev["short"]}</td><td class="b dop-txt">{esc(fmt_club(t["team"], t["state"]))}</td>'
        f'<td class="num mono">{t["roster_count"]}</td><td class="mono">{nat_s}</td><td class="mono">{cyo_s}</td></tr>'
    )

sch_counts = {}
for a in dop_all:
    s = short_school(a.get("home_school"))
    sch_counts[s] = sch_counts.get(s, 0) + 1
sch_badges = " ".join(f'<span class="sch-pill"><b>{esc(s)}</b> · {n}</span>' for s, n in sorted(sch_counts.items(), key=lambda x: (-x[1], x[0])))

# Page 3: All-11-Races Projected Top 3 National & CYO Team Winners
nat_pod_rows, cyo_pod_rows = [], []
for en in range(1, 12):
    ev = EVENTS[en]
    nt = sorted([t for t in TEAMS if t["event_num"] == en and t["scores_official_team"]], key=lambda t: t["nat"]["exp_rank"])
    ct = sorted([t for t in TEAMS if t["event_num"] == en and t["scores_official_team"] and t["is_cyo"]], key=lambda t: t["cyo"]["exp_rank"])

    def fmt_pod_cell(t_list, idx, lens):
        if idx >= len(t_list):
            return '<span class="muted">—</span>'
        t = t_list[idx]
        st = t[lens]
        cls = "dop-txt" if t["is_dop"] else ("cyo-txt" if t["is_cyo"] and lens == "nat" else "")
        stat = f'{st["exp_score"]:.0f}p · {st["win_prob"]:.0f}%W' if idx == 0 else f'{st["exp_score"]:.0f}p · {st["podium_prob"]:.0f}%P'
        return f'<div class="b {cls}" style="font-size:7.6pt">{esc(smart_club_name(t["team"], t["state"], 28))}</div><div class="mono muted" style="font-size:6.7pt">{stat} · {st["top5_avg_str"]}</div>'

    nat_pod_rows.append(
        f'<tr><td class="mono nw">{ev["time_est"]}</td><td class="b nw">Ev {en} · {ev["short"]}</td>'
        f'<td>{fmt_pod_cell(nt, 0, "nat")}</td><td>{fmt_pod_cell(nt, 1, "nat")}</td><td>{fmt_pod_cell(nt, 2, "nat")}</td>'
        f'<td class="num mono">{len(nt)}</td></tr>'
    )
    if ct:
        cyo_pod_rows.append(
            f'<tr class="{"row-dop" if any(x["is_dop"] for x in ct[:3]) else ""}"><td class="mono nw">{ev["time_est"]}</td><td class="b nw">Ev {en} · {ev["short"]}</td>'
            f'<td>{fmt_pod_cell(ct, 0, "cyo")}</td><td>{fmt_pod_cell(ct, 1, "cyo")}</td><td>{fmt_pod_cell(ct, 2, "cyo")}</td>'
            f'<td class="num mono">{len(ct)}</td></tr>'
        )
    else:
        cyo_pod_rows.append(
            f'<tr><td class="mono nw">{ev["time_est"]}</td><td class="b nw">Ev {en} · {ev["short"]}</td>'
            f'<td colspan="3" class="muted">No complete 5+ CYO scoring squads entered</td><td class="num mono">0</td></tr>'
        )

cyo_cup_orgs = sorted(
    [(c, sum(t["cyo"]["win_prob"] / 100.0 for t in TEAMS if t["base_org"] == c["org"] and t["scores_official_team"] and t.get("cyo"))) for c in CLUBS if c["is_cyo"]],
    key=lambda x: (-x[1], -x[0]["runners_count"]),
)
cyo_cup_pills = " ".join(
    f'<span class="sch-pill {"pill-dop-hl" if c["is_dop"] else ""}"><b>{esc(fmt_club(c["org"], c["state"]))}</b> · {cw:.2f} titles · {c["runners_count"]} rnrs · {c["exp_age_all_americans"]:.1f} AA</span>'
    for c, cw in cyo_cup_orgs[:6]
)

page3_html = f"""
<div class="page">
  <div class="pg-hdr">
    <div>
      <div class="eyebrow">ALL 11 CHAMPIONSHIP RACES · 10,000-TRIAL MONTE CARLO TEAM DISPLACEMENT</div>
      <h1>Projected Top 3 Team Winners — National Open &amp; CYO Championship</h1>
    </div>
    <div class="hdr-meta">
      <div class="mono b">Official Rule B.5 Scoring</div>
      <div class="muted">Top 5 score · 6–7 displace · #6 tiebreak</div>
    </div>
  </div>

  <div class="ed-sec">
    <div class="sec-bar navy">
      <span>Projected Top 3 National Open Team Winners (All 11 Races)</span>
      <span class="sec-sub">Pts = Expected Score · %W = Win Prob · %P = Podium Prob · Top-5 Avg</span>
    </div>
    <table>
      <thead>
        <tr>
          <th>Time</th><th>Division</th>
          <th>{medal_badge(1)} 1st Favorite</th><th>{medal_badge(2)} 2nd Contender</th><th>{medal_badge(3)} 3rd Contender</th><th class="num">Tms</th>
        </tr>
      </thead>
      <tbody>{"".join(nat_pod_rows)}</tbody>
    </table>
  </div>

  <div class="ed-sec">
    <div class="sec-bar plum">
      <span>Projected Top 3 CYO National Championship Team Winners (All 11 Races)</span>
      <span class="sec-sub">Crimson highlight = Pittsburgh CYO projected CYO podium</span>
    </div>
    <table>
      <thead>
        <tr>
          <th>Time</th><th>Division</th>
          <th>{medal_badge(1)} 1st CYO Favorite</th><th>{medal_badge(2)} 2nd CYO</th><th>{medal_badge(3)} 3rd CYO</th><th class="num">CYO</th>
        </tr>
      </thead>
      <tbody>{"".join(cyo_pod_rows)}</tbody>
    </table>
  </div>

  <div class="ed-sec">
    <div class="sec-bar subtle"><span>CYO National Cup Omnium Leaders · Top 6 Catholic Programs by Expected CYO Titles</span></div>
    <div style="margin-top:4px">{cyo_cup_pills}</div>
  </div>

  <div class="pfoot">
    <span>2026 CCCNYC &amp; CYO Nationals · Team Mile-Pace Density Ridgelines follow on Pages 4–7</span>
    <span class="mono">Page 3 of {TOTAL_PAGES}</span>
  </div>
</div>
"""

# Pages 4–7: Editorial Team Mile-Pace Density Ridgelines (Full Vertical Harmony!)
RIDGE_GROUPS = [
    (4, "Morning High School & 6–8 Divisions", [1, 2, 3]),
    (5, "Developmental 6–8 Boys, 1K Open & 9–10 Girls", [4, 5, 6]),
    (6, "9–10 Boys & 11–12 Championship Divisions", [7, 8, 9]),
    (7, "13–14 Championship Finale Divisions", [10, 11]),
]
ridge_pages_html = []
for p_num, grp_title, ev_list in RIDGE_GROUPS:
    blocks = []
    svg_h = 248 if len(ev_list) == 3 else 355
    for en in ev_list:
        ev = EVENTS[en]
        nt = sorted([t for t in TEAMS if t["event_num"] == en and t["scores_official_team"]], key=lambda t: t["nat"]["exp_rank"])
        ct = sorted([t for t in TEAMS if t["event_num"] == en and t["scores_official_team"] and t["is_cyo"]], key=lambda t: t["cyo"]["exp_rank"])
        ridge_svg = build_ridgeline_svg(en, W=465, H=svg_h)

        def pod_lines(t_list, lens):
            if not t_list:
                return '<div class="muted" style="font-size:7.3pt;padding:2px 0">No complete 5+ CYO scoring squads</div>'
            out = []
            for idx, t in enumerate(t_list[:3], start=1):
                st = t[lens]
                c_cls = "dop-txt" if t["is_dop"] else ("cyo-txt" if t["is_cyo"] and lens == "nat" else "")
                out.append(
                    f'<div class="pod-mini">'
                    f'{medal_badge(idx)} '
                    f'<div style="min-width:0;flex:1">'
                    f'<div class="b {c_cls}" style="line-height:1.15">{esc(smart_club_name(t["team"], t["state"], 25))}</div>'
                    f'<div class="mono muted" style="font-size:6.6pt">{st["exp_score"]:.0f} pts · {st["win_prob"]:.0f}%W · Avg {st["top5_avg_str"]} · 1–5: {st["spread_1_5_sec"]:.0f}s</div>'
                    f'</div>'
                    f'</div>'
                )
            return "".join(out)

        # Optional tactical pack compression note for spacious 2-race Page 7!
        tact_note = ""
        if len(ev_list) == 2 and nt:
            tight = min(nt[:6], key=lambda t: t["nat"]["spread_1_5_sec"])
            dop_ev = [t for t in ct if t["is_dop"]]
            dop_part = f' · <b>Pittsburgh CYO (PA)</b> projects CYO #{dop_ev[0]["cyo"]["exp_rank"]:.1f} ({dop_ev[0]["cyo"]["win_prob"]:.0f}% CYO Win, 1–5 spread {dop_ev[0]["nat"]["spread_1_5_sec"]:.0f}s)' if dop_ev else ""
            tact_note = (
                f'<div class="tact-strip"><b>Pack Dynamics:</b> <b>{esc(smart_club_name(nt[0]["team"], nt[0]["state"], 28))}</b> leads at {nt[0]["nat"]["exp_score"]:.0f} pts '
                f'({nt[0]["nat"]["win_prob"]:.0f}%W); tightest Top-6 pack is <b>{esc(smart_club_name(tight["team"], tight["state"], 26))}</b> ({tight["nat"]["spread_1_5_sec"]:.0f}s 1–5){dop_part}.</div>'
            )

        blocks.append(f"""
  <div class="ridge-card">
    <div class="sec-bar subtle" style="margin-bottom:4px">
      <span><b>Ev {en} · {esc(ev['name'])}</b> <span class="muted">({ev['time_est']} EST · {ev['unique_runners']} rnrs · {ev['scoring_teams_count']} tms)</span></span>
      <span class="sec-sub"><span class="sw" style="background:#b8251e"></span>Pgh CYO &nbsp;<span class="sw" style="background:#5b359a"></span>CYO &nbsp;<span class="sw" style="background:#0d7a47"></span>#1 Nat</span>
    </div>
    <div class="ridge-grid">
      <div>{ridge_svg}</div>
      <div class="ridge-side">
        <div class="pod-hdr">Overall National Top 3</div>
        {pod_lines(nt, "nat")}
        <div class="pod-hdr plum-hdr">CYO National Top 3</div>
        {pod_lines(ct, "cyo")}
      </div>
    </div>
    {tact_note}
  </div>
""")
    ridge_pages_html.append(f"""
<div class="page">
  <div class="pg-hdr">
    <div>
      <div class="eyebrow">TEAM MILE-PACE DENSITY RIDGELINES &amp; TOP-3 PODIUMS · ALL 11 RACES</div>
      <h1>{grp_title}</h1>
    </div>
    <div class="hdr-meta">
      <div class="mono b">Left-Shifted = Faster Pack</div>
      <div class="muted">Narrower wave = tighter 1–5 spread</div>
    </div>
  </div>
  <div class="ridge-stack">{"".join(blocks)}</div>
  <div class="pfoot">
    <span>2026 CCCNYC &amp; CYO Nationals · Gaussian KDE Mile-Pace Ridgelines (vertical ticks = Top-5 scorers; spread = 1–5 sec)</span>
    <span class="mono">Page {p_num} of {TOTAL_PAGES}</span>
  </div>
</div>
""")

# Pages 8–15: Dedicated S-Curve & Scouting Sheets for Pittsburgh CYO's 8 Races
DOP_EVENTS = [3, 4, 6, 7, 8, 9, 10, 11]
race_pages_html = []

for p_idx, ev_num in enumerate(DOP_EVENTS, start=8):
    ev = EVENTS[ev_num]
    ev_aths = sorted([a for a in ATHLETES if a["event_num"] == ev_num], key=lambda a: a["exp_place"])
    ev_dop = [a for a in ev_aths if a["is_dop"]]
    ev_dop_teams = sorted([t for t in TEAMS if t["event_num"] == ev_num and t["is_dop"]], key=lambda x: x["team"])
    scurve_h = 242 if len(ev_dop) >= 10 else 285
    scurve_svg = build_scurve_svg(ev_num, ev_aths, W=740, H=scurve_h)

    t_pills = []
    for t in ev_dop_teams:
        if t["scores_official_team"]:
            t_pills.append(
                f'<b>{esc(fmt_club(t["team"], t["state"]))}</b>: Nat #{t["nat"]["exp_rank"]:.1f} ({t["nat"]["podium_prob"]:.0f}% Pod) · '
                f'<span class="dop-txt b">CYO #{t["cyo"]["exp_rank"]:.1f} ({t["cyo"]["win_prob"]:.1f}% CYO Win)</span>'
            )
        else:
            t_pills.append(f'<b>{esc(fmt_club(t["team"], t["state"]))}</b>: {t["roster_count"]} runners (1 short of 5-runner team scoring)')
    team_banner = " &nbsp;|&nbsp; ".join(t_pills)

    top3_rows = []
    for i, a in enumerate(ev_aths[:3], start=1):
        top3_rows.append(
            f'<tr>'
            f'<td class="nw">{medal_badge(i)} <span class="mono muted">(#{a["exp_place"]:.1f})</span></td>'
            f'<td class="b nw">{esc(a["display_name"])}</td>'
            f'<td class="num mono">{a["age"]}</td>'
            f'<td>{esc(fmt_club(a["team"], a["club_state"]))}</td>'
            f'<td class="num mono b">{a["proj_time_str"]}</td>'
            f'<td class="num mono muted">{a["p10_time_str"]}–{a["p90_time_str"]}</td>'
            f'<td class="num mono">{a["proj_pace_mi"]}/mi</td>'
            f'<td class="num mono b">{a["win_prob"]:.1f}%</td>'
            f'</tr>'
        )

    dop_rows = []
    for a in ev_dop:
        sq = a["team"].replace("Pittsburgh CYO", "Pgh CYO")
        cyo_rk = f'#{a["cyo_exp_rank"]:.1f}' if a.get("cyo_exp_rank") else "—"
        age_rk = f'#{a["aa_age_exp_rank"]:.1f}/{a["aa_age_field_size"]}'
        aa_pct = a["aa_age_prob"]
        aa_cls = "aa-hi" if aa_pct >= 50 else ("aa-mid" if aa_pct >= 20 else "aa-lo")
        dop_rows.append(
            f'<tr>'
            f'<td class="mono nw muted">{esc(sq)}</td>'
            f'<td class="b nw">{esc(a["display_name"])}</td>'
            f'<td class="nw">{esc(short_school(a.get("home_school")))}</td>'
            f'<td class="num mono">{a["age"]}</td>'
            f'<td class="num mono b">{a["proj_time_str"]}</td>'
            f'<td class="num mono">{a["proj_pace_mi"]}/mi</td>'
            f'<td class="num mono b">#{a["exp_place"]:.1f}</td>'
            f'<td class="num mono">{cyo_rk}</td>'
            f'<td class="num mono b nw">{age_rk} <span class="muted">(Age {a["award_group"]})</span></td>'
            f'<td class="num mono"><span class="{aa_cls}">{aa_pct:.1f}%</span></td>'
            f'</tr>'
        )

    cut_notes = []
    for ag in sorted(ev["award_group_sizes"].keys(), key=lambda x: int(x)):
        grp = sorted([a for a in ev_aths if a["award_group"] == ag], key=lambda x: x["proj_time_sec"])
        if len(grp) >= 25:
            ct = grp[24]["proj_time_sec"]
            cut_notes.append(f'<b>Age {ag} #25 Cutline</b> ({len(grp)} rnrs): <span class="mono b">{fmt_time(ct)}</span> ({fmt_pace(ct, ev["dist_m"])})')
        else:
            cut_notes.append(f'<b>Age {ag}</b> ({len(grp)} rnrs): All finishers Top 25!')
    cut_html = " &nbsp;·&nbsp; ".join(cut_notes)

    race_pages_html.append(f"""
<div class="page">
  <div class="pg-hdr">
    <div>
      <div class="eyebrow">EVENT {ev_num} · {ev['time_est']} EST · {ev['dist_m']:,} METERS · AWARDS {ev['awards_time']}</div>
      <h1>{esc(ev['name'])} · S-Curve &amp; Pittsburgh CYO Scouting</h1>
    </div>
    <div class="hdr-meta">
      <div class="mono b">{ev['unique_runners']} Runners · {ev['scoring_teams_count']} Scoring Teams</div>
      <div class="muted">{ev['dop_entries_count']} Pittsburgh CYO · {ev['cyo_scoring_teams_count']} CYO Teams</div>
    </div>
  </div>
  <div class="team-strip">{team_banner}</div>

  <div class="ed-sec">
    <div class="sec-bar subtle">
      <span>Projected Finish S-Curve &amp; Traffic Density</span>
      <span class="sec-sub">P10–P90 band · Bottom bars = runners finishing per 10s window</span>
    </div>
    {scurve_svg}
  </div>

  <div class="ed-sec">
    <div class="sec-bar navy"><span>Overall Projected Top 3 Runners &amp; Clubs</span></div>
    <table>
      <thead>
        <tr>
          <th>Proj Pl</th><th>Runner</th><th class="num">Age</th><th>Club (State)</th>
          <th class="num">Proj Time</th><th class="num">P10–P90</th><th class="num">Proj Pace</th><th class="num">Win %</th>
        </tr>
      </thead>
      <tbody>{"".join(top3_rows)}</tbody>
    </table>
  </div>

  <div class="ed-sec">
    <div class="sec-bar crimson"><span>Pittsburgh CYO Runners (PA) · Projected Times, Paces, Schools &amp; Single-Year Age Places</span></div>
    <table>
      <thead>
        <tr>
          <th>Squad</th><th>Runner</th><th>Catholic School</th><th class="num">Age</th>
          <th class="num">Proj Time</th><th class="num">Proj Pace</th><th class="num">Ov Pl</th>
          <th class="num">CYO Pl</th><th class="num">Single-Year Age Pl</th><th class="num">Age AA %</th>
        </tr>
      </thead>
      <tbody>{"".join(dop_rows)}</tbody>
    </table>
    <div class="cutline-bar"><b>Single-Year Birth-Age #25 All-American Targets:</b> &nbsp;{cut_html}</div>
  </div>

  <div class="pfoot">
    <span>2026 CCCNYC &amp; CYO Nationals · Elvin R. King XC Course, Cedarville University · 10,000 Monte Carlo Trials</span>
    <span class="mono">Page {p_idx} of {TOTAL_PAGES}</span>
  </div>
</div>
""")

full_html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Pittsburgh CYO — 2026 CCCNYC &amp; CYO Nationals Race-Day Packet</title>
<style>
@page {{
  size: letter portrait;
  margin: 0.34in 0.38in;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: "IBM Plex Sans", "Segoe UI", Arial, sans-serif;
  color: #132238;
  background: #ffffff;
  font-size: 9pt;
  line-height: 1.32;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}
.page {{
  position: relative;
  width: 100%;
  height: 10.28in;
  page-break-after: always;
  display: flex;
  flex-direction: column;
  gap: 8px;
}}
.page:last-child {{ page-break-after: auto; }}
.mono {{ font-family: "IBM Plex Mono", Consolas, monospace; font-variant-numeric: tabular-nums; }}
.nw {{ white-space: nowrap; }}
.b {{ font-weight: 700; }}
.muted {{ color: #676e78; font-weight: 400; }}
.num {{ text-align: right; }}
.dop-txt {{ color: #b8251e; }}
.cyo-txt {{ color: #5b359a; }}

/* Cover Masthead (Deep Championship Navy + Gold/Crimson Accent) */
.masthead {{
  background: #132238;
  color: #ffffff;
  border-radius: 6px;
  padding: 13px 16px 12px;
  border-bottom: 3.5px solid #b8251e;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 14px;
}}
.mh-eyebrow {{
  font-family: "IBM Plex Mono", Consolas, monospace;
  font-size: 7.2pt;
  letter-spacing: 0.11em;
  text-transform: uppercase;
  color: #f5c518;
  font-weight: 700;
}}
.masthead h1 {{
  font-family: Georgia, "Times New Roman", serif;
  font-size: 16.5pt;
  font-weight: 700;
  color: #ffffff;
  margin: 3px 0 3px;
  line-height: 1.12;
  letter-spacing: -0.01em;
}}
.mh-sub {{
  font-size: 8pt;
  color: #c8d4e3;
}}
.mh-date {{
  text-align: right;
  white-space: nowrap;
  border-left: 1px solid rgba(255,255,255,0.18);
  padding-left: 12px;
}}
.mh-date .big {{
  font-family: Georgia, serif;
  font-size: 11.5pt;
  font-weight: 700;
  color: #ffffff;
}}
.mh-date .sm {{
  font-family: "IBM Plex Mono", Consolas, monospace;
  font-size: 7.2pt;
  color: #a9bbd1;
}}

/* Editorial KPI Strip (borderless hairline dividers instead of bulky boxes) */
.kpi-strip {{
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  background: #f8f6f0;
  border-top: 1px solid #dedad0;
  border-bottom: 1.5px solid #132238;
  padding: 6px 0;
}}
.kpi-cell {{
  text-align: center;
  padding: 0 5px;
  border-right: 1px solid #dedad0;
}}
.kpi-cell:last-child {{ border-right: none; }}
.kpi-cell .v {{
  font-family: "IBM Plex Mono", Consolas, monospace;
  font-size: 12.5pt;
  font-weight: 700;
  line-height: 1.1;
  color: #132238;
}}
.kpi-cell.dop .v {{ color: #b8251e; }}
.kpi-cell.cyo .v {{ color: #5b359a; }}
.kpi-cell.up .v {{ color: #0d7a47; }}
.kpi-cell .l {{
  font-size: 6.9pt;
  color: #5b616b;
  margin-top: 2px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}}

/* Standard Page Header */
.pg-hdr {{
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 10px;
  border-bottom: 2px solid #132238;
  padding-bottom: 5px;
}}
.eyebrow {{
  font-family: "IBM Plex Mono", Consolas, monospace;
  font-size: 7.2pt;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #b8251e;
  font-weight: 700;
}}
.pg-hdr h1 {{
  font-family: Georgia, "Times New Roman", serif;
  font-size: 13.2pt;
  margin: 2px 0 0;
  line-height: 1.15;
  color: #132238;
}}
.hdr-meta {{ text-align: right; font-size: 7.8pt; white-space: nowrap; }}

/* Editorial Section Headers (replacing heavy borders with crisp tinted bars) */
.ed-sec {{
  display: flex;
  flex-direction: column;
  gap: 4px;
}}
.sec-bar {{
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 4px 8px;
  border-radius: 3px;
  font-size: 8.4pt;
  font-weight: 700;
}}
.sec-bar.navy {{ background: #132238; color: #ffffff; }}
.sec-bar.navy .sec-sub {{ color: #bfd0e4; }}
.sec-bar.plum {{ background: #5b359a; color: #ffffff; }}
.sec-bar.plum .sec-sub {{ color: #dfd4f5; }}
.sec-bar.crimson {{ background: #b8251e; color: #ffffff; }}
.sec-bar.crimson .sec-sub {{ color: #fad6d4; }}
.sec-bar.subtle {{
  background: #f5f3ec;
  color: #132238;
  border-left: 3px solid #132238;
}}
.sec-sub {{ font-weight: 400; font-size: 7pt; color: #676e78; }}

.team-strip {{
  background: #fdf2f1;
  border-left: 3px solid #b8251e;
  border-top: 1px solid #f0d0cd;
  border-right: 1px solid #f0d0cd;
  border-bottom: 1px solid #f0d0cd;
  border-radius: 3px;
  padding: 4.5px 9px;
  font-size: 8pt;
  color: #2f2120;
}}

/* Map + Top States Sidebar Grid */
.map-split {{
  display: grid;
  grid-template-columns: 1fr 142px;
  gap: 10px;
  align-items: center;
}}
.st-sidebar {{
  background: #f8f6f0;
  border: 1px solid #e4e0d5;
  border-radius: 5px;
  padding: 7px 8px;
}}
.st-sb-title {{
  font-size: 7pt;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #132238;
  border-bottom: 1px solid #d8d3c6;
  padding-bottom: 3px;
  margin-bottom: 5px;
}}
.st-row {{
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 7.4pt;
  margin-bottom: 4.5px;
}}
.st-row:last-child {{ margin-bottom: 0; }}
.st-rail {{
  flex: 1;
  height: 6px;
  background: #e7e3d8;
  border-radius: 3px;
  overflow: hidden;
}}
.st-fill {{ height: 100%; border-radius: 3px; }}

.map-leg {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 7.4pt;
  color: #4a515c;
  padding-top: 4px;
  border-top: 1px solid #ece9e0;
}}
.sw {{
  display: inline-block;
  width: 7.5px;
  height: 7.5px;
  border-radius: 50%;
  margin-right: 3px;
  vertical-align: middle;
}}

/* Clean Editorial Tables */
table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 7.7pt;
}}
th {{
  text-align: left;
  font-size: 6.6pt;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #5b616b;
  padding: 3px 4.5px;
  border-bottom: 1.3px solid #132238;
  background: #f8f6f0;
}}
td {{
  padding: 2.8px 4.5px;
  border-bottom: 1px solid #ebe8df;
  vertical-align: middle;
}}
tr.row-dop td {{ background: #fdf3f2; }}
tr.row-mile td {{ background: #f3f1ea; color: #4a515c; font-weight: 600; }}

/* Circular Typographic Medal Badges */
.medal {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  font-family: "IBM Plex Mono", Consolas, monospace;
  font-size: 6.8pt;
  font-weight: 700;
  color: #ffffff;
  vertical-align: middle;
  flex-shrink: 0;
}}
.m-gold {{ background: #c98e00; }}
.m-silver {{ background: #77818d; }}
.m-bronze {{ background: #a86234; }}
.m-slate {{ background: #132238; }}

.badge-dop {{
  display: inline-block;
  background: #b8251e;
  color: #ffffff;
  font-family: "IBM Plex Mono", Consolas, monospace;
  font-weight: 700;
  font-size: 6.8pt;
  padding: 1px 6px;
  border-radius: 99px;
}}
.aa-hi {{
  background: #e3f5ec;
  color: #0b683c;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 3px;
}}
.aa-mid {{
  background: #fcebe9;
  color: #a51e18;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 3px;
}}
.aa-lo {{ color: #676e78; }}

.cutline-bar {{
  margin-top: 3px;
  padding: 5px 8px;
  background: #f2f5f9;
  border-left: 3px solid #132238;
  border-radius: 3px;
  font-size: 7.7pt;
  color: #132238;
}}
.sch-pill {{
  display: inline-block;
  background: #f5f3ec;
  border: 1px solid #ddd9cc;
  border-radius: 99px;
  padding: 2px 7.5px;
  font-size: 7.3pt;
  margin: 2px 2px 2px 0;
  color: #132238;
}}
.pill-dop-hl {{
  background: #fdf2f1;
  border-color: #b8251e;
  color: #9e1e18;
}}

/* Ridgelines Pages */
.ridge-stack {{
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  justify-content: space-between;
}}
.ridge-card {{
  border-bottom: 1px solid #e2dfd6;
  padding-bottom: 6px;
}}
.ridge-card:last-child {{ border-bottom: none; padding-bottom: 0; }}
.ridge-grid {{
  display: grid;
  grid-template-columns: 1.52fr 1fr;
  gap: 9px;
  align-items: center;
}}
.ridge-side {{
  background: #f8f6f0;
  border: 1px solid #e5e1d6;
  border-radius: 5px;
  padding: 6px 8px;
}}
.pod-hdr {{
  font-size: 6.8pt;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #132238;
  border-bottom: 1.2px solid #132238;
  padding-bottom: 2px;
  margin-bottom: 4px;
}}
.pod-hdr.plum-hdr {{
  margin-top: 7px;
  color: #5b359a;
  border-bottom-color: #5b359a;
}}
.pod-mini {{
  display: flex;
  align-items: flex-start;
  gap: 5px;
  font-size: 7.2pt;
  padding: 2.5px 0;
  border-bottom: 1px dashed #e2dfd6;
}}
.pod-mini:last-child {{ border-bottom: none; }}
.tact-strip {{
  margin-top: 5px;
  padding: 4.5px 8px;
  background: #f2f5f9;
  border-left: 3px solid #132238;
  border-radius: 3px;
  font-size: 7.5pt;
  color: #263448;
}}

.pfoot {{
  margin-top: auto;
  padding-top: 5px;
  border-top: 1px solid #d8d4c8;
  display: flex;
  justify-content: space-between;
  font-size: 7pt;
  color: #717782;
}}
</style>
</head>
<body>

<!-- PAGE 1: EDITORIAL COVER + USA MAP + TOP 10 STATES + OFFICIAL EST SCHEDULE -->
<div class="page">
  <div class="masthead">
    <div>
      <div class="mh-eyebrow">20th Annual CCCNYC &amp; CYO National Championships · Coaches' Intelligence Dossier</div>
      <h1>Pittsburgh CYO · 2026 Cedarville Race-Day Briefing</h1>
      <div class="mh-sub">Final Nov 20 Entry List · <b>2,616</b> Unique Runners · <b>91</b> Clubs · <b>10</b> CYO Programs · <b>2,226 (85.1%)</b> Empirical Seeds · 10,000 Monte Carlo Trials</div>
    </div>
    <div class="mh-date">
      <div class="big">Sat, Nov 21, 2026</div>
      <div class="sm">Elvin R. King XC Course<br>Cedarville Univ. · OH</div>
    </div>
  </div>

  <div class="kpi-strip">
    <div class="kpi-cell dop"><div class="v">63 / 63</div><div class="l">Pgh CYO Matched</div></div>
    <div class="kpi-cell dop"><div class="v">13</div><div class="l">Feeder Schools</div></div>
    <div class="kpi-cell"><div class="v">9 (+1)</div><div class="l">Scoring Squads</div></div>
    <div class="kpi-cell cyo"><div class="v">{exp_cyo_titles:.2f}</div><div class="l">Proj CYO Titles</div></div>
    <div class="kpi-cell up"><div class="v">{exp_aa_tot:.1f}</div><div class="l">Proj Age AAs</div></div>
    <div class="kpi-cell"><div class="v">20 + BM</div><div class="l">States + Intl</div></div>
  </div>

  <div class="ed-sec">
    <div class="sec-bar subtle">
      <span>National Field Footprint · Runners by State &amp; Club Home Cities</span>
      <span class="sec-sub">Darker states = more runners · {n_cities} club cities · &#9733; Cedarville, OH</span>
    </div>
    <div class="map-split">
      <div>{usa_svg}</div>
      <div class="st-sidebar">
        <div class="st-sb-title">Top 10 States</div>
        {"".join(top_st_bars)}
      </div>
    </div>
    <div class="map-leg">
      <span><b>State Runners:</b> 0 <span style="display:inline-block;width:9px;height:9px;background:#f1efe8;border:1px solid #ccc;vertical-align:middle"></span> 1 <span style="display:inline-block;width:95px;height:9px;background:linear-gradient(90deg,{grad_css});border:1px solid #b5b9c0;vertical-align:middle"></span> {max_st}</span>
      <span>
        <span class="sw" style="background:#d98200"></span>Club City &nbsp;
        <span class="sw" style="background:#5b359a"></span>CYO City &nbsp;
        <span class="sw" style="background:#b8251e"></span>Pittsburgh CYO &nbsp;
        <b style="color:#c98e00">&#9733;</b> Cedarville Venue
      </span>
    </div>
  </div>

  <div class="ed-sec">
    <div class="sec-bar navy">
      <span>Official Meet Schedule (All Times Eastern Standard Time — EST)</span>
      <span class="sec-sub">Team Podiums &amp; Ridgelines: Pages 3–7 · Pgh CYO Scouting Sheets: Pages 8–15</span>
    </div>
    <table>
      <thead><tr><th style="width:72px">Time (EST)</th><th>Event</th><th class="num" style="width:68px">Distance</th><th class="num" style="width:110px">Field / Pgh CYO</th></tr></thead>
      <tbody>{"".join(sched_rows_html)}</tbody>
    </table>
  </div>

  <div class="pfoot">
    <span>2026 CCCNYC &amp; CYO Nationals · Live Interactive Dashboard: jtv55.github.io/xc/nationals/</span>
    <span class="mono">Page 1 of {TOTAL_PAGES}</span>
  </div>
</div>

<!-- PAGE 2: PITTSBURGH CYO ALL-AMERICAN LIKELIHOOD + SQUAD OUTLOOK + FEEDER SCHOOLS -->
<div class="page">
  <div class="pg-hdr">
    <div>
      <div class="eyebrow">PITTSBURGH CYO (DIOCESE OF PITTSBURGH) · SINGLE-YEAR BIRTH-AGE MEDAL ODDS</div>
      <h1>All-American Likelihood Board (Top 25 by Birth Year) &amp; Team Outlook</h1>
    </div>
    <div class="hdr-meta">
      <div class="mono b">{exp_aa_tot:.1f} Expected Age All-Americans</div>
      <div class="muted">{sum(1 for a in dop_all if a["aa_age_prob"] >= 50)} athletes project &ge;50% Top-25</div>
    </div>
  </div>

  <div class="ed-sec">
    <div class="sec-bar subtle">
      <span>Top 26 Pittsburgh CYO Birth-Age All-American Contenders</span>
      <span class="sec-sub"><span class="sw" style="background:#0d7a47"></span>&ge;50% Strong &nbsp;<span class="sw" style="background:#b8251e"></span>20–49% Contender &nbsp;<span class="sw" style="background:#8a8880"></span>Dark Horse · 10,000 trials</span>
    </div>
    {dop_aa_svg}
  </div>

  <div class="ed-sec">
    <div class="sec-bar navy"><span>Pittsburgh CYO Team Projections · National Open vs. CYO National Championship</span></div>
    <table>
      <thead>
        <tr>
          <th>Time</th><th>Division</th><th>Squad</th><th class="num">Rnrs</th>
          <th>National Open Projection</th><th>CYO National Projection</th>
        </tr>
      </thead>
      <tbody>{"".join(squad_rows_html)}</tbody>
    </table>
  </div>

  <div class="ed-sec">
    <div class="sec-bar subtle"><span>13 Catholic Feeder Schools Comprising Pittsburgh CYO (63 / 63 Season Verified)</span></div>
    <div style="margin-top:2px">{sch_badges}</div>
  </div>

  <div class="pfoot">
    <span>2026 CCCNYC &amp; CYO Nationals · Single-Year Birth-Age All-American Awards: Top 25 per exact birth year (Ages 6..14)</span>
    <span class="mono">Page 2 of {TOTAL_PAGES}</span>
  </div>
</div>

{page3_html}

{"".join(ridge_pages_html)}

{"".join(race_pages_html)}

</body>
</html>
"""

OUT_HTML.write_text(full_html, encoding="utf-8")
print(f"Wrote editorial HTML: {OUT_HTML} ({len(full_html):,} bytes)")

edge_exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
cmd = [
    edge_exe,
    "--headless=new",
    "--disable-gpu",
    "--no-pdf-header-footer",
    f"--print-to-pdf={OUT_PDF}",
    OUT_HTML.as_uri(),
]
res = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
assert OUT_PDF.exists() and OUT_PDF.stat().st_size > 20000, f"PDF generation failed: {res.stderr}"
print(f"Generated Editorial PDF: {OUT_PDF} ({OUT_PDF.stat().st_size:,} bytes)")
