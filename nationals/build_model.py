import os, glob, re, json, math, csv
import numpy as np
from bs4 import BeautifulSoup

np.random.seed(20261121)

base_scratch = r"C:\Users\j_t_v\.gemini\antigravity\brain\fd1d52a6-9fa9-45a6-a634-3e07b1681514\scratch"
web_dir = os.path.join(base_scratch, "cccnyc_web")
ms_dir = os.path.join(web_dir, "milesplit_raw")
sm_dir = os.path.join(web_dir, "smiley_2026")

site_dir = r"c:\Users\j_t_v\XC\nationals"
data_out_dir = os.path.join(site_dir, "data")
os.makedirs(data_out_dir, exist_ok=True)

def parse_time_sec(tstr):
    if not tstr: return None
    tstr = tstr.strip()
    m = re.match(r"^(?:(\d+):)?(\d{1,2}):(\d{2}(?:\.\d+)?)$", tstr)
    if m:
        h, mn, sc = m.groups()
        return (int(h)*3600 if h else 0) + int(mn)*60 + float(sc)
    return None

def fmt_time(sec, tenths=False):
    if sec is None or math.isnan(sec): return ""
    mn = int(sec // 60)
    rem = sec - mn * 60
    if tenths:
        return f"{mn}:{rem:04.1f}"
    return f"{mn}:{rem:05.2f}"

def fmt_pace_mi(sec, dist_m):
    if not sec or not dist_m: return ""
    pace_s = sec / (dist_m / 1609.344)
    mn = int(pace_s // 60)
    sc = int(round(pace_s - mn * 60))
    if sc == 60: mn += 1; sc = 0
    return f"{mn}:{sc:02d}"

def clean_person_name(first, last):
    first = re.sub(r"\(.*?\)", "", first or "").strip()
    first = re.sub(r"^\d+\s+", "", first).strip()
    last = re.sub(r"^\d+\s+", "", last or "").strip()
    first_tok = first.split()[0] if first else ""
    return first_tok.lower(), last.lower()

NICKNAMES = {
    "colette": ["collette"], "collette": ["colette"],
    "katalina": ["catalina", "kat", "kate"], "catalina": ["katalina"],
    "madelyn": ["maddie", "maddy", "madeline"], "maddy": ["madeline", "madelyn", "maddie"], "madeline": ["maddie", "maddy", "madelyn"],
    "william": ["will", "liam", "billy"], "will": ["william"],
    "joseph": ["joey", "joe"], "joey": ["joseph"],
    "benjamin": ["ben", "benny"], "ben": ["benjamin"],
    "samuel": ["sam"], "sam": ["samuel"],
    "nicholas": ["nick"], "nick": ["nicholas"],
    "alexander": ["alex"], "alex": ["alexander", "alexandros"],
    "elizabeth": ["ellie", "liz", "beth"], "ellie": ["elizabeth", "eleanor"],
    "katherine": ["kate", "katie"], "kate": ["katherine", "kaitlyn"],
    "cecilia": ["cece"], "cece": ["cecilia", "celia"],
    "theodore": ["theo", "teddy"], "theo": ["theodore"], "teddi": ["theodora", "teddy"],
    "christopher": ["chris"], "daniel": ["dan", "danny"],
    "matthew": ["matt"], "andrew": ["andy", "drew"], "drew": ["andrew"],
    "gabriel": ["gabe"], "gabe": ["gabriel"],
    "jacob": ["jake"], "jake": ["jacob"],
    "michael": ["mike"], "thomas": ["tom", "tommy"], "tommy": ["thomas"],
    "phillip": ["phil", "philip"], "charles": ["charlie"], "charlie": ["charles"],
    "lucia": ["lucy"], "evina": ["evie"], "mirabella": ["bella"],
    "vincenzo": ["vinny", "enzo", "vincent"], "raymond": ["ray"], "maximus": ["max"],
    "james": ["jamie", "jimmy"], "allie": ["allison", "alison"], "abby": ["abigail"], "abigail": ["abby"],
    "addison": ["addie"], "addi": ["addison", "adeline"], "cam": ["cameron", "camden"], "cameron": ["cam"],
    "philomena": ["phoebe"], "virginia": ["jenni", "ginny"],
    "cecila": ["cecilia"], "noaah": ["noah"], "acher": ["archer", "david"],
    "marty": ["martin"], "maddison": ["maddi", "madison", "maddie"],
    "karlee": ["carly"], "joseph": ["joey", "joe", "jay"],
}

def name_keys(first, last):
    fn, ln = clean_person_name(first, last)
    keys = [(fn, ln), (ln, fn)]
    if re.search(r"([a-z])\1\1", ln):
        keys.append((fn, re.sub(r"([a-z])\1\1", r"\1\1", ln)))
    # Also full compound last name without spaces (e.g. Mas Pecina -> maspecina or pecina)
    if " " in ln:
        keys.append((fn, ln.replace(" ", "")))
        for p in ln.split():
            if len(p) >= 4: keys.append((fn, p))
    if "-" in ln:
        for p in ln.split("-"):
            if len(p) >= 4: keys.append((fn, p))
    for alt in NICKNAMES.get(fn, []):
        keys.append((alt, ln))
    return keys

EVENT_META = {
    1: {"num": 1, "name": "Girls 15–18 5K", "short": "15–18 Girls", "gender": "F", "dist_m": 5000, "time_est": "9:00 AM", "awards_time": "9:45 AM", "ages": [15,16,17,18], "award_groups": ["15-16", "17-18"], "qual_std": "Open (No Min)"},
    2: {"num": 2, "name": "Boys 15–18 5K", "short": "15–18 Boys", "gender": "M", "dist_m": 5000, "time_est": "9:30 AM", "awards_time": "10:15 AM", "ages": [15,16,17,18], "award_groups": ["15-16", "17-18"], "qual_std": "Open (No Min)"},
    3: {"num": 3, "name": "Girls 6–8 2K", "short": "6–8 Girls", "gender": "F", "dist_m": 2000, "time_est": "10:00 AM", "awards_time": "10:45 AM", "ages": [6,7,8], "award_groups": ["6", "7", "8"], "qual_std": "12:55 (2K)"},
    4: {"num": 4, "name": "Boys 6–8 2K", "short": "6–8 Boys", "gender": "M", "dist_m": 2000, "time_est": "10:25 AM", "awards_time": "11:15 AM", "ages": [6,7,8], "award_groups": ["6", "7", "8"], "qual_std": "12:55 (2K)"},
    5: {"num": 5, "name": "Race of the Americas (Mixed 1–8 1K)", "short": "Mixed 1–8 1K", "gender": "X", "dist_m": 1000, "time_est": "10:45 AM", "awards_time": "10:50 AM", "ages": [1,2,3,4,5,6,7,8], "award_groups": ["Boys 1-8", "Girls 1-8"], "qual_std": "Developmental Open"},
    6: {"num": 6, "name": "Girls 9–10 3K", "short": "9–10 Girls", "gender": "F", "dist_m": 3000, "time_est": "11:15 AM", "awards_time": "12:15 PM", "ages": [9,10], "award_groups": ["9", "10"], "qual_std": "15:50 (3K)"},
    7: {"num": 7, "name": "Boys 9–10 3K", "short": "9–10 Boys", "gender": "M", "dist_m": 3000, "time_est": "11:45 AM", "awards_time": "12:45 PM", "ages": [9,10], "award_groups": ["9", "10"], "qual_std": "14:50 (3K)"},
    8: {"num": 8, "name": "Girls 11–12 3K", "short": "11–12 Girls", "gender": "F", "dist_m": 3000, "time_est": "12:15 PM", "awards_time": "1:15 PM", "ages": [11,12], "award_groups": ["11", "12"], "qual_std": "15:45 (3K)"},
    9: {"num": 9, "name": "Boys 11–12 3K", "short": "11–12 Boys", "gender": "M", "dist_m": 3000, "time_est": "12:45 PM", "awards_time": "1:45 PM", "ages": [11,12], "award_groups": ["11", "12"], "qual_std": "14:45 (3K)"},
    10: {"num": 10, "name": "Girls 13–14 4K", "short": "13–14 Girls", "gender": "F", "dist_m": 4000, "time_est": "1:15 PM", "awards_time": "2:15 PM", "ages": [13,14], "award_groups": ["13", "14"], "qual_std": "18:45 (4K)"},
    11: {"num": 11, "name": "Boys 13–14 4K", "short": "13–14 Boys", "gender": "M", "dist_m": 4000, "time_est": "1:45 PM", "awards_time": "2:45 PM", "ages": [13,14], "award_groups": ["13", "14"], "qual_std": "17:45 (4K)"},
}

# Club metadata: state, category (CYO/Catholic vs Youth Club vs School), city/region
CLUB_GEO = {
    "Diocese of Pittsburgh": ("PA", "CYO / Diocesan", "Pittsburgh, PA"),
    "Diocese of Pittsburgh A": ("PA", "CYO / Diocesan", "Pittsburgh, PA"),
    "Diocese of Pittsburgh B": ("PA", "CYO / Diocesan", "Pittsburgh, PA"),
    "Columbus CYO": ("OH", "CYO / Diocesan", "Columbus, OH"),
    "Columbus CYO-B": ("OH", "CYO / Diocesan", "Columbus, OH"),
    "Greensburg CYO": ("PA", "CYO / Diocesan", "Greensburg, PA"),
    "Bishop McDevitt - CYO": ("PA", "CYO / Diocesan", "Harrisburg, PA"),
    "St. Patrick": ("MI", "CYO / Parish", "White Lake, MI"),
    "St. Charles Club": ("MI", "CYO / Parish", "Newport, MI"),
    "CRC Grasshoppers": ("OH", "Youth Club", "Columbus, OH"),
    "CRC Grasshoppers B": ("OH", "Youth Club", "Columbus, OH"),
    "CRC Grasshoppers Dublin": ("OH", "Youth Club", "Dublin, OH"),
    "CRC Grasshoppers Westerville": ("OH", "Youth Club", "Westerville, OH"),
    "Buckeye Racers": ("OH", "Youth Club", "Upper Sandusky / NW OH"),
    "Buckeye Racers-B Team": ("OH", "Youth Club", "Upper Sandusky / NW OH"),
    "Minster XC": ("OH", "School / Town Club", "Minster, OH"),
    "Hudson Youth Cross Country": ("OH", "Youth Club", "Hudson, OH"),
    "Copley Youth Cross Country": ("OH", "Youth Club", "Copley, OH"),
    "Cleveland Youth Running Club": ("OH", "Youth Club", "Cleveland, OH"),
    "Ohio Elite Cross Country": ("OH", "Youth Club", "Central / SW OH"),
    "Hilliard Track Club": ("OH", "Youth Club", "Hilliard, OH"),
    "North Union Intermdiate": ("OH", "School", "Richwood, OH"),
    "Dresden Middle": ("OH", "School", "Dresden, OH"),
    "Clinton Running Club": ("MI", "Youth Club", "Clinton, MI"),
    "Team Kentucky": ("KY", "State All-Star Club", "Kentucky"),
    "Bates Elementary": ("KY", "School", "Louisville, KY"),
    "Harmony Elementary School": ("KY", "School", "Goshen, KY"),
    "Shelby County Pacers": ("KY", "Youth Club", "Shelbyville, KY"),
    "Camden Clock Chasers": ("NJ", "Youth Club", "Camden, NJ"),
    "Northeast Striders": ("KY", "Youth Club", "Louisville, KY"),
    "Eastern KY Striders": ("KY", "Youth Club", "Eastern KY"),
    "Green Wave": ("IN", "Youth Club", "Westfield, IN"),
    "Eagles Elite": ("MI", "Youth Club", "Hartland, MI"),
    "Accel Sports": ("TN", "Youth Club", "Lebanon, TN"),
    "Indiana Pathfinders": ("IN", "Youth Club", "Columbus, IN"),
    "Southern Indiana Runing Club": ("IN", "Youth Club", "New Albany / So. IN"),
    "Saline MS": ("MI", "School", "Saline, MI"),
    "Ann Arbor Track Club": ("MI", "Youth Club", "Ann Arbor, MI"),
    "Michigan Cougars": ("MI", "Youth Club", "SE Michigan"),
    "Pinconning": ("MI", "School / Club", "Pinconning, MI"),
    "Chicago Rabbits": ("IL", "Youth Club", "Chicago, IL"),
    "Crimson Knights": ("NJ", "Youth Club", "Woodbridge, NJ"),
    "Buffalo Chips Running Club": ("CA", "Youth Club", "Sacramento, CA"),
    "NorCal Distance": ("CA", "Youth Club", "Northern California"),
    "FREDERICK BLAZE": ("MD", "Youth Club", "Frederick, MD"),
    "Olney Cross Country Club": ("MD", "Youth Club", "Olney, MD"),
    "Damascus Freedom": ("MD", "Youth Club", "Damascus, MD"),
    "Nittany Track and Field": ("PA", "Youth Club", "State College, PA"),
    "Team F.C.A. KS": ("KS", "Youth Club", "Kansas"),
    "Southern MN Youth XC": ("MN", "Youth Club", "Owatonna, MN"),
    "Staley Striders": ("IL", "Youth Club", "Decatur, IL"),
    "Edmond Thunder Cross Country &": ("OK", "Youth Club", "Edmond, OK"),
    "Delta Hawks Racing": ("CA", "Youth Club", "West Sacramento, CA"),
    "Embrace Sportz": ("MI", "Youth Club", "Detroit, MI"),
    "Fox City": ("VA", "Youth Club", "Fairfax, VA"),
    "ALTIUS Track & Field": ("OH", "Youth Club", "Ohio"),
    "Bermuda Pacers": ("INTL", "Youth Club", "Bermuda"),
    "REAL Distance Training Academy": ("AL", "Youth Club", "Madison, AL"),
    "Styn Strong Racing": ("OH", "Youth Club", "Columbus, OH"),
    "Tailwind TC": ("NY", "Youth Club", "Westchester, NY"),
    "The Stead": ("CO", "Youth Club", "Colorado"),
    "Threshold and Beyond": ("OH", "Youth Club", "Ohio"),
    "Unattached": ("USA", "Individual", "National Individual"),
}

def get_base_org(team_name):
    t = team_name or "Unattached"
    for suf in [" A", " B", "-B", "-B Team", " Dublin", " Westerville"]:
        if t.endswith(suf):
            return t[:-len(suf)].strip()
    return t

def is_cyo_team(team_name):
    st, cat, _ = CLUB_GEO.get(team_name, ("USA", "Youth Club", ""))
    return "CYO" in cat

def is_b_squad(team_name):
    return any(team_name.endswith(s) for s in [" B", "-B", "-B Team"])

# Load entries
with open(os.path.join(base_scratch, "parsed_entries.json"), encoding="utf-8") as f:
    drive_raw = json.load(f)["entries"]
with open(os.path.join(base_scratch, "unified_entries_2026.json"), encoding="utf-8") as f:
    uni_data = json.load(f)

drive_set = {(e["event_num"], e["raw_name"], e["age"]) for e in drive_raw}

DELTA_GHOSTS = {
    (6, "Cypress, Connelly"), (6, "Kailey, Donovan"), (6, "Rosie, Steed"),
    (8, "Betsy, Steed"), (8, "Mia, Jackson"),
    (9, "Benjamin, Schafer"), (9, "William, Welch"),
    (10, "Amelia, Weeks"), (10, "Josie, Thronson"), (10, "Maddi, Orr"),
    (11, "David, Rodriguez"),
}

athletes = []
for idx, e in enumerate(uni_data["entries"]):
    ev_num = e["event_num"]
    raw_nm = re.sub(r"^\d+\s+", "", e["raw_name"].strip())
    if "," in raw_nm:
        ln, fn = [x.strip() for x in raw_nm.split(",", 1)]
    else:
        parts = raw_nm.split()
        ln, fn = parts[-1], " ".join(parts[:-1])
    age_raw = e["age"]
    if age_raw.startswith("M") or age_raw.startswith("W"):
        gend = "M" if age_raw.startswith("M") else "F"
        age_num = int(age_raw[1:])
    else:
        gend = EVENT_META[ev_num]["gender"]
        age_num = int(age_raw)
    team = e["team"]
    st, cat, reg = CLUB_GEO.get(team, ("USA", "Youth Club", ""))
    is_ghost = False
    anomaly_note = None
    if team == "Delta Hawks Racing" and (ev_num, raw_nm) in DELTA_GHOSTS:
        is_ghost = True
        anomaly_note = "Duplicate swapped First/Last registration row in official Hy-Tek PDF"
    if ev_num == 3 and raw_nm == "Gerko, Elaine" and team == "Unattached":
        is_ghost = True
        anomaly_note = "Dual-listed on both Columbus CYO and Unattached in Event 3"
    in_drive_pdf = (ev_num, e["raw_name"], e["age"]) in drive_set
    if not in_drive_pdf and not anomaly_note:
        anomaly_note = "Added in Saturday 10:00 PM official entry update"

    # Determine single-year award group
    if ev_num in (1, 2):
        awd_grp = "15-16" if age_num <= 16 else "17-18"
    elif ev_num == 5:
        awd_grp = "Boys 1-8" if gend == "M" else "Girls 1-8"
    else:
        awd_grp = str(age_num)

    athletes.append({
        "id": f"A{idx+1:04d}",
        "event_num": ev_num,
        "first_name": fn,
        "last_name": ln,
        "display_name": f"{fn} {ln}".strip(),
        "raw_name": raw_nm,
        "gender": gend,
        "age": age_num,
        "award_group": awd_grp,
        "team": team,
        "base_org": get_base_org(team),
        "club_state": st,
        "club_category": cat,
        "club_region": reg,
        "is_cyo": is_cyo_team(team),
        "is_dop": "Diocese of Pittsburgh" in team,
        "in_drive_pdf": in_drive_pdf,
        "is_duplicate_ghost": is_ghost,
        "anomaly_note": anomaly_note,
        "home_school": None,
        "grade": None,
        "races_2026": [],
        "cccnyc_history": [],
    })

ath_lookup = {}
for i, a in enumerate(athletes):
    for fk, lk in name_keys(a["first_name"], a["last_name"]):
        ath_lookup.setdefault((a["gender"], fk, lk), []).append(i)

def match_athlete(gender, first, last, grade=None, age=None, state_hint=None):
    matched = set()
    for fk, lk in name_keys(first, last):
        for idx in ath_lookup.get((gender, fk, lk), []):
            a = athletes[idx]
            if a["is_duplicate_ghost"]: continue
            if age is not None and str(age).isdigit():
                av = int(age)
                if av >= 5 and abs(av - a["age"]) > 1: continue
            if grade is not None and str(grade).isdigit():
                gv = int(grade)
                if 0 <= gv <= 12:
                    if not (gv + 4 <= a["age"] <= gv + 8): continue
            if state_hint and a["club_state"] not in ("USA", "INTL", state_hint):
                # Allow border states (e.g. KY/IN/OH or MD/PA) only if exact club region fits
                border = {
                    "KY": {"IN", "OH"}, "IN": {"KY", "OH", "IL", "MI"},
                    "OH": {"KY", "IN", "MI", "PA"}, "PA": {"OH", "MD"},
                    "IL": {"IN", "WI", "MO"}, "MI": {"OH", "IN"},
                }
                if a["club_state"] not in border.get(state_hint, set()):
                    continue
            matched.add(idx)
    return sorted(matched)

# --- 1. Ingest RunSignup JSONs ---
def ingest_rsu(fp, meet_label, meet_date, state_code):
    if not os.path.exists(fp): return 0
    with open(fp, encoding="utf-8") as f: d = json.load(f)
    hits = 0
    for ev in d.get("events", []):
        ev_name = ev.get("event_name", "")
        if "Combined" in ev_name: continue
        dist_str = str(ev.get("distance") or "") + " " + ev_name
        dm_fixed = None
        if "5K" in dist_str.upper() or "5000" in dist_str: dm_fixed = 5000
        elif "4K" in dist_str.upper() or "4000" in dist_str: dm_fixed = 4000
        elif "2 Mile" in dist_str or "3200" in dist_str: dm_fixed = 3219
        elif "3K" in dist_str.upper() or "3000" in dist_str or ("Middle School" in meet_label and state_code == "IN"): dm_fixed = 3000
        elif "2K" in dist_str.upper() or "2000" in dist_str: dm_fixed = 2000
        elif "1.5" in dist_str: dm_fixed = 2414
        elif "0.75" in dist_str: dm_fixed = 1207
        elif "1 Mile" in dist_str and "193936" not in fp: dm_fixed = 1609
        headers_map = ev.get("headers", {})
        school_fields = [k for k, v in headers_map.items() if v in ("School", "Team Name")]
        year_fields = [k for k, v in headers_map.items() if v in ("Year", "Grade")]
        split_fields = [k for k, v in headers_map.items() if "1 Mile" in v and "Pace" not in v]
        res_list = ev.get("results", [])
        nf = len(res_list)
        for r in res_list:
            t_sec = parse_time_sec(r.get("chip_time") or "") or parse_time_sec(r.get("clock_time") or "")
            if not t_sec or t_sec < 150: continue
            pace_sec = parse_time_sec(r.get("pace") or "")
            dm = dm_fixed
            if dm is None and pace_sec and pace_sec > 180:
                dm = round((t_sec / pace_sec) * 1609.344)
            if not dm: dm = 3000
            # Empirical course distance correction for Pittsburgh Diocesan Dev (actual 1.50 mi = 2414m vs timer 1.35 mi) & Pumpkins Dev (2220m)
            if "193936" in fp and "Dev" in ev_name:
                dm = 2414
            elif "193469" in fp and dm < 2200:
                dm = 2220
            gend = (r.get("gender") or "").upper()
            if gend not in ("M", "F"):
                gend = "F" if "Girl" in ev_name else ("M" if "Boy" in ev_name else "")
            yr_val = next((str(r.get(yf)).strip() for yf in year_fields if r.get(yf)), None)
            sch_vals = [str(r.get(sf)).strip() for sf in school_fields if r.get(sf) and str(r.get(sf)) != "None"]
            sch = sch_vals[-1] if sch_vals else None
            split_1m = next((str(r.get(sf)).strip() for sf in split_fields if r.get(sf)), None)
            for idx in match_athlete(gend, r.get("first_name"), r.get("last_name"), grade=yr_val, age=r.get("age"), state_hint=state_code):
                a = athletes[idx]
                if "193936" in fp and not a["is_dop"] and a["club_state"] != "PA": continue
                if sch and (not a["home_school"] or "193936" in fp):
                    a["home_school"] = sch
                if yr_val and not a["grade"]:
                    a["grade"] = yr_val
                a["races_2026"].append({
                    "meet": meet_label, "date": meet_date, "division": ev_name,
                    "place": int(r["place"]) if str(r.get("place", "")).isdigit() else None,
                    "field_size": nf, "dist_m": dm, "time_sec": round(t_sec, 2),
                    "time_str": fmt_time(t_sec), "pace_mi": fmt_pace_mi(t_sec, dm),
                    "split_1m": split_1m, "school_team": sch,
                })
                hits += 1
    return hits

ingest_rsu(r"c:\Users\j_t_v\XC\data\extra\rsu_193936_diocesan_champ.json", "Pittsburgh Diocesan XC Championship", "2026-10-17", "PA")
ingest_rsu(r"c:\Users\j_t_v\XC\data\extra\rsu_191674_oakland_catholic.json", "Oakland Catholic XC Invitational", "2026-09-12", "PA")
ingest_rsu(r"c:\Users\j_t_v\XC\data\extra\rsu_193469_run_for_pumpkins.json", "Run for the Pumpkins XC", "2026-10-10", "PA")
ingest_rsu(os.path.join(ms_dir, "rsu_217626_oh_state.json"), "Ohio Elementary & MS State Championship", "2026-10-24", "OH")

# Ingest all newly scraped regional RunSignup Youth/CYO/Qualifier JSONs across 14 states!
for rsu_fp in sorted(glob.glob(os.path.join(ms_dir, "rsu_*.json"))) + sorted(glob.glob(os.path.join(web_dir, "extra_2026", "rsu_*.json"))):
    if "217626" in rsu_fp:
        continue
    try:
        meta_rsu = json.load(open(rsu_fp, encoding="utf-8"))
        r_nm = meta_rsu.get("race_name") or os.path.basename(rsu_fp)
        r_st = meta_rsu.get("state") or ("DE" if "218442" in rsu_fp else ("NJ" if "96405" in rsu_fp else ("MI" if "191074" in rsu_fp else ("OH" if "toledo" in rsu_fp or "anthony" in rsu_fp else None))))
        r_dt_raw = str(meta_rsu.get("date") or "2026-10-01")
        if "/" in r_dt_raw:
            mm_d, dd_d, yy_d = r_dt_raw.split("/")
            r_dt_raw = f"{yy_d}-{int(mm_d):02d}-{int(dd_d):02d}"
        if r_dt_raw.startswith("2026"):
            ingest_rsu(rsu_fp, r_nm, r_dt_raw, r_st)
    except Exception:
        pass

# --- 2. Ingest Smiley Miles 2026 ---
sm_line_re = re.compile(r"^\s*(\d+)\s+([A-Za-z'\-\.\s]+?)\s{2,}([A-Za-z0-9'\-\.\&\s]+?)\s+(\d+)\s+(\d{1,2})\s+([MF])\s+(?:[\d:]+\s+)?(\d+:\d+\.\d+)\s+(\d+:\d+)/[MK]")
for fp in sorted(glob.glob(os.path.join(sm_dir, "*.htm"))):
    bn = os.path.basename(fp)
    m_dt = re.search(r"RES(\d{2})(\d{2})(\d{2})", bn)
    dt_str = f"20{m_dt.group(3)}-{m_dt.group(1)}-{m_dt.group(2)}" if m_dt else "2026-09-15"
    meet_clean = re.sub(r"^2026__RES\d{6}\s*", "", bn).replace(" OA.htm", "").replace(".htm", "").strip()
    txt = BeautifulSoup(open(fp, encoding="utf-8", errors="ignore").read(), "html.parser").get_text()
    rows = []
    for line in txt.splitlines():
        m = sm_line_re.match(line)
        if m:
            pl, nm, tm, bib, age_gr, gend, t_s, p_s = m.groups()
            t_sec, p_sec = parse_time_sec(t_s), parse_time_sec(p_s)
            if t_sec and p_sec and p_sec > 180:
                dm = round((t_sec / p_sec) * 1609.344)
                if 1400 <= dm <= 5300:
                    rows.append((int(pl), nm.strip(), tm.strip(), int(age_gr), gend, t_sec, dm))
    f_cnt = {g: sum(1 for r in rows if r[4] == g) for g in ("M", "F")}
    for pl, nm, tm, age_gr, gend, t_sec, dm in rows:
        parts = nm.split()
        if len(parts) < 2: continue
        fn, ln = parts[0], " ".join(parts[1:])
        gr_h = age_gr if age_gr <= 12 else None
        ag_h = age_gr if age_gr > 12 else None
        for idx in match_athlete(gend, fn, ln, grade=gr_h, age=ag_h, state_hint="PA"):
            a = athletes[idx]
            if a["club_state"] != "PA" and a["team"] != "Unattached": continue
            if not a["home_school"] and tm: a["home_school"] = tm.title()
            if gr_h and not a["grade"]: a["grade"] = str(gr_h)
            a["races_2026"].append({
                "meet": meet_clean, "date": dt_str, "division": meet_clean,
                "place": pl, "field_size": f_cnt.get(gend, len(rows)), "dist_m": dm,
                "time_sec": round(t_sec, 2), "time_str": fmt_time(t_sec),
                "pace_mi": fmt_pace_mi(t_sec, dm), "school_team": tm.title(),
            })

# --- 3. Ingest MileSplit 2026 Raw HTML files (improved column + regex parser!) ---
MS_MEET_INFO = {
    "769360": ("KTCCCA KY Elem & MS State Championship", "2026-10-17", "KY"),
    "789089": ("Bulldog Youth Invitational (OH Qualifier)", "2026-10-17", "OH"),
    "770596": ("Celtic Clash Youth (Dublin OH)", "2026-09-19", "OH"),
    "772133": ("Celtic Clash MS (Dublin OH)", "2026-09-19", "OH"),
    "770598": ("Celtic Clash HS (Dublin OH)", "2026-09-19", "OH"),
    "771794": ("St. Matthews CYO Invitational", "2026-09-13", "OH"),
    "780373": ("St. Pius CYO Invitational", "2026-09-20", "OH"),
    "780376": ("St. Brendan CYO Invitational", "2026-10-04", "OH"),
    "789976": ("Cleveland CYO Championship", "2026-10-18", "OH"),
    "715784": ("Cedarville Friendship XC Invite", "2026-09-19", "OH"),
    "787982": ("Indiana Middle School State Championship", "2026-10-03", "IN"),
    "789290": ("NXR Midwest MS & Community Race", "2026-11-14", "IN"),
    "777310": ("Greensburg CYO Meet #1", "2026-09-13", "PA"),
    "783097": ("Greensburg CYO Meet #3 (Kunkle Park)", "2026-09-27", "PA"),
    "788598": ("Greensburg CYO Meet #5 (St. Vincent)", "2026-10-11", "PA"),
    "779207": ("Windy City XC Challenge", "2026-09-12", "IL"),
    "789241": ("Illinois Youth XC Championships", "2026-11-08", "IL"),
    "761984": ("SEC-MS Saline MS vs Dexter MS", "2026-09-15", "MI"),
}

def infer_dist_and_gender(hl):
    h = hl.lower()
    gend = "F" if any(w in h for w in ["girl", "women", "female"]) else ("M" if any(w in h for w in ["boy", "men", "male"]) else None)
    dm = None
    if any(k in h for k in ["5000", "5,000", "5k"]): dm = 5000
    elif any(k in h for k in ["4000", "4,000", "4k"]): dm = 4000
    elif any(k in h for k in ["3200", "3,200", "2 mile"]): dm = 3200
    elif any(k in h for k in ["3000", "3,000", "3k"]): dm = 3000
    elif any(k in h for k in ["2400", "1.5 mile"]): dm = 2414
    elif any(k in h for k in ["2000", "2,000", "2k"]): dm = 2000
    elif any(k in h for k in ["1 mile", "1600", "1,600"]): dm = 1609
    return gend, dm

ms_re_meetpro = re.compile(r"^\s*(\d+)\s+([A-Z'\-\s]+),\s*([A-Za-z'\-\.\s]+?)\s+(\d{1,2}|SR|JR|SO|FR)?\s+\d+\s+([A-Za-z0-9'\-\.\&\s\/\(\)]+?)\s+(?:\d+\s+)?(\d+:\d+\.\d+)")
ms_re_std = re.compile(r"^\s*(\d+)\s+(?:\d+\s+)?([A-Za-z'\-\.]+)\s+([A-Za-z'\-\.]+(?:\s+[A-Za-z'\-\.]+)?)\s{2,}(\d{1,2}|-)?\s*([A-Za-z0-9'\-\.\&\s\/\(\)]+?)\s+(\d+:\d+\.\d+)")

for fp in sorted(glob.glob(os.path.join(ms_dir, "ms_*.html"))):
    bn = os.path.basename(fp)
    m_id = bn.split("_")[1]
    if m_id not in MS_MEET_INFO: continue
    m_title, m_date, m_state = MS_MEET_INFO[m_id]
    pre = BeautifulSoup(open(fp, encoding="utf-8", errors="ignore").read(), "html.parser").find("pre")
    if not pre: continue
    cur_g, cur_d, cur_div, div_rows = None, None, "", []
    def flush_ms(rows, g, d, dv):
        if not rows or not g or not d: return
        nf = len(rows)
        for pl, fn, ln, yr, tm, t_sec in rows:
            gr_h = int(yr) if (yr and yr.isdigit() and int(yr) <= 8) else None
            ag_h = int(yr) if (yr and yr.isdigit() and int(yr) >= 9 and m_id == "789241") else None
            if yr and yr.isdigit() and 9 <= int(yr) <= 12 and m_id != "789241": gr_h = int(yr)
            for idx in match_athlete(g, fn, ln, grade=gr_h, age=ag_h, state_hint=m_state):
                a = athletes[idx]
                if not a["home_school"] and tm and tm.lower() not in a["team"].lower() and tm.lower() != "unattached":
                    a["home_school"] = tm.strip()
                if gr_h and not a["grade"]: a["grade"] = str(gr_h)
                a["races_2026"].append({
                    "meet": m_title, "date": m_date, "division": dv,
                    "place": pl, "field_size": nf, "dist_m": d,
                    "time_sec": round(t_sec, 2), "time_str": fmt_time(t_sec),
                    "pace_mi": fmt_pace_mi(t_sec, d), "school_team": tm.strip(),
                })

    for line in pre.get_text().splitlines():
        ls = line.strip()
        if not ls: continue
        if not ls[0].isdigit() and any(k in ls.lower() for k in ["meter", "mile", "3200m", "3000m", "2000m", "4000m", "5000m", "5k", "3k", "2k", "4k"]):
            gn, dn = infer_dist_and_gender(ls)
            if gn and dn:
                flush_ms(div_rows, cur_g, cur_d, cur_div)
                div_rows, cur_g, cur_d, cur_div = [], gn, dn, ls[:80]
                continue
        mm = ms_re_meetpro.match(line)
        if mm:
            pl, ln, fn, yr, tm, ts = mm.groups()
            t_sec = parse_time_sec(ts)
            if t_sec: div_rows.append((int(pl), fn.strip(), ln.strip().title(), yr, tm.strip(), t_sec))
            continue
        ms = ms_re_std.match(line)
        if ms:
            pl, fn, ln, yr, tm, ts = ms.groups()
            if fn.lower() not in ("rank", "place", "team", "score"):
                t_sec = parse_time_sec(ts)
                if t_sec: div_rows.append((int(pl), fn.strip(), ln.strip(), yr, tm.strip(), t_sec))
    flush_ms(div_rows, cur_g, cur_d, cur_div)

# --- 4. Ingest PAUSATF 2026 HTML tables (CA: Buffalo Chips / NorCal Distance) ---
for fp in sorted(glob.glob(os.path.join(ms_dir, "pausatf_*.html"))):
    soup = BeautifulSoup(open(fp, encoding="utf-8", errors="ignore").read(), "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else os.path.basename(fp)
    for tr in soup.find_all("tr"):
        tds = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(tds) >= 6 and tds[0].isdigit() and tds[2] in ("M", "F") and tds[3].isdigit():
            pl, nm, sx, ag, t_str = int(tds[0]), tds[1], tds[2], int(tds[3]), tds[-1]
            t_sec = parse_time_sec(t_str) if ":" in t_str else None
            if t_sec and ag <= 18:
                parts = nm.split()
                if len(parts) >= 2:
                    # Estimate distance from time (youth races 2K-5K)
                    dm = 5000 if t_sec > 960 else (3000 if t_sec > 580 else 2000)
                    for idx in match_athlete(sx, parts[0], " ".join(parts[1:]), age=ag, state_hint="CA"):
                        athletes[idx]["races_2026"].append({
                            "meet": title[:55], "date": "2026-10-17", "division": "PAUSATF XC",
                            "place": pl, "field_size": 50, "dist_m": dm,
                            "time_sec": round(t_sec, 2), "time_str": fmt_time(t_sec),
                            "pace_mi": fmt_pace_mi(t_sec, dm), "school_team": "PAUSATF",
                        })

# --- 5. Ingest Historical CCCNYC 2022-2025 + Build Empirical Age Baseline & Club Strength ---
with open(os.path.join(web_dir, "cccnyc_2022_2025_parsed.json"), encoding="utf-8") as f:
    hist_cccnyc = json.load(f)

# Empirical CCCNYC pace (sec per km) by (gender, single_age) AND club residuals!
cccnyc_age_paces = {} # (gender, age) -> list of sec_per_km
cccnyc_club_z = {}    # base_club_prefix -> list of z-scores (negative = faster than age median!)
cccnyc_club_medals = {} # club_prefix -> {"top25": int, "top3_indiv": int, "finishers": int}

for r in hist_cccnyc:
    yr = r["year"]
    g, d = infer_dist_and_gender(r["event"])
    if not g or not d: continue
    t_sec = parse_time_sec(r["time"])
    if not t_sec: continue
    ag_s = re.sub(r"^[MW]", "", r["age"])
    if not ag_s.isdigit(): continue
    ag = int(ag_s)
    spk = t_sec / (d / 1000.0)
    cccnyc_age_paces.setdefault((g, ag), []).append(spk)
    nm = r["name"]
    if "," in nm:
        ln, fn = [x.strip() for x in nm.split(",", 1)]
        exp_age = ag + (2026 - yr)
        for idx in match_athlete(g, fn, ln, age=exp_age):
            a = athletes[idx]
            if abs(a["age"] - exp_age) <= 1:
                a["cccnyc_history"].append({
                    "year": yr, "event": r["event"], "place": r["place"],
                    "age": ag, "club": r["club"], "dist_m": d,
                    "time_sec": round(t_sec, 2), "time_str": r["time"],
                    "pace_mi": fmt_pace_mi(t_sec, d),
                })

# Compute median & std sec/km per (gender, age) at CCCNYC 2022-2025
age_stats = {}
for (g, ag), vals in cccnyc_age_paces.items():
    arr = np.array(vals)
    med = float(np.median(arr))
    iqr_sd = float(np.percentile(arr, 75) - np.percentile(arr, 25)) / 1.349
    age_stats[(g, ag)] = (med, max(iqr_sd, 12.0))

# Fallback interpolation if any (g, ag) is sparse
for g in ("M", "F"):
    for ag in range(4, 19):
        if (g, ag) not in age_stats:
            near = [age_stats[(g, a2)] for a2 in range(4, 19) if (g, a2) in age_stats]
            age_stats[(g, ag)] = near[0] if near else (280.0, 25.0)

# Compute historical club z-scores across 2022-2025 CCCNYC
for r in hist_cccnyc:
    g, d = infer_dist_and_gender(r["event"])
    t_sec = parse_time_sec(r["time"])
    ag_s = re.sub(r"^[MW]", "", r["age"])
    if not g or not d or not t_sec or not ag_s.isdigit(): continue
    ag = int(ag_s)
    med, sd = age_stats[(g, ag)]
    spk = t_sec / (d / 1000.0)
    z = (spk - med) / sd
    club_key = r["club"][:10].lower().strip()
    cccnyc_club_z.setdefault(club_key, []).append(z)
    st_m = cccnyc_club_medals.setdefault(club_key, {"top25": 0, "top3": 0, "finishers": 0})
    st_m["finishers"] += 1
    if r["place"] <= 25: st_m["top25"] += 1
    if r["place"] <= 3: st_m["top3"] += 1

# --- 6. Ingest Curated Verified 2026 Open-Web Marks & MileSplit National Athlete Sweep (v2) ---
curated_fp = os.path.join(base_scratch, "curated_verified_2026.json")
if os.path.exists(curated_fp):
    curated_map = json.load(open(curated_fp, encoding="utf-8"))
    for a in athletes:
        if a["is_duplicate_ghost"]: continue
        if a["display_name"] in curated_map:
            for cm in curated_map[a["display_name"]]:
                a["races_2026"].append({
                    "meet": cm["meet"], "date": cm["date"], "division": cm["division"],
                    "place": cm.get("place"), "field_size": cm.get("field_size", 60),
                    "dist_m": cm["dist_m"], "time_sec": round(float(cm["time_sec"]), 2),
                    "time_str": fmt_time(float(cm["time_sec"])),
                    "pace_mi": fmt_pace_mi(float(cm["time_sec"]), cm["dist_m"]),
                    "school_team": cm.get("school_team"),
                    "surface": "track" if "Track" in cm["meet"] or "Outdoor" in cm["meet"] else "xc",
                })

ms_v2_fp = os.path.join(base_scratch, "ms_athlete_verified_v2.json")
for a in athletes:
    a["prior_season_marks"] = []

if os.path.exists(ms_v2_fp):
    ms_v2 = json.load(open(ms_v2_fp, encoding="utf-8"))
    for a in athletes:
        if a["is_duplicate_ghost"]: continue
        rec = ms_v2.get(a["id"])
        if not rec or not rec.get("marks"): continue
        for m in rec["marks"]:
            dm = int(m["dist_m"])
            if dm < 800: continue # Do not extrapolate pure 100m/200m/400m sprints to XC distance
            t_sec = float(m["time_sec"])
            seas = m.get("season", "cc")
            surf = "xc" if seas == "cc" else "track"
            pid = int(m.get("perf_id") or 0)
            if m.get("year") == 2026:
                if seas == "cc":
                    dt_est = "2026-10-18" if pid >= 220_500_000 else ("2026-09-26" if pid >= 218_500_000 else "2026-09-05")
                elif seas == "outdoor":
                    dt_est = "2026-05-16"
                else:
                    dt_est = "2026-02-14"
                a["races_2026"].append({
                    "meet": m["meet"], "date": dt_est,
                    "division": f"{'XC' if surf == 'xc' else 'Track'} {m['event_code']}",
                    "place": None, "field_size": None, "dist_m": dm,
                    "time_sec": round(t_sec, 2), "time_str": fmt_time(t_sec),
                    "pace_mi": fmt_pace_mi(t_sec, dm), "school_team": None,
                    "surface": surf,
                })
            else:
                a["prior_season_marks"].append({
                    "year": int(m.get("year") or 2025),
                    "meet": m["meet"], "event_code": m["event_code"],
                    "dist_m": dm, "time_sec": round(t_sec, 2),
                    "time_str": fmt_time(t_sec), "pace_mi": fmt_pace_mi(t_sec, dm),
                    "surface": surf,
                })

def clean_school_str(s):
    if not s: return s
    return re.sub(r"\s*\([^)]*$", "", s).strip()

# Deduplicate races_2026 & sort
for a in athletes:
    if a.get("home_school"):
        a["home_school"] = clean_school_str(a["home_school"])
    seen = set()
    dedup = []
    # Prefer entries with actual place/field_size from raw meet scrapes when deduplicating same time!
    for rc in sorted(a["races_2026"], key=lambda x: (x["date"], 0 if x.get("place") else 1)):
        k = (round(rc["time_sec"], 1), rc["dist_m"])
        if k not in seen:
            seen.add(k)
            dedup.append(rc)
    a["races_2026"] = sorted(dedup, key=lambda x: x["date"])
    a["cccnyc_history"] = sorted(a["cccnyc_history"], key=lambda x: -x["year"])

dop_check = [a for a in athletes if a["is_dop"]]
print(f"DoP 2026 matched: {sum(1 for a in dop_check if a['races_2026'])}/{len(dop_check)}!")
unique_all = [a for a in athletes if not a["is_duplicate_ghost"]]
print(f"Total unique entrants with empirical individual seed: {sum(1 for a in unique_all if a['races_2026'] or a['cccnyc_history'] or a['prior_season_marks'])}/{len(unique_all)}")

# ==============================================================================
# STEP 2: PROJECTION ENGINE (Cedarville Target-Distance Equivalent Time mu, sigma)
# ==============================================================================
# Riegel youth exponent: 1.07
# Also adjust for Cedarville Elvin R. King fast NCAA championship grass surface (-1.2% vs hilly park XC like Youthtowne/North Park!)
COURSE_FACTOR = {
    "Pittsburgh Diocesan XC Championship": 0.978, # Youthtowne/North Park rolling hills -> Cedarville fast grass
    "North Area XC Championships": 0.982,
    "Ohio Elementary & MS State Championship": 1.005, # Dublin Jerome very fast flat track/grass finish
    "NXR Midwest MS & Community Race": 0.995, # LaVern Gibson championship grass
    "KTCCCA KY Elem & MS State Championship": 0.992, # KY Horse Park
}

def project_from_2026(a, target_dist_m):
    ests = []
    weights = []
    has_xc = any(rc.get("surface", "xc") != "track" for rc in a["races_2026"])
    for rc in a["races_2026"]:
        dm = rc["dist_m"]
        t = rc["time_sec"]
        surf = rc.get("surface", "xc")
        # Convert distance via Youth Riegel (1.095 for 800m, 1.080 for 1500m/1600m track, 1.07 for XC)
        exp_r = 1.095 if dm <= 800 else (1.080 if (surf == "track" and dm <= 1650) else 1.07)
        conv = t * ((target_dist_m / dm) ** exp_r)
        if surf == "track":
            # Rubber track -> grass XC surface conversion (+5.2%, or +7.5% from 800m mid-distance)
            cf = 1.075 if dm <= 800 else 1.052
        else:
            cf = 0.992
            for k, v in COURSE_FACTOR.items():
                if k.lower() in rc["meet"].lower():
                    cf = v; break
        conv *= cf
        # Weight recent & championship & closer-distance XC races higher
        dist_ratio = min(dm, target_dist_m) / max(dm, target_dist_m)
        w = (0.45 + 0.55 * dist_ratio)
        if surf == "track":
            w *= (0.28 if has_xc else 0.75)
        if "championship" in rc["meet"].lower() or "state" in rc["meet"].lower() or "nxr" in rc["meet"].lower() or "qualifier" in rc["meet"].lower():
            w *= 1.6
        if rc["date"] >= "2026-10-01":
            w *= 1.35
        ests.append(conv)
        weights.append(w)
    ests = np.array(ests)
    weights = np.array(weights)
    # Blend weighted mean (62%) and best normalized XC performance (38%) to reflect championship peaking
    w_mean = float(np.sum(ests * weights) / np.sum(weights))
    xc_ests = [ests[i] for i, rc in enumerate(a["races_2026"]) if rc.get("surface", "xc") != "track"]
    best_t = float(np.min(xc_ests)) if xc_ests else float(np.min(ests))
    mu = 0.62 * w_mean + 0.38 * best_t
    # Individual consistency from multi-race CV if >=3 races
    if len(ests) >= 3:
        emp_sd = float(np.std(ests))
        rel_sd = np.clip(emp_sd / mu, 0.024, 0.048)
    elif len(ests) == 2:
        rel_sd = 0.034 if has_xc else 0.044
    else:
        rel_sd = 0.038 if has_xc else 0.048
    return mu, mu * rel_sd

def project_from_prior_marks(a, target_dist_m):
    ests, weights = [], []
    g = a["gender"]
    med_now, _ = age_stats[(g, min(max(a["age"], 6), 18))]
    for m in a["prior_season_marks"]:
        yr = m["year"]
        yr_gap = max(1, 2026 - yr)
        hist_age = max(6, a["age"] - yr_gap)
        med_then, _ = age_stats[(g, min(hist_age, 18))]
        dm = m["dist_m"]
        exp_r = 1.085 if dm <= 800 else 1.07
        conv_then = m["time_sec"] * ((target_dist_m / dm) ** exp_r)
        if m.get("surface") == "track":
            conv_then *= (1.070 if dm <= 800 else 1.044)
        spk_then = conv_then / (target_dist_m / 1000.0)
        ratio = spk_then / med_then
        damped_ratio = 1.0 + 0.85 * (ratio - 1.0)
        est_t = (med_now * damped_ratio) * (target_dist_m / 1000.0) * 0.995
        w = (1.0 / (yr_gap ** 1.1)) * (1.0 if m.get("surface") == "xc" else 0.65)
        ests.append(est_t); weights.append(w)
    mu = float(np.sum(np.array(ests) * np.array(weights)) / np.sum(weights))
    return mu, mu * 0.046

def project_from_cccnyc_vet(a, target_dist_m):
    # Project using empirical age_stats ratio from historical age -> 2026 age!
    ests, weights = [], []
    g = a["gender"]
    med_now, _ = age_stats[(g, min(max(a["age"], 6), 18))]
    for h in a["cccnyc_history"]:
        med_then, _ = age_stats[(g, min(max(h["age"], 6), 18))]
        spk_then = h["time_sec"] / (h["dist_m"] / 1000.0)
        # Age-maturation ratio with 0.85 regression-to-mean damping
        ratio = spk_then / med_then
        damped_ratio = 1.0 + 0.86 * (ratio - 1.0)
        spk_proj_base = med_now * damped_ratio
        # Adjust distance from historical CCCNYC standard dist for that age to target_dist_m
        # Note med_now is already at target_dist_m's age group in CCCNYC!
        est_t = spk_proj_base * (target_dist_m / 1000.0) * 0.994 # Cedarville slightly faster than Victor Ashe / Tom Sawyer
        yr_gap = 2026 - h["year"]
        w = 1.0 / (yr_gap ** 1.1)
        ests.append(est_t); weights.append(w)
    mu = float(np.sum(np.array(ests) * np.array(weights)) / np.sum(weights))
    return mu, mu * 0.043

# First pass: compute empirical seeds for Tier 1 & Tier 2
for a in athletes:
    if a["is_duplicate_ghost"]: continue
    td = EVENT_META[a["event_num"]]["dist_m"]
    mu_26, sd_26 = (project_from_2026(a, td) if a["races_2026"] else (None, None))
    mu_vet, sd_vet = (project_from_cccnyc_vet(a, td) if a["cccnyc_history"] else (None, None))
    mu_prior, sd_prior = (project_from_prior_marks(a, td) if (not mu_26 and a.get("prior_season_marks")) else (None, None))
    if mu_26 and mu_vet:
        # Inverse-variance precision blend of 2026 form + CCCNYC Nationals pedigree!
        p1, p2 = 1.0 / (sd_26**2), 0.55 / (sd_vet**2)
        mu = (mu_26 * p1 + mu_vet * p2) / (p1 + p2)
        sd = math.sqrt(1.0 / (p1 + p2))
        tier = "Tier 1+ (2026 + CCCNYC Vet)"
    elif mu_26:
        mu, sd = mu_26, sd_26
        tier = "Tier 1 (2026 Empirical)"
    elif mu_vet and mu_prior:
        p1, p2 = 1.0 / (sd_vet**2), 0.85 / (sd_prior**2)
        mu = (mu_vet * p1 + mu_prior * p2) / (p1 + p2)
        sd = math.sqrt(1.0 / (p1 + p2))
        tier = "Tier 2 (CCCNYC Veteran)"
    elif mu_vet:
        mu, sd = mu_vet, sd_vet
        tier = "Tier 2 (CCCNYC Veteran)"
    elif mu_prior:
        mu, sd = mu_prior, sd_prior
        tier = "Tier 2M (Prior Season Empirical)"
    else:
        mu, sd, tier = None, None, "Tier 3 (Club × Age Prior)"
    a["proj_mu"] = mu
    a["proj_sd"] = sd
    a["seed_tier"] = tier

# Compute 2026 seeded teammate z-scores per team to inform Tier 3 Hierarchical Shrinkage Prior!
team_2026_z = {}
for a in athletes:
    if a["is_duplicate_ghost"] or a["proj_mu"] is None: continue
    td = EVENT_META[a["event_num"]]["dist_m"]
    med, sd_age = age_stats[(a["gender"], min(max(a["age"], 6), 18))]
    spk = a["proj_mu"] / (td / 1000.0)
    z = (spk - med) / sd_age
    team_2026_z.setdefault(a["team"], []).append(z)
    team_2026_z.setdefault(a["base_org"], []).append(z)

# Second pass: assign Hierarchical Club × Age Prior for Tier 3 athletes
for a in athletes:
    if a["is_duplicate_ghost"]:
        a["proj_mu"], a["proj_sd"], a["seed_tier"] = None, None, "Duplicate Ghost"
        continue
    if a["proj_mu"] is not None: continue
    td = EVENT_META[a["event_num"]]["dist_m"]
    med, sd_age = age_stats[(a["gender"], min(max(a["age"], 6), 18))]
    # Combine historical CCCNYC club z + 2026 club z with Empirical Bayes shrinkage!
    ckey = a["base_org"][:10].lower().strip()
    hz_list = cccnyc_club_z.get(ckey, [])
    tz_list = team_2026_z.get(a["team"], team_2026_z.get(a["base_org"], []))
    z_prior = -0.10 # Nationals qualifiers average slightly faster than median all-comers
    if hz_list and tz_list:
        nh, nt = len(hz_list), len(tz_list)
        zh = float(np.median(hz_list))
        zt = float(np.median(tz_list))
        z_prior = (nh * zh + 2.5 * nt * zt) / (nh + 2.5 * nt + 6.0)
    elif hz_list:
        nh = len(hz_list)
        z_prior = (nh * float(np.median(hz_list))) / (nh + 8.0)
    elif tz_list:
        nt = len(tz_list)
        z_prior = (2.0 * nt * float(np.median(tz_list))) / (2.0 * nt + 6.0)
    # B-squad offset (+0.48 SD slower than A-squad)
    if is_b_squad(a["team"]):
        z_prior += 0.48
    # Slight intra-roster spread so unseeded teammates aren't identical clones (use deterministic tiny spread around prior, real variance handled in MC!)
    spk_est = med + z_prior * sd_age
    mu = spk_est * (td / 1000.0) * 0.995
    a["proj_mu"] = mu
    a["proj_sd"] = mu * 0.062

# ==============================================================================
# STEP 3: 10,000-TRIAL MONTE CARLO SIMULATION ACROSS ALL 11 EVENTS
# ==============================================================================
N_SIMS = 10000
events_output = []
teams_output = []

for ev_num in sorted(EVENT_META.keys()):
    meta = EVENT_META[ev_num]
    ev_aths = [a for a in athletes if a["event_num"] == ev_num and not a["is_duplicate_ghost"]]
    n_ath = len(ev_aths)
    td = meta["dist_m"]

    mus = np.array([a["proj_mu"] for a in ev_aths])
    sds = np.array([a["proj_sd"] for a in ev_aths])

    # Shared team-day shock (1.1% SD) + individual race-day performance (slight right-skew XC distribution)
    unique_teams = sorted(set(a["team"] for a in ev_aths))
    team_idx_map = {t: i for i, t in enumerate(unique_teams)}
    ath_t_idx = np.array([team_idx_map[a["team"]] for a in ev_aths])

    team_shocks = np.random.normal(0.0, 0.011, size=(N_SIMS, len(unique_teams)))
    # Unattached runners don't share a team shock!
    if "Unattached" in team_idx_map:
        team_shocks[:, team_idx_map["Unattached"]] = 0.0

    # Individual shocks: mixture of Normal + slight Gumbel right-tail (models stitch/fatigue risk vs breakthrough)
    z_norm = np.random.normal(0.0, 0.85, size=(N_SIMS, n_ath))
    z_skew = (np.random.gumbel(0.0, 0.42, size=(N_SIMS, n_ath)) - 0.42 * 0.5772)
    z_tot = z_norm + z_skew # mean ~0, var ~ 0.85^2 + (pi^2/6)*0.42^2 = 0.7225 + 0.290 = 1.01

    sim_times = mus[None, :] * (1.0 + team_shocks[:, ath_t_idx]) + sds[None, :] * z_tot
    sim_times = np.maximum(sim_times, mus[None, :] * 0.82) # physiological floor

    # Overall ranks per trial (1..n_ath)
    order = np.argsort(sim_times, axis=1)
    ranks = np.empty_like(order)
    rows_grid = np.arange(N_SIMS)[:, None]
    ranks[rows_grid, order] = np.arange(1, n_ath + 1)[None, :]

    # Single-year Award Group ranks per trial! (Top 25 per single age!)
    awd_groups = sorted(set(a["award_group"] for a in ev_aths))
    awd_top25_prob = np.zeros(n_ath)
    awd_top3_prob = np.zeros(n_ath)
    awd_win_prob = np.zeros(n_ath)
    awd_exp_rank = np.zeros(n_ath)
    awd_group_sizes = {}
    for ag in awd_groups:
        mask = np.array([i for i, a in enumerate(ev_aths) if a["award_group"] == ag])
        awd_group_sizes[ag] = int(len(mask))
        sub_t = sim_times[:, mask]
        sub_ord = np.argsort(sub_t, axis=1)
        sub_rk = np.empty_like(sub_ord)
        sub_rk[np.arange(N_SIMS)[:, None], sub_ord] = np.arange(1, len(mask) + 1)[None, :]
        awd_top25_prob[mask] = np.mean(sub_rk <= 25, axis=0)
        awd_top3_prob[mask] = np.mean(sub_rk <= 3, axis=0)
        awd_win_prob[mask] = np.mean(sub_rk == 1, axis=0)
        awd_exp_rank[mask] = np.mean(sub_rk, axis=0)

    # CYO Individual ranks per trial
    cyo_mask = np.array([i for i, a in enumerate(ev_aths) if a["is_cyo"]])
    cyo_indiv_win = np.zeros(n_ath)
    cyo_indiv_top10 = np.zeros(n_ath)
    cyo_exp_rank = np.zeros(n_ath)
    if len(cyo_mask) > 0:
        sub_c = sim_times[:, cyo_mask]
        c_ord = np.argsort(sub_c, axis=1)
        c_rk = np.empty_like(c_ord)
        c_rk[np.arange(N_SIMS)[:, None], c_ord] = np.arange(1, len(cyo_mask) + 1)[None, :]
        cyo_indiv_win[cyo_mask] = np.mean(c_rk == 1, axis=0)
        cyo_indiv_top10[cyo_mask] = np.mean(c_rk <= 10, axis=0)
        cyo_exp_rank[cyo_mask] = np.mean(c_rk, axis=0)

    # Projected S-curve passing leverage: places gained if 15 seconds faster (or 10s for 2K/1K)
    delta_s = 10.0 if td <= 2000 else 15.0
    sorted_mus = np.sort(mus)

    for i, a in enumerate(ev_aths):
        a["proj_time_sec"] = round(float(mus[i]), 2)
        a["proj_time_str"] = fmt_time(float(mus[i]), tenths=True)
        a["proj_pace_mi"] = fmt_pace_mi(float(mus[i]), td)
        a["p10_time_sec"] = round(float(np.percentile(sim_times[:, i], 10)), 2)
        a["p90_time_sec"] = round(float(np.percentile(sim_times[:, i], 90)), 2)
        a["p10_time_str"] = fmt_time(a["p10_time_sec"], tenths=True)
        a["p90_time_str"] = fmt_time(a["p90_time_sec"], tenths=True)
        a["exp_place"] = round(float(np.mean(ranks[:, i])), 1)
        a["med_place"] = int(np.median(ranks[:, i]))
        a["p10_place"] = int(np.percentile(ranks[:, i], 10))
        a["p90_place"] = int(np.percentile(ranks[:, i], 90))
        a["win_prob"] = round(float(np.mean(ranks[:, i] == 1)) * 100, 1)
        a["podium_prob"] = round(float(np.mean(ranks[:, i] <= 3)) * 100, 1)
        a["top10_prob"] = round(float(np.mean(ranks[:, i] <= 10)) * 100, 1)
        a["top25_prob"] = round(float(np.mean(ranks[:, i] <= 25)) * 100, 1)
        a["aa_age_prob"] = round(float(awd_top25_prob[i]) * 100, 1)
        a["aa_age_podium_prob"] = round(float(awd_top3_prob[i]) * 100, 1)
        a["aa_age_win_prob"] = round(float(awd_win_prob[i]) * 100, 1)
        a["aa_age_exp_rank"] = round(float(awd_exp_rank[i]), 1)
        a["aa_age_field_size"] = awd_group_sizes[a["award_group"]]
        a["cyo_win_prob"] = round(float(cyo_indiv_win[i]) * 100, 1)
        a["cyo_top10_prob"] = round(float(cyo_indiv_top10[i]) * 100, 1)
        a["cyo_exp_rank"] = round(float(cyo_exp_rank[i]), 1) if a["is_cyo"] else None
        # Passing leverage
        cur_rk = int(np.searchsorted(sorted_mus, mus[i], side="left")) + 1
        faster_rk = int(np.searchsorted(sorted_mus, mus[i] - delta_s, side="left")) + 1
        a["leverage_gain"] = max(0, cur_rk - faster_rk)
        a["leverage_sec"] = int(delta_s)

    # --- OFFICIAL XC TEAM SCORING SIMULATION (Rule B: >=5 runners on same team, non-team runners displaced!) ---
    def simulate_xc_teams(eligible_teams_list):
        if len(eligible_teams_list) == 0:
            return {}, []
        el_set = set(eligible_teams_list)
        el_ath_mask = np.array([i for i, a in enumerate(ev_aths) if a["team"] in el_set])
        el_ath_teams = [ev_aths[i]["team"] for i in el_ath_mask]
        t_to_k = {t: k for k, t in enumerate(eligible_teams_list)}
        ath_k = np.array([t_to_k[t] for t in el_ath_teams])
        K = len(eligible_teams_list)

        sub_times = sim_times[:, el_ath_mask]
        sub_ord = np.argsort(sub_times, axis=1)
        # Team points = 1..M within eligible team runners!
        pts_mat = np.empty_like(sub_ord)
        pts_mat[np.arange(N_SIMS)[:, None], sub_ord] = np.arange(1, len(el_ath_mask) + 1)[None, :]

        scores = np.zeros((N_SIMS, K), dtype=np.int32)
        sixth_pts = np.full((N_SIMS, K), 99999, dtype=np.int32)
        top5_avg = np.zeros((N_SIMS, K), dtype=np.float64)
        spread_1_5 = np.zeros((N_SIMS, K), dtype=np.float64)

        for k, tname in enumerate(eligible_teams_list):
            t_cols = np.where(ath_k == k)[0]
            t_pts = np.sort(pts_mat[:, t_cols], axis=1)
            t_tms = np.sort(sub_times[:, t_cols], axis=1)
            scores[:, k] = np.sum(t_pts[:, :5], axis=1)
            if len(t_cols) >= 6:
                sixth_pts[:, k] = t_pts[:, 5]
            top5_avg[:, k] = np.mean(t_tms[:, :5], axis=1)
            spread_1_5[:, k] = t_tms[:, 4] - t_tms[:, 0]

        # Rank teams with 6th-runner tiebreaker! (composite key: score * 100000 + sixth_pts)
        comp = scores.astype(np.int64) * 100000 + sixth_pts.astype(np.int64)
        t_ord = np.argsort(comp, axis=1)
        t_ranks = np.empty_like(t_ord)
        t_ranks[np.arange(N_SIMS)[:, None], t_ord] = np.arange(1, K + 1)[None, :]
        ties_broken_by_6th = float(np.mean(
            np.any(np.diff(np.sort(scores, axis=1), axis=1) == 0, axis=1)
        )) * 100

        res = {}
        for k, tname in enumerate(eligible_teams_list):
            res[tname] = {
                "exp_score": round(float(np.mean(scores[:, k])), 1),
                "med_score": int(np.median(scores[:, k])),
                "p10_score": int(np.percentile(scores[:, k], 10)),
                "p90_score": int(np.percentile(scores[:, k], 90)),
                "exp_rank": round(float(np.mean(t_ranks[:, k])), 2),
                "win_prob": round(float(np.mean(t_ranks[:, k] == 1)) * 100, 1),
                "podium_prob": round(float(np.mean(t_ranks[:, k] <= 3)) * 100, 1),
                "top5_prob": round(float(np.mean(t_ranks[:, k] <= 5)) * 100, 1),
                "top5_avg_sec": round(float(np.mean(top5_avg[:, k])), 2),
                "top5_avg_str": fmt_time(float(np.mean(top5_avg[:, k])), tenths=True),
                "spread_1_5_sec": round(float(np.mean(spread_1_5[:, k])), 1),
                "tiebreak_rate_race": round(ties_broken_by_6th, 1),
            }
        # Top-8 Head-to-Head Win Matrix
        top_k_idx = sorted(range(K), key=lambda k: np.mean(t_ranks[:, k]))[:8]
        h2h = []
        for ka in top_k_idx:
            row_h = {"team": eligible_teams_list[ka], "vs": {}}
            for kb in top_k_idx:
                if ka == kb: row_h["vs"][eligible_teams_list[kb]] = None
                else:
                    row_h["vs"][eligible_teams_list[kb]] = round(float(np.mean(comp[:, ka] < comp[:, kb])) * 100, 1)
            h2h.append(row_h)
        return res, h2h

    scoring_teams = sorted([t for t in unique_teams if t != "Unattached" and sum(1 for a in ev_aths if a["team"] == t) >= 5])
    cyo_scoring_teams = [t for t in scoring_teams if is_cyo_team(t)]

    nat_res, nat_h2h = simulate_xc_teams(scoring_teams)
    cyo_res, cyo_h2h = simulate_xc_teams(cyo_scoring_teams)

    # Record every team in this event (including incomplete <5 teams so coaches see incomplete status!)
    for tname in unique_teams:
        if tname == "Unattached": continue
        t_aths = sorted([a for a in ev_aths if a["team"] == tname], key=lambda x: x["proj_time_sec"])
        st, cat, reg = CLUB_GEO.get(tname, ("USA", "Youth Club", ""))
        nr = nat_res.get(tname)
        cr = cyo_res.get(tname)
        teams_output.append({
            "event_num": ev_num,
            "event_name": meta["name"],
            "event_short": meta["short"],
            "gender": meta["gender"],
            "dist_m": td,
            "team": tname,
            "base_org": get_base_org(tname),
            "state": st,
            "category": cat,
            "region": reg,
            "is_cyo": is_cyo_team(tname),
            "is_dop": "Diocese of Pittsburgh" in tname,
            "roster_count": len(t_aths),
            "scores_official_team": len(t_aths) >= 5,
            "seeded_count": sum(1 for a in t_aths if "Tier 3" not in a["seed_tier"]),
            "nat": nr,
            "cyo": cr,
            "runner_ids": [a["id"] for a in t_aths],
            "top5_names": [a["display_name"] for a in t_aths[:5]],
        })

    events_output.append({
        **meta,
        "total_entries_raw": sum(1 for a in athletes if a["event_num"] == ev_num),
        "unique_runners": n_ath,
        "scoring_teams_count": len(scoring_teams),
        "cyo_scoring_teams_count": len(cyo_scoring_teams),
        "dop_entries_count": sum(1 for a in ev_aths if a["is_dop"]),
        "award_group_sizes": awd_group_sizes,
        "h2h_national": nat_h2h,
        "h2h_cyo": cyo_h2h,
    })

# Print quick verification of Event standings & Diocese of Pittsburgh projections!
print("\n=== NATIONAL & CYO TEAM PROJECTIONS SUMMARY ===")
for ev in events_output:
    ev_t = [t for t in teams_output if t["event_num"] == ev["num"] and t["scores_official_team"]]
    ev_t.sort(key=lambda x: x["nat"]["exp_rank"])
    top3 = ", ".join(f"{t['team']} ({t['nat']['exp_score']} pts, {t['nat']['win_prob']}%W)" for t in ev_t[:3])
    dop_t = [t for t in teams_output if t["event_num"] == ev["num"] and t["is_dop"]]
    dop_str = "; ".join(
        f"{t['team']}: Nat #{t['nat']['exp_rank']} ({t['nat']['podium_prob']}% pod) / CYO #{t['cyo']['exp_rank']} ({t['cyo']['win_prob']}% CYO Win)"
        if t["scores_official_team"] else f"{t['team']}: {t['roster_count']} runners (Incomplete <5)"
        for t in dop_t
    )
    print(f"Ev {ev['num']:2d} {ev['short']:12s} | {ev['unique_runners']:3d} r / {ev['scoring_teams_count']:2d} t | Top 3: {top3}")
    if dop_str: print(f"      -> DoP: {dop_str}")

# Check Marcela Victor & top DoP All-American contenders!
print("\n=== SAMPLE DIOCESE OF PITTSBURGH RUNNER PROJECTIONS ===")
for a in sorted([x for x in athletes if x["is_dop"]], key=lambda x: -x["aa_age_prob"])[:15]:
    print(f"  {a['display_name']:22s} ({a['team']}, Age {a['age']}, {a['home_school']}) | Ev {a['event_num']} | Proj {a['proj_time_str']} | Ov #{a['exp_place']} | Age-{a['award_group']} AA Top-25: {a['aa_age_prob']}% (Age Rk #{a['aa_age_exp_rank']})")

for a in [x for x in athletes if "Victor" in x["last_name"]]:
    print("  FOCUS CHECK:", a["display_name"], a["team"], "School:", a["home_school"], "2026 races:", len(a["races_2026"]), "Proj:", a["proj_time_str"], "Age-9 AA%:", a["aa_age_prob"], "Age Rk:", a["aa_age_exp_rank"])

# Build Historical CCCNYC Champions & Course Records Summary for Venue/Meet tab
hist_venue_summary = [
    {"year": 2025, "venue": "Victor Ashe Park (Knoxville, TN)", "finishers": 3389, "returning_2026": sum(1 for a in unique_all if any(h["year"]==2025 for h in a["cccnyc_history"]))},
    {"year": 2024, "venue": "Masterson Station Park (Lexington, KY)", "finishers": 3616, "returning_2026": sum(1 for a in unique_all if any(h["year"]==2024 for h in a["cccnyc_history"]))},
    {"year": 2023, "venue": "E.P. 'Tom' Sawyer State Park (Louisville, KY)", "finishers": 3438, "returning_2026": sum(1 for a in unique_all if any(h["year"]==2023 for h in a["cccnyc_history"]))},
    {"year": 2022, "venue": "Blue River XC Course (Shelbyville, IN)", "finishers": 3097, "returning_2026": sum(1 for a in unique_all if any(h["year"]==2022 for h in a["cccnyc_history"]))},
]

# Club aggregate rollup across all 11 events
clubs_rollup = {}
for a in athletes:
    if a["is_duplicate_ghost"]: continue
    bo = a["base_org"]
    c = clubs_rollup.setdefault(bo, {
        "org": bo,
        "state": a["club_state"],
        "category": a["club_category"],
        "region": a["club_region"],
        "is_cyo": a["is_cyo"],
        "is_dop": a["is_dop"],
        "runners_count": 0,
        "events_entered": set(),
        "scoring_squads": 0,
        "seeded_runners": 0,
        "cccnyc_vets": 0,
        "exp_national_titles": 0.0,
        "exp_national_podiums": 0.0,
        "exp_age_all_americans": 0.0,
        "feeder_schools": {},
    })
    c["runners_count"] += 1
    c["events_entered"].add(a["event_num"])
    if "Tier 3" not in a["seed_tier"]: c["seeded_runners"] += 1
    if a["cccnyc_history"]: c["cccnyc_vets"] += 1
    c["exp_age_all_americans"] += a["aa_age_prob"] / 100.0
    if a["home_school"]:
        c["feeder_schools"][a["home_school"]] = c["feeder_schools"].get(a["home_school"], 0) + 1

for t in teams_output:
    if not t["scores_official_team"]: continue
    c = clubs_rollup[t["base_org"]]
    c["scoring_squads"] += 1
    c["exp_national_titles"] += t["nat"]["win_prob"] / 100.0
    c["exp_national_podiums"] += t["nat"]["podium_prob"] / 100.0

clubs_list = []
for bo, c in clubs_rollup.items():
    c["events_entered"] = sorted(list(c["events_entered"]))
    c["exp_national_titles"] = round(c["exp_national_titles"], 2)
    c["exp_national_podiums"] = round(c["exp_national_podiums"], 2)
    c["exp_age_all_americans"] = round(c["exp_age_all_americans"], 1)
    ck = bo[:10].lower().strip()
    hm = cccnyc_club_medals.get(ck, {"top25": 0, "top3": 0, "finishers": 0})
    c["hist_2022_2025_finishers"] = hm["finishers"]
    c["hist_2022_2025_top25"] = hm["top25"]
    c["hist_2022_2025_top3"] = hm["top3"]
    clubs_list.append(c)

clubs_list.sort(key=lambda x: (-x["runners_count"], x["org"]))

# Export master dataset JSON + JS bundle + CSVs!
master_payload = {
    "meta": {
        "meet_name": "2026 Cross Country Coaches National Youth Championships (20th Edition) & CYO Nationals",
        "meet_date": "2026-11-21",
        "venue": "Elvin R. King Cross Country Course · Cedarville University",
        "location": "Cedarville, Ohio (251 N. Main St.)",
        "simulations": N_SIMS,
        "generated_at": "2026-11-15",
        "raw_pdf_entries": len(athletes),
        "drive_pdf_entries": len(drive_raw),
        "unique_runners": len(unique_all),
        "ghost_duplicates": sum(1 for a in athletes if a["is_duplicate_ghost"]),
        "web_late_additions": sum(1 for a in athletes if not a["in_drive_pdf"]),
        "seeded_individual_count": sum(1 for a in unique_all if "Tier 3" not in a["seed_tier"]),
        "verified_2026_runners": sum(1 for a in unique_all if a["races_2026"]),
        "cccnyc_veterans": sum(1 for a in unique_all if a["cccnyc_history"]),
        "dop_runners": len(dop_check),
        "dop_feeder_schools": len(set(a["home_school"] for a in dop_check if a["home_school"])),
        "clubs_count": len([c for c in clubs_list if c["org"] != "Unattached"]),
        "states_represented": sorted(list(set(c["state"] for c in clubs_list if c["state"] not in ("USA", "INTL")))),
        "hist_editions": hist_venue_summary,
    },
    "events": events_output,
    "teams": teams_output,
    "clubs": clubs_list,
    "athletes": athletes,
}

with open(os.path.join(data_out_dir, "cccnyc_2026_master.json"), "w", encoding="utf-8") as f:
    json.dump(master_payload, f)

with open(os.path.join(data_out_dir, "data.js"), "w", encoding="utf-8") as f:
    f.write("window.CCCNYC_DATA = ")
    json.dump(master_payload, f, separators=(",", ":"))
    f.write(";\n")

# Export CSVs for downloads
with open(os.path.join(data_out_dir, "cccnyc_2026_runner_predictions.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["ID", "Event_Num", "Event", "Name", "Age", "Gender", "Award_Group", "Team", "State", "Category", "Home_School", "Grade", "Seed_Tier", "Races_2026", "CCCNYC_Prior_Years", "Proj_Time", "P10_Time", "P90_Time", "Proj_Pace_Mi", "Exp_Overall_Place", "Win_Pct", "Podium_Pct", "Overall_Top25_Pct", "Single_Age_AllAmerican_Top25_Pct", "Single_Age_Exp_Rank", "CYO_Exp_Rank", "Anomaly_Note"])
    for a in athletes:
        ev_n = EVENT_META[a["event_num"]]["name"]
        w.writerow([
            a["id"], a["event_num"], ev_n, a["display_name"], a["age"], a["gender"], a["award_group"],
            a["team"], a["club_state"], a["club_category"], a["home_school"] or "", a["grade"] or "",
            a["seed_tier"], len(a["races_2026"]), len(a["cccnyc_history"]),
            a.get("proj_time_str", ""), a.get("p10_time_str", ""), a.get("p90_time_str", ""), a.get("proj_pace_mi", ""),
            a.get("exp_place", ""), a.get("win_prob", ""), a.get("podium_prob", ""), a.get("top25_prob", ""),
            a.get("aa_age_prob", ""), a.get("aa_age_exp_rank", ""), a.get("cyo_exp_rank") or "", a["anomaly_note"] or ""
        ])

with open(os.path.join(data_out_dir, "cccnyc_2026_team_predictions.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Event_Num", "Event", "Team", "State", "Category", "Roster_Count", "Official_Scoring_5Plus", "Seeded_Runners", "Nat_Exp_Rank", "Nat_Exp_Score", "Nat_P10_Score", "Nat_P90_Score", "Nat_Win_Pct", "Nat_Podium_Pct", "Top5_Avg_Time", "Pack_1_5_Spread_Sec", "CYO_Exp_Rank", "CYO_Exp_Score", "CYO_Win_Pct", "CYO_Podium_Pct"])
    for t in teams_output:
        nr, cr = t["nat"] or {}, t["cyo"] or {}
        w.writerow([
            t["event_num"], t["event_name"], t["team"], t["state"], t["category"], t["roster_count"], t["scores_official_team"], t["seeded_count"],
            nr.get("exp_rank", ""), nr.get("exp_score", ""), nr.get("p10_score", ""), nr.get("p90_score", ""), nr.get("win_prob", ""), nr.get("podium_prob", ""),
            nr.get("top5_avg_str", ""), nr.get("spread_1_5_sec", ""),
            cr.get("exp_rank", ""), cr.get("exp_score", ""), cr.get("win_prob", ""), cr.get("podium_prob", "")
        ])

# Copy PDFs into nationals/data/pdfs for direct viewing/download!
pdf_dir = os.path.join(data_out_dir, "pdfs")
os.makedirs(pdf_dir, exist_ok=True)
import shutil
shutil.copyfile(os.path.join(base_scratch, "Entry_List__CYO.pdf"), os.path.join(pdf_dir, "Entry_List__CYO.pdf"))
shutil.copyfile(os.path.join(web_dir, "Entry_List_Web.pdf"), os.path.join(pdf_dir, "Entry_List_Saturday_10PM.pdf"))

print(f"\nExported data.js ({os.path.getsize(os.path.join(data_out_dir, 'data.js'))/1024:.1f} KB) and CSVs/PDFs to {data_out_dir}!")
