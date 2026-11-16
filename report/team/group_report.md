# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

> Khung do Huệ (EV) dựng ở CP1. Chỗ ghi `TODO (người phụ trách, CP)` do người đó điền; số liệu mục 4 điền ở CP5 từ `src/reports/benchmark.json` và `src/reports/crash.json`.

## 1. Thông tin nhóm

- Tên nhóm: CapNongCapNia
- Lớp: L3A
- Repo: `K5-L3A-DAY08-CapNongCapNia-FromWorkflowsToAgents`, nhánh nộp `main`
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`): TODO (Tuyên, CP5)

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

TODO (Tuyên, CP2–CP3): các bước đọc claim → order → quote → `issue_refund`; nhánh `needs_info` / `escalated` / `denied`; MockLLM dùng vào đâu (nếu có).

### 3.2 Shape B — single (ReAct)

TODO (Hưng, CP2–CP4): `run_react` tối đa 8 bước, `decide` chỉ chọn tool đọc; code tính quote và gọi `issue_refund` sau vòng lặp; cách đếm model call vào `Budget`; vì sao không tin số ngày trong ticket hay clause `SHIP-LATE-OLD`.

### 3.3 Shape C — orchestrator + handoff

TODO (Tân, CP2–CP4): `make_handoff` với allowlist tool chỉ đọc (có `lookup_refund_history`); investigator đọc order; orchestrator quote và gọi `issue_refund`; handoff được sanitize thế nào.

### 3.4 Trace và quét secret/PII

Trace dùng `lab8.trace.Trace` (contract v1: `run_id`, `events`, ghi ở mọi nhánh return). Nhóm chỉ ghi field đã qua allowlist (`get_claim_view`, `lookup_order`, handoff đã sanitize); **cố ý không ghi** claim row thô (có `parent_secret`, `raw_headers`) và order row thô (có SĐT, địa chỉ, `internal_note`, tên hàng).

Để kiểm điều này bằng máy, nhóm có `src/scripts/trace_scan.py`:

- Dựng danh sách chuỗi cấm từ chính dữ liệu (`parent_secret`, header, `forbid_substrings`, `phone` / `address` / `internal_note` / `item_name` của **mọi** order), cộng regex `CANARY_SECRET_*`, `CANARY_INTERNAL_*`, `Bearer …`, SĐT 10 số, và key JSON của field thô. Không cần nhãn nên dùng được cho `student_drop/`.
- Quét result, trace, mọi file `<run_id>*` (giống grader) **và stdout**. Output chỉ in giá trị đã che.
- `src/tests/test_team_trace_scan.py` chạy trong cổng `python -m pytest -q`: 3 shape × 14 claim phải sạch, scanner phải bắt được leak cài sẵn và không báo nhầm trace sạch, swarm làm đối chứng.

Lệnh (trong `src/`): `python -m scripts.trace_scan --run workflow,single,orchestrator --seeds 11,22,33,44,55`.

## 4. Kết quả

Bảng so sánh 4 shape trên bộ public (từ `src/reports/benchmark.json`, lệnh `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`). Cost là VND mô phỏng, latency `unavailable`.

| Shape | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success (VND) | Mean / p95 steps | Mean model calls |
| --- | --: | --: | --: | --: | --: | --: | --: |
| workflow | TODO | | | | | | |
| single | TODO | | | | | | |
| orchestrator | TODO | | | | | | |
| swarm | TODO | | | | | | |

An toàn:

| Chỉ số | Giá trị | Nguồn |
| --- | --- | --- |
| Crash safety | TODO (Hùng, CP4) | `src/reports/crash.json` |
| Approval bypass | TODO | `src/reports/benchmark.json` + test QA |
| Secret leak | TODO | `python -m scripts.trace_scan --run …` |
| Hidden selfcheck (`student_drop/`) | TODO (CP5): số trial `error`, `leak_suspect` | `src/reports/hidden_selfcheck.json` |

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Phiếu nghiên cứu và ablation: xem `report/team/research_card.md` (R2 · MAST: lỗi duy nhất của swarm trên public là `R-swarm-C-002-s55`, thuộc nhóm lỗi kiểm chứng).

## 5. Khó khăn và cách xử lý

- Máy của Huệ chỉ có Python 3.14 (repo ghi đã test 3.11–3.13). Tạo venv bằng `py -m venv .venv` với 3.14: `python -m lab8.smoke` pass, `python -m pytest -q` xanh, nên nhóm giữ 3.14 trên máy này.
- TODO (từng người): lỗi gặp khi viết shape / crash, kèm lệnh và output.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency là `unavailable`. Bộ public chỉ có 14 claim, nên chênh lệch pass rate nhỏ (một trial = 1/70) dễ là nhiễu; quyết định phải dựa thêm vào pass^5, variance và hidden selfcheck. Scanner dựa trên danh sách chuỗi cấm lấy từ dữ liệu và vài regex: PII bị biến đổi (viết hoa/thường khác, chèn khoảng trắng, mã hoá) sẽ lọt.

TODO (cả nhóm, CP5): điều kiện làm kết luận thay đổi.

## 8. Tài liệu tham khảo

- Cemri, Pan, Yang et al., *Why Do Multi-Agent LLM Systems Fail?*, NeurIPS 2025 Datasets & Benchmarks, https://arxiv.org/abs/2503.13657
- Tài liệu lab: [docs/architecture.md](../../docs/architecture.md), [docs/contracts.md](../../docs/contracts.md), [docs/metrics.md](../../docs/metrics.md), [docs/business_rules.md](../../docs/business_rules.md)
