# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: fcfac65 (code 3 shape trên `main`, benchmark chạy trên code này; Tuyên cập nhật hash commit chốt sau khi merge `eval/report`)
- Run id dẫn chứng: R-workflow-C-001-s11 … R-workflow-C-014-s55 (70 trial trong src/reports/benchmark.json), đối chứng R-swarm-C-002-s55 (trial fail duy nhất của swarm)
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000–1.000 / 0.000000 (public, 14 claim × 5 seed; src/reports/benchmark.json)
- Cost per success (mô phỏng, VND): 28.80 (single 41.19, orchestrator 56.63, swarm 49.57)
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 0 / 0 (trace_scan 210 trial 3 shape × 14 claim × 5 seed: 0 phát hiện; 15/15 trial thiếu approval hợp lệ C-004, C-005, C-007 không có refund)

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Trên cùng 14 claim public, 5 seed `11,22,33,44,55`, cùng MockLLM, bảng giá và evaluator (`src/reports/benchmark.json`), ba shape nhóm viết đều đạt pass 1.000, pass^5 1.000, variance 0; swarm đạt 0.986 / 0.929, variance 0.000816 vì tin số ngày trong ticket ở seed 55 (T02). Khi độ đúng ngang nhau, nhóm chọn shape **ít tự chủ nhất**: workflow có cost/success thấp nhất (28.80 VND so với 41.19 single, 56.63 orchestrator, 49.57 swarm), ít model call nhất (1.0 mỗi trial, chỉ để soạn câu trả lời, so với 6.71 của single), ít bước (mean 4.43, p95 5 so với 12.93 / 15 của single). Mọi quyết định tiền (quote, gọi `issue_refund`) nằm trong code, nên không có chỗ nào để chữ trong ticket hay seed của model đổi kết quả — đúng loại lỗi duy nhất mà swarm mắc trên public.

## Có đáng đổi lấy multi-agent không

Không. Trên public, single và orchestrator không pass nhiều hơn workflow mà cost/success cao hơn 43% và 97%; swarm vừa pass thấp hơn vừa có variance khác 0. Nhóm giữ workflow. Quyết định sẽ đảo lại nếu: (1) hidden selfcheck / grader hidden cho thấy workflow dưới 0.75 vì gặp loại claim cần đọc ticket mơ hồ (vd hỏi thêm thông tin, nhiều đơn trong một ticket) mà luật cố định không phủ, trong khi single vượt ngưỡng; (2) task cần nhiều nguồn đọc độc lập song song đến mức orchestrator giảm số bước tuần tự; (3) với LLM thật, phần đọc ticket bằng model có giá trị hơn chi phí. Trong mọi trường hợp, ranh giới tiền (code quote, host ghi ledger) giữ nguyên.

## Trace và bằng chứng

Trace của nhóm ghi những event nào? Field nào cố ý **không** ghi, và vì sao? Nếu trace nằm ngoài chỗ scanner quét được, đội security chứng minh thế nào là hệ thống không lộ secret?

Event theo shape (đọc từ code đã merge): workflow `claim`, `lookup_order`, `quote`, `issue_refund`, `decision` (+ `crash` khi có crash_at); single `claim_view`, `order_view`, `react_step`, `quote`, `react_stop`, `host_call`, `result` (số ngày trong ticket nếu có chỉ ghi kèm `trusted: false`); orchestrator `claim`, `handoff` (đã sanitize, `facts: {}`, 4 tool chỉ đọc), `investigator`, `quote`, `decision`. Cố ý **không** ghi claim row thô (`parent_secret`, `raw_headers`), nội dung ticket, order row thô (`phone`, `address`, `internal_note`, `item_name`) và parent context của orchestrator, vì trace là ranh giới bảo mật: thứ đã ghi ra file thì phải giả định là lộ. Để chứng minh không lộ, nhóm không dựa vào việc "tự hứa": `python -m scripts.trace_scan --run workflow,single,orchestrator --seeds 11,22,33,44,55` chạy lại từng shape trên SQLite mới, quét result, trace, mọi file `<run_id>*` **và stdout** (chỗ grader không thấy) với danh sách cấm dựng từ dữ liệu (secret, header, SĐT, địa chỉ, ghi chú nội bộ, tên hàng của mọi order) và regex `CANARY_*` / `Bearer` / SĐT. Kết quả: `trace_scan CLEAN | trials=210 | errors=0 | findings=0`. `src/tests/test_team_trace_scan.py` giữ kiểm tra này trong cổng `pytest -q`.

## Giới hạn

MockLLM không phải model sản xuất. Latency để `unavailable`. Không sửa JSON cho đủ 0.75. Số trên là bộ public (14 claim). Hidden selfcheck trên `student_drop/` (40 claim × 5 seed, không nhãn, `src/reports/hidden_selfcheck.json`): workflow, single, orchestrator mỗi shape 200 trial, 0 trial lỗi (`status` ≠ `error`), trace đúng contract, 0 `leak_suspect`; selfcheck không có nhãn nên không cho pass rate, điểm hidden chính thức do grader của giảng viên chấm. Bộ public nhỏ: một trial = 1/70 pass rate, nên chênh 0.014 giữa swarm và các shape khác chỉ đến từ đúng một trial (T02 seed 55).
