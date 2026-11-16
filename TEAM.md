# Team

## Thông tin nhóm

- Tên nhóm:
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-TenNhom-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt:

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Nguyễn Tiến Hưng | 2A202603365 | | tienhungw | Shape B single (ReAct) |
|   2 |        |      |       |        |         |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Nguyễn Tiến Hưng | Shape B single (ReAct), `src/lab8/shapes/single.py`, nhánh `feat/single` | (điền hash sau khi commit) | `src/tests/test_team_single.py` (thêm mới: số bước ≤ 8, model không gọi `issue_refund`, không tin ticket, trace sạch) |
| | | | |

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
