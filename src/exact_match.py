import pandas as pd

def load_data():
    bank = pd.read_csv("data/bank_statement.csv")
    rzp = pd.read_csv("data/razorpay_settlement.csv")
    erp = pd.read_csv("data/erp_invoices.csv")
    return bank, rzp, erp

def exact_match(bank, rzp, erp):
    # Step A: bank <-> rzp settlement, match on UTR (always present both sides)
    bank_rzp = bank.merge(rzp, left_on="utr_number", right_on="utr_ref", how="left", suffixes=("_bank", "_rzp"))

    results = []
    unmatched_for_fuzzy = []

    for _, row in bank_rzp.iterrows():
        utr = row["utr_number"]
        erp_row = erp[erp["payment_ref"] == utr]

        if not erp_row.empty:
            # FULL EXACT MATCH — all 3 sources tied by UTR
            erp_row = erp_row.iloc[0]
            results.append({
                "utr_number": utr,
                "settlement_id": row["settlement_id"],
                "invoice_no": erp_row["invoice_no"],
                "match_type": "exact",
                "confidence": 1.0,
                "reason": "UTR matched across bank, Razorpay settlement, and ERP invoice."
            })
        else:
            # bank+rzp matched, but ERP has no UTR ref — needs fuzzy pass
            unmatched_for_fuzzy.append({
                "utr_number": utr,
                "settlement_id": row["settlement_id"],
                "customer_name": row["customer_name"],
                "order_amount": row["order_amount"],
                "settlement_date": row["settlement_date"]
            })

    return pd.DataFrame(results), pd.DataFrame(unmatched_for_fuzzy)

if __name__ == "__main__":
    bank, rzp, erp = load_data()
    exact_results, leftover = exact_match(bank, rzp, erp)

    print(f"Exact matches: {len(exact_results)}")
    print(f"Leftover for fuzzy matching: {len(leftover)}")

    exact_results.to_csv("data/exact_matches.csv", index=False)
    leftover.to_csv("data/leftover_for_fuzzy.csv", index=False)
    print("Saved: data/exact_matches.csv, data/leftover_for_fuzzy.csv")