# Deployment — Day 14

## URL và nền tảng

- **URL public** — https://TEN-SERVICE.onrender.com
- **Nền tảng** — Render
- **Thư mục deploy** — `06-lab-complete/`
- **Blueprint** — `06-lab-complete/render.yaml`
- **Dịch vụ** — `day14-agent` chạy FastAPI bằng Docker.
  `day14-redis` cung cấp Redis cho rate limit và cost guard.

## Lệnh kiểm tra

Chạy trên Bash. Nhập API key khi terminal hỏi để kiểm tra request
có xác thực.

```bash
BASE="https://TEN-SERVICE.onrender.com"
read -r -s -p "API key trên Render: " AGENT_API_KEY
printf '\n'

curl -sS -o /dev/null -w 'GET /health -> %{http_code}\n' "$BASE/health"
curl -sS -o /dev/null -w 'GET /ready  -> %{http_code}\n' "$BASE/ready"

curl -sS -o /dev/null -w 'POST /ask thiếu key -> %{http_code}\n' \
  "$BASE/ask" -H 'Content-Type: application/json' \
  -d '{"question":"Hello"}'

curl -sS -o /dev/null -w 'POST /ask đúng key  -> %{http_code}\n' \
  "$BASE/ask" -H 'Content-Type: application/json' \
  -H "X-API-Key: $AGENT_API_KEY" -d '{"question":"Hello"}'

unset AGENT_API_KEY
```

## Kết quả kiểm tra

| Phép thử | Mã HTTP | Ý nghĩa |
|---|---|---|
| `GET /health` | `200 OK` | Agent đang hoạt động. |
| `GET /ready` | `200 OK` | Agent kết nối được Redis và sẵn sàng nhận request. |
| `POST /ask` thiếu key | `401 Unauthorized` | Agent yêu cầu xác thực. |
| `POST /ask` đúng key | `200 OK` | Agent chấp nhận API key và xử lý câu hỏi. |

## Biến môi trường

| Biến | Cách cấu hình |
|---|---|
| `PORT` | Render cấp cho web service. |
| `ENVIRONMENT` | Đặt thành `production` trong Blueprint. |
| `AGENT_API_KEY` | Render sinh bằng `generateValue: true`. |
| `REDIS_URL` | Blueprint lấy URL kết nối nội bộ từ `day14-redis`. |

## Ảnh bằng chứng

- [Blueprint và các service](screenshots/dashboard.png)
- [Agent đang Live trên Render](screenshots/running.png)
- [Kết quả bốn phép thử HTTP](screenshots/test.png)