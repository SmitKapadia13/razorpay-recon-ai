import pandas as pd
from rapidfuzz import fuzz

def load_leftover_and_erp():
    leftover = pd.read_csv("data/leftover_for_fuzzy.csv")
    erp = pd.read_csv("data/erp_invoices.csv")

    # only ERP rows NOT already used in exact match (blank payment_ref = still candidates)
    erp_candidates = erp[erp["payment_ref"].isna() | (erp["payment_ref"] == "")]
    return leftover, erp_candidates

def fuzzy_match(leftover, erp_candidates, amount_tolerance=1.0, date_tolerance_days=3):
    matched_rows = []
    exception_rows = []
    used_invoices = set()

    for _, row in leftover.iterrows():
        best_name_score = -1
        best_invoice = None
        best_amount_diff = None
        best_date_diff = None

        for _, erp_row in erp_candidates.iterrows():
            if erp_row["invoice_no"] in used_invoices:
                continue

            amount_diff = abs(row["order_amount"] - erp_row["invoice_amount"])
            date_diff = abs((pd.to_datetime(row["settlement_date"]) - pd.to_datetime(erp_row["invoice_date"])).days)

            # GATE on strong signals: amount must be near-exact, date must be close
            if amount_diff <= amount_tolerance and date_diff <= date_tolerance_days:
                name_score = fuzz.token_sort_ratio(row["customer_name"], erp_row["customer_name"])
                # among amount+date candidates, pick best name score (tiebreak/confidence only)
                if name_score > best_name_score:
                    best_name_score = name_score
                    best_invoice = erp_row
                    best_amount_diff = amount_diff
                    best_date_diff = date_diff

        if best_invoice is not None:
            confidence = round(max(0.5, best_name_score / 100), 2)
            matched_rows.append({
                "utr_number": row["utr_number"],
                "settlement_id": row["settlement_id"],
                "invoice_no": best_invoice["invoice_no"],
                "match_type": "fuzzy",
                "confidence": confidence,
                "reason": f"Amount matched (diff ₹{best_amount_diff:.2f}), date diff {best_date_diff}d, name similarity {best_name_score:.0f}%"
            })
            used_invoices.add(best_invoice["invoice_no"])
        else:
            exception_rows.append({
                "utr_number": row["utr_number"],
                "settlement_id": row["settlement_id"],
                "customer_name": row["customer_name"],
                "order_amount": row["order_amount"],
                "settlement_date": row["settlement_date"],
                "reason": "No ERP invoice found matching amount+date within tolerance."
            })

    return pd.DataFrame(matched_rows), pd.DataFrame(exception_rows)

if __name__ == "__main__":
    leftover, erp_candidates = load_leftover_and_erp()
    fuzzy_results, exceptions = fuzzy_match(leftover, erp_candidates)

    print(f"Fuzzy matches: {len(fuzzy_results)}")
    print(f"True exceptions (unmatched): {len(exceptions)}")

    fuzzy_results.to_csv("data/fuzzy_matches.csv", index=False)
    exceptions.to_csv("data/exceptions.csv", index=False)
    print("Saved: data/fuzzy_matches.csv, data/exceptions.csv")