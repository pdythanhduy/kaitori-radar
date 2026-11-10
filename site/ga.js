// Thống kê lượt xem & hành động.
// - Cloudflare Web Analytics: lượt tải trang (không cookie).
// - Sự kiện ẩn danh (tìm gì, bấm sang tiệm nào…) gửi về worker kaitori-push → Cloudflare Analytics Engine.
//   Không cookie, không lưu IP, không định danh người dùng. Báo cáo: marketing/events_report.py
// - Google Analytics 4 (tuỳ chọn): dán Measurement ID vào GA_ID nếu muốn bật thêm.
(function () {
  var GA_ID = "";
  var EV_URL = "https://kaitori-push.thanhduy8vn.workers.dev/ev";
  var CF_TOKEN = "0ed70a31538b456293c208bf5f799cfb";  // Cloudflare Web Analytics (mã công khai, không cookie)
  var live = location.hostname === "kaitoriprice.com";
  // chủ web: mở kaitoriprice.com/?me=1 một lần trên mỗi máy → máy đó không bị đếm nữa (?me=0 để bật lại)
  try {
    var me = new URLSearchParams(location.search).get("me");
    if (me === "1") { localStorage.setItem("kp_me", "1"); alert("✓ Máy này sẽ không bị đếm vào lượt truy cập nữa"); }
    if (me === "0") localStorage.removeItem("kp_me");
    if (localStorage.getItem("kp_me") === "1") live = false;
  } catch (e) {}
  if (/[?&]evdebug=1/.test(location.search)) live = true;  // thử trên máy local

  function lang() { try { return localStorage.getItem("lang") || (location.pathname.indexOf("/vi") === 0 ? "vi" : "ja"); } catch (e) { return ""; } }
  function cut(v, n) { return v == null ? "" : String(v).slice(0, n || 100); }
  var sent = 0;
  function beacon(name, p) {
    if (!live || sent > 200) return; sent++;   // chặn spam: tối đa 200 sự kiện mỗi lần mở trang
    p = p || {};
    var a = p.search_term || p.shop || p.program || p.step || p.item || p.tab || p.platform || "";
    var b = p.item && a !== p.item ? p.item : p.value || p.n || "";
    var body = JSON.stringify({ e: cut(name, 40), a: cut(a), b: cut(b), p: cut(location.pathname, 60), l: lang() });
    try {
      if (navigator.sendBeacon) navigator.sendBeacon(EV_URL, new Blob([body], { type: "text/plain" }));
      else fetch(EV_URL, { method: "POST", body: body, keepalive: true, mode: "no-cors" });
    } catch (e) {}
  }
  window.kpTrack = function (name, params) { beacon(name, params); if (window.gtag) window.gtag("event", name, params || {}); };
  window.kpPage = function () {
    if (window.gtag) window.gtag("event", "page_view", { page_location: location.href, page_title: document.title });
  };

  if (CF_TOKEN && live && location.hostname === "kaitoriprice.com") {
    var cf = document.createElement("script");
    cf.defer = true; cf.src = "https://static.cloudflareinsights.com/beacon.min.js";
    cf.setAttribute("data-cf-beacon", JSON.stringify({ token: CF_TOKEN, spa: true }));
    document.head.appendChild(cf);
  }

  // vào web từ link có ?q= (thường là link trong bài Facebook) → biết link nào kéo người vào
  try {
    var q0 = new URLSearchParams(location.search).get("q");
    var ref = document.referrer ? new URL(document.referrer).hostname.replace(/^(www|m|l|lm)\./, "") : "";
    if (ref === location.hostname) ref = "";
    if (q0 || ref) beacon("land", { search_term: q0 || "(trang chủ)", value: ref || "(trực tiếp)" });
    // 07/11/2026: điểm bỏ đi — khi rời trang (đóng tab/chuyển app), người vào từ link đã làm gì và ở bao lâu
    if (q0 || ref) {
      var t0 = Date.now(), act = "none", done = false;
      document.addEventListener("click", function (e) {
        var s = e.target.closest && e.target.closest("a.sh, .pt a, a.sbest, a[rel~=sponsored]");
        act = s ? "shop" : act === "shop" ? "shop" : "click";
      }, true);
      addEventListener("scroll", function () { if (act === "none") act = "scroll"; }, { passive: true, once: true });
      document.addEventListener("keydown", function () { if (act !== "shop") act = "click"; }, true);  // gõ tìm cũng là có tương tác
      var fin = function () {
        if (done) return; done = true;
        var s = (Date.now() - t0) / 1000;
        beacon("land_exit", { step: act, value: s < 5 ? "<5s" : s < 15 ? "5-15s" : s < 60 ? "15-60s" : "60s+" });
      };
      addEventListener("pagehide", fin);
      document.addEventListener("visibilitychange", function () { if (document.visibilityState === "hidden") fin(); });
    }
  } catch (e) {}

  // tỉ lệ quay lại: trên máy chỉ lưu ngày vào gần nhất + số ngày đã vào; gửi đi chỉ nhóm "lần đầu / cách mấy ngày" (không ID)
  try {
    var td = new Date(Date.now() + 9 * 36e5).toISOString().slice(0, 10);
    var lv = localStorage.getItem("kp_lastday"), nd = +(localStorage.getItem("kp_days") || 0) + 1;
    if (lv !== td) {
      var gap = lv ? Math.round((Date.parse(td) - Date.parse(lv)) / 864e5) : -1;
      beacon("visit", { step: gap < 0 ? "new" : gap <= 1 ? "1d" : gap <= 7 ? "2-7d" : "8d+", value: lv ? (nd >= 6 ? "6+" : String(nd)) : "1" });
      localStorage.setItem("kp_lastday", td); localStorage.setItem("kp_days", lv ? nd : 1);
    }
  } catch (e) {}

  // bấm sang trang tiệm / link affiliate / mã giới thiệu (dùng chung cho app và trang tĩnh /p/)
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href]"); if (!a) return;
    var card = a.closest(".card"), item = card ? (card.querySelector(".c-name") || {}).textContent : (document.querySelector("h1") || {}).textContent;
    if (/sponsored/.test(a.rel)) return window.kpTrack("affiliate_click", { program: a.textContent.replace("→", "").trim(), item: (item || "").trim().slice(0, 100) });
    var shop = a.matches("a.sh") ? (a.querySelector(".sn b") || {}).textContent : a.closest(".pt") ? a.textContent : a.matches(".sbest") ? (a.querySelector("b") || {}).textContent : "";
    if (shop) return window.kpTrack("shop_click", { shop: shop.trim(), item: (item || "").trim().slice(0, 100) });
    if (a.closest("#qpick")) return window.kpTrack("qpick_click", { item: a.textContent.trim() });  // 10/11: chip 🔥 Hay xem trên trang chủ
    if (/\/guide\//.test(a.getAttribute("href") || "")) window.kpTrack("guide_click", { item: a.getAttribute("href") });
  }, true);

  // ghi chú quyền riêng tư ở chân trang
  addEventListener("DOMContentLoaded", function () {
    var f = document.querySelector("footer .wrap") || document.querySelector("footer"); if (!f) return;
    var p = document.createElement("p"); p.className = "small";
    var ls = ""; try { ls = localStorage.getItem("lang") || ""; } catch (e) {}
    var vi = /[?&]lang=ja/.test(location.search) ? false : ls === "vi" || (document.documentElement.lang || "").indexOf("vi") === 0 || location.pathname.indexOf("/vi") === 0 || /[?&]lang=vi/.test(location.search);
    p.textContent = GA_ID
      ? (vi ? "Trang dùng Google Analytics (cookie) để thống kê lượt xem ẩn danh." : "当サイトはアクセス解析にGoogle アナリティクス（Cookie）を使用しています。個人を特定する情報は収集しません。")
      : (vi ? "Trang thống kê ẩn danh (từ khoá, lượt bấm, lần đầu hay quay lại), không dùng cookie, không thu thập thông tin cá nhân. Món bạn đã xem và ngày vào gần nhất chỉ lưu trên máy bạn." : "当サイトはCookieを使わない匿名のアクセス解析（検索語・クリック数・初回/再訪の集計）を行っています。個人を特定する情報は収集しません。閲覧した商品と前回の訪問日はお使いの端末内にのみ保存されます。");
    f.appendChild(p);
  });

  if (!GA_ID || !live) return;  // GA chỉ bật khi có GA_ID, trên web thật
  var s = document.createElement("script");
  s.async = true; s.src = "https://www.googletagmanager.com/gtag/js?id=" + GA_ID;
  document.head.appendChild(s);
  window.dataLayer = window.dataLayer || [];
  window.gtag = function () { window.dataLayer.push(arguments); };
  window.gtag("js", new Date());
  // trang chủ là app 1 trang: app.js tự gửi page_view mỗi khi đổi nhóm/tìm kiếm; trang /p/ /c/ gửi tự động
  var app = location.pathname === "/" || location.pathname === "/index.html" || location.pathname.indexOf("/vi") === 0;
  window.gtag("config", GA_ID, { send_page_view: !app });
})();
