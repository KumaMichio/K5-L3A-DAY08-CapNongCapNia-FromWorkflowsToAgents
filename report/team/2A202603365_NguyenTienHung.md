# Báo cáo cá nhân — 2A202603365_NguyenTienHung

## 1. Thông tin thành viên

- Họ tên: Nguyễn Tiến Hưng
- MSSV: 2A202603365
- Email:
- GitHub: tienhungw

## 2. Phần việc phụ trách

Shape B `single` (một agent ReAct), file `src/lab8/shapes/single.py`, nhánh `feat/single`.

Mục tiêu của shape: cùng claims flow với swarm nhưng ở mức tự chủ thấp hơn: **một** model, vòng ReAct tối đa 8 bước, model chỉ được chọn tool đọc, code của shape là bên duy nhất gọi `durability.issue_refund` sau khi vòng lặp đã dừng.

## 3. Đóng góp cụ thể

### Code: `src/lab8/shapes/single.py`

| Checkpoint | Việc đã làm |
| --- | --- |
| CP1 | Đọc `lab8/runtime.py` (`run_react`, `dispatch`), `lab8/mock_llm.py`, `config/tools.manifest.v1.1.yaml`, `swarm_reference.py`, `durability.py`, `docs/contracts.md`. |
| CP2 | Viết `run_claim` dùng `run_react(max_steps=8)` với `decide` là một state machine (`_Agent`): `get_claim_view` → `lookup_order` → (`get_clause` nếu ticket viện dẫn clause) → `lookup_refund_history` → `compute_compensation` → `final`. Mọi nhánh return đi qua `common.finish()` nên trace và `RunResult` đúng contract. Sau vòng lặp: quote 0 → `denied` không chạm host; quote > 0 → code gọi `issue_refund` với **quote đầy đủ** (host tự trừ phần đã hoàn, T13/T14). |
| CP2 | Đếm model call vào `Budget`: mỗi lần `decide` chạy là một `complete(purpose="decide")`, thêm một `parse` khi đọc ticket và một `draft` khi soạn trả lời. Nhờ vậy cost của single so sánh được với swarm trên cùng bảng giá. |
| CP3 | Truyền `crash_at` thẳng vào `issue_refund`; `InjectedCrash` chỉ được bắt để ghi trace rồi `raise` lại, không nuốt. T11 (gọi lại) và T12 (crash rồi resume) xanh. |
| CP4 | `decide` không tin ticket: số ngày trễ trong ticket chỉ được ghi vào trace với `trusted: false`; `delay_days` lấy từ dòng order. Clause khách nhắc (`SHIP-LATE-OLD`) được tra bằng `get_clause` để ghi `is_current`, nhưng tiền luôn tính bằng `compute_compensation` trên policy hiện hành. Trace không ghi ticket, `parent_secret`, header, SĐT, địa chỉ, tên hàng (order đi qua allowlist `lookup_order` rồi lọc thêm một lần). |

### Test đã thêm: `src/tests/test_team_single.py` (26 test, chạy trong cổng host mặc định)

- `test_react_loop_stays_within_eight_steps`: monkeypatch `run_react` để đếm số lần `decide`; khẳng định ≤ 8 trên 8 claim × 2 seed và số `react_step` trong trace khớp số lần decide thật.
- `test_model_never_calls_issue_refund`: monkeypatch `lab8.runtime.dispatch` và `single.issue_refund`; mọi tool model chọn đều thuộc `READONLY_TOOLS`, `issue_refund` chỉ được gọi tối đa một lần, **sau khi vòng lặp đã dừng**, đúng claim, và với quote đầy đủ (35.000 cho T13, 150.000 cho T14).
- `test_decide_ignores_ticket_delay_and_old_clause`: T02 (ticket 5 ngày, order 2 ngày) và T06 (viện `SHIP-LATE-OLD`) đều `denied`, trace ghi `trusted: false`, `is_current: false`.
- `test_trace_contract_and_no_leak_on_every_branch`: trace đúng contract v1 và không chứa canary, ticket, `parent_secret`, `raw_headers` trên mọi nhánh return.

### Quyết định kỹ thuật

- `run_react` chỉ đưa lại `last_tool`/`last_result` giữa các bước, nên agent giữ trạng thái riêng trong `_Agent` thay vì nhét cả claim row vào observation (tránh secret đi vào prompt và trace).
- `lookup_refund_history` được gọi để **ghi trace** cho người đọc, không dùng để tự trừ tiền. Nếu shape tự trừ rồi mới truyền vào, host trừ thêm lần nữa và T14 sai.
- Số bước tối đa là 6 ở kịch bản dài nhất (có `get_clause`), còn dư 2 bước so với trần 8; nếu vượt trần thì `run_react` trả `step_cap` và shape kết thúc `failed`, không ghi ledger.

## 4. Bằng chứng

- Lệnh tự kiểm shape: `python -m pytest -q -m student -o addopts= -k "single and not workflow and not orchestrator and not swarm"` → **62 passed**.
- Cổng host: `python -m pytest -q` → **80 passed** (54 có sẵn + 26 test mới), không có `failed`.
- Benchmark public (single, swarm; seed 11,22,33,44,55):

  | Shape | pass rate | pass^5 | seed variance | cost/success (VND mô phỏng) | mean steps | mean model calls |
  | --- | --- | --- | --- | --- | --- | --- |
  | single | 1.000 | 1.000 | 0.0 | 41.19 | 12.93 | 6.71 |
  | swarm | 0.986 | 0.929 | 0.00082 | 49.57 | 2.80 | 3.00 |

  Single tốn nhiều model call hơn (một call mỗi bước ReAct) nhưng rẻ hơn swarm trên mỗi lần thành công và không dao động theo seed, vì không có chỗ nào tin ticket.
- Run id dẫn chứng: `R-single-C-006-s11` (viện clause cũ → denied, trace có `clause_check.is_current=false`), `R-single-C-012-s11` (crash `after_effect_before_checkpoint` rồi resume → `resolved`, một dòng ledger 35.000, một audit `refund_committed`).
- Commit: điền hash sau khi commit nhánh `feat/single`.

## 5. Công cụ AI đã dùng

- Claude Code (Claude Fable 5.1) để đọc starter, viết `single.py`, viết test và soạn báo cáo này.
- Cách tự kiểm: chạy 62 test student của shape, cổng host, 26 test riêng; đọc trace `traces/R-single-C-006-s11.json` bằng mắt để chắc không có ticket, secret, SĐT; chạy `lab8.run` với `--crash-at after_effect_before_checkpoint` rồi chạy lại cùng DB để xem ledger còn một dòng; chạy `lab8.benchmark` cho single và swarm để so cost và variance.

## 6. Tự đánh giá

Hoàn thành đủ 5 việc trên thẻ phân công (CP1–CP4) và test phải thêm. Shape qua 62/62 test public, T11 và T12 xanh, trace sạch. Điểm còn mở cho nhóm: chạy benchmark 4 shape vào `src/reports/benchmark.json` và tự kiểm trên `student_drop/` ở CP5 khi hai shape còn lại xong.
