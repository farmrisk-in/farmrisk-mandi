import os
import json
import urllib.request
import time

SUPABASE_URL = "https://meaqfipbbrlqfautkaan.supabase.co"
SUPABASE_KEY = "sb_secret__"
TABLE_NAME = "mandi_prices"

def deduplicate(records):
    """Removes duplicate rows within the batch to prevent PostgreSQL error 21000"""
    seen = set()
    unique_records = []
    for r in records:
        # This matches the UNIQUE constraint in the database exactly
        key = (
            r.get('state', ''), 
            r.get('district', ''), 
            r.get('market', ''), 
            r.get('commodity', ''), 
            r.get('variety', ''), 
            r.get('arrival_date', '')
        )
        if key not in seen:
            seen.add(key)
            unique_records.append(r)
    return unique_records

def upload_batch(records):
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?on_conflict=state,district,market,commodity,variety,arrival_date"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    
    data = json.dumps(records).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return True
        except Exception as e:
            if hasattr(e, 'read'):
                print(f"Upload failed: {e.read().decode('utf-8')}")
            else:
                print(f"Upload failed: {e}")
            time.sleep(2)
    return False

def main():
    folder = "local_data"
    files = sorted([f for f in os.listdir(folder) if f.endswith(".json")])
    
    total_uploaded = 0
    for file in files:
        print(f"Processing {file}...")
        with open(f"{folder}/{file}", "r") as f:
            data = json.load(f)
            
        # DEDUPLICATE BEFORE UPLOADING
        data = deduplicate(data)
            
        batch_size = 5000
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            success = upload_batch(batch)
            if success:
                total_uploaded += len(batch)
                print(f"  Uploaded batch of {len(batch)}... (Total: {total_uploaded})")
            else:
                print(f"  Failed to upload batch.")
                
    print(f"\nFinished! Total unique records processed: {total_uploaded}")

if __name__ == "__main__":
    main()
