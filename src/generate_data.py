"""Generate the FinFlow raw (messy) transactions file.

Step 2 version: 20 hand-crafted rows so every cleaning rule can be checked by eye.
Run from the project root:  python src/generate_data.py
Output: data/raw_transactions.csv
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw_transactions.csv"

COLUMNS = [
    "txn_id", "customer_id", "account_no", "card_no", "email", "txn_date",
    "amount", "currency", "merchant", "category", "channel", "status", "meta_json",
]

# Fake customers (all synthetic). Card numbers are well-known test numbers.
C1 = ("C001", "ACC1001", "4111111111111111", "rahul.sharma@gmail.com")
C2 = ("C002", "ACC1002", "5500-0000-0000-0004", "priya.nair@yahoo.com")
C3 = ("C003", "ACC1003", "340000000000009", "amit.verma@outlook.com")
C4 = ("C004", "ACC1004", "4012 8888 8888 1881", "sneha.iyer@gmail.com")
C5 = ("C005", "ACC1005", "", "karan.mehta@@gmail.com")  # UPI user, bad email
C6 = ("C006", "ACC1006", "6011111111111117", "neha.gupta@gmail.com")


def row(txn_id, cust, date, amount, cur, merchant, category, channel, status, meta):
    cid, acc, card, email = cust
    return [txn_id, cid, acc, card, email, date, amount, cur, merchant,
            category, channel, status, meta]


ROWS = [
    # 1-2: exact duplicate of T1001
    row("T1001", C1, "03/11/2026 10:15", "₹1,200.50", "inr", "swiggy", "Food", "UPI", "SUCCESS", '{"city":"Mumbai","device":"android"}'),
    row("T1001", C1, "03/11/2026 10:15", "₹1,200.50", "inr", "swiggy", "Food", "UPI", "SUCCESS", '{"city":"Mumbai","device":"android"}'),
    # 3: accounting-style negative amount, abbreviated merchant, lowercase status
    row("T1002", C2, "2026-11-04", "(500)", "INR", "AMAZN", "Shopping", "CARD", "success", '{"city":"Bengaluru","device":"web"}'),
    # 4: text month date, NULL merchant, blank category, mixed-case currency
    row("T1003", C3, "5 Nov 2026", "2,300", "Inr", "NULL", "", "card", "SUCCESS", '{"city":"Delhi","device":"ios"}'),
    # 5: dashes in date
    row("T1004", C4, "04-11-2026", "₹75.00", "INR", "Zomato", "Food", "UPI", "SUCCESS", '{"city":"Pune","device":"android"}'),
    # 6: invalid amount -> quarantine
    row("T1005", C5, "02/11/2026", "abc", "INR", "Uber", "Travel", "UPI", "SUCCESS", '{"city":"Chennai","device":"android"}'),
    # 7: impossible date (31 Feb) -> quarantine
    row("T1006", C2, "31/02/2026", "999.00", "INR", "Myntra", "Shopping", "CARD", "SUCCESS", '{"city":"Bengaluru","device":"web"}'),
    # 8-10: foreign currency (needs the FX seed in dbt)
    row("T1007", C1, "01/11/2026 21:40", "$120.00", "usd", "Netflix", "Entertainment", "CARD", "SUCCESS", '{"city":"Mumbai","device":"tv"}'),
    row("T1008", C3, "02/11/2026 09:05", "80.00", "EUR", "Booking.com", "Travel", "CARD", "SUCCESS", '{"city":"Delhi","device":"web"}'),
    row("T1009", C5, "03/11/2026 18:30", "45", "Usd", "spotify", "Entertainment", "UPI", "SUCCESS", '{"city":"Chennai","device":"android"}'),
    # 11-12: misspelled / mixed-case merchant
    row("T1010", C4, "04/11/2026 08:20", "₹350.00", "INR", "Starbuks", "Food", "CARD", "SUCCESS", '{"city":"Pune","device":"pos"}'),
    row("T1011", C6, "04/11/2026 08:45", "₹420.00", "INR", "STARBUCKS", "Food", "CARD", "SUCCESS", '{"city":"Pune","device":"pos"}'),
    # 13: refund (negative), status REFUNDED
    row("T1012", C2, "2026-11-05", "-250", "INR", "Myntra", "Shopping", "CARD", "REFUNDED", '{"city":"Bengaluru","device":"web"}'),
    # 14: blank amount -> quarantine
    row("T1013", C3, "05/11/2026", "", "INR", "Flipkart", "Shopping", "CARD", "pending", '{"city":"Delhi","device":"android"}'),
    # 15: Indian digit grouping
    row("T1014", C6, "03/11/2026 16:10", "₹1,05,000.00", "INR", "croma", "Electronics", "CARD", "SUCCESS", '{"city":"Hyderabad","device":"pos"}'),
    # 16: FRAUD pattern 1 - very large amount
    row("T1015", C4, "05/11/2026 02:11", "₹4,85,000.00", "INR", "Tanishq", "Jewellery", "CARD", "SUCCESS", '{"city":"Pune","device":"pos"}'),
    # 17-18: FRAUD pattern 2 - same card, Mumbai then Delhi, 7 minutes apart
    row("T1016", C1, "03/11/2026 14:05", "₹2,499.00", "INR", "Apple Store", "Electronics", "CARD", "SUCCESS", '{"city":"Mumbai","device":"pos"}'),
    row("T1017", C1, "03/11/2026 14:12", "₹18,999.00", "INR", "Reliance Digital", "Electronics", "CARD", "SUCCESS", '{"city":"Delhi","device":"pos"}'),
    # 19: UPI, no card, NULL email
    row("T1018", ("C007", "ACC1007", "", ""), "04/11/2026 12:00", "150", "INR", "paytm", "Utilities", "UPI", "SUCCESS", '{"city":"Jaipur","device":"android"}'),
    # 20: broken JSON, failed status
    row("T1019", C6, "05/11/2026 11:30", "₹899.00", "INR", "Uber", "Travel", "CARD", "FAILED", '{city: Pune, device:'),
]


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # plain utf-8 (no BOM) so Spark does not glue a BOM onto the first column name
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        w.writerows(ROWS)
    print(f"Wrote {len(ROWS)} rows to {OUT}")


if __name__ == "__main__":
    main()