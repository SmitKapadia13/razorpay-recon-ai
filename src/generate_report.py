import pandas as pd
from datetime import datetime

def generate_html_report():
    matched = pd.read_csv("data/final_matched_report.csv")
    exceptions = pd.read_csv("data/final_exceptions_report.csv")

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

    matched_rows_html = "".join([
        f"<tr><td>{r['utr_number']}</td><td>{r['invoice_no']}</td><td><span class='badge {r['match_type']}'>{r['match_type']}</span></td><td>{r['confidence']}</td><td>{r['reason']}</td></tr>"
        for _, r in matched.head(20).iterrows()
    ])

    exception_rows_html = "".join([
        f"<tr><td>{r['utr_number']}</td><td>{r['customer_name']}</td><td>₹{r['order_amount']:.2f}</td><td>{r['reason']}</td></tr>"
        for _, r in exceptions.iterrows()
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
  body {{ font-family: -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 24px; max-width: 1000px; margin: 0 auto; }}
  h1 {{ font-size: 22px; margin-bottom: 4px; }}
  .subtitle {{ color: #888; margin-bottom: 24px; font-size: 14px; }}
  .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 24px; }}
  .stat-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }}
  .stat-value {{ font-size: 26px; font-weight: 700; }}
  .stat-label {{ font-size: 12px; color: #888; margin-top: 4px; }}
  .bar-container {{ background: var(--card); border-radius: 8px; overflow: hidden; height: 32px; display: flex; margin-bottom: 24px; border: 1px solid var(--border); }}
  .bar {{ height: 100%; display: flex; align-items: center; justify-content: center; font-size: 11px; color: white; font-weight: 600; }}
  .bar.exact {{ background: var(--exact); width: {exact_pct}%; }}
  .bar.fuzzy {{ background: var(--fuzzy); width: {fuzzy_pct}%; }}
  .bar.exception {{ background: var(--exception); width: {exception_pct}%; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 13px; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); }}
  th {{ color: #888; font-weight: 600; font-size: 12px; text-transform: uppercase; }}
  .badge {{ padding: 2px 8px; border-radius: 12px; font-size: 11px; color: white; }}
  .badge.exact {{ background: var(--exact); }}
  .badge.fuzzy {{ background: var(--fuzzy); }}
  .table-wrap {{ overflow-x: auto; }}
  h2 {{ font-size: 16px; margin-top: 32px; }}
  @media (max-width: 600px) {{
    body {{ padding: 12px; }}
    .stats {{ grid-template-columns: repeat(2, 1fr); }}
    table {{ font-size: 11px; }}
    th, td {{ padding: 6px; }}
  }}
  .stat-card {{ transition: transform 0.15s; }}
  .stat-card:hover {{ transform: translateY(-2px); }}
</style>
</head>
<body>
  <h1>Multi-Source Settlement Reconciliation Report</h1>
  <div class="subtitle">Generated {datetime.now().strftime('%d %b %Y, %I:%M %p')} · {total} transactions processed</div>

  <div class="stats">
    <div class="stat-card"><div class="stat-value">{match_pct:.1f}%</div><div class="stat-label">Auto-Matched</div></div>
    <div class="stat-card"><div class="stat-value">{exact_count}</div><div class="stat-label">Exact Matches</div></div>
    <div class="stat-card"><div class="stat-value">{fuzzy_count}</div><div class="stat-label">Fuzzy Matches</div></div>
    <div class="stat-card"><div class="stat-value">{exception_count}</div><div class="stat-label">Honest Exceptions</div></div>
    <div class="stat-card"><div class="stat-value">₹{total_amount_matched:,.0f}</div><div class="stat-label">Amount Reconciled</div></div>
  </div>

  <div class="bar-container">
    <div class="bar exact">{exact_pct:.0f}%</div>
    <div class="bar fuzzy">{fuzzy_pct:.0f}%</div>
    <div class="bar exception">{exception_pct:.0f}%</div>
  </div>

  <h2>Sample Matched Transactions (first 20)</h2>
  <div class="table-wrap">
  <table>
    <tr><th>UTR</th><th>Invoice</th><th>Type</th><th>Confidence</th><th>Reason</th></tr>
    {matched_rows_html}
  </table>
  </div>

  <h2>Exceptions — Flagged for Human Review</h2>
  <div class="table-wrap">
  <table>
    <tr><th>UTR</th><th>Customer</th><th>Amount</th><th>Reason</th></tr>
    {exception_rows_html}
  </table>
  </div>
</body>
</html>"""

    with open("data/reconciliation_report.html", "w") as f:
        f.write(html)

    print(f"HTML report saved: data/reconciliation_report.html")
    print(f"Total: {total} | Matched: {match_pct:.1f}% | Amount reconciled: ₹{total_amount_matched:,.0f}")

if __name__ == "__main__":
    generate_html_report()