# 5-Minute Pitch Script — Recon AI (Track T4)

Plain language throughout — no jargon a non-technical judge would have to stop and parse. Each block has a rough time budget; total ~5:00. Bracketed notes are what to show on screen, not what to say.

---

## 1. The problem (0:00 – 0:45)

> Every month, finance teams at companies that use Razorpay have to check three things by hand:
> One — did the money that landed in the bank actually match what Razorpay says it settled, and what the invoice says was billed?
> Two — did Razorpay deduct the *correct* fee and tax, or did something silently overcharge or undercharge?
> Three — when a customer gets a partial refund, who updates the books to split that refund correctly across fee, tax, and the actual amount?

> Today, all three of these are manual, spreadsheet-driven, and error-prone. I built one tool that closes all three loops — and instead of just saying "it works," I'm going to show you the actual numbers, including where it says "I'm not sure, a human should look at this."

[Screen: title slide or terminal, nothing fancy]

---

## 2. What it actually does (0:45 – 1:15)

> It's one pipeline, three checks, run on the same 500 fake-but-realistic transactions:
> **Loop 1** matches bank statement, Razorpay settlement, and ERP invoice records to each other.
> **Loop 2** re-calculates what the fee and GST *should* have been, and flags anything that doesn't match.
> **Loop 3** takes every partial refund and works out exactly how much fee, tax, and net amount needs to be reversed.

> I'll run the whole thing live, then walk through the dashboard it produces.

[Screen: terminal, ready to run]

---

## 3. Live run (1:15 – 1:45)

> Here's the whole pipeline running as one command.

```
python3 src/run_all.py
```

> [let it run, ~1 second total] That's 500 transactions, three separate audits, done in under a second. Now let's look at what it found.

[Screen: terminal output scrolling, then open `data/reconciliation_report.html` in browser]

---

## 4. Loop 1 — Reconciliation tab (1:45 – 2:45)

> This is the dashboard — one tab per loop, so it's easy to jump between them.

> First tab: **87.8% of transactions matched automatically.** Some matched perfectly because they shared the same reference number. Others had messy data — a different spelling of the customer name, a missing reference — so the tool used amount and date to find the right match instead, and only used the name as a tie-breaker, never as the deciding factor.

> The remaining **12.2%** — that's not swept under the rug. Every single one is listed here, with a plain-English reason why it couldn't be matched confidently. That's the honest part: this tool never pretends to be more certain than it is.

> And because I built my own answer key upfront, I can tell you this isn't a guess — it's **100% precision and recall**, measured, not estimated.

[Screen: point at stat cards, click into exceptions table, show a reason string]

---

## 5. Loop 2 — Fee/GST Audit tab (2:45 – 3:30)

> Second tab. Razorpay tells you what fee and GST it deducted — but nothing normally checks whether that number was *correct*. This recalculates the expected fee and tax from the actual contracted rate, compares it to what was really deducted, and flags anything off by more than fifty paise — small enough to ignore rounding noise, large enough to catch a real mistake.

> On this batch: **14 discrepancies out of 500, totaling about ₹55 in leakage.** Doesn't sound like much on 500 transactions — but at real merchant scale, that's the kind of silent leak that adds up to lakhs a year and nobody notices, because nobody's checking.

[Screen: point at leakage total, scroll one flagged row, read its reason]

---

## 6. Loop 3 — Refund Allocator tab (3:30 – 4:00)

> Third tab. When a refund is partial, the fee and tax need to be split proportionally and tied back to the original transaction — today that's manual ratio math. This does it automatically: 18 refund events, all 18 correctly allocated, each one showing exactly how much fee, tax, and net amount gets reversed, and which original settlement it's tied to.

[Screen: point at journal table, one row]

---

## 7. Why this design, and what it doesn't claim (4:00 – 4:40)

> A couple of deliberate choices. I used rule-based logic — not an LLM — for all of this, because it's faster, free, fully explainable, and there's nothing "fuzzy" about a rate card or a bank UTR. Every single decision this tool makes comes with a plain-English reason attached — that's the audit trail a compliance team would actually need.

> And I'll be upfront about the limits: this is a controlled synthetic dataset, not live production data — real-world cases like split invoices or multi-currency will need more work. I actually found a real bug during development — my matcher accepted a coincidental match with only 23% name similarity, a pure fluke. I added a floor to catch that, documented it in the failure log, and re-verified my accuracy numbers afterward. Showing you a mistake I found and fixed is more convincing than claiming a perfect first try.

[Screen: optional — flash `failure_log.md` for 2 seconds]

---

## 8. Close (4:40 – 5:00)

> So: three real finance-ops problems, one pipeline, real measured accuracy, honest exceptions, and a clear path for a human to step in exactly when they should. That's Recon AI.

[Screen: back to dashboard, top tab]

---

## Delivery notes
- Say numbers exactly as measured (87.8%, 100%, ₹54.66, 18/18) — don't round up further, the precision is part of the pitch.
- Don't read this word-for-word on camera — it's long-form so you can trim to your own voice; the beats (problem → 3 live demos → design rationale → honest limits → close) are what matters.
- If you're short on time, cut section 7 down to one sentence: "Rule-based, not LLM — faster, free, fully explainable, with a reason attached to every decision."
