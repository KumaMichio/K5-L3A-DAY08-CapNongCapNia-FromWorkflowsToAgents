# Judge audit

Chạy: `python -m lab9.judge --csv <file> --audit 5` (backend REPLAY, verdict judge lưu sẵn trong CSV). Lớp dương = FAIL (việc của judge là *tìm* reply lỗi).

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | **Đạt** (tp 24, fp 4, fn 6, tn 66) | **dùng**, chỉ để giám sát giọng văn, không đặt làm gate tiền |
| helpful | 100 | 0.375 | 1.000 | **0.300** | **Không đạt** (tp 9, fp 0, fn 21, tn 70) | **loại** |

Tỉ lệ lỗi hiệu chỉnh Rogan-Gladen: tone quan sát 0.28 → 0.30; helpful quan sát **0.09 → 0.30**. Judge helpful báo lỗi ít hơn thực tế khoảng 3 lần.

## Audit thủ công (10/10 bất đồng của tone + 5 mẫu của helpful)
| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú / sửa rubric |
|---|---|---|---|---|---|
| 1 | H-008 "Em đã hoàn tiền cho anh rồi nha…" | PASS | FAIL | Người | Xưng "em" + "nha" quá suồng sã. Rubric: liệt kê đại từ được phép (anh/chị, quý khách) và cấm tiểu từ "nha/nhé" trong khiếu nại. |
| 2 | H-017 "Dạ, bạn ơi LogiX đã hoàn 25.000đ…" | PASS | FAIL | Người | Xưng "bạn" với khách. Cùng quy tắc đại từ như #1; thêm 1 ví dụ âm vào few-shot. |
| 3 | H-029 "…không cần nhắn thêm." | PASS | FAIL | Người | Judge chỉ thấy "Dạ, vui lòng" lịch sự ở đầu câu. Rubric: chấm *cả câu*, câu ra lệnh / chặn khách liên hệ = FAIL dù có kính ngữ. |
| 4 | H-042 "Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ." | FAIL | PASS | Người | Judge phạt vì "thiếu xin lỗi". Rubric: xin lỗi **không bắt buộc** khi đã giải quyết xong; ngắn gọn + đủ ý = PASS. |
| 5 | H-051 "LogiX đã refund 90.000đ…" | FAIL | PASS | Người | Style guide CS LogiX cho phép "refund". Rubric: thêm whitelist thuật ngữ tiếng Anh được phép. |
| 6 | H-063 "…và sẽ hoàn thêm cho anh/chị ạ." | PASS | FAIL | Người | Hứa ngoài kết quả hệ thống. Đây là lỗi **nội dung** (gần FM-08), không phải giọng văn: chuyển sang grader code (`ReplyMatchesLedger` + cấm cụm "sẽ hoàn thêm"), không bắt judge tone gánh. |
| 7 | H-070 "…ạ 😂😂" | PASS | FAIL | Người | Rubric: emoji trong phản hồi khiếu nại = FAIL. |
| 8 | H-081 "Dạ, đơn O-107 chưa đủ điều kiện…" | FAIL | PASS | **Judge** | Nhãn người sai (đọc nhầm ticket). Hành động: **sửa nhãn** human → FAIL trong bộ nhãn kế tiếp; ghi vào changelog nhãn, không sửa CSV public đang dùng để chấm. |
| 9 | H-088 "Dạ, dạ, LogiX đã hoàn…" | FAIL | PASS | Người (lỗi nhỏ) | Lặp "Dạ" do gõ lỗi, không xúc phạm. Rubric: lỗi chính tả nhẹ không làm FAIL tone; nếu muốn bắt, dùng grader code riêng. |
| 10 | H-094 "Da, LogiX da hoan…" (mất dấu) | PASS | FAIL | Người | Rubric: tiếng Việt không dấu / dịch máy = FAIL; có thể kiểm bằng code (tỉ lệ ký tự có dấu). |
| 11 | HL-015 "đã hoàn 55.000đ…" (ledger 40.000) | PASS | FAIL | Người | Judge helpful không thấy ledger nên không thể biết số sai. |
| 12 | HL-016 / HL-028 / HL-035 reply dài, xin lỗi lặp 2–3 lần, số tiền sai | PASS | FAIL | Người | Judge bị **verbosity bias**: câu xin lỗi dài được chấm "helpful" bất kể số tiền sai. |
| 13 | HL-047 "Ok bạn, đơn O-515 xử lý rồi nhé." | PASS | FAIL | Người | Không nêu kết quả, số tiền hay thời gian; judge vẫn cho PASS. |

## Kết luận
- **tone_ok dùng được**: κ 0.757, P 0.857, R 0.8 đều trên sàn. 9/10 bất đồng là judge sai và sửa được bằng rubric (đại từ, emoji, câu ra lệnh, whitelist thuật ngữ); 1/10 (H-081) là nhãn người sai.
- **helpful bị loại**, không được làm gate: recall 0.3 nghĩa là judge bỏ lọt **21/30** reply lỗi (fn = 21). P = 1.0 chỉ vì judge gần như không bao giờ nói FAIL (9/100). κ 0.375 < 0.6. Phần lớn các ca bị lọt là reply **nêu sai số tiền** so với ledger. Judge không có ledger trong ngữ cảnh nên đây là việc của code: `ReplyMatchesLedger` (FM-08) đã thay vai trò này. Nếu dùng judge helpful làm gate, tỉ lệ lỗi quan sát 0.09 sẽ che tỉ lệ thật ≈ 0.30 (Rogan-Gladen).
- Tiền và approval không bao giờ chấm bằng judge, kể cả judge đã qua calibration.
- Rủi ro còn lại: judge chỉ được kiểm trên dữ liệu replay đã công khai; sau khi sửa rubric phải gán nhãn người **mới** (held-out) rồi calibrate lại, không đo lại trên chính 100 dòng đã dùng để sửa rubric.
