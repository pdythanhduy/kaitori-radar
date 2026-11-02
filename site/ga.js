// Thống kê lượt xem & hành động (Google Analytics 4).
// BẬT: dán Measurement ID vào GA_ID bên dưới (vd "G-ABC123XYZ"), commit là xong.
(function () {
  var GA_ID = "";

  window.kpTrack = function (name, params) { if (window.gtag) window.gtag("event", name, params || {}); };
  window.kpPage = function () {
    if (window.gtag) window.gtag("event", "page_view", { page_location: location.href, page_title: document.title });
  };
  var CF_TOKEN = "0ed70a31538b456293c208bf5f799cfb";  // Cloudflare Web Analytics (mã công khai, không cookie)
  // chủ web: mở kaitoriprice.com/?me=1 một lần trên mỗi máy → máy đó không bị đếm nữa (?me=0 để bật lại)
  try {
    var me = new URLSearchParams(location.search).get("me");
    if (me === "1") { localStorage.setItem("kp_me", "1"); alert("✓ Máy này sẽ không bị đếm vào lượt truy cập nữa"); }
    if (me === "0") localStorage.removeItem("kp_me");
    if (localStorage.getItem("kp_me") === "1") CF_TOKEN = "";
  } catch (e) {}
  if (CF_TOKEN && location.hostname === "kaitoriprice.com") {
    var cf = document.createElement("script");
    cf.defer = true; cf.src = "https://static.cloudflareinsights.com/beacon.min.js";
    cf.setAttribute("data-cf-beacon", JSON.stringify({ token: CF_TOKEN, spa: true }));
    document.head.appendChild(cf);
  }
  if (!GA_ID || location.hostname !== "kaitoriprice.com") return;  // chỉ đếm trên web thật

  var s = document.createElement("script");
  s.async = true; s.src = "https://www.googletagmanager.com/gtag/js?id=" + GA_ID;
  document.head.appendChild(s);
  window.dataLayer = window.dataLayer || [];
  window.gtag = function () { window.dataLayer.push(arguments); };
  window.gtag("js", new Date());
  // trang chủ là app 1 trang: app.js tự gửi page_view mỗi khi đổi nhóm/tìm kiếm; trang /p/ /c/ gửi tự động
  var app = location.pathname === "/" || location.pathname === "/index.html";
  window.gtag("config", GA_ID, { send_page_view: !app });

  // bấm sang trang tiệm / link affiliate (dùng chung cho app và trang tĩnh /p/)
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href]"); if (!a) return;
    var card = a.closest(".card"), item = card ? (card.querySelector(".c-name") || {}).textContent : (document.querySelector("h1") || {}).textContent;
    if (/sponsored/.test(a.rel)) return window.kpTrack("affiliate_click", { program: a.textContent.replace("→", "").trim(), link_url: a.href });
    var shop = a.matches("a.sh") ? (a.querySelector(".sn b") || {}).textContent : a.closest(".pt") ? a.textContent : a.matches(".sbest") ? (a.querySelector("b") || {}).textContent : "";
    if (shop) window.kpTrack("shop_click", { shop: shop.trim(), item: (item || "").trim().slice(0, 100), link_url: a.href });
  }, true);

  // ghi chú quyền riêng tư ở chân trang
  addEventListener("DOMContentLoaded", function () {
    var f = document.querySelector("footer .wrap") || document.querySelector("footer"); if (!f) return;
    var p = document.createElement("p"); p.className = "small";
    p.textContent = "当サイトはアクセス解析にGoogle アナリティクス（Cookie）を使用しています。個人を特定する情報は収集しません。 / Trang dùng Google Analytics (cookie) để thống kê lượt xem ẩn danh.";
    f.appendChild(p);
  });
})();
