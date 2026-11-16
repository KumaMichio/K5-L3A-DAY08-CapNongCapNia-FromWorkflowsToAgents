# Báo cáo cá nhân — 2A202603420_PhanSyHung

## 1. Thông tin thành viên

- Họ tên: Phan Sỹ Hùng
- MSSV: 2A202603420
- Email: hungphan120304@gmail.com
- GitHub: KumaMichio

## 2. Phần việc phụ trách

Ledger / policy / crash — QA ba điều kiện must-pass của nhóm:

- Cổng duyệt của host (`lab8/policy.py` + `lab8/durability.py`): không refund khi thiếu approval hợp lệ (hết hạn, bị thu hồi, pending, approval của claim khác).
- Trần hoàn tiền theo đơn (stacking rule): đơn đã hoàn đủ không trả thêm (T13), quyền lợi lớn hơn chỉ trả phần chênh (T14), trần theo số tiền đã trả của đơn.
- An toàn khi crash: ba cửa sổ crash (`before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`) không bao giờ tạo quá một refund; chạy crash suite CP4.
- Kiểm T11 (gọi lại cùng claim) và T12 (crash rồi resume) trên cả ba shape của nhóm.

## 3. Đóng góp cụ thể

- Commit chính: `8986fa8a17e5d77e261d4717f48d14d35a442c88` (nhánh `test/durability`).
- Test đã thêm: `src/tests/test_team_durability.py` (21 test, trong đó 15 test host-level chạy ngay trong cổng host và 6 test shape-level T11/T12 tự kích hoạt khi shape hết stub — dùng `pytest.skip` khi shape còn trả `not_implemented` để cổng host luôn xanh trước khi PR của B, C merge).
- Chạy crash suite CP4: `python -m lab8.crash_test --count 20 --out reports/crash.json` → `crash_safety 20/20`; commit file `src/reports/crash.json` đúng dạng máy sinh ra, không sửa tay.
- Quyết định kỹ thuật: test cap theo đơn viết ở tầng `policy.authorize` (tham số hóa `proposed / already / paid`) thay vì lặp lại các test `issue_refund` đã có của host, để vừa phủ nhánh `order_already_refunded`, `non_positive_amount`, trần theo `paid_vnd`, vừa không trùng với `test_order_cap_and_approval_binding.py`.

## 4. Bằng chứng

- Commit: `8986fa8a17e5d77e261d4717f48d14d35a442c88` trên nhánh `test/durability`.
- Test: `src/tests/test_team_durability.py` — các test `test_expired_approval_denies_even_on_retry`, `test_non_valid_approval_status_is_refused`, `test_approval_of_another_claim_never_pays`, `test_approval_lower_than_quote_caps_the_payout`, `test_authorize_cap_math`, `test_crash_then_resume_pays_exactly_once`, `test_resume_with_a_different_amount_is_a_conflict_not_a_second_refund`, `test_t11_shape_retry_keeps_one_refund`, `test_t12_shape_crash_resume_does_not_double_pay`.
- Kết quả chạy: `python -m pytest -q` → 69 passed, 6 skipped (6 skip là T11/T12 cho 3 shape còn stub trên `main` tại thời điểm commit); `crash_safety 20/20` trong `src/reports/crash.json`.

## 5. Công cụ AI đã dùng

- Claude Code (Claude Fable 5): đọc `durability.py`, `policy.py`, `metrics.py` và data public để liệt kê các nhánh cần phủ; gợi ý và viết khung test theo phân công trong TEAM.md; chạy pytest và crash suite.
- Tự kiểm tra: chạy lại `python -m pytest -q` và `python -m pytest -q tests/test_team_durability.py` trên máy mình; đối chiếu từng assert với code thật của `policy.authorize` và `durability.issue_refund` (ví dụ thứ tự cap: trừ `already` → trần approval → trần `paid - already`); đối chiếu số tiền kỳ vọng với nhãn trong `data/public_claims.jsonl` (C-007 denied, C-008 trả 20000, C-013 denied, C-014 trả 120000).

## 6. Tự đánh giá

- Hoàn thành phần QA must-pass theo phân công: cổng approval, trần theo đơn và crash suite 20/20 đều có test và bằng chứng máy sinh.
- Phần T11/T12 trên shape `single` và `orchestrator` mới ở trạng thái "tự kích hoạt khi shape merge"; cần chạy lại toàn bộ suite sau khi PR của Hưng và Tân vào `main` rồi báo kết quả cho người phụ trách shape.
