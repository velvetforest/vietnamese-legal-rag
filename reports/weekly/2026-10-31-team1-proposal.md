# Đề xuất task Team 1 – 2026-10-31

Duyệt bằng: `duyệt 1,3` · `bỏ 2` · `sửa 2: <ý kiến>`. Nhánh đích: `pr_targets[team1]` (theo config).

### [x] T1. Sửa `BM25Retriever._search` trả list + test hồi quy Hybrid
- **Lý do:** Trên `main`, `_search` trả `dict` nhưng `retrieve()` bọc thêm lần nữa và `HybridRetriever` dùng `_search` như list → kết quả BM25/Hybrid sai (liên quan VLRA-35/37). Fix đang nằm ở nhánh chưa merge.
- **File dự kiến đổi:** `team1_data/retrieval/bm25.py`, `tests/test_bm25_retrieval.py`, `tests/test_hybrid_retrieval.py`.
- **Tiêu chí xong:** Test mới: `BM25Retriever._search` trả `list[dict]`; `retrieve()["results"]` là list phẳng; Hybrid RRF nhận đủ kết quả BM25. `pytest tests/test_bm25_retrieval.py tests/test_hybrid_retrieval.py tests/test_retrieval_edge_cases.py` pass, không có lỗi mới so với baseline.
- **Ước lượng:** S

### [ ] T2. Thêm test cho `chunk_document()` (data/doanh-nghiep/chunk_documents.py)
- **Lý do:** Hàm mới dùng cho tích hợp preprocessing↔retrieval (commit f6c9672) nhưng chưa có test; đảm bảo `chunk_id` duy nhất và gắn đúng `article_id` (DoD VLRA-17/35).
- **File dự kiến đổi:** `data/doanh-nghiep/chunk_documents.py` (chỉ thêm hàm nếu đích chưa có), `tests/test_chunk_documents.py` (mới).
- **Tiêu chí xong:** Test với văn bản mẫu nhỏ (2 Điều, có Khoản/Điểm): số chunk đúng, `chunk_id` không trùng, mọi chunk có `article_id` hợp lệ. Test pass.
- **Ước lượng:** S

### [ ] T3. Chạy baseline đánh giá retrieval bằng `scripts/eval_retrieval.py` (VLRA-48/49)
- **Lý do:** VLRA-48/49 hạn 2026-11-01, script đánh giá đã có; cần một lệnh tái lập được + test cho phần tính Recall@5/20, MRR@10 trên golden split.
- **File dự kiến đổi:** `tests/test_eval_retrieval.py` (bổ sung case), `team1_data/docs_1/` (ghi kết quả baseline BM25/Dense/Hybrid nếu chạy được offline).
- **Tiêu chí xong:** `pytest tests/test_eval_retrieval.py` pass; có file kết quả baseline ghi rõ commit, cấu hình, số câu hỏi. Nếu không tải được model embedding offline thì chỉ báo cáo BM25 và ghi rõ giới hạn.
- **Ước lượng:** M
