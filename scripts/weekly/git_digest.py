#!/usr/bin/env python3
"""Tóm tắt gọn thay đổi git kể từ lần chạy trước để Claude đọc (ít token).

Đọc last_sha trong STATE.json; nếu chưa có (hoặc commit không còn), lấy N ngày gần nhất.
Chỉ in thống kê + danh sách commit, KHÔNG in diff đầy đủ.

    python3 scripts/weekly/git_digest.py --state ../weekly-reports/reports/weekly/STATE.json
"""
import argparse
import json
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


def git(*args: str, check: bool = True) -> str:
    r = subprocess.run(["git", *args], capture_output=True, text=True, check=check)
    return r.stdout.strip()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default=".claude/weekly/config.json")
    p.add_argument("--state", default="reports/weekly/STATE.json")
    p.add_argument("--since-days", type=int)
    p.add_argument("--max-commits", type=int, default=80)
    a = p.parse_args()

    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
    state_path = Path(a.state)
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    days = a.since_days or cfg.get("default_since_days", 7)

    branch, remote = cfg["base_branch"], cfg.get("upstream_remote", "origin")
    # chỉ ĐỌC repo gốc: lấy mọi nhánh (main + develop + nhánh team)
    git("fetch", "-q", "--prune", remote, f"+refs/heads/*:refs/remotes/{remote}/*", check=False)
    ref = f"{remote}/{branch}"
    head = git("rev-parse", ref)

    last = state.get("last_sha")
    if last and subprocess.run(["git", "cat-file", "-e", f"{last}^{{commit}}"],
                               capture_output=True).returncode == 0:
        base, why = last, "từ lần chạy trước"
    else:
        base = git("rev-list", "-1", f"--before={days} days ago", ref, check=False)
        if not base:
            base = git("rev-list", "--max-parents=0", ref).splitlines()[-1]
        why = f"{days} ngày gần nhất (chưa có last_sha hợp lệ)"

    rng = f"{base}..{head}"
    print(f"# Git digest {ref}: {base[:8]}..{head[:8]} ({why})")
    if base == head:
        print("KHÔNG CÓ THAY ĐỔI MỚI TRÊN NHÁNH CHÍNH.")
        branches_section(cfg, state, ref, remote, days)
        print(f"HEAD_SHA={head}")
        return

    print("\n## Số commit theo người (không tính merge)")
    print(git("shortlog", "-sn", "--no-merges", rng) or "(không có)")

    print("\n## PR/merge")
    print(git("log", "--merges", "--format=%h %ad %s", "--date=short", rng) or "(không có)")

    print(f"\n## Commit (tối đa {a.max_commits}, mới nhất trước)")
    print(git("log", "--no-merges", f"-{a.max_commits}", "--format=%h %ad %an: %s", "--date=short", rng))

    print("\n## Thay đổi theo team")
    for team, paths in cfg["teams"].items():
        stat = git("diff", "--shortstat", base, head, "--", *paths) or "không đổi"
        print(f"- {team}: {stat}")

    print("\n## 30 file đổi nhiều nhất (thêm/xoá/đường dẫn)")
    rows = []
    for line in git("diff", "--numstat", base, head).splitlines():
        add, dele, path = line.split("\t", 2)
        n = (int(add) if add.isdigit() else 0) + (int(dele) if dele.isdigit() else 0)
        rows.append((n, add, dele, path))
    for _, add, dele, path in sorted(rows, reverse=True)[:30]:
        print(f"+{add} -{dele} {path}")
    if len(rows) > 30:
        print(f"... và {len(rows) - 30} file khác")

    branches_section(cfg, state, ref, remote, days)
    print(f"\nHEAD_SHA={head}")


def branches_section(cfg: dict, state: dict, main_ref: str, remote: str, days: int) -> None:
    """Nhánh team/develop có commit mới kể từ lần trước và chưa vào nhánh chính."""
    since = state.get("last_run") or (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    old = state.get("branch_shas") or {}
    pat = re.compile(cfg.get("branch_pattern", r"team|develop"))
    out, shas, seen = [], {}, {}
    for line in git("for-each-ref", "--sort=-committerdate",
                    "--format=%(refname:short) %(objectname) %(committerdate:short)",
                    f"refs/remotes/{remote}/").splitlines():
        name, sha, date = line.split()
        short = name.removeprefix(f"{remote}/")
        if name == main_ref or short == "HEAD" or not pat.search(short):
            continue
        ahead = int(git("rev-list", "--count", f"{main_ref}..{sha}"))
        if not ahead or date < since:
            continue
        shas[short] = sha
        prev = old.get(short)
        new_rng = f"{prev}..{sha}" if prev and prev != sha else f"{main_ref}..{sha}"
        if prev == sha:
            continue  # không có gì mới kể từ lần trước
        if sha in seen:
            out.append(f"### {short} – trùng commit với {seen[sha]}")
            continue
        seen[sha] = short
        m = re.search(r"team[-_/]?(\d)", short)
        team = f"Team {m.group(1)}" if m else "Chung"
        stat = git("diff", "--shortstat", f"{main_ref}...{sha}")
        out.append(f"### {short} ({team}) – hơn main {ahead} commit, sửa lần cuối {date}\n"
                   f"tổng so với main: {stat}\n  "
                   + git("log", "--no-merges", "-8", "--format=  %h %ad %an: %s", "--date=short", new_rng))
    print(f"\n## Nhánh đang làm, chưa vào {main_ref} (có commit mới từ {since})")
    print("\n".join(out) if out else "(không có)")
    print("BRANCH_SHAS=" + json.dumps({**old, **shas}))


if __name__ == "__main__":
    main()
