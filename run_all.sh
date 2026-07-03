#!/usr/bin/env bash
# Run the standard real-model battery and analyse each result.
# Usage:  ./run_all.sh          (expects .env next to this script, or keys in env)
set -euo pipefail
cd "$(dirname "$0")"

# Load keys if a .env file is present.
if [ -f .env ]; then
  set -a; source .env; set +a
fi

MODELS=(
  "anthropic:claude-haiku-4-5-20251001"   # small
  "anthropic:claude-sonnet-5"             # large
  "anthropic:claude-opus-4-8"             # largest / reasoning-tier
)

for spec in "${MODELS[@]}"; do
  slug="${spec//[:.]/_}"
  echo "=== running ${spec} ==="
  python3 -m evalfaking.run --provider "${spec}" --scenarios scenarios.jsonl \
    --out "results/${slug}.jsonl" --repeats 1
  python3 -m evalfaking.analyze --results "results/${slug}.jsonl"
  echo
done

echo "All runs complete. Summaries are in results/*.summary.json"
