import pandas as pd
import random
from datetime import datetime, timedelta

random.seed(42)  # reproducible results

# ---- CONFIG ----
NUM_TRANSACTIONS = 500

customers = [
    ("Amazon Pvt Ltd", "AMZN-PAY", "Amazon India"),
    ("Flipkart Internet Pvt Ltd", "FLPKRT", "Flipkart"),
    ("Swiggy Bundl Technologies", "SWIGGY", "Swiggy Foods"),
    ("Zomato Ltd", "ZOMATO", "Zomato Media"),
    ("Reliance Retail Ltd", "RELNCE", "Reliance Digital"),
    ("Myntra Designs Pvt Ltd", "MYNTRA", "Myntra Jabong"),
    ("BigBasket Innovative Retail", "BIGBSKT", "Big Basket"),
    ("Nykaa E-Retail Pvt Ltd", "NYKAA", "Nykaa Fashion"),
]

bank_rows, rzp_rows, erp_rows, truth_rows = [], [], [], []

start_date = datetime(2026, 8, 1)

for i in range(1, NUM_TRANSACTIONS + 1):
    cust_erp_name, cust_bank_code, cust_alt_name = random.choice(customers)
    order_amount = round(random.uniform(500, 5000), 2)
    fee = round(order_amount * 0.025, 2)
    gst = round(fee * 0.18, 2)
    net_amount = round(order_amount - fee - gst, 2)

    txn_date = start_date + timedelta(days=random.randint(0, 20))
    settle_date = txn_date + timedelta(days=1)
    invoice_date = txn_date - timedelta(days=random.randint(0, 2))

    utr = f"UTR{8800000 + i}"
    payment_id = f"pay_{29000 + i}xA"
    order_id = f"order_{88000 + i}x"
    settlement_id = f"stl_{i:03d}"
    invoice_no = f"INV-{4500 + i}"

    # decide row type: clean match / messy match / orphan
    roll = random.random()

    if roll < 0.75:
        # CLEAN MATCH — exact everything
        bank_rows.append([txn_date.date(), utr, f"NEFT CR {cust_bank_code}", net_amount, "CR"])
        rzp_rows.append([settlement_id, payment_id, order_id, cust_erp_name, order_amount, fee, gst, net_amount, settle_date.date(), utr])
        erp_rows.append([invoice_no, cust_erp_name, order_amount, invoice_date.date(), utr])
        truth_rows.append([utr, settlement_id, invoice_no, "yes"])

    elif roll < 0.90:
        # MESSY MATCH — name mismatch + rounding diff + missing ref (needs fuzzy)
        rounding_noise = round(random.uniform(-0.5, 0.5), 2)
        bank_rows.append([txn_date.date(), utr, f"NEFT CR {cust_bank_code}", net_amount + rounding_noise, "CR"])
        rzp_rows.append([settlement_id, payment_id, order_id, cust_erp_name, order_amount, fee, gst, net_amount, settle_date.date(), utr])
        erp_rows.append([invoice_no, cust_alt_name, order_amount, invoice_date.date(), ""])  # blank ref, alt name
        truth_rows.append([utr, settlement_id, invoice_no, "yes"])

    else:
        # ORPHAN — genuinely unmatched (no ERP entry, or extra bank row)
        bank_rows.append([txn_date.date(), utr, f"NEFT CR {cust_bank_code}", net_amount, "CR"])
        rzp_rows.append([settlement_id, payment_id, order_id, cust_erp_name, order_amount, fee, gst, net_amount, settle_date.date(), utr])
        # no ERP row added — orphan
        truth_rows.append([utr, settlement_id, "NONE", "no"])

# ---- SAVE FILES ----
pd.DataFrame(bank_rows, columns=["txn_date", "utr_number", "narration", "amount", "type"]).to_csv("data/bank_statement.csv", index=False)

pd.DataFrame(rzp_rows, columns=["settlement_id", "payment_id", "order_id", "customer_name", "order_amount", "fee", "gst", "net_amount", "settlement_date", "utr_ref"]).to_csv("data/razorpay_settlement.csv", index=False)

pd.DataFrame(erp_rows, columns=["invoice_no", "customer_name", "invoice_amount", "invoice_date", "payment_ref"]).to_csv("data/erp_invoices.csv", index=False)

pd.DataFrame(truth_rows, columns=["utr_number", "settlement_id", "invoice_no", "should_match"]).to_csv("data/ground_truth.csv", index=False)

print(f"Generated {NUM_TRANSACTIONS} synthetic transactions.")
print(f"Bank rows: {len(bank_rows)}, RZP rows: {len(rzp_rows)}, ERP rows: {len(erp_rows)}")
print("Files saved in data/ folder.")