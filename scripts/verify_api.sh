#!/usr/bin/env bash
# Verify all API endpoints against a running server (default: http://127.0.0.1:8000)
set -euo pipefail
BASE="${1:-http://127.0.0.1:8000}"

echo "==> Health"
curl -sf "$BASE/health" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='ok'; print('  OK mode=', d.get('mode'))"

echo "==> Stack status"
curl -sf "$BASE/api/v1/status" | python3 -c "
import sys,json
d=json.load(sys.stdin)
assert d.get('corpus',{}).get('verse_count',0) >= 20
print('  OK verses=', d['corpus']['verse_count'])
"

echo "==> Query: weight loss"
curl -sf -X POST "$BASE/api/v1/query" -H "Content-Type: application/json" \
  -d '{"query":"weight loss"}' | python3 -c "
import sys,json
d=json.load(sys.stdin)['result']
assert d['grounded'] and 'Sthoulya' in d['conditions_detected']
assert not any('Bhringraj' in r['formulation_name'] for r in d['remedies'])
print('  OK remedies=', [r['formulation_name'] for r in d['remedies'][:3]])
"

echo "==> Query: acidity"
curl -sf -X POST "$BASE/api/v1/query" -H "Content-Type: application/json" \
  -d '{"query":"acidity remedies"}' | python3 -c "
import sys,json
d=json.load(sys.stdin)['result']
assert d['grounded'] and 'Amlapitta' in d['conditions_detected']
print('  OK sources=', d['sources_used'])
"

echo "==> Profile + feedback"
TEST_USER="verify-$(date +%s)"
curl -sf -X POST "$BASE/api/v1/profile" -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$TEST_USER\",\"prakriti\":{\"vata\":0.3,\"pitta\":0.4,\"kapha\":0.3},\"vikriti\":{\"aggravated\":[\"Pitta aggravation\"]},\"allergies\":[],\"contraindications\":[],\"active_protocol\":{}}" \
  | python3 -c "import sys,json; print('  OK user=', json.load(sys.stdin)['user_id'])"

curl -sf -X POST "$BASE/api/v1/feedback" -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$TEST_USER\",\"formulation_name\":\"Shatavari Swarasa\",\"outcome\":\"helped\",\"checkpoint_day\":14,\"notes\":\"verify\"}" \
  | python3 -c "import sys,json; print('  OK delta=', json.load(sys.stdin)['efficacy_delta'])"

echo "==> Retrieve debug"
curl -sf "$BASE/api/v1/retrieve?q=Guduchi&limit=3" | python3 -c "
import sys,json
d=json.load(sys.stdin)
assert len(d['hits']) >= 1
print('  OK hits=', len(d['hits']))
"

echo ""
echo "All API checks passed."
