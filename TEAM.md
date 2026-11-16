# Team

## Thông tin nhóm

- Tên nhóm: CapNongCapNia
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-CapNongCapNia-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/tuyenboy198/K5-L3A-DAY08-CapNongCapNia-FromWorkflowsToAgents, nhánh `main`, commit chốt: _(điền ở CP5)_

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
| 1 | Dương Ngọc Tuyên | 2A202603511 | vlthuthuatblog@gmail.com | tuyenboy198 | Trưởng nhóm · Integration · Shape A `workflow` |
| 2 | Nguyễn Tiến Hưng | 2A202603365 | nguyentienhung04042004@gmail.com | tienhungw | Shape B `single` (ReAct) |
| 3 | Dương Minh Tân | 2A202603464 | duongminhtan325@gmail.com | mihtan05 | Shape C `orchestrator` + handoff |
| 4 | Phan Sỹ Hùng | 2A202603420 | hungphan120304@gmail.com | KumaMichio | Ledger / policy / crash (QA must-pass) |
| 5 | Dương Thị Huệ | 2A202603430 | duonghue2004yp@gmail.com | dhuee10 | Eval / benchmark / báo cáo |

## Phân công chi tiết

Nguyên tắc chung:

- Mỗi người làm trên nhánh riêng (`feat/workflow`, `feat/single`, `feat/orchestrator`, `test/durability`, `eval/report`), mở PR vào `main`. Trưởng nhóm review và merge.
- Trước khi push: `python -m pytest -q` phải xanh (cổng host). Không sửa `metrics.py`, `durability.py`, `policy.py`, `config/`, `data/` hay JSON trong `reports/`.
- Mỗi người phải có **ít nhất một commit kỹ thuật và một test** trong lịch sử (`src/tests/test_team_<tên>.py`). Đây là điều kiện chấm C8.
- Tiền luôn tính bằng `compute_compensation`, truyền **quote đầy đủ** vào `durability.issue_refund`, truyền `crash_at`, không bắt `InjectedCrash`, trả kết quả bằng `common.finish()`.

### 1. Dương Ngọc Tuyên: Trưởng nhóm, Integration, Shape A `workflow`

| Checkpoint | Việc |
| --- | --- |
| CP1 | Cài môi trường, chạy smoke và cổng host; hỗ trợ các bạn cài trên máy mình. Chốt quy ước nhánh và PR |
| CP2 | Viết `src/lab8/shapes/workflow.py` (các bước cố định, theo docstring). Làm xong sớm để làm **mẫu** cho B và C (đọc claim, quote, gọi host, `finish()`, trace) |
| CP3 | Thêm `crash_at` vào workflow; review và merge PR của B, C |
| CP4–CP5 | Chạy `python -m lab8.check_submission`, chốt commit hash và run id vào `decision_adr.md`, push bản cuối |
| Tự kiểm | `python -m pytest -q -m student -o addopts= -k workflow` ra 62 passed |
| Test | `src/tests/test_team_workflow.py`: ví dụ ticket ghi "trễ 9 ngày" nhưng order trễ 2 ngày thì phải ra `denied` |

### 2. Nguyễn Tiến Hưng: Shape B `single` (ReAct)

| Checkpoint | Việc |
| --- | --- |
| CP1 | Đọc `lab8/runtime.py` (`run_react`), `lab8/mock_llm.py`, `config/tools.manifest.v1.1.yaml`, `swarm_reference.py` |
| CP2 | Viết `src/lab8/shapes/single.py`: vòng `run_react` tối đa 8 bước, `decide` chỉ chọn tool đọc; sau vòng lặp code tính quote rồi gọi `issue_refund`. Đếm model call vào Budget |
| CP3 | Thêm `crash_at`; đảm bảo T11, T12 xanh |
| CP4 | Kiểm `decide` không tin số ngày trong ticket hay clause cũ (`SHIP-LATE-OLD`) |
| Tự kiểm | `python -m pytest -q -m student -o addopts= -k single` ra 62 passed |
| Test | `src/tests/test_team_single.py`: ví dụ số bước ≤ 8 và model không bao giờ gọi `issue_refund` |

### 3. Dương Minh Tân: Shape C `orchestrator` + handoff

| Checkpoint | Việc |
| --- | --- |
| CP1 | Đọc `lab8/handoff.py` (allowlist), `run_readonly_investigators` trong `lab8/runtime.py`, `harness_map.yaml` |
| CP2 | Viết `src/lab8/shapes/orchestrator.py`: dựng handoff bằng `make_handoff` với tool chỉ đọc (kể cả `lookup_refund_history`), investigator đọc order, orchestrator quote và gọi `issue_refund` |
| CP3 | Trace chỉ ghi handoff đã sanitize, không ghi parent context; thêm `crash_at` |
| CP4 | Rà trace orchestrator không có `parent_secret`, SĐT, địa chỉ, tên hàng, internal note |
| Tự kiểm | `python -m pytest -q -m student -o addopts= -k orchestrator` ra 62 passed |
| Test | `src/tests/test_team_orchestrator.py`: ví dụ handoff không chứa `CANARY_SECRET_` và investigator không có tool ghi |

### 4. Phan Sỹ Hùng: Ledger / policy / crash (QA must-pass)

| Checkpoint | Việc |
| --- | --- |
| CP1 | Đọc `lab8/durability.py`, `lab8/policy.py`, `docs/business_rules.md`; chạy `python -m lab8.demo.buggy_workflow` để hiểu vì sao checkpoint không thay được ledger |
| CP2 | Trong lúc A/B/C đang viết: viết test cho các nhánh khó, chạy trên cả 3 shape: approval hết hạn, bị thu hồi, của claim khác (`approval_claim_mismatch`), đơn đã hoàn đủ (T13), hoàn phần chênh (T14), approval thấp hơn quote |
| CP3 | Kiểm T11 (gọi lại cùng claim) và T12 (crash rồi resume) trên cả 3 shape; báo lỗi cho người phụ trách shape |
| CP4 | Chạy `python -m lab8.crash_test --count 20 --out reports/crash.json`, phải ra `crash_safety` = `20/20` |
| Test | `src/tests/test_team_durability.py`: test tham số hoá theo 3 shape cho các nhánh approval, trần theo đơn và crash |

### 5. Dương Thị Huệ: Eval / benchmark / báo cáo

| Checkpoint | Việc |
| --- | --- |
| CP1 | Đọc `docs/metrics.md`, `docs/architecture.md`, `report/team/research_card.md`, `decision_adr.md`; dựng khung `group_report.md` |
| CP2–CP3 | Điền research card R1–R4 (cột "Nhóm điền"); viết script quét trace tìm secret/PII để cả nhóm dùng |
| CP4 | Đăng ký bonus với giảng viên **trước 15:30** nếu nhóm làm (xem `docs/bonus_topics.md`) |
| CP5 | Chạy benchmark 4 shape × 5 seed: `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`; tự kiểm bộ hidden trên `student_drop/`; cùng cả nhóm điền ADR (số liệu lấy **từ file report**, không chép tay) và hoàn thiện `group_report.md` |
| Test | `src/tests/test_team_trace_scan.py`: chạy cả 3 shape trên claim public, quét trace không có `CANARY_SECRET_*` hay PII |

### Lịch phối hợp

| Mốc | Cả nhóm |
| --- | --- |
| 13:30 CP1 | Mỗi máy chạy smoke pass; đọc business rules và contracts; thống nhất phân công này |
| 13:45 CP2 | Tuyên push workflow sớm làm mẫu; Hưng và Tân viết B, C song song; Hùng viết test; Huệ làm research card |
| 14:30 CP3 | Merge cả 3 shape; Hùng chạy T11/T12 trên toàn bộ |
| 15:30 CP4 | Crash 20/20; rà trace; chốt bonus (nếu có) |
| 16:15 CP5 | Benchmark, hidden selfcheck, chọn shape, ADR. Mỗi người viết báo cáo cá nhân `report/team/MSSV_HoTen.md` và điền dòng của mình ở bảng dưới |

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Dương Ngọc Tuyên | Trưởng nhóm · Integration · Shape A `workflow`, `src/lab8/shapes/workflow.py`, nhánh `feat/workflow`; merge 4 nhánh vào `main` | `998d2a7` | `src/tests/test_team_workflow.py` (thêm mới, 23 test: ticket nói dối hoặc injection không đổi số tiền, không lấy mã đơn từ ticket, trace không có secret hay ticket, crash rồi resume chỉ một refund) |
| Nguyễn Tiến Hưng | Shape B single (ReAct), `src/lab8/shapes/single.py`, nhánh `feat/single` | `13668f2` | `src/tests/test_team_single.py` (thêm mới: số bước ≤ 8, model không gọi `issue_refund`, không tin ticket, trace sạch) |
| Dương Minh Tân | Shape C `orchestrator` + handoff, `src/lab8/shapes/orchestrator.py`, nhánh `feat/orchestrator` | `bf7edad` | `src/tests/test_team_orchestrator.py` (thêm mới, 6 test: handoff đã sanitize và chỉ có tool đọc, trace không có `CANARY_SECRET_`; crash ở 3 điểm đều resume ra đúng 1 refund; approval của claim khác hoặc đã thu hồi → `denied`) |
| Phan Sỹ Hùng | Ledger / policy / crash | | |
| Dương Thị Huệ | Eval / benchmark / báo cáo | `39b683f` (trace scanner + test + ablation R2) | `src/tests/test_team_trace_scan.py` (thêm mới: scanner bắt leak cài sẵn, 3 shape × 14 claim public trace/stdout sạch) |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## MSSV_HoTen

### Phần việc phụ trách

-

### Đóng góp cụ thể

-

### Bằng chứng

-

## 2A202603365_NguyenTienHung

### Phần việc phụ trách

- Shape B `single` (ReAct): `src/lab8/shapes/single.py`, nhánh `feat/single`. Báo cáo cá nhân: [report/team/2A202603365_NguyenTienHung.md](report/team/2A202603365_NguyenTienHung.md).

### Đóng góp cụ thể

- CP2: vòng ReAct tối đa 8 bước qua `run_react`, `decide` chỉ chọn tool đọc; sau vòng lặp code tính quote bằng `compute_compensation` rồi gọi `durability.issue_refund` với quote đầy đủ. Mỗi bước decide là một model call vào `Budget`.
- CP3: truyền `crash_at` vào `issue_refund`, không nuốt `InjectedCrash`; T11, T12 xanh.
- CP4: `decide` không tin số ngày trong ticket hay clause cũ `SHIP-LATE-OLD`; trace không ghi ticket, secret, header, PII.
- Test thêm: `src/tests/test_team_single.py`.

### Bằng chứng

- `python -m pytest -q -m student -o addopts= -k "single and not workflow and not orchestrator and not swarm"` → 62 passed.
- `python -m pytest -q` xanh, có thêm 26 test của `test_team_single.py`.
- Run id: `R-single-C-006-s11`, `R-single-C-012-s11`.

## 2A202603430_DuongThiHue

### Phần việc phụ trách

- Eval / benchmark / báo cáo, nhánh `eval/report`. Báo cáo cá nhân: [report/team/2A202603430_DuongThiHue.md](report/team/2A202603430_DuongThiHue.md).

### Đóng góp cụ thể

- CP1: dựng khung `report/team/group_report.md`.
- CP2: điền research card R2 (MAST), ablation swarm → workflow.
- CP3: script quét trace `src/scripts/trace_scan.py` (secret, header, SĐT, địa chỉ, ghi chú nội bộ, tên hàng; quét cả stdout) cho cả nhóm dùng.
- CP5: benchmark 4 shape × 5 seed (`src/reports/benchmark.json`), điền ADR, hoàn thiện group report.
- Test thêm: `src/tests/test_team_trace_scan.py` (55 test).

### Bằng chứng

- Commit: `39b683f`, `a9031fa`, `433cfbd`.
- `python -m scripts.trace_scan --run workflow,single,orchestrator --seeds 11,22,33,44,55` → CLEAN, 210 trial, 0 phát hiện.
- `python -m lab8.check_submission` → 0 FAIL, 0 WARN.

## 2A202603464_DuongMinhTan

### Phần việc phụ trách

- Shape C `orchestrator` + handoff: `src/lab8/shapes/orchestrator.py`, nhánh `feat/orchestrator`. Báo cáo cá nhân: [report/team/2A202603464_DuongMinhTan.md](report/team/2A202603464_DuongMinhTan.md).

### Đóng góp cụ thể

- CP2: dựng handoff bằng `make_handoff` với 4 tool chỉ đọc (`lookup_order`, `lookup_policy`, `lookup_refund_history`, `compute_compensation`), `facts={}`; investigator đọc order, orchestrator quote và là nơi duy nhất gọi `durability.issue_refund` với quote đầy đủ.
- CP3: truyền `crash_at`, không bắt `InjectedCrash`; trace chỉ ghi handoff đã sanitize, không ghi parent context.
- CP4: rà trace orchestrator không có secret, SĐT, địa chỉ, tên hàng, internal note.
- Test thêm: `src/tests/test_team_orchestrator.py` (6 test).

### Bằng chứng

- Commit: `bf7edad`; PR: https://github.com/tuyenboy198/K5-L3A-DAY08-CapNongCapNia-FromWorkflowsToAgents/pull/1
- `python -m pytest -q -m student -o addopts= -k orchestrator` → 62 passed.
- Run id: `R-orchestrator-C-001-s11`.
