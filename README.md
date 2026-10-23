# Aquinas Academy Cross Country — 2026 Season Analytics & Visualization

Interactive data analytics dashboard and complete race results archive for **Aquinas Academy of Pittsburgh Cross Country** (High School WPIAL Class A & Diocesan Youth K–8 programs), sourced from [Smiley Miles 2026 Race Results](https://www.smileymiles.com/2026%20Results.html).

## Dataset Summary (2026 Season)

- **10 Meets / Events** (9 Cross Country meets + 1 Community 5K/1M race)
- **85 Raw Result Pages** archived in [`data/raw/`](data/raw/) (Overall Finish Lists & Team Scorecards)
- **52 Race Sections** & **50 Official Team Standings**
- **623 Aquinas Academy Finishes** across **187 Unique Runners**

### Meets Included
1. **2026-08-25** — Seelos Pine Park XC Opener (Wexford, PA) — Developmental, JV, Varsity Boys & Girls
2. **2026-08-29** — Blessed Trinity (BTA) XC Invitational (Glenshaw, PA) — Developmental, JV, Varsity Boys & Girls
3. **2026-09-04** — St. Kilian XC Invitational (Mars, PA) — Developmental, JV, Varsity Boys & Girls
4. **2026-09-10** — St. Al Twilight Harvest Home 5K & 1 Mile (Allison Park, PA)
5. **2026-09-18** — Youthtowne Clash XC Invitational (Clinton, PA) — HS Varsity (9–12), Jr High (7–8), 5th & 6th Grade, 3rd & 4th Grade Boys & Girls
6. **2026-09-24** — Aquinas & Holy Cross Home XC Meet (Allison Park, PA) — Developmental, JV, Varsity Boys & Girls
7. **2026-09-29** — Avonworth WPIAL Tri-Meet vs. Avonworth & Neighborhood Academy (Sewickley, PA) — HS Varsity Boys & Girls
8. **2026-10-02** — North Area Diocesan XC Championships (North Park, PA) — Developmental, JV, Varsity Boys & Girls
9. **2026-10-06** — Bl. Francis Seelos "Second Chance" XC Meet (Wexford, PA) — Developmental, JV, Varsity Boys & Girls
10. **2026-10-22** — TSTCA Championship Tune-Up Invite Class A (White Oak, PA) — HS Class A Boys & Girls

## Structured Data Files

- [`data/aquinas_2026_performances.csv`](data/aquinas_2026_performances.csv) — Every Aquinas Academy individual finish with time, pace, overall place, team rank, and field percentile.
- [`data/aquinas_2026_team_scores.csv`](data/aquinas_2026_team_scores.csv) — Every official team score, placement, top-5 total time, and top-5 average time.
- [`data/aquinas_2026_full.json`](data/aquinas_2026_full.json) — Complete JSON dataset including full race fields for percentile and pack gap analysis.
