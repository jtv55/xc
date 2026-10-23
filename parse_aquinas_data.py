import json
import os
import re
import csv

with open("aquinas_matches.json", "r", encoding="utf-8") as f:
    matches = json.load(f)["matches"]

MEET_META = {
    "RES082526": {
        "meet_id": "2026-08-25-seelos-1",
        "meet_name": "Seelos Pine Park XC Opener",
        "short_name": "Seelos #1",
        "short_label": "Seelos #1 (Aug 25)",
        "date": "2026-08-25",
        "location": "Pine Community Park, Wexford, PA",
        "program": "Youth / Diocesan (K-8)",
        "host": "Blessed Francis Seelos Academy",
        "is_1m": False
    },
    "RES082926": {
        "meet_id": "2026-08-29-bta",
        "meet_name": "Blessed Trinity (BTA) XC Invitational",
        "short_name": "BTA Invite",
        "short_label": "BTA Invite (Aug 29)",
        "date": "2026-08-29",
        "location": "Hartwood Acres, Glenshaw, PA",
        "program": "Youth / Diocesan (K-8)",
        "host": "Blessed Trinity Academy",
        "is_1m": False
    },
    "RES090426": {
        "meet_id": "2026-09-04-st-kilian",
        "meet_name": "St. Kilian XC Invitational",
        "short_name": "St. Kilian",
        "short_label": "St. Kilian (Sep 4)",
        "date": "2026-09-04",
        "location": "Mars, PA",
        "program": "Youth / Diocesan (K-8)",
        "host": "St. Kilian Parish School",
        "is_1m": False
    },
    "RES090926": {
        "meet_id": "2026-09-10-harvest-home",
        "meet_name": "St. Al Twilight Harvest Home 1M",
        "short_name": "Harvest Home 1M",
        "short_label": "Harvest Home 1M (Sep 10)",
        "date": "2026-09-10",
        "location": "Allison Park, PA",
        "program": "Youth / Diocesan (K-8)",
        "host": "St. Aloysius / Harvest Home",
        "is_1m": True
    },
    "EXTRA_RWB": {
        "meet_id": "2026-09-12-rwb",
        "meet_name": "24th Annual Red, White & Blue Classic (1A)",
        "short_name": "RWB Classic",
        "short_label": "RWB Classic (Sep 12)",
        "date": "2026-09-12",
        "location": "White Oak Park, White Oak, PA",
        "program": "High School (9-12)",
        "host": "Baldwin High School",
        "is_1m": False
    },
    "EXTRA_OC": {
        "meet_id": "2026-09-12-oakland-catholic",
        "meet_name": "Oakland Catholic XC Invitational",
        "short_name": "Oakland Catholic",
        "short_label": "Oakland Catholic (Sep 12)",
        "date": "2026-09-12",
        "location": "Youthtowne, Clinton, PA",
        "program": "Youth / Diocesan (K-8)",
        "host": "Oakland Catholic High School",
        "is_1m": False
    },
    "RES091826": {
        "meet_id": "2026-09-18-youthtowne",
        "meet_name": "Youthtowne Clash XC Invitational",
        "short_name": "Youthtowne Clash",
        "short_label": "Youthtowne Clash (Sep 18)",
        "date": "2026-09-18",
        "location": "Youthtowne, Clinton, PA",
        "program": "Both (HS & Youth)",
        "host": "Youthtowne",
        "is_1m": False
    },
    "RES092426": {
        "meet_id": "2026-09-24-aquinas",
        "meet_name": "Aquinas & Holy Cross Home XC Meet",
        "short_name": "Aquinas Home",
        "short_label": "Aquinas Home Meet (Sep 24)",
        "date": "2026-09-24",
        "location": "Allison Park, PA",
        "program": "Youth / Diocesan (K-8)",
        "host": "Aquinas Academy & Holy Cross",
        "is_1m": False
    },
    "EXTRA_PIAA": {
        "meet_id": "2026-09-26-piaa-foundation",
        "meet_name": "20th PIAA Foundation XC Invitational (1A)",
        "short_name": "PIAA Foundation",
        "short_label": "PIAA Foundation (Sep 26)",
        "date": "2026-09-26",
        "location": "Parkview XC Course, Hershey, PA",
        "program": "High School (9-12)",
        "host": "PIAA Foundation",
        "is_1m": False
    },
    "RES092926": {
        "meet_id": "2026-09-29-avonworth",
        "meet_name": "Avonworth WPIAL Tri-Meet",
        "short_name": "Avonworth Tri",
        "short_label": "Avonworth Tri-Meet (Sep 29)",
        "date": "2026-09-29",
        "location": "Sewickley, PA",
        "program": "High School (9-12)",
        "host": "Avonworth High School",
        "is_1m": False
    },
    "RES100226": {
        "meet_id": "2026-10-02-north-area",
        "meet_name": "North Area Diocesan XC Championships",
        "short_name": "North Area Champs",
        "short_label": "North Area Champs (Oct 2)",
        "date": "2026-10-02",
        "location": "North Park, PA",
        "program": "Youth / Diocesan (K-8)",
        "host": "North Area Diocesan League",
        "is_1m": False
    },
    "RES100626": {
        "meet_id": "2026-10-06-seelos-2",
        "meet_name": "Bl. Francis Seelos 'Second Chance' XC Meet",
        "short_name": "Seelos #2",
        "short_label": "Seelos #2 (Oct 6)",
        "date": "2026-10-06",
        "location": "Pine Community Park, Wexford, PA",
        "program": "Youth / Diocesan (K-8)",
        "host": "Blessed Francis Seelos Academy",
        "is_1m": False
    },
    "EXTRA_SEC4": {
        "meet_id": "2026-10-06-wpial-sec4",
        "meet_name": "WPIAL A/AA Section 4 XC Championships",
        "short_name": "WPIAL Sec 4",
        "short_label": "WPIAL Sec 4 (Oct 6)",
        "date": "2026-10-06",
        "location": "Chatham Univ. Eden Hall, Gibsonia, PA",
        "program": "High School (9-12)",
        "host": "Shady Side Academy / WPIAL",
        "is_1m": False
    },
    "EXTRA_PUMPKINS": {
        "meet_id": "2026-10-10-pumpkins",
        "meet_name": "Run for the Pumpkins XC Invitational",
        "short_name": "Pumpkins XC",
        "short_label": "Pumpkins XC (Oct 10)",
        "date": "2026-10-10",
        "location": "Youthtowne, Clinton, PA",
        "program": "Youth / Diocesan (K-8)",
        "host": "Archangel Gabriel School",
        "is_1m": False
    },
    "EXTRA_DIOCESAN": {
        "meet_id": "2026-10-17-diocesan-champ",
        "meet_name": "Pittsburgh Diocesan XC Championships",
        "short_name": "Diocesan Champ",
        "short_label": "Diocesan Champ (Oct 17)",
        "date": "2026-10-17",
        "location": "Youthtowne, Clinton, PA",
        "program": "Youth / Diocesan (K-8)",
        "host": "St. Louise de Marillac / Diocese of Pittsburgh",
        "is_1m": False
    },
    "RES102226": {
        "meet_id": "2026-10-22-tstca",
        "meet_name": "TSTCA Championship Tune-Up Invite (Class A)",
        "short_name": "TSTCA Class A",
        "short_label": "TSTCA Invite (Oct 22)",
        "date": "2026-10-22",
        "location": "White Oak Park, White Oak, PA",
        "program": "High School (9-12)",
        "host": "Tri-State Track Coaches Association",
        "is_1m": False
    }
}

NICKNAME_MAP = {
    "Katalina Barnett": "Kat Barnett",
    "Mary Clare Austin": "Mary Austin",
    "William Campbell": "Will Campbell",
    "Nicholas Crawford": "Nick Crawford",
    "Zachary Guillen": "Zach Guillen",
    "Samuel Martello": "Sam Martello",
    "Emilia Mullican": "Emi Mullican",
    "Leonidas Predis": "Leo Predis",
    "Rosalie Sheehan": "Rosie Sheehan",
    "Adeline Vaskov": "Addie Vaskov",
    "Lander Catherine": "Catherine Lander",
    "John Nolan IV": "Johnny Nolan",
    "John Nolan Iv": "Johnny Nolan",
    "Theodore Burchill": "Teddy Burchill",
    "Alina Gonanao": "Alina Gonano"
}

TEAM_NAME_MAP = {
    "AQUINAS": "Aquinas Academy",
    "AQUINAS ACADEMY": "Aquinas Academy",
    "AQUINAS ACADEMY PA": "Aquinas Academy",
    "BL. FRANCIS SEELOS": "Bl. Francis Seelos",
    "BLESSED FRANCIS SEELOS ACADEMY": "Bl. Francis Seelos",
    "KENNETH (KJ) ALSCHULER SEELOS": "Bl. Francis Seelos",
    "SEELOS": "Bl. Francis Seelos",
    "BLESSED TRINITY": "Blessed Trinity (BTA)",
    "BLESSED TRINITY ACADEMY": "Blessed Trinity (BTA)",
    "BTA": "Blessed Trinity (BTA)",
    "ST. KILIAN": "St. Kilian",
    "ST KILIAN": "St. Kilian",
    "SAINT KILIAN": "St. Kilian",
    "ST. KILIAN PARISH SCHOOL": "St. Kilian",
    "HOLY CROSS": "Holy Cross",
    "HOLY CROSS ACADEMY": "Holy Cross",
    "HOLY SEPULCHER": "Holy Sepulcher",
    "HOLY SEPULCHER CATHOLIC SCHOOL (": "Holy Sepulcher",
    "HOLY FAMILY": "Holy Family",
    "HOLY FAMILY MIDDLE SCHOOL": "Holy Family",
    "BUTLER CATHOLIC": "Butler Catholic",
    "BCS": "Butler Catholic",
    "ARCHANGEL GABRIEL": "Archangel Gabriel (AGS)",
    "ARCHANGEL GABRIEL SCHOOL": "Archangel Gabriel (AGS)",
    "AGS": "Archangel Gabriel (AGS)",
    "OUR LADY OF FATIMA": "Our Lady of Fatima",
    "OLOF": "Our Lady of Fatima",
    "FATIMA": "Our Lady of Fatima",
    "ST. LOUISE DE MARILLAC": "St. Louise de Marillac",
    "ST. LOUISE DE MARILLAC SCHOOL": "St. Louise de Marillac",
    "ST. LOUISE": "St. Louise de Marillac",
    "GUARDIAN ANGEL": "Guardian Angel",
    "GUARDIAN ANGEL ACADEMY": "Guardian Angel",
    "GAA": "Guardian Angel",
    "AVE MARIA": "Ave Maria",
    "AVE MARIA ACADEMY": "Ave Maria",
    "DIVINE MERCY": "Divine Mercy",
    "DIVINE MERCY ACADEMY": "Divine Mercy",
    "NORTHSIDE CATHOLIC": "Northside Catholic",
    "SOUTH HILLS CATHOLIC ACADEMY": "South Hills Catholic",
    "SACRED HEART ELEMENTARY SCHOOL": "Sacred Heart",
    "CDTCA": "CDTCA",
    "ST. JAMES": "St. James",
    "ST. JAMES CATHOLIC": "St. James",
    "ST. BEDE": "St. Bede",
    "ST. GREGORY": "St. Gregory",
    "ST GREGORY": "St. Gregory",
    "ST. GREGORY CATHOLIC SCHOOL": "St. Gregory",
    "ST. BENEDICT": "St. Benedict",
    "ST. THERESE OF LISIEUX": "St. Therese of Lisieux",
    "THE SAINT CONSTANTINE SCHOOL - E": "St. Constantine",
    "THE SAINT CONSTANTINE SCHOOL - M": "St. Constantine",
    "ST CONSTANTINE": "St. Constantine",
    "ST. CONSTANTINE": "St. Constantine",
    "ROBINSON TOWNSHIP CHRISTIAN SCHO": "Robinson Twp. Christian",
    "JOHN F. KENNEDY CATHOLIC SCHOOL": "JFK Catholic",
    "JFK": "JFK Catholic",
    "SSPP": "SS. Peter & Paul",
    "STS. PETER & PAUL": "SS. Peter & Paul",
    "STS. PETER AND PAUL CATHOLIC SCH": "SS. Peter & Paul",
    "MOTHER OF MERCY": "Mother of Mercy",
    "HILLEL": "Hillel Academy",
    "HILLEL ACADEMY": "Hillel Academy",
    "NEIGHBORHOOD ACADEM": "Neighborhood Academy",
    "NEIGHBORHOOD ACADEMY": "Neighborhood Academy",
    "AVONWORTH": "Avonworth",
    "SOUTH SIDE": "South Side",
    "NESHANNOCK": "Neshannock",
    "RIVERSIDE": "Riverside",
    "SHENANGO": "Shenango",
    "EDEN CHRISTIAN": "Eden Christian",
    "FRAZIER": "Frazier",
    "WASHINGTON": "Washington",
    "CARMICHAELS": "Carmichaels",
    "CARMICHAELS AREA": "Carmichaels",
    "TRINITY CHRISTIAN": "Trinity Christian",
    "NEW BRIGHTON": "New Brighton",
    "ELLIS": "Ellis School",
    "THE ELLIS SCHOOL": "Ellis School",
    "NORTHGATE": "Northgate",
    "SERRA CATHOLIC": "Serra Catholic",
    "CARLYNTON": "Carlynton",
    "MOHAWK": "Mohawk",
    "REDEEMER LUTHERAN": "Redeemer Lutheran",
    "SEWICKLEY ACADEMY": "Sewickley Academy",
    "SHADY SIDE ACADEMY": "Shady Side Academy",
    "STEEL VALLEY": "Steel Valley",
    "BROWNSVILLE": "Brownsville",
    "BROWNSVILLE AREA": "Brownsville",
    "WINCHESTER THURSTON": "Winchester Thurston",
    "OUR LADY OF SACRED HEART": "OLSH",
    "OLSH": "OLSH",
    "BURGETTSTOWN": "Burgettstown",
    "FORT CHERRY": "Fort Cherry",
    "CHARTIERS HOUSTON": "Chartiers-Houston",
    "HOPEDALE CHRISTIAN": "Hopedale Christian",
    "BEAVER COUNTY CHRISTIAN": "Beaver Co. Christian",
    "BEAVER COUNTY CHRISTIAN HS": "Beaver Co. Christian",
    "FREEDOM AREA": "Freedom Area",
    "FREEPORT AREA": "Freeport Area"
}

def normalize_team(t_raw):
    if not t_raw:
        return "Unattached"
    t = " ".join(str(t_raw).split()).strip()
    # Strip trailing 2-digit PIAA district code (e.g. "Winchester Thurston 07")
    t = re.sub(r'\s+\d{2}$', '', t)
    u = t.upper()
    if u in TEAM_NAME_MAP:
        return TEAM_NAME_MAP[u]
    return " ".join(w.capitalize() if len(w) > 3 else w.upper() for w in t.split())

def normalize_name(name):
    parts = " ".join(str(name).split()).split(" ")
    out = []
    for p in parts:
        if p.upper() in ("II", "III", "IV", "JR", "JR.", "SR", "SR."):
            out.append(p.upper().rstrip("."))
        elif p.startswith("Mc") and len(p) > 2:
            out.append("Mc" + p[2:].capitalize())
        elif p.upper().startswith("MC") and len(p) > 2:
            out.append("Mc" + p[2:].capitalize())
        elif p.upper().startswith("O'") and len(p) > 2:
            out.append("O'" + p[2:].capitalize())
        elif "-" in p:
            out.append("-".join(x.capitalize() for x in p.split("-")))
        else:
            out.append(p.capitalize())
    res = " ".join(out)
    return NICKNAME_MAP.get(res, res)

def parse_time_to_seconds(t_str):
    if not t_str:
        return None
    t_str = str(t_str).strip()
    parts = t_str.split(":")
    try:
        if len(parts) == 2:
            return round(int(parts[0]) * 60 + float(parts[1]), 2)
        elif len(parts) == 3:
            return round(int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2]), 2)
    except Exception:
        return None
    return None

def fmt_seconds(sec):
    if sec is None:
        return None
    mins = int(sec // 60)
    rem = sec - mins * 60
    return f"{mins}:{rem:05.2f}"

def parse_pace_to_seconds(p_str):
    if not p_str:
        return None
    m = re.match(r'(\d+):(\d+)', str(p_str).strip())
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    return None

def fmt_pace_from_sec(p_sec):
    if not p_sec:
        return None
    p_int = int(round(p_sec))
    return f"{p_int // 60}:{p_int % 60:02d}/M"

def classify_division(title, filename, program):
    t = (title + " " + filename).lower()
    if "5k" in t:
        return "Community 5K", "Community"
    if "1 mile" in t or "1m" in t:
        return "Community 1 Mile", "Youth (K-8)"
    if program == "High School (9-12)" or ("youthtowne" in t and "varsity" in t):
        return "HS Varsity (9-12)", "High School"
    if "jr high" in t or "jr hi" in t or ("varsity" in t and program != "High School (9-12)"):
        return "MS Varsity (7-8)", "Youth (K-8)"
    if "5th and 6th" in t or "jv" in t:
        return "Elementary JV (5-6)", "Youth (K-8)"
    if "3 and 4" in t or "3rd and 4th" in t or "dev" in t:
        return "Developmental (K-4)", "Youth (K-8)"
    return "Other", program

def infer_division_from_age(age):
    if age <= 10:
        return "Developmental (K-4)", max(0, age - 5)
    elif age <= 12:
        return "Elementary JV (5-6)", age - 5
    elif age <= 14:
        return "MS Varsity (7-8)", min(8, age - 5)
    else:
        return "HS Varsity (9-12)", min(12, age - 5)

row_xc_re = re.compile(
    r'^\s*(\d+)\s+([A-Za-z0-9\.\'\-\s]+?)\s{2,}([A-Za-z0-9\.\'\-\s&\(\)/]+?)\s+(\d+)\s+(\d+)\s+([MF])\s+(\d+:\d+\.\d+)\s+(\d+:\d+/[A-Za-z]+)',
    re.MULTILINE
)
row_comm_re = re.compile(
    r'^\s*(\d+)\s+([A-Za-z0-9\.\'\-\s]+?)\s{2,}([A-Za-z0-9\.\'\-\s&\(\)/]+?)\s+(\d+)\s+(\d+)\s+([MF])\s+([A-Za-z0-9\-\*\s]+?)\s+(\d+:\d+(?::\d+)?\.\d+)\s+(\d+:\d+/[A-Za-z]+)',
    re.MULTILINE
)

detail_team_header_re = re.compile(
    r'<b>([A-Za-z0-9\.\'\-\s&\(\)/]+?)\s+Finish Position -\s+([0-9]+|Inc\.)</b>.*?'
    r'<b>\s*Team Score \(places\):\s*([0-9]+|Inc\.)\s+Team Score \(times\):\s*([0-9:\.]*)\s*(?:Average Time:\s*([0-9:\.]*))?</b>',
    re.DOTALL | re.IGNORECASE
)

summary_team_row_re = re.compile(
    r'<b>\s*(\d+|Inc\.)\s+([A-Za-z0-9\.\'\-\s&\(\)/]+?)\s+(\d+|\d+\s+finishers)\s+(?:(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)(?:\s+(\d+))?(?:\s+(\d+))?)?\s*</b>\s*(?:Top\s+5\s+Times:\s*([0-9:\.]*))?',
    re.IGNORECASE
)

# Pass 1: Determine every Aquinas runner's default school XC division and grade
runner_default_div = {}
runner_default_grade = {}

for m in matches:
    fname = m["file"]
    if "OA" not in fname or "RES090926" in fname:
        continue
    m_code = re.search(r'(RES\d{6})', m["href"]).group(1)
    meta = MEET_META[m_code]
    div_name, level = classify_division(m["title"], fname, meta["program"])
    with open(os.path.join("data/raw", fname), "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    for match in row_xc_re.finditer(content):
        place, name, team, bib, grade_age, gend, time_str, pace = match.groups()
        if "aquinas" in team.lower():
            cname = normalize_name(name)
            runner_default_div[(cname, gend)] = div_name
            runner_default_grade[(cname, gend)] = int(grade_age)

# Also seed default division/grade from Diocesan Championship (193936) and PIAA Foundation
runner_default_div[("Max Predis", "M")] = "HS Varsity (9-12)"
runner_default_grade[("Max Predis", "M")] = 10
runner_default_div[("George McEvoy", "M")] = "Elementary JV (5-6)"
runner_default_grade[("George McEvoy", "M")] = 6

def compute_school_scoring_from_oa(r_list):
    """Given the overall finisher list for a race, compute official XC team scoring
    and return each school's ranking, total points, top-5 avg, and runner composition."""
    by_school = {}
    for r in r_list:
        if r["team"] == "Unattached":
            continue
        by_school.setdefault(r["team"], []).append(r)
    full_teams = {t for t, members in by_school.items() if len(members) >= 5}
    
    # Assign team scoring places (only runners on teams with >= 5 finishers, top 7 per team displace)
    team_counts = {}
    scoring_place = 0
    runner_scoring_map = {}
    for r in r_list:
        t = r["team"]
        if t == "Unattached":
            continue
        team_counts[t] = team_counts.get(t, 0) + 1
        t_idx = team_counts[t]
        if t in full_teams and t_idx <= 7:
            scoring_place += 1
            runner_scoring_map[(r["place"], r["name"])] = scoring_place
        else:
            runner_scoring_map[(r["place"], r["name"])] = None

    school_summaries = []
    for t, members in by_school.items():
        members_sorted = sorted(members, key=lambda x: x["place"])
        comp = []
        for idx, m in enumerate(members_sorted[:7], 1):
            sp = runner_scoring_map.get((m["place"], m["name"]))
            comp.append({
                "team_rank": idx,
                "name": m["name"],
                "overall_place": m["place"],
                "scoring_points": sp if idx <= 5 else None,
                "displacer_points": sp if idx in (6, 7) else None,
                "time": m["time"],
                "time_seconds": m["time_seconds"],
                "pace": m["pace"],
                "grade": m["grade_or_age"]
            })
        if t in full_teams:
            pts = sum(c["scoring_points"] for c in comp[:5] if c["scoring_points"] is not None)
            top5_sec = sum(c["time_seconds"] for c in comp[:5] if c["time_seconds"])
            avg_sec = round(top5_sec / 5.0, 2)
            sixth_pts = comp[5]["displacer_points"] if len(comp) >= 6 else 9999
            school_summaries.append({
                "team": t,
                "is_aquinas": "aquinas" in t.lower(),
                "scored": True,
                "finishers_count": len(members_sorted),
                "points": pts,
                "sixth_runner_points": sixth_pts,
                "total_time": fmt_seconds(top5_sec),
                "avg_time": fmt_seconds(avg_sec),
                "avg_seconds": avg_sec,
                "composition": comp
            })
        else:
            school_summaries.append({
                "team": t,
                "is_aquinas": "aquinas" in t.lower(),
                "scored": False,
                "finishers_count": len(members_sorted),
                "points": None,
                "sixth_runner_points": 9999,
                "total_time": None,
                "avg_time": None,
                "avg_seconds": None,
                "composition": comp
            })

    scored_list = [s for s in school_summaries if s["scored"]]
    scored_list.sort(key=lambda s: (s["points"], s["sixth_runner_points"], s["avg_seconds"] or 99999))
    for pos, s in enumerate(scored_list, 1):
        s["position"] = pos
    unscored_list = [s for s in school_summaries if not s["scored"]]
    unscored_list.sort(key=lambda s: (-s["finishers_count"], s["team"]))
    for s in unscored_list:
        s["position"] = "Inc."
    return scored_list + unscored_list

all_races = []
all_aquinas_performances = []
all_team_standings = []

def register_race_from_runners(meta, div_name, gender_label, r_list, source_url, source_file, sub_slug=None, custom_short_meet=None, race_div_override=None):
    """Helper to register a race section, compute team scoring, and append Aquinas performances."""
    if not r_list:
        return
    r_list.sort(key=lambda x: x["place"])
    total_runners = len(r_list)
    aq_runners = [r for r in r_list if r["is_aquinas"]]
    if not aq_runners:
        return
    is_comm = meta["is_1m"]
    slug_part = sub_slug if sub_slug else re.sub(r'[^a-z0-9]+', '_', div_name.lower()).strip('_')
    race_id = f"{meta['meet_id']}__{slug_part}__{gender_label.lower()}"

    aq_sorted = sorted(aq_runners, key=lambda x: x["time_seconds"] or 999999)
    top5 = aq_sorted[:5]
    spread_1_5 = round(top5[-1]["time_seconds"] - top5[0]["time_seconds"], 2) if len(top5) == 5 else None
    avg_top5_sec = round(sum(x["time_seconds"] for x in top5) / len(top5), 2) if top5 else None
    p_vals = [x["pace_seconds"] for x in top5 if x["pace_seconds"]]
    avg_top5_pace = round(sum(p_vals) / len(p_vals), 1) if p_vals else None

    school_teams = [] if is_comm else compute_school_scoring_from_oa(r_list)
    winning_school = next((s for s in school_teams if s["position"] == 1), None)
    aq_school_entry = next((s for s in school_teams if s["is_aquinas"]), None)

    meet_short_col = custom_short_meet if custom_short_meet else meta["short_name"]

    race_obj = {
        "race_id": race_id,
        "meet_id": meta["meet_id"],
        "meet_name": meta["meet_name"],
        "short_meet_name": meta["short_label"],
        "meet_short": meet_short_col,
        "date": meta["date"],
        "location": meta["location"],
        "level": "High School" if div_name == "HS Varsity (9-12)" else "Youth (K-8)",
        "division": "All Youth (1M)" if is_comm else div_name,
        "sub_division": race_div_override,
        "is_1m": is_comm,
        "gender": gender_label,
        "source_url": source_url,
        "source_file": source_file,
        "total_finishers": total_runners,
        "aquinas_finishers_count": len(aq_runners),
        "aquinas_top5_avg_seconds": None if is_comm else avg_top5_sec,
        "aquinas_top5_avg_pace_seconds": avg_top5_pace,
        "aquinas_1_to_5_spread_seconds": None if is_comm else spread_1_5,
        "winner_time_seconds": r_list[0]["time_seconds"],
        "winner_name": r_list[0]["name"],
        "winner_team": r_list[0]["team"],
        "top3_runners": [
            {"place": r["place"], "name": r["name"], "team": r["team"], "time": r["time"], "pace": r["pace"], "is_aquinas": r["is_aquinas"]}
            for r in r_list[:3]
        ],
        "winning_school": {
            "team": winning_school["team"],
            "points": winning_school["points"],
            "avg_time": winning_school["avg_time"],
            "is_aquinas": winning_school["is_aquinas"]
        } if winning_school else None,
        "aquinas_team_summary": {
            "position": aq_school_entry["position"],
            "points": aq_school_entry["points"],
            "avg_time": aq_school_entry["avg_time"],
            "scored_teams_count": sum(1 for s in school_teams if s["scored"])
        } if aq_school_entry else None,
        "school_teams": school_teams,
        "aquinas_runners": aq_sorted,
        "all_runners": r_list
    }
    all_races.append(race_obj)

    for idx_team, r in enumerate(aq_sorted, 1):
        effective_div = r["default_division"]
        effective_level = "High School" if effective_div == "HS Varsity (9-12)" else "Youth (K-8)"
        perf = {
            "meet_id": meta["meet_id"],
            "meet_name": meta["meet_name"],
            "short_meet_name": meta["short_label"],
            "meet_short": meet_short_col,
            "date": meta["date"],
            "location": meta["location"],
            "level": effective_level,
            "division": effective_div,
            "race_division": "Harvest Home 1M" if is_comm else (race_div_override or div_name),
            "is_1m": is_comm,
            "gender": gender_label,
            "race_id": race_id,
            "name": r["name"],
            "grade_or_age": r["grade_or_age"],
            "bib": r["bib"],
            "overall_place": r["place"],
            "total_finishers": total_runners,
            "percentile": round(100.0 * (total_runners - r["place"]) / max(total_runners - 1, 1), 1),
            "team_rank": idx_team,
            "time": r["time"],
            "time_seconds": r["time_seconds"],
            "pace": r["pace"],
            "pace_seconds": r["pace_seconds"],
            "source_url": source_url
        }
        all_aquinas_performances.append(perf)

    return race_obj

def append_team_standing_from_race(race_obj, title_str):
    if not race_obj or not race_obj.get("school_teams"):
        return
    st_list = race_obj["school_teams"]
    scored_teams = [s for s in st_list if s["scored"]]
    aq_team = next((s for s in st_list if s["is_aquinas"]), None)
    if not aq_team:
        return
    all_team_standings.append({
        "meet_id": race_obj["meet_id"],
        "meet_name": race_obj["meet_name"],
        "short_meet_name": race_obj["short_meet_name"],
        "meet_short": race_obj["meet_short"],
        "date": race_obj["date"],
        "level": race_obj["level"],
        "division": race_obj["division"],
        "gender": race_obj["gender"],
        "matchup": None,
        "title": title_str,
        "source_url": race_obj["source_url"],
        "source_file": race_obj["source_file"],
        "scored_teams_count": len(scored_teams),
        "aquinas_position": aq_team["position"],
        "aquinas_points": aq_team["points"],
        "aquinas_total_time": aq_team["total_time"],
        "aquinas_avg_time": aq_team["avg_time"],
        "teams": [
            {
                "team": s["team"],
                "is_aquinas": s["is_aquinas"],
                "position": s["position"],
                "points": s["points"],
                "total_time": s["total_time"],
                "avg_time": s["avg_time"]
            }
            for s in st_list
        ]
    })

# 1. Process the 10 Smiley Miles meets
for m in matches:
    href = m["href"]
    fname = m["file"]
    title = m["title"]
    m_code = re.search(r'(RES\d{6})', href).group(1)
    meta = MEET_META[m_code]
    div_name, level = classify_division(title, fname, meta["program"])
    
    if div_name == "Community 5K":
        continue

    fpath = os.path.join("data/raw", fname)
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if "OA" in fname:
        is_comm = (m_code == "RES090926")
        runners_by_gender = {"M": [], "F": []}
        
        if not is_comm:
            for match in row_xc_re.finditer(content):
                place, name, team, bib, grade_age, gend, time_str, pace = match.groups()
                clean_name = normalize_name(name)
                norm_team = normalize_team(team)
                secs = parse_time_to_seconds(time_str)
                p_secs = parse_pace_to_seconds(pace)
                is_aq = "aquinas" in norm_team.lower()
                runner = {
                    "place": int(place),
                    "name": clean_name,
                    "team": norm_team,
                    "bib": int(bib),
                    "grade_or_age": int(grade_age),
                    "gender": gend,
                    "time": time_str,
                    "time_seconds": secs,
                    "pace": pace.strip(),
                    "pace_seconds": p_secs,
                    "is_aquinas": is_aq,
                    "default_division": runner_default_div.get((clean_name, gend), div_name) if is_aq else div_name
                }
                runners_by_gender[gend].append(runner)
        else:
            for match in row_comm_re.finditer(content):
                place, name, team, bib, age_str, gend, ag, time_str, pace = match.groups()
                age = int(age_str)
                if age >= 19:
                    continue
                clean_name = normalize_name(name)
                norm_team = normalize_team(team) if "aquinas" in team.lower() else " ".join(team.split())
                secs = parse_time_to_seconds(time_str)
                p_secs = parse_pace_to_seconds(pace)
                is_aq = "aquinas" in norm_team.lower()
                inferred_div, inferred_grade = infer_division_from_age(age)
                def_div = runner_default_div.get((clean_name, gend), inferred_div) if is_aq else inferred_div
                def_grade = runner_default_grade.get((clean_name, gend), inferred_grade) if is_aq else inferred_grade
                runner = {
                    "place": int(place),
                    "name": clean_name,
                    "team": norm_team,
                    "bib": int(bib),
                    "grade_or_age": def_grade,
                    "gender": gend,
                    "time": time_str,
                    "time_seconds": secs,
                    "pace": pace.strip(),
                    "pace_seconds": p_secs,
                    "is_aquinas": is_aq,
                    "default_division": def_div
                }
                runners_by_gender[gend].append(runner)

        for gend, r_list in runners_by_gender.items():
            if not r_list:
                continue
            if is_comm:
                for idx_new, r_item in enumerate(r_list, 1):
                    r_item["place"] = idx_new
            gender_label = "Boys" if gend == "M" else "Girls"
            register_race_from_runners(
                meta, div_name, gender_label, r_list,
                "https://www.smileymiles.com/" + href, fname
            )

    elif "AG" not in fname:
        gender_label = "Boys" if "boys" in fname.lower() else "Girls"
        matchup = None
        vs_m = re.search(r'Teams\s+(.+?),\s*[A-Za-z\s]+,\s*PA', title)
        if vs_m and "vs" in vs_m.group(1).lower():
            matchup = vs_m.group(1).strip()
        
        teams_parsed = []
        if "Detail Team Results" in content:
            for tm in detail_team_header_re.finditer(content):
                t_name, pos, score_places, score_time, avg_time = tm.groups()
                norm_t = normalize_team(t_name)
                teams_parsed.append({
                    "team": norm_t,
                    "is_aquinas": "aquinas" in norm_t.lower(),
                    "position": int(pos) if pos.isdigit() else pos,
                    "points": int(score_places) if score_places.isdigit() else None,
                    "total_time": score_time.strip() if score_time else None,
                    "avg_time": avg_time.strip() if avg_time else None
                })
        else:
            for tm in summary_team_row_re.finditer(content):
                pos, t_name, pts, f1, f2, f3, f4, f5, f6, f7, top5_time = tm.groups()
                if t_name.strip().lower().startswith("place"):
                    continue
                norm_t = normalize_team(t_name)
                t_sec = parse_time_to_seconds(top5_time.strip()) if top5_time else None
                avg_str = None
                if t_sec:
                    avg_s = t_sec / 5.0
                    mins = int(avg_s // 60)
                    rem = avg_s - mins * 60
                    avg_str = f"{mins}:{rem:05.2f}"
                teams_parsed.append({
                    "team": norm_t,
                    "is_aquinas": "aquinas" in norm_t.lower(),
                    "position": int(pos) if pos.isdigit() else pos,
                    "points": int(pts) if pts.isdigit() else None,
                    "finishers": [int(x) for x in (f1, f2, f3, f4, f5, f6, f7) if x],
                    "total_time": top5_time.strip() if top5_time else None,
                    "avg_time": avg_str
                })

        scored_teams = [t for t in teams_parsed if isinstance(t["position"], int)]
        aq_team = next((t for t in teams_parsed if t["is_aquinas"]), None)
        if matchup and "aquinas" not in matchup.lower():
            continue
        all_team_standings.append({
            "meet_id": meta["meet_id"],
            "meet_name": meta["meet_name"],
            "short_meet_name": meta["short_label"],
            "meet_short": meta["short_name"],
            "date": meta["date"],
            "level": level,
            "division": div_name,
            "gender": gender_label,
            "matchup": matchup,
            "title": title,
            "source_url": "https://www.smileymiles.com/" + href,
            "source_file": fname,
            "scored_teams_count": len(scored_teams),
            "aquinas_position": aq_team["position"] if aq_team else None,
            "aquinas_points": aq_team["points"] if aq_team else None,
            "aquinas_total_time": aq_team["total_time"] if aq_team else None,
            "aquinas_avg_time": aq_team["avg_time"] if aq_team else None,
            "teams": teams_parsed
        })

# 2. Process Extra Meet 1: Red, White & Blue Classic (2026-09-12)
with open("data/extra/milesplit_rwb_1318896.html", "r", encoding="utf-8") as f:
    rwb_html = f.read()

for sec_hdr, gend, g_lbl in [
    ("Girls 1A 5000 Meter run (Finals)", "F", "Girls"),
    ("Boys 1A 5000 Meters (Finals)", "M", "Boys")
]:
    idx = rwb_html.find(sec_hdr)
    if idx != -1:
        r_list = []
        for l in rwb_html[idx:].splitlines()[1:]:
            ls = l.strip()
            if not ls or ls.startswith("Place\t"):
                continue
            if re.match(r'^\d+\t\d*\t', ls):
                parts = ls.split("\t")
                place = int(parts[0])
                bib = int(parts[1]) if parts[1].isdigit() else 0
                clean_name = normalize_name(parts[2])
                norm_team = normalize_team(parts[3])
                time_str = parts[4].strip()
                secs = parse_time_to_seconds(time_str)
                p_secs = int(round(secs / 3.10686)) if secs else None
                pace_str = fmt_pace_from_sec(p_secs)
                is_aq = "aquinas" in norm_team.lower()
                def_grade = runner_default_grade.get((clean_name, gend), 10)
                r_list.append({
                    "place": place,
                    "name": clean_name,
                    "team": norm_team,
                    "bib": bib,
                    "grade_or_age": def_grade,
                    "gender": gend,
                    "time": time_str,
                    "time_seconds": secs,
                    "pace": pace_str,
                    "pace_seconds": p_secs,
                    "is_aquinas": is_aq,
                    "default_division": "HS Varsity (9-12)"
                })
            else:
                break
        ro = register_race_from_runners(
            MEET_META["EXTRA_RWB"], "HS Varsity (9-12)", g_lbl, r_list,
            "https://pa.milesplit.com/meets/766811-24th-annual-red-white-and-blue-classic-2026/results/1318896/raw",
            "milesplit_rwb_1318896.html"
        )
        append_team_standing_from_race(ro, f"24th Annual Red, White & Blue Classic - {g_lbl} 1A")

# 3. Process Extra Meet 2: RunHigh PIAA Foundation XC Invitational (2026-09-26)
rh_ind_re = re.compile(
    r'^\s*(\d+)\s+(\d+)\s+(?:\d+\s+)?([A-Za-z\.\'\-\s]+?),\s*(1[0-2]|[789])\*?\s*(?:\d+:\d+\.\d+\s+)?(\d+:\d+\.\d+)\s+(\d+:\d+)\s+(.+?)\s*$'
)
for code, gend, g_lbl, is_jv in [
    ("R092626DB.html", "F", "Girls", False),
    ("R092626DE.html", "M", "Boys", False),
    ("R092626DI.html", "M", "Boys", True)
]:
    with open(f"data/extra/runhigh_{code}", "r", encoding="utf-8") as f:
        h = f.read()
    idx = h.rfind("INDIVIDUALS")
    r_list = []
    for l in h[idx:].splitlines():
        m = rh_ind_re.match(l)
        if m:
            bib, place, name, grade_str, time_str, pace_raw, team_raw = m.groups()
            clean_name = normalize_name(name)
            norm_team = normalize_team(team_raw)
            secs = parse_time_to_seconds(time_str)
            pace_str = pace_raw.strip() + "/M"
            p_secs = parse_pace_to_seconds(pace_str)
            is_aq = "aquinas" in norm_team.lower()
            r_list.append({
                "place": int(place),
                "name": clean_name,
                "team": norm_team,
                "bib": int(bib),
                "grade_or_age": int(grade_str),
                "gender": gend,
                "time": time_str,
                "time_seconds": secs,
                "pace": pace_str,
                "pace_seconds": p_secs,
                "is_aquinas": is_aq,
                "default_division": "HS Varsity (9-12)"
            })
    if not is_jv:
        ro = register_race_from_runners(
            MEET_META["EXTRA_PIAA"], "HS Varsity (9-12)", g_lbl, r_list,
            f"https://www.runhigh.com/2026RESULTS/{code}",
            f"runhigh_{code}"
        )
        append_team_standing_from_race(ro, f"20th PIAA Foundation XC Invitational - {g_lbl} 1A")
    else:
        # Add JV Boys individual finishes for Peter Koble & Luke Schellhaas
        total_jv = len(r_list)
        aq_jv = [r for r in r_list if r["is_aquinas"]]
        for idx_t, r in enumerate(aq_jv, 1):
            all_aquinas_performances.append({
                "meet_id": MEET_META["EXTRA_PIAA"]["meet_id"],
                "meet_name": MEET_META["EXTRA_PIAA"]["meet_name"],
                "short_meet_name": MEET_META["EXTRA_PIAA"]["short_label"],
                "meet_short": MEET_META["EXTRA_PIAA"]["short_name"],
                "date": MEET_META["EXTRA_PIAA"]["date"],
                "location": MEET_META["EXTRA_PIAA"]["location"],
                "level": "High School",
                "division": "HS Varsity (9-12)",
                "race_division": "HS JV (9-12)",
                "is_1m": False,
                "gender": "Boys",
                "race_id": f"{MEET_META['EXTRA_PIAA']['meet_id']}__hs_varsity_9_12__boys",
                "name": r["name"],
                "grade_or_age": r["grade_or_age"],
                "bib": r["bib"],
                "overall_place": r["place"],
                "total_finishers": total_jv,
                "percentile": round(100.0 * (total_jv - r["place"]) / max(total_jv - 1, 1), 1),
                "team_rank": 7 + idx_t,
                "time": r["time"],
                "time_seconds": r["time_seconds"],
                "pace": r["pace"],
                "pace_seconds": r["pace_seconds"],
                "source_url": f"https://www.runhigh.com/2026RESULTS/{code}"
            })

# 4. Process Extra Meet 3: WPIAL A/AA Section 4 XC Championships (2026-10-06)
with open("data/extra/firestore_782377_wpial_sec4.json", "r", encoding="utf-8") as f:
    fs_sec4 = json.load(f)

for ev_num, gend, g_lbl, is_jv in [
    ("1", "M", "Boys", False),
    ("2", "F", "Girls", False),
    ("3", "M", "Boys", True)
]:
    ev_docs = [d for d in fs_sec4["entries"] if d.get("fields", {}).get("event", {}).get("integerValue") == ev_num]
    r_list = []
    for d in ev_docs:
        flds = d["fields"]
        res = flds.get("result", {}).get("mapValue", {}).get("fields", {})
        place_str = res.get("place", {}).get("integerValue")
        time_str = res.get("text", {}).get("stringValue")
        if not place_str or not time_str:
            continue
        ath = flds.get("athlete", {}).get("mapValue", {}).get("fields", {})
        tm = ath.get("team", {}).get("mapValue", {}).get("fields", {})
        raw_name = f"{ath.get('firstName', {}).get('stringValue', '')} {ath.get('lastName', {}).get('stringValue', '')}".strip()
        clean_name = normalize_name(raw_name)
        norm_team = normalize_team(tm.get("name", {}).get("stringValue", ""))
        bib_str = ath.get("compNo", {}).get("integerValue", "0")
        secs = parse_time_to_seconds(time_str)
        p_secs = int(round(secs / 3.10686)) if secs else None
        pace_str = fmt_pace_from_sec(p_secs)
        is_aq = "aquinas" in norm_team.lower()
        def_grade = runner_default_grade.get((clean_name, gend), 10)
        r_list.append({
            "place": int(place_str),
            "name": clean_name,
            "team": norm_team,
            "bib": int(bib_str) if str(bib_str).isdigit() else 0,
            "grade_or_age": def_grade,
            "gender": gend,
            "time": time_str,
            "time_seconds": secs,
            "pace": pace_str,
            "pace_seconds": p_secs,
            "is_aquinas": is_aq,
            "default_division": "HS Varsity (9-12)"
        })
    if not is_jv:
        ro = register_race_from_runners(
            MEET_META["EXTRA_SEC4"], "HS Varsity (9-12)", g_lbl, r_list,
            "https://milesplit.live/meets/782377/schedule",
            "firestore_782377_wpial_sec4.json"
        )
        append_team_standing_from_race(ro, f"WPIAL A/AA Section 4 XC Championships - {g_lbl} 5K")
    else:
        r_list.sort(key=lambda x: x["place"])
        total_jv = len(r_list)
        aq_jv = [r for r in r_list if r["is_aquinas"]]
        for idx_t, r in enumerate(aq_jv, 1):
            all_aquinas_performances.append({
                "meet_id": MEET_META["EXTRA_SEC4"]["meet_id"],
                "meet_name": MEET_META["EXTRA_SEC4"]["meet_name"],
                "short_meet_name": MEET_META["EXTRA_SEC4"]["short_label"],
                "meet_short": MEET_META["EXTRA_SEC4"]["short_name"],
                "date": MEET_META["EXTRA_SEC4"]["date"],
                "location": MEET_META["EXTRA_SEC4"]["location"],
                "level": "High School",
                "division": "HS Varsity (9-12)",
                "race_division": "HS JV (9-12)",
                "is_1m": False,
                "gender": "Boys",
                "race_id": f"{MEET_META['EXTRA_SEC4']['meet_id']}__hs_varsity_9_12__boys",
                "name": r["name"],
                "grade_or_age": r["grade_or_age"],
                "bib": r["bib"],
                "overall_place": r["place"],
                "total_finishers": total_jv,
                "percentile": round(100.0 * (total_jv - r["place"]) / max(total_jv - 1, 1), 1),
                "team_rank": 7 + idx_t,
                "time": r["time"],
                "time_seconds": r["time_seconds"],
                "pace": r["pace"],
                "pace_seconds": r["pace_seconds"],
                "source_url": "https://milesplit.live/meets/782377/schedule"
            })

# 5. Process Extra Meets 4, 5, 6: RunSignup (Oakland Catholic 191674, Run for Pumpkins 193469, Diocesan Champ 193936)
pumpkins_team_lookup = {}
if os.path.exists("data/extra/rsu_193469_team_results.json"):
    with open("data/extra/rsu_193469_team_results.json", "r", encoding="utf-8") as f:
        ptr = json.load(f)
    for tr_id, tr_obj in ptr.items():
        lbl = tr_obj["label"]
        tdata = tr_obj["data"]
        tid_to_name = {}
        for row in tdata.get("results", []):
            if len(row) >= 2:
                tid_to_name[row[0]] = row[1]
        for mrow in tdata.get("member_results", []):
            # [team_id, team_place, overall_place, member_score, name, gender, bib, clock_time, chip_time, dist]
            tid = mrow[0]
            tname = tid_to_name.get(tid, "")
            if not tname:
                continue
            m_place = int(mrow[2]) if str(mrow[2]).isdigit() else None
            m_name = normalize_name(mrow[4])
            m_bib = int(mrow[6]) if str(mrow[6]).isdigit() else None
            if m_bib is not None:
                pumpkins_team_lookup[(lbl, "bib", m_bib)] = tname
            if m_place is not None:
                pumpkins_team_lookup[(lbl, "place", m_place)] = tname
            if m_name:
                pumpkins_team_lookup[(lbl, "name", m_name)] = tname

def process_rsu_file(fname, meta_key):
    meta = MEET_META[meta_key]
    with open(f"data/extra/{fname}", "r", encoding="utf-8") as f:
        d = json.load(f)
    rid = d["race_id"]
    for ev in d["events"]:
        ev_name = ev["event_name"]
        # Skip synthetic Combined Dev in 193936 so K-2 and 3-4 runners aren't duplicated
        if "Combined" in ev_name:
            continue
        res = ev["results"]
        if not res:
            continue
        rev_h = {v: k for k, v in ev["headers"].items()}
        t_key = rev_h.get("Team Name")
        y_key = rev_h.get("Year")
        if not t_key and str(rid) != "193469":
            continue

        # Determine division, gender, sub_slug, race_div_override
        ev_low = ev_name.lower()
        gend = "M" if "boy" in ev_low else "F"
        g_lbl = "Boys" if gend == "M" else "Girls"

        sub_slug = None
        div_override = None
        if "varsity" in ev_low:
            div_name = "MS Varsity (7-8)"
        elif "jv" in ev_low:
            div_name = "Elementary JV (5-6)"
        elif "k-2" in ev_low:
            div_name = "Developmental (K-4)"
            sub_slug = "developmental_k_2"
            div_override = "Developmental (K-2)"
        elif "3-4" in ev_low:
            div_name = "Developmental (K-4)"
            sub_slug = "developmental_3_4"
            div_override = "Developmental (3-4)"
        else:
            div_name = "Developmental (K-4)"

        r_list = []
        for r in res:
            place_val = r.get("place")
            time_str = (r.get("clock_time") or r.get("chip_time") or "").strip()
            if not place_val or not str(place_val).isdigit() or not time_str:
                continue
            secs = parse_time_to_seconds(time_str)
            if secs is None:
                continue
            raw_n = f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
            clean_name = normalize_name(raw_n)
            bib_num = int(r.get("bib") or 0) if str(r.get("bib") or "").isdigit() else 0
            p_num = int(place_val)
            if t_key:
                t_raw = (r.get(t_key) or "").strip()
            else:
                t_raw = (
                    pumpkins_team_lookup.get((ev_name, "bib", bib_num))
                    or pumpkins_team_lookup.get((ev_name, "place", p_num))
                    or pumpkins_team_lookup.get((ev_name, "name", clean_name))
                    or ""
                )
            norm_team = normalize_team(t_raw)
            is_aq = "aquinas" in norm_team.lower()
            pace_raw = (r.get("pace") or "").strip()
            pace_str = (pace_raw + "/M") if pace_raw and not pace_raw.endswith("/M") else pace_raw
            p_secs = parse_pace_to_seconds(pace_str)
            if p_secs is None and secs:
                dist_miles = 1.2427 if "Developmental" in div_name else 1.8641
                p_secs = int(round(secs / dist_miles))
                pace_str = fmt_pace_from_sec(p_secs)
            yr_val = r.get(y_key) if y_key else None
            if yr_val and str(yr_val).isdigit():
                grade_val = int(yr_val)
            else:
                grade_val = runner_default_grade.get((clean_name, gend), 7 if "Varsity" in div_name else (5 if "JV" in div_name else 3))

            def_div = runner_default_div.get((clean_name, gend), div_name) if is_aq else div_name
            if is_aq and (clean_name, gend) not in runner_default_div:
                runner_default_div[(clean_name, gend)] = div_name
                runner_default_grade[(clean_name, gend)] = grade_val

            r_list.append({
                "place": p_num,
                "name": clean_name,
                "team": norm_team,
                "bib": bib_num,
                "grade_or_age": grade_val,
                "gender": gend,
                "time": time_str,
                "time_seconds": secs,
                "pace": pace_str,
                "pace_seconds": p_secs,
                "is_aquinas": is_aq,
                "default_division": def_div
            })

        src_url = f"https://runsignup.com/Race/Results/{rid}?resultSetId={ev['result_set_id']}"
        ro = register_race_from_runners(
            meta, div_name, g_lbl, r_list,
            src_url, fname,
            sub_slug=sub_slug, custom_short_meet=None, race_div_override=div_override
        )
        append_team_standing_from_race(ro, f"{meta['meet_name']} - {ev_name}")

process_rsu_file("rsu_191674_oakland_catholic.json", "EXTRA_OC")
process_rsu_file("rsu_193469_run_for_pumpkins.json", "EXTRA_PUMPKINS")
process_rsu_file("rsu_193936_diocesan_champ.json", "EXTRA_DIOCESAN")

all_races.sort(key=lambda x: (x["date"], x["meet_id"], x["division"], x["race_id"]))
all_aquinas_performances.sort(key=lambda x: (x["date"], x["meet_id"], x["division"], x["gender"], x["overall_place"]))
all_team_standings.sort(key=lambda x: (x["date"], x["meet_id"], x["division"], x["gender"], x["title"]))

athletes = {}
for p in all_aquinas_performances:
    key = (p["name"], p["gender"])
    if key not in athletes:
        athletes[key] = {
            "name": p["name"],
            "gender": p["gender"],
            "level": p["level"],
            "division": p["division"],
            "grade_or_age": p["grade_or_age"],
            "races": []
        }
    athletes[key]["races"].append({
        "meet_id": p["meet_id"],
        "short_meet_name": p["short_meet_name"],
        "meet_short": p["meet_short"],
        "date": p["date"],
        "division": p["division"],
        "race_division": p["race_division"],
        "is_1m": p["is_1m"],
        "overall_place": p["overall_place"],
        "total_finishers": p["total_finishers"],
        "percentile": p["percentile"],
        "team_rank": p["team_rank"],
        "time": p["time"],
        "time_seconds": p["time_seconds"],
        "pace": p["pace"],
        "pace_seconds": p["pace_seconds"],
        "source_url": p["source_url"]
    })

athlete_list = []
for key, a in athletes.items():
    a["races"].sort(key=lambda r: (r["date"], r["meet_id"]))
    xc_races = [r for r in a["races"] if not r["is_1m"]]
    ref_races = xc_races if xc_races else a["races"]
    
    times = [r["time_seconds"] for r in ref_races if r["time_seconds"]]
    paces = [r["pace_seconds"] for r in a["races"] if r["pace_seconds"]]
    best_race = min(ref_races, key=lambda r: r["time_seconds"] or 999999)
    best_pace_race = min(a["races"], key=lambda r: r["pace_seconds"] or 999999)
    
    pace_change_sec = None
    if len(xc_races) >= 2 and xc_races[0]["pace_seconds"] and xc_races[-1]["pace_seconds"]:
        pace_change_sec = xc_races[-1]["pace_seconds"] - xc_races[0]["pace_seconds"]
    elif len(a["races"]) >= 2 and a["races"][0]["pace_seconds"] and a["races"][-1]["pace_seconds"]:
        pace_change_sec = a["races"][-1]["pace_seconds"] - a["races"][0]["pace_seconds"]

    best_gain_sec = None
    if len(xc_races) >= 2:
        first_p = xc_races[0]["pace_seconds"]
        later_p = [r["pace_seconds"] for r in xc_races[1:] if r["pace_seconds"]]
        if first_p and later_p:
            best_gain_sec = min(later_p) - first_p

    a["races_count"] = len(a["races"])
    a["xc_races_count"] = len(xc_races)
    a["pr_seconds"] = best_race["time_seconds"]
    a["pr_time"] = best_race["time"]
    a["pr_meet"] = best_race["short_meet_name"]
    a["pr_pace"] = best_race["pace"]
    a["pr_pace_seconds"] = best_race["pace_seconds"]
    a["fastest_pace"] = best_pace_race["pace"]
    a["fastest_pace_seconds"] = best_pace_race["pace_seconds"]
    a["avg_seconds"] = round(sum(times) / len(times), 2) if times else None
    a["avg_pace_seconds"] = round(sum(paces) / len(paces), 1) if paces else None
    a["avg_percentile"] = round(sum(r["percentile"] for r in a["races"]) / len(a["races"]), 1)
    a["best_place"] = min(r["overall_place"] for r in a["races"])
    a["top_10_finishes"] = sum(1 for r in a["races"] if r["overall_place"] <= 10)
    a["pace_change_sec"] = pace_change_sec
    a["best_gain_sec"] = best_gain_sec
    athlete_list.append(a)

athlete_list.sort(key=lambda x: (x["level"], x["division"], x["gender"], x["pr_seconds"] or 999999))

meets_ordered = sorted(list(MEET_META.values()), key=lambda m: (m["date"], m["meet_id"]))

full_dataset = {
    "generated_at": "2026-10-23",
    "team": "Aquinas Academy of Pittsburgh",
    "source": "Smiley Miles, Wolf Creek / RunSignup, Runner's High & PA MileSplit",
    "summary": {
        "total_meets": len(meets_ordered),
        "total_matched_files": len(matches) + 8,
        "total_race_sections": len(all_races),
        "total_aquinas_entries": len(all_aquinas_performances),
        "unique_aquinas_athletes": len(athlete_list),
        "total_team_standings": len(all_team_standings)
    },
    "meets": meets_ordered,
    "team_standings": all_team_standings,
    "athletes": athlete_list,
    "performances": all_aquinas_performances,
    "races": all_races
}

os.makedirs("data", exist_ok=True)
with open("data/aquinas_2026_full.json", "w", encoding="utf-8") as f:
    json.dump(full_dataset, f, indent=2)

with open("data/data.js", "w", encoding="utf-8") as f:
    f.write("window.AQUINAS_XC_DATA = ")
    json.dump(full_dataset, f)
    f.write(";\n")

# Also write CSVs
with open("data/aquinas_2026_performances.csv", "w", newline="", encoding="utf-8") as f:
    if all_aquinas_performances:
        w = csv.DictWriter(f, fieldnames=list(all_aquinas_performances[0].keys()))
        w.writeheader()
        w.writerows(all_aquinas_performances)

with open("data/aquinas_2026_team_scores.csv", "w", newline="", encoding="utf-8") as f:
    if all_team_standings:
        fields = [k for k in all_team_standings[0].keys() if k != "teams"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in all_team_standings:
            w.writerow({k: row[k] for k in fields})

print("Summary:", json.dumps(full_dataset["summary"], indent=2))
