"""Generate a small second batch to demo incremental loads.

5 brand-new transactions + 2 corrections of rows from batch 1:
  T1013 had a blank amount (was quarantined) -> now has an amount
  T1019 had status FAILED and broken JSON    -> now SUCCESS with valid JSON

Run from the project root:  python src/generate_batch2.py
Output: data/raw_transactions_batch2.csv
"""
import csv
from pathlib import Path

from generate_data import COLUMNS, C1, C2, C3, C4, C5, C6, row

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw_transactions_batch2.csv"

ROWS = [
    # corrections
    row("T1013", C3, "05/11/2026", "₹1,850.00", "INR", "Flipkart", "Shopping", "CARD", "SUCCESS", '{"city":"Delhi","device":"android"}'),
    row("T1019", C6, "05/11/2026 11:30", "₹899.00", "INR", "Uber", "Travel", "CARD", "SUCCESS", '{"city":"Pune","device":"android"}'),
    # new transactions
    row("T1020", C2, "04/11/2026 19:45", "₹649.00", "INR", "swiggy", "Food", "UPI", "SUCCESS", '{"city":"Bengaluru","device":"android"}'),
    row("T1021", C4, "04/11/2026 20:10", "₹2,150.00", "INR", "AMAZN", "Shopping", "CARD", "SUCCESS", '{"city":"Pune","device":"web"}'),
    row("T1022", C1, "05/11/2026 09:30", "$15.99", "usd", "Spotify", "Entertainment", "CARD", "SUCCESS", '{"city":"Mumbai","device":"android"}'),
    row("T1023", C5, "05/11/2026 13:15", "₹320.00", "INR", "Zomato", "Food", "UPI", "SUCCESS", '{"city":"Chennai","device":"android"}'),
    row("T1024", C3, "03/11/2026 17:00", "(1,200.00)", "INR", "Croma", "Electronics", "CARD", "REFUNDED", '{"city":"Delhi","device":"pos"}'),
]


def main():
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        w.writerows(ROWS)
    print(f"Wrote {len(ROWS)} rows to {OUT}")


if __name__ == "__main__":
    main()