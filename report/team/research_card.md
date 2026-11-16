# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R2 · Failure taxonomy |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Cemri, Pan, Yang et al. (UC Berkeley), *Why Do Multi-Agent LLM Systems Fail?*, NeurIPS 2025 Datasets & Benchmarks, https://arxiv.org/abs/2503.13657 . Loại bằng chứng: nghiên cứu thực nghiệm, gán nhãn thủ công trace của nhiều hệ MAS rồi dựng taxonomy (MAST) |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Lỗi của hệ multi-agent gom được vào 14 failure mode thuộc 3 nhóm: (1) đặc tả / thiết kế hệ thống, (2) lệch giữa các agent, (3) kiểm chứng và kết thúc task. Phần lớn lỗi đến từ thiết kế hệ thống chứ không chỉ do model yếu |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Trace của các framework MAS mã nguồn mở trên task code, toán, trợ lý tổng quát, dùng LLM thật (GPT/Claude…). Không có task hoàn tiền có ledger, không dùng MockLLM; nhãn lỗi do người gán. Trên LogiX chỉ dùng taxonomy để phân loại, không suy ra tỉ lệ lỗi |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Trial fail của swarm (D) trên public chỉ rơi vào nhóm (3) kiểm chứng: agent tin số ngày trong ticket thay vì `delay_days` của order (seed 55, T02) và không agent nào kiểm lại. Đổi D→A (workflow, code luôn đọc `delay_days` từ order) thì lỗi này biến mất: pass 0.986→1.0, pass^5 0.929→1.0, variance 0.0008→0, cost/success giảm vì bớt model call |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Cố định: MockLLM, tools.manifest v1.1, seed 11,22,33,44,55, 14 claim `data/public_claims.jsonl`, `config/pricing.yaml`, evaluator `lab8.metrics.trial_pass`, SQLite mới mỗi trial. Biến duy nhất được thay đổi: shape (swarm → workflow), tức có hay không bước kiểm chứng `delay_days` bằng code |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến: FM nhóm (3) "incorrect verification" — refund 20.000 VND cho claim lẽ ra `denied`. Đo bằng reason `status resolved != denied` trong `trials`, pass rate, pass^5, seed variance, cost/success; kèm approval bypass = 0 và secret leak = 0 (quét bằng `python -m scripts.trace_scan`) |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn, trong `src/`): `python -m lab8.benchmark --shapes swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/ablation_r2_swarm.json`. Nhánh workflow lấy từ `reports/benchmark.json` (CP5, cùng claim, seed, giá).
- Run id / file report: `src/reports/ablation_r2_swarm.json`; trial fail duy nhất `R-swarm-C-002-s55`.
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: **Đúng** cho nửa swarm. Swarm: pass 0.986 (69/70), pass^5 0.929 (13/14), seed min 0.929 (seed 55) – max 1.000, variance 0.000816, cost/success 49.57 VND mô phỏng, mean 3.0 model call. Fail duy nhất: C-002 (T02) seed 55, `status resolved != denied`, trace có event `model_override` ghi `delay_days` lấy từ ticket → nhóm (3) kiểm chứng của MAST, không có lỗi nhóm (1) hay (2) trên bộ public. Nửa workflow: điền số từ `reports/benchmark.json` sau khi chạy benchmark CP5.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`. Lỗi swarm được cài cố ý (`REFERENCE_WEAKNESS`, seed chia hết cho 5), nên chỉ có 1 trial fail trên 70: đủ để minh hoạ taxonomy, không đủ để ước lượng tỉ lệ từng nhóm lỗi. Với LLM thật, lỗi nhóm (1) và (2) (giao việc, lệch mục tiêu) có thể xuất hiện mà MockLLM không tái tạo được.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
