# kaitori-cron (Cloudflare Worker)

Cron miễn phí của GitHub hay trễ/bỏ lượt, nên Worker này gọi `workflow_dispatch` của `update.yml` đúng giờ.

- Worker: `kaitori-cron` (tài khoản Cloudflare của chủ web) — https://kaitori-cron.thanhduy8vn.workers.dev/ (hiện "token: set")
- Cron Triggers (UTC): `7,37 1-13 * * *` → mode=hot (10:07–22:37 JST mỗi 30 phút), `47 1 * * *` → mode=full (10:47 JST)
- Secret `GH_TOKEN`: GitHub fine-grained token, chỉ repo kaitori-radar, quyền Actions: Read and write (hết hạn sau 1 năm → nhớ tạo lại)
- Code: `worker.js` (dán vào Cloudflare → Edit code → Deploy)
