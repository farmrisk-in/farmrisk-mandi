import urllib.parse, urllib.request, json
API_KEY = "579b464db66ec23bdd0000012ceaedf3f88b4abd64a2b24e70081b0e"
BASE_URL = "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"

params = {
    "api-key": API_KEY,
    "format": "json",
    "limit": 10000,
    "filters[State]": "Gujarat"
}
url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode("utf-8")).get("records", [])

districts = set()
for r in data:
    districts.add(r.get("District"))

print(f"Total records returned: {len(data)}")
print(f"Unique districts in this API response: {districts}")
