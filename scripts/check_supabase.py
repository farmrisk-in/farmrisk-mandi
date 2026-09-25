import os, json, urllib.request, urllib.parse

SUPABASE_URL = "https://meaqfipbbrlqfautkaan.supabase.co"
SUPABASE_KEY = "sb_publishable_jCYy_8ivOndk6MRLJ3nzNw_vT9_R8el"

url = f"{SUPABASE_URL}/rest/v1/mandi_prices?state=eq.Gujarat&select=district&limit=10000"
headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode("utf-8"))

districts = set()
for r in data:
    districts.add(r['district'])

print(f"Total rows fetched: {len(data)}")
print(f"Unique districts in Supabase limit=10000: {districts}")
