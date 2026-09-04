import pandas as pd
import time

def load_all():
    exact = pd.read_csv("data/exact_matches.csv")
    fuzzy = pd.read_csv("data/fuzzy_matches.csv")
    exceptions = pd.read_csv("data/exceptions.csv")
    ground_truth = pd.read_csv("data/ground_truth.csv")
    return exact, fuzzy, exceptions, ground_truth

def build_final_report(exact, fuzzy, exceptions, ground_truth):
    exact["match_type"] = "exact"
    combined = pd.concat([exact[["utr_number", "settlement_id", "invoice_no", "match_type", "confidence", "reason"]],
                          fuzzy[["utr_number", "settlement_id", "invoice_no", "match_type", "confidence", "reason"]]],
                          ignore_index=True)

    total_rows = len(ground_truth)
    matched_rows = len(combined)
    exception_count = len(exceptions)

    # ---- REAL precision/recall against ground truth ----
    gt = ground_truth.set_index("utr_number")

    true_positive = 0
    false_positive = 0
    false_negative = 0

    for _, row in combined.iterrows():
        utr = row["utr_number"]
        predicted_invoice = row["invoice_no"]
        actual = gt.loc[utr, "should_match"]
        actual_invoice = gt.loc[utr, "invoice_no"]

        if actual == "yes" and predicted_invoice == actual_invoice:
            true_positive += 1
        else:
            false_positive += 1  # matched something, but wrong or shouldn't have matched

    for _, row in exceptions.iterrows():
        utr = row["utr_number"]
        actual = gt.loc[utr, "should_match"]
        if actual == "yes":
            false_negative += 1  # should have matched, but we flagged as exception

    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print("=" * 50)
    print("FINAL RECONCILIATION REPORT")
    print("=" * 50)
    print(f"Total transactions: {total_rows}")
    print(f"Auto-matched: {matched_rows} ({matched_rows/total_rows*100:.1f}%)")
    print(f"  - Exact matches: {len(exact)}")
    print(f"  - Fuzzy matches: {len(fuzzy)}")
    print(f"Exceptions (honest, unmatched): {exception_count} ({exception_count/total_rows*100:.1f}%)")
    print("-" * 50)
    print(f"Precision: {precision:.2%}")
    print(f"Recall: {recall:.2%}")
    print(f"F1 Score: {f1:.2%}")
    print("=" * 50)

    combined.to_csv("data/final_matched_report.csv", index=False)
    exceptions.to_csv("data/final_exceptions_report.csv", index=False)
    print("Saved: data/final_matched_report.csv, data/final_exceptions_report.csv")

if __name__ == "__main__":
    start_time = time.time()

    exact, fuzzy, exceptions, ground_truth = load_all()
    build_final_report(exact, fuzzy, exceptions, ground_truth)

    elapsed = time.time() - start_time
    total_records = len(ground_truth)
    throughput = total_records / elapsed if elapsed > 0 else 0
    print(f"Processing time: {elapsed:.3f}s | Throughput: {throughput:.1f} records/sec")