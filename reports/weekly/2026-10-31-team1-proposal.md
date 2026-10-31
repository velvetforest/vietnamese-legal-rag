# Danh sách task Team 1 tự làm – 2026-10-31 (Pha B tự động)

Nguồn: `2026-10-31-jira.txt` (snapshot có cột sprint) — mọi issue Team 1 chưa Done thuộc sprint active (Sprint 4 → Sprint 5).
Nhánh code: `claude/weekly-team1-2026-10-31` (đích `develop`), không mở PR —
[compare](https://github.com/Banh-Van-Hiep/vietnamese-legal-rag/compare/develop...velvetforest:vietnamese-legal-rag:claude/weekly-team1-2026-10-31?expand=1).
Đề xuất cũ: T1 (test hồi quy BM25) gộp vào VLRA-35; T2 (test `chunk_document`) gộp vào VLRA-50 (dùng lại chunker khi thử chunk size); T3 (baseline eval) = VLRA-48/49.

### [x] T1. VLRA-35 Sửa lỗi và chuẩn hóa chunk_id/metadata Retrieval ↔ Reranker
- **Lý do:** AC: Reranker nhận đủ chunk_id + metadata, không lỗi parse. 3 test Dense/embedding đang fail trên `develop`.
- **File:** `team1_data/retrieval/dense.py`, `embedding.py`, `tests/test_retrieval_reranker_contract.py`, `tests/test_bm25_retrieval.py`.
- **Tiêu chí xong:** toàn corpus + đầu ra BM25/Hybrid qua `team2_rag.reranker._validate`; 3 test fail → pass. **Ước lượng:** S
- **Kết quả:** DONE VLRA-35 (commit `2166789`, `31e64cb`), test 447/3 fail → 453/0 fail.

### [!] T2. VLRA-37 Phối hợp kiểm thử luồng truy xuất trong E2E MVP
- **Lý do:** cần luồng truy xuất ổn định khi Backend gọi API.
- **File dự kiến:** `tests/test_retrieval_e2e.py` (mới): build BM25 trên corpus thật → Hybrid → reranker validator → kiểm tra API contract `contracts/v0.1`.
- **Tiêu chí xong:** test E2E phần truy xuất pass offline; phần cần Team 3 chạy Frontend/Backend thật ghi rõ. **Ước lượng:** M
- **Kết quả:** [!] làm một phần (commit `e83f22e`, 453 → 456 passed): luồng truy xuất E2E chạy ổn với corpus thật nhưng model là bản giả (HF bị chặn) và chưa chạy cùng Backend/Frontend Team 3 → không chuyển Done.

### [x] T3. VLRA-36 Golden Dataset Phase 1 (100–150 câu)
- **Lý do:** cần Dev Set cố định cho VLRA-48..53; hiện có 40 câu (Team 2, `team2_rag/data/golden/golden_phase1_30cai.json`).
- **File dự kiến:** `team1_data/golden/golden_phase1.json` (mới, Team 1), test kiểm tra schema + mọi `gold_chunk_ids` tồn tại.
- **Tiêu chí xong:** ≥ 100 câu, mỗi câu có `gold_chunk_ids` + Điều/Khoản nguồn + đáp án trích nguyên văn chunk; không bịa nội dung. **Ước lượng:** L
- **Kết quả:** DONE VLRA-36 (commit `7a61fbd`): 110 câu, test 456 → 461 passed. 70 câu mới cần rà soát pháp lý cách hỏi.

### [x] T4. VLRA-48 Pipeline đánh giá Retrieval
- **File dự kiến:** `scripts/eval_retrieval.py` (Recall@10, MRR@20, adapter hybrid), `evaluation/README.md`, `tests/test_eval_retrieval.py`. **Ước lượng:** M
- **Kết quả:** DONE VLRA-48 (commit `2bbb7a3`), test 461 → 466 passed.
### [x] T5. VLRA-49 Đánh giá BM25 / Dense / Hybrid (Recall@5/10/20, MRR@20) — phụ thuộc T4. **Ước lượng:** M
- **Kết quả:** DONE VLRA-49 (commit `148a6ee`): Hybrid k=60 R@5 0.876 / MRR@20 0.829 > BM25 0.863 / 0.814 > Dense-LSA 0.852 / 0.757. Dense dùng LSA offline (HF 403).
### [x] T6. VLRA-50 Chunk size 384/512 × overlap 32/64 — phụ thuộc T4. **Ước lượng:** M
- **Kết quả:** DONE VLRA-50 (commit `2f81fd6`): chênh lệch không đáng kể (chỉ 14 Khoản > 384 token); đề xuất giữ chunk theo Khoản, cắt 384/64 khi cần.
### [x] T7. VLRA-51 RRF k (cơ sở k=60) — phụ thuộc T5. **Ước lượng:** S
- **Kết quả:** DONE VLRA-51 (commit `f60c9cf`): k ≥ 20 ổn định, giữ k = 60.
### [!] T8. VLRA-52 So sánh mô hình Embedding — phụ thuộc T5; HuggingFace bị chặn (403) trong môi trường chạy → có thể chỉ làm được một phần. **Ước lượng:** M
- **Kết quả:** [!] làm một phần (commit `4f66fcc`): chỉ so được embedder offline (hash, LSA 128–768; LSA 384 cân bằng nhất). Model thật không tải được (HuggingFace 403) → không chuyển Done.
### [ ] T9. VLRA-53 Chọn cấu hình Retrieval v2 — phụ thuộc T5–T8. **Ước lượng:** S
