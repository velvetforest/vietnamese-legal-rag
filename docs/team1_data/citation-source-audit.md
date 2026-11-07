# Kiểm tra nguồn trích dẫn (VLRA-64)

Ngày kiểm: 07/11/2026 · Người thực hiện: Team 1 (Thành viên A) · Trạng thái: **chưa hoàn tất**, vì chưa kiểm được trực tuyến (xem mục 5).

## 1. Phạm vi và dữ liệu đầu vào

| Nguồn | Ghi chú |
| --- | --- |
| `data/doanh-nghiep/registry/documents.json` | 8 văn bản |
| `data/doanh-nghiep/processed/chunks.jsonl` | 2.576 chunk, sha256 `042bd7f1…5466`, **trùng** hash corpus của lượt chạy Team 2 |
| `data/doanh-nghiep/interim/vbhn-67-vbhn-vpqh-v1.txt` | Dùng chú thích `[n]` của VBHN để biết điều/khoản nào đã bị sửa sau Luật 59/2020 |
| `team2_rag/data/evaluation/colab-20261102/` | Lượt eval gần nhất của Team 2 (02/11/2026), gồm 110 câu, nhánh BGE truncate; **không gọi LLM** |
| `team2_rag/data/golden/golden_sample_5qa.json` | Bộ 5 câu mà `test_answer_citation_accuracy.py` dùng |
| `docs/team2_rag/citation-specification.md` | Form citation 9 trường |

Lượt chạy ngày 02/11 không sinh câu trả lời LLM, nên báo cáo chỉ kiểm được hai lớp:
(a) nhãn `citation` của Golden so với `gold_chunk_ids`;
(b) top-5 context (theo `context_cutoff = 5`) mà LLM sẽ nhận, xem có rủi ro trích sai hay không.

## 2. Bảng loại lỗi citation (bàn giao cho VLRA-65)

| Mã | Loại lỗi | Định nghĩa vận hành | Cách phát hiện |
| --- | --- | --- | --- |
| E1 | Sai Điều | Điều được trích không phải điều chứa căn cứ. Cũng tính lỗi khi Golden/context không có điều đúng | So `(document_id, article)` của citation với gold |
| E2 | Sai Khoản/Điểm | Đúng Điều nhưng khoản/điểm được trích lệch với gold (thiếu hoặc thừa) | So `clause`/`point` khi đã khớp Điều |
| E3 | Sai phiên bản sửa đổi | Trích Luật 59/2020 gốc cho điều/khoản đã bị Luật 03/2022 hoặc 76/2025 sửa, bổ sung, bãi bỏ. Cũng tính lỗi khi gold và citation chỉ khác văn bản (59/2020 hay VBHN 67) trong khi nội dung khác nhau | Có chú thích `[n]` tại điều/khoản tương ứng trong VBHN 67 |
| E4 | URL sai/chết | `source_url` không mở được, không trỏ đúng văn bản/số hiệu, hoặc không phải nguồn chính thức | HTTP check và so số hiệu trên trang |
| E5 | Văn bản hết hiệu lực | Trích văn bản/điều đã hết hiệu lực tại ngày hỏi, hoặc `legal_status`/`effective_date` không đúng nguồn chính thức | So với trang vbpl.vn hoặc Công báo |
| (phụ) | Nhãn thiếu tên văn bản | Nhãn chỉ có "Điều N - <tên điều>", không nêu văn bản. Người đọc không xác định được nguồn | Không map được tên văn bản |

Quy ước: **khi luật 59/2020 và VBHN 67 có nội dung giống hệt nhau thì không tính E3**. Trong 906 chunk Luật 59/2020, có 861 chunk có nội dung giống hệt chunk cùng Điều/Khoản trong VBHN 67 (bỏ qua khoảng trắng và chú thích); chỉ **45 chunk khác nội dung**.

## 3. Rà 8 văn bản trong registry

Chưa kiểm trực tuyến được: vbpl.vn trả về 403 do CDN của site chặn bot (`Ws-Action: bot`). Các host congbao.chinhphu.vn, xaydungchinhsach.chinhphu.vn và thuvienphapluat.vn bị proxy của môi trường chặn (`CONNECT tunnel failed, 403`). Theo quy định, tôi không vòng qua các chặn này.
Dưới đây là phần kiểm **offline**: so registry với phần đầu và điều khoản hiệu lực trong văn bản đã tải (`interim/`).

| Văn bản | Số hiệu & ngày ban hành khớp văn bản | effective_date | legal_status | URL (offline) | Phát hiện |
| --- | --- | --- | --- | --- | --- |
| 59/2020/QH14 | Khớp | 2021-01-01: khớp theo đầu VBHN 67 | het_hieu_luc_mot_phan: hợp lý, vì đã bị 03/2022 và 76/2025 sửa | vbpl.vn (chính thức) | — |
| 76/2025/QH15 | Khớp | 2025-07-01: khớp Điều 3 | con_hieu_luc | Công báo | — |
| 67/VBHN-VPQH | Khớp | null (VBHN không có ngày hiệu lực riêng) | con_hieu_luc | Công báo | Xem lưu ý L1, L2 |
| 7566/VBHN-BKHĐT | Khớp | 2021-04-01: là ngày hiệu lực của NĐ 47/2021 | het_hieu_luc_mot_phan: **chưa kiểm** | Slug URL là `nghi-dinh-so-47-2021-nd-cp-33620/35577` | **Nghi E4**: URL có vẻ trỏ trang NĐ 47/2021 chứ không phải VBHN 7566, cần mở để xác nhận |
| 168/2025/NĐ-CP | Khớp | 2025-07-01: khớp khoản 1 điều hiệu lực | con_hieu_luc | Cổng TTĐT Chính phủ, không phải Công báo/vbpl | Nên thay bằng URL vbpl/Công báo |
| 122/2021/NĐ-CP | Khớp | 2022-01-01: **chưa kiểm**, vì bản trích không có điều hiệu lực | het_hieu_luc_mot_phan: hợp lý theo NĐ 288/2026 | Công báo | — |
| 288/2026/NĐ-CP | Khớp | 2026-07-21: khớp ("kể từ ngày ký") | con_hieu_luc | **thuvienphapluat.vn**, không phải nguồn chính thức | Nghi E4 (nguồn không chính thức) |
| 68/2025/TT-BTC | Khớp | 2025-07-01: khớp | het_hieu_luc_mot_phan: **chưa kiểm** (TT 121/2026 chưa có trong corpus) | vbpl.vn | — |

Lưu ý dữ liệu Team 1:
- **L1.** Registry để `effective_date = null` cho VBHN 67, nhưng chunk ghi `2025-08-15`. Nguyên nhân: `chunk_documents.py:220` lấy `issued_date` khi `effective_date` rỗng. Điểm lệch này có chủ ý, nhưng Backend/Frontend không được hiển thị giá trị này là "ngày hiệu lực". Nó làm 65/110 câu Golden lệch metadata chunk so với registry.
- **L2.** Registry VBHN 67 ghi `article_count = 220`, `last_article = "3"` vì tính cả Điều 11 (Luật 03/2022) và Điều 3 (Luật 76/2025) về chuyển tiếp ở cuối văn bản. Chunk chỉ đến Điều 218, nên **hai điều chuyển tiếp này không có trong index**. Câu hỏi về chuyển tiếp sau sửa đổi sẽ dễ bị trích sai phiên bản (E3).

## 4. Đối chiếu citation của lượt eval 02/11/2026

### 4.1 Nhãn Golden và gold chunk (110 câu + 5 câu mẫu)

| Loại | Số câu | Câu |
| --- | --- | --- |
| E1 Sai Điều | 0 | — |
| E2 Sai Khoản/Điểm | 1 | gold_014: nhãn "Khoản 2 Điều 24" nhưng gold gồm khoản 1–4 Điều 24 |
| E3 Sai phiên bản | 3 | gold_011: Điều 16, gold là bản 59/2020; khoản 1, 4, 5 đã bị 76/2025 sửa. gold_012: Điều 20, khoản 3 đã sửa. gold_013: Điều 23, thiếu khoản 10 do 76/2025 bổ sung |
| (phụ) Nhãn thiếu tên văn bản | 5 + 1 | gold_011 đến gold_015 (nhãn "Điều N - <tên điều>"); câu mẫu gold_041 không có nhãn, đúng vì là câu `insufficient_context` |
| Chunk gold không tồn tại | 0 | — |
| `gold_citations` (bộ 5 câu) lệch metadata chunk | 0 | 9 trường đều khớp chunk |

Cả 4 câu có lỗi E2/E3 đều ở nhóm `team2_reviewed`.

### 4.2 Rủi ro trong top-5 context (BGE truncate, 110/110 câu chạy xong)

| Chỉ số | Hybrid top-5 | Sau rerank top-5 |
| --- | --- | --- |
| Đủ gold trong context | 88 | 85 |
| Thiếu gold, context có cùng khoản nhưng **khác phiên bản** (rủi ro E3) | 1 | 4 (gold_005, 011, 053, 054) |
| Thiếu gold, context có **cùng Điều, khác khoản** (rủi ro E2) | 11 | 11 |
| Thiếu gold, context **không có Điều đúng** (rủi ro E1) | 12 | 15 |
| Context có chunk Luật 59/2020 **đã bị sửa** (rủi ro E3 thật) | 6 | 7 (gold_011, 026, 031, 039, 054, 082, 088) |
| Context chứa **cả hai phiên bản** của cùng một khoản | 81 | 83 |

Nhận xét:
- Context chứa cả hai phiên bản của cùng một khoản ở 83/110 câu. Khi nội dung giống nhau, việc này phí chỗ trong context. Khi nội dung khác nhau, LLM có thể trích bản gốc đã bị sửa (E3).
- Trong 4 ca "khác phiên bản", gold_005, 053 và 054 có nội dung giống hệt nhau giữa hai phiên bản. Recall thấp hơn ở các ca này là do Golden chỉ chấp nhận một `chunk_id`, không phải lỗi nội dung. Riêng gold_011 thì gold là bản cũ, nên câu trả lời đúng sẽ bị chấm sai.

## 5. Mục chưa kiểm được và lý do

1. Kiểm trực tuyến `source_url` (HTTP, khớp số hiệu) và `legal_status`/`effective_date` theo vbpl.vn cho cả 8 văn bản: bị chặn (vbpl.vn chặn bot; các host khác bị proxy chặn). Cần chạy lại từ máy có truy cập, hoặc mở các host này trong môi trường.
2. Trạng thái hiệu lực của 7566/VBHN-BKHĐT và 68/2025/TT-BTC, và ngày hiệu lực của 122/2021/NĐ-CP: corpus không đủ căn cứ.
3. Lỗi citation trong câu trả lời LLM thật: lượt 02/11 không gọi LLM. Mục 4.2 chỉ là rủi ro ở mức context.

## 6. Đề xuất

- **Team 1:** (a) bổ sung `amended_by`/`amendment_notes` cho chunk Luật 59/2020 từ chú thích VBHN 67 (hiện 2.576/2.576 chunk đều để rỗng); (b) xem lại việc bỏ hai điều chuyển tiếp ở L2; (c) thay URL nguồn không chính thức của 168/2025 và 288/2026, và xác nhận URL của 7566.
- **Chuyển Team 2** (chỉ ghi nhận, Team 1 không sửa): xem lại gold của gold_011–014. Cho phép group gold nhận chunk tương đương giữa 59/2020 và VBHN 67 khi nội dung trùng. Cân nhắc khử trùng hai phiên bản trong context, ưu tiên VBHN.
