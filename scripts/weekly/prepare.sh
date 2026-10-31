#!/usr/bin/env bash
# Chuẩn bị thư mục báo cáo (worktree của nhánh reports_branch) và in STATE.json.
#   bash scripts/weekly/prepare.sh      -> in WEEKLY_DIR=... và nội dung STATE
set -euo pipefail
cfg() { python3 -c "import json;print(json.load(open('.claude/weekly/config.json'))['$1'])"; }
RB=$(cfg reports_branch)
BB=$(cfg base_branch)
UP=$(cfg upstream_remote); UPURL=$(cfg upstream_url)
R=${WEEKLY_DIR:-../weekly-reports}

[ "$(git rev-parse --is-shallow-repository)" = true ] && git fetch -q --unshallow origin 2>/dev/null || true
# Repo gốc chỉ đọc (fetch); mọi thứ ghi đều push lên origin = fork của chủ repo.
git remote get-url "$UP" >/dev/null 2>&1 || git remote add "$UP" "$UPURL"
git fetch -q "$UP" "$BB"
git fetch -q origin "$RB" 2>/dev/null || true

if [ ! -e "$R/.git" ]; then
  if git rev-parse -q --verify "origin/$RB" >/dev/null; then
    git worktree add -q -B "$RB" "$R" "origin/$RB"
  else
    git worktree add -q -B "$RB" "$R" "$UP/$BB"   # lần đầu: tạo nhánh báo cáo từ base
  fi
else
  git -C "$R" pull -q --ff-only origin "$RB" 2>/dev/null || true
fi

mkdir -p "$R/reports/weekly"
S="$R/reports/weekly/STATE.json"
[ -f "$S" ] || echo '{"last_sha": null, "last_run": null, "status": "idle", "pending_proposal": null, "last_pr": null}' > "$S"
echo "WEEKLY_DIR=$R"
cat "$S"
