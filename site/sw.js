// Service worker tối giản: cho phép "Thêm vào màn hình chính" trên Android.
// Luôn lấy bản mới từ mạng (giá đổi liên tục); chỉ khi mất mạng mới trả bản đã lưu của trang chủ.
const SHELL = "kp-shell-v1";
self.addEventListener("install", (e) => { self.skipWaiting(); e.waitUntil(caches.open(SHELL).then((c) => c.addAll(["/"])).catch(() => {})); });
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));
self.addEventListener("fetch", (e) => {
  if (e.request.mode !== "navigate") return;  // dữ liệu giá, ảnh, script: để trình duyệt tự xử lý
  e.respondWith(fetch(e.request).catch(() => caches.match("/")));
});
