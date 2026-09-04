import pandas as pd
from datetime import datetime

def generate_html_report():
    matched = pd.read_csv("data/final_matched_report.csv")
    exceptions = pd.read_csv("data/final_exceptions_report.csv")
    fee_flagged = pd.read_csv("data/fee_audit_flagged.csv")
    rzp = pd.read_csv("data/razorpay_settlement.csv")
    refund_journal = pd.read_csv("data/refund_journal.csv")
    refund_exceptions = pd.read_csv("data/refund_exceptions.csv")

    total = len(matched) + len(exceptions)
    exact_count = len(matched[matched["match_type"] == "exact"])
    fuzzy_count = len(matched[matched["match_type"] == "fuzzy"])
    exception_count = len(exceptions)

    match_pct = (len(matched) / total * 100) if total > 0 else 0
    exact_pct = (exact_count / total * 100) if total > 0 else 0
    fuzzy_pct = (fuzzy_count / total * 100) if total > 0 else 0
    exception_pct = (exception_count / total * 100) if total > 0 else 0

    total_amount_matched = matched.merge(
        pd.read_csv("data/razorpay_settlement.csv")[["settlement_id", "order_amount"]],
        on="settlement_id", how="left"
    )["order_amount"].sum()

    total_amount_exception = exceptions["order_amount"].sum() if "order_amount" in exceptions.columns else 0

    exact_sample = matched[matched["match_type"] == "exact"].head(10)
    fuzzy_sample = matched[matched["match_type"] == "fuzzy"].head(10)
    sample_combined = pd.concat([exact_sample, fuzzy_sample])

    matched_rows_html = "".join([
        f"<tr><td>{r['utr_number']}</td><td>{r['invoice_no']}</td><td><span class='badge {r['match_type']}'>{r['match_type']}</span></td><td>{r['confidence']}</td><td>{r['reason']}</td></tr>"
        for _, r in sample_combined.iterrows()
    ])

    exception_rows_html = "".join([
        f"<tr><td>{r['utr_number']}</td><td>{r['customer_name']}</td><td>₹{r['order_amount']:.2f}</td><td>{r['reason']}</td></tr>"
        for _, r in exceptions.iterrows()
    ])

    # ---- PS2: Fee/GST audit stats ----
    fee_total_leakage = fee_flagged["leakage"].sum() if len(fee_flagged) else 0.0
    fee_flagged_count = len(fee_flagged)
    fee_clean_count = len(rzp) - fee_flagged_count
    fee_flagged_pct = (fee_flagged_count / len(rzp) * 100) if len(rzp) else 0

    fee_rows_html = "".join([
        f"<tr><td>{r['settlement_id']}</td><td>{r['customer_name']}</td><td>₹{r['expected_fee']:.2f}</td><td>₹{r['actual_fee']:.2f}</td><td>₹{r['leakage']:.2f}</td><td>{r['reason']}</td></tr>"
        for _, r in fee_flagged.iterrows()
    ])

    # ---- PS3: Refund allocation stats ----
    refund_total = len(refund_journal) + len(refund_exceptions)
    refund_net_reversed = refund_journal["allocated_net_reversal"].sum() if len(refund_journal) else 0.0

    refund_rows_html = "".join([
        f"<tr><td>{r['refund_id']}</td><td>{r['settlement_id']}</td><td>{r['refund_type']}</td><td>₹{r['refund_amount']:.2f}</td><td>{r['refund_ratio']:.1%}</td><td>₹{r['allocated_fee_reversal']:.2f}</td><td>₹{r['allocated_gst_reversal']:.2f}</td><td>₹{r['allocated_net_reversal']:.2f}</td></tr>"
        for _, r in refund_journal.iterrows()
    ])

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Reconciliation Report</title>
<style>
  :root {{
    --bg: #ffffff; --text: #1a1a1a; --card: #f5f5f7; --border: #e0e0e0;
    --exact: #22c55e; --fuzzy: #f59e0b; --exception: #ef4444; --accent: #6366f1;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{ --bg: #0f0f0f; --text: #e5e5e5; --card: #1a1a1a; --border: #2a2a2a; }}
  }}
  :root[data-theme="dark"] {{ --bg: #0f0f0f; --text: #e5e5e5; --card: #1a1a1a; --border: #2a2a2a; }}
  * {{ box-sizing: border-box; }}
  html {{ scroll-behavior: smooth; }}
  body {{ font-family: -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 24px; max-width: 1000px; margin: 0 auto; }}
  h1 {{ font-size: 22px; margin-bottom: 4px; }}
  .subtitle {{ color: #888; margin-bottom: 24px; font-size: 14px; }}
  .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 16px; }}
  .stat-card {{
    background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 16px;
    text-decoration: none; color: inherit; cursor: pointer; display: block;
    transition: transform 0.15s, box-shadow 0.15s;
  }}
  .stat-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
  .stat-card:active {{ transform: translateY(0); }}
  .stat-value {{ font-size: 26px; font-weight: 700; }}
  .stat-label {{ font-size: 12px; color: #888; margin-top: 4px; }}
  .bar-container {{
    background: var(--card); border-radius: 8px; overflow: hidden; height: 32px;
    display: flex; margin-bottom: 10px; border: 1px solid var(--border);
  }}
  .bar {{
    height: 100%; display: flex; align-items: center; justify-content: center;
    font-size: 11px; color: white; font-weight: 600;
    text-decoration: none; cursor: pointer;
  }}
  .bar.exact {{ background: var(--exact); width: {exact_pct}%; }}
  .bar.fuzzy {{ background: var(--fuzzy); width: {fuzzy_pct}%; }}
  .bar.exception {{ background: var(--exception); width: {exception_pct}%; }}
  .legend {{ display: flex; gap: 16px; margin-bottom: 24px; font-size: 12px; color: #888; }}
  .dot {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; }}
  .dot.exact {{ background: var(--exact); }}
  .dot.fuzzy {{ background: var(--fuzzy); }}
  .dot.exception {{ background: var(--exception); }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 13px; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); }}
  th {{ color: #888; font-weight: 600; font-size: 12px; text-transform: uppercase; }}
  .badge {{ padding: 2px 8px; border-radius: 12px; font-size: 11px; color: white; }}
  .badge.exact {{ background: var(--exact); }}
  .badge.fuzzy {{ background: var(--fuzzy); }}
  .table-wrap {{ overflow-x: auto; }}
  h2 {{ font-size: 16px; margin-top: 32px; scroll-margin-top: 20px; }}
  .tabs {{ display: flex; gap: 8px; margin-bottom: 24px; border-bottom: 1px solid var(--border); }}
  .tab-btn {{
    background: none; border: none; cursor: pointer; font: inherit;
    color: #888; padding: 10px 4px; margin-bottom: -1px;
    border-bottom: 2px solid transparent; font-size: 13px; font-weight: 600;
  }}
  .tab-btn:hover {{ color: var(--text); }}
  .tab-btn.active {{ color: var(--accent); border-bottom-color: var(--accent); }}
  .tab-panel {{ display: none; }}
  .tab-panel.active {{ display: block; }}
  @media (max-width: 600px) {{
    .tabs {{ overflow-x: auto; white-space: nowrap; }}
    body {{ padding: 12px; }}
    .stats {{ grid-template-columns: repeat(2, 1fr); }}
    table {{ font-size: 11px; }}
    th, td {{ padding: 6px; }}
    .legend {{ flex-wrap: wrap; gap: 10px; }}
  }}
</style>
</head>
<body>
  <h1 id="top">Multi-Source Settlement Reconciliation Report</h1>
  <div class="subtitle">Generated {datetime.now().strftime('%d %b %Y, %I:%M %p')} · {total} transactions processed</div>

  <div class="tabs">
    <button class="tab-btn active" data-tab="tab-1" onclick="showTab('tab-1', this)">1. Reconciliation</button>
    <button class="tab-btn" data-tab="tab-2" onclick="showTab('tab-2', this)">2. Fee/GST Audit</button>
    <button class="tab-btn" data-tab="tab-3" onclick="showTab('tab-3', this)">3. Refund Allocator</button>
  </div>

  <div class="tab-panel active" id="tab-1">
  <div class="stats">
    <a href="#matched-table" class="stat-card"><div class="stat-value">{match_pct:.1f}%</div><div class="stat-label">Auto-Matched</div></a>
    <a href="#matched-table" class="stat-card"><div class="stat-value">{exact_count}</div><div class="stat-label">Exact Matches</div></a>
    <a href="#matched-table" class="stat-card"><div class="stat-value">{fuzzy_count}</div><div class="stat-label">Fuzzy Matches</div></a>
    <a href="#exceptions-table" class="stat-card"><div class="stat-value">{exception_count}</div><div class="stat-label">Honest Exceptions</div></a>
    <div class="stat-card"><div class="stat-value">₹{total_amount_matched:,.0f}</div><div class="stat-label">Amount Reconciled</div></div>
  </div>

  <div class="bar-container">
    <a href="#matched-table" class="bar exact">{exact_pct:.0f}%</a>
    <a href="#matched-table" class="bar fuzzy">{fuzzy_pct:.0f}%</a>
    <a href="#exceptions-table" class="bar exception">{exception_pct:.0f}%</a>
  </div>
  <div class="legend">
    <span><i class="dot exact"></i>Exact Match</span>
    <span><i class="dot fuzzy"></i>Fuzzy Match</span>
    <span><i class="dot exception"></i>Needs Review</span>
  </div>

  <h2 id="matched-table">Sample Matched Transactions (10 exact + 10 fuzzy)</h2>
  <div class="table-wrap">
  <table>
    <tr><th>UTR</th><th>Invoice</th><th>Type</th><th>Confidence</th><th>Reason</th></tr>
    {matched_rows_html}
  </table>
  </div>

  <h2 id="exceptions-table">Exceptions — Flagged for Human Review</h2>
  <div class="table-wrap">
  <table>
    <tr><th>UTR</th><th>Customer</th><th>Amount</th><th>Reason</th></tr>
    {exception_rows_html}
  </table>
  </div>
  </div>

  <div class="tab-panel" id="tab-2">
  <h1 id="fee-audit">Fee / GST Split Audit</h1>
  <div class="subtitle">Recomputed against 2.5% fee + 18% GST rate card · ₹0.50 tolerance</div>

  <div class="stats">
    <a href="#fee-audit-table" class="stat-card"><div class="stat-value">{fee_clean_count}</div><div class="stat-label">Clean Settlements</div></a>
    <a href="#fee-audit-table" class="stat-card"><div class="stat-value">{fee_flagged_count}</div><div class="stat-label">Flagged Discrepancies</div></a>
    <a href="#fee-audit-table" class="stat-card"><div class="stat-value">{fee_flagged_pct:.1f}%</div><div class="stat-label">Flag Rate</div></a>
    <div class="stat-card"><div class="stat-value">₹{fee_total_leakage:,.2f}</div><div class="stat-label">Total Leakage Found</div></div>
  </div>

  <h2 id="fee-audit-table">Flagged Fee/GST Discrepancies</h2>
  <div class="table-wrap">
  <table>
    <tr><th>Settlement</th><th>Customer</th><th>Expected Fee</th><th>Actual Fee</th><th>Leakage</th><th>Reason</th></tr>
    {fee_rows_html}
  </table>
  </div>
  </div>

  <div class="tab-panel" id="tab-3">
  <h1 id="refund-allocator">Partial Refund Allocator</h1>
  <div class="subtitle">Fee/GST/net split proportionally per refund, tied to original settlement</div>

  <div class="stats">
    <a href="#refund-table" class="stat-card"><div class="stat-value">{refund_total}</div><div class="stat-label">Refund Events</div></a>
    <a href="#refund-table" class="stat-card"><div class="stat-value">{len(refund_journal)}</div><div class="stat-label">Journal Entries</div></a>
    <a href="#refund-table" class="stat-card"><div class="stat-value">{len(refund_exceptions)}</div><div class="stat-label">Unresolved</div></a>
    <div class="stat-card"><div class="stat-value">₹{refund_net_reversed:,.2f}</div><div class="stat-label">Net Amount Reversed</div></div>
  </div>

  <h2 id="refund-table">Refund Journal Entries</h2>
  <div class="table-wrap">
  <table>
    <tr><th>Refund</th><th>Settlement</th><th>Type</th><th>Amount</th><th>Ratio</th><th>Fee Reversal</th><th>GST Reversal</th><th>Net Reversal</th></tr>
    {refund_rows_html}
  </table>
  </div>

  <div style="text-align:center; margin-top:32px;">
    <a href="#top" style="font-size:12px; color:#888; text-decoration:none;">↑ Back to top</a>
  </div>
  </div>

  <script>
    function showTab(tabId, btn) {{
      document.querySelectorAll('.tab-panel').forEach(function(panel) {{
        panel.classList.toggle('active', panel.id === tabId);
      }});
      document.querySelectorAll('.tab-btn').forEach(function(b) {{
        b.classList.toggle('active', b === btn);
      }});
    }}
  </script>
</body>
</html>"""

    with open("data/reconciliation_report.html", "w") as f:
        f.write(html)

    print(f"HTML report saved: data/reconciliation_report.html")
    print(f"Total: {total} | Matched: {match_pct:.1f}% | Amount reconciled: ₹{total_amount_matched:,.0f}")

if __name__ == "__main__":
    generate_html_report()