import os
import json
import urllib.parse
import urllib.request
import time
from datetime import datetime, timedelta

# Your API Key
API_KEY = os.environ.get("GOV_API_KEY")
RESOURCE_ID = "35985678-0d79-46b4-9ed6-6f13308a1d24"
BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

# Config
DAYS_TO_FETCH = 30  # Starting with 7 days to test speed and size
OUTPUT_DIR = "local_data"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_day(date_str):
    print(f"Fetching data for {date_str}...")
    all_records = []
    offset = 0
    limit = 10000

    while True:
        params = {
            "api-key": API_KEY,
            "format": "json",
            "limit": limit,
            "offset": offset,
            "filters[Arrival_Date]": date_str
        }
        url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
        
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
                records = data.get("records", [])
                
                if not records:
                    break
                    
                all_records.extend(records)
                
                # If we fetched less than the limit, we've reached the end
                if len(records) < limit:
                    break
                    
                offset += limit
                
        except Exception as e:
            print(f"  Failed on offset {offset}: {e}")
            time.sleep(5)
            break

    return all_records

def clean_and_save(date_str, records):
    if not records:
        print(f"  No records found for {date_str}")
        return

    cleaned_data = []
    for r in records:
        cleaned_data.append({
            "state": r.get("State", ""),         
            "district": r.get("District", ""),      
            "market": r.get("Market", ""),        
            "commodity": r.get("Commodity", ""),     
            "variety": r.get("Variety", ""),       
            "min_price": r.get("Min_Price"),
            "max_price": r.get("Max_Price"),
            "modal_price": r.get("Modal_Price")
        })

    # Save to a local JSON file 
    iso_date = datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    filename = f"{OUTPUT_DIR}/{iso_date}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, separators=(',', ':'))
        
    size_kb = os.path.getsize(filename) / 1024
    print(f"  Saved {len(cleaned_data)} records to {filename} ({size_kb:.1f} KB)")

def main():
    print(f"Starting fetch for the last {DAYS_TO_FETCH} days for all of India...")
    
    for i in range(DAYS_TO_FETCH):
        target_date = datetime.now() - timedelta(days=i)
        date_str = target_date.strftime("%d/%m/%Y")
        
        records = fetch_day(date_str)
        clean_and_save(date_str, records)
        time.sleep(1)

if __name__ == "__main__":
    main()
