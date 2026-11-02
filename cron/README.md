# kaitori-cron (Cloudflare Worker)

Cron miễn phí của GitHub hay trễ/bỏ lượt, nên Worker này gọi `workflow_dispatch` của `update.yml` đúng giờ.

- Worker: `kaitori-cron` (tài khoản Cloudflare của chủ web) — https://kaitori-cron.thanhduy8vn.workers.dev/ (hiện "token: set")
- Cron Triggers (UTC): `7,37 1-13 * * *` → mode=hot (10:07–22:37 JST mỗi 30 phút), `47 1 * * *` → mode=full (10:47 JST)
- Secret `GH_TOKEN`: GitHub fine-grained token, chỉ repo kaitori-radar, quyền Actions: Read and write (hết hạn sau 1 năm → nhớ tạo lại)
- Code: `worker.js` (dán vào Cloudflare → Edit code → Deploy)

# kaitori-push (Cloudflare Worker) — cảnh báo giá Web Push

- Worker: `kaitori-push` → https://kaitori-push.thanhduy8vn.workers.dev/ (GET hiện `{"ok":true,"kv":true,"vapid":true}`)
- Code: `push.js`. Deploy bằng API (token `CF_WORKER_TOKEN` trong `.env`, quyền Workers Scripts + Workers KV Edit).
- Bindings: KV `KV` (namespace "kaitori-push"), `VAPID_PUBLIC` (text), secret `VAPID_PRIVATE_JWK` — cặp khoá nằm trong `.env`, khoá công khai cũng có trong `site/app.js`.
  Đổi khoá thì mọi đăng ký cũ hỏng → người dùng phải bật lại.
- Cron (UTC) `22,52 1-13 * * *`: ~15 phút sau mỗi lượt cập nhật giá, đọc `kaitoriprice.com/data/cat/*.json`, gửi push (không payload);
  service worker (`site/sw.js`) gọi `/msg` để lấy nội dung.
