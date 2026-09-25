import os, json

for f in os.listdir("local_data"):
    if f.endswith(".json"):
        date_str = f.replace(".json", "")
        with open(f"local_data/{f}", "r") as fp:
            data = json.load(fp)
        
        for r in data:
            if "arrival_date" not in r:
                r["arrival_date"] = date_str
                
        with open(f"local_data/{f}", "w") as fp:
            json.dump(data, fp, separators=(',',':'))
print("Fixed all local JSON files to include arrival_date!")
