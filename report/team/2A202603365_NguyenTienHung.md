# Báo cáo cá nhân — 2A202603365_NguyenTienHung

## 1. Thông tin thành viên

- Họ tên: Nguyễn Tiến Hưng
- MSSV: 2A202603365
- Email: nguyentienhung04042004@gmail.com
- GitHub: tienhungw
- Nhóm: CapNongCapNia, lớp L3A, repo `K5-L3A-DAY08-CapNongCapNia-FromWorkflowsToAgents`
- Nhánh cá nhân: `feat/single`

## 2. Phần việc phụ trách

Shape B `single` (một agent ReAct), file `src/lab8/shapes/single.py`, và test riêng `src/tests/test_team_single.py`.

Mục tiêu của shape: cùng claims flow và cùng chữ ký `run_claim` với ba shape còn lại, nhưng ở mức tự chủ trung gian giữa workflow (A) và orchestrator (C): **một** model, vòng ReAct tối đa 8 bước, model chỉ được chọn tool đọc, và code của shape là bên duy nhất gọi `durability.issue_refund` sau khi vòng lặp đã dừng. Shape này là cột "single" trong benchmark để nhóm so cost và variance với workflow và swarm khi chọn kiến trúc.

## 3. Đóng góp cụ thể

### 3.1 Commit chính

| Commit | Nhánh | Nội dung |
| --- | --- | --- |
| `13668f2` | `feat/single` | `feat(single)`: shape B ReAct agent, test ranh giới code/model, báo cáo cá nhân, dòng đóng góp trong `TEAM.md` |
| `fcfac65` | `main` | Trưởng nhóm merge `feat/single` vào `main` |

### 3.2 Code: `src/lab8/shapes/single.py`

| Checkpoint | Việc đã làm |
| --- | --- |
| CP1 | Đọc `lab8/runtime.py` (`run_react`, `dispatch`), `lab8/mock_llm.py`, `config/tools.manifest.v1.1.yaml`, `swarm_reference.py`, `durability.py`, `docs/business_rules.md`, `docs/contracts.md`. Chạy smoke và cổng host trên máy mình. |
| CP2 | Viết `run_claim` dùng `run_react(max_steps=8)` với `decide` là một state machine (`_Agent`): `get_claim_view` → `lookup_order` → (`get_clause` nếu ticket viện dẫn clause) → `lookup_refund_history` → `compute_compensation` → `final`. Mọi nhánh return đi qua `common.finish()` nên trace và `RunResult` đúng contract. Sau vòng lặp: quote 0 → `denied` không chạm host; quote > 0 → code gọi `issue_refund` với **quote đầy đủ** (host tự trừ phần đã hoàn, T13/T14). |
| CP2 | Đếm model call vào `Budget`: mỗi lần `decide` chạy là một `complete(purpose="decide")`, thêm một `parse` khi đọc ticket và một `draft` khi soạn trả lời. Nhờ vậy cost của single so sánh được với swarm trên cùng bảng giá. |
| CP3 | Truyền `crash_at` thẳng vào `issue_refund`; `InjectedCrash` chỉ được bắt để ghi trace rồi `raise` lại, không nuốt. T11 (gọi lại) và T12 (crash rồi resume) xanh. |
| CP4 | `decide` không tin ticket: số ngày trễ trong ticket chỉ được ghi vào trace với `trusted: false`; `delay_days` lấy từ dòng order. Clause khách nhắc (`SHIP-LATE-OLD`) được tra bằng `get_clause` để ghi `is_current`, nhưng tiền luôn tính bằng `compute_compensation` trên policy hiện hành. Trace không ghi ticket, `parent_secret`, header, SĐT, địa chỉ, tên hàng (order đi qua allowlist `lookup_order` rồi lọc thêm một lần). |

### 3.3 Test đã thêm: `src/tests/test_team_single.py` (26 test, chạy trong cổng host mặc định)

- `test_react_loop_stays_within_eight_steps`: monkeypatch `run_react` để đếm số lần `decide`; khẳng định ≤ 8 trên 8 claim × 2 seed và số `react_step` trong trace khớp số lần decide thật.
- `test_model_never_calls_issue_refund`: monkeypatch `lab8.runtime.dispatch` và `single.issue_refund`; mọi tool model chọn đều thuộc `READONLY_TOOLS`, `issue_refund` chỉ được gọi tối đa một lần, **sau khi vòng lặp đã dừng**, đúng claim, và với quote đầy đủ (35.000 cho T13, 150.000 cho T14).
- `test_decide_ignores_ticket_delay_and_old_clause`: T02 (ticket 5 ngày, order 2 ngày) và T06 (viện `SHIP-LATE-OLD`) đều `denied`, trace ghi `trusted: false`, `is_current: false`.
- `test_trace_contract_and_no_leak_on_every_branch`: trace đúng contract v1 và không chứa canary, ticket, `parent_secret`, `raw_headers` trên mọi nhánh return.

### 3.4 Quyết định kỹ thuật

- `run_react` chỉ đưa lại `last_tool`/`last_result` giữa các bước, nên agent giữ trạng thái riêng trong `_Agent` thay vì nhét cả claim row vào observation. Nhờ vậy secret không đi vào prompt hay trace.
- `lookup_refund_history` được gọi để **ghi trace** cho người đọc, không dùng để tự trừ tiền. Nếu shape tự trừ rồi mới truyền vào, host trừ thêm lần nữa và T14 sai.
- Kịch bản dài nhất dùng 6 bước (có `get_clause`), còn dư 2 bước so với trần 8. Nếu vượt trần thì `run_react` trả `step_cap` và shape kết thúc `failed`, không ghi ledger.
- Prompt gửi MockLLM chỉ gồm claim id, số bước, tên tool và vài field an toàn (`found`, `visible`, `amount_vnd`); ticket chỉ đi vào call `parse`, không đi vào trace.

## 4. Bằng chứng

### 4.1 Test

| Lệnh (chạy trong `src/`) | Kết quả |
| --- | --- |
| `python -m pytest -q -m student -o addopts= -k "single and not workflow and not orchestrator and not swarm"` | 62 passed |
| `python -m pytest -q tests/test_team_single.py` | 26 passed |
| `python -m pytest -q` trên `main` sau khi merge 4 nhánh | 130 passed, không có `failed` |
| `python -m pytest -q -m student -o addopts=` trên `main` | 248 passed (62 × 4 shape) |

Lưu ý: lệnh `-k single` trên thẻ phân công khớp cả tên test `test_public_single_run_cases` của các shape khác, nên khi shape khác còn stub sẽ thấy thêm fail của chúng. Lọc như dòng đầu bảng thì ra đúng 62 test của shape single.

### 4.2 Benchmark public (4 shape × 14 claim × 5 seed, `src/reports/benchmark.json`)

| Shape | pass rate | pass^5 | seed variance | cost/success (VND mô phỏng) | mean steps | mean model calls |
| --- | --- | --- | --- | --- | --- | --- |
| workflow | 1.000 | 1.000 | 0 | 28.80 | 4.43 | 1.00 |
| **single** | **1.000** | **1.000** | **0** | **41.19** | **12.93** | **6.71** |
| orchestrator | 1.000 | 1.000 | 0 | 56.63 | 4.71 | 1.00 |
| swarm | 0.986 | 0.929 | 0.00082 | 49.57 | 2.80 | 3.00 |

Single đúng bằng workflow và orchestrator trên public, rẻ hơn swarm trên mỗi lần thành công và không dao động theo seed, vì không có chỗ nào tin ticket. Single tốn nhiều model call và bước nhất trong ba shape nhóm viết (một call mỗi bước ReAct), nên cost/success cao hơn workflow 43%. Đó là lý do nhóm chọn **workflow** trong `decision_adr.md`: cùng độ đúng thì lấy shape ít tự chủ nhất và rẻ nhất. Tôi đồng ý với quyết định này; single chỉ đáng chọn khi bộ hidden có ticket mơ hồ mà luật cố định không phủ.

### 4.3 Run id dẫn chứng

- `R-single-C-006-s11`: ticket viện `SHIP-LATE-OLD` → `denied`, trace có `clause_check.is_current = false`, `trusted = false`.
- `R-single-C-002-s55`: ticket nói trễ 5 ngày, order ghi 2 → `denied`, `proposal_amount = 0` (trial mà swarm fail ở cùng seed).
- `R-single-C-012-s11`: crash `after_effect_before_checkpoint` rồi chạy lại cùng DB → `resolved`, một dòng ledger 35.000, một audit `refund_committed`.
- `R-single-C-014-s11`: đơn đã hoàn 30.000, hỏng hàng đã verify → `proposal_amount = 150000`, ledger 120.000 (host trừ, shape truyền quote đầy đủ).

### 4.4 Crash và an toàn

- `python -m lab8.crash_test --count 20 --out reports/crash.json` → `crash_safety 20/20` (`src/reports/crash.json`).
- Trace scan của nhóm (`python -m scripts.trace_scan --run workflow,single,orchestrator --seeds 11,22,33,44,55`) → 210 trial, 0 phát hiện; 70 trial single nằm trong số đó.

## 5. Công cụ AI đã dùng

- Claude Code (Claude Fable 5.1) để đọc starter, viết `single.py`, viết test, chạy các lệnh kiểm tra và soạn báo cáo này.
- Cách tự kiểm kết quả AI sinh ra:
  - Chạy 62 test student của shape, cổng host, và 26 test riêng; đọc lại từng test để chắc nó kiểm đúng điều cần kiểm (monkeypatch có bắt đúng chỗ `issue_refund` được gọi không).
  - Mở trace `traces/R-single-C-006-s11.json` đọc bằng mắt để chắc không có ticket, secret, SĐT, địa chỉ.
  - Chạy `python -m lab8.run --shape single --claim-id C-012 --seed 11 --db data/tmp.sqlite --crash-at after_effect_before_checkpoint` rồi chạy lại không có `--crash-at` trên cùng DB để xem ledger còn một dòng.
  - Chạy `lab8.benchmark` cho single và swarm, đối chiếu với `src/reports/benchmark.json` do Huệ chạy: số khớp.
  - Đối chiếu code với `docs/business_rules.md` và `docs/contracts.md` từng dòng trong bảng status.

## 6. Tự đánh giá

Hoàn thành đủ 5 việc trên thẻ phân công (CP1–CP4) và test phải thêm. Shape qua 62/62 test public, T11 và T12 xanh, trace sạch, cost và variance đo được và đã vào benchmark của nhóm. Điểm tôi thấy còn có thể làm tốt hơn: single tốn 6.7 model call mỗi claim vì mỗi bước decide đều gọi MockLLM; nếu gộp `parse` vào bước decide đầu tiên thì cost giảm mà ranh giới không đổi. Phần còn lại của nhóm: hidden selfcheck trên `student_drop/` khi nhận được, và cập nhật commit hash chốt sau khi merge `eval/report`.
