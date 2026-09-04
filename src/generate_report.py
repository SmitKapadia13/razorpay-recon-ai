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
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Recon AI — Reconciliation Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #f4f6fb; --surface: #ffffff; --text: #10192e; --muted: #6b7688; --border: #e3e7f0;
    --navy: #0c1f45; --navy-2: #142c5c; --accent: #3395ff; --accent-soft: #e8f2ff;
    --exact: #16a34a; --exact-soft: #e7f8ee;
    --fuzzy: #d97706; --fuzzy-soft: #fef3e2;
    --exception: #dc2626; --exception-soft: #fdeaea;
    --shadow: 0 1px 2px rgba(16,25,46,0.04), 0 8px 24px rgba(16,25,46,0.06);
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg: #090e1b; --surface: #121a2e; --text: #eaeefb; --muted: #8b96ae; --border: #223054;
      --navy: #060c1c; --navy-2: #0d1730; --accent: #5dabff; --accent-soft: #132540;
      --exact-soft: #103322; --fuzzy-soft: #3a2a0d; --exception-soft: #3a1414;
      --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 8px 24px rgba(0,0,0,0.4);
    }}
  }}
  :root[data-theme="dark"] {{
    --bg: #090e1b; --surface: #121a2e; --text: #eaeefb; --muted: #8b96ae; --border: #223054;
    --navy: #060c1c; --navy-2: #0d1730; --accent: #5dabff; --accent-soft: #132540;
    --exact-soft: #103322; --fuzzy-soft: #3a2a0d; --exception-soft: #3a1414;
    --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 8px 24px rgba(0,0,0,0.4);
  }}
  * {{ box-sizing: border-box; }}
  html {{ scroll-behavior: smooth; }}
  body {{
    font-family: 'Inter', -apple-system, sans-serif; background: var(--bg); color: var(--text);
    margin: 0; -webkit-font-smoothing: antialiased;
  }}
  .topbar {{ background: linear-gradient(135deg, var(--navy), var(--navy-2)); padding: 18px 24px; }}
  .topbar-inner {{ max-width: 1040px; margin: 0 auto; display: flex; align-items: center; gap: 12px; }}
  .brand-mark {{
    width: 34px; height: 34px; border-radius: 9px; background: var(--accent);
    color: var(--navy); font-weight: 800; font-size: 16px; display: flex;
    align-items: center; justify-content: center; flex-shrink: 0;
  }}
  .brand-text {{ line-height: 1.25; }}
  .brand-title {{ color: #fff; font-weight: 700; font-size: 15px; letter-spacing: 0.2px; }}
  .brand-sub {{ color: #9db4de; font-size: 11px; font-weight: 500; letter-spacing: 0.3px; text-transform: uppercase; }}

  .container {{ max-width: 1040px; margin: 0 auto; padding: 28px 24px 48px; }}
  h1 {{ font-size: 21px; font-weight: 700; margin: 0 0 4px; letter-spacing: -0.2px; }}
  .subtitle {{ color: var(--muted); margin-bottom: 22px; font-size: 13.5px; }}
  .subtitle .sep {{ margin: 0 6px; opacity: 0.5; }}

  .tabs {{ display: flex; gap: 6px; margin-bottom: 26px; background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 5px; box-shadow: var(--shadow); }}
  .tab-btn {{
    flex: 1; background: none; border: none; cursor: pointer; font: inherit;
    color: var(--muted); padding: 10px 12px; border-radius: 8px; font-size: 13px; font-weight: 600;
    transition: background 0.15s, color 0.15s;
  }}
  .tab-btn:hover {{ color: var(--text); background: var(--accent-soft); }}
  .tab-btn.active {{ color: #fff; background: var(--accent); }}
  .tab-panel {{ display: none; }}
  .tab-panel.active {{ display: block; animation: fadein 0.2s ease; }}
  @keyframes fadein {{ from {{ opacity: 0; transform: translateY(3px); }} to {{ opacity: 1; transform: translateY(0); }} }}

  .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 18px; }}
  .stat-card {{
    background: var(--surface); border: 1px solid var(--border); border-top: 3px solid var(--accent);
    border-radius: 12px; padding: 16px 18px; text-decoration: none; color: inherit; cursor: pointer;
    display: block; box-shadow: var(--shadow); transition: transform 0.15s, box-shadow 0.15s;
  }}
  .stat-card:hover {{ transform: translateY(-3px); box-shadow: 0 4px 8px rgba(16,25,46,0.06), 0 16px 32px rgba(16,25,46,0.1); }}
  .stat-card:active {{ transform: translateY(-1px); }}
  .stat-card.exact {{ border-top-color: var(--exact); }}
  .stat-card.fuzzy {{ border-top-color: var(--fuzzy); }}
  .stat-card.exception {{ border-top-color: var(--exception); }}
  .stat-value {{ font-size: 25px; font-weight: 800; font-family: 'JetBrains Mono', monospace; letter-spacing: -0.5px; }}
  .stat-label {{ font-size: 11.5px; color: var(--muted); margin-top: 5px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; }}

  .bar-container {{
    background: var(--surface); border-radius: 10px; overflow: hidden; height: 34px;
    display: flex; margin-bottom: 10px; border: 1px solid var(--border); box-shadow: var(--shadow);
  }}
  .bar {{
    height: 100%; display: flex; align-items: center; justify-content: center;
    font-size: 11px; color: white; font-weight: 700; text-decoration: none; cursor: pointer;
  }}
  .bar.exact {{ background: var(--exact); width: {exact_pct}%; }}
  .bar.fuzzy {{ background: var(--fuzzy); width: {fuzzy_pct}%; }}
  .bar.exception {{ background: var(--exception); width: {exception_pct}%; }}
  .legend {{ display: flex; gap: 18px; margin-bottom: 28px; font-size: 12px; color: var(--muted); font-weight: 500; }}
  .dot {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 5px; }}
  .dot.exact {{ background: var(--exact); }}
  .dot.fuzzy {{ background: var(--fuzzy); }}
  .dot.exception {{ background: var(--exception); }}

  h2 {{ font-size: 14px; font-weight: 700; margin: 32px 0 12px; scroll-margin-top: 20px; display: flex; align-items: center; gap: 8px; }}
  h2::before {{ content: ""; width: 3px; height: 14px; background: var(--accent); border-radius: 2px; display: inline-block; }}
  .table-wrap {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; box-shadow: var(--shadow); overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ text-align: left; padding: 11px 14px; border-bottom: 1px solid var(--border); white-space: nowrap; }}
  td {{ white-space: normal; }}
  tr:last-child td {{ border-bottom: none; }}
  tbody tr:hover td {{ background: var(--accent-soft); }}
  th {{ color: var(--muted); font-weight: 700; font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.4px; background: var(--bg); }}
  .badge {{ padding: 3px 9px; border-radius: 20px; font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3px; }}
  .badge.exact {{ background: var(--exact-soft); color: var(--exact); }}
  .badge.fuzzy {{ background: var(--fuzzy-soft); color: var(--fuzzy); }}

  .section-head {{ margin-top: 6px; }}
  .section-head h1 {{ display: flex; align-items: center; gap: 10px; }}
  .section-icon {{
    width: 30px; height: 30px; border-radius: 8px; background: var(--accent-soft); color: var(--accent);
    display: inline-flex; align-items: center; justify-content: center; font-size: 15px; font-weight: 700;
  }}

  .footer {{ text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--border); }}
  .footer a {{ font-size: 12px; color: var(--muted); text-decoration: none; font-weight: 600; }}
  .footer a:hover {{ color: var(--accent); }}
  .footer .tag {{ display: block; font-size: 11px; color: var(--muted); opacity: 0.7; margin-top: 6px; }}

  @media (max-width: 600px) {{
    .container {{ padding: 20px 14px 36px; }}
    .topbar {{ padding: 14px 16px; }}
    .tabs {{ flex-wrap: wrap; }}
    .tab-btn {{ flex: 1 1 30%; }}
    .stats {{ grid-template-columns: repeat(2, 1fr); }}
    table {{ font-size: 11.5px; }}
    th, td {{ padding: 8px 10px; }}
    .legend {{ flex-wrap: wrap; gap: 10px; }}
  }}
</style>
</head>
<body>
  <div class="topbar">
    <div class="topbar-inner">
      <div class="brand-mark">₹</div>
      <div class="brand-text">
        <div class="brand-title">Recon AI — Multi-Loop Finance Controller</div>
        <div class="brand-sub">Razorpay AI Buildathon 2026 · Track T4</div>
      </div>
    </div>
  </div>

  <div class="container">
  <h1 id="top">Reconciliation Dashboard</h1>
  <div class="subtitle">Generated {datetime.now().strftime('%d %b %Y, %I:%M %p')}<span class="sep">·</span>{total} transactions processed<span class="sep">·</span>3 closed loops</div>

  <div class="tabs">
    <button class="tab-btn active" data-tab="tab-1" onclick="showTab('tab-1', this)">1 · Reconciliation</button>
    <button class="tab-btn" data-tab="tab-2" onclick="showTab('tab-2', this)">2 · Fee/GST Audit</button>
    <button class="tab-btn" data-tab="tab-3" onclick="showTab('tab-3', this)">3 · Refund Allocator</button>
  </div>

  <div class="tab-panel active" id="tab-1">
  <div class="stats">
    <a href="#matched-table" class="stat-card exact"><div class="stat-value">{match_pct:.1f}%</div><div class="stat-label">Auto-Matched</div></a>
    <a href="#matched-table" class="stat-card exact"><div class="stat-value">{exact_count}</div><div class="stat-label">Exact Matches</div></a>
    <a href="#matched-table" class="stat-card fuzzy"><div class="stat-value">{fuzzy_count}</div><div class="stat-label">Fuzzy Matches</div></a>
    <a href="#exceptions-table" class="stat-card exception"><div class="stat-value">{exception_count}</div><div class="stat-label">Honest Exceptions</div></a>
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
  <div class="section-head">
  <h1><span class="section-icon">%</span>Fee / GST Split Audit</h1>
  <div class="subtitle">Recomputed against 2.5% fee + 18% GST rate card<span class="sep">·</span>₹0.50 tolerance</div>
  </div>

  <div class="stats">
    <a href="#fee-audit-table" class="stat-card exact"><div class="stat-value">{fee_clean_count}</div><div class="stat-label">Clean Settlements</div></a>
    <a href="#fee-audit-table" class="stat-card exception"><div class="stat-value">{fee_flagged_count}</div><div class="stat-label">Flagged Discrepancies</div></a>
    <a href="#fee-audit-table" class="stat-card exception"><div class="stat-value">{fee_flagged_pct:.1f}%</div><div class="stat-label">Flag Rate</div></a>
    <div class="stat-card exception"><div class="stat-value">₹{fee_total_leakage:,.2f}</div><div class="stat-label">Total Leakage Found</div></div>
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
  <div class="section-head">
  <h1><span class="section-icon">↺</span>Partial Refund Allocator</h1>
  <div class="subtitle">Fee/GST/net split proportionally per refund<span class="sep">·</span>tied to original settlement</div>
  </div>

  <div class="stats">
    <a href="#refund-table" class="stat-card"><div class="stat-value">{refund_total}</div><div class="stat-label">Refund Events</div></a>
    <a href="#refund-table" class="stat-card exact"><div class="stat-value">{len(refund_journal)}</div><div class="stat-label">Journal Entries</div></a>
    <a href="#refund-table" class="stat-card exception"><div class="stat-value">{len(refund_exceptions)}</div><div class="stat-label">Unresolved</div></a>
    <div class="stat-card"><div class="stat-value">₹{refund_net_reversed:,.2f}</div><div class="stat-label">Net Amount Reversed</div></div>
  </div>

  <h2 id="refund-table">Refund Journal Entries</h2>
  <div class="table-wrap">
  <table>
    <tr><th>Refund</th><th>Settlement</th><th>Type</th><th>Amount</th><th>Ratio</th><th>Fee Reversal</th><th>GST Reversal</th><th>Net Reversal</th></tr>
    {refund_rows_html}
  </table>
  </div>
  </div>

  <div class="footer">
    <a href="#top">↑ Back to top</a>
    <span class="tag">Rule-based matching · Full audit trail · Honest exceptions, never cherry-picked</span>
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