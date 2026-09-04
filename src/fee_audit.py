import pandas as pd
import time

FEE_RATE = 0.025   # 2.5% of order_amount, per contracted rate card
GST_RATE = 0.18    # 18% of fee
TOLERANCE = 0.50   # ₹0.50 tolerance, matches real-world rounding norms

def load_data():
    return pd.read_csv("data/razorpay_settlement.csv")

FLAGGED_COLUMNS = [
    "settlement_id", "payment_id", "customer_name", "order_amount", "expected_fee",
    "actual_fee", "fee_diff", "expected_gst", "actual_gst", "gst_diff", "leakage", "reason"
]
CLEAN_COLUMNS = ["settlement_id", "reason"]

def audit_fees(rzp, fee_rate=FEE_RATE, gst_rate=GST_RATE, tolerance=TOLERANCE):
    rzp = rzp.copy()
    rzp["expected_fee"] = (rzp["order_amount"] * fee_rate).round(2)
    rzp["expected_gst"] = (rzp["expected_fee"] * gst_rate).round(2)
    rzp["fee_diff"] = (rzp["fee"] - rzp["expected_fee"]).round(2)
    rzp["gst_diff"] = (rzp["gst"] - rzp["expected_gst"]).round(2)

    flagged_rows = []
    clean_rows = []

    for _, row in rzp.iterrows():
        fee_off = abs(row["fee_diff"]) > tolerance
        gst_off = abs(row["gst_diff"]) > tolerance

        if fee_off or gst_off:
            reasons = []
            if fee_off:
                reasons.append(f"fee off by ₹{row['fee_diff']:.2f} (expected ₹{row['expected_fee']:.2f}, actual ₹{row['fee']:.2f})")
            if gst_off:
                reasons.append(f"GST off by ₹{row['gst_diff']:.2f} (expected ₹{row['expected_gst']:.2f}, actual ₹{row['gst']:.2f})")

            flagged_rows.append({
                "settlement_id": row["settlement_id"],
                "payment_id": row["payment_id"],
                "customer_name": row["customer_name"],
                "order_amount": row["order_amount"],
                "expected_fee": row["expected_fee"],
                "actual_fee": row["fee"],
                "fee_diff": row["fee_diff"],
                "expected_gst": row["expected_gst"],
                "actual_gst": row["gst"],
                "gst_diff": row["gst_diff"],
                "leakage": round(row["fee_diff"] + row["gst_diff"], 2),
                "reason": "; ".join(reasons) + f" — exceeds ₹{tolerance:.2f} tolerance"
            })
        else:
            clean_rows.append({
                "settlement_id": row["settlement_id"],
                "reason": "Fee and GST match rate-card expectation within tolerance."
            })

    return pd.DataFrame(flagged_rows, columns=FLAGGED_COLUMNS), pd.DataFrame(clean_rows, columns=CLEAN_COLUMNS)

if __name__ == "__main__":
    start_time = time.time()

    rzp = load_data()
    flagged, clean = audit_fees(rzp)

    total_leakage = flagged["leakage"].sum() if len(flagged) else 0.0

    print("=" * 50)
    print("FEE / GST SPLIT AUDIT")
    print("=" * 50)
    print(f"Total settlements audited: {len(rzp)}")
    print(f"Clean (within ₹{TOLERANCE:.2f} tolerance): {len(clean)} ({len(clean)/len(rzp)*100:.1f}%)")
    print(f"Flagged discrepancies: {len(flagged)} ({len(flagged)/len(rzp)*100:.1f}%)")
    print(f"Total leakage detected: ₹{total_leakage:,.2f}")
    print("=" * 50)

    flagged.to_csv("data/fee_audit_flagged.csv", index=False)

    elapsed = time.time() - start_time
    throughput = len(rzp) / elapsed if elapsed > 0 else 0
    print(f"Processing time: {elapsed:.3f}s | Throughput: {throughput:.1f} records/sec")
    print("Saved: data/fee_audit_flagged.csv")
