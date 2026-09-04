import pandas as pd
import time

def load_data():
    refunds = pd.read_csv("data/refunds.csv")
    rzp = pd.read_csv("data/razorpay_settlement.csv")
    return refunds, rzp

JOURNAL_COLUMNS = [
    "refund_id", "settlement_id", "invoice_ref", "refund_type", "original_order_amount",
    "refund_amount", "refund_ratio", "allocated_fee_reversal", "allocated_gst_reversal",
    "allocated_net_reversal", "refund_date", "reason"
]
EXCEPTION_COLUMNS = ["refund_id", "settlement_id", "reason"]

def allocate_refunds(refunds, rzp):
    rzp_by_settlement = rzp.set_index("settlement_id")

    journal_rows = []
    exception_rows = []

    for _, r in refunds.iterrows():
        settlement_id = r["settlement_id"]

        if settlement_id not in rzp_by_settlement.index:
            exception_rows.append({
                "refund_id": r["refund_id"],
                "settlement_id": settlement_id,
                "reason": "No matching original settlement found — cannot allocate refund."
            })
            continue

        original = rzp_by_settlement.loc[settlement_id]
        order_amount = original["order_amount"]
        original_fee = original["fee"]
        original_gst = original["gst"]
        original_net = original["net_amount"]

        refund_ratio = round(r["refund_amount"] / order_amount, 4) if order_amount else 0

        refund_fee = round(original_fee * refund_ratio, 2)
        refund_gst = round(original_gst * refund_ratio, 2)
        refund_net = round(original_net * refund_ratio, 2)

        journal_rows.append({
            "refund_id": r["refund_id"],
            "settlement_id": settlement_id,
            "invoice_ref": original["order_id"],
            "refund_type": r["refund_type"],
            "original_order_amount": order_amount,
            "refund_amount": r["refund_amount"],
            "refund_ratio": refund_ratio,
            "allocated_fee_reversal": refund_fee,
            "allocated_gst_reversal": refund_gst,
            "allocated_net_reversal": refund_net,
            "refund_date": r["refund_date"],
            "reason": f"Refund ₹{r['refund_amount']:.2f} is {refund_ratio:.1%} of original order ₹{order_amount:.2f} "
                      f"({r['refund_type']}) — fee/GST/net reversed proportionally, tied to settlement {settlement_id}."
        })

    return pd.DataFrame(journal_rows, columns=JOURNAL_COLUMNS), pd.DataFrame(exception_rows, columns=EXCEPTION_COLUMNS)

if __name__ == "__main__":
    start_time = time.time()

    refunds, rzp = load_data()
    journal, exceptions = allocate_refunds(refunds, rzp)

    print("=" * 50)
    print("PARTIAL REFUND ALLOCATOR")
    print("=" * 50)
    print(f"Refund events processed: {len(refunds)}")
    print(f"Journal entries generated: {len(journal)}")
    print(f"Unresolved (no matching settlement): {len(exceptions)}")
    if len(journal):
        print(f"Total fee reversed: ₹{journal['allocated_fee_reversal'].sum():,.2f}")
        print(f"Total GST reversed: ₹{journal['allocated_gst_reversal'].sum():,.2f}")
        print(f"Total net reversed: ₹{journal['allocated_net_reversal'].sum():,.2f}")
    print("=" * 50)

    journal.to_csv("data/refund_journal.csv", index=False)
    exceptions.to_csv("data/refund_exceptions.csv", index=False)

    elapsed = time.time() - start_time
    throughput = len(refunds) / elapsed if elapsed > 0 else 0
    print(f"Processing time: {elapsed:.3f}s | Throughput: {throughput:.1f} records/sec")
    print("Saved: data/refund_journal.csv, data/refund_exceptions.csv")
