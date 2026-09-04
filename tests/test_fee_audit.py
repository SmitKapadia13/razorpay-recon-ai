"""Plain assert-based tests for src/fee_audit.py. Run: python3 tests/test_fee_audit.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from src.fee_audit import audit_fees, FEE_RATE, GST_RATE, TOLERANCE


def make_row(order_amount, fee, gst, settlement_id="stl_test"):
    return {
        "settlement_id": settlement_id,
        "payment_id": "pay_test",
        "customer_name": "Test Customer",
        "order_amount": order_amount,
        "fee": fee,
        "gst": gst,
    }


def test_clean_row_not_flagged():
    order_amount = 1000.0
    fee = round(order_amount * FEE_RATE, 2)
    gst = round(fee * GST_RATE, 2)
    rzp = pd.DataFrame([make_row(order_amount, fee, gst)])

    flagged, clean = audit_fees(rzp)

    assert len(flagged) == 0, f"expected 0 flagged, got {len(flagged)}"
    assert len(clean) == 1, f"expected 1 clean, got {len(clean)}"


def test_real_discrepancy_flagged_with_correct_leakage():
    order_amount = 1000.0
    expected_fee = round(order_amount * FEE_RATE, 2)
    expected_gst = round(expected_fee * GST_RATE, 2)
    actual_fee = round(expected_fee + 5.00, 2)   # well beyond tolerance
    rzp = pd.DataFrame([make_row(order_amount, actual_fee, expected_gst)])

    flagged, clean = audit_fees(rzp)

    assert len(flagged) == 1, f"expected 1 flagged, got {len(flagged)}"
    assert len(clean) == 0
    row = flagged.iloc[0]
    assert row["fee_diff"] == 5.00, f"expected fee_diff 5.00, got {row['fee_diff']}"
    assert row["leakage"] == 5.00, f"expected leakage 5.00, got {row['leakage']}"


def test_zero_order_amount_is_clean():
    rzp = pd.DataFrame([make_row(0.0, 0.0, 0.0)])

    flagged, clean = audit_fees(rzp)

    assert len(flagged) == 0, "zero order/fee/gst should not be flagged"
    assert len(clean) == 1


def test_tiny_order_amount_rounds_to_zero_fee():
    # order_amount so small expected_fee rounds to 0.00 — actual fee of 0.00 should be clean
    order_amount = 0.01
    rzp = pd.DataFrame([make_row(order_amount, 0.0, 0.0)])

    flagged, clean = audit_fees(rzp)

    assert len(flagged) == 0
    assert len(clean) == 1


def test_tolerance_boundary_exact_diff_not_flagged():
    # diff exactly equal to tolerance must NOT be flagged (audit_fees uses strict '>')
    order_amount = 1000.0
    expected_fee = round(order_amount * FEE_RATE, 2)
    expected_gst = round(expected_fee * GST_RATE, 2)
    actual_fee = round(expected_fee + TOLERANCE, 2)  # diff == 0.50 exactly
    rzp = pd.DataFrame([make_row(order_amount, actual_fee, expected_gst)])

    flagged, clean = audit_fees(rzp)

    assert len(flagged) == 0, "diff exactly at tolerance should not be flagged"
    assert len(clean) == 1


def test_tolerance_boundary_just_over_is_flagged():
    order_amount = 1000.0
    expected_fee = round(order_amount * FEE_RATE, 2)
    expected_gst = round(expected_fee * GST_RATE, 2)
    actual_fee = round(expected_fee + TOLERANCE + 0.01, 2)  # diff == 0.51
    rzp = pd.DataFrame([make_row(order_amount, actual_fee, expected_gst)])

    flagged, clean = audit_fees(rzp)

    assert len(flagged) == 1, "diff just over tolerance should be flagged"


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    failures = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL: {t.__name__} — {e}")

    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    sys.exit(1 if failures else 0)
