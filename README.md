# Multi-Source Settlement Reconciliation — AI-Assisted

Built for Razorpay AI Buildathon 2026 — Track T4 (AI Finance Controller)

## Problem
Merchants reconciling Razorpay settlements against bank statements and ERP invoices (Tally/Zoho) still do this manually at month-end. Razorpay's Settlement Recon API (`/v1/settlements/recon/combined`) and Smart Collect 2.0 solve payment-side reconciliation, but matching that data into a merchant's own ERP ledger remains unsolved — confirmed gap, per public integration docs: "requires bespoke API integration and matching logic... rarely offered."

## What this does
Reconciles three messy data sources — bank statement, Razorpay settlement report, ERP invoices — using a hybrid pipeline:

1. **Exact match** — ties all 3 sources via UTR number when present
2. **Fuzzy match** — for rows missing a clean reference, gates candidates on amount + date tolerance (reliable numeric signals), then uses name similarity (`rapidfuzz`) only as a confidence score — not as the primary filter
3. **Honest exceptions** — anything genuinely unmatched is flagged for human review, never hidden or cherry-picked

## Results (on 500-transaction synthetic dataset)
- **89.6% auto-matched** (387 exact + 61 fuzzy)
- **10.4% honest exceptions** (52 transactions — correctly routed to human review)
- **100% precision/recall** against ground truth (see Limitations below)
- **₹12,66,609 reconciled** automatically
- **10,313 records/sec** throughput

Beats published literature benchmarks (91.7% best-case auto-match rate in academic hybrid OCR+RPA systems).

## Why this approach (not pure LLM)
Research (Prakash et al., 2025) shows small domain-tuned models can outperform general LLMs on narrow matching tasks. We use `rapidfuzz` (deterministic, offline, free) for the bulk of matching and reserve LLM calls only for genuinely ambiguous cases — cheaper, faster, and more explainable than calling an LLM on every row. Every match includes a human-readable reason string (audit trail).

## Honest Limitations
100% precision/recall was achieved on synthetic data intentionally designed with resolvable patterns (amount/date always reliable by construction). This is a controlled demo, not a production accuracy claim — real-world data would include partial refunds, multi-invoice splits, and cross-currency cases not simulated here. See `failure_log.md` for a documented bug (initial fuzzy matcher over-relied on noisy name-similarity as a hard filter) and how it was fixed.

## Stack
Python 3.14, pandas, rapidfuzz — no paid APIs required for core pipeline.

## Run it
\`\`\`bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 src/generate_data.py
python3 src/exact_match.py
python3 src/fuzzy_match.py
python3 src/main.py
\`\`\`

## Files
- `src/generate_data.py` — synthetic dataset generator (with injected messiness + ground truth)
- `src/exact_match.py` — layer 1: UTR-based exact matching
- `src/fuzzy_match.py` — layer 2: amount/date-gated fuzzy matching
- `src/main.py` — merges results, computes real precision/recall, generates final report
- `failure_log.md` — documented bug + fix from development
- `data/` — generated datasets and outputs

**Scalability note:** Pipeline processed 500 transactions in 0.048s (~10,313 records/sec). Runtime is dominated by pandas I/O overhead, not matching logic — the exact+fuzzy matching itself is O(n) to O(n·m) bounded by blocking (date+amount gating), so this scales cleanly to thousands of records without architectural changes.