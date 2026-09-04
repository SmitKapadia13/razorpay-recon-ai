# Project: Razorpay AI Buildathon — Multi-Loop Finance Reconciliation Tool

## Context
Solo dev, hackathon deadline Sept 5 2026. Track: T4 (AI Finance Controller).
Prize: ₹75k/mo AI Builder Internship at Razorpay, Bangalore.

## The 4 Selection Rules (always apply when proposing new features/ideas)
1. Uncommon problems — avoid crowded/hyped areas, pick low-competition angles
2. Clear direction — must have simple input→process→output before building
3. Verify not already solved — check for existing tools/APIs covering it first
4. Gut check — must feel "big + genuinely helpful," not a toy feature

## Rubric (T4 track requirements — build must satisfy these)
- Close finance-ops loop across 50+ record synthetic batch
- Measured accuracy (real precision/recall, not estimated)
- Measured throughput
- Honest exception list — NEVER cherry-pick or hide unmatched/flagged rows
- Compliant escalation path (clear human-review routing)
- Audit trail (every automated decision needs a human-readable reason)

## Project Concept — Three Closed Loops, One Pipeline
Single codebase solving THREE related finance-ops problems using the same core synthetic dataset:

### PS1 — Multi-Source Settlement Reconciliation (DONE, working)
Problem: Razorpay settlement data, bank statements, and ERP invoices use different identifiers/naming — matching them across all 3 sources is manual today (confirmed gap: ERP integration "requires bespoke API integration... rarely offered").
Solution: Exact match by UTR first (deterministic) → fuzzy match remaining by amount+date gating (NOT name-gating — name similarity used only as confidence score, not filter) → honest exception list for anything unmatched.
Status: Built, tested at 500 records, 89.6% auto-match rate, 100% precision/recall vs ground truth.

### PS2 — Fee/GST Split Auditor (DONE, working)
Problem: Razorpay tells merchants what fee/GST was deducted from settlement, but nothing verifies that deduction was actually CORRECT per the contracted rate card. Silent leakage possible (rate card bugs, promo pricing not reverted, etc).
Solution: Recompute expected fee (2.5% of order) + GST (18% of fee) per known rate card, compare against actual deducted values, flag discrepancies beyond ₹0.50 tolerance, sum total ₹ leakage found.
Status: Built (`src/fee_audit.py`). 500 settlements audited, 2.8% flagged, ₹54.66 total leakage detected. Outputs `data/fee_audit_flagged.csv`.

### PS3 — Partial Refund Allocator (DONE, working)
Problem: When a partial refund happens, fee/GST/net must be split proportionally and tied back to the ORIGINAL invoice — this is manual ratio math today, easy to get wrong, no tool automates it.
Solution: For each refund event, compute refund_ratio = refund_amount / original_order_amount, split fee/gst/net proportionally, generate a ledger-ready journal entry tied to the original settlement_id/invoice.
Status: Built (`src/refund_allocator.py`). 18 refund events, 100% allocated, ₹36,781.25 net reversed. Outputs `data/refund_journal.csv` + `data/refund_exceptions.csv`.

## Tech Stack
- Python 3.14, pandas, rapidfuzz (fuzzy string matching), python-dotenv
- No paid APIs required for core pipeline (rule-based first, LLM reserved for edge cases only — was a deliberate AI-judgment decision, not yet implemented as optional bonus)
- Virtual env: `venv/` (activate with `source venv/bin/activate`)
- Gemini API key available in `.env` as `GEMINI_API_KEY` if LLM escalation layer gets added later

## File Structure
razorpay-recon-ai/
├── data/ # generated datasets + outputs (gitignored generation, tracked outputs)
│ ├── bank_statement.csv
│ ├── razorpay_settlement.csv # has fee/gst columns, ~4% have injected glitches for PS2
│ ├── erp_invoices.csv
│ ├── ground_truth.csv # our own answer key for real precision/recall
│ ├── refunds.csv # NEW: refund events for PS3, mix full/partial
│ ├── exact_matches.csv, fuzzy_matches.csv, leftover_for_fuzzy.csv, exceptions.csv
│ ├── final_matched_report.csv, final_exceptions_report.csv
│ └── reconciliation_report.html # visual dashboard, clickable stat cards
├── src/
│ ├── generate_data.py # synthetic data generator, seed=42, NUM_TRANSACTIONS=500
│ ├── exact_match.py # PS1 layer 1: UTR-based exact match
│ ├── fuzzy_match.py # PS1 layer 2: amount+date gated fuzzy match (rapidfuzz)
│ ├── main.py # PS1: merges results, computes real precision/recall, throughput
│ ├── generate_report.py # builds HTML dashboard from PS1 outputs
│ ├── run_all.py # chains all pipeline steps in one command
│ ├── fee_audit.py # PS2: NOT YET BUILT — needs creation
│ └── refund_allocator.py # PS3: NOT YET BUILT — needs creation
├── failure_log.md # 2 real bugs documented so far (fuzzy-match gating bug, f-string brace escaping bug)
├── README.md
├── requirements.txt
└── .env # GEMINI_API_KEY (gitignored)


## Known Bugs Already Fixed (see failure_log.md for full writeups)
1. Fuzzy matcher initially gated on name_score first (wrong — noisy signal), fixed to gate on amount+date first (reliable), use name only as confidence tiebreak.
2. f-string brace escaping bug in HTML report generator — all literal `{` `}` in the f-string template must be doubled `{{` `}}` or Python throws SyntaxError.

## Design Principles To Maintain
- Rule-based/deterministic matching ALWAYS preferred over LLM calls where possible — cheaper, faster, more explainable, directly satisfies rubric's "know when NOT to use AI" criterion
- Every automated match/flag needs a human-readable `reason` string — non-negotiable, this is the audit trail
- NEVER hide or cherry-pick exceptions — always output the full honest list, even if it makes numbers look less perfect
- Fee audit tolerance: ₹0.50 (matches real-world rounding norms, avoids noise flagging)
- Ground truth files exist so we can report REAL precision/recall, not estimated — this beats most published literature which uses unsupervised estimation

## Immediate Next Steps
All of PS1/PS2/PS3 are built, wired into `run_all.py`, and reflected in the HTML report + README as of 2026-09-05. Remaining:
1. Commit + push (git remote already configured: `https://github.com/SmitKapadia13/razorpay-recon-ai`)
2. LAST — record 5-min pitch video (not started, do after commit)

## Communication Style Note
User prefers terse, direct instructions — no fluff, no hedging, technical content stays exact/verbatim. Confirm outputs before moving to next step. This isn't a formatting requirement for CLAUDE.md itself, just context on how the user likes to work.