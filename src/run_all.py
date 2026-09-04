import subprocess
import sys
import time

def run_step(script_name, description):
    print(f"\n{'='*60}")
    print(f"▶ {description}")
    print('='*60)
    time.sleep(0.3)  # tiny dramatic pause, feels intentional on camera
    result = subprocess.run([sys.executable, script_name])
    if result.returncode != 0:
        print(f"✗ FAILED at: {script_name}")
        sys.exit(1)
    print(f"✓ Done")

if __name__ == "__main__":
    print("RAZORPAY RECONCILIATION PIPELINE — FULL RUN")

    run_step("src/generate_data.py", "Generating synthetic dataset")
    run_step("src/exact_match.py", "Running exact match (UTR-based)")
    run_step("src/fuzzy_match.py", "Running fuzzy match (amount+date gated)")
    run_step("src/main.py", "Building final report + scoring")
    run_step("src/generate_report.py", "Generating HTML report")

    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE — check data/final_matched_report.csv and data/final_exceptions_report.csv")
    print('='*60)