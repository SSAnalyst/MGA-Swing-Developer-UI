from __future__ import annotations

import argparse
from dotenv import load_dotenv
from .runner import run


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run Indian equity swing-research decision support using myGenAssist.")
    parser.add_argument("--capital", type=float, required=True, help="Trading capital in INR")
    parser.add_argument("--risk-percent", type=float, default=1.0, help="Maximum risk per trade (percent)")
    parser.add_argument("--max-positions", type=int, default=3, help="Maximum simultaneous positions")
    parser.add_argument("--run-context", choices=["post-market", "pre-open"], default="post-market")
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()
    if args.capital <= 0 or not 0 < args.risk_percent <= 5 or not 1 <= args.max_positions <= 10:
        parser.error("capital must be >0; risk-percent must be >0 and <=5; max-positions must be 1..10")
    report, path = run(args.capital, args.risk_percent, args.max_positions, args.run_context, args.output_dir)
    print(report)
    print(f"\nSaved report: {path}")


if __name__ == "__main__":
    main()
