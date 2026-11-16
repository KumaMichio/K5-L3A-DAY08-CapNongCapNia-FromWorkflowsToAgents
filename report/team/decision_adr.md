# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn:
- Commit hash:
- Run id dẫn chứng:
- Pass rate / pass^5 / seed min-max / variance:
- Cost per success (mô phỏng, VND):
- Crash safety:
- Secret leak / approval bypass:

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Viết 1 đoạn. So cùng corpus và cùng seed, không so với một lần chạy lẻ.

## Có đáng đổi lấy multi-agent không

Nếu pass nhỉnh hơn mà cost và variance cao hơn, nhóm giữ hay đổi? Điều kiện nào làm quyết định đảo lại?

## Trace và bằng chứng

Trace của nhóm ghi những event nào? Field nào cố ý **không** ghi, và vì sao? Nếu trace nằm ngoài chỗ scanner quét được, đội security chứng minh thế nào là hệ thống không lộ secret?

Nháp (Huệ, CP3 — các bạn phụ trách shape bổ sung danh sách event của shape mình): trace chỉ ghi field đã qua allowlist (`get_claim_view`, `lookup_order`, handoff đã sanitize), quote, kết quả `issue_refund`. Cố ý **không** ghi claim row thô (`parent_secret`, `raw_headers`), order row thô (`phone`, `address`, `internal_note`, `item_name`) và parent context của orchestrator, vì trace là ranh giới bảo mật: thứ đã ghi ra file thì scanner nào cũng phải giả định là lộ. Để chứng minh không lộ, nhóm không dựa vào việc "tự hứa": `python -m scripts.trace_scan --run workflow,single,orchestrator --seeds 11,22,33,44,55` chạy lại từng shape trên SQLite mới, quét result, trace, mọi file `<run_id>*` **và stdout** (chỗ grader không thấy) với danh sách cấm dựng từ dữ liệu và regex `CANARY_*` / `Bearer` / SĐT; `src/tests/test_team_trace_scan.py` giữ kiểm tra này trong cổng `pytest -q`. Mọi log nằm ngoài các chỗ đó thì bị cấm ngay từ code (shape không `print` dữ liệu claim / order).

## Giới hạn

MockLLM không phải model sản xuất. Latency để `unavailable`. Không sửa JSON cho đủ 0.75.
