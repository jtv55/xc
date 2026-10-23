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
        "short_name": "Seelos #1 (Aug 25)",
        "date": "2026-08-25",
        "location": "Pine Community Park, Wexford, PA",
        "program": "Youth / Diocesan (K-8)",
        "host": "Blessed Francis Seelos Academy"
    },
    "RES082926": {
        "meet_id": "2026-08-29-bta",
        "meet_name": "Blessed Trinity (BTA) XC Invitational",
        "short_name": "BTA Invite (Aug 29)",
        "date": "2026-08-29",
        "location": "Hartwood Acres, Glenshaw, PA",
        "program": "Youth / Diocesan (K-8)",
        "host": "Blessed Trinity Academy"
    },
    "RES090426": {
        "meet_id": "2026-09-04-st-kilian",
        "meet_name": "St. Kilian XC Invitational",
        "short_name": "St. Kilian (Sep 4)",
        "date": "2026-09-04",
        "location": "Mars, PA",
        "program": "Youth / Diocesan (K-8)",
        "host": "St. Kilian Parish School"
    },
    "RES090926": {
        "meet_id": "2026-09-10-harvest-home",
        "meet_name": "St. Al Twilight Harvest Home 5K & 1M",
        "short_name": "Harvest Home (Sep 10)",
        "date": "2026-09-10",
        "location": "Allison Park, PA",
        "program": "Community Race",
        "host": "St. Aloysius / Harvest Home"
    },
    "RES091826": {
        "meet_id": "2026-09-18-youthtowne",
        "meet_name": "Youthtowne Clash XC Invitational",
        "short_name": "Youthtowne Clash (Sep 18)",
        "date": "2026-09-18",
        "location": "Youthtowne, Clinton, PA",
        "program": "Both (HS & Youth)",
        "host": "Youthtowne"
    },
    "RES092426": {
        "meet_id": "2026-09-24-aquinas",
        "meet_name": "Aquinas & Holy Cross Home XC Meet",
        "short_name": "Aquinas Home Meet (Sep 24)",
        "date": "2026-09-24",
        "location": "Allison Park, PA",
        "program": "Youth / Diocesan (K-8)",
        "host": "Aquinas Academy & Holy Cross"
    },
    "RES092926": {
        "meet_id": "2026-09-29-avonworth",
        "meet_name": "Avonworth WPIAL Tri-Meet",
        "short_name": "Avonworth Tri-Meet (Sep 29)",
        "date": "2026-09-29",
        "location": "Sewickley, PA",
        "program": "High School (9-12)",
        "host": "Avonworth High School"
    },
    "RES100226": {
        "meet_id": "2026-10-02-north-area",
        "meet_name": "North Area Diocesan XC Championships",
        "short_name": "North Area Champs (Oct 2)",
        "date": "2026-10-02",
        "location": "North Park, PA",
        "program": "Youth / Diocesan (K-8)",
        "host": "North Area Diocesan League"
    },
    "RES100626": {
        "meet_id": "2026-10-06-seelos-2",
        "meet_name": "Bl. Francis Seelos 'Second Chance' XC Meet",
        "short_name": "Seelos #2 (Oct 6)",
        "date": "2026-10-06",
        "location": "Pine Community Park, Wexford, PA",
        "program": "Youth / Diocesan (K-8)",
        "host": "Blessed Francis Seelos Academy"
    },
    "RES102226": {
        "meet_id": "2026-10-22-tstca",
        "meet_name": "TSTCA Championship Tune-Up Invite (Class A)",
        "short_name": "TSTCA Invite (Oct 22)",
        "date": "2026-10-22",
        "location": "White Oak Park, White Oak, PA",
        "program": "High School (9-12)",
        "host": "Tri-State Track Coaches Association"
    }
}

def normalize_name(name):
    parts = " ".join(name.split()).split(" ")
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
    return " ".join(out)

def parse_time_to_seconds(t_str):
    if not t_str:
        return None
    t_str = t_str.strip()
    parts = t_str.split(":")
    try:
        if len(parts) == 2:
            return round(int(parts[0]) * 60 + float(parts[1]), 2)
        elif len(parts) == 3:
            return round(int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2]), 2)
    except Exception:
        return None
    return None

def classify_division(title, filename, program):
    t = (title + " " + filename).lower()
    if "5k" in t:
        return "Community 5K", "Community"
    if "1 mile" in t or "1m" in t:
        return "Community 1 Mile", "Community"
    if program == "High School (9-12)" or ("youthtowne" in t and "varsity" in t):
        return "HS Varsity (9-12)", "High School"
    if "jr high" in t or "jr hi" in t or ("varsity" in t and program != "High School (9-12)"):
        return "MS Varsity (7-8)", "Youth (K-8)"
    if "5th and 6th" in t or "jv" in t:
        return "Elementary JV (5-6)", "Youth (K-8)"
    if "3 and 4" in t or "3rd and 4th" in t or "dev" in t:
        return "Developmental (K-4)", "Youth (K-8)"
    return "Other", program

row_xc_re = re.compile(
    r'^\s*(\d+)\s+([A-Za-z0-9\.\'\-\s]+?)\s{2,}([A-Za-z0-9\.\'\-\s&\(\)/]+?)\s+(\d+)\s+(\d+)\s+([MF])\s+(\d+:\d+\.\d+)\s+(\d+:\d+/[A-Za-z]+)',
    re.MULTILINE
)
row_comm_re = re.compile(
    r'^\s*(\d+)\s+([A-Za-z0-9\.\'\-\s]+?)\s{2,}([A-Za-z0-9\.\'\-\s&\(\)/]+?)\s+(\d+)\s+(\d+)\s+([MF])\s+([A-Za-z0-9\-\*\s]+?)\s+(\d+:\d+(?::\d+)?\.\d+)\s+(\d+:\d+/[A-Za-z]+)',
    re.MULTILINE
)

# Parse Team files
detail_team_header_re = re.compile(
    r'<b>([A-Za-z0-9\.\'\-\s&\(\)/]+?)\s+Finish Position -\s+([0-9]+|Inc\.)</b>.*?'
    r'<b>\s*Team Score \(places\):\s*([0-9]+|Inc\.)\s+Team Score \(times\):\s*([0-9:\.]*)\s*(?:Average Time:\s*([0-9:\.]*))?</b>',
    re.DOTALL | re.IGNORECASE
)

summary_team_row_re = re.compile(
    r'<b>\s*(\d+|Inc\.)\s+([A-Za-z0-9\.\'\-\s&\(\)/]+?)\s+(\d+|\d+\s+finishers)\s+(?:(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)(?:\s+(\d+))?(?:\s+(\d+))?)?\s*</b>\s*(?:Top\s+5\s+Times:\s*([0-9:\.]*))?',
    re.IGNORECASE
)

all_races = []
all_aquinas_performances = []
all_team_standings = []

for m in matches:
    href = m["href"]
    fname = m["file"]
    title = m["title"]
    m_code = re.search(r'(RES\d{6})', href).group(1)
    meta = MEET_META[m_code]
    div_name, level = classify_division(title, fname, meta["program"])
    
    fpath = os.path.join("data/raw", fname)
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if "OA" in fname:
        is_comm = (meta["program"] == "Community Race")
        runners_by_gender = {"M": [], "F": []}
        
        if not is_comm:
            for match in row_xc_re.finditer(content):
                place, name, team, bib, grade_age, gend, time_str, pace = match.groups()
                clean_name = normalize_name(name)
                team = " ".join(team.split())
                secs = parse_time_to_seconds(time_str)
                is_aq = "aquinas" in team.lower()
                runner = {
                    "place": int(place),
                    "name": clean_name,
                    "team": team,
                    "bib": int(bib),
                    "grade_or_age": int(grade_age),
                    "gender": gend,
                    "time": time_str,
                    "time_seconds": secs,
                    "pace": pace.strip(),
                    "is_aquinas": is_aq
                }
                runners_by_gender[gend].append(runner)
        else:
            for match in row_comm_re.finditer(content):
                place, name, team, bib, age, gend, ag, time_str, pace = match.groups()
                clean_name = normalize_name(name)
                team = " ".join(team.split())
                secs = parse_time_to_seconds(time_str)
                is_aq = "aquinas" in team.lower()
                runner = {
                    "place": int(place),
                    "name": clean_name,
                    "team": team,
                    "bib": int(bib),
                    "grade_or_age": int(age),
                    "gender": gend,
                    "age_group": " ".join(ag.split()),
                    "time": time_str,
                    "time_seconds": secs,
                    "pace": pace.strip(),
                    "is_aquinas": is_aq
                }
                runners_by_gender[gend].append(runner)

        for gend, r_list in runners_by_gender.items():
            if not r_list:
                continue
            total_runners = len(r_list)
            aq_runners = [r for r in r_list if r["is_aquinas"]]
            gender_label = "Boys" if gend == "M" else "Girls"
            race_id = f"{meta['meet_id']}__{re.sub(r'[^a-z0-9]+', '_', div_name.lower()).strip('_')}__{gender_label.lower()}"
            
            aq_sorted = sorted(aq_runners, key=lambda x: x["time_seconds"] or 999999)
            top5 = aq_sorted[:5]
            spread_1_5 = round(top5[-1]["time_seconds"] - top5[0]["time_seconds"], 2) if len(top5) == 5 else None
            avg_top5_sec = round(sum(x["time_seconds"] for x in top5) / len(top5), 2) if top5 else None
            
            race_obj = {
                "race_id": race_id,
                "meet_id": meta["meet_id"],
                "meet_name": meta["meet_name"],
                "short_meet_name": meta["short_name"],
                "date": meta["date"],
                "location": meta["location"],
                "level": level,
                "division": div_name,
                "gender": gender_label,
                "source_url": "https://www.smileymiles.com/" + href,
                "source_file": fname,
                "total_finishers": total_runners,
                "aquinas_finishers_count": len(aq_runners),
                "aquinas_top5_avg_seconds": avg_top5_sec,
                "aquinas_1_to_5_spread_seconds": spread_1_5,
                "winner_time_seconds": r_list[0]["time_seconds"],
                "winner_name": r_list[0]["name"],
                "winner_team": r_list[0]["team"],
                "aquinas_runners": aq_sorted,
                "all_runners": r_list
            }
            all_races.append(race_obj)
            
            for idx_team, r in enumerate(aq_sorted, 1):
                perf = {
                    "meet_id": meta["meet_id"],
                    "meet_name": meta["meet_name"],
                    "short_meet_name": meta["short_name"],
                    "date": meta["date"],
                    "location": meta["location"],
                    "level": level,
                    "division": div_name,
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
                    "source_url": "https://www.smileymiles.com/" + href
                }
                all_aquinas_performances.append(perf)

    elif "AG" not in fname:
        # Team file!
        gender_label = "Boys" if "boys" in fname.lower() else "Girls"
        # Check if dual/tri-meet matchup in title
        matchup = None
        vs_m = re.search(r'Teams\s+(.+?),\s*[A-Za-z\s]+,\s*PA', title)
        if vs_m and "vs" in vs_m.group(1).lower():
            matchup = vs_m.group(1).strip()
        
        teams_parsed = []
        if "Detail Team Results" in content:
            for tm in detail_team_header_re.finditer(content):
                t_name, pos, score_places, score_time, avg_time = tm.groups()
                t_name = " ".join(t_name.split())
                teams_parsed.append({
                    "team": t_name,
                    "is_aquinas": "aquinas" in t_name.lower(),
                    "position": int(pos) if pos.isdigit() else pos,
                    "points": int(score_places) if score_places.isdigit() else None,
                    "total_time": score_time.strip() if score_time else None,
                    "avg_time": avg_time.strip() if avg_time else None
                })
        else:
            for tm in summary_team_row_re.finditer(content):
                pos, t_name, pts, f1, f2, f3, f4, f5, f6, f7, top5_time = tm.groups()
                t_name = " ".join(t_name.split())
                if t_name.lower().startswith("place"):
                    continue
                t_sec = parse_time_to_seconds(top5_time.strip()) if top5_time else None
                avg_str = None
                if t_sec:
                    avg_s = t_sec / 5.0
                    mins = int(avg_s // 60)
                    rem = avg_s - mins * 60
                    avg_str = f"{mins}:{rem:05.2f}"
                teams_parsed.append({
                    "team": t_name,
                    "is_aquinas": "aquinas" in t_name.lower(),
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
            "short_meet_name": meta["short_name"],
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

# Sort chronologically
all_races.sort(key=lambda x: (x["date"], x["division"], x["gender"]))
all_aquinas_performances.sort(key=lambda x: (x["date"], x["division"], x["gender"], x["overall_place"]))
all_team_standings.sort(key=lambda x: (x["date"], x["division"], x["gender"], x["title"]))

# Build athlete summary profiles
athletes = {}
for p in all_aquinas_performances:
    key = (p["name"], p["gender"], p["level"])
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
        "date": p["date"],
        "division": p["division"],
        "overall_place": p["overall_place"],
        "total_finishers": p["total_finishers"],
        "percentile": p["percentile"],
        "team_rank": p["team_rank"],
        "time": p["time"],
        "time_seconds": p["time_seconds"],
        "pace": p["pace"],
        "source_url": p["source_url"]
    })

athlete_list = []
for key, a in athletes.items():
    times = [r["time_seconds"] for r in a["races"] if r["time_seconds"]]
    best_race = min(a["races"], key=lambda r: r["time_seconds"] or 999999)
    a["races_count"] = len(a["races"])
    a["pr_seconds"] = best_race["time_seconds"]
    a["pr_time"] = best_race["time"]
    a["pr_meet"] = best_race["short_meet_name"]
    a["pr_pace"] = best_race["pace"]
    a["avg_seconds"] = round(sum(times) / len(times), 2) if times else None
    a["avg_percentile"] = round(sum(r["percentile"] for r in a["races"]) / len(a["races"]), 1)
    a["best_place"] = min(r["overall_place"] for r in a["races"])
    a["top_10_finishes"] = sum(1 for r in a["races"] if r["overall_place"] <= 10)
    athlete_list.append(a)

athlete_list.sort(key=lambda x: (x["level"], x["gender"], x["pr_seconds"] or 999999))

full_dataset = {
    "generated_at": "2026-10-23",
    "team": "Aquinas Academy of Pittsburgh",
    "source": "https://www.smileymiles.com/2026%20Results.html",
    "summary": {
        "total_meets": len(MEET_META),
        "total_matched_files": len(matches),
        "total_race_sections": len(all_races),
        "total_aquinas_entries": len(all_aquinas_performances),
        "unique_aquinas_athletes": len(athlete_list),
        "total_team_standings": len(all_team_standings)
    },
    "meets": list(MEET_META.values()),
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

# Save CSVs
perf_fields = [
    "date", "short_meet_name", "meet_name", "location", "level", "division",
    "gender", "name", "grade_or_age", "bib", "overall_place", "total_finishers",
    "percentile", "team_rank", "time", "time_seconds", "pace", "source_url"
]
with open("data/aquinas_2026_performances.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=perf_fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(all_aquinas_performances)

team_fields = [
    "date", "short_meet_name", "level", "division", "gender", "matchup",
    "aquinas_position", "scored_teams_count", "aquinas_points",
    "aquinas_total_time", "aquinas_avg_time", "source_url"
]
with open("data/aquinas_2026_team_scores.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=team_fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(all_team_standings)

print("Summary:", json.dumps(full_dataset["summary"], indent=2))
