# Benchmark & Observability Report — Day 14

> Copy file này thành `BENCHMARK_REPORT.md` trong repo của bạn và điền đầy đủ.
> Mọi con số phải lấy từ report JSON / CSV / screenshot thật, không ước lượng.

**Họ tên:** ...
**Ngày chạy:** ...
**Môi trường:** (vd MacBook M2, Docker Desktop 4 CPU / 8GB RAM)

---

## 1. SLO của agent

| SLI | SLO | Lý do chọn ngưỡng này |
|---|---|---|
| p95 latency `/ask` | < ___ ms | |
| Error rate `/ask` | < ___ % | |
| Accuracy trên golden dataset | ≥ ___ % | |

---

## 2. Benchmark hiệu năng (develop, `load_test.py`)

### 2.1 Concurrency vs latency (agent v2)

| Concurrency | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Error rate | SLO |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 4,20 | 190,6 | 217,9 | 1.706,4 | 0,67% | PASS |
| 10 | 46,14 | 190,5 | 218,3 | 1.683,2 | 1,33% | PASS |
| 50 | 109,26 | 196,0 | 253,8 | 1.690,8 | 0,33% | PASS |
| 100 | 55,05 | 529,0 | 3.522,9 | 3.801,8 | FAIL p95 |

**Nhận xét:** RPS có tăng tuyến tính theo concurrency không? Vì sao?
RPS tăng từ 4,20 lên 109,26 khi concurrency tăng từ 1 lên 50. Khi tăng tiếp lên 100, RPS giảm còn 55,05 và p95 tăng từ 253,8 ms lên 3.522,9 ms. Trong bốn mức đã thử, concurrency 50 cho throughput cao nhất và vẫn đạt cả hai SLO. Ở mức 100, tỷ lệ lỗi vẫn thấp, nhưng nhiều request hoàn tất chậm hơn.

### 2.2 Tail latency

| `MOCK_SLOW_RATE` | avg (ms) | p95 (ms) | p99 (ms) |
|---|---:|---:|---:|
| `0` | 188,8 | 221,3 | 244,4 |
| `0.03` | 255,1 | 238,0 | 1.696,7 |
| `0.1` | 371,4 | 1.692,7 | 1.710,5 |

**Nhận xét:** Chỉ số nào nhạy nhất với request chậm? Vì sao SLO không nên đặt theo average?
Khi tỷ lệ request chậm tăng từ 0% lên 3%, p99 tăng từ 244,4 ms lên 1.696,7 ms, trong khi p95 chỉ tăng từ 221,3 ms lên 238,0 ms. Ở mức 10%, p95 tăng lên 1.692,7 ms và vượt SLO 500 ms, dù trung bình vẫn chỉ 371,4 ms. Trong thử nghiệm này, p99 phát hiện nhóm request chậm sớm nhất. Số trung bình có thể che khuất độ trễ mà nhóm người dùng chậm nhất gặp phải.

---

## 3. Benchmark chất lượng (develop, `eval/run_eval.py`)

| Chỉ số | Agent v1 | Agent v2 | Agent v2 sau khi sửa KB |
|---|---:|---:|---:|
| Accuracy | 4,3% (1/23) | 91,3% (21/23) | **100% (23/23)** |
| Avg tokens / câu | 56,6 | 108,7 | 113,8 |
| Tổng cost (USD) | 0,000397 | 0,000756 | 0,000792 |
| Cost / câu đúng (USD) | 0,00039735 | 0,00003599 | 0,00003445 |
| Quality gate | FAIL | PASS | **PASS** |

**Những câu v2 trả lời sai ban đầu và cách bạn sửa:**

| ID | Keyword bị thiếu | Bạn đã sửa gì |
|---|---|---|
| `security-02` | `token`, `hết hạn`, `chữ ký` | Thêm mục giải thích JWT có chữ ký và thời hạn, đồng thời mô tả cách API key được đối chiếu với giá trị đã cấu hình. |
| `scaling-03` | `cpu`, `memory`, `custom metrics` | Thêm mục giải thích Kubernetes HPA điều chỉnh số replica dựa trên các metric được cấu hình. |

**Nhận xét về trade-off chất lượng / chi phí / latency giữa v1 và v2:**

Sau khi bổ sung hai mục vào KNOWLEDGE_BASE, accuracy tăng từ 91,3% lên 100% và không có regression. Tổng chi phí tăng từ 0,000756 lên 0,000792 USD, còn chi phí mỗi câu đúng giảm từ 0,00003599 xuống 0,00003445 USD. Trong lần eval cuối, p95 là 1.553,3 ms và hai request mất khoảng 1.684 ms. Với chỉ 23 câu và mock có độ trễ ngẫu nhiên, kết quả load test ở mục 2 phù hợp hơn để đánh giá độ trễ.

---

## 4. Observability stack (production)

### 4.1 Screenshot

- [ ] Dashboard Grafana khi đang có tải (thấy rõ Golden Signals)
- [ ] Một trace chậm trong Jaeger (thấy span nào chiếm thời gian)
- [ ] Một trace lỗi trong Jaeger (có event `exception`)
- [ ] Trang Alerts của Prometheus với ít nhất 1 alert đang **firing**

### 4.2 Thí nghiệm "phá hệ thống"

| # | Thay đổi | Alert nào firing | Thời gian từ lúc đổi → firing | Panel nào phản ánh rõ nhất |
|---|---|---|---|---|
| A | `MOCK_ERROR_RATE=0.2` | | | |
| B | `MOCK_SLOW_RATE=0.3` | | | |
| C | `LLM_MODEL=mock-llm-large` | | | |
| D | `docker pause` 1 instance | | | |
| E | `AGENT_VERSION=v1` | | | |

**Thí nghiệm E không làm alert nào firing. Bạn sẽ phát hiện loại sự cố này trong production bằng cách nào?**

...

### 4.3 Debug bằng trace

#### Trace chậm

- Trace ID — `ebec6630065ed6de064b6a3f9feb306c`
- Tổng thời gian trace - 151 ms
- Span chiếm nhiều thời gian nhất - `chat mock-llm-small`
- Thời gian span - 149 ms
- Log đối chiếu — dòng `llm_call` có cùng trace ID và `llm_ms: 1690.9`

```json
{"ts": "2026-11-26T15:14:41.963824+00:00", "level": "INFO", "service": "observable-agent", "instance": "d83fc83c8c7c", "event": "llm_call", "trace_id": "ebec6630065ed6de064b6a3f9feb306c", "span_id": "67b0e80f5a5393f2", "request_id": "767d5480c903", "model": "mock-llm-small", "agent_version": "v2", "input_tokens": 83, "output_tokens": 44, "cost_usd": 3.9e-05, "llm_ms": 1690.9}
```

#### Trace lỗi

- `trace_id`: `2cb0b6b99fbe94c5442602c42a74f237`
- Span phát sinh lỗi: `chat mock-llm-small`
- Event `exception`: mock LLM upstream trả lỗi `503 Service Unavailable`.
- Ảnh: [Trace lỗi trong Jaeger](screenshots/jaeger-error-trace.png)

```json
{"ts": "2026-11-26T15:14:37.415546+00:00", "level": "INFO", "service": "observable-agent", "instance": "d83fc83c8c7c", "event": "llm_error", "trace_id": "2cb0b6b99fbe94c5442602c42a74f237", "span_id": "1288ca881cb6161d", "request_id": "3ca06e718411", "error": "Upstream LLM error: 503 Service Unavailable (mock)"}
```

## 5. Benchmark scaling (production, Locust headless, 100 users, 2 phút)

| Số instance | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Failures |
|---|---|---|---|---|---|
| 1 | | | | | |
| 3 | | | | | |

**Giải thích kết quả:** Scale có cải thiện p95 không? Nút thắt nằm ở đâu?

...

---

## 6. Kết luận

- 3 điều bạn học được về benchmark & observability:
  1. ...
  2. ...
  3. ...
- Nếu đưa agent này lên production thật, bạn sẽ thêm metric / alert nào nữa?

...
