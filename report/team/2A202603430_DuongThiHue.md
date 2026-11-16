# Báo cáo cá nhân — 2A202603430_DuongThiHue

## 1. Thông tin thành viên

- Họ tên: Dương Thị Huệ
- MSSV: 2A202603430
- Email: duonghue2004yp@gmail.com
- GitHub: dhuee10
- Nhóm: CapNongCapNia · Lớp L3A
- Vai: EV — Eval / benchmark / báo cáo · nhánh `eval/report`

## 2. Phần việc phụ trách

| Checkpoint | Việc | Trạng thái |
| --- | --- | --- |
| CP1 | Đọc `docs/metrics.md`, `docs/architecture.md`, `research_card.md`, `decision_adr.md`; dựng khung `report/team/group_report.md` | Xong |
| CP2 | Điền research card (cột "Nhóm điền"), chọn R2 · Failure taxonomy (MAST) | Xong |
| CP3 | Viết script quét trace tìm secret/PII cho cả nhóm: `src/scripts/trace_scan.py` + test `src/tests/test_team_trace_scan.py` | Xong |
| CP4 | Bonus: đăng ký topic với giảng viên trước 15:30 | Nhóm không làm bonus |
| CP5 | Benchmark 4 shape × 5 seed, hidden selfcheck, cùng nhóm điền ADR, hoàn thiện group report | Xong trên bộ public; hidden selfcheck chờ `student_drop/` |

## 3. Đóng góp cụ thể

### 3.1 Commit

| Commit | Nội dung |
| --- | --- |
| `39b683f` | `feat(eval)`: script quét trace `src/scripts/trace_scan.py`, test `src/tests/test_team_trace_scan.py`, kết quả ablation `src/reports/ablation_r2_swarm.json` |
| `a9031fa` | `docs(report)`: research card R2, khung group report, nháp ADR mục trace, dòng đóng góp trong `TEAM.md` |
| `f0f4efd` | Merge `main` (3 shape + QA durability) vào `eval/report`, giải conflict bảng đóng góp `TEAM.md` |
| `433cfbd` | `docs(eval)`: `src/reports/benchmark.json` (4 shape × 14 claim × 5 seed), điền ADR, group report, research card |
| `1f4784c` | `docs(report)`: mục cá nhân của Huệ trong `TEAM.md` |

### 3.2 Script quét trace (`src/scripts/trace_scan.py`)

- Dựng danh sách chuỗi cấm **từ chính dữ liệu**, không hard-code: `parent_secret`, giá trị `raw_headers`, `expected.forbid_substrings` của claim; `phone`, `address`, `internal_note`, `item_name` của **mọi** order.
- Thêm regex: `CANARY_SECRET_*`, `CANARY_INTERNAL_*`, `Bearer <token>`, SĐT 10 số; và key JSON của field thô (`parent_secret`, `raw_headers`, `phone`, `address`, `internal_note`, `item_name`) — dấu hiệu ghi nguyên claim row / order row vào trace.
- Hai chế độ:
  - `python -m scripts.trace_scan --traces traces` — quét thư mục trace có sẵn.
  - `python -m scripts.trace_scan --run workflow,single,orchestrator --seeds 11,22,33,44,55` — chạy lại từng shape trên SQLite mới, quét result + trace + mọi file `<run_id>*` (giống grader) **và stdout** (chỗ grader không thấy).
- Dùng được cho `student_drop/` (không cần nhãn): thêm `--cases`, `--world`.
- Output chỉ in giá trị đã che (4 ký tự đầu), để chính scanner không thành nơi rò rỉ. Exit code 1 nếu có phát hiện.

### 3.3 Test `src/tests/test_team_trace_scan.py` (55 test, chạy trong cổng `python -m pytest -q`)

- Scanner tự kiểm: danh sách cấm phủ đủ secret, header và PII của mọi order; bắt được 7 loại leak cài sẵn (token, canary secret, canary internal, bearer, SĐT, địa chỉ, tên hàng); bắt key field thô; không báo nhầm trace sạch; quét cả file phụ `<run_id>*`; output đã che.
- 3 shape nhóm viết × 14 claim public: trace đúng contract v1, result + trace + stdout không có secret/PII.
- Đối chứng: swarm tham chiếu (trace có nội dung thật) vẫn sạch → scanner không báo nhầm.

### 3.4 Benchmark, ADR và báo cáo (CP5)

- Chạy benchmark 4 shape × 5 seed trên code đã merge (`main` `fcfac65`), ghi `src/reports/benchmark.json` bằng công cụ, không sửa tay.
- Chạy lại crash suite để xác nhận `src/reports/crash.json` của Hùng vẫn đúng trên code đã merge (20/20).
- Tính approval bypass từ `benchmark.json`: các claim có `approval_ok = false` (C-004, C-005, C-007).
- Điền `report/team/decision_adr.md` (shape chọn, số liệu, lý do, điều kiện đảo quyết định, trace và bằng chứng), hoàn thiện `report/team/group_report.md` (mục 1–8), cập nhật kết quả ablation trong `report/team/research_card.md`.

### 3.5 Quyết định kỹ thuật

- Danh sách cấm lấy từ dữ liệu nên scanner chạy được trên bộ hidden mà không cần nhãn.
- Quét cả stdout vì contract cấm in PII ra stdout, nhưng grader không đọc stdout.
- So khớp token theo biên từ để tên hàng ngắn ("Sach", "Ghe") không báo nhầm bên trong từ khác.
- Research card chọn R2 vì đo được ngay trên swarm có sẵn: lỗi duy nhất của swarm (`R-swarm-C-002-s55`) là lỗi kiểm chứng của MAST — tin số ngày trong ticket thay vì `delay_days` của order.
- Đề xuất shape **workflow** trong ADR: cùng pass 1.000 với single và orchestrator, nhưng ít tự chủ nhất và cost/success thấp nhất.

## 4. Bằng chứng

Mọi lệnh chạy trong `src/`.

| Lệnh | Kết quả |
| --- | --- |
| `python -m pytest -q` | 185 passed (gồm 55 test của mình) |
| `python -m pytest -q -m student -o addopts=` | 248 passed (62 test × 4 shape) |
| `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json` | xem bảng dưới |
| `python -m scripts.trace_scan --run workflow,single,orchestrator --seeds 11,22,33,44,55` | `trace_scan CLEAN` · trials=210 · errors=0 · findings=0 |
| `python -m lab8.crash_test --count 20` | `crash_safety 20/20` |
| `python -m lab8.benchmark --shapes swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/ablation_r2_swarm.json` | swarm pass 0.986, pass^5 0.929, fail duy nhất `R-swarm-C-002-s55` |
| `python -m lab8.check_submission` | 0 FAIL, 0 WARN |

Bảng từ `src/reports/benchmark.json` (cost là VND mô phỏng, latency `unavailable`):

| Shape | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success | Mean / p95 steps | Mean model calls |
| --- | --: | --: | --: | --: | --: | --: | --: |
| workflow | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 28.80 | 4.43 / 5 | 1.00 |
| single | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 41.19 | 12.93 / 15 | 6.71 |
| orchestrator | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 56.63 | 4.71 / 5 | 1.00 |
| swarm | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 / 3 | 3.00 |

Must-pass: approval bypass 0 (15/15 trial thiếu approval hợp lệ không có refund ở mỗi shape), secret leak 0/210 trial, crash safety 20/20.

## 5. Công cụ AI đã dùng

- **Claude Code**: đọc repo, gợi ý cấu trúc scanner và test, chạy benchmark, viết nháp research card, ADR và group report.
- **Cách tự kiểm tra:**
  - Chạy `python -m pytest -q` và `-m student` sau khi merge: đều xanh.
  - Cố ý cài leak vào trace giả để chắc scanner bắt được; chạy scanner trên swarm (trace có nội dung thật) để chắc không báo nhầm.
  - Trước khi các shape merge, thử scanner trên workflow của nhánh `feat/workflow` (70 trial sạch, không commit).
  - Mọi số trong ADR, group report, research card đọc lại từ `src/reports/benchmark.json`, `src/reports/ablation_r2_swarm.json`, `src/reports/crash.json`, không chép tay từ terminal.
  - Kiểm trace `R-swarm-C-002-s55` bằng `python -m lab8.run`: ra `resolved`, 20.000 VND, có event `model_override`.
  - Thông tin về paper MAST (14 failure mode, 3 nhóm) cần đối chiếu lại với bản arXiv https://arxiv.org/abs/2503.13657.

## 6. Tự đánh giá

- Hoàn thành CP1, CP2, CP3, CP5 của vai EV trên bộ public; `check_submission` ra 0 FAIL.
- Điểm mạnh: scanner dùng chung cho cả nhóm, quét rộng hơn grader (stdout, PII của mọi order) và nằm trong cổng `pytest`; số liệu báo cáo đều lấy từ file do công cụ sinh ra.
- Hạn chế: chưa chạy hidden selfcheck vì chưa nhận `student_drop/`; scanner dựa trên danh sách chuỗi và regex nên PII bị biến đổi (viết hoa/thường khác, chèn khoảng trắng, mã hoá) có thể lọt; kết luận chọn shape mới dựa trên bộ public 14 claim.
