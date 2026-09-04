"""Plain assert-based tests for src/refund_allocator.py. Run: python3 tests/test_refund_allocator.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from src.refund_allocator import allocate_refunds


def make_settlement(settlement_id, order_amount, fee, gst, net_amount, order_id="order_test"):
    return {
        "settlement_id": settlement_id,
        "payment_id": "pay_test",
        "order_id": order_id,
        "customer_name": "Test Customer",
        "order_amount": order_amount,
        "fee": fee,
        "gst": gst,
        "net_amount": net_amount,
        "settlement_date": "2026-08-01",
        "utr_ref": "UTR_TEST",
    }


def make_refund(refund_id, settlement_id, refund_amount, refund_type="partial"):
    return {
        "refund_id": refund_id,
        "payment_id": "pay_test",
        "settlement_id": settlement_id,
        "refund_amount": refund_amount,
        "refund_date": "2026-08-05",
        "refund_type": refund_type,
    }


def test_full_refund_reverses_everything():
    rzp = pd.DataFrame([make_settlement("stl_1", 1000.0, 25.0, 4.5, 970.5)])
    refunds = pd.DataFrame([make_refund("rfnd_1", "stl_1", 1000.0, "full")])

    journal, exceptions = allocate_refunds(refunds, rzp)

    assert len(exceptions) == 0
    assert len(journal) == 1
    row = journal.iloc[0]
    assert row["refund_ratio"] == 1.0
    assert row["allocated_fee_reversal"] == 25.0
    assert row["allocated_gst_reversal"] == 4.5
    assert row["allocated_net_reversal"] == 970.5


def test_partial_refund_prorates_correctly():
    rzp = pd.DataFrame([make_settlement("stl_2", 1000.0, 25.0, 4.5, 970.5)])
    refunds = pd.DataFrame([make_refund("rfnd_2", "stl_2", 500.0, "partial")])

    journal, exceptions = allocate_refunds(refunds, rzp)

    assert len(exceptions) == 0
    row = journal.iloc[0]
    assert row["refund_ratio"] == 0.5
    assert row["allocated_fee_reversal"] == 12.5
    assert row["allocated_gst_reversal"] == 2.25
    assert row["allocated_net_reversal"] == 485.25


def test_zero_order_amount_gives_zero_ratio_not_divide_error():
    rzp = pd.DataFrame([make_settlement("stl_3", 0.0, 0.0, 0.0, 0.0)])
    refunds = pd.DataFrame([make_refund("rfnd_3", "stl_3", 0.0, "full")])

    journal, exceptions = allocate_refunds(refunds, rzp)

    assert len(exceptions) == 0
    row = journal.iloc[0]
    assert row["refund_ratio"] == 0


def test_missing_settlement_routed_to_exceptions():
    rzp = pd.DataFrame([make_settlement("stl_4", 1000.0, 25.0, 4.5, 970.5)])
    refunds = pd.DataFrame([make_refund("rfnd_4", "stl_does_not_exist", 500.0)])

    journal, exceptions = allocate_refunds(refunds, rzp)

    assert len(journal) == 0
    assert len(exceptions) == 1
    assert exceptions.iloc[0]["refund_id"] == "rfnd_4"


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
