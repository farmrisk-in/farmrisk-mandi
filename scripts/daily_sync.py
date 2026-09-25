import os
import json
import urllib.parse
import urllib.request
import time
from datetime import datetime, timedelta

# Configuration
GOV_API_KEY = os.environ.get("GOV_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://meaqfipbbrlqfautkaan.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TABLE_NAME = "mandi_prices"
RESOURCE_ID = "35985678-0d79-46b4-9ed6-6f13308a1d24"
BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

RETRIES = 5
RETENTION_DAYS = 30  # Keep data for the last 30 days

def get_latest_date_in_db():
    """Queries Supabase to find the most recent arrival_date we have stored."""
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?select=arrival_date&order=arrival_date.desc&limit=1"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                if data and len(data) > 0:
                    return datetime.strptime(data[0]['arrival_date'], "%Y-%m-%d")
        except Exception as e:
            print(f"  ⚠️ Failed to get latest date (Attempt {attempt+1}): {e}")
            time.sleep(2)
            
    # If table is empty or query fails, default to fetching yesterday only.
    return datetime.now() - timedelta(days=2)

def fetch_gov_data(date_str):
    all_records = []
    offset = 0
    limit = 10000

    print(f"📡 Fetching data from Gov API for {date_str}...")
    while True:
        params = {
            "api-key": GOV_API_KEY,
            "format": "json",
            "limit": limit,
            "offset": offset,
            "filters[Arrival_Date]": date_str
        }
        url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
        
        success = False
        for attempt in range(RETRIES):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "MandiSync/1.0"})
                with urllib.request.urlopen(req, timeout=60) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    records = data.get("records", [])
                    all_records.extend(records)
                    
                    if len(records) < limit:
                        return all_records
                    
                    offset += limit
                    success = True
                    break
            except Exception as e:
                print(f"  ⚠️ Fetch failed on offset {offset} (Attempt {attempt+1}): {e}")
                time.sleep(5)
                
        if not success:
            print(f"❌ Failed to fetch complete data for {date_str}.")
            return None

def upload_to_supabase(records):
    if not records: return True
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?on_conflict=state,district,market,commodity,variety,arrival_date"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    
    batch_size = 5000
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        data = json.dumps(batch).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        
        success = False
        for attempt in range(RETRIES):
            try:
                with urllib.request.urlopen(req, timeout=45) as response:
                    success = True
                    break
            except Exception as e:
                msg = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
                print(f"  ⚠️ Upload failed for batch (Attempt {attempt+1}): {msg}")
                time.sleep(5)
                
        if not success:
            return False
    return True

def delete_old_data(cutoff_iso_date):
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?arrival_date=lt.{cutoff_iso_date}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    
    print(f"🧹 Cleaning up records strictly older than {cutoff_iso_date}...")
    req = urllib.request.Request(url, headers=headers, method="DELETE")
    
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                print("✅ Cleanup successful.")
                return True
        except Exception:
            time.sleep(5)
    return False

def main():
    yesterday = datetime.now() - timedelta(days=1)
    
    # SMART FETCH: Figure out what dates we are missing!
    latest_db_date = get_latest_date_in_db()
    
    # We want to fetch starting from the latest DB date up to yesterday.
    # This ensures if the latest date was only partially fetched, it gets updated!
    days_to_fetch = []
    current = latest_db_date
    while current.date() <= yesterday.date():
        days_to_fetch.append(current)
        current += timedelta(days=1)
        
    if not days_to_fetch:
        print("✅ Database is already perfectly up to date!")
    
    all_uploads_successful = True
    
    for target_date in days_to_fetch:
        date_str_gov = target_date.strftime("%d/%m/%Y")
        date_str_iso = target_date.strftime("%Y-%m-%d")
        
        raw_records = fetch_gov_data(date_str_gov)
        if raw_records is None:
            all_uploads_successful = False
            break # Stop fetching if the Gov API crashes
            
        cleaned_records = []
        for r in raw_records:
            cleaned_records.append({
                "state": r.get("State", ""),         
                "district": r.get("District", ""),      
                "market": r.get("Market", ""),        
                "commodity": r.get("Commodity", ""),     
                "variety": r.get("Variety", ""),       
                "arrival_date": date_str_iso, 
                "min_price": r.get("Min_Price"),
                "max_price": r.get("Max_Price"),
                "modal_price": r.get("Modal_Price")
            })
            
        seen = set()
        unique_cleaned_records = []
        for r in cleaned_records:
            key = (r['state'], r['district'], r['market'], r['commodity'], r['variety'], r['arrival_date'])
            if key not in seen:
                seen.add(key)
                unique_cleaned_records.append(r)
            
        print(f"☁️ Uploading {len(unique_cleaned_records)} records for {date_str_iso}...")
        if not upload_to_supabase(unique_cleaned_records):
            all_uploads_successful = False
            break
    
    # SMART CLEANUP: Only cleanup if everything successfully uploaded
    if all_uploads_successful:
        # Calculate exactly 30 days before today
        cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
        delete_old_data(cutoff_date.strftime("%Y-%m-%d"))
    else:
        print("🛑 Skipping cleanup because some uploads failed.")

if __name__ == "__main__":
    main()
