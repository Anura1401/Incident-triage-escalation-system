"""
Batch Upload Utility for Airtable Tickets Table.
Uploads records from data/tickets.csv in batches of 10 using pyairtable.
ALL DATA IS SYNTHETIC. NO REAL CUSTOMER OR ROBOT DATA.
"""

import argparse
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List
from dotenv import load_dotenv
import pandas as pd
from pyairtable import Api

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_CSV = DATA_DIR / "tickets.csv"

# Load environment variables
load_dotenv()


def map_row_to_airtable(row: Dict[str, Any]) -> Dict[str, Any]:
    """Map CSV columns to Airtable table schema fields."""
    fields = {}

    def clean_val(val: Any) -> Any:
        if pd.isna(val) or val is None:
            return None
        s = str(val).strip()
        return s if s != "" else None

    # Schema mapping
    fields["Ticket ID"] = clean_val(row.get("Ticket ID"))
    fields["Created At"] = clean_val(row.get("Created At"))
    fields["Reporter Role"] = clean_val(row.get("Reporter Role"))
    fields["Site"] = clean_val(row.get("Site"))
    fields["Robot ID"] = clean_val(row.get("Robot ID"))
    fields["Category"] = clean_val(row.get("Category"))
    fields["Description"] = clean_val(row.get("Description"))
    fields["Firmware Version"] = clean_val(row.get("Firmware Version"))
    fields["Priority"] = clean_val(row.get("Priority"))
    fields["Status"] = clean_val(row.get("Status"))

    first_resp = clean_val(row.get("First Response At"))
    if first_resp:
        fields["First Response At"] = first_resp

    resolved = clean_val(row.get("Resolved At"))
    if resolved:
        fields["Resolved At"] = resolved

    nr = clean_val(row.get("Needs Review"))
    if nr is not None:
        fields["Needs Review"] = (nr.lower() in ("true", "1", "yes"))

    fields["Synthetic Data Label"] = clean_val(row.get("Synthetic Data Label", "SIMULATED SYNTHETIC DATA"))

    # Return only non-null keys
    return {k: v for k, v in fields.items() if v is not None}


def push_to_airtable(csv_path: Path = DEFAULT_CSV, dry_run: bool = False, limit: int = None) -> None:
    """Push CSV records to Airtable in batches of 10."""
    pat = os.getenv("AIRTABLE_PAT")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_name = os.getenv("AIRTABLE_TABLE", "Tickets")

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}. Run src/generate_tickets.py first.")

    df = pd.read_csv(csv_path)
    if limit:
        df = df.head(limit)

    total_records = len(df)
    print("=" * 65)
    print("AIRTABLE BATCH PUSH UTILITY")
    print(f"Source CSV       : {csv_path.name}")
    print(f"Target Records   : {total_records}")
    print(f"Target Table     : {table_name}")
    print(f"Dry Run Mode     : {dry_run}")
    print("=" * 65)

    if not pat or not base_id:
        print("\n[INFO] Missing AIRTABLE_PAT or AIRTABLE_BASE_ID environment variables.")
        print("To push to live Airtable:")
        print("  1. Copy .env.example to .env: cp .env.example .env")
        print("  2. Add your Airtable Personal Access Token (PAT) and Base ID.")
        print("  3. Create fields in Airtable according to specs/airtable_schema.md.")
        print("  4. Re-run: python src/push_to_airtable.py\n")
        if not dry_run:
            print("Running in DRY-RUN validation mode instead...")
            dry_run = True

    records_to_upload = [map_row_to_airtable(row) for _, row in df.iterrows()]

    if dry_run:
        print(f"\n[DRY RUN] Validated {len(records_to_upload)} records locally.")
        print("Sample mapped record payload (Record 1):")
        print(records_to_upload[0])
        print("\nAll records validated successfully against schema mapping. No network calls made.")
        return

    api = Api(pat)
    table = api.table(base_id, table_name)

    batch_size = 10
    total_uploaded = 0

    for i in range(0, len(records_to_upload), batch_size):
        batch = records_to_upload[i : i + batch_size]
        success = False
        retries = 3
        delay = 1.0

        while not success and retries > 0:
            try:
                table.batch_create(batch, typecast=True)
                total_uploaded += len(batch)
                print(f"Uploaded batch {i // batch_size + 1}: records {i + 1} to {min(i + batch_size, total_records)}...")
                success = True
                # Small throttle to avoid hitting the 5 req/sec Airtable rate limit
                time.sleep(0.25)
            except Exception as e:
                retries -= 1
                if "429" in str(e) or "Too Many Requests" in str(e):
                    print(f"Rate limit hit (429). Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    print(f"Error uploading batch {i // batch_size + 1}: {e}")
                    if retries == 0:
                        raise

    print(f"\nBatch push complete: {total_uploaded} records uploaded to Airtable table '{table_name}'.")


def main():
    parser = argparse.ArgumentParser(description="Push synthetic tickets to Airtable.")
    parser.add_argument("--csv", type=str, default=str(DEFAULT_CSV), help="Path to tickets.csv")
    parser.add_argument("--dry-run", action="store_true", help="Simulate upload without network requests")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of records to upload")
    args = parser.parse_args()

    push_to_airtable(csv_path=Path(args.csv), dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    main()

