#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate

python3 run_pipeline.py refresh-top10 --top-n 10 --sets-csv data/input/sets.csv --interval 10 "$@"
