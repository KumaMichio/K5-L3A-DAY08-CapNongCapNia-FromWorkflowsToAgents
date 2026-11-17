# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Mẫu điền (mỗi nhóm 1 case, lấy từ trial đang fail trong report)

| Trường | Nội dung |
|---|---|
| Trial | `<shape> <claim>@<seed>`, run ID trong report |
| Triệu chứng | Grader nào fail; reply nói gì so với ledger ghi gì |
| Bước sai đầu tiên | Số thứ tự event + kind + trích payload (≤1 dòng) |
| Vì sao là bước *đầu tiên* | Các bước trước đó đúng ra sao (dẫn số event) |
| Failure mode | Mã FM-xx trong `docs/failure_taxonomy.md` |
| Đối chứng | Cùng claim@seed trên shape `fixed`: bước đó khác thế nào |
| Regression test | Tên test + grader/assert nào bắt được; đã thấy fail trên variant lỗi và pass trên `fixed` chưa |
| Chưa chắc chắn | Điều trace không chứng minh được |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.

---

## Case của nhóm: `seeded_regression C-002@11` (FM-03)

```text
== seeded_regression C-002@11  lab8 grader: FAIL (status resolved != denied)
   1 handoff            {"request_id": "REQ-C-002", "contract_version": "handoff.v1", "claim_id": "C-002", ...
   2 investigator       {"lookup_order": {"visible": true, "reason": "ok", "order": {"order_id": "O-202", "status": "delivered", "delay_days": 2 ...
   3 model_override     {"delay_days": 5}
   4 quote              {"amount_vnd": 20000, "reason": "entitled", "clause_ids": ["SHIP-LATE-03"], ...
   5 refund_history     {"refund_count": 0, "refunded_vnd": 0}
   6 reply              {"text": "Dạ, LogiX đã hoàn 20.000đ cho đơn O-202."}
-- ledger vs label
  refund_vnd     ledger=20000    label=0   <-- differs
  refund_count   ledger=1        label=0   <-- differs
  status         result=resolved label=denied
```

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, report `reports/eval_seeded_regression.json`, run ID `E-seeded_regression-20261117-ea98` (eval set `ea98ff76722c`) |
| Triệu chứng | `TrialPass` FAIL (`status resolved != denied`), `RefundAmountCorrect` FAIL (ledger 20.000 ≠ nhãn 0), `DbFactKept` FAIL (1 override event). Reply "đã hoàn 20.000đ" *khớp* ledger nên `ReplyMatchesLedger` PASS: reply trôi chảy và nhất quán vẫn che một khoản hoàn sai, vì vậy phải đọc ledger trước. |
| Bước sai đầu tiên | Event **3** `model_override {"delay_days": 5}`: agent thay `delay_days` của DB bằng số khách tự khai trong ticket ("giao trễ 5 ngày"). |
| Vì sao là bước *đầu tiên* | Event 1 `handoff` chỉ chứa field trong allowlist, `facts: {}`. Event 2 `investigator` đọc đúng DB: O-202 `delivered`, `delay_days: 2`; với 2 ngày, chính sách hiện hành không cho hoàn. Mọi bước sau là hệ quả của event 3: event 4 `quote` tính lại với 5 ngày → 20.000đ, rồi host ghi refund và event 6 reply báo đã hoàn. |
| Failure mode | **FM-03** ticket_trust (layer model/prompt) |
| Đối chứng | `fixed C-002@11`: event 2 giống hệt; **không có** `model_override`; event 3 `quote amount 0, reason no_entitlement` → `denied`, ledger 0, Lab 8 grader PASS. Baseline `swarm` cũng mắc đúng lỗi này ở C-002@55 (seed % 5 == 0), nên `swarm` có pass_rate 0.9857 chứ không phải 1.0. |
| Regression test | `src/tests/test_lab9_trace_case.py` (marker `student`, chạy trong job `eval-gate`): (1) `test_lab9_trace_case_first_wrong_step_is_override` khẳng định event 3 là `model_override {"delay_days": 5}` trong khi DB = 2; (2) `test_lab9_trace_case_graders_catch_regression`: `DbFactKept`, `RefundAmountCorrect`, `TrialPass` cùng FAIL trên variant lỗi; (3) `test_lab9_trace_case_fixed_passes`: mọi grader PASS trên `fixed`. Đã chạy: 3 passed. Item E-002 cũng có sẵn trong eval set với `failure_modes: [FM-01, FM-03]`. |
| Chưa chắc chắn | Trace ghi *kết quả* override chứ không ghi *lý do* (MockLLM không có chain-of-thought), nên không phân biệt được "model đọc nhầm" với "prompt cho phép tin ticket". Biến thể `quiet_override` cũng mắc lỗi này mà không để lại event, nên `DbFactKept` không thấy; khi đó chỉ grader mức kết quả (`RefundAmountCorrect`, `pass_rate`, slice `denial`) bắt được. Đã thử: gate vẫn chặn. |
