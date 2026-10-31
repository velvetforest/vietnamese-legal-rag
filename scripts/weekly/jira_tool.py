#!/usr/bin/env python3
"""Đọc/ghi Jira qua REST API với output cực gọn (thay cho MCP để tiết kiệm token).

Xác thực (chọn 1):
  - Khuyên dùng: "Network secrets" của môi trường cloud tự gắn header Authorization cho host Jira
    -> script KHÔNG cần token, Claude không thấy token.
  - Hoặc env JIRA_EMAIL + JIRA_API_TOKEN (chạy local).
Địa chỉ Jira: jira.base_url trong .claude/weekly/config.json (hoặc env JIRA_BASE_URL).

    python3 scripts/weekly/jira_tool.py snapshot            # 1 dòng / issue, theo team
    python3 scripts/weekly/jira_tool.py create tasks.json   # tạo issue SAU KHI người dùng duyệt
    python3 scripts/weekly/jira_tool.py done VLRA-12 "ghi chú" [--dry-run]  # chuyển sang Done + comment

tasks.json: [{"team": "Team 1", "summary": "...", "description": "..."}]
"""
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

CFG = json.loads(Path(".claude/weekly/config.json").read_text(encoding="utf-8"))["jira"]


BASE_URL = (os.environ.get("JIRA_BASE_URL") or CFG.get("base_url") or "").rstrip("/")


def env_ok() -> bool:
    if not BASE_URL or not CFG.get("project_key"):
        print("JIRA_SKIPPED: chưa điền jira.base_url / jira.project_key trong config")
        return False
    return True


def call(method: str, path: str, body: dict | None = None) -> dict:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if os.environ.get("JIRA_EMAIL") and os.environ.get("JIRA_API_TOKEN"):
        raw = f"{os.environ['JIRA_EMAIL']}:{os.environ['JIRA_API_TOKEN']}".encode()
        headers["Authorization"] = "Basic " + base64.b64encode(raw).decode()
    # không có env -> header do Network secrets của môi trường cloud gắn vào
    req = urllib.request.Request(
        BASE_URL + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        hint = " (kiểm tra Network secret của host Jira)" if e.code in (401, 403) else ""
        sys.exit(f"JIRA_ERROR {e.code} {path}{hint}: {e.read()[:300]!r}")


def teams_of(summary: str) -> list[str]:
    """Team theo tiêu đề: "[Team 1] …", "team1-…", "[Team 2 / Team 3] …" (nhiều team được)."""
    head = summary.strip()[:30]
    found = [f"Team {n}" for n in re.findall(CFG.get("team_regex", r"(?i)team\s*[-_]?\s*(\d)"), head)]
    return list(dict.fromkeys(t for t in found if t in CFG["team_values"]))


def snapshot() -> None:
    """1 truy vấn cho cả project rồi chia team phía client (rẻ hơn 1 truy vấn/team)."""
    sp = CFG.get("story_points_field")
    fields = list(CFG["fields"]) + ([sp] if sp else [])
    jql = (f'project = {CFG["project_key"]} AND (statusCategory != Done OR updated >= -14d) '
           f'ORDER BY status, priority DESC')
    issues, token = [], None
    while len(issues) < CFG.get("max_issues", 300):
        body = {"jql": jql, "fields": fields, "maxResults": 100}
        if token:
            body["nextPageToken"] = token
        data = call("POST", "/rest/api/3/search/jql", body)
        issues += data.get("issues", [])
        token = data.get("nextPageToken")
        if not token or data.get("isLast", True):
            break
    groups: dict[str, list] = {t: [] for t in CFG["team_values"]}
    groups["Epic"], groups["Chưa gắn team"] = [], []
    epic = re.compile(CFG.get("epic_regex", r"(?i)^\s*\[epic"))
    for it in issues:
        summary = it["fields"].get("summary", "")
        if epic.search(summary):
            groups["Epic"].append(it)
            continue
        teams = teams_of(summary)
        if not teams and CFG.get("team_from_story_points") and sp:
            # task cũ: số team bị điền nhầm vào Story point estimate (1/2/3)
            guess = f"Team {int(it['fields'].get(sp) or 0)}"
            if guess in groups:
                it["_sp_team"] = True
                teams = [guess]
        for team in teams or ["Chưa gắn team"]:
            groups[team].append(it)
    for team, items in groups.items():
        print(f"## {team} ({len(items)} issue)")
        if items:
            print("key | trạng thái | người làm | SP | hạn | cập nhật | tiêu đề")
        for it in items:
            f = it["fields"]
            print(" | ".join([
                it["key"],
                (f.get("status") or {}).get("name", "-"),
                (f.get("assignee") or {}).get("displayName", "CHƯA GIAO"),
                "-" if it.get("_sp_team") or not sp else str(f.get(sp) or "-"),
                f.get("duedate") or "-",
                (f.get("updated") or "-")[:10],
                f.get("summary", "") + (" (team suy từ SP)" if it.get("_sp_team") else ""),
            ]))


def create(path: str) -> None:
    tasks = json.loads(Path(path).read_text(encoding="utf-8"))
    by = CFG.get("team_by", "component")
    for t in tasks:
        value = CFG["team_values"].get(t["team"], "")
        summary = t["summary"]
        if by.startswith("summary") and value and t["team"] not in teams_of(summary):
            summary = f"{value} {summary}"
        fields = {
            "project": {"key": CFG["project_key"]},
            "issuetype": {"name": CFG.get("issue_type", "Task")},
            "summary": summary,
            "description": {"type": "doc", "version": 1, "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": line}]}
                for line in t.get("description", "").splitlines() if line.strip()]},
        }
        if value and by == "component":
            fields["components"] = [{"name": value}]
        elif value and by == "label":
            fields["labels"] = [value]
        res = call("POST", "/rest/api/3/issue", {"fields": fields})
        print(f"CREATED {res.get('key')} | {summary}")


def done(key: str, note: str = "", dry_run: bool = False) -> None:
    """Chuyển issue sang trạng thái nhóm Done (+ comment ghi chú, vd link nhánh)."""
    if not re.fullmatch(rf'{re.escape(CFG["project_key"])}-\d+', key):
        sys.exit(f"JIRA_ERROR key không thuộc project {CFG['project_key']}: {key}")
    issue = call("GET", f"/rest/api/3/issue/{key}?fields=status")
    cur = issue["fields"]["status"]
    if cur.get("statusCategory", {}).get("key") == "done":
        print(f"ALREADY_DONE {key} ({cur.get('name')})")
        return
    trans = call("GET", f"/rest/api/3/issue/{key}/transitions").get("transitions", [])
    t = next((t for t in trans if t.get("to", {}).get("statusCategory", {}).get("key") == "done"), None)
    if not t:
        sys.exit(f"JIRA_ERROR {key}: không có transition sang Done từ '{cur.get('name')}'")
    if dry_run:
        print(f"DRY_RUN {key}: {cur.get('name')} -> {t['to']['name']} (transition {t['id']})")
        return
    if note:
        call("POST", f"/rest/api/3/issue/{key}/comment", {"body": {"type": "doc", "version": 1, "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": note}]}]}})
    call("POST", f"/rest/api/3/issue/{key}/transitions", {"transition": {"id": t["id"]}})
    print(f"DONE {key}: {cur.get('name')} -> {t['to']['name']}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd not in ("snapshot", "create", "done") or (cmd in ("create", "done") and len(sys.argv) < 3):
        sys.exit(__doc__)
    if env_ok():
        if cmd == "snapshot":
            snapshot()
        elif cmd == "create":
            create(sys.argv[2])
        else:
            args = sys.argv[3:]
            dry = "--dry-run" in args
            done(sys.argv[2], " ".join(a for a in args if a != "--dry-run"), dry)
