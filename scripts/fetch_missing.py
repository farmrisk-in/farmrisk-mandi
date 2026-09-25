import urllib.parse, urllib.request, json, time
from datetime import datetime

API_KEY = os.environ.get("GOV_API_KEY")
BASE_URL = "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"
date_str = "31/08/2026"
print(f"Fetching {date_str}...")

all_records = []
offset = 0
while True:
    params = {"api-key": API_KEY, "format": "json", "limit": 10000, "offset": offset, "filters[Arrival_Date]": date_str}
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as res:
            recs = json.loads(res.read().decode("utf-8")).get("records", [])
            if not recs: break
            all_records.extend(recs)
            if len(recs) < 10000: break
            offset += 10000
    except Exception as e:
        print(f"Failed offset {offset}: {e}")
        time.sleep(2)

cleaned = [{"state": r.get("State",""), "district": r.get("District",""), "market": r.get("Market",""), "commodity": r.get("Commodity",""), "variety": r.get("Variety",""), "min_price": r.get("Min_Price"), "max_price": r.get("Max_Price"), "modal_price": r.get("Modal_Price")} for r in all_records]

with open(f"local_data/2026-08-31.json", 'w') as f:
    json.dump(cleaned, f, separators=(',',':'))
print(f"Saved {len(cleaned)} records for 31/08/2026")
