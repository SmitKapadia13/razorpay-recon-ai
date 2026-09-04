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

    # Inject deliberate fee discrepancy in ~4% of rows (simulates gateway rate-card glitch)
    if random.random() < 0.04:
        glitch_amount = round(random.uniform(1.5, 8.0), 2)
        fee = round(fee + glitch_amount, 2)
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

# ---- GENERATE REFUNDS (subset of settled transactions) ----
refund_rows = []
eligible_for_refund = [r for r in rzp_rows if r[4] > 500]  # order_amount > 500, index 4

num_refunds = 18
refund_candidates = random.sample(eligible_for_refund, min(num_refunds, len(eligible_for_refund)))

for idx, rzp_row in enumerate(refund_candidates, 1):
    settlement_id = rzp_row[0]
    payment_id = rzp_row[1]
    order_amount = rzp_row[4]
    fee = rzp_row[5]
    gst = rzp_row[6]
    settlement_date = rzp_row[8]

    refund_id = f"rfnd_{9000 + idx}"

    is_full_refund = random.random() < 0.3  # 30% full, 70% partial
    if is_full_refund:
        refund_amount = order_amount
    else:
        refund_amount = round(order_amount * random.uniform(0.2, 0.7), 2)

    refund_date = pd.to_datetime(str(settlement_date)) + pd.Timedelta(days=random.randint(2, 10))

    refund_rows.append([refund_id, payment_id, settlement_id, refund_amount, refund_date.date(), "full" if is_full_refund else "partial"])

pd.DataFrame(refund_rows, columns=["refund_id", "payment_id", "settlement_id", "refund_amount", "refund_date", "refund_type"]).to_csv("data/refunds.csv", index=False)

print(f"Generated {len(refund_rows)} refund events (mix of full/partial).")

print(f"Generated {NUM_TRANSACTIONS} synthetic transactions.")
print(f"Bank rows: {len(bank_rows)}, RZP rows: {len(rzp_rows)}, ERP rows: {len(erp_rows)}")
print("Files saved in data/ folder.")