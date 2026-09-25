import os, json
total_records = 0
states = set()
commodities = set()
for f in os.listdir("local_data"):
    if f.endswith(".json"):
        with open(f"local_data/{f}") as fp:
            data = json.load(fp)
            total_records += len(data)
            for r in data:
                states.add(r.get("state"))
                commodities.add(r.get("commodity"))
print(f"Total Records: {total_records}")
print(f"Total States: {len(states)}")
print(f"Total Commodities: {len(commodities)}")
print(f"Top States Sample: {list(states)[:5]}")
print(f"Top Commodities Sample: {list(commodities)[:5]}")
