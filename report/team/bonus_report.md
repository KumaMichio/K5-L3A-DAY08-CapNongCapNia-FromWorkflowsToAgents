# Bonus report: B1

- Topic + nguồn (tên, năm, slide): B1 · Investigator song song và critical path. Google Research 2026, *Towards a Science of Scaling Agent Systems*. Slide 15 (Parallelization), 24 (Graph scheduling), 33 (Latency model), 41.
- CLAIM của nguồn (1 câu): multi-agent chỉ có lợi khi task chia song song được; với task tuần tự, các biến thể multi-agent trong nghiên cứu kém đi 39–70%.
- BOUNDARY (model / dataset / setup): đo trên LLM thật, nhiều benchmark, latency thật của model và tool. LogiX dùng MockLLM (không có latency), 14 claim public × 5 seed, tool là truy vấn SQLite cục bộ.
- HYPOTHESIS trên LogiX: claims flow chủ yếu tuần tự (claim → order → quote → ghi tiền → soạn trả lời). Chạy song song ba investigator đọc chỉ rút ngắn critical path một chút, và mức rút ngắn bị Amdahl chặn trên. Pass rate và ledger không đổi.
- Biến cố định / biến thay đổi: cố định claim, seed `11,22,33,44,55`, bảng giá, evaluator (`lab8.metrics.trial_pass`), cùng tool, cùng số tool call và model call, cùng `bonus/latency.yaml`, cùng jitter theo (seed, claim, node). Biến thay đổi duy nhất là lịch chạy: `orchestrator_seq` (đọc tuần tự, bản sao trung thực của shape C) và `orchestrator_parallel` (`lookup_order`, `lookup_policy`, `lookup_refund_history` chạy trong `ThreadPoolExecutor`, mỗi thread một connection SQLite, join theo thứ tự cố định, orchestrator vẫn là writer duy nhất).
- Lệnh tái lập (copy-paste được, chạy trong `src/`):

  ```bash
  python -m lab8.benchmark --shapes workflow,orchestrator,orchestrator_seq,orchestrator_parallel --extra-shape orchestrator_seq=bonus.orchestrator_parallel:run_claim_sequential --extra-shape orchestrator_parallel=bonus.orchestrator_parallel:run_claim --seeds 11,22,33,44,55 --out reports/bonus_benchmark.json
  python -m bonus.parallel_report --seeds 11,22,33,44,55 --out reports/bonus_parallel.json
  python -m pytest -q tests/test_bonus_parallel.py
  ```

- File report + run id: `src/reports/bonus_benchmark.json`, `src/reports/bonus_parallel.json`. Run id ví dụ: `R-orchestrator_parallel-C-001-s11`, `R-orchestrator_seq-C-001-s11` (trace có sự kiện `schedule` ghi DAG đã chạy).

## Kết quả

Chất lượng và chi phí (`reports/bonus_benchmark.json`, 70 trial mỗi shape = 14 claim × 5 seed):

| Shape | pass rate | pass^5 | seed variance | cost/success (VND mô phỏng) | tool call TB | model call TB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| workflow | 1.000 | 1.000 | 0.0 | 28.80 | 2.79 | 1.0 |
| orchestrator (shape C) | 1.000 | 1.000 | 0.0 | 56.63 | 5.57 | 1.0 |
| orchestrator_seq | 1.000 | 1.000 | 0.0 | 56.63 | 5.57 | 1.0 |
| orchestrator_parallel | 1.000 | 1.000 | 0.0 | 56.63 | 5.57 | 1.0 |

Latency mô phỏng và an toàn (`reports/bonus_parallel.json`):

| Biến thể | critical path mean | critical path p95 | secret leak | refund lệch nhãn |
| --- | ---: | ---: | ---: | ---: |
| orchestrator_seq | 972.2 ms | 1116.4 ms | 0 | 0 |
| orchestrator_parallel | 882.3 ms | 1025.8 ms | 0 | 0 |

- Cùng kết quả (status, ledger, pass) trên **70/70** cặp (claim, seed).
- Speedup trung bình trên 65 cặp có chạy tới bước đọc song song: **1.109×** (tính cả 5 cặp `needs_info` không có gì để song song: 1.102×). Theo status: resolved 1.107×, denied 1.113×, escalated 1.112×, needs_info 1.000×.
- Amdahl: phần thời gian chạy song song được p = **0.159** (tổng ba read / tổng thời gian tuần tự), n = 3 → speedup tối đa **1.118×**. Đo được 1.109× nằm sát dưới trần, vì ba read không dài bằng nhau: nhánh dài nhất (`lookup_order`) vẫn nằm trên critical path.
- Test (`tests/test_bonus_parallel.py`, 7 test, chạy trong cổng host): hai biến thể khớp shape C trên mọi claim public (status, proposal, ledger, số call, cost); kết quả giống hệt khi ép thứ tự thread hoàn thành ngược lại; critical path đúng trên DAG mẫu; bản song song qua cả 3 điểm crash với đúng 1 refund.

## Kết luận

**Ủng hộ** hypothesis, và qua đó ủng hộ CLAIM của nguồn trên LogiX: claims flow gần như tuần tự, nên song song hóa chỉ cho khoảng 11% critical path, không đổi pass rate và không đổi chi phí. Phần song song được chỉ là ba read sau khi đã biết `order_id`. `compute_compensation` phải chờ order, `issue_refund` phải chờ quote, và lần gọi model soạn trả lời (700 ms trong mô hình) chiếm phần lớn thời gian mà không song song được.

Kết luận đảo ngược khi phần song song được chiếm tỉ lệ lớn hơn:

- Bỏ lần gọi model soạn trả lời (trả lời bằng template): theo giá trị gốc trong `latency.yaml`, p ≈ 155 / 300 ≈ 0.52, trần Amdahl ≈ 1.53×. Song song khi đó đáng làm hơn nhiều.
- Tool đọc là dịch vụ từ xa chậm (ví dụ hãng vận chuyển trả về sau vài trăm ms), hoặc mỗi claim cần đọc nhiều nguồn độc lập (nhiều đơn, nhiều hãng).
- Ngược lại, nếu tool đọc nhanh hơn nữa hoặc model chậm hơn, lợi ích tiến về 0, và chi phí phức tạp (thread, connection riêng, join cố định) không còn đáng.

Với LogiX như hiện tại, song song hóa không đổi quyết định chọn kiến trúc: workflow vẫn rẻ bằng một nửa với cùng pass rate.

## Giới hạn

- **MockLLM không có latency.** Toàn bộ thời gian là mô phỏng từ `bonus/latency.yaml` (giả định của nhóm, jitter ±20% cố định theo seed), không phải đo thật. Đổi các con số này thì speedup đổi theo, nên kết quả chỉ đúng tương đối.
- Mô hình bỏ qua chi phí tạo thread và mở connection SQLite riêng, nên speedup thật còn thấp hơn.
- Chỉ 14 claim public. Phần lớn claim đi hết luồng, nên ít đa dạng về hình dạng DAG.
- Metric `steps` của benchmark đếm số sự kiện trong trace. Hai biến thể bonus ghi thêm sự kiện `schedule`, nên `mean_steps` cao hơn shape C 1.0 (5.71 so với 4.71) dù số tool call và model call bằng nhau.
