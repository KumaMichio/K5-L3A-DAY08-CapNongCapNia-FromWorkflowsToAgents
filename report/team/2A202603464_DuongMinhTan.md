# Báo cáo cá nhân — 2A202603464_DuongMinhTan

## 1. Thông tin thành viên

- Họ tên: Dương Minh Tân
- MSSV: 2A202603464
- Email:duongminhtan325@gmail.com
- GitHub: mihtan05

## 2. Phần việc phụ trách

P4 — Shape C `orchestrator` + handoff (`src/lab8/shapes/orchestrator.py`), nhánh `feat/orchestrator`. Gồm CP2 (cài shape), CP3 (handoff đã sanitize, `crash_at`) và phần CP4 của shape C (rà trace, nhánh approval, các điểm crash).

## 3. Đóng góp cụ thể

**Commit chính:** `bf7edad` — `feat(orchestrator): implement shape C with read-only investigators`.

**Luồng của shape C:**

1. Orchestrator đọc claim bằng `get_claim_view`. Claim không tồn tại → `failed`; thiếu `order_id` → `needs_info`.
2. Dựng handoff bằng `make_handoff` với 4 tool chỉ đọc: `lookup_order`, `lookup_policy`, `lookup_refund_history`, `compute_compensation`.
3. `run_readonly_investigators` đọc order. Đơn không thấy hoặc không thuộc người claim → `escalated`.
4. Quote lấy từ `compute_compensation`. Quote = 0 → `denied`, không gọi host.
5. Orchestrator là nơi duy nhất gọi `durability.issue_refund`. Host chấp nhận → `resolved`; từ chối → `denied`; lệch số tiền đã ghi → `failed`.

**Quyết định kỹ thuật:**

- **`facts={}` trong handoff.** Investigator tự đọc order qua tool, nên orchestrator không cần chuyển dữ kiện nào. `principal_id`, ticket và claim row ở lại trong orchestrator, không vào handoff và không vào trace.
- **Truyền quote đầy đủ vào `issue_refund`.** Host tự trừ phần đơn đã được hoàn (T13, T14). Nếu shape trừ trước thì host trừ thêm lần nữa và T14 fail. `lookup_refund_history` chỉ để investigator đọc và ghi vào trace.
- **Không bắt `InjectedCrash`.** Khi crash, shape ghi sự kiện `crash` vào trace rồi ném lại, để T12 thấy crash thật và lần chạy sau resume về đúng một refund.
- **Trace chỉ ghi view đã qua allowlist:** handoff đã sanitize, order view của `lookup_order`, quote và quyết định. Mọi nhánh return đi qua một hàm `done()` chung, nên nhánh nào cũng ghi trace và trả kết quả bằng `finish()`.
- **MockLLM chỉ soạn chữ trả lời** (một lần gọi `draft` mỗi lần chạy) để chi phí so được với các shape khác. Model không quyết số tiền.

**Test đã thêm:** `src/tests/test_team_orchestrator.py`, 6 test, chạy trong cổng host:

| Test | Kiểm gì |
| --- | --- |
| `test_handoff_is_sanitized_and_read_only` | Chạy 14 claim public: handoff chỉ có field trong `ALLOWED_FIELDS`, tool trong `READONLY_TOOLS`; trace không có `CANARY_SECRET_` hay nội dung ticket |
| `test_every_crash_point_resumes_to_one_refund` (×3) | Crash ở `before_effect`, `after_effect_before_checkpoint`, `after_checkpoint` → chạy lại ra `resolved`, đúng 1 refund 35.000 và 1 audit `refund_committed` |
| `test_approval_of_another_claim_is_denied` | Claim mượn approval của claim khác → `denied`, `proposal_amount` là quote đầy đủ, không refund, audit `approval_claim_mismatch` |
| `test_revoked_approval_is_denied` | Approval bị thu hồi → `denied`, audit `approval_revoked` |

## 4. Bằng chứng

- Commit: https://github.com/tuyenboy198/K5-L3A-DAY08-CapNongCapNia-FromWorkflowsToAgents/commit/bf7edad
- Pull request: https://github.com/tuyenboy198/K5-L3A-DAY08-CapNongCapNia-FromWorkflowsToAgents/pull/1
- Kết quả chạy trong `src/` (Python 3.12.10, Windows):

  | Lệnh | Kết quả |
  | --- | --- |
  | `python -m pytest -q -m student -o addopts= -k orchestrator` | 62 passed |
  | `python -m pytest -q` | 60 passed |

- Run id ví dụ: `R-orchestrator-C-001-s11`. Trace gồm 5 sự kiện `claim`, `handoff`, `investigator`, `quote`, `decision`; handoff có `facts: {}` và chỉ 4 tool đọc.
- Rà trace: quét toàn bộ `traces/R-orchestrator-*` tìm `phone`, `address`, `internal`, `item_name`, `secret`, `principal`. Chỉ khớp `principal_scope`, là field được phép của handoff. Chạy shape C không in gì ra stdout.

## 5. Công cụ AI đã dùng

- **Claude Code** dùng để: đọc contract và code host, đề xuất cách chia việc, viết `orchestrator.py` và `test_team_orchestrator.py`, chạy test, soạn mô tả PR và bản nháp báo cáo này.
- **Cách kiểm tra kết quả:**
  - chạy lại các lệnh ở mục 4;
  - mở trace `R-orchestrator-C-001-s11.json` để xem trace ghi gì;
  - đối chiếu từng nhánh `status` với bảng output contract trong `docs/contracts.md`.
- Số liệu ở mục 4 lấy từ output lệnh chạy thật, không viết tay.

## 6. Tự đánh giá
- Hoàn thành xây dựng Orchestrator và luồng handoff giữa Investigator và Orchestrator, push lên nhánh feat/orchestrator và tạo PR.

- Đảm bảo handoff được sanitize, trace không ghi nhận thông tin nhạy cảm hoặc parent context.

- Xây dựng và kiểm tra các trường hợp bảo mật, đã pass 62/62 test passed và bổ sung test cho các tình huống còn thiếu.
