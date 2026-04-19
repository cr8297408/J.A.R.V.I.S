#!/usr/bin/env bash
# Asigna cada issue al milestone correcto
# Uso: bash assign_milestones.sh
set -e

export PATH="/opt/homebrew/bin:$PATH"
REPO="cr8297408/J.A.R.V.I.S"

assign() {
  local search="$1"
  local milestone="$2"
  local number
  number=$(gh issue list --repo "$REPO" --search "$search in:title" --json number --jq '.[0].number' 2>/dev/null)
  if [ -z "$number" ] || [ "$number" = "null" ]; then
    echo "  ⚠️  No encontré issue: $search"
    return
  fi
  gh issue edit "$number" --repo "$REPO" --milestone "$milestone" 2>/dev/null
  echo "  ✅ #$number → $milestone"
}

echo "── M1: Foundation ──────────────────────────────"
assign "[EPIC-1]" "M1: Foundation"
assign "[EPIC-2]" "M1: Foundation"
assign "[EPIC-3]" "M1: Foundation"
assign "[EPIC-4]" "M1: Foundation"

echo "── M2: Tool System ─────────────────────────────"
assign "[EPIC-5]"  "M2: Tool System"
assign "[EPIC-6]"  "M2: Tool System"
assign "[EPIC-7]"  "M2: Tool System"
assign "[EPIC-8]"  "M2: Tool System"
assign "[EPIC-9]"  "M2: Tool System"
assign "[EPIC-10]" "M2: Tool System"
assign "[EPIC-11]" "M2: Tool System"
assign "[EPIC-12]" "M2: Tool System"

echo "── M3: Voice UX ────────────────────────────────"
assign "[EPIC-13]" "M3: Voice UX"
assign "[EPIC-14]" "M3: Voice UX"
assign "[EPIC-15]" "M3: Voice UX"
assign "[EPIC-16]" "M3: Voice UX"
assign "[EPIC-17]" "M3: Voice UX"
assign "[EPIC-18]" "M3: Voice UX"

echo "── M4: Latency Zero ────────────────────────────"
assign "[EPIC-19]" "M4: Latency Zero"
assign "[EPIC-20]" "M4: Latency Zero"
assign "[EPIC-21]" "M4: Latency Zero"
assign "[EPIC-22]" "M4: Latency Zero"
assign "[EPIC-23]" "M4: Latency Zero"

echo "── M5: Intelligence ────────────────────────────"
assign "[EPIC-24]" "M5: Intelligence"
assign "[EPIC-25]" "M5: Intelligence"
assign "[EPIC-26]" "M5: Intelligence"
assign "[EPIC-27]" "M5: Intelligence"

echo "── M6: Advanced ────────────────────────────────"
assign "[EPIC-28]" "M6: Advanced"
assign "[EPIC-29]" "M6: Advanced"
assign "[EPIC-30]" "M6: Advanced"
assign "[EPIC-31]" "M6: Advanced"
assign "[EPIC-32]" "M6: Advanced"

echo ""
echo "✅ Listo → https://github.com/$REPO/milestones"
