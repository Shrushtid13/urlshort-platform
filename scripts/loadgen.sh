#!/usr/bin/env bash
# Creates links and hits them repeatedly to populate Grafana.
set -euo pipefail
HOST=${HOST:-http://localhost:8000}
for i in $(seq 1 20); do
  code=$(curl -fsS -X POST "$HOST/api/v1/links" -H 'content-type: application/json' \
    -d "{\"url\":\"https://example.com/$i\"}" | python3 -c 'import sys,json;print(json.load(sys.stdin)["code"])')
  for _ in $(seq 1 25); do curl -s -o /dev/null "$HOST/$code"; done
done
echo "done - open http://localhost:3000"
