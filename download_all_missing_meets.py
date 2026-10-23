import urllib.request
import json
import os
import re

os.makedirs('data/extra', exist_ok=True)
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as resp:
        return resp.read().decode('utf-8', errors='ignore')

# 1. Download RunSignup 191674, 193469, 193936 complete 2026 result sets
for rid, slug in [('191674', 'oakland_catholic'), ('193469', 'run_for_pumpkins'), ('193936', 'diocesan_champ')]:
    r_data = json.loads(fetch(f'https://runsignup.com/Rest/race/{rid}?format=json&include_events=T'))
    events = [ev for ev in r_data.get('race', {}).get('events', []) if '2026' in (ev.get('start_time') or '')]
    out = {'race_id': rid, 'race_name': r_data.get('race', {}).get('name'), 'events': []}
    for ev in events:
        ev_id = ev['event_id']
        rsets = json.loads(fetch(f'https://runsignup.com/Rest/race/{rid}/results/get-result-sets?event_id={ev_id}&format=json')).get('individual_results_sets', [])
        for rs in rsets:
            rs_id = rs['individual_result_set_id']
            res_data = json.loads(fetch(f'https://runsignup.com/Rest/race/{rid}/results/get-results?event_id={ev_id}&individual_result_set_id={rs_id}&page=1&results_per_page=2500&format=json'))
            rset_full = res_data.get('individual_results_sets', [{}])[0]
            out['events'].append({
                'event_id': ev_id,
                'event_name': ev.get('name'),
                'start_time': ev.get('start_time'),
                'distance': ev.get('distance'),
                'result_set_id': rs_id,
                'result_set_name': rset_full.get('individual_result_set_name'),
                'headers': rset_full.get('results_headers', {}),
                'results': rset_full.get('results', [])
            })
    with open(f'data/extra/rsu_{rid}_{slug}.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    print(f"Saved data/extra/rsu_{rid}_{slug}.json ({len(out['events'])} events)")

# 2. Download RunHigh PIAA Foundation (R092626DB.html, R092626DE.html, R092626DI.html)
for code in ['R092626DB.html', 'R092626DE.html', 'R092626DI.html']:
    html = fetch(f'https://www.runhigh.com/2026RESULTS/{code}')
    with open(f'data/extra/runhigh_{code}', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Saved data/extra/runhigh_{code} ({len(html)}B)")

# 3. Download Red, White & Blue Classic (766811) raw results from PA MileSplit
# Check all result links on https://pa.milesplit.com/meets/766811-24th-annual-red-white-and-blue-classic-2026/results
rwb_index = fetch('https://pa.milesplit.com/meets/766811-24th-annual-red-white-and-blue-classic-2026/results')
rwb_links = set(re.findall(r'href=["\']([^"\']*results/\d+/raw)["\']', rwb_index, re.I))
print("RWB raw links:", rwb_links)
for idx_l, rl in enumerate(sorted(rwb_links)):
    full_u = rl if rl.startswith('http') else 'https://pa.milesplit.com' + rl
    h = fetch(full_u)
    rid_num = rl.split('/')[-2]
    with open(f'data/extra/milesplit_rwb_{rid_num}.html', 'w', encoding='utf-8') as f:
        f.write(h)
    print(f"Saved data/extra/milesplit_rwb_{rid_num}.html ({len(h)}B, has_aquinas={'aquinas' in h.lower()})")

# 4. Download Firestore meets/782377 (WPIAL A/AA Section 4 XC Championships) all pages
ev_782 = json.loads(fetch('https://firestore.googleapis.com/v1/projects/milesplit-live-results/databases/(default)/documents/meets/782377/events'))
all_docs = []
page_token = None
while True:
    u = 'https://firestore.googleapis.com/v1/projects/milesplit-live-results/databases/(default)/documents/meets/782377/entries?pageSize=300'
    if page_token:
        u += f'&pageToken={ urllib.parse.quote(page_token) }'
    d = json.loads(fetch(u))
    docs = d.get('documents', [])
    all_docs.extend(docs)
    page_token = d.get('nextPageToken')
    if not page_token:
        break

with open('data/extra/firestore_782377_wpial_sec4.json', 'w', encoding='utf-8') as f:
    json.dump({'events': ev_782.get('documents', []), 'entries': all_docs}, f, indent=2)
print(f"Saved data/extra/firestore_782377_wpial_sec4.json ({len(all_docs)} entry docs)")
