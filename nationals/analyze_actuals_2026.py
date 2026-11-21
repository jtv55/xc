import json
import math
import pathlib
import re
import numpy as np

RAW_DIR = pathlib.Path(r"c:\Users\j_t_v\XC\nationals\data\actuals_2026\raw")
SNAP_DIR = pathlib.Path(r"c:\Users\j_t_v\XC\nationals\data\snapshots\pre_race_20261121")
OUT_DIR = pathlib.Path(r"c:\Users\j_t_v\XC\nationals\data\actuals_2026")

# Official FinishTiming file mapping per Event (1..11)
EVENT_FILES = {
    1:  {"ind": "3341", "nat_team": "3341", "cyo_team": None,   "cyo_ind": None,   "dist_m": 5000, "name": "Girls 15–18 5K", "short": "15–18G"},
    2:  {"ind": "3342", "nat_team": "3342", "cyo_team": None,   "cyo_ind": None,   "dist_m": 5000, "name": "Boys 15–18 5K",  "short": "15–18B"},
    3:  {"ind": "3343", "nat_team": "3352", "cyo_team": "3354", "cyo_ind": "3365", "dist_m": 2000, "name": "Girls 6–8 2K",   "short": "6–8G"},
    4:  {"ind": "3344", "nat_team": "3353", "cyo_team": "3355", "cyo_ind": "3366", "dist_m": 2000, "name": "Boys 6–8 2K",    "short": "6–8B"},
    5:  {"ind": "3345", "nat_team": "3345", "cyo_team": None,   "cyo_ind": None,   "dist_m": 1000, "name": "Mixed 1–8 1K",   "short": "1K Open"},
    6:  {"ind": "3346", "nat_team": "3356", "cyo_team": "3363", "cyo_ind": "3367", "dist_m": 3000, "name": "Girls 9–10 3K",  "short": "9–10G"},
    7:  {"ind": "3347", "nat_team": "3357", "cyo_team": "3364", "cyo_ind": "3368", "dist_m": 3000, "name": "Boys 9–10 3K",   "short": "9–10B"},
    8:  {"ind": "3348", "nat_team": "3358", "cyo_team": "3369", "cyo_ind": "3370", "dist_m": 3000, "name": "Girls 11–12 3K", "short": "11–12G"},
    9:  {"ind": "3349", "nat_team": "3359", "cyo_team": "3371", "cyo_ind": "3372", "dist_m": 3000, "name": "Boys 11–12 3K",  "short": "11–12B"},
    10: {"ind": "3350", "nat_team": "3360", "cyo_team": "3373", "cyo_ind": "3374", "dist_m": 4000, "name": "Girls 13–14 4K", "short": "13–14G"},
    11: {"ind": "3351", "nat_team": "3361", "cyo_team": "3375", "cyo_ind": "3376", "dist_m": 4000, "name": "Boys 13–14 4K",  "short": "13–14B"},
}

def norm_name(s):
    s = (s or "").lower().strip()
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"[^a-z]", "", s)
    return s

def fmt_time(sec):
    if sec is None or math.isnan(sec):
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
    return f"{mn}:{sc:02d}"

def parse_split_info(ath):
    sps = ath.get("splits") or []
    for sp in reversed(sps):
        if isinstance(sp, dict) and sp.get("timeSeconds"):
            return sp
    return None

def load_event_actuals(ev_num):
    cfg = EVENT_FILES[ev_num]
    ind_data = json.loads((RAW_DIR / f"{cfg['ind']}.json").read_text(encoding="utf-8"))
    groups = ind_data.get("groups") or []
    overall_grp = None
    age_grps = {}
    for g in groups:
        nm = (g.get("name") or "").strip()
        if nm.lower() == "overall":
            overall_grp = g
        else:
            age_grps[nm] = g

    # Build age-group place lookup by bib/athlete_id
    age_place_map = {}
    age_field_sizes = {}
    for gname, g in age_grps.items():
        fin_cnt = 0
        for a in g.get("athletes") or []:
            sp = parse_split_info(a)
            if sp and not sp.get("dnf"):
                fin_cnt += 1
        age_field_sizes[gname] = fin_cnt
        for a in g.get("athletes") or []:
            sp = parse_split_info(a)
            if sp and not sp.get("dnf"):
                aid = a.get("athlete_id") or a.get("bib")
                age_place_map[aid] = {
                    "age_group_name": gname,
                    "age_place": int(sp["place"]) if str(sp.get("place", "")).isdigit() else sp.get("placeInternal"),
                    "age_field_size": fin_cnt,
                }

    # Build CYO individual place lookup
    cyo_place_map = {}
    cyo_age_place_map = {}
    cyo_field_size = 0
    if cfg["cyo_ind"]:
        cd = json.loads((RAW_DIR / f"{cfg['cyo_ind']}.json").read_text(encoding="utf-8"))
        for g in cd.get("groups") or []:
            gnm = (g.get("name") or "").strip()
            aths = g.get("athletes") or []
            if gnm.lower() == "overall":
                cyo_field_size = sum(1 for a in aths if (parse_split_info(a) and not parse_split_info(a).get("dnf")))
                for a in aths:
                    sp = parse_split_info(a)
                    if sp and not sp.get("dnf"):
                        aid = a.get("athlete_id") or a.get("bib")
                        cyo_place_map[aid] = int(sp["place"]) if str(sp.get("place", "")).isdigit() else sp.get("placeInternal")
            else:
                for a in aths:
                    sp = parse_split_info(a)
                    if sp and not sp.get("dnf"):
                        aid = a.get("athlete_id") or a.get("bib")
                        cyo_age_place_map[aid] = int(sp["place"]) if str(sp.get("place", "")).isdigit() else sp.get("placeInternal")

    # Overall finishers
    finishers = []
    if overall_grp:
        raw_aths = overall_grp.get("athletes") or []
        fin_total = sum(1 for a in raw_aths if (parse_split_info(a) and not parse_split_info(a).get("dnf")))
        for a in raw_aths:
            sp = parse_split_info(a)
            if not sp or sp.get("dnf"):
                continue
            aid = a.get("athlete_id") or a.get("bib")
            t_sec = float(sp["timeSeconds"])
            ag_info = age_place_map.get(aid, {})
            finishers.append({
                "event_num": ev_num,
                "athlete_id": aid,
                "bib": a.get("bib"),
                "first_name": (a.get("first_name") or "").strip(),
                "last_name": (a.get("last_name") or "").strip(),
                "display_name": f"{(a.get('first_name') or '').strip()} {(a.get('last_name') or '').strip()}".strip(),
                "age": a.get("age"),
                "gender": a.get("gender"),
                "team": (a.get("team") or "").strip(),
                "overall_place": int(sp["place"]) if str(sp.get("place", "")).isdigit() else sp.get("placeInternal"),
                "overall_field_size": fin_total,
                "time_sec": t_sec,
                "time_str": sp.get("time") or fmt_time(t_sec),
                "time_exact": sp.get("timeOriginal") or sp.get("time"),
                "pace_mi": fmt_pace(t_sec, cfg["dist_m"]),
                "age_group_name": ag_info.get("age_group_name"),
                "age_place": ag_info.get("age_place"),
                "age_field_size": ag_info.get("age_field_size"),
                "cyo_place": cyo_place_map.get(aid),
                "cyo_field_size": cyo_field_size if aid in cyo_place_map else None,
                "cyo_age_place": cyo_age_place_map.get(aid),
            })

    # Parse official National Open & CYO Team Scores
    def parse_teams(file_id):
        if not file_id:
            return []
        td = json.loads((RAW_DIR / f"{file_id}.json").read_text(encoding="utf-8"))
        out = []
        for g in td.get("groups") or []:
            if (g.get("name") or "").strip().lower() != "overall":
                continue
            for t in g.get("teams") or []:
                sp = None
                for s in reversed(t.get("splits") or []):
                    if isinstance(s, dict):
                        sp = s
                        break
                if not sp:
                    continue
                pl_raw = sp.get("place")
                sc_raw = sp.get("score")
                if not str(pl_raw).isdigit() or not str(sc_raw).isdigit():
                    continue
                out.append({
                    "team": (t.get("name") or "").strip(),
                    "place": int(pl_raw),
                    "score": int(sc_raw),
                    "num_runners": sp.get("numRunners") or t.get("numRunners"),
                    "avg_time": sp.get("avgTime"),
                    "avg_mile": sp.get("avgMile"),
                    "gap": sp.get("gap"),
                    "team_time": sp.get("teamTime"),
                    "scoring_places": sp.get("scoringPlaces"),
                    "finish_places": sp.get("finishPlaces"),
                    "athletes": sp.get("athletes") or [],
                })
        out.sort(key=lambda x: x["place"])
        return out

    nat_teams = parse_teams(cfg["nat_team"])
    cyo_teams = parse_teams(cfg["cyo_team"])
    return finishers, nat_teams, cyo_teams, age_field_sizes

# Load frozen pre-race master predictions
pre_master = json.loads((SNAP_DIR / "cccnyc_2026_master_prerace.json").read_text(encoding="utf-8"))
pre_athletes = [a for a in pre_master["athletes"] if not a["is_duplicate_ghost"]]
pre_teams = pre_master["teams"]

# Build lookup indices for pre-race athletes
by_ev_exact = {}
by_ev_last = {}
for a in pre_athletes:
    ev = a["event_num"]
    fn, ln = norm_name(a["first_name"]), norm_name(a["last_name"])
    by_ev_exact.setdefault((ev, fn, ln), []).append(a)
    by_ev_last.setdefault((ev, ln), []).append(a)

all_actual_finishers = []
all_matched_pairs = []
unmatched_actuals = []
event_summaries = []
team_comparisons = []

def norm_team(s):
    s = (s or "").lower().strip()
    s = re.sub(r"\([a-z0-9]+\)$", "", s).strip()
    s = s.replace("philadelphia cyo", "phila. cyo")
    s = s.replace("louisville tigersharks", "louisville tigersharks")
    s = re.sub(r"[\*\'\^1]+$", "", s).strip()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s

for ev_num in range(1, 12):
    fins, nat_teams, cyo_teams, ag_sizes = load_event_actuals(ev_num)
    all_actual_finishers.extend(fins)
    used_pre_ids = set()
    ev_pairs = []

    for f in fins:
        fn, ln = norm_name(f["first_name"]), norm_name(f["last_name"])
        cand = None
        # 1. Exact first+last (or swapped last+first) in same event
        cands = [a for a in by_ev_exact.get((ev_num, fn, ln), []) if a["id"] not in used_pre_ids]
        if not cands:
            cands = [a for a in by_ev_exact.get((ev_num, ln, fn), []) if a["id"] not in used_pre_ids]
        if len(cands) == 1:
            cand = cands[0]
        elif len(cands) > 1:
            # Prefer matching age/team
            cands.sort(key=lambda a: (0 if a["age"] == f["age"] else 1, 0 if norm_team(a["team"]) == norm_team(f["team"]) else 1))
            cand = cands[0]
        else:
            # 2. Fuzzy same last name + first initial or age + team in same event
            lcands = [a for a in by_ev_last.get((ev_num, ln), []) if a["id"] not in used_pre_ids]
            scored = []
            for a in lcands:
                afn = norm_name(a["first_name"])
                score = 0
                if afn and fn and (afn.startswith(fn[:3]) or fn.startswith(afn[:3])):
                    score += 3
                elif afn and fn and afn[0] == fn[0]:
                    score += 1
                if a["age"] == f["age"]:
                    score += 2
                if norm_team(a["team"]) == norm_team(f["team"]):
                    score += 2
                if score >= 4:
                    scored.append((score, a))
            if scored:
                scored.sort(key=lambda x: -x[0])
                cand = scored[0][1]

        if cand:
            used_pre_ids.add(cand["id"])
            time_err = f["time_sec"] - cand["proj_mu"]  # negative = ran FASTER than predicted!
            place_err = f["overall_place"] - cand["exp_place"]
            in_p10_p90 = (cand["p10_time_sec"] <= f["time_sec"] <= cand["p90_time_sec"]) if cand.get("p10_time_sec") else None
            # Check actual AA Top-25 status
            act_aa = (f["age_place"] is not None and f["age_place"] <= 25)
            pair = {
                "id": cand["id"],
                "event_num": ev_num,
                "event_name": EVENT_FILES[ev_num]["name"],
                "event_short": EVENT_FILES[ev_num]["short"],
                "dist_m": EVENT_FILES[ev_num]["dist_m"],
                "display_name": cand["display_name"],
                "team": cand["team"],
                "actual_team": f["team"],
                "club_state": cand["club_state"],
                "is_dop": cand["is_dop"],
                "is_cyo": cand["is_cyo"],
                "home_school": cand["home_school"],
                "age": cand["age"],
                "award_group": cand["award_group"],
                "seed_tier": cand["seed_tier"],
                "races_2026_count": len(cand["races_2026"]),
                "pred_time_sec": round(cand["proj_mu"], 2),
                "pred_time_str": cand["proj_time_str"],
                "p10_time_sec": round(cand["p10_time_sec"], 2),
                "p90_time_sec": round(cand["p90_time_sec"], 2),
                "p10_time_str": cand["p10_time_str"],
                "p90_time_str": cand["p90_time_str"],
                "pred_pace_mi": cand["proj_pace_mi"],
                "pred_place": cand["exp_place"],
                "pred_cyo_place": cand["cyo_exp_rank"],
                "pred_age_rank": cand["aa_age_exp_rank"],
                "pred_aa_prob": cand["aa_age_prob"],
                "act_time_sec": round(f["time_sec"], 2),
                "act_time_str": f["time_str"],
                "act_time_exact": f["time_exact"],
                "act_pace_mi": f["pace_mi"],
                "act_place": f["overall_place"],
                "act_field_size": f["overall_field_size"],
                "act_age_place": f["age_place"],
                "act_age_field_size": f["age_field_size"],
                "act_cyo_place": f["cyo_place"],
                "act_cyo_field_size": f["cyo_field_size"],
                "act_cyo_age_place": f["cyo_age_place"],
                "act_is_aa": act_aa,
                "time_err_sec": round(time_err, 2),
                "abs_time_err_sec": round(abs(time_err), 2),
                "pct_time_err": round(100.0 * time_err / cand["proj_mu"], 2),
                "place_err": round(place_err, 1),
                "age_rank_err": round(f["age_place"] - cand["aa_age_exp_rank"], 1) if f["age_place"] else None,
                "in_p10_p90": in_p10_p90,
                "bib": f["bib"],
            }
            ev_pairs.append(pair)
            all_matched_pairs.append(pair)
        else:
            unmatched_actuals.append(f)

    # Event-level calibration stats
    errs = np.array([p["time_err_sec"] for p in ev_pairs])
    abs_errs = np.abs(errs)
    pct_errs = np.array([abs(p["pct_time_err"]) for p in ev_pairs])
    pl_errs = np.array([abs(p["place_err"]) for p in ev_pairs])
    corr_t = float(np.corrcoef([p["pred_time_sec"] for p in ev_pairs], [p["act_time_sec"] for p in ev_pairs])[0, 1]) if len(ev_pairs) > 2 else None
    cov_80 = 100.0 * sum(1 for p in ev_pairs if p["in_p10_p90"]) / max(1, len(ev_pairs))

    # Compare predicted vs actual National & CYO teams
    pre_ev_nat = [t for t in pre_teams if t["event_num"] == ev_num and t["scores_official_team"]]
    pre_ev_nat.sort(key=lambda x: x["nat"]["exp_rank"])
    pre_ev_cyo = [t for t in pre_teams if t["event_num"] == ev_num and t["scores_official_team"] and t["is_cyo"]]
    pre_ev_cyo.sort(key=lambda x: x["cyo"]["exp_rank"])

    def match_team_list(pred_list, act_list, lens):
        rows = []
        act_by_norm = {norm_team(t["team"]): t for t in act_list}
        for pt in pred_list:
            nt = norm_team(pt["team"])
            at = act_by_norm.get(nt)
            if not at:
                # try without trailing " a"
                at = act_by_norm.get(re.sub(r" a$", "", nt)) or act_by_norm.get(nt + " a")
            if not at and pt["is_dop"] and lens in ("nat", "cyo"):
                for k, v in act_by_norm.items():
                    if "pittsburgh" in k:
                        if (" b" in nt) == (" b" in k):
                            at = v; break
            rows.append({
                "event_num": ev_num,
                "event_short": EVENT_FILES[ev_num]["short"],
                "lens": lens,
                "team": pt["team"],
                "state": pt["state"],
                "is_dop": pt["is_dop"],
                "is_cyo": pt["is_cyo"],
                "pred_rank": pt[lens]["exp_rank"],
                "pred_score": pt[lens]["exp_score"],
                "pred_win_prob": pt[lens]["win_prob"],
                "pred_podium_prob": pt[lens]["podium_prob"],
                "act_team_name": at["team"] if at else None,
                "act_rank": at["place"] if at else None,
                "act_score": at["score"] if at else None,
                "act_avg_time": at["avg_time"] if at else None,
                "act_gap": at["gap"] if at else None,
                "act_scoring_places": at["scoring_places"] if at else None,
            })
        return rows

    nat_cmp = match_team_list(pre_ev_nat, nat_teams, "nat")
    cyo_cmp = match_team_list(pre_ev_cyo, cyo_teams, "cyo")
    team_comparisons.extend(nat_cmp)
    team_comparisons.extend(cyo_cmp)

    event_summaries.append({
        "event_num": ev_num,
        "name": EVENT_FILES[ev_num]["name"],
        "short": EVENT_FILES[ev_num]["short"],
        "dist_m": EVENT_FILES[ev_num]["dist_m"],
        "actual_finishers": len(fins),
        "matched_finishers": len(ev_pairs),
        "unmatched_finishers": len(fins) - len(ev_pairs),
        "median_time_bias_sec": round(float(np.median(errs)), 2) if len(errs) else None,
        "mae_time_sec": round(float(np.mean(abs_errs)), 2) if len(abs_errs) else None,
        "median_abs_err_sec": round(float(np.median(abs_errs)), 2) if len(abs_errs) else None,
        "mape_pct": round(float(np.mean(pct_errs)), 2) if len(pct_errs) else None,
        "mae_place": round(float(np.mean(pl_errs)), 1) if len(pl_errs) else None,
        "time_r": round(corr_t, 4) if corr_t is not None else None,
        "p10_p90_coverage_pct": round(cov_80, 1),
        "nat_top3_pred": [{"team": t["team"], "score": t["nat"]["exp_score"], "win": t["nat"]["win_prob"]} for t in pre_ev_nat[:3]],
        "nat_top3_act": [{"team": t["team"], "score": t["score"], "avg": t["avg_time"]} for t in nat_teams[:3]],
        "cyo_top3_pred": [{"team": t["team"], "score": t["cyo"]["exp_score"], "win": t["cyo"]["win_prob"]} for t in pre_ev_cyo[:3]],
        "cyo_top3_act": [{"team": t["team"], "score": t["score"], "avg": t["avg_time"]} for t in cyo_teams[:3]],
    })

# Global metrics
all_errs = np.array([p["time_err_sec"] for p in all_matched_pairs])
all_abs = np.abs(all_errs)
all_pct = np.array([abs(p["pct_time_err"]) for p in all_matched_pairs])
all_pl = np.array([abs(p["place_err"]) for p in all_matched_pairs])
all_cov = 100.0 * sum(1 for p in all_matched_pairs if p["in_p10_p90"]) / max(1, len(all_matched_pairs))

# Brier score & calibration buckets for Single-Year All-American Top-25 predictions (Ev 3,4,6..11)
aa_pairs = [p for p in all_matched_pairs if p["event_num"] not in (1, 2, 5) and p["act_age_place"] is not None]
brier = float(np.mean([(p["pred_aa_prob"] / 100.0 - (1.0 if p["act_is_aa"] else 0.0)) ** 2 for p in aa_pairs]))
exp_aa_total = sum(p["pred_aa_prob"] / 100.0 for p in aa_pairs)
act_aa_total = sum(1 for p in aa_pairs if p["act_is_aa"])

# Calibration by Seed Tier
tier_stats = {}
for tier in sorted(set(p["seed_tier"] for p in all_matched_pairs)):
    sub = [p for p in all_matched_pairs if p["seed_tier"] == tier]
    e = np.array([p["time_err_sec"] for p in sub])
    tier_stats[tier] = {
        "n": len(sub),
        "median_bias_sec": round(float(np.median(e)), 2),
        "mae_sec": round(float(np.mean(np.abs(e))), 2),
        "median_abs_sec": round(float(np.median(np.abs(e))), 2),
        "mape_pct": round(float(np.mean([abs(p["pct_time_err"]) for p in sub])), 2),
        "p10_p90_cov": round(100.0 * sum(1 for p in sub if p["in_p10_p90"]) / len(sub), 1),
    }

# Print Headline Results!
print("=" * 80)
print(f"2026 CCCNYC & CYO NATIONALS — ACTUAL VS. PREDICTED SUMMARY")
print("=" * 80)
print(f"Total Actual Finishers: {len(all_actual_finishers)} | Matched to Pre-Race Forecast: {len(all_matched_pairs)} ({100*len(all_matched_pairs)/len(all_actual_finishers):.1f}%) | Unmatched (race-day/DNS-swap): {len(unmatched_actuals)}")
print(f"Global Time Bias (Act - Pred): median {np.median(all_errs):+.2f}s (mean {np.mean(all_errs):+.2f}s) | MAE: {np.mean(all_abs):.2f}s | Median Abs Err: {np.median(all_abs):.2f}s | MAPE: {np.mean(all_pct):.2f}%")
print(f"P10–P90 80% Interval Coverage: {all_cov:.1f}% (target: 80.0%) | AA Top-25 Brier Score: {brier:.4f} (Exp AA: {exp_aa_total:.1f} vs Act AA: {act_aa_total})")

print("\n--- BY SEED TIER ---")
for t, st in tier_stats.items():
    print(f"  {t:34s} | n={st['n']:4d} | bias={st['median_bias_sec']:+6.1f}s | MAE={st['mae_sec']:5.1f}s | MedAE={st['median_abs_sec']:5.1f}s | MAPE={st['mape_pct']:4.2f}% | P10-90={st['p10_p90_cov']:4.1f}%")

print("\n--- BY EVENT ---")
for es in event_summaries:
    print(f"  Ev {es['event_num']:2d} {es['short']:7s} | fin={es['actual_finishers']:3d} (m={es['matched_finishers']:3d}) | bias={es['median_time_bias_sec']:+6.1f}s | MAE={es['mae_time_sec']:5.1f}s | MAPE={es['mape_pct']:4.2f}% | r={es['time_r']:.3f} | 80%cov={es['p10_p90_coverage_pct']:4.1f}%")
    if es["nat_top3_pred"] and es["nat_top3_act"]:
        p1 = es["nat_top3_pred"][0]["team"]
        a1 = es["nat_top3_act"][0]["team"]
        print(f"        Nat #1 Pred: {p1} vs Act: {a1} ({es['nat_top3_act'][0]['score']} pts)")
    if es["cyo_top3_pred"] and es["cyo_top3_act"]:
        p1 = es["cyo_top3_pred"][0]["team"]
        a1 = es["cyo_top3_act"][0]["team"]
        print(f"        CYO #1 Pred: {p1} vs Act: {a1} ({es['cyo_top3_act'][0]['score']} pts)")

print("\n" + "=" * 80)
print("AQUINAS ACADEMY (11 PITTSBURGH CYO RUNNERS) — PREDICTED VS. ACTUAL")
print("=" * 80)
aq_pairs = sorted([p for p in all_matched_pairs if p["is_dop"] and (p["home_school"] or "") == "Aquinas Academy"], key=lambda x: (x["event_num"], x["act_place"]))
pre_aq = [a for a in pre_athletes if a["is_dop"] and (a["home_school"] or "") == "Aquinas Academy"]
matched_aq_ids = {p["id"] for p in aq_pairs}
for p in aq_pairs:
    aa_flag = "ALL-AMERICAN!" if p["act_is_aa"] else ""
    print(f"  Ev {p['event_num']:2d} ({p['event_short']:6s}) | {p['display_name']:20s} (Age {p['age']:2d}) | Pred {p['pred_time_str']:>7s} (#{p['pred_place']:5.1f}, Age #{p['pred_age_rank']:4.1f}, {p['pred_aa_prob']:5.1f}% AA) -> ACT {p['act_time_str']:>7s} ({p['act_pace_mi']}/mi, Ov #{p['act_place']:3d}/{p['act_field_size']}, CYO #{p['act_cyo_place']}, Age #{p['act_age_place']}/{p['act_age_field_size']}) | Δt={p['time_err_sec']:+6.1f}s {aa_flag}")
for a in pre_aq:
    if a["id"] not in matched_aq_ids:
        print(f"  [DNS/UNMATCHED] Ev {a['event_num']} {a['display_name']} (Age {a['age']}, {a['team']})")

print("\n" + "=" * 80)
print("PITTSBURGH CYO — ALL 64 RUNNERS & 10 SQUADS")
print("=" * 80)
dop_pairs = [p for p in all_matched_pairs if p["is_dop"]]
dop_aa_act = [p for p in dop_pairs if p["act_is_aa"]]
dop_aa_exp = sum(p["pred_aa_prob"] / 100.0 for p in dop_pairs)
print(f"Pittsburgh CYO Finishers matched: {len(dop_pairs)} / 64 | Expected Age AAs: {dop_aa_exp:.1f} vs ACTUAL Age AAs: {len(dop_aa_act)}!")
print("Actual Pittsburgh CYO All-Americans:")
for p in sorted(dop_aa_act, key=lambda x: (x["act_age_place"], x["event_num"])):
    print(f"  Age #{p['act_age_place']:2d}/{p['act_age_field_size']:3d} | {p['display_name']:22s} (Age {p['age']:2d}, {p['event_short']:6s}, {p['home_school']}) | Act {p['act_time_str']} vs Pred {p['pred_time_str']} (Δt={p['time_err_sec']:+5.1f}s | Pre-race AA%: {p['pred_aa_prob']:.1f}%)")

print("\nPittsburgh CYO Squads (Pred vs Act):")
for tc in [t for t in team_comparisons if t["is_dop"]]:
    print(f"  Ev {tc['event_num']:2d} {tc['event_short']:6s} {tc['lens'].upper():3s} | {tc['team']:18s} | Pred #{tc['pred_rank']:4.1f} ({tc['pred_score']:5.1f} pts) -> Act #{str(tc['act_rank']):>4s} ({str(tc['act_score']):>4s} pts, avg {tc['act_avg_time']}, gap {tc['act_gap']})")

# Save full structured output
payload = {
    "summary": {
        "total_actual_finishers": len(all_actual_finishers),
        "matched_finishers": len(all_matched_pairs),
        "unmatched_finishers": len(unmatched_actuals),
        "median_time_bias_sec": round(float(np.median(all_errs)), 2),
        "mean_time_bias_sec": round(float(np.mean(all_errs)), 2),
        "mae_time_sec": round(float(np.mean(all_abs)), 2),
        "median_abs_err_sec": round(float(np.median(all_abs)), 2),
        "mape_pct": round(float(np.mean(all_pct)), 2),
        "mae_place": round(float(np.mean(all_pl)), 1),
        "p10_p90_coverage_pct": round(all_cov, 1),
        "aa_brier_score": round(brier, 4),
        "exp_aa_total": round(exp_aa_total, 1),
        "act_aa_total": act_aa_total,
        "dop_matched": len(dop_pairs),
        "dop_exp_aa": round(dop_aa_exp, 1),
        "dop_act_aa": len(dop_aa_act),
    },
    "tier_stats": tier_stats,
    "events": event_summaries,
    "teams": team_comparisons,
    "athletes": all_matched_pairs,
    "unmatched_actuals_count": len(unmatched_actuals),
}
(OUT_DIR / "predicted_vs_actual_2026.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(f"\nSaved {OUT_DIR / 'predicted_vs_actual_2026.json'}")
