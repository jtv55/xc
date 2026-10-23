import re
import os
import json
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

with open("smiley_2026.html", "r", encoding="utf-8", errors="ignore") as f:
    html = f.read()

# Find all <A HREF="...">...</A>
pattern = re.compile(r'<A\s+HREF="([^"]+)"[^>]*>(.*?)</A>', re.IGNORECASE | re.DOTALL)
matches = pattern.findall(html)

links = []
seen = set()
for href, text in matches:
    clean_text = re.sub(r'<[^>]+>', '', text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    if href not in seen and href.lower().endswith(('.htm', '.html')):
        seen.add(href)
        links.append((href, clean_text))

print(f"Total unique HTML links: {len(links)}")
# Filter to likely XC or fall/school races, or just check all of them!
# Checking ~500 small static HTML files with 16 threads takes ~5-10 seconds.
os.makedirs("raw_all", exist_ok=True)
os.makedirs("data/raw", exist_ok=True)

base_url = "https://www.smileymiles.com/"

def fetch_and_check(item):
    idx, (href, text) = item
    # Construct full URL safely
    # href is already URL-encoded in the HTML like "2026/RES102226%20TSTCA..."
    url = base_url + href
    safe_name = urllib.parse.unquote(href).replace("/", "__").replace("\\", "__")
    local_path = os.path.join("raw_all", safe_name)
    try:
        if not os.path.exists(local_path):
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8", errors="ignore")
            with open(local_path, "w", encoding="utf-8") as out:
                out.write(content)
        else:
            with open(local_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        has_aquinas = "aquinas" in content.lower()
        return (idx, href, text, safe_name, has_aquinas, None)
    except Exception as e:
        return (idx, href, text, safe_name, False, str(e))

results = []
with ThreadPoolExecutor(max_workers=20) as ex:
    futures = [ex.submit(fetch_and_check, (i, l)) for i, l in enumerate(links)]
    for fut in as_completed(futures):
        res = fut.result()
        results.append(res)
        if res[4]:
            print(f"[MATCH] {res[2]} -> {res[1]}")

results.sort(key=lambda x: x[0])
matches_out = [
    {"index": r[0], "href": r[1], "title": r[2], "file": r[3]}
    for r in results if r[4]
]
errors_out = [
    {"index": r[0], "href": r[1], "title": r[2], "error": r[5]}
    for r in results if r[5]
]

print(f"\nFound {len(matches_out)} pages mentioning 'Aquinas' (errors: {len(errors_out)})")
with open("aquinas_matches.json", "w", encoding="utf-8") as f:
    json.dump({"matches": matches_out, "errors": errors_out}, f, indent=2)
