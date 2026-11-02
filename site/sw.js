// Service worker: cho phép "Thêm vào màn hình chính" + nhận thông báo giá (Web Push).
// Luôn lấy bản mới từ mạng (giá đổi liên tục); chỉ khi mất mạng mới trả bản đã lưu của trang chủ.
const SHELL = "kp-shell-v1";
const PUSH_API = "https://kaitori-push.thanhduy8vn.workers.dev";
self.addEventListener("install", (e) => { self.skipWaiting(); e.waitUntil(caches.open(SHELL).then((c) => c.addAll(["/"])).catch(() => {})); });
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));
self.addEventListener("fetch", (e) => {
  if (e.request.mode !== "navigate") return;  // dữ liệu giá, ảnh, script: để trình duyệt tự xử lý
  e.respondWith(fetch(e.request).catch(() => caches.match("/")));
});
// Push gửi đi không kèm dữ liệu → hỏi Worker nội dung thông báo
self.addEventListener("push", (e) => e.waitUntil((async () => {
  let m = { title: "買取プライス", body: "Giá thu mua đã cập nhật", url: "/vi/?v=mine" };
  try {
    const sub = await self.registration.pushManager.getSubscription();
    if (sub) m = await (await fetch(PUSH_API + "/msg", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ endpoint: sub.endpoint }) })).json();
  } catch (_) {}
  await self.registration.showNotification(m.title, { body: m.body, icon: "/icon-192.png", badge: "/favicon-96.png", tag: "kp-price", renotify: true, data: { url: m.url } });
})()));
self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  const url = new URL((e.notification.data && e.notification.data.url) || "/vi/?v=mine", self.location.origin).href;
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((cs) => {
    for (const c of cs) if (c.url.startsWith(self.location.origin) && "navigate" in c) return c.navigate(url).then((w) => w && w.focus());
    return self.clients.openWindow(url);
  }));
});
