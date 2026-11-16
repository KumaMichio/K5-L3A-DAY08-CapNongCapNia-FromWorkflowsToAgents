# Báo cáo cá nhân — 2A202603430_DuongThiHue

## 1. Thông tin thành viên

- Họ tên: Dương Thị Huệ
- MSSV: 2A202603430
- Email: duonghue2004yp@gmail.com
- GitHub: dhuee10

## 2. Phần việc phụ trách

Vai EV (Eval / benchmark / báo cáo), nhánh `eval/report`:

- CP1: dựng khung `report/team/group_report.md`.
- CP2: điền research card (`report/team/research_card.md`), chọn R2 · Failure taxonomy (MAST).
- CP3: script quét trace tìm secret/PII cho cả nhóm (`src/scripts/trace_scan.py`) và test `src/tests/test_team_trace_scan.py`.
- CP4: bonus — nhóm chưa đăng ký topic.
- CP5: chạy benchmark 4 shape × 5 seed và hidden selfcheck, cùng nhóm điền ADR, hoàn thiện group report.

## 3. Đóng góp cụ thể

- Commit `39b683f` — `feat(eval): add trace/secret/PII scanner and team trace-scan test`:
  - `src/scripts/trace_scan.py`: dựng danh sách chuỗi cấm từ chính dữ liệu (`parent_secret`, header, `forbid_substrings`, SĐT / địa chỉ / ghi chú nội bộ / tên hàng của mọi order) cộng regex `CANARY_SECRET_*`, `CANARY_INTERNAL_*`, `Bearer …`, SĐT 10 số và key JSON của field thô. Hai chế độ: quét thư mục `traces/`, hoặc `--run` chạy lại shape trên SQLite mới rồi quét result + trace + file `<run_id>*` + stdout. Output chỉ in giá trị đã che để scanner không tự làm lộ secret.
  - `src/tests/test_team_trace_scan.py` (55 test, chạy trong cổng `python -m pytest -q`): scanner bắt được leak cài sẵn (7 loại), không báo nhầm trace sạch, quét file phụ `<run_id>*`; 3 shape × 14 claim public phải sạch; swarm làm đối chứng.
  - `src/reports/ablation_r2_swarm.json`: kết quả `lab8.benchmark` cho ablation R2.
- Quyết định kỹ thuật:
  - Danh sách cấm lấy từ dữ liệu chứ không hard-code, nên dùng được cho `student_drop/` (không có nhãn).
  - Quét cả stdout, vì contract cấm in PII ra stdout nhưng grader không thấy stdout.
  - So khớp token theo biên từ để tên hàng ngắn ("Sach", "Ghe") không báo nhầm bên trong từ khác.
  - Chọn R2 cho research card vì đo được ngay trên swarm có sẵn: lỗi duy nhất của swarm trên public (`R-swarm-C-002-s55`, T02 seed 55) là lỗi kiểm chứng (tin số ngày trong ticket, trace có event `model_override`).

## 4. Bằng chứng

- Commit: `39b683f` trên nhánh `eval/report`.
- Test: `python -m pytest -q` → 109 passed (54 cổng host + 55 test của mình).
- `python -m scripts.trace_scan --run swarm --seeds 11,55` → `trace_scan CLEAN | trials=28 | errors=0 | findings=0`.
- Kiểm thử scanner với shape workflow của Tuyên (nhánh `feat/workflow`, chạy tạm trên máy, không commit): `--run workflow --seeds 11,22,33,44,55` → `CLEAN, trials=70, findings=0`.
- Ablation R2: `src/reports/ablation_r2_swarm.json` — swarm pass 0.986, pass^5 0.929, seed min–max 0.929–1.000, variance 0.000816, cost/success 49.57 VND mô phỏng.

## 5. Công cụ AI đã dùng

- Claude Code: đọc repo, gợi ý cấu trúc scanner và test, viết nháp research card và khung báo cáo.
- Cách tự kiểm tra: chạy `python -m pytest -q` (xanh), chạy scanner trên swarm và trên workflow của nhóm; cố ý cài leak vào trace giả để chắc scanner bắt được; mọi số trong research card đọc lại từ `src/reports/ablation_r2_swarm.json` và kiểm trace `R-swarm-C-002-s55` bằng `python -m lab8.run` (ra `resolved`, 20.000 VND, có event `model_override`). Thông tin về paper MAST (14 failure mode, 3 nhóm) cần đối chiếu lại với bản arXiv trước khi nộp.

## 6. Tự đánh giá

Xong CP1–CP3 của vai EV. Còn lại CP5: benchmark 4 shape và hidden selfcheck sau khi workflow, single, orchestrator merge vào `main`, rồi điền số vào ADR, group report và nửa workflow của ablation R2.
