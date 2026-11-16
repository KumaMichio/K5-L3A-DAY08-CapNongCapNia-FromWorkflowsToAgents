# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: CapNongCapNia
- Lớp: L3A
- Repo: `K5-L3A-DAY08-CapNongCapNia-FromWorkflowsToAgents`, nhánh nộp `main`
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`): `fcfac65` (code 3 shape; Tuyên cập nhật hash commit chốt sau khi merge `eval/report`)

## 2. Mục tiêu và cách tiếp cận

Bài toán: xử lý claim hoàn tiền của LogiX-VN (trễ giao, hàng hỏng) sao cho tiền chỉ ra khi có approval hợp lệ, không lộ secret/PII, và crash không tạo refund thứ hai. Nhóm so bốn shape có mức tự chủ tăng dần (A workflow → B single ReAct → C orchestrator → D swarm có sẵn) trên **cùng** 14 claim public, 5 seed `11,22,33,44,55`, cùng MockLLM, bảng giá và evaluator. Nguyên tắc chọn: **shape ít tự chủ nhất mà vẫn đạt pass rate hidden ≥ 0.75**, quyết định dựa trên số đo chứ không dựa trên cảm giác.

Chia việc (5 người, mỗi người một nhánh, PR vào `main`, Tuyên review và merge):

| Người | Vai | Nhánh | Sản phẩm chính |
| --- | --- | --- | --- |
| Dương Ngọc Tuyên | Trưởng nhóm, integration, shape A | `feat/workflow` | `src/lab8/shapes/workflow.py` |
| Nguyễn Tiến Hưng | Shape B single (ReAct) | `feat/single` | `src/lab8/shapes/single.py` |
| Dương Minh Tân | Shape C orchestrator + handoff | `feat/orchestrator` | `src/lab8/shapes/orchestrator.py` |
| Phan Sỹ Hùng | QA ledger / policy / crash | `test/durability` | `src/tests/test_team_durability.py`, `src/reports/crash.json` |
| Dương Thị Huệ | Eval / benchmark / báo cáo | `eval/report` | `src/scripts/trace_scan.py`, `src/reports/benchmark.json`, research card, báo cáo |

Thứ tự: A trước (làm mẫu cho `finish()`, trace và cách gọi `issue_refund`), rồi B và C song song; QA chạy test nhánh khó trên cả 3 shape; EV chạy benchmark khi 3 shape đã merge.

## 3. Giải pháp

Ranh giới chung cho cả ba shape (theo [docs/architecture.md](../../docs/architecture.md)): tiền do `compute_compensation` tính; approval, idempotency và ghi ledger do host (`durability.issue_refund`) làm trong một transaction; shape luôn truyền **quote đầy đủ** để host tự trừ phần đã hoàn (T13, T14); truyền `crash_at` và không bắt `InjectedCrash`; trả kết quả bằng `common.finish()`. Chữ trong ticket là dữ liệu, không phải lệnh.

### 3.1 Shape A — workflow

Các bước cố định trong Python: `get_claim_view` (claim không tồn tại → `failed`; thiếu `order_id` → `needs_info`) → `lookup_order` (không thấy hoặc không thuộc principal → `escalated`) → `compute_compensation` trên dòng order, bỏ qua số ngày ghi trong ticket (quote 0 → `denied`, không gọi host) → `durability.issue_refund(conn, claim_id, quote đầy đủ, crash_at=crash_at)` (host chấp nhận → `resolved`; từ chối → `denied`; lệch số tiền → `failed`). MockLLM chỉ được gọi một lần để soạn câu trả lời (`purpose="draft"`), không ảnh hưởng tiền. Trace: `claim`, `lookup_order`, `quote`, `issue_refund`, `decision`. Test nhóm: `src/tests/test_team_workflow.py` (ticket ghi trễ 9 ngày, order trễ 2 ngày → `denied`).

### 3.2 Shape B — single (ReAct)

Một agent ReAct qua `run_react(max_steps=8)`; `decide` là state machine chỉ chọn tool đọc: `get_claim_view` → `lookup_order` → (`get_clause` nếu ticket viện dẫn clause) → `lookup_refund_history` → `compute_compensation` → `final` (dài nhất 6 bước). Sau vòng lặp, **code** gọi `issue_refund` với quote đầy đủ; model không bao giờ gọi tool ghi. Mỗi bước `decide` là một model call vào `Budget`, nên cost so được với các shape khác. Số ngày trong ticket chỉ ghi trace kèm `trusted: false`; clause `SHIP-LATE-OLD` được tra để ghi `is_current: false` nhưng tiền luôn tính theo policy hiện hành. Test nhóm: `src/tests/test_team_single.py` (≤ 8 bước, model không gọi `issue_refund`, không tin ticket, trace sạch).

### 3.3 Shape C — orchestrator + handoff

Orchestrator đọc claim, dựng handoff bằng `make_handoff` với `facts={}` và 4 tool chỉ đọc (`lookup_order`, `lookup_policy`, `lookup_refund_history`, `compute_compensation`); `principal_id`, ticket và claim row ở lại phía orchestrator. `run_readonly_investigators` đọc order; orchestrator quote và là nơi duy nhất gọi `issue_refund` (quote đầy đủ, `crash_at`). Trace chỉ ghi handoff đã sanitize, order view qua allowlist, quote và quyết định. Test nhóm: `src/tests/test_team_orchestrator.py` (handoff không có `CANARY_SECRET_`, investigator không có tool ghi, 3 điểm crash, approval của claim khác / bị thu hồi).

### 3.4 Trace và quét secret/PII

Trace dùng `lab8.trace.Trace` (contract v1: `run_id`, `events`, ghi ở mọi nhánh return). Nhóm chỉ ghi field đã qua allowlist (`get_claim_view`, `lookup_order`, handoff đã sanitize); **cố ý không ghi** claim row thô (có `parent_secret`, `raw_headers`) và order row thô (có SĐT, địa chỉ, `internal_note`, tên hàng).

Để kiểm điều này bằng máy, nhóm có `src/scripts/trace_scan.py`:

- Dựng danh sách chuỗi cấm từ chính dữ liệu (`parent_secret`, header, `forbid_substrings`, `phone` / `address` / `internal_note` / `item_name` của **mọi** order), cộng regex `CANARY_SECRET_*`, `CANARY_INTERNAL_*`, `Bearer …`, SĐT 10 số, và key JSON của field thô. Không cần nhãn nên dùng được cho `student_drop/`.
- Quét result, trace, mọi file `<run_id>*` (giống grader) **và stdout**. Output chỉ in giá trị đã che.
- `src/tests/test_team_trace_scan.py` chạy trong cổng `python -m pytest -q`: 3 shape × 14 claim phải sạch, scanner phải bắt được leak cài sẵn và không báo nhầm trace sạch, swarm làm đối chứng.

Lệnh (trong `src/`): `python -m scripts.trace_scan --run workflow,single,orchestrator --seeds 11,22,33,44,55` → `trace_scan CLEAN | trials=210 | errors=0 | findings=0`.

### 3.5 QA ledger / policy / crash

`src/tests/test_team_durability.py` (Hùng) phủ các nhánh khó trên cả 3 shape: approval hết hạn, bị thu hồi, pending, của claim khác, approval thấp hơn quote, trần theo đơn (T13, T14), T11 gọi lại và T12 crash rồi resume.

## 4. Kết quả

Bảng so sánh 4 shape trên bộ public (từ `src/reports/benchmark.json`, lệnh `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`). Cost là VND mô phỏng, latency `unavailable`.

| Shape | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success (VND) | Mean / p95 steps | Mean model calls |
| --- | --: | --: | --: | --: | --: | --: | --: |
| workflow | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 28.80 | 4.43 / 5 | 1.00 |
| single | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 41.19 | 12.93 / 15 | 6.71 |
| orchestrator | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 56.63 | 4.71 / 5 | 1.00 |
| swarm | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 / 3 | 3.00 |

Trial fail duy nhất trong 280 trial: `R-swarm-C-002-s55` (`status resolved != denied`): swarm tin "trễ 5 ngày" trong ticket thay vì `delay_days = 2` của order và hoàn 20.000 VND. Ba shape nhóm viết đều đọc `delay_days` từ order nên không mắc lỗi này.

An toàn:

| Chỉ số | Giá trị | Nguồn |
| --- | --- | --- |
| Crash safety | 20/20 (chạy lại trên code đã merge cũng ra 20/20) | `src/reports/crash.json` |
| Approval bypass | 0 — 15/15 trial thiếu approval hợp lệ (C-004, C-005, C-007 × 5 seed) mỗi shape đều pass, không có refund | `src/reports/benchmark.json` + `test_team_durability.py` |
| Secret leak | 0 / 210 trial (3 shape × 14 claim × 5 seed) | `python -m scripts.trace_scan --run workflow,single,orchestrator --seeds 11,22,33,44,55` |
| Hidden selfcheck (`student_drop/`) | Chưa chạy: chưa nhận `student_drop/` | `src/reports/hidden_selfcheck.json` (khi có) |

Cổng test: `python -m pytest -q` → 185 passed; `python -m pytest -q -m student -o addopts=` → 248 passed (62 test × 4 shape).

Quyết định kiến trúc: **workflow** — cùng pass 1.000 với single và orchestrator nhưng ít tự chủ nhất và rẻ nhất (lý do chi tiết: `report/team/decision_adr.md`). Phiếu nghiên cứu và ablation: xem `report/team/research_card.md` (R2 · MAST: lỗi duy nhất của swarm trên public là `R-swarm-C-002-s55`, thuộc nhóm lỗi kiểm chứng).

## 5. Khó khăn và cách xử lý

- Máy của Huệ chỉ có Python 3.14 (repo ghi đã test 3.11–3.13). Tạo venv bằng `py -m venv .venv` với 3.14: `python -m lab8.smoke` pass, `python -m pytest -q` xanh, nên nhóm giữ 3.14 trên máy này.
- Trước khi 3 shape merge, test quét trace chạy trên stub nên không chứng minh được gì; Huệ kiểm thêm bằng shape workflow của nhánh `feat/workflow` (70 trial sạch), rồi chạy lại toàn bộ 210 trial sau khi merge.
- Merge `main` vào `eval/report` bị conflict ở bảng đóng góp `TEAM.md` (hai nhánh cùng sửa); giữ bảng của `main` và chỉ điền dòng của Huệ.
- Test T11/T12 của QA dùng `pytest.skip` khi shape còn stub để cổng host luôn xanh trước khi các PR shape merge.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency là `unavailable`. Bộ public chỉ có 14 claim, nên chênh lệch pass rate nhỏ (một trial = 1/70) dễ là nhiễu; quyết định phải dựa thêm vào pass^5, variance và hidden selfcheck. Scanner dựa trên danh sách chuỗi cấm lấy từ dữ liệu và vài regex: PII bị biến đổi (viết hoa/thường khác, chèn khoảng trắng, mã hoá) sẽ lọt.

Kết luận chọn workflow đổi nếu: hidden cho thấy workflow dưới 0.75 do gặp ticket mơ hồ mà luật cố định không phủ trong khi single vượt ngưỡng; hoặc task có nhiều nguồn đọc độc lập đủ để orchestrator giảm số bước; hoặc dùng LLM thật và việc đọc ticket bằng model đáng giá hơn chi phí. Chưa có hidden selfcheck vì chưa nhận `student_drop/`.

## 8. Tài liệu tham khảo

- Cemri, Pan, Yang et al., *Why Do Multi-Agent LLM Systems Fail?*, NeurIPS 2025 Datasets & Benchmarks, https://arxiv.org/abs/2503.13657
- Tài liệu lab: [docs/architecture.md](../../docs/architecture.md), [docs/contracts.md](../../docs/contracts.md), [docs/metrics.md](../../docs/metrics.md), [docs/business_rules.md](../../docs/business_rules.md)
