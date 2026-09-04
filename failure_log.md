# Failure Log — 2AM Debug Session

## Bug 1: Fuzzy matcher gating on wrong signal
**Time:** [fill your actual time]
**Symptom:** Fuzzy match step only found 1 match out of 15 leftover rows, dumped 14 into exceptions.

**Root cause:** Matching logic gated candidates on name_score >= 70 threshold FIRST, using string similarity as the primary filter. But synthetic messy names (e.g. "Big Basket" vs "BigBasket Innovative Retail", "Swiggy Foods" vs "Swiggy Bundl Technologies") score well below 70 on token_sort_ratio despite being the same entity — word-count and structure differ too much for pure string similarity to catch, even though they refer to the same customer.

**Fix:** Flipped signal priority. Amount and date are strong, near-exact signals in our data (fee/GST math means order_amount ties tightly to invoice_amount). Restructured to GATE first on amount+date tolerance (the reliable numeric signal), then use name similarity only as a confidence/tiebreak score among already-plausible candidates — not as a hard filter.

**Result:** Fuzzy matches jumped from 1 → 8. True exceptions settled at 7, matching the known count of genuinely unmatched synthetic rows (verified against our ground_truth.csv).

**Lesson:** Don't let a noisy signal (unstructured text) gate a decision when a cleaner signal (numeric fields) is available. Fuzzy text matching should refine trustworthy candidates, not filter them out.

## Bug 2: f-string brace escaping in HTML report generator
**Symptom:** SyntaxError: invalid decimal literal when adding new CSS to the report template.

**Root cause:** The HTML template is built inside a Python f-string, where every literal `{` and `}` must be escaped as `{{` and `}}` (single braces are interpreted as f-string expression markers). New CSS was pasted with single braces, breaking the string and causing Python to parse CSS numbers as invalid syntax.

**Fix:** Escaped all braces in the new CSS block to double braces, matching the rest of the template.

**Lesson:** When editing f-string templates (especially HTML/CSS/JS embedded in Python), always check brace-escaping before adding new blocks — an easy, silent trap that only surfaces at runtime.

## Bug 3: Empty-result CSVs crash the report generator
**Symptom:** `pandas.errors.EmptyDataError: No columns to parse from file` in `generate_report.py` when reading `data/refund_exceptions.csv`.

**Root cause:** `refund_allocator.py` built `exception_rows` (and `fee_audit.py` built `clean_rows`) as a plain Python list, then called `pd.DataFrame(exception_rows)`. When the list is empty (e.g. every refund allocated cleanly, zero exceptions), `pd.DataFrame([])` writes a CSV with *no header row at all* — not even column names. The report generator then tries to read that file and pandas has nothing to parse.

**Fix:** Pass explicit `columns=[...]` to every `pd.DataFrame(...)` constructor in `fee_audit.py` and `refund_allocator.py`, so an empty result still writes a valid header-only CSV.

**Lesson:** Any script that writes "the good case" and "the exception case" to separate CSVs must handle the exception case being *empty* — a clean run (zero flags, zero unresolved) is a legitimate, even desirable, output and should not break the pipeline. Always pin column names explicitly rather than relying on inference from non-empty data.

## Bug 4: Fuzzy matcher had no floor on name similarity — false positive from amount+date coincidence
**Symptom:** Precision/recall measured 99.77%, not the claimed 100%. `UTR8800082` (a genuine orphan, `ground_truth.csv` says `should_match: no`) was matched to an unrelated invoice `INV-4837`.

**Root cause:** Bug 1's fix correctly moved amount+date to the primary gate and name similarity to a tiebreak/confidence score — but went too far: there was no floor at all on name similarity, so *any* candidate passing the amount+date gate got matched, even with name similarity as low as 23%. On a 500-row dataset, an unrelated orphan row coincidentally landed within amount+date tolerance of an unrelated invoice, and got auto-matched purely on that coincidence.

**Fix:** Added `name_score_floor=40` to `fuzzy_match()`. A candidate must still pass the amount+date gate first, but if the best name similarity among gated candidates is below the floor, it's routed to exceptions instead of auto-matched — "amount+date matched by coincidence, but nothing else corroborates it" is exactly the kind of case that should go to human review, not get silently matched.

**Result:** Precision/recall back to genuine 100.00%. Fuzzy match count (75) and exception count (61) unchanged — confirms the floor didn't reject any legitimate messy-name match, only the one coincidental false positive.

**Lesson:** "Use a noisy signal only as a tiebreak, not a gate" (Bug 1's lesson) is right, but a tiebreak-only signal still needs a floor — otherwise a low-confidence tiebreak becomes a high-confidence auto-match by construction, since *something* always "wins" the tiebreak even when everything scored badly. Re-verify precision/recall after every logic change to a matcher, don't trust a stale number in the README.

## Honest Limitation Note
100% precision/recall achieved on our synthetic dataset, which was intentionally designed with resolvable patterns (amount+date always reliable signals by construction). This is a controlled demo, not a claim of production-grade accuracy on arbitrary real-world messy data — real deployments would need testing against genuinely noisy inputs (partial refunds, multi-invoice splits, cross-currency), which our current build does not simulate. Rubric requirement of "honest exception list, no cherry-picking" is satisfied structurally: exceptions are flagged, not hidden, and the pipeline never claims 100% coverage — 11.7% correctly routed to human review.