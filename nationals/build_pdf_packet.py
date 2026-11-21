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

# Extract CLUB_CITY_COORDS directly from app.js so map pins stay 100% synchronized!
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
        .replace("Archangel Gabriel", "Archangel Gabriel")
        .replace("Guardian Angel Academy", "Guardian Angel")
    )

# ==============================================================================
# 1. VECTOR USA CHOROPLETH + CLUB CITIES SVG (US Census 10m Lower-48 Albers)
# ==============================================================================
def build_usa_map_svg(W=740, H=352):
    phi1 = math.radians(29.5)
    phi2 = math.radians(45.5)
    phi0 = math.radians(38.7)
    lon0 = math.radians(-96.0)
    n = 0.5 * (math.sin(phi1) + math.sin(phi2))
    C = math.cos(phi1) ** 2 + 2.0 * n * math.sin(phi1)
    rho0 = math.sqrt(C - 2.0 * n * math.sin(phi0)) / n

    def raw_proj(lon, lat):
        th = n * (math.radians(lon) - lon0)
        rho = math.sqrt(max(1e-9, C - 2.0 * n * math.sin(math.radians(lat)))) / n
        return rho * math.sin(th), -(rho0 - rho * math.cos(th))

    # Compute bounding box across all 49 features
    xs, ys = [], []
    for f in geo["features"]:
        polys = [f["geometry"]["coordinates"]] if f["geometry"]["type"] == "Polygon" else f["geometry"]["coordinates"]
        for poly in polys:
            for pt in poly[0]:
                px, py = raw_proj(pt[0], pt[1])
                xs.append(px)
                ys.append(py)
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    pad_x, pad_y = 14, 10
    scale = min((W - 2 * pad_x) / (maxx - minx), (H - 2 * pad_y) / (maxy - miny))
    ox = (W - (maxx - minx) * scale) / 2.0 - minx * scale
    oy = (H - (maxy - miny) * scale) / 2.0 - miny * scale

    def proj(lon, lat):
        px, py = raw_proj(lon, lat)
        return px * scale + ox, py * scale + oy

    # State totals
    st_tot = {}
    for c in CLUBS:
        if c["state"] not in ("USA", "INTL"):
            st_tot[c["state"]] = st_tot.get(c["state"], 0) + c["runners_count"]
    max_st = max(st_tot.values()) if st_tot else 1

    # Smooth ColorBrewer Blues sequential interpolation (light sky -> deep navy)
    BLUES = [
        (222, 235, 247),
        (189, 215, 231),
        (158, 202, 225),
        (107, 174, 214),
        (66, 146, 198),
        (33, 113, 181),
        (8, 81, 156),
        (8, 48, 107),
    ]
    def blue_color(cnt):
        if cnt <= 0:
            return "#efede6"
        t = (cnt / max_st) ** 0.55
        idx_f = min(len(BLUES) - 1, max(0.0, t * (len(BLUES) - 1)))
        i0 = int(math.floor(idx_f))
        i1 = min(len(BLUES) - 1, i0 + 1)
        frac = idx_f - i0
        r = int(round(BLUES[i0][0] + frac * (BLUES[i1][0] - BLUES[i0][0])))
        g = int(round(BLUES[i0][1] + frac * (BLUES[i1][1] - BLUES[i0][1])))
        b = int(round(BLUES[i0][2] + frac * (BLUES[i1][2] - BLUES[i0][2])))
        return f"rgb({r},{g},{b})"

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;height:auto">']

    # 1. State polygons + centroid calculation
    label_skip = {"DE", "MD", "NJ", "DC", "RI", "CT", "MA", "VT", "NH"}
    centroids = {}
    for f in geo["features"]:
        st = f["properties"]["code"]
        cnt = st_tot.get(st, 0)
        fill = blue_color(cnt)
        polys = [f["geometry"]["coordinates"]] if f["geometry"]["type"] == "Polygon" else f["geometry"]["coordinates"]
        d_cmds = []
        best_area = -1
        best_c = None
        for poly in polys:
            for ri, ring in enumerate(poly):
                pts = [proj(p[0], p[1]) for p in ring]
                if not pts:
                    continue
                cmd = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"
                d_cmds.append(cmd)
                if ri == 0 and len(pts) >= 4:
                    # Polygon centroid for largest ring
                    a2 = 0.0
                    cx = cy = 0.0
                    for i in range(len(pts) - 1):
                        x0, y0 = pts[i]
                        x1, y1 = pts[i + 1]
                        cr = x0 * y1 - x1 * y0
                        a2 += cr
                        cx += (x0 + x1) * cr
                        cy += (y0 + y1) * cr
                    if abs(a2) > best_area and abs(a2) > 1e-3:
                        best_area = abs(a2)
                        best_c = (cx / (3.0 * a2), cy / (3.0 * a2))
        if best_c:
            centroids[st] = best_c
        parts.append(f'<path d="{"".join(d_cmds)}" fill="{fill}" stroke="#ffffff" stroke-width="0.95"/>')

    # 2. State labels on active states
    for st, cnt in st_tot.items():
        if st in label_skip or st not in centroids:
            continue
        cx, cy = centroids[st]
        # Slight manual nudge for MI Lower Peninsula / LA / FL if needed
        if st == "MI":
            cx += 6
            cy += 8
        txt_col = "#ffffff" if cnt >= max_st * 0.30 else "#1c1c1a"
        parts.append(
            f'<text x="{cx:.1f}" y="{cy + 3.5:.1f}" text-anchor="middle" font-family="IBM Plex Mono,Consolas,monospace" '
            f'font-size="9.5" font-weight="700" fill="{txt_col}" opacity="0.9">{st}</text>'
        )

    # 3. Aggregate city dots + gentle overlap separation
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
        if c["is_dop"]:
            e["has_dop"] = True
        if c["is_cyo"]:
            e["has_cyo"] = True

    max_city = max(e["runners"] for e in city_map.values())
    dots = []
    for e in sorted(city_map.values(), key=lambda x: -x["runners"]):
        px, py = proj(e["lon"], e["lat"])
        r = 2.6 + 4.4 * math.sqrt(e["runners"] / max_city)
        dots.append({**e, "x": px, "y": py, "ox": px, "oy": py, "r": r})

    for _ in range(14):
        for i in range(len(dots)):
            for j in range(i + 1, len(dots)):
                a, b = dots[i], dots[j]
                dx, dy = b["x"] - a["x"], b["y"] - a["y"]
                dist = math.hypot(dx, dy) or 0.01
                min_d = a["r"] + b["r"] + 1.0
                if dist < min_d:
                    push = (min_d - dist) * 0.38
                    ux, uy = dx / dist, dy / dist
                    a["x"] -= ux * push * 0.45
                    a["y"] -= uy * push * 0.45
                    b["x"] += ux * push * 0.55
                    b["y"] += uy * push * 0.55
            d = dots[i]
            d["x"] += (d["ox"] - d["x"]) * 0.14
            d["y"] += (d["oy"] - d["y"]) * 0.14

    for d in dots:
        col = "#c43225" if d["has_dop"] else ("#6a3ab2" if d["has_cyo"] else "#e68a00")
        parts.append(
            f'<circle cx="{d["x"]:.1f}" cy="{d["y"]:.1f}" r="{d["r"]:.1f}" '
            f'fill="{col}" fill-opacity="0.90" stroke="#ffffff" stroke-width="1.0"/>'
        )

    # 4. Cedarville Venue Star Pin (-83.806, 39.741)
    cx, cy = proj(-83.806, 39.741)
    star_pts = []
    for k in range(10):
        ang = math.radians(-90 + k * 36)
        rad = 6.8 if k % 2 == 0 else 2.9
        star_pts.append(f"{cx + rad * math.cos(ang):.1f},{cy + rad * math.sin(ang):.1f}")
    parts.append(f'<polygon points="{" ".join(star_pts)}" fill="#ffd43b" stroke="#151513" stroke-width="1.1"/>')

    # 5. Bermuda inset badge (clean bottom-right corner)
    bx, by = W - 118, H - 46
    parts.append(f'<rect x="{bx}" y="{by}" width="108" height="36" rx="6" fill="#f5f3ec" stroke="#c8c4b8" stroke-dasharray="3,2"/>')
    parts.append(f'<circle cx="{bx + 15}" cy="{by + 18}" r="3.8" fill="#e68a00" stroke="#ffffff" stroke-width="1"/>')
    parts.append(f'<text x="{bx + 26}" y="{by + 15}" font-family="IBM Plex Sans,Segoe UI,sans-serif" font-size="9.5" font-weight="700" fill="#151513">Bermuda (BM)</text>')
    parts.append(f'<text x="{bx + 26}" y="{by + 28}" font-family="IBM Plex Mono,Consolas,monospace" font-size="8.5" fill="#6b6962">2 runners · INTL</text>')

    parts.append("</svg>")
    top_st_str = ", ".join(f"<b>{st} ({cnt})</b>" for st, cnt in sorted(st_tot.items(), key=lambda x: -x[1])[:8])
    grad_css = ", ".join(blue_color(int(max_st * f)) for f in [0.02, 0.15, 0.35, 0.6, 0.85, 1.0])
    return "".join(parts), grad_css, max_st, len(city_map), top_st_str

# ==============================================================================
# 2. VECTOR ALL-AMERICAN LIKELIHOOD CHART (TOP 25 PITTSBURGH CYO RUNNERS)
# ==============================================================================
def build_dop_aa_chart_svg(dop_aths, W=740, H=435):
    rows = sorted(dop_aths, key=lambda a: (-a["aa_age_prob"], a["aa_age_exp_rank"]))[:26]
    m_l, m_r, m_t, m_b = 260, 115, 14, 24
    row_h = (H - m_t - m_b) / len(rows)
    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;height:auto">']
    # Grid lines 0, 25, 50, 75, 100
    def sx(p):
        return m_l + (p / 100.0) * (W - m_l - m_r)
    for tick in (0, 25, 50, 75, 100):
        tx = sx(tick)
        col = "#c43225" if tick == 50 else "#e2dfd6"
        dash = ' stroke-dasharray="3,2"' if tick == 50 else ""
        parts.append(f'<line x1="{tx:.1f}" y1="{m_t}" x2="{tx:.1f}" y2="{H - m_b}" stroke="{col}" stroke-width="0.9"{dash}/>')
        parts.append(f'<text x="{tx:.1f}" y="{H - 8}" text-anchor="middle" font-family="IBM Plex Mono,Consolas,monospace" font-size="8.5" fill="#6b6962">{tick}%</text>')

    for i, a in enumerate(rows):
        y0 = m_t + i * row_h + 2.2
        bh = max(7.5, row_h - 4.4)
        yc = y0 + bh / 2.0
        ev_s = EVENTS[a["event_num"]]["short"].replace(" Girls", "G").replace(" Boys", "B")
        prob = a["aa_age_prob"]
        col = "#0d7a47" if prob >= 50 else ("#c43225" if prob >= 20 else "#76746d")
        # Subtle zebra background
        if i % 2 == 0:
            parts.append(f'<rect x="0" y="{m_t + i * row_h:.1f}" width="{W}" height="{row_h:.1f}" fill="#faf9f5"/>')
        lbl = f'{a["display_name"]} (Age {a["age"]} · {ev_s})'
        sch = short_school(a.get("home_school"))
        parts.append(
            f'<text x="{m_l - 8}" y="{yc + 3:.1f}" text-anchor="end" font-family="IBM Plex Sans,Segoe UI,sans-serif" '
            f'font-size="8.7" font-weight="{"700" if prob >= 50 else "500"}" fill="#151513">{esc(lbl)} · <tspan fill="#6b6962">{esc(sch)}</tspan></text>'
        )
        bw = max(2.0, sx(prob) - sx(0))
        parts.append(f'<rect x="{sx(0):.1f}" y="{y0:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="2.5" fill="{col}" opacity="0.86"/>')
        rk_txt = f'{prob:.1f}%  (Age #{a["aa_age_exp_rank"]:.1f}/{a["aa_age_field_size"]})'
        parts.append(
            f'<text x="{sx(prob) + 5:.1f}" y="{yc + 3:.1f}" font-family="IBM Plex Mono,Consolas,monospace" '
            f'font-size="8.3" font-weight="{"700" if prob >= 50 else "500"}" fill="#151513">{rk_txt}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)

# ==============================================================================
# 3. VECTOR S-CURVE & TRAFFIC DENSITY CHART FOR EACH PITTSBURGH CYO RACE
# ==============================================================================
def build_scurve_svg(ev_num, ev_aths, W=740, H=265):
    ev = EVENTS[ev_num]
    aths = sorted(ev_aths, key=lambda a: a["exp_place"])
    n_tot = len(aths)
    m_l, m_r, m_t, m_b = 54, 24, 16, 40

    # Time range (trim extreme 98th-percentile tail outlier if needed so core curve stays readable!)
    t_vals = [a["proj_time_sec"] for a in aths]
    dop_ts = [a["proj_time_sec"] for a in aths if a["is_dop"]]
    ymin = min(a["p10_time_sec"] for a in aths) * 0.985
    p98_t = sorted(t_vals)[min(len(t_vals) - 1, int(len(t_vals) * 0.985))]
    ymax = max(p98_t * 1.03, (max(dop_ts) * 1.07 if dop_ts else p98_t * 1.03))

    plot_w = W - m_l - m_r
    plot_h = H - m_t - m_b
    dens_h = 34.0  # bottom traffic density strip inside plot area

    def sx(pl):
        return m_l + ((pl - 1) / max(1, n_tot - 1)) * plot_w

    def sy(t):
        tc = min(ymax, max(ymin, t))
        return m_t + plot_h - ((tc - ymin) / max(1e-6, ymax - ymin)) * plot_h

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;height:auto">']
    parts.append(f'<rect x="{m_l}" y="{m_t}" width="{plot_w}" height="{plot_h}" fill="#fcfbf8" stroke="#e2dfd6" stroke-width="0.8"/>')

    # Y-axis time ticks (5 neat 30s/60s intervals)
    span = ymax - ymin
    step = 60 if span > 260 else (30 if span > 110 else 15)
    t0 = math.ceil(ymin / step) * step
    tcur = t0
    while tcur <= ymax:
        yy = sy(tcur)
        parts.append(f'<line x1="{m_l}" y1="{yy:.1f}" x2="{W - m_r}" y2="{yy:.1f}" stroke="#ece9e0" stroke-width="0.7"/>')
        parts.append(f'<text x="{m_l - 6}" y="{yy + 3:.1f}" text-anchor="end" font-family="IBM Plex Mono,Consolas,monospace" font-size="8.5" fill="#6b6962">{fmt_time(tcur)[:-2]}</text>')
        tcur += step

    # X-axis place ticks
    x_step = 50 if n_tot > 260 else (25 if n_tot > 120 else 20)
    for pl in [1] + list(range(x_step, n_tot + 1, x_step)):
        xx = sx(pl)
        parts.append(f'<line x1="{xx:.1f}" y1="{m_t}" x2="{xx:.1f}" y2="{H - m_b}" stroke="#f0ede4" stroke-width="0.7"/>')
        parts.append(f'<text x="{xx:.1f}" y="{H - m_b + 13}" text-anchor="middle" font-family="IBM Plex Mono,Consolas,monospace" font-size="8.5" fill="#6b6962">#{pl}</text>')
    parts.append(f'<text x="{m_l + plot_w / 2:.1f}" y="{H - 6}" text-anchor="middle" font-family="IBM Plex Sans,Segoe UI,sans-serif" font-size="8.5" fill="#6b6962">Expected Overall Finish Place (1 to {n_tot})  ·  Shaded bars along bottom = Traffic Density (runners per 10s finishing window)</text>')

    # Traffic Density Histogram along bottom (runners per 10s finish window mapped to place bins!)
    n_bins = 28
    bin_w = plot_w / n_bins
    # Compute local passing density = runners within +/-5 sec of each bin's median finish time
    bin_dens = []
    for bi in range(n_bins):
        i0 = int(bi * n_tot / n_bins)
        i1 = max(i0 + 1, int((bi + 1) * n_tot / n_bins))
        med_t = aths[(i0 + i1) // 2]["proj_time_sec"]
        cnt_10s = sum(1 for a in aths if abs(a["proj_time_sec"] - med_t) <= 5.0)
        bin_dens.append(cnt_10s)
    max_d = max(bin_dens) or 1
    for bi, cnt_10s in enumerate(bin_dens):
        bh = (cnt_10s / max_d) * dens_h
        bx = m_l + bi * bin_w
        by = H - m_b - bh
        parts.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{max(1, bin_w - 1):.1f}" height="{bh:.1f}" fill="#1d5bbf" opacity="0.13"/>')

    # P10-P90 uncertainty band polygon
    upper = " ".join(f"{sx(a['exp_place']):.1f},{sy(a['p90_time_sec']):.1f}" for a in aths)
    lower = " ".join(f"{sx(a['exp_place']):.1f},{sy(a['p10_time_sec']):.1f}" for a in reversed(aths))
    parts.append(f'<polygon points="{upper} {lower}" fill="#1d5bbf" opacity="0.09"/>')

    # Field dots (National Open = gray, Other CYO = purple)
    for a in aths:
        if a["is_dop"]:
            continue
        xx, yy = sx(a["exp_place"]), sy(a["proj_time_sec"])
        if a["is_cyo"]:
            parts.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="2.7" fill="#6a3ab2" opacity="0.72"/>')
        else:
            parts.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="1.9" fill="#8b8980" opacity="0.48"/>')

    # Overall Top 3 Gold Stars
    for rank_i, a in enumerate(aths[:3]):
        xx, yy = sx(a["exp_place"]), sy(a["proj_time_sec"])
        spts = []
        for k in range(10):
            ang = math.radians(-90 + k * 36)
            rad = 5.4 if k % 2 == 0 else 2.3
            spts.append(f"{xx + rad * math.cos(ang):.1f},{yy + rad * math.sin(ang):.1f}")
        parts.append(f'<polygon points="{" ".join(spts)}" fill="#f0b429" stroke="#151513" stroke-width="0.8"/>')

    # Pittsburgh CYO Runners (Crimson Diamonds + clean P10-P90 whiskers + non-overlapping direct labels!)
    dop_in_ev = [a for a in aths if a["is_dop"]]
    # Pre-place labels cleanly alternating above/below with collision avoidance
    placed_boxes = []
    for idx_d, a in enumerate(dop_in_ev):
        xx, yy = sx(a["exp_place"]), sy(a["proj_time_sec"])
        y10, y90 = sy(a["p10_time_sec"]), sy(a["p90_time_sec"])
        parts.append(f'<line x1="{xx:.1f}" y1="{y10:.1f}" x2="{xx:.1f}" y2="{y90:.1f}" stroke="#c43225" stroke-width="1.2" opacity="0.65"/>')
        # Diamond marker
        r_d = 4.6
        dpts = f"{xx:.1f},{yy - r_d:.1f} {xx + r_d:.1f},{yy:.1f} {xx:.1f},{yy + r_d:.1f} {xx - r_d:.1f},{yy:.1f}"
        parts.append(f'<polygon points="{dpts}" fill="#c43225" stroke="#ffffff" stroke-width="1.0"/>')

        # Find clean non-overlapping label position
        short_nm = f'{a["first_name"][0]}. {a["last_name"]} (#{round(a["exp_place"])})'
        lbl_w = len(short_nm) * 4.7 + 6
        lbl_h = 11.5
        # Try candidate offsets (above-left, below-right, higher above, lower below)
        cand_offsets = [
            (-lbl_w / 2 - 4, -14), (6, 15), (-lbl_w / 2 - 4, -27), (6, 28),
            (-lbl_w - 6, -4), (8, -14), (-lbl_w / 2, -40), (8, 41),
            (-lbl_w - 6, 15), (10, -28), (-lbl_w / 2, -53), (10, 54),
            (-lbl_w - 10, -40), (14, -42), (-lbl_w / 2, -66), (10, 67),
            (18, -55), (-lbl_w - 12, 28),
        ]
        if idx_d % 2 == 1:
            cand_offsets = [
                (6, 15), (-lbl_w / 2 - 4, -14), (6, 28), (-lbl_w / 2 - 4, -27),
                (8, -14), (-lbl_w - 6, 15), (8, 41), (-lbl_w / 2, -40),
                (10, 54), (-lbl_w / 2, -53), (10, 67), (-lbl_w / 2, -66),
                (14, -42), (-lbl_w - 10, -40), (18, -55), (-lbl_w - 12, 28),
            ]
        best_pos = None
        for ox, oy in cand_offsets:
            lx = min(W - m_r - lbl_w - 2, max(m_l + 2, xx + ox))
            ly = min(H - m_b - 10, max(m_t + 11, yy + oy))
            box = (lx, ly - 9, lx + lbl_w, ly + 3)
            if not any(not (box[2] < b[0] or box[0] > b[2] or box[3] < b[1] or box[1] > b[3]) for b in placed_boxes):
                best_pos = (lx, ly, box)
                break
        if not best_pos:
            lx = min(W - m_r - lbl_w - 2, max(m_l + 2, xx + 6))
            ly = min(H - m_b - 10, max(m_t + 11, yy - 14 - (idx_d % 4) * 12))
            best_pos = (lx, ly, (lx, ly - 9, lx + lbl_w, ly + 3))
        lx, ly, b_rect = best_pos
        placed_boxes.append(b_rect)
        parts.append(f'<line x1="{xx:.1f}" y1="{yy:.1f}" x2="{lx + lbl_w / 2:.1f}" y2="{ly - 3:.1f}" stroke="#c43225" stroke-width="0.65" opacity="0.55"/>')
        parts.append(f'<rect x="{lx - 2:.1f}" y="{ly - 8.5:.1f}" width="{lbl_w + 2:.1f}" height="10.8" rx="2" fill="#ffffff" opacity="0.88" stroke="#c43225" stroke-width="0.45"/>')
        parts.append(f'<text x="{lx + 1:.1f}" y="{ly:.1f}" font-family="IBM Plex Sans,Segoe UI,sans-serif" font-size="7.8" font-weight="700" fill="#a82419">{esc(short_nm)}</text>')

    # Mini inline legend top-left inside plot
    parts.append(f'<rect x="{m_l + 6}" y="{m_t + 6}" width="318" height="17" rx="3" fill="#ffffff" opacity="0.92" stroke="#e2dfd6" stroke-width="0.6"/>')
    parts.append(f'<polygon points="{m_l+15},{m_t+10} {m_l+19},{m_t+14.5} {m_l+15},{m_t+19} {m_l+11},{m_t+14.5}" fill="#c43225"/>')
    parts.append(f'<text x="{m_l + 23}" y="{m_t + 17.5}" font-family="IBM Plex Sans,Segoe UI,sans-serif" font-size="8" font-weight="700" fill="#a82419">Pittsburgh CYO ({len(dop_in_ev)})</text>')
    parts.append(f'<circle cx="{m_l + 112}" cy="{m_t + 14.5}" r="2.8" fill="#6a3ab2"/>')
    parts.append(f'<text x="{m_l + 118}" y="{m_t + 17.5}" font-family="IBM Plex Sans,Segoe UI,sans-serif" font-size="8" fill="#4a4944">Other CYO</text>')
    parts.append(f'<circle cx="{m_l + 170}" cy="{m_t + 14.5}" r="2.2" fill="#8b8980"/>')
    parts.append(f'<text x="{m_l + 176}" y="{m_t + 17.5}" font-family="IBM Plex Sans,Segoe UI,sans-serif" font-size="8" fill="#4a4944">National Field</text>')
    parts.append(f'<text x="{m_l + 240}" y="{m_t + 17.5}" font-family="IBM Plex Sans,Segoe UI,sans-serif" font-size="8" font-weight="600" fill="#b87d00">&#9733; Top 3 Overall</text>')

    parts.append("</svg>")
    return "".join(parts)

# ==============================================================================
# 4. ASSEMBLE COMPLETE 10-PAGE PRINT-READY HTML PACKET
# ==============================================================================
usa_svg, grad_css, max_st, n_cities, top_st_str = build_usa_map_svg()
dop_all = [a for a in ATHLETES if a["is_dop"]]
dop_aa_svg = build_dop_aa_chart_svg(dop_all)
dop_teams_all = [t for t in TEAMS if t["is_dop"]]
dop_scoring = [t for t in dop_teams_all if t["scores_official_team"]]
exp_cyo_titles = sum(t["cyo"]["win_prob"] / 100.0 for t in dop_scoring if t.get("cyo"))
exp_nat_pods = sum(t["nat"]["podium_prob"] / 100.0 for t in dop_scoring if t.get("nat"))
exp_aa_tot = sum(a["aa_age_prob"] / 100.0 for a in dop_all)

# Official EST Schedule rows
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
        badge = f'<span class="badge-dop">Pgh CYO ({ev["dop_entries_count"]})</span>' if has_d else f'<span class="muted">{ev["unique_runners"]} rnrs</span>'
        sched_rows_html.append(
            f'<tr{cls}><td class="mono b">{tm}</td><td><b>Ev {en}:</b> {lbl}</td><td class="mono num">{dist}</td><td class="num">{badge}</td></tr>'
        )

# Page 2: Squad Outlook Table + Feeder Schools Strip
squad_rows_html = []
for t in sorted(dop_teams_all, key=lambda x: (x["event_num"], x["team"])):
    ev = EVENTS[t["event_num"]]
    if t["scores_official_team"]:
        nat_s = f'#{t["nat"]["exp_rank"]:.1f} ({t["nat"]["exp_score"]} pts · {t["nat"]["podium_prob"]}% Pod)'
        cyo_s = f'#{t["cyo"]["exp_rank"]:.1f} ({t["cyo"]["exp_score"]} pts · <b>{t["cyo"]["win_prob"]}% Win</b>)'
    else:
        nat_s = f'Incomplete ({t["roster_count"]}/5)'
        cyo_s = "Incomplete (<5)"
    squad_rows_html.append(
        f'<tr><td class="b">{ev["time_est"]}</td><td>{ev["short"]}</td><td class="b">{esc(fmt_club(t["team"], t["state"]))}</td>'
        f'<td class="num mono">{t["roster_count"]}</td><td class="mono">{nat_s}</td><td class="mono">{cyo_s}</td></tr>'
    )

sch_counts = {}
for a in dop_all:
    s = short_school(a.get("home_school"))
    sch_counts[s] = sch_counts.get(s, 0) + 1
sch_badges = " ".join(f'<span class="sch-pill"><b>{esc(s)}</b> ({n})</span>' for s, n in sorted(sch_counts.items(), key=lambda x: (-x[1], x[0])))

# Pages 3–10: Dedicated page for each of Pittsburgh CYO's 8 races
DOP_EVENTS = [3, 4, 6, 7, 8, 9, 10, 11]
race_pages_html = []

for p_idx, ev_num in enumerate(DOP_EVENTS, start=3):
    ev = EVENTS[ev_num]
    ev_aths = sorted([a for a in ATHLETES if a["event_num"] == ev_num], key=lambda a: a["exp_place"])
    ev_dop = [a for a in ev_aths if a["is_dop"]]
    ev_dop_teams = sorted([t for t in TEAMS if t["event_num"] == ev_num and t["is_dop"]], key=lambda x: x["team"])
    scurve_h = 232 if len(ev_dop) >= 10 else 268
    scurve_svg = build_scurve_svg(ev_num, ev_aths, W=740, H=scurve_h)

    # Team summary pills in race header
    t_pills = []
    for t in ev_dop_teams:
        if t["scores_official_team"]:
            t_pills.append(
                f'{esc(t["team"])}: Nat #{t["nat"]["exp_rank"]:.1f} ({t["nat"]["podium_prob"]}% Pod) · '
                f'<b>CYO #{t["cyo"]["exp_rank"]:.1f} ({t["cyo"]["win_prob"]}% CYO Win)</b>'
            )
        else:
            t_pills.append(f'{esc(t["team"])}: {t["roster_count"]} runners (1 short of 5-runner team scoring)')
    team_banner = " &nbsp;|&nbsp; ".join(t_pills)

    # Top 3 Overall table
    top3_rows = []
    for i, a in enumerate(ev_aths[:3], start=1):
        medal = ["1st", "2nd", "3rd"][i - 1]
        top3_rows.append(
            f'<tr>'
            f'<td class="num mono b">{medal} (#{a["exp_place"]:.1f})</td>'
            f'<td class="b">{esc(a["display_name"])}</td>'
            f'<td class="num mono">{a["age"]}</td>'
            f'<td>{esc(fmt_club(a["team"], a["club_state"]))}</td>'
            f'<td class="num mono b">{a["proj_time_str"]}</td>'
            f'<td class="num mono muted">{a["p10_time_str"]}–{a["p90_time_str"]}</td>'
            f'<td class="num mono">{a["proj_pace_mi"]}/mi</td>'
            f'<td class="num mono">{a["win_prob"]:.1f}%</td>'
            f'</tr>'
        )

    # Pittsburgh CYO runners table (with projected overall place, CYO place, school, single-year age place, and AA%)
    dop_rows = []
    for a in ev_dop:
        sq = a["team"].replace("Pittsburgh CYO", "Pgh CYO")
        cyo_rk = f'#{a["cyo_exp_rank"]:.1f}' if a.get("cyo_exp_rank") else "—"
        age_rk = f'#{a["aa_age_exp_rank"]:.1f}/{a["aa_age_field_size"]}'
        aa_pct = a["aa_age_prob"]
        aa_cls = "aa-hi" if aa_pct >= 50 else ("aa-mid" if aa_pct >= 20 else "aa-lo")
        dop_rows.append(
            f'<tr>'
            f'<td class="mono nw">{esc(sq)}</td>'
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

    # Compute exact #25 All-American cutline time & pace for each single-year birth age in this race
    cut_notes = []
    for ag in sorted(ev["award_group_sizes"].keys(), key=lambda x: int(x)):
        grp = sorted([a for a in ev_aths if a["award_group"] == ag], key=lambda x: x["proj_time_sec"])
        if len(grp) >= 25:
            ct = grp[24]["proj_time_sec"]
            cut_notes.append(f'<b>Age {ag} #25 Cutline ({len(grp)} rnrs):</b> {fmt_time(ct)} ({fmt_pace(ct, ev["dist_m"])})')
        else:
            cut_notes.append(f'<b>Age {ag} ({len(grp)} rnrs):</b> All finishers Top 25!')
    cut_html = " &nbsp;·&nbsp; ".join(cut_notes)

    race_pages_html.append(f"""
<div class="page">
  <div class="race-hdr">
    <div>
      <div class="eyebrow">EVENT {ev_num} · {ev['time_est']} EST · {ev['dist_m']:,} METERS · AWARDS {ev['awards_time']}</div>
      <h1>{esc(ev['name'])} — Projected Finish S-Curve &amp; Pittsburgh CYO Scouting Sheet</h1>
    </div>
    <div class="hdr-meta">
      <div class="mono b">{ev['unique_runners']} Runners · {ev['scoring_teams_count']} Scoring Teams</div>
      <div class="muted">{ev['dop_entries_count']} Pittsburgh CYO Qualifiers · {ev['cyo_scoring_teams_count']} CYO Teams</div>
    </div>
  </div>
  <div class="team-strip">{team_banner}</div>

  <div class="box">
    <div class="box-title">Projected Finish S-Curve &amp; Traffic Density <span class="muted">(P10–P90 whiskers · bottom bars = pack density per 10s window)</span></div>
    {scurve_svg}
  </div>

  <div class="box">
    <div class="box-title">Overall Projected Top 3 Runners &amp; Clubs</div>
    <table>
      <thead>
        <tr>
          <th class="num">Proj Place</th><th>Runner</th><th class="num">Age</th><th>Club (State)</th>
          <th class="num">Proj Time</th><th class="num">P10–P90</th><th class="num">Proj Pace</th><th class="num">Win %</th>
        </tr>
      </thead>
      <tbody>{"".join(top3_rows)}</tbody>
    </table>
  </div>

  <div class="box">
    <div class="box-title">Pittsburgh CYO Runners · Projected Times, Paces, Schools &amp; Single-Year Age Places</div>
    <table>
      <thead>
        <tr>
          <th>Squad</th><th>Runner</th><th>Catholic School</th><th class="num">Age</th>
          <th class="num">Proj Time</th><th class="num">Proj Pace</th><th class="num">Ov Place</th>
          <th class="num">CYO Place</th><th class="num">Single-Year Age Place</th><th class="num">Age AA %</th>
        </tr>
      </thead>
      <tbody>{"".join(dop_rows)}</tbody>
    </table>
    <div class="cutline-bar"><b>Single-Year Birth-Age #25 All-American Targets:</b> {cut_html}</div>
  </div>

  <div class="pfoot">
    <span>2026 CCCNYC &amp; CYO Nationals · Cedarville University (Elvin R. King XC Course) · 10,000 Monte Carlo Trials</span>
    <span class="mono">Page {p_idx} of 10</span>
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
  margin: 0.34in 0.36in;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: "IBM Plex Sans", "Segoe UI", Arial, sans-serif;
  color: #151513;
  background: #ffffff;
  font-size: 9.5pt;
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
.muted {{ color: #6b6962; font-weight: 400; }}
.num {{ text-align: right; }}
.eyebrow {{
  font-family: "IBM Plex Mono", Consolas, monospace;
  font-size: 7.5pt;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: #c43225;
  font-weight: 700;
}}
h1 {{
  font-size: 14pt;
  margin: 2px 0 0;
  line-height: 1.18;
  letter-spacing: -0.015em;
}}
.cover-hdr {{
  border-left: 4px solid #c43225;
  background: #faf9f5;
  border-top: 1px solid #e2dfd6;
  border-right: 1px solid #e2dfd6;
  border-bottom: 1px solid #e2dfd6;
  border-radius: 6px;
  padding: 10px 14px;
}}
.race-hdr {{
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 10px;
  border-bottom: 2px solid #c43225;
  padding-bottom: 5px;
}}
.race-hdr h1 {{ font-size: 12.2pt; }}
.hdr-meta {{ text-align: right; font-size: 8.2pt; white-space: nowrap; }}
.team-strip {{
  background: rgba(196, 50, 37, 0.08);
  border: 1px solid rgba(196, 50, 37, 0.25);
  border-radius: 5px;
  padding: 4.5px 10px;
  font-size: 8.2pt;
  color: #5c1812;
}}
.kpis {{
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 6px;
}}
.kpi {{
  background: #faf9f5;
  border: 1px solid #e2dfd6;
  border-top: 2.5px solid #1d5bbf;
  border-radius: 5px;
  padding: 6px 7px;
  text-align: center;
}}
.kpi.dop {{ border-top-color: #c43225; }}
.kpi.cyo {{ border-top-color: #6a3ab2; }}
.kpi.up {{ border-top-color: #0d7a47; }}
.kpi .v {{ font-family: "IBM Plex Mono", Consolas, monospace; font-size: 13pt; font-weight: 700; line-height: 1.1; }}
.kpi .l {{ font-size: 7.2pt; color: #57554e; margin-top: 2px; }}
.box {{
  border: 1px solid #e2dfd6;
  border-radius: 6px;
  padding: 7px 10px;
  background: #ffffff;
}}
.box-title {{
  font-size: 9pt;
  font-weight: 700;
  margin-bottom: 4px;
  color: #151513;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}}
.map-leg {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 7.6pt;
  color: #4a4944;
  margin-top: 4px;
  padding-top: 4px;
  border-top: 1px solid #ece9e0;
}}
.sw {{
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 3px;
  vertical-align: middle;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 7.7pt;
}}
th {{
  text-align: left;
  font-size: 6.7pt;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #6b6962;
  padding: 2.8px 4.5px;
  border-bottom: 1.2px solid #c8c4b8;
  background: #faf9f5;
}}
td {{
  padding: 2.5px 4.5px;
  border-bottom: 1px solid #ece9e0;
  vertical-align: middle;
}}
tr.row-dop td {{ background: rgba(196, 50, 37, 0.06); }}
tr.row-mile td {{ background: #f3f1ea; color: #4a4944; font-weight: 600; }}
.badge-dop {{
  display: inline-block;
  background: rgba(196, 50, 37, 0.13);
  color: #a82419;
  font-family: "IBM Plex Mono", Consolas, monospace;
  font-weight: 700;
  font-size: 7pt;
  padding: 1px 5px;
  border-radius: 3px;
}}
.aa-hi {{
  background: rgba(13, 122, 71, 0.13);
  color: #0d7a47;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 3px;
}}
.aa-mid {{
  background: rgba(196, 50, 37, 0.11);
  color: #a82419;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 3px;
}}
.aa-lo {{ color: #6b6962; }}
.cutline-bar {{
  margin-top: 6px;
  padding: 5px 8px;
  background: #faf9f5;
  border-left: 3px solid #1d5bbf;
  border-radius: 3px;
  font-size: 7.8pt;
  color: #2f2e2a;
}}
.sch-pill {{
  display: inline-block;
  background: #f3f1ea;
  border: 1px solid #dedad0;
  border-radius: 99px;
  padding: 2px 7px;
  font-size: 7.4pt;
  margin: 2px 2px 2px 0;
}}
.pfoot {{
  margin-top: auto;
  padding-top: 5px;
  border-top: 1px solid #e2dfd6;
  display: flex;
  justify-content: space-between;
  font-size: 7.2pt;
  color: #76746d;
}}
</style>
</head>
<body>

<!-- PAGE 1: COVER + USA MAP + OFFICIAL EST SCHEDULE -->
<div class="page">
  <div class="cover-hdr">
    <div class="eyebrow">20th Annual Cross Country Coaches National Youth Championships &amp; CYO Nationals · Race-Day Briefing Packet</div>
    <h1>Pittsburgh CYO (Diocese of Pittsburgh) · 2026 Cedarville Nationals Intelligence</h1>
    <div style="font-size:8.4pt;color:#4a4944;margin-top:3px">
      <b>Saturday, November 21, 2026</b> · Elvin R. King Cross Country Course, Cedarville University, OH · Final Nov 20 Entry List (<b>2,616</b> Unique Runners · <b>91</b> Clubs · <b>10</b> CYO Programs · <b>2,226 / 85.1%</b> Direct Empirical Seeds · 10,000 Monte Carlo Trials/Race)
    </div>
  </div>

  <div class="kpis">
    <div class="kpi dop"><div class="v">63 / 63</div><div class="l">Pittsburgh CYO Matched</div></div>
    <div class="kpi dop"><div class="v">13</div><div class="l">Catholic Feeder Schools</div></div>
    <div class="kpi"><div class="v">9</div><div class="l">Scoring Squads (+1 Inc.)</div></div>
    <div class="kpi cyo"><div class="v">{exp_cyo_titles:.2f}</div><div class="l">Proj. CYO Team Titles</div></div>
    <div class="kpi up"><div class="v">{exp_aa_tot:.1f}</div><div class="l">Proj. Age All-Americans</div></div>
    <div class="kpi"><div class="v">20 + BM</div><div class="l">States + Bermuda</div></div>
  </div>

  <div class="box">
    <div class="box-title">
      <span>National Field Footprint · Runners by State &amp; Club Home Cities</span>
      <span class="muted" style="font-weight:400;font-size:7.6pt">Darker states = more runners · Dots = {n_cities} club cities · &#9733; Cedarville, OH</span>
    </div>
    {usa_svg}
    <div class="map-leg">
      <span><b>State Runners:</b> 0 <span style="display:inline-block;width:9px;height:9px;background:#efede6;border:1px solid #ccc;vertical-align:middle"></span> 1 <span style="display:inline-block;width:95px;height:9px;background:linear-gradient(90deg,{grad_css});border:1px solid #bbb;vertical-align:middle"></span> {max_st}</span>
      <span>
        <span class="sw" style="background:#e68a00"></span>Club City &nbsp;
        <span class="sw" style="background:#6a3ab2"></span>CYO City &nbsp;
        <span class="sw" style="background:#c43225"></span>Pittsburgh CYO &nbsp;
        <b style="color:#d49b00">&#9733;</b> Cedarville Venue
      </span>
    </div>
    <div style="font-size:7.5pt;color:#4a4944;margin-top:3px"><b>Top States:</b> {top_st_str}</div>
  </div>

  <div class="box">
    <div class="box-title">
      <span>Official Meet Schedule (All Times Eastern Standard Time — EST)</span>
      <span class="muted" style="font-weight:400;font-size:7.6pt">Shaded rows = Pittsburgh CYO races (Pages 3–10)</span>
    </div>
    <table>
      <thead><tr><th style="width:72px">Time (EST)</th><th>Event</th><th class="num" style="width:70px">Distance</th><th class="num" style="width:115px">Field / Pgh CYO</th></tr></thead>
      <tbody>{"".join(sched_rows_html)}</tbody>
    </table>
  </div>

  <div class="pfoot">
    <span>2026 CCCNYC &amp; CYO Nationals · Pittsburgh CYO Coaches' Briefing Packet · Live Dashboard: jtv55.github.io/xc/nationals/</span>
    <span class="mono">Page 1 of 10</span>
  </div>
</div>

<!-- PAGE 2: PITTSBURGH CYO ALL-AMERICAN LIKELIHOOD + SQUAD OUTLOOK + FEEDER SCHOOLS -->
<div class="page">
  <div class="race-hdr">
    <div>
      <div class="eyebrow">PITTSBURGH CYO (DIOCESE OF PITTSBURGH) · SINGLE-YEAR BIRTH-AGE MEDAL PROBABILITIES</div>
      <h1>All-American Likelihood Board (Top 25 by Birth Year) &amp; Team Outlook</h1>
    </div>
    <div class="hdr-meta">
      <div class="mono b">{exp_aa_tot:.1f} Expected Age All-Americans</div>
      <div class="muted">{sum(1 for a in dop_all if a["aa_age_prob"] >= 50)} athletes project &ge;50% Top-25</div>
    </div>
  </div>

  <div class="box">
    <div class="box-title">
      <span>Top 26 Pittsburgh CYO Single-Year Birth-Age All-American Contenders (10,000 Monte Carlo Trials)</span>
      <span class="muted" style="font-weight:400;font-size:7.5pt">Green &ge;50% · Red 20–49% · Dashed line = 50%</span>
    </div>
    {dop_aa_svg}
  </div>

  <div class="box">
    <div class="box-title"><span>Pittsburgh CYO Team Projections · National Open vs. CYO National Championship</span></div>
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

  <div class="box">
    <div class="box-title"><span>13 Catholic Feeder Schools Comprising Pittsburgh CYO (63 / 63 Verified)</span></div>
    <div>{sch_badges}</div>
  </div>

  <div class="pfoot">
    <span>2026 CCCNYC &amp; CYO Nationals · Single-Year Birth-Age All-American Awards: Top 25 per exact birth year (Ages 6..14)</span>
    <span class="mono">Page 2 of 10</span>
  </div>
</div>

{"".join(race_pages_html)}

</body>
</html>
"""

OUT_HTML.write_text(full_html, encoding="utf-8")
print(f"Wrote print-ready HTML: {OUT_HTML} ({len(full_html):,} bytes)")

# Render crisp 100% vector PDF using headless Microsoft Edge
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
print(f"Generated PDF: {OUT_PDF} ({OUT_PDF.stat().st_size:,} bytes)")
