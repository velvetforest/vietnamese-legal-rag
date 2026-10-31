# RUNBOOK – Tóm tắt code & chia task hằng tuần

Kích hoạt: chủ repo nhắn **`s`** (bất kỳ lúc nào) hoặc lịch tự động sáng Thứ 7 → **Pha A**.
Khi đang có đề xuất chờ duyệt (`STATE.status == "waiting_approval"`) và chủ repo nhắn `duyệt …` / `bỏ …` / `sửa …` → **Pha B**.

## Quyền truy cập
- Repo gốc (`upstream_url`, remote `upstream`): **chỉ fetch để đọc**, không bao giờ push.
- Mọi thứ ghi (nhánh báo cáo, nhánh code) push lên `origin` = fork của `fork_owner`.
- Chỉ "chạm" repo gốc khi mở PR từ fork sang (Pha B bước 7).

## Nguyên tắc (tiết kiệm token, không phụ thuộc trí nhớ)
- Trí nhớ duy nhất là file: `STATE.json` + các file trong `$WEEKLY_DIR/reports/weekly/`. Không dựa vào lịch sử chat.
- Chỉ đọc output của script. Diff đầy đủ chỉ mở cho ≤ 5 file quan trọng, mỗi file `| head -200`.
- Không quét toàn repo, không đọc lại báo cáo cũ trừ file được chỉ định.
- Tin nhắn trả lời chủ repo ≤ 10 dòng; chi tiết nằm trong file.
- Viết tiếng Việt. Ngày `D` = ngày hôm nay dạng `YYYY-MM-DD`.

## Pha A – Tóm tắt + đánh giá + đề xuất (KHÔNG ghi gì lên Jira, KHÔNG sửa code)
1. `bash scripts/weekly/prepare.sh` → lấy `WEEKLY_DIR` (mặc định `../weekly-reports`) và đọc STATE.
2. `python3 scripts/weekly/git_digest.py --state $WEEKLY_DIR/reports/weekly/STATE.json` → ghi nhớ `HEAD_SHA` và `BRANCH_SHAS`.
   Output gồm nhánh chính + các nhánh team/develop có commit mới chưa vào nhánh chính; bảng 1 phải gộp cả hai, ghi rõ nhánh.
   Nếu "KHÔNG CÓ THAY ĐỔI MỚI" thì vẫn làm bước 3–4 nhưng bảng 1 chỉ ghi một dòng.
3. `python3 scripts/weekly/jira_tool.py snapshot > $WEEKLY_DIR/reports/weekly/D-jira.txt`
   Nếu ra `JIRA_SKIPPED`: đánh giá dựa trên kế hoạch tuần trong `docs/team*/README.md` (chỉ grep phần tuần hiện tại) và ghi rõ "Jira chưa kết nối".
4. Viết `$WEEKLY_DIR/reports/weekly/D.md`:

   ```markdown
   # Báo cáo tuần D  (commit <base8>..<head8>)
   ## 1. Thay đổi code
   | Thay đổi | Ảnh hưởng | Đề xuất |
   |---|---|---|
   (5–12 dòng, gom theo chủ đề/team, mỗi ô ≤ 2 câu; dòng rủi ro đặt lên đầu với ⚠️)
   ## 2. Đánh giá chia task
   | Task (Team 1/2/3) | Đã ổn chưa, lý do | Đề xuất chia mới |
   |---|---|---|
   (Jira: team lấy từ tiêu đề `[Team 1]` / `team1-` / `[Team 2 / Team 3]`; task "Chưa gắn team" chưa Done → nêu ra để gắn team;
   ghi key Jira nếu có; ✅ ổn / ⚠️ cần xem / ❌ không ổn; chỉ liệt kê task đáng nói + 1 dòng tổng mỗi team)
   ```
5. Viết `$WEEKLY_DIR/reports/weekly/D-team1-proposal.md`: tối đa `max_tasks_per_run` task cho Team 1, mỗi task:
   `### [ ] T<n>. <tiêu đề>` + Lý do · File dự kiến đổi · Tiêu chí xong (test nào chứng minh) · Ước lượng (S/M/L).
   Chỉ đề xuất task Claude tự làm & tự test được trong repo.
6. Cập nhật STATE: `last_sha=HEAD_SHA`, `branch_shas=BRANCH_SHAS`, `last_run=D`, `status="waiting_approval"`, `pending_proposal="reports/weekly/D-team1-proposal.md"`.
   Commit trong `$WEEKLY_DIR` (`docs(weekly): báo cáo D`) và `git -C $WEEKLY_DIR push -u origin <reports_branch>`.
7. Trả lời chủ repo: đường dẫn 2 file, 3 điểm nổi bật nhất, danh sách T1..Tn (1 dòng/task), và hướng dẫn:
   `duyệt 1,3` · `bỏ 2` · `sửa 2: <ý kiến>`. Rồi DỪNG, chờ.

## Pha B – Làm task đã duyệt
1. `bash scripts/weekly/prepare.sh`; chỉ đọc file `pending_proposal` (không đọc lại báo cáo).
   `sửa n: …` → sửa đề xuất, commit, hỏi lại; không làm code.
2. Jira: ghi các task được duyệt vào `/tmp/weekly-tasks.json` rồi `python3 scripts/weekly/jira_tool.py create /tmp/weekly-tasks.json`
   (nếu `JIRA_SKIPPED` thì ghi chú, vẫn làm tiếp).
3. Nhánh đích `T = pr_targets[team]` (vd Team 1 → `develop`, Team 2 → `feature/team2-rag`).
   Baseline test trên đích: `git fetch -q upstream T && git checkout -B claude/weekly-team1-D upstream/T`, chạy `test_setup` (1 lần) rồi
   `<test_cmd> -rf 2>&1 | grep -E '^(FAILED|ERROR)' | sed 's/ - .*//' | sort > /tmp/base_fail.txt`.
4. Làm từng task, commit nhỏ theo `docs/CODING_CONVENTIONS.md`; code mới phải có test.
5. Chạy lại test → `/tmp/after_fail.txt`; `comm -13 /tmp/base_fail.txt /tmp/after_fail.txt` phải RỖNG.
   Được tự sửa tối đa 2 lần; vẫn có lỗi mới → KHÔNG push, ghi lý do vào STATE và báo chủ repo.
6. Viết `docs/weekly-changes/D.md` trên nhánh code: mỗi task → Đã đổi gì · Vì sao · File · Test chứng minh · Kết quả test (passed/failed trước–sau).
7. `git push -u origin claude/weekly-team1-D` (lên fork). Mở PR **từ fork sang nhánh team `T` của repo gốc** (không phải `main`) theo `.github/pull_request_template.md`;
   nếu công cụ không có quyền tạo PR trên repo gốc thì đưa chủ repo link 1-click:
   `https://github.com/<owner gốc>/<repo>/compare/T...<fork_owner>:<repo>:claude/weekly-team1-D?expand=1`. KHÔNG merge.
   (Nếu môi trường chỉ cho push một nhánh chỉ định thì dùng nhánh đó và ghi rõ.)
8. STATE: `status="done"`, `last_pr=<link PR>`, `pending_proposal=null`; commit + push nhánh báo cáo.
9. Trả lời ≤ 8 dòng: link PR, task nào xong/không xong, test trước–sau.

## Cấm
- Ghi Jira hoặc sửa code trước khi được duyệt. Push thẳng vào `main`. Tự merge PR.
- Skip/xoá/đánh dấu xfail test để qua cổng test.
- In secret (JIRA_API_TOKEN…) ra file hoặc chat.
