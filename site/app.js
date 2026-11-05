(async function () {
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const yen = (n) => n.toLocaleString("ja-JP") + "円";
  const man = (n) => (lang === "vi" ? (n / 10000).toLocaleString("vi-VN", { maximumFractionDigits: 2 }) + " man" : n.toLocaleString("ja-JP") + "円");
  const bust = "?" + Math.floor(Date.now() / 600000);
  // mặc định theo ngôn ngữ trình duyệt: máy tiếng Việt → vi, còn lại (Nhật, Googlebot…) → ja; ?lang=vi|ja để ép
  const qLang = new URLSearchParams(location.search).get("lang");
  let lang = (["vi", "ja"].includes(qLang) && qLang) || (location.pathname.startsWith("/vi") && "vi") || localStorage.getItem("lang") ||
    ((navigator.languages || [navigator.language || ""]).some((l) => /^vi/i.test(l)) ? "vi" : "ja");
  const T = () => window.I18N[lang];

  const idx = await fetch("data/index.json" + bust).then((r) => r.json());
  const SH = idx.shops, CATS = idx.cats;
  const cache = {}, hcache = {};
  const ICON = { phone: "📱", tablet: "📲", game: "🎮", card: "🃏", pc: "💻", camera: "📷", audio: "🎧", appliance: "🔌", watch: "⌚", hobby: "🧸", other: "📦" };
  const PRICE = [[0, Infinity], [0, 10000], [10000, 50000], [50000, 200000], [200000, Infinity]];
  const st = { view: "home", cat: null, q: "", f: { cat: new Set(), brand: new Set(), series: new Set(), cap: new Set(), shop: new Set() },
    price: 0, multi: false, gap: false, sort: "rec", layout: localStorage.getItem("layout2") || "card" };

  const promos = await fetch("promos.json" + bust).then((r) => r.json()).catch(() => ({ groups: [], inline: {} }));
  const AFF = promos.inline || {};
  // mã giới thiệu tiệm (promos.json → ref): hiện ở dòng giá tiệm đó + thẻ ở trang Ưu đãi
  const REF = Object.fromEntries(Object.entries(promos.ref || {}).filter(([, r]) => r && r.code));
  const refText = (sid) => { const r = REF[sid]; if (!r) return "";
    return lang === "vi" ? `🎁 Mã giới thiệu ${r.code}: coupon ${r.bonus.toLocaleString()}円 (nhập khi đăng ký mới)` : `🎁 紹介コード ${r.code} で${r.bonus.toLocaleString()}円分クーポン`; };
  const pxSeen = new Set();
  function pixel(src) {  // ảnh 1x1 đo lượt hiển thị A8 — mỗi chương trình 1 lần/trang
    if (!src || pxSeen.has(src)) return;
    pxSeen.add(src);
    const i = new Image(1, 1); i.src = src; i.alt = ""; i.style.cssText = "position:absolute;width:1px;height:1px;opacity:0"; document.body.appendChild(i);
  }
  // nút mua hàng mới qua もしもアフィリエイト (楽天市場 / Yahoo!ショッピング)
  const MOSHIMO = { rakuten: [5876750, 54, 54, 616, (q) => "https://search.rakuten.co.jp/search/mall/" + encodeURIComponent(q) + "/"],
    yahoo: [5876756, 1225, 1925, 18502, (q) => "https://shopping.yahoo.co.jp/search?p=" + encodeURIComponent(q)] };
  const buyQ = (it) => (it.key.startsWith("iPhone") ? it.key.split("|")[0] : it.name).replace(/[【\[(（][^】\])）]*[】\])）]/g, " ").replace(/\s+/g, " ").trim().slice(0, 60);
  const mLink = (k, q) => { const [a, p, pc, pl, u] = MOSHIMO[k]; return `https://af.moshimo.com/af/c/click?a_id=${a}&p_id=${p}&pc_id=${pc}&pl_id=${pl}&url=${encodeURIComponent(u(q))}`; };
  function buyBox(it) {
    const q = buyQ(it);
    return `<div class="buy"><span class="pr">PR</span><span>${T().buyNew}</span><a href="${mLink("rakuten", q)}" target="_blank" rel="sponsored nofollow noopener">楽天</a><a href="${mLink("yahoo", q)}" target="_blank" rel="sponsored nofollow noopener">Yahoo!</a></div>`;
  }
  // nhiều chương trình cho 1 nhóm hàng → chọn cố định theo sản phẩm (xen kẽ đều, để so chương trình nào hiệu quả)
  function affBox(cat, key = "") {
    let a = AFF[cat]; if (!a) return "";
    if (Array.isArray(a)) { let h = 0; for (const ch of key) h = (h * 31 + ch.charCodeAt(0)) >>> 0; a = a[h % a.length]; }
    pixel(a.px + "?a8mat=" + a.a8mat);
    return `<div class="aff"><span class="pr">PR</span><span>${T().affText}</span><a href="https://px.a8.net/svt/ejp?a8mat=${a.a8mat}" target="_blank" rel="sponsored nofollow noopener">${esc(a.name)} →</a></div>`;
  }
  // thẻ tín dụng tích điểm cho sản phẩm bán ở Apple (promos.cardpay) — thay dòng 楽天/Yahoo để thẻ không dài thêm
  function cardBox(it) {
    const c = promos.cardpay; if (!c || !c.a8mat || !it.msrp) return "";
    pixel(c.px + "?a8mat=" + c.a8mat);
    return `<div class="aff"><span class="pr">PR</span><span>${T().cardText}</span><a href="https://px.a8.net/svt/ejp?a8mat=${c.a8mat}" target="_blank" rel="sponsored nofollow noopener">${esc(c.name)} →</a></div>`;
  }
  const loadCat = async (c) => (cache[c] ||= FACETS.enrich(await fetch(`data/cat/${c}.json` + bust).then((r) => r.json())));
  const loadHist = async (c) => (hcache[c] ||= await fetch(`data/hist/${c}.json` + bust).then((r) => r.json()).catch(() => ({})));

  // ================= "Của tôi": theo dõi (♥) + kho hàng — lưu trên máy (localStorage), không cần đăng nhập
  const MINE_KEY = "kp_mine";
  const mine = (() => { try { return { watch: {}, stock: {}, ...JSON.parse(localStorage.getItem(MINE_KEY) || "{}") }; } catch { return { watch: {}, stock: {} }; } })();
  const saveMine = () => localStorage.setItem(MINE_KEY, JSON.stringify(mine));
  const idOf = (it) => it.cat + "|" + it.key;
  const REG = new Map();  // id → item đang hiển thị (để bấm ♥ / lưu kho biết món nào)
  async function mineItems() {
    const ids = [...new Set([...Object.keys(mine.watch), ...Object.keys(mine.stock)])];
    const cats = [...new Set(ids.map((i) => i.split("|")[0]).filter((c) => CATS[c]))];
    const all = (await Promise.all(cats.map(loadCat))).flat();
    const m = new Map(all.map((it) => [idOf(it), it]));
    return m;
  }
  function changedWatch(m) {
    // món theo dõi có giá cao nhất khác lần cuối bạn xem
    return Object.entries(mine.watch).map(([id, w]) => ({ id, w, it: m.get(id) })).filter((x) => x.it && x.it.best !== x.w.seen);
  }

  // ================= 👀 "Từ lần trước bạn xem": tự nhớ món đã xem (chỉ lưu trên máy bạn), lần sau vào báo giá đổi bao nhiêu
  const REC_KEY = "kp_recent", REC_GAP = 3 * 36e5;  // cách ≥3 giờ mới tính là "lần trước"
  let recent = []; try { const r = JSON.parse(localStorage.getItem(REC_KEY) || "[]"); if (Array.isArray(r)) recent = r.filter((x) => x && x.id && x.name); } catch {}
  const saveRec = () => { try { localStorage.setItem(REC_KEY, JSON.stringify(recent.slice(0, 8).map(({ cur, ...r }) => r))); } catch {} };
  function noteSeen(it) {
    if (!it || !it.best) return;
    const id = idOf(it), now = Date.now(), i = recent.findIndex((r) => r.id === id);
    const r = i >= 0 ? recent.splice(i, 1)[0] : { id };
    if (r.t && now - r.t > REC_GAP) { r.pp = r.p; r.pt = r.t; }
    Object.assign(r, { name: it.name, p: it.best, t: now, cur: it.best });
    recent.unshift(r); saveRec(); renderRecent();
  }
  let recReady = false;
  async function initRecent() {
    const now = Date.now(), use = recent.slice(0, 6);
    if (use.length) {
      const cats = [...new Set(use.map((r) => r.id.split("|")[0]).filter((c) => CATS[c]))];
      const m = new Map((await Promise.all(cats.map((c) => loadCat(c).catch(() => [])))).flat().map((it) => [idOf(it), it]));
      for (const r of use) {
        const it = m.get(r.id); if (!it || !it.best) continue;
        r.cur = it.best;
        if (r.t && now - r.t > REC_GAP) { r.pp = r.p; r.pt = r.t; r.p = it.best; r.t = now; }  // lần vào mới: mốc so sánh = giá lần trước
      }
      saveRec();
      const back = use.filter((r) => r.pt).length;
      if (back) window.kpTrack?.("recent_show", { n: back });
    }
    recReady = true; renderRecent();
  }
  function renderRecent() {
    const el = $("#recent"); if (!el) return;
    const t = T(), hide = !recReady || (!st.q && (st.view === "mine" || st.view === "deals"));
    const rows = hide ? [] : recent.filter((r) => r.pp && r.pt).slice(0, 6);
    if (!rows.length) { el.innerHTML = ""; return; }
    const now = Date.now();
    el.innerHTML = `<div class="rec"><b class="rec-t">${t.recTitle}</b>` + rows.map((r) => {
      const cur = r.cur ?? r.p, d = cur - r.pp, cls = d > 0 ? "up" : d < 0 ? "dn" : "eq";
      const dd = d ? `${d > 0 ? "▲" : "▼"}${Math.abs(d).toLocaleString("ja-JP")}円` : t.recSame;
      return `<button class="rec-i" data-q="${esc(r.name)}" title="${esc(`${t.recAgo((now - r.pt) / 36e5)}: ${yen(r.pp)} → ${yen(cur)}`)}"><span class="rn">${esc(r.name.replace(/^iPhone /, ""))}</span><span class="rp">${yen(cur)}</span><b class="${cls}">${dd}</b><small>${t.recAgo((now - r.pt) / 36e5)}</small></button>`;
    }).join("") + "</div>";
  }

  // ================= static text
  function applyLang() {
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach((el) => { const v = T()[el.dataset.i18n]; if (typeof v === "string") el.textContent = v; });
    // nút VI | JP: ngôn ngữ đang dùng được tô đậm, bấm để đổi
    $("#lang").innerHTML = `<span class="${lang === "vi" ? "on" : ""}">VI</span><span class="${lang === "ja" ? "on" : ""}">JP</span>`;
    $("#lang").setAttribute("aria-label", lang === "vi" ? "日本語に切り替え" : "Chuyển sang tiếng Việt");
    const fbg = $("#fbg"); if (fbg) fbg.hidden = lang !== "vi";
    // đầu/chân trang theo ngôn ngữ: link hướng dẫn + tên danh mục
    $("#hdGuide") && ($("#hdGuide").href = lang === "vi" ? "/guide/vi/" : "/guide/");
    $("#ftGuideJa") && ($("#ftGuideJa").hidden = lang === "vi");
    $("#ftGuideVi") && ($("#ftGuideVi").hidden = lang !== "vi");
    document.querySelectorAll(".ft-col a[data-c]").forEach((a) => { a.textContent = lang === "vi" ? (T().cats[a.dataset.c] || a.textContent) : (CAT_JA[a.dataset.c] || a.textContent); });  // nhóm FB tiếng Việt: chỉ hiện cho người dùng tiếng Việt
    $("#q").placeholder = T().search;
    $("#upd").innerHTML = `<span class="upd-l">${T().upd} ${idx.updated.slice(0, 5)}</span>${idx.updated.slice(5)}`; $("#upd").title = `${T().upd} ${idx.updated}`;
    $("#heroStat").textContent = T().hero(Object.keys(SH).length, idx.total.toLocaleString());
    $("#shops").innerHTML = T().stores + " " + Object.values(SH).map((s) => `<a href="${s.url}" target="_blank" rel="noopener">${s.name}</a>`).join("・");
    $("#sort").innerHTML = Object.entries(T().sort).map(([k, v]) => `<option value="${k}" ${st.sort === k ? "selected" : ""}>${v}</option>`).join("");
    document.querySelectorAll("#vtog button").forEach((b) => b.classList.toggle("on", b.dataset.v === st.layout));
    chips();
  }
  let chipsLang = null;
  function mobileCat() {
    // điện thoại: 1 hàng gọn [🏠] [Nhóm đang chọn ▾] [🎁], bấm ▾ mở lưới tất cả nhóm
    const t = T(), short = t.catsShort || {};
    const cur = st.view === "cat" && !st.q ? `${ICON[st.cat] || ""} ${short[st.cat] || t.cats[st.cat] || ""}` : `📂 ${t.pickShort}`;
    $("#mcLabel").textContent = cur;
    $("#mcPick").classList.toggle("on", st.view === "cat" && !st.q);
    $("#mcat .mc-home").classList.toggle("on", st.view === "home" && !st.q);
    $("#mcDeal").innerHTML = `🎁<span class="dl">${t.dealsShort}</span><small class="prb">PR</small>`;
    $("#mcDeal").classList.toggle("on", st.view === "deals" && !st.q);
    $("#mcMine").classList.toggle("on", st.view === "mine" && !st.q);
    $("#hdMine").classList.toggle("on", st.view === "mine" && !st.q);
    $("#cgTitle").textContent = t.pickCat;
  }
  function chips() {
    mobileCat();
    // chỉ dựng lại HTML khi đổi ngôn ngữ; còn lại chỉ đổi class → thanh chip không bị nhảy/mất vị trí cuộn ngang
    if (chipsLang === lang) {
      document.querySelectorAll("#chips button, #cgrid button").forEach((b) => {
        const on = b.dataset.c ? st.view === "cat" && st.cat === b.dataset.c && !st.q : st.view === b.dataset.v && !st.q;
        b.classList.toggle("on", on);
      });
      return;
    }
    chipsLang = lang;
    // thứ tự cố định theo mức quan tâm của người đi kaitori (hot trước)
    const PRIO = ["phone", "game", "camera", "card", "tablet", "audio", "watch", "pc", "hobby", "appliance", "other"];
    const order = Object.entries(CATS).sort((a, b) => (PRIO.indexOf(a[0]) + 99) % 99 - (PRIO.indexOf(b[0]) + 99) % 99);
    const short = T().catsShort || {};
    $("#chips").innerHTML =
      `<button data-v="home" class="${st.view === "home" ? "on" : ""}"><span class="lf">${T().home}</span><span class="ls">🏠</span></button>` +
      order.map(([c, v]) => `<button data-c="${c}" class="${st.view === "cat" && st.cat === c && !st.q ? "on" : ""}">${ICON[c] || ""} <span class="lf">${T().cats[c] || v.label}</span><span class="ls">${short[c] || T().cats[c] || v.label}</span><small>${v.count.toLocaleString()}</small></button>`).join("") +
      `<button data-v="deals" class="deal ${st.view === "deals" ? "on" : ""}">${T().deals}</button>`;
    // "♥ Của tôi" không phải nhóm hàng → đặt trên header (máy tính), không trộn vào hàng chip
    $("#hdMine").innerHTML = `♥ <span>${T().mine}</span><b class="mine-n" hidden></b>`;
    $("#hcats").innerHTML = `<h2>${T().hcTitle}</h2><div class="cgrid">` + order.map(([c, v]) =>
      `<button data-c="${c}"><span class="ci">${ICON[c] || "📦"}</span><span class="cn">${short[c] || T().cats[c] || v.label}</span><span class="cc">${v.count.toLocaleString()}</span></button>`).join("") + "</div>";
    $("#cgrid").innerHTML = order.map(([c, v]) =>
      `<button data-c="${c}" class="${st.view === "cat" && st.cat === c && !st.q ? "on" : ""}"><span class="ci">${ICON[c] || "📦"}</span><span class="cn">${short[c] || T().cats[c] || v.label}</span><span class="cc">${v.count.toLocaleString()}</span></button>`).join("");
  }

  // ================= card / table
  function spark(it, w = 84, h = 32) {
    const s = ((hcache[it.cat] || {})[it.key] || []).slice(-30);
    if (s.length < 2) return "";
    const v = s.map((p) => p[1]), mn = Math.min(...v), mx = Math.max(...v), r = mx - mn || 1;
    const pts = v.map((y, i) => [(i / (v.length - 1)) * (w - 6) + 2, 3 + (1 - (y - mn) / r) * (h - 8)]);
    const c = v[v.length - 1] >= v[0] ? "#16a34a" : "#dc2626", line = pts.map((p) => p.map((n) => n.toFixed(1)).join(",")).join(" ");
    const [ex, ey] = pts[pts.length - 1];
    return `<svg class="spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" aria-hidden="true"><path d="M${pts[0][0].toFixed(1)},${h - 1} L${line.replace(/ /g, " L")} L${ex.toFixed(1)},${h - 1} Z" fill="${c}" opacity=".12"/><polyline fill="none" stroke="${c}" stroke-width="2" stroke-linejoin="round" points="${line}"/><circle cx="${ex.toFixed(1)}" cy="${ey.toFixed(1)}" r="2.8" fill="${c}"/></svg>`;
  }
  // thước giá: hôm nay nằm ở đâu trong khoảng thấp–cao các ngày có dữ liệu
  function gauge(it) {
    const s = ((hcache[it.cat] || {})[it.key] || []).slice(-30);
    if (s.length < 3) return "";
    const v = s.map((p) => p[1]), mn = Math.min(...v), mx = Math.max(...v);
    if (mx === mn) return "";
    const pos = Math.max(0, Math.min(100, ((it.best - mn) / (mx - mn)) * 100)), t = T();
    const lab = pos >= 90 ? t.gHi(s.length) : pos <= 10 ? t.gLo(s.length) : t.gMid(s.length);
    return `<div class="gauge" title="${esc(t.trendTip)}"><div class="g-track"><span class="g-knob" style="left:${pos.toFixed(0)}%"></span></div><div class="g-ends"><span>${man(mn)}</span><span>${lab}</span><span>${man(mx)}</span></div></div>`;
  }
  // 📈 xu hướng: giá cao nhất hôm nay so với trung bình tối đa 7 ngày trước (cần ≥ 3 ngày dữ liệu). Chỉ nêu sự thật, không khuyên bán/giữ.
  function trend(it) {
    const s = (hcache[it.cat] || {})[it.key] || [];
    if (s.length < 3) return "";
    const prev = s.slice(-8, -1).map((p) => p[1]), avg = prev.reduce((a, b) => a + b, 0) / prev.length;
    const pct = ((it.best - avg) / avg) * 100, n = prev.length, t = T();
    const top = pct > 0.5 && s.length >= 4 && it.best >= Math.max(...s.map((p) => p[1]));
    const cls = pct > 0.5 ? "up" : pct < -0.5 ? "dn" : "eq";
    return `<span class="trend ${cls}" title="${esc(t.trendTip)}">${t.trend(cls, n, Math.abs(pct).toFixed(1))}${top ? t.trendTop(s.length) : ""}</span>`;
  }
  // tiệm không có trang riêng cho SP: link "#:~:text=" → trình duyệt tự cuộn tới & tô vàng đúng dòng sản phẩm
  const lstUrl = (p, it) => p.url.split("#")[0] + "#:~:text=" + encodeURIComponent((p.n || it.name).trim()).replace(/-/g, "%2D");
  function shopLink(sid, p, it) {
    const lst = SH[sid]?.list;
    return lst
      ? `<a href="${esc(lstUrl(p, it))}" target="_blank" rel="noopener nofollow" class="lst" data-copy="${esc(p.n || it.name)}" title="${esc(T().listTip)}">${SH[sid]?.name || sid} 🔍</a>`
      : `<a href="${esc(p.url)}" target="_blank" rel="noopener nofollow">${SH[sid]?.name || sid}</a>`;
  }
  function shopRows(it, shops) {
    const t = T();
    return shops.map(([sid, p, d], i) => {
      const extra = d != null ? (d > 0 ? `<span class="nt cd">${t.colDed(yen(d))}</span>` : d < 0 ? `<span class="nt">${p.min && p.min < p.price ? `${t.colUnk} (${yen(p.min)}〜${yen(p.price)})` : t.colUnk}</span>` : "")
        : p.min && p.min !== p.price ? `<span class="nt">${t.colorFrom} ${yen(p.min)}</span>` : p.note ? `<span class="nt">${esc(p.note.slice(0, 16))}</span>` : "";
      const lst = SH[sid]?.list, nm = SH[sid]?.name || sid;
      // cả dòng là 1 link sang trang tiệm (có ↗ ở cuối để người dùng biết bấm được)
      return `<a class="sh ${i === 0 && shops.length > 1 ? "top" : ""} ${lst ? "lst" : ""}" href="${esc(lst ? lstUrl(p, it) : p.url)}" target="_blank" rel="noopener nofollow"${lst ? ` data-copy="${esc(p.n || it.name)}" title="${esc(t.listTip)}"` : ""}>`
        + `<span class="sn"><b>${nm}</b>${lst ? `<i class="sq">${t.searchTag}</i>` : ""}${extra}${REF[sid] ? `<i class="ref">${esc(refText(sid))}</i>` : ""}</span><span class="p">${d < 0 && p.min && p.min < p.price ? yen(p.min) + "〜" : yen(p.price - (d > 0 ? d : 0))}</span><span class="go" aria-hidden="true">↗</span></a>`;
    }).join("");
  }
  // 🍎 so với giá niêm yết Apple (chỉ đời Apple đang bán: iPhone 18 / Duo)
  function msrpLine(it, best = it.best) {
    if (!it.msrp || !/^iPhone (18|Duo)\b/.test(it.key)) return "";
    const d = best - it.msrp, cls = d >= 0 ? "up" : "dn";
    return `<div class="msrp ${cls}" title="${esc(T().msrpTip)}">${T().msrpLine(yen(it.msrp), `<b>${d >= 0 ? "+" : "−"}${yen(Math.abs(d))}</b>`)}</div>`;
  }
  // 🎨 trừ tiền theo màu: đọc ghi chú tiệm ("ブラック,グレイシャー-7000,シルバー-11000", "色減額:White-6000"…)
  // → {by: {sid: {màu: số tiền}}, cols: [màu…]}; màu chỉ nhận khi có tên màu rõ ràng, số tiền 1.000–60.000円
  const COLS = [["white", /ホワイト|white/i], ["black", /ブラック|black/i], ["silver", /シルバー|silver/i], ["glacier", /グレイシャー|glacier/i],
    ["nightsky", /ナイトスカイ/i], ["blue", /ブルー|blue/i], ["orange", /オレンジ|orange/i], ["red", /レッド|バーガンディ|burgundy|red/i],
    ["pink", /ピンク|pink/i], ["green", /グリーン|green/i], ["purple", /パープル|purple/i], ["gold", /ゴールド|gold/i]];
  const COL_RE = /スターホワイト|ホワイト|ブラック|シルバー|グレイシャー|ナイトスカイ|ディープブルー|ブルー|コズミックオレンジ|オレンジ|レッド|バーガンディ|ピンク|グリーン|パープル|ゴールド|white|black|silver|glacier|blue|orange|burgundy|red|pink|green|purple|gold|(\d[\d,]{3,})/gi;
  const colKey = (w) => (COLS.find(([, r]) => r.test(w)) || [])[0];
  const DED = new WeakMap(), CSEL = new Map();
  function colorDeds(it) {
    if (DED.has(it)) return DED.get(it);
    const by = {}, seen = new Set(), hit = new Set(), multi = new Set();
    for (const [sid, p] of Object.entries(it.prices)) {
      // tiệm đăng mỗi màu 1 giá (p.c từ run.py): mức trừ = giá cao nhất − giá màu đó (0 = màu đó được đủ giá)
      const cs = Object.entries(p.c || {});
      if (cs.length >= 2) {
        multi.add(sid);
        for (const [k, v] of cs) { (by[sid] ||= {})[k] = Math.max(0, p.price - v); seen.add(k); if (p.price > v) hit.add(k); }
        continue;
      }
      const t = (p.note || "").replace(/色減額[:：]?/g, "").split(/\s*(?:店頭|郵送|△|※)/)[0];
      let pend = [];
      for (const m of t.matchAll(COL_RE)) {
        if (!m[1]) { const k = colKey(m[0]); if (k && !pend.includes(k)) pend.push(k); continue; }
        const amt = +m[1].replace(/,/g, "");
        if (pend.length && amt >= 1000 && amt <= 60000) for (const k of pend) { (by[sid] ||= {})[k] = amt; seen.add(k); hit.add(k); }
        pend = [];
      }
    }
    // chỉ hiện ô chọn màu khi có ít nhất 1 màu thật sự bị trừ ở 1 tiệm
    const r = { by, multi, cols: hit.size ? COLS.map(([k]) => k).filter((k) => seen.has(k)) : [] };
    DED.set(it, r);
    return r;
  }
  function colorPick(it, id, col, shops) {
    const { cols } = colorDeds(it), t = T();
    if (!cols.length) return "";
    const b = (k, label) => `<button type="button" class="${col === k ? "on" : ""}" data-col="${k}" data-id="${esc(id)}">${esc(label)}</button>`;
    let note = "";
    if (col) {  // 1 dòng tóm tắt thay cho nhãn lặp ở từng tiệm
      const ds = shops.map((x) => x[2]).filter((d) => d > 0), unk = shops.some((x) => x[2] < 0);
      const name = col === "_o" ? t.colOther : t.colNames[col] || col;
      note = ds.length ? t.colSumDed(name, yen(Math.min(...ds)), yen(Math.max(...ds))) : t.colSumNone(name);
      note = `<div class="cnote ${ds.length ? "" : "ok"}">${esc(note)}${unk ? " " + esc(t.colSumUnk) : ""}</div>`;
    }
    return `<div class="cpick"><span>${t.colPick}</span>${cols.map((k) => b(k, t.colNames[k] || k)).join("")}${b("_o", t.colOther)}</div>${note}`;
  }
  function boostTag(it) {
    const b = Object.entries(it.prices).filter(([, p]) => p.b).map(([s]) => SH[s]?.name || s);
    return b.length ? `<div class="boost">${esc(T().boostTag(b.join("・")))}</div>` : "";
  }
  function moversHtml(mv) {
    const t = T(), row = (i) => `<button class="mv-i" data-q="${esc(i.name)}"><span>${esc(i.name)}</span><b class="${i.mv > 0 ? "up" : "dn"}">${i.mv > 0 ? "▲" : "▼"}${Math.abs(i.mv).toLocaleString()}円</b><small>${yen(i.best)}</small></button>`;
    const col = (title, arr) => arr.length ? `<div class="mv-c"><h3>${title}</h3>${arr.slice(0, 3).map(row).join("")}</div>` : "";
    const h = col(t.upTitle, mv.up || []) + col(t.downTitle, mv.down || []);
    return h ? `<div class="movers">${h}</div>` : "";
  }
  function card(it) {
    const t = T();
    const id = idOf(it); REG.set(id, it);
    // đã chọn màu → giá thực nhận = giá tiệm − mức trừ màu tiệm ghi; xếp lại theo giá thực nhận
    const { by, multi, cols } = colorDeds(it), col = cols.length ? CSEL.get(id) || "" : "";
    // d: số tiền trừ; -1 = tiệm có đăng giá theo màu nhưng không có màu này (chưa rõ) → tạm tính giá cao nhất của tiệm
    // tiệm có biến thể giá thấp hơn (p.min) mà không rõ màu nào → cũng "chưa rõ", không khẳng định "không trừ"
    const dOf = (s) => (by[s]?.[col] ?? (multi.has(s) || it.prices[s].min < it.prices[s].price ? -1 : 0));
    // chưa rõ giá màu này → xếp theo giá thấp nhất của tiệm (thận trọng), không đẩy lên đầu
    const net = ([s, p]) => { if (!col) return p.price; const d = dOf(s); return d < 0 ? Math.min(p.price, p.min || p.price) : p.price - d; };
    const shops = Object.entries(it.prices).map((e) => col ? [e[0], e[1], dOf(e[0])] : e).sort((a, b) => net(b) - net(a));
    const bestP = net(shops[0]), bestS = shops[0][0];
    const chg = it.chg && !col ? `<span class="chg ${it.chg > 0 ? "up" : "dn"}">${it.chg > 0 ? "▲" : "▼"}${Math.abs(it.chg).toLocaleString()}</span>` : "";
    const rows = shopRows(it, shops);
    const spread = col ? bestP - net(shops[shops.length - 1]) : it.spread;
    const diff = it.n_shops > 1 && spread > 0 ? `<div class="diff">${t.diff(yen(spread))}</div>` : "";
    const br = it._f?.brand !== "Khác" ? it._f?.brand : "";
    const tag = [br && !(it._f?.series || "").startsWith(br.split(" ")[0]) ? br : "", it._f?.series && FL(it._f.series), it._f?.cap].filter(Boolean).join(" · ");
    const fav = mine.watch[id] ? "on" : "";
    // B · "quyết định nhanh": bán ở đâu, được bao nhiêu, giá đang cao hay thấp → top 3 → nút mở tiệm; phần còn lại thu gọn
    const lnk = (sid, p) => (SH[sid]?.list ? lstUrl(p, it) : p.url);
    const pv = ([sid, p, d]) => (col && d < 0 && p.min && p.min < p.price ? man(p.min) + "〜" : man(p.price - (d > 0 ? d : 0)));
    const pods = shops.slice(0, 3).map((e, i) => {
      const [sid, p, d] = e, lst = SH[sid]?.list;
      return `<a class="sh pod ${i === 0 ? "first" : ""}" href="${esc(lnk(sid, p))}" target="_blank" rel="noopener nofollow"${lst ? ` data-copy="${esc(p.n || it.name)}"` : ""}>`
        + `<span class="rk">#${i + 1}</span><span class="sn"><b>${SH[sid]?.name || sid}</b></span><span class="pa">${pv(e)}</span>`
        + `${d > 0 ? `<span class="nt cd">−${(d / 1000).toLocaleString()}k ${t.colShort}</span>` : d < 0 ? `<span class="nt">${t.colUnkShort}</span>` : ""}</a>`;
    }).join("");
    const rest = shops.slice(3);
    const restLine = rest.length ? t.restN(rest.length, man(net(rest[rest.length - 1])), man(net(rest[0]))) : "";
    const vsA = it.msrp && /^iPhone (18|Duo)\b/.test(it.key) ? bestP - it.msrp : null;
    const pills = [col ? "" : trend(it), vsA != null ? `<span class="trend ${vsA >= 0 ? "up" : "dn"}" title="${esc(t.msrpTip)}">🍎 Apple ${vsA >= 0 ? "+" : "−"}${yen(Math.abs(vsA))}</span>` : "", chg].filter(Boolean).join("");
    const bp = shops[0][1];
    return `<article class="card bcard">
      <div class="c-top"><div><div class="c-name">${esc(it.name)}</div><div class="c-sub">${ICON[it.cat] || ""} ${esc(tag || t.cats[it.cat] || "")}・${t.shopsN(it.n_shops)}</div></div><div class="c-act"><button class="shr" data-id="${esc(id)}" aria-label="${esc(t.share)}" title="${esc(t.share)}"><svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7"/><path d="M12 3v12"/><path d="m7 8 5-5 5 5"/></svg></button><button class="fav ${fav}" data-id="${esc(id)}" aria-label="${esc(t.watch)}" title="${esc(t.watch)}">${fav ? "♥" : "♡"}</button></div></div>
      <div class="bhero"><div class="bh-l"><div class="bh-lab">${it.n_shops > 1 ? t.sellAt(SH[bestS]?.name || "") : SH[bestS]?.name || ""}${col ? ` · ${esc(col === "_o" ? t.colOther : t.colNames[col] || col)}` : ""}</div>
        <div class="bh-p">${bestP.toLocaleString("ja-JP")}<small>円</small></div></div>${spark(it)}${col ? "" : gauge(it)}</div>
      ${pills ? `<div class="bh-pills">${pills}</div>` : ""}
      ${colorPick(it, id, col, shops)}
      ${shops.length > 1 ? `<div class="pods">${pods}</div>` : ""}
      ${rest.length ? `<div class="shops clip">${shopRows(it, shops)}</div><button class="shmore" type="button">${restLine} · ${t.allShops(shops.length)} ▾</button>` : ""}
      <a class="sbest cta" href="${esc(lnk(bestS, bp))}" target="_blank" rel="noopener nofollow"${SH[bestS]?.list ? ` data-copy="${esc(bp.n || it.name)}"` : ""}><span>${t.ctaOpen}<b>${SH[bestS]?.name || ""}</b></span><span aria-hidden="true">↗</span></a>
      ${REF[bestS] ? `<div class="ref-line">${esc(refText(bestS))}</div>` : ""}${boostTag(it)}
      <div class="b-acts"><button class="bell ${mine.watch[id]?.target ? "on" : ""}" type="button" data-id="${esc(id)}" title="${esc(t.bellTip)}">${mine.watch[id]?.target ? "🔔 " + yen(mine.watch[id].target) : t.bellBtn}</button></div>
      ${affBox(it.cat, it.key)}${cardBox(it) || buyBox(it)}
      <div class="calc-row"><label class="calc">${t.calc} <input type="number" inputmode="numeric" placeholder="${Math.round(it.best * 0.9).toLocaleString()}" data-best="${it.best}"> 円 → ${t.profit} <b class="pf">—</b></label><button class="stk ${mine.stock[id] ? "on" : ""}" data-id="${esc(id)}">${mine.stock[id] ? t.inStock : t.addStock}</button></div>
    </article>`;
  }
  // C · danh sách gọn (điện thoại): 1 dòng / máy, chạm để mở thẻ B ngay bên dưới
  function crow(it, open) {
    const id = idOf(it); REG.set(id, it);
    const vsA = it.msrp && /^iPhone (18|Duo)\b/.test(it.key) ? it.best - it.msrp : null;
    const k = (n) => (Math.abs(n) / 1000).toLocaleString(undefined, { maximumFractionDigits: 1 }) + "k";
    return `<div class="crow ${open ? "open" : ""}" data-id="${esc(id)}"><button class="crow-h" type="button" data-id="${esc(id)}" aria-expanded="${!!open}">
      <span class="cr-n">${esc(it.name)}</span><span class="cr-p">${man(it.best)}</span>
      <span class="cr-s">${it.n_shops > 1 ? SH[it.best_shop]?.name || "" : ""}${vsA != null ? ` <i class="${vsA >= 0 ? "up" : "dn"}">Apple ${vsA >= 0 ? "+" : "−"}${k(vsA)}</i>` : ""}${it.chg ? ` <i class="${it.chg > 0 ? "up" : "dn"}">${it.chg > 0 ? "▲" : "▼"}${k(it.chg)}</i>` : ""}</span>
      <span class="cr-sp">${spark(it, 64, 22)}</span></button><div class="crow-b">${open ? card(it) : ""}</div></div>`;
  }
  function tableHead() {
    const t = T();
    return `<div class="tbl"><div class="tr th"><span>${t.colName}</span><span>${t.colBest}</span><span>${t.colShop}</span><span>${t.col2nd}</span><span>${t.colGap}</span></div>`;
  }
  function trow(it) {
    const shops = Object.entries(it.prices).sort((a, b) => b[1].price - a[1].price);
    const [s1, p1] = shops[0], s2 = shops[1];
    const chg = it.chg ? `<i class="${it.chg > 0 ? "up" : "dn"}">${it.chg > 0 ? "▲" : "▼"}${Math.abs(it.chg).toLocaleString()}</i>` : "";
    return `<div class="tr"><span class="tn">${esc(it.name)}<small>${esc([it._f?.series && FL(it._f.series), it._f?.cap].filter(Boolean).join(" · "))} · ${T().shopsN(it.n_shops)}</small></span>
      <span class="tb">${yen(it.best)} ${chg}</span><span>${shopLink(s1, p1, it)}</span>
      <span class="t2">${s2 ? `${yen(s2[1].price)}<small>${SH[s2[0]]?.name || ""}</small>` : "—"}</span>
      <span class="tg">${it.spread ? "+" + it.spread.toLocaleString() : "—"}</span>
      ${shops.length > 1 ? `<button class="tmore" type="button">${T().allShops(shops.length)} ▾</button><div class="tx shops">${shopRows(it, shops)}</div>` : ""}</div>`;
  }

  // ================= filtering with facet counts
  let base = [], view = [], shown = 0;
  const PAGE = 48;
  function passes(it, skip) {
    const f = st.f, [lo, hi] = PRICE[st.price];
    if (st.multi && it.n_shops < 2) return false;
    if (st.gap && it.spread < 3000) return false;
    if (it.best < lo || it.best >= hi) return false;
    if (skip !== "cat" && f.cat.size && !f.cat.has(it.cat)) return false;
    if (skip !== "brand" && f.brand.size && !f.brand.has(it._f.brand)) return false;
    if (skip !== "series" && f.series.size && !f.series.has(it._f.series)) return false;
    if (skip !== "cap" && f.cap.size && !f.cap.has(it._f.cap)) return false;
    if (skip !== "shop" && f.shop.size && !Object.keys(it.prices).some((s) => f.shop.has(s))) return false;
    return true;
  }
  function counts(key, getter) {
    const m = new Map();
    for (const it of base) {
      if (!passes(it, key)) continue;
      for (const v of [].concat(getter(it))) if (v) m.set(v, (m.get(v) || 0) + 1);
    }
    return m;
  }
  function facetBlock(key, title, map, { sort, limit = 10, labels } = {}) {
    if (!map.size || (map.size === 1 && !st.f[key].size)) return "";
    let entries = [...map.entries()];
    entries.sort(sort ? (a, b) => sort(a[0], b[0]) : (a, b) => b[1] - a[1]);
    for (const v of st.f[key]) if (!map.has(v)) entries.unshift([v, 0]);
    const open = st._open?.[key];
    if (entries.length <= limit + 2) limit = entries.length;  // chỉ ẩn khi dư ≥3 lựa chọn, tránh "Xem thêm 1"
    const rows = entries.map(([v, n], i) => `<label class="fo ${i >= limit && !open ? "hid" : ""}"><input type="checkbox" data-k="${key}" value="${esc(v)}" ${st.f[key].has(v) ? "checked" : ""}><span>${esc(labels ? labels(v) : v)}</span><em>${n}</em></label>`).join("");
    const more = entries.length > limit ? `<button class="fmore" data-k="${key}">${open ? T().less : T().moreN(entries.length - limit)}</button>` : "";
    return `<div class="fg" data-fk="${key}"><div class="fg-t">${title}</div>${rows}${more}</div>`;
  }
  // giá trị bộ lọc trong facets.js là tiếng Việt (dùng làm khoá) → khi xem tiếng Nhật thì dịch để không lẫn tiếng Việt
  const FL_JA = { "Khác": "その他", "Tay cầm": "コントローラー", "Switch 2 (bộ kèm game)": "Switch 2（ソフト同梱）", "Nintendo (khác)": "Nintendo（その他）" };
  const FL = (v) => (lang === "ja" ? FL_JA[v] || v : v === "Khác" ? T().otherB : v);
  const PIN = ["iPad", "Nintendo Switch 2", "PlayStation 5", "Pokémon", "iPhone"];  // hãng hay tìm nhất lên đầu (cuối mảng = ưu tiên cao nhất)
  function renderFacets() {
    const t = T();
    let h = "";
    if (st.q) h += facetBlock("cat", t.fCat, counts("cat", (i) => i.cat), { labels: (c) => `${ICON[c] || ""} ${t.cats[c] || c}` });
    h += facetBlock("brand", t.fBrand, counts("brand", (i) => i._f.brand), { labels: FL, sort: (a, b) => (a === "Khác") - (b === "Khác") || PIN.indexOf(b) - PIN.indexOf(a) || (cnt.brand.get(b) || 0) - (cnt.brand.get(a) || 0) });
    const sc = counts("series", (i) => i._f.series);
    h += facetBlock("series", t.fSeries, sc, { labels: FL, sort: st.f.brand.size ? FACETS.seriesSort : (a, b) => (sc.get(b) || 0) - (sc.get(a) || 0), limit: 12 });
    h += facetBlock("cap", t.fCap, counts("cap", (i) => i._f.cap), { sort: FACETS.capSort });
    h += facetBlock("shop", t.fShop, counts("shop", (i) => Object.keys(i.prices)), { labels: (s) => SH[s]?.name || s, limit: 12 });
    h += `<div class="fg" data-fk="price"><div class="fg-t">${t.fPrice}</div>${t.price.map((p, i) => `<label class="fo"><input type="radio" name="pr" data-p="${i}" ${st.price === i ? "checked" : ""}><span>${p}</span></label>`).join("")}</div>`;
    h += `<div class="fg" data-fk="more"><div class="fg-t">${t.fMore}</div>
      <label class="fo"><input type="checkbox" id="multi" ${st.multi ? "checked" : ""}><span>${t.fMulti}</span></label>
      <label class="fo"><input type="checkbox" id="gap" ${st.gap ? "checked" : ""}><span>${t.fGap}</span></label></div>`;
    const side = $("#side"), keep = side.scrollTop;  // giữ vị trí cuộn của bộ lọc khi tick → không bị nhảy lên đầu
    $("#facets").innerHTML = h;
    side.scrollTop = keep;
  }
  let cnt = { brand: new Map() };
  function renderActive() {
    const t = T(), chipsA = [];
    const lab = { cat: (c) => t.cats[c], shop: (s) => SH[s]?.name || s };
    for (const k of ["cat", "brand", "series", "cap", "shop"]) for (const v of st.f[k]) chipsA.push(`<button class="ac" data-k="${k}" data-v="${esc(v)}">${esc(lab[k] ? lab[k](v) : v)} ✕</button>`);
    if (st.price) chipsA.push(`<button class="ac" data-k="price">${t.price[st.price]} ✕</button>`);
    if (st.multi) chipsA.push(`<button class="ac" data-k="multi">${t.fMulti} ✕</button>`);
    if (st.gap) chipsA.push(`<button class="ac" data-k="gap">${t.fGap} ✕</button>`);
    $("#active").innerHTML = chipsA.length ? chipsA.join("") + `<button class="ac clr" data-k="all">${t.reset}</button>` : "";
    $("#fCount").textContent = chipsA.length ? `(${chipsA.length})` : "";
  }
  const SLIDERS = `<svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M2 4h7M13 4h1M2 12h1M7 12h7"/><circle cx="11" cy="4" r="2"/><circle cx="5" cy="12" r="2"/></svg>`;
  function renderQuick() {
    // điện thoại: dãy nút theo LOẠI bộ lọc (kiểu Amazon/Rakuten) — bấm nút nào mở đúng bộ lọc đó
    const t = T(), n = st.price + st.multi + st.gap + Object.values(st.f).reduce((a, x) => a + x.size, 0);
    const q = [`<button class="qc qf ${n ? "has" : ""}" data-open="all">${SLIDERS}<span>${t.filterShort}</span>${n ? `<b>${n}</b>` : ""}</button>`];
    const lab = (k, set) => { const v = [...set]; return v.length ? (v.length === 1 ? FL(v[0]) : `${v[0]} +${v.length - 1}`) : ""; };
    const chip = (key, name, has) => { const v = has || ""; return `<button class="qc dd ${v ? "on" : ""}" data-open="${key}">${esc(v || name)}<i>▾</i></button>`; };
    q.push(chip("price", t.qPrice, st.price ? t.price[st.price] : ""));
    q.push(`<button class="qc tg ${st.multi ? "on" : ""}" data-k="multi" ${st.multi ? "" : 'data-add="1"'}>${st.multi ? "✓ " : ""}${t.qMulti}</button>`);
    if (st.f.shop.size) q.push(chip("shop", t.fShop, lab("shop", new Set([...st.f.shop].map((x) => SH[x]?.name || x)))));
    $("#quick").innerHTML = q.join("");
    renderDrill();
  }
  // điện thoại: chọn theo bậc Hãng → Dòng máy → Dung lượng ngay trên 1 hàng chip (kiểu kakaku/Mercari), không phải mở bảng lọc
  function renderDrill() {
    const t = T(), steps = [["brand", t.qBrand, (i) => i._f.brand], ["series", t.qSeries, (i) => i._f.series], ["cap", t.qCap, (i) => i._f.cap]];
    const crumbs = [];
    let next = null;
    for (const [k, name, get] of steps) {
      if (st.f[k].size) { const v = [...st.f[k]]; crumbs.push(`<button class="dc" data-k="${k}">${esc(v.length > 1 ? `${v[0]} +${v.length - 1}` : FL(v[0]))}<i>✕</i></button>`); continue; }
      const m = counts(k, get);
      if (m.size > 1) { next = [k, name, m]; break; }
    }
    let opts = "";
    if (next) {
      const [k, name, m] = next;
      const sort = k === "cap" ? FACETS.capSort : k === "series" && st.f.brand.size ? FACETS.seriesSort
        : k === "brand" ? (a, b) => (a === "Khác") - (b === "Khác") || PIN.indexOf(b) - PIN.indexOf(a) || m.get(b) - m.get(a) : (a, b) => m.get(b) - m.get(a);
      const vals = [...m.keys()].sort(sort);
      opts = `<span class="dl">${esc(t.drPick(name))}</span>` + vals.map((v) => `<button class="do" data-k="${k}" data-v="${esc(v)}">${esc(FL(v))}<em>${m.get(v)}</em></button>`).join("");
    }
    const el = $("#drill");
    el.innerHTML = (crumbs.length ? `<div class="dcr">${crumbs.join('<span class="dsep">›</span>')}</div>` : "") + (opts ? `<div class="dop">${opts}</div>` : "");
    el.hidden = !el.innerHTML;
  }
  function sortItems(items) {
    const f = { new: (a, b) => (b.first || "").localeCompare(a.first || "") || ((b._f.rec || 0) - (a._f.rec || 0)) || (b.best - a.best),
      rec: (a, b) => (b.n_shops - a.n_shops) || (b.spread - a.spread) || (b.best - a.best), best: (a, b) => b.best - a.best,
      spread: (a, b) => b.spread - a.spread, up: (a, b) => (b.chg || 0) - (a.chg || 0), down: (a, b) => (a.chg || 0) - (b.chg || 0),
      name: (a, b) => a.name.localeCompare(b.name, "ja") }[st.sort];
    return items.sort(f);
  }
  function paint(reset) {
    const tbl = st.layout === "table";
    if (reset) { shown = 0; $("#list").innerHTML = tbl ? tableHead() + "</div>" : ""; $("#list").className = tbl ? "" : "list"; }
    const slice = view.slice(shown, shown + PAGE);
    const target = tbl ? $("#list .tbl") : $("#list");
    // điện thoại: danh sách gọn (C), chạm để mở thẻ (B); ít kết quả (vd link ?q= từ Facebook) thì mở sẵn món đầu
    const compact = !tbl && matchMedia("(max-width:560px)").matches;
    const autoOpen = compact && reset && (view.length <= 3 || !!st.q);
    target.insertAdjacentHTML("beforeend", slice.map(tbl ? trow : compact ? (it, i) => crow(it, autoOpen && i === 0) : card).join(""));
    shown += slice.length;
    $("#more").hidden = shown >= view.length;
    $("#empty").hidden = view.length > 0;
  }
  function refresh() {
    cnt.brand = counts("brand", (i) => i._f.brand);
    view = sortItems(base.filter((i) => passes(i)));
    $("#hint").textContent = $("#mhint").textContent = st.q ? T().hintQ(st.q, view.length.toLocaleString()) : T().hintCat(T().cats[st.cat], view.length.toLocaleString(), CATS[st.cat]?.multi?.toLocaleString() || 0);
    renderFacets(); renderActive(); renderQuick(); paint(true);
    if (st.q && st.q === landQ && view.length && view.length <= 3) noteSeen(view[0]);
    if (document.body.classList.contains("side-open")) updApply();
  }
  async function render() {
    const listMode = st.view === "cat" || !!st.q;
    $("#home").hidden = st.view !== "home" || !!st.q;
    $("#catview").hidden = !listMode;
    $("#deals").hidden = st.view !== "deals" || !!st.q;
    $("#mine").hidden = st.view !== "mine" || !!st.q;
    const ttl = st.q ? `「${st.q}」` : st.view === "cat" ? (lang === "ja" ? CAT_JA[st.cat] : T().cats[st.cat]) : "";
    document.title = ttl ? `${ttl} ${lang === "ja" ? "買取価格比較｜買取プライス" : "– so sánh giá thu mua｜Kaitori Price"}` : (lang === "ja" ? TITLE0 : "Kaitori Price｜So sánh giá thu mua iPhone, máy game, thẻ Pokémon ở Nhật");
    chips(); renderRecent();
    // thống kê: 1 page_view mỗi lần đổi màn hình, gửi SAU khi URL đã cập nhật
    const pv = (url) => { history.replaceState(null, "", new URL(url, location.href).href); if (url !== lastPv) { lastPv = url; window.kpPage?.(); } };
    if (st.view === "deals" && !st.q) { pv("?v=deals"); return renderDeals(); }
    if (st.view === "mine" && !st.q) { pv("?v=mine"); return renderMine(); }
    if (st.view === "home" && !st.q) renderNews();
    if (!listMode) { pv("./"); return; }
    $("#hint").textContent = "…";
    if (st.q) {
      const q = st.q.toLowerCase().replace(/\s/g, "");
      // tìm trước trong mục lục nhỏ → chỉ tải những nhóm có kết quả
      sidx ||= await fetch("data/search.json" + bust).then((r) => r.json()).catch(() => null);
      const cats = sidx ? [...new Set(sidx.filter(([, n]) => n.toLowerCase().replace(/\s/g, "").includes(q)).map(([c]) => c))] : Object.keys(CATS);
      const use = (cats.length ? cats : Object.keys(CATS)).filter((c) => CATS[c]);
      // tìm trong ≤ 2 nhóm (vd link ?q=iPhone từ Facebook): tải luôn lịch sử để có biểu đồ + nhãn xu hướng
      const [all] = await Promise.all([Promise.all(use.map(loadCat)).then((a) => a.flat()), use.length <= 2 ? Promise.all(use.map(loadHist)) : null]);
      base = all.filter((i) => (i.name + i.key + (i._f.series || "")).toLowerCase().replace(/\s/g, "").includes(q));
    } else {
      base = (await Promise.all([loadCat(st.cat), loadHist(st.cat)]))[0];
    }
    refresh();
    pv(st.q ? "./?q=" + encodeURIComponent(st.q) : "?c=" + st.cat);
  }
  let lastPv = null, sidx = null, landQ = "";
  function clearFilters() { for (const k in st.f) st.f[k].clear(); st.price = 0; st.multi = st.gap = false; }

  // ================= Của tôi
  function updMineBadge(n) {
    const total = Object.keys(mine.watch).length + Object.keys(mine.stock).length;
    document.querySelectorAll(".mine-n").forEach((b) => { b.textContent = n ? n : ""; b.hidden = !n; });
    document.querySelectorAll("[data-v=mine]").forEach((b) => b.classList.toggle("has", total > 0));
  }
  async function renderNews() {
    // trang chủ: "Thay đổi từ lần trước bạn vào" cho các món đang theo dõi
    if (!Object.keys(mine.watch).length) { $("#news").innerHTML = ""; updMineBadge(0); return; }
    const m = await mineItems(), ch = changedWatch(m), t = T();
    updMineBadge(ch.length);
    if (!ch.length) { $("#news").innerHTML = ""; return; }
    const li = ch.slice(0, 4).map(({ w, it }) => { const d = it.best - w.seen;
      return `<li><span>${esc(it.name)}</span><b class="${d > 0 ? "up" : "dn"}">${d > 0 ? "▲" : "▼"}${Math.abs(d).toLocaleString()}円</b></li>`; }).join("");
    $("#news").innerHTML = `<button class="news" data-v="mine"><div class="news-t">🔔 ${t.newsTitle(ch.length)}</div><ul>${li}</ul><span class="news-go">${t.newsGo} →</span></button>`;
  }
  // kho hàng: giá ở các tiệm còn lại + lời/lỗ nếu bán ở đó (gập lại, bấm mới mở)
  function stockShops(it, s) {
    const sh = Object.entries(it.prices).filter(([, p]) => p && p.price).sort((a, b) => b[1].price - a[1].price);
    if (sh.length < 2) return "";
    const q = s.qty || 1;
    const rows = sh.map(([sid, p]) => {
      const pf = (p.price - s.buy) * q, lst = SH[sid]?.list;
      return `<a class="ssh" href="${esc(lst ? lstUrl(p, it) : p.url || "#")}" target="_blank" rel="noopener nofollow"><span>${esc(SH[sid]?.name || sid)}</span><span class="p">${yen(p.price)}</span><b class="${pf >= 0 ? "up" : "dn"}">${pf >= 0 ? "+" : ""}${pf.toLocaleString()}</b></a>`;
    }).join("");
    return `<details class="sshops"><summary>${T().allShops(sh.length)}</summary>${rows}</details>`;
  }
  async function renderMine() {
    const t = T(), m = await mineItems();
    const stock = Object.entries(mine.stock).map(([id, s]) => ({ id, s, it: m.get(id) }));
    let sum = 0, cnt = 0;
    const rows = stock.map(({ id, s, it }) => {
      if (!it) return `<div class="srow gone"><div class="sn">${esc(s.name)}</div><div class="sm">${t.noPrice}</div><button class="sdel" data-id="${esc(id)}" aria-label="delete">✕</button></div>`;
      const p = it.prices[it.best_shop] || {}, per = it.best - s.buy, tot = per * (s.qty || 1);
      sum += tot; cnt += s.qty || 1;
      const chg = it.chg ? `<span class="chg ${it.chg > 0 ? "up" : "dn"}">${it.chg > 0 ? "▲" : "▼"}${Math.abs(it.chg).toLocaleString()}</span>` : "";
      return `<div class="srow"><div class="sn">${esc(it.name)}</div>
        <div class="sm">${t.boughtAt} ${yen(s.buy)} · ${t.qty} <input class="sq-in" type="number" min="1" inputmode="numeric" value="${s.qty || 1}" data-id="${esc(id)}"></div>
        <a class="sbest" href="${esc(p.url || "#")}" target="_blank" rel="noopener nofollow"><span>${t.sellNow} <b>${SH[it.best_shop]?.name || ""}</b></span><span class="p">${yen(it.best)} ${chg}</span></a>
        <div class="spf ${tot >= 0 ? "up" : "dn"}">${t.profit} ${tot >= 0 ? "+" : ""}${tot.toLocaleString()}円${(s.qty || 1) > 1 ? ` <small>(${per >= 0 ? "+" : ""}${per.toLocaleString()}円 × ${s.qty})</small>` : ""}</div>
        ${stockShops(it, s)}
        <button class="sdel" data-id="${esc(id)}" aria-label="delete">✕</button></div>`;
    }).join("");
    const watch = Object.entries(mine.watch).map(([id, w]) => ({ id, w, it: m.get(id) }));
    const wcards = watch.filter((x) => x.it).map((x) => card(x.it)).join("");
    const gone = watch.filter((x) => !x.it).map((x) => `<li>${esc(x.w.name)} — ${t.noPrice} <button class="wdel" data-id="${esc(x.id)}">✕</button></li>`).join("");
    $("#mineBody").innerHTML = `
      <h2 class="sec">📦 ${t.stockTitle}</h2>
      ${stock.length ? `<div class="ssum"><span>${t.stockSum(cnt)}</span><b class="${sum >= 0 ? "up" : "dn"}">${sum >= 0 ? "+" : ""}${sum.toLocaleString()}円</b></div><div class="slist">${rows}</div>` : `<p class="mempty">${t.stockEmpty}</p>`}
      <h2 class="sec">♥ ${t.watchTitle}</h2>
      ${await pushBox(watch)}
      ${watch.length ? `<div class="list">${wcards}</div>${gone ? `<ul class="wgone">${gone}</ul>` : ""}` : `<p class="mempty">${t.watchEmpty}</p>`}`;
    // đã xem → cập nhật mốc "lần trước"
    for (const { id, it } of watch) if (it) mine.watch[id].seen = it.best;
    saveMine(); updMineBadge(0);
  }
  // ================= 🔔 cảnh báo giá qua Web Push (Worker kaitori-push lưu đăng ký, cron gửi khi giá đạt điều kiện)
  const PUSH_API = "https://kaitori-push.thanhduy8vn.workers.dev";
  const VAPID = "BLbRGmtO0hD8tyxin38tRvoaGuUznUEC-u1bv2FEY5lSzxNVXOB54kGykHf4-N-nOx-HB2LRYqj70LgvQwzaJvs";
  const vi = () => lang === "vi";
  const isIos = /iPhone|iPad|iPod/.test(navigator.userAgent);
  const standalone = matchMedia("(display-mode: standalone)").matches || navigator.standalone;
  const pushOk = "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
  const getSub = async () => { if (!pushOk) return null; try {
    const reg = await Promise.race([navigator.serviceWorker.ready, new Promise((r) => setTimeout(r, 1500))]);  // SW lỗi thì `ready` treo mãi
    return reg ? await reg.pushManager.getSubscription() : null; } catch { return null; } };
  async function syncPush(sub) {
    sub = sub || await getSub(); if (!sub) return;
    const items = Object.entries(mine.watch).map(([, w]) => ({ cat: w.cat, key: w.key, name: w.name, target: w.target || 0, last: w.seen }));
    await fetch(PUSH_API + "/sub", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sub: sub.toJSON(), items, lang }) }).catch(() => {});
  }
  const inApp = /FBAN|FBAV|FB_IAB|Instagram|Line\/|Zalo|Messenger/i.test(navigator.userAgent);
  let pushHelp = "";  // hướng dẫn hiện ngay trong khung 🔔 khi bật không được
  function helpText() {
    if (inApp) return vi() ? "Bạn đang mở web trong <b>Facebook / Zalo / LINE</b>, ở đây không bật được thông báo. Bấm <b>⋯</b> (góc trên) → <b>Mở bằng trình duyệt</b> (Safari / Chrome), rồi bật lại." : "Facebook・LINEなどのアプリ内ブラウザでは通知をオンにできません。<b>⋯</b> → <b>ブラウザで開く</b> を選んでください。";
    if (isIos && !standalone) return vi() ? "iPhone: bấm nút <b>Chia sẻ ⬆</b> → <b>Thêm vào Màn hình chính</b>, rồi <b>mở web từ biểu tượng mới</b> trên màn hình và bật lại." : "iPhone：<b>共有⬆</b> → <b>ホーム画面に追加</b> し、そのアイコンから開いてオンにしてください。";
    if (pushOk && Notification.permission === "denied") return vi() ? (isIos ? "Thông báo đang bị chặn: vào <b>Cài đặt → Thông báo → 買取プライス</b> → bật <b>Cho phép thông báo</b>." : "Thông báo đang bị chặn: bấm <b>biểu tượng ổ khoá / ⓘ</b> cạnh địa chỉ web → <b>Quyền / Thông báo</b> → <b>Cho phép</b>, rồi tải lại trang.") : "通知がブロックされています。アドレスバーの🔒 → 通知 → 許可 にしてから再読み込みしてください。";
    if (!pushOk) return vi() ? "Trình duyệt này chưa hỗ trợ thông báo. Hãy mở bằng Chrome (Android) hoặc Safari (iPhone)." : "このブラウザは通知に未対応です。";
    return vi() ? "Khi trình duyệt hỏi, hãy chọn <b>Cho phép</b>. Lỡ bấm Chặn thì bấm biểu tượng ổ khoá / ⓘ cạnh địa chỉ web để bật lại." : "ブラウザの確認で<b>許可</b>を選んでください。";
  }
  async function enablePush() {
    if (inApp || !pushOk || Notification.permission === "denied") { pushHelp = helpText(); return renderMine(); }
    if (await Notification.requestPermission() !== "granted") { pushHelp = helpText(); return renderMine(); }
    pushHelp = "";
    const key = Uint8Array.from(atob(VAPID.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0));
    const sub = await (await navigator.serviceWorker.ready).pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: key });
    await syncPush(sub);
    fetch(PUSH_API + "/test", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ endpoint: sub.endpoint }) }).catch(() => {});
    window.kpTrack?.("push_on", { n: Object.keys(mine.watch).length });
    renderMine();
  }
  async function disablePush() {
    const sub = await getSub();
    if (sub) { fetch(PUSH_API + "/unsub", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ endpoint: sub.endpoint }) }).catch(() => {}); await sub.unsubscribe().catch(() => {}); }
    renderMine();
  }
  async function pushBox(watch) {
    if (!watch.length) return "";
    const on = !!(await getSub()) && Notification.permission === "granted";
    const rows = watch.filter((x) => x.it).map(({ id, w, it }) => `<div class="arow"><span class="an">${esc(it.name)}<small>${vi() ? "Hiện" : "現在"} ${yen(it.best)}</small></span>
      <label>${vi() ? "Báo khi ≥" : "通知 ≥"} <input class="atg" type="number" inputmode="numeric" step="1000" placeholder="${vi() ? "mọi thay đổi ≥2%" : "2%以上の変動"}" value="${w.target || ""}" data-id="${esc(id)}">円</label></div>`).join("");
    const iosHint = pushHelp ? `<p class="phelp">⚠️ ${pushHelp}</p>`
      : (inApp || (isIos && !standalone)) && !on ? `<p class="small">📱 ${helpText()}</p>` : "";
    return `<div class="pbox ${on ? "on" : ""}"><div class="ph"><b>🔔 ${vi() ? "Báo về điện thoại khi giá đổi" : "価格変動をスマホに通知"}</b>
      ${on ? `<button class="poff" type="button">${vi() ? "Tắt" : "オフ"}</button>` : `<button class="pon" type="button">${vi() ? "Bật thông báo" : "通知をオン"}</button>`}</div>
      <p class="small">${on ? (vi() ? "Đang bật. Web kiểm tra sau mỗi lần cập nhật giá (khoảng 30 phút/lần). Không cần đăng nhập." : "オン中。価格更新（約30分ごと）のたびにチェックします。") : (vi() ? "Không cần mở web: giá đạt mức bạn đặt, hoặc đổi từ 2% trở lên, là điện thoại báo ngay." : "サイトを開かなくても、目標価格到達や2%以上の変動を通知します。")}</p>
      ${iosHint}${on ? `<div class="alist">${rows}</div>` : ""}</div>`;
  }
  // 🔔 trên thẻ: đặt mức giá muốn bán ngay tại chỗ → tự theo dõi (♥) + bật thông báo đẩy
  function bellPanel(btn) {
    const el = btn.closest(".card"), id = btn.dataset.id, it = REG.get(id); if (!el || !it) return;
    const old = el.querySelector(".apanel"); if (old) return old.remove();
    const t = T(), w = mine.watch[id], def = w?.target || Math.ceil((it.best + 3000) / 1000) * 1000;
    (el.querySelector(".bh-pills") || el.querySelector(".bhero")).insertAdjacentHTML("afterend", `<div class="apanel"><label>${t.bellAsk} <input class="atg2" type="number" inputmode="numeric" step="1000" value="${def}">円</label>`
      + `<button class="aok" type="button" data-id="${esc(id)}">${t.bellOk}</button>${w?.target ? `<button class="aoff" type="button" data-id="${esc(id)}">${t.bellOff}</button>` : ""}<p class="ahelp" hidden></p></div>`);
    el.querySelector(".atg2").focus();
  }
  async function bellSave(btn, off) {
    const id = btn.dataset.id, it = REG.get(id), el = btn.closest(".card"), box = btn.closest(".apanel"); if (!it || !box) return;
    const t = T(), v = off ? 0 : Math.max(0, Math.round(+box.querySelector(".atg2").value || 0));
    if (!off && !v) return box.querySelector(".atg2").focus();
    if (!mine.watch[id]) mine.watch[id] = { cat: it.cat, key: it.key, name: it.name, seen: it.best, at: it.best };
    mine.watch[id].target = v; saveMine(); updMineBadge(0);
    el.querySelectorAll(".fav").forEach((b) => { b.classList.add("on"); b.textContent = "♥"; });
    el.querySelectorAll(".bell").forEach((b) => { b.classList.toggle("on", !!v); b.textContent = v ? "🔔 " + yen(v) : t.bellBtn; });
    window.kpTrack?.(off ? "bell_off" : "bell_set", { item: it.name, value: v });
    if (off) { if (pushOk) syncPush(); box.remove(); return toast(t.bellRemoved); }
    let on = !!(await getSub()) && Notification.permission === "granted";
    if (!on && !inApp && pushOk && Notification.permission !== "denied" && !(isIos && !standalone)) { await enablePush().catch(() => {}); on = !!(await getSub()) && Notification.permission === "granted"; }
    if (on) { await syncPush(); box.remove(); return toast(t.bellDone(yen(v))); }
    // chưa bật được (trình duyệt trong Facebook/Zalo, iPhone chưa thêm vào màn hình chính…): mức giá vẫn được lưu
    const h = box.querySelector(".ahelp"); h.hidden = false; h.innerHTML = `✅ ${esc(t.bellSaved(yen(v)))}<br>⚠️ ${helpText()}`;
  }
  function toggleWatch(id) {
    const it = REG.get(id);
    if (mine.watch[id]) delete mine.watch[id];
    else if (it) mine.watch[id] = { cat: it.cat, key: it.key, name: it.name, seen: it.best, at: it.best };
    saveMine();
    document.querySelectorAll(`.fav[data-id="${CSS.escape(id)}"]`).forEach((b) => { const on = !!mine.watch[id]; b.classList.toggle("on", on); b.textContent = on ? "♥" : "♡"; });
    document.querySelectorAll(`.bell[data-id="${CSS.escape(id)}"]`).forEach((b) => { const v = mine.watch[id]?.target; b.classList.toggle("on", !!v); b.textContent = v ? "🔔 " + yen(v) : T().bellBtn; });
    toast(mine.watch[id] ? T().watchAdded : T().watchRemoved);
    window.kpTrack?.(mine.watch[id] ? "watch_add" : "watch_remove", { item: it?.name || id });
    updMineBadge(0);
    if (pushOk) syncPush();
  }
  function addStock(id, btn) {
    const it = REG.get(id); if (!it) return;
    if (mine.stock[id]) { st.view = "mine"; return render(); }
    const inp = btn.closest(".card")?.querySelector(".calc input");
    const buy = +(inp?.value || 0);
    if (!buy) { inp?.focus(); return toast(T().needBuy); }
    mine.stock[id] = { cat: it.cat, key: it.key, name: it.name, buy, qty: 1, d: idx.updated.slice(0, 10) };
    saveMine();
    btn.classList.add("on"); btn.textContent = T().inStock;
    toast(T().stockAdded);
    window.kpTrack?.("stock_add", { item: it.name, value: buy, currency: "JPY" });
    updMineBadge(0);
  }
  document.addEventListener("click", (e) => {
    const ri = e.target.closest(".rec-i"); if (ri) { window.kpTrack?.("recent_click", { item: ri.dataset.q }); st.q = ri.dataset.q; $("#q").value = st.q; window.scrollTo({ top: 0 }); return render(); }
    const so = e.target.closest("a.sh, a.sbest"); if (so) { const c = so.closest(".card"); noteSeen(REG.get(c?.querySelector("[data-id]")?.dataset.id)); }
    const sh = e.target.closest(".shr"); if (sh) { e.preventDefault(); return shareItem(REG.get(sh.dataset.id)); }
    const ch = e.target.closest(".crow-h"); if (ch) {
      const w = ch.closest(".crow"), it = REG.get(ch.dataset.id), body = w.querySelector(".crow-b"); if (!it) return;
      const open = !w.classList.contains("open"); w.classList.toggle("open", open); ch.setAttribute("aria-expanded", open);
      body.innerHTML = open ? card(it) : "";
      if (open) { window.kpTrack?.("row_open", { item: it.name }); noteSeen(it); }
      return;
    }
    const bl = e.target.closest(".bell"); if (bl) { e.preventDefault(); return bellPanel(bl); }
    const ok = e.target.closest(".aok, .aoff"); if (ok) { e.preventDefault(); return bellSave(ok, ok.classList.contains("aoff")); }
    const cp = e.target.closest(".cpick button"); if (cp) {
      const id = cp.dataset.id, it = REG.get(id), el = cp.closest(".card"); if (!it || !el) return;
      const v = CSEL.get(id) === cp.dataset.col ? "" : cp.dataset.col;  // bấm lại màu đang chọn = bỏ chọn
      v ? CSEL.set(id, v) : CSEL.delete(id);
      el.outerHTML = card(it);
      if (v) window.kpTrack?.("color_pick", { item: it.name, color: v });
      noteSeen(it);
      return;
    }
    const sm = e.target.closest(".shmore"); if (sm) { const box = sm.previousElementSibling; box.classList.toggle("clip"); sm.textContent = box.classList.contains("clip") ? sm.textContent.replace("▴", "▾") : sm.textContent.replace("▾", "▴"); return; }
    const f = e.target.closest(".fav"); if (f) { e.preventDefault(); return toggleWatch(f.dataset.id); }
    const k = e.target.closest(".stk"); if (k) { e.preventDefault(); return addStock(k.dataset.id, k); }
    const d = e.target.closest(".sdel"); if (d) { delete mine.stock[d.dataset.id]; saveMine(); return renderMine(); }
    const w = e.target.closest(".wdel"); if (w) { delete mine.watch[w.dataset.id]; saveMine(); if (pushOk) syncPush(); return renderMine(); }
    if (e.target.closest(".pon")) return enablePush().catch(() => toast(vi() ? "Chưa bật được thông báo, thử lại sau" : "通知をオンにできませんでした"));
    if (e.target.closest(".poff")) return disablePush();
    const n = e.target.closest(".news,[data-v=mine]");
    if (n && !n.closest("#chips,#mcat")) { st.view = "mine"; $("#q").value = ""; st.q = ""; window.scrollTo({ top: 0 }); return render(); }
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Enter" && e.target.closest(".atg2")) { e.preventDefault(); e.target.closest(".apanel").querySelector(".aok").click(); } });
  document.addEventListener("change", (e) => {
    const a = e.target.closest(".atg");
    if (a) { const w = mine.watch[a.dataset.id]; if (!w) return; w.target = Math.max(0, Math.round(+a.value || 0)); saveMine(); syncPush();
      return toast(w.target ? (vi() ? `🔔 Sẽ báo khi giá ≥ ${yen(w.target)}` : `🔔 ${yen(w.target)}以上で通知`) : (vi() ? "🔔 Sẽ báo khi giá đổi ≥2%" : "🔔 2%以上の変動で通知")); }
    const q = e.target.closest(".sq-in"); if (!q) return;
    const s = mine.stock[q.dataset.id]; if (!s) return;
    s.qty = Math.max(1, Math.round(+q.value || 1)); saveMine(); renderMine();
  });

  // ================= deals (PR)
  let deals = null, dTab = "", dQ = "";
  const dSeen = new Set(); // pixel hiển thị chỉ bắn 1 lần / mục, không bắn lại mỗi lần lọc
  const dTxt = (o) => (o && (o[lang] || o.vi)) || "";
  const dNorm = (x) => x.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d");
  async function renderDeals() {
    deals ||= promos;
    const vi = lang === "vi", groups = deals.groups.map((g) => ({ ...g, items: g.items.filter((x) => x.url) })).filter((g) => g.items.length);
    const tabs = [...new Set(groups.map((g) => dTxt(g.tab) || dTxt(g.title)))];
    if (dTab && !tabs.includes(dTab)) dTab = "";
    const chip = (v, label) => `<button class="dtab ${dTab === v ? "on" : ""}" data-tab="${esc(v)}">${esc(label)}</button>`;
    const tabHtml = chip("", vi ? "Tất cả" : "すべて") + tabs.map((t) => chip(t, t)).join("");
    const q = dNorm(dQ.trim());
    const html = groups.map((g) => {
      if (dTab && (dTxt(g.tab) || dTxt(g.title)) !== dTab) return "";
      const items = q ? g.items.filter((x) => dNorm([x.name, x.desc?.vi, x.desc?.ja, x.badge?.vi, x.badge?.ja, g.title?.vi, g.title?.ja].join(" ")).includes(q)) : g.items;
      if (!items.length) return "";
      items.forEach((x) => x.px && !dSeen.has(x.px) && (dSeen.add(x.px), pixel(x.px)));
      return `<h3 class="dg">${esc(dTxt(g.title))}</h3><div class="dlist">` + items.map((x) => `
        <a class="deal-card" href="${esc(x.url)}" target="_blank" rel="sponsored noopener">
          <span class="pr">${x.affiliate ? "PR" : "LINK"}</span>
          ${x.badge ? `<span class="badge">${esc(dTxt(x.badge))}</span>` : ""}
          <b>${esc((lang === "ja" && x.name_ja) || x.name)}</b><span>${esc(dTxt(x.desc))}</span>
          ${Object.entries(SH).some(([sid, s]) => s.name === x.name && REF[sid]) ? `<span class="ref">${esc(refText(Object.keys(SH).find((sid) => SH[sid].name === x.name)))}</span>` : ""}
          <span class="go">${vi ? "Xem chi tiết →" : "詳しく見る →"}</span>
        </a>`).join("") + "</div>";
    }).join("");
    const empty = `<p class="mempty">${vi ? "Không có ưu đãi phù hợp." : "該当するお得情報がありません。"}</p>`;
    // ô tìm giữ nguyên (không vẽ lại) để bàn phím điện thoại không bị đóng khi gõ
    if (!$("#dq") || $("#dq").dataset.lang !== lang) $("#dealList").innerHTML = `<div class="dbar"><input id="dq" type="search" data-lang="${lang}" value="${esc(dQ)}" placeholder="${vi ? "🔍 Tìm ưu đãi (vd: iPhone, máy ảnh, SIM…)" : "🔍 お得情報を検索（例：iPhone、カメラ、SIM）"}"><div class="dtabs"></div></div><div id="dealRes"></div>`;
    $("#dealList .dtabs").innerHTML = tabHtml;
    $("#dealRes").innerHTML = html || empty;
    history.replaceState(null, "", new URL("?v=deals", location.href).href);
  }

  $("#dealList").addEventListener("click", (e) => {
    const b = e.target.closest(".dtab"); if (!b) return;
    dTab = b.dataset.tab; renderDeals();
    window.kpTrack?.("deal_filter", { tab: dTab || "all" });
  });
  $("#dealList").addEventListener("input", (e) => { if (e.target.id === "dq") { dQ = e.target.value; renderDeals(); } });

  // ================= events
  const cgOpen = (o) => document.body.classList.toggle("cg-open", o);
  $("#mcPick").addEventListener("click", () => cgOpen(true));
  $("#cgClose").addEventListener("click", () => cgOpen(false));
  const pickNav = (e) => {
    const b = e.target.closest("button[data-c],button[data-v]"); if (!b) return;
    cgOpen(false);
    $("#q").value = ""; st.q = ""; clearFilters();
    if (b.dataset.c) { st.view = "cat"; st.cat = b.dataset.c; } else st.view = b.dataset.v;
    const anchor = $("main").getBoundingClientRect().top + window.scrollY - 52;
    if (window.scrollY > anchor + 4) window.scrollTo({ top: anchor, behavior: "smooth" });
    render();
  };
  // ☰ menu bên (điện thoại): danh mục + mục phụ (hướng dẫn, nhóm FB, ngôn ngữ)
  const drOpen = (o) => { document.body.classList.toggle("dr-open", o); if (o) renderDrawer(); };
  function renderDrawer() {
    const t = T(), on = (c) => (c ? " on" : "");
    const cats = Object.keys(CATS).map((c) => `<button data-c="${c}" class="${on(st.view === "cat" && st.cat === c && !st.q)}">${ICON[c] || ""} ${esc(t.cats[c] || c)}<small>${(CATS[c].count || 0).toLocaleString()}</small></button>`).join("");
    $("#drNav").innerHTML = `
      <button data-v="home" class="${on(st.view === "home" && !st.q)}">🏠 ${t.drHome}</button>
      <button data-v="mine" class="${on(st.view === "mine")}">♥ ${t.drMine}</button>
      <button data-v="deals" class="${on(st.view === "deals")}">🎁 ${t.drDeals}</button>
      <a href="${lang === "vi" ? "/guide/vi/" : "/guide/"}">📚 ${t.guideBtn}</a>
      ${lang === "vi" ? `<a href="https://www.facebook.com/groups/1118827834446963" target="_blank" rel="noopener">👥 ${t.drFb}</a>` : ""}
      <h4>${t.drCats}</h4>${cats}
      <button class="dr-lang" data-lang="1">🌐 ${t.drLang}</button>`;
  }
  $("#hdMenu").addEventListener("click", () => drOpen(true));
  $("#drClose").addEventListener("click", () => drOpen(false));
  $("#drNav").addEventListener("click", (e) => {
    if (e.target.closest("[data-lang]")) { drOpen(false); return $("#lang").click(); }
    if (e.target.closest("a")) return drOpen(false);
    if (e.target.closest("button[data-c],button[data-v]")) { drOpen(false); pickNav(e); }
  });
  $("#mcat").addEventListener("click", pickNav);
  $("#hdMine").addEventListener("click", pickNav);
  $("#cgrid").addEventListener("click", pickNav);
  $("#hcats").addEventListener("click", pickNav);
  $("#chips").addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    $("#q").value = ""; st.q = ""; clearFilters();
    if (b.dataset.c) { st.view = "cat"; st.cat = b.dataset.c; } else st.view = b.dataset.v;
    b.scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" });  // chip được chọn ra giữa, không nhảy dọc
    const anchor = $("main").getBoundingClientRect().top + window.scrollY - 52;  // đầu vùng nội dung (dưới header)
    if (window.scrollY > anchor + 4) window.scrollTo({ top: anchor, behavior: "smooth" });  // đang ở sâu → về đầu danh sách mới
    render();
  });
  $("#facets").addEventListener("change", (e) => {
    const el = e.target;
    if (el.dataset.k) { const s = st.f[el.dataset.k]; el.checked ? s.add(el.value) : s.delete(el.value); if (el.dataset.k === "brand" && !el.checked) st.f.series.clear(); }
    else if (el.name === "pr") st.price = +el.dataset.p;
    else if (el.id === "multi") st.multi = el.checked;
    else if (el.id === "gap") st.gap = el.checked;
    refresh();
  });
  $("#facets").addEventListener("click", (e) => {
    const b = e.target.closest(".fmore"); if (!b) return;
    st._open = { ...(st._open || {}), [b.dataset.k]: !(st._open || {})[b.dataset.k] }; renderFacets();
  });
  $("#quick").addEventListener("click", (e) => {
    const b = e.target.closest(".qc"); if (!b) return;
    if (b.dataset.open) return openSide(true, b.dataset.open === "all" ? "" : b.dataset.open);
    const k = b.dataset.k, add = !!b.dataset.add;
    if (k === "multi") st.multi = add; else if (k === "gap") st.gap = add; else if (k === "price") st.price = 0;
    else { add ? st.f[k].add(b.dataset.v) : st.f[k].delete(b.dataset.v); if (k === "brand" && !add) st.f.series.clear(); }
    refresh();
    $("#quick").scrollLeft = 0;
  });
  $("#drill").addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    const k = b.dataset.k, order = ["brand", "series", "cap"];
    if (b.classList.contains("dc")) order.slice(order.indexOf(k)).forEach((x) => st.f[x].clear());  // bỏ bậc này + các bậc sau
    else { st.f[k] = new Set([b.dataset.v]); window.kpTrack?.("drill", { step: k, value: b.dataset.v }); }
    refresh();
  });
  $("#active").addEventListener("click", (e) => {
    const b = e.target.closest(".ac"); if (!b) return;
    const k = b.dataset.k;
    if (k === "all") clearFilters(); else if (k === "price") st.price = 0; else if (k === "multi") st.multi = false; else if (k === "gap") st.gap = false;
    else st.f[k].delete(b.dataset.v);
    refresh();
  });
  $("#reset").addEventListener("click", () => { clearFilters(); refresh(); });
  $("#sort").addEventListener("change", (e) => { st.sort = e.target.value; refresh(); });
  $("#vtog").addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    st.layout = b.dataset.v; localStorage.setItem("layout2", st.layout);
    document.querySelectorAll("#vtog button").forEach((x) => x.classList.toggle("on", x === b)); paint(true);
  });
  // focus: chỉ hiện 1 nhóm bộ lọc (hãng / dòng máy / dung lượng / giá); rỗng = tất cả
  const openSide = (o, focus = "") => {
    document.body.classList.toggle("side-open", o);
    const side = $("#side");
    if (o && focus) side.dataset.focus = focus; else delete side.dataset.focus;
    if (o) { side.scrollTop = 0; updApply(); }
  };
  const updApply = () => { $("#apply").textContent = T().applyN(view.length); };
  $("#fbtn").addEventListener("click", () => openSide(true));
  $("#sideClose").addEventListener("click", () => openSide(false));
  $("#apply").addEventListener("click", () => {
    openSide(false);
    const r = $("#catview").getBoundingClientRect().top;
    window.scrollTo({ top: window.scrollY + r - 60, behavior: "smooth" });
  });
  // nút ↑ về đầu trang
  const toTop = document.createElement("button");
  toTop.id = "toTop"; toTop.setAttribute("aria-label", "top"); toTop.textContent = "↑";
  document.body.appendChild(toTop);
  toTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
  window.addEventListener("scroll", () => {
    toTop.classList.toggle("show", window.scrollY > 600);
    document.body.classList.toggle("scrolled", window.scrollY > 80);
    $("#chips").classList.toggle("stuck", $("#chips").getBoundingClientRect().top <= 53 && window.scrollY > 60);
  }, { passive: true });
  $("#scrim").addEventListener("click", () => { openSide(false); cgOpen(false); drOpen(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") { openSide(false); cgOpen(false); drOpen(false); } });
  let qT, qL; $("#q").addEventListener("input", (e) => { clearTimeout(qT); clearTimeout(qL); qT = setTimeout(() => { st.q = e.target.value.trim(); clearFilters(); render(); }, 250);
    qL = setTimeout(() => { const v = e.target.value.trim(); if (v.length >= 2) window.kpTrack?.($("#empty").hidden ? "search" : "search_none", { search_term: v.slice(0, 80) }); }, 1500); });
  $("#more").addEventListener("click", () => paint(false));
  // bảng: bấm "Xem cả N tiệm" để mở danh sách giá tất cả tiệm của món đó
  $("#list").addEventListener("click", (e) => {
    const b = e.target.closest(".tmore"); if (!b) return;
    b.parentElement.classList.toggle("open");
  });
  $("#lang").addEventListener("click", () => { lang = lang === "vi" ? "ja" : "vi"; localStorage.setItem("lang", lang); applyLang(); render(); $("#top").innerHTML = top.slice(0, 18).map(card).join(""); });
  document.body.addEventListener("click", (e) => {
    const a = e.target.closest("a.lst"); if (!a) return;
    navigator.clipboard?.writeText(a.dataset.copy).catch(() => {});
    toast(T().copied);
  });
  // ================= thêm vào màn hình chính (PWA): hiện từ lần vào thứ 2, tắt rồi thì 30 ngày sau mới hỏi lại
  function installPrompt() {
    if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
    const standalone = matchMedia("(display-mode: standalone)").matches || navigator.standalone;
    const visits = +(localStorage.getItem("kp_visits") || 0) + 1; localStorage.setItem("kp_visits", visits);
    const off = +(localStorage.getItem("kp_a2hs_off") || 0);
    if (standalone || visits < 2 || Date.now() - off < 30 * 864e5 || innerWidth > 900) return;
    const box = $("#a2hs"), t = T();
    const close = () => { box.hidden = true; localStorage.setItem("kp_a2hs_off", Date.now()); };
    const ios = /iphone|ipad|ipod/i.test(navigator.userAgent) && !/crios|fxios/i.test(navigator.userAgent);
    let deferred = null;
    const show = (html) => { box.innerHTML = `<img src="icon-192.png" alt="">${html}<button class="a2hs-x" aria-label="close">✕</button>`; box.hidden = false; box.querySelector(".a2hs-x").onclick = close; };
    if (ios) setTimeout(() => { show(`<span>${t.a2hsIos}</span>`); window.kpTrack?.("a2hs_prompt", { platform: "ios" }); }, 4000);
    addEventListener("beforeinstallprompt", (e) => {
      e.preventDefault(); deferred = e;
      show(`<span>${t.a2hsText}</span><button class="a2hs-b">${t.a2hsBtn}</button>`);
      box.querySelector(".a2hs-b").onclick = async () => { deferred.prompt(); const c = await deferred.userChoice.catch(() => ({})); window.kpTrack?.("a2hs_" + (c.outcome || "unknown"), { platform: "android" }); close(); };
    });
  }
  // chia sẻ 1 sản phẩm: link mở đúng món (theo ngôn ngữ đang dùng) + tên, giá cao nhất, tiệm
  async function shareItem(it) {
    if (!it) return;
    const t = T(), url = location.origin + (lang === "vi" ? "/vi/" : "/") + "?q=" + encodeURIComponent(it.name);
    const text = t.shareText(it.name, yen(it.best), SH[it.best_shop]?.name || "");
    window.kpTrack?.("share", { item: it.name });
    if (navigator.share) { try { await navigator.share({ title: it.name, text, url }); return; } catch (err) { if (err && err.name === "AbortError") return; } }
    try { await navigator.clipboard.writeText(text + "\n" + url); toast(t.linkCopied); } catch { toast(url); }
  }
  function toast(msg) {
    let el = $("#toast"); if (!el) { el = document.createElement("div"); el.id = "toast"; document.body.appendChild(el); }
    el.textContent = msg; el.classList.add("show"); clearTimeout(el._t); el._t = setTimeout(() => el.classList.remove("show"), 3500);
  }
  document.body.addEventListener("input", (e) => {
    if (!e.target.matches(".calc input")) return;
    const v = parseInt(e.target.value, 10), best = +e.target.dataset.best, out = e.target.parentElement.querySelector(".pf");
    if (!v) { out.textContent = "—"; out.style.color = ""; return; }
    const p = best - v; out.textContent = (p >= 0 ? "+" : "") + p.toLocaleString() + "円"; out.style.color = p >= 0 ? "#16a34a" : "#dc2626";
  });

  const TITLE0 = location.pathname.startsWith("/vi") ? "買取プライス｜iPhone・ゲーム機・ポケカの買取価格を毎時比較" : document.title;
  const CAT_JA = { phone: "スマホ・iPhone", tablet: "タブレット・iPad", game: "ゲーム機", card: "トレカ・ポケカBOX", pc: "パソコン", camera: "カメラ・レンズ", audio: "オーディオ", appliance: "家電", watch: "時計", hobby: "ホビー・フィギュア", other: "その他" };
  // ================= start
  const top = FACETS.enrich(await fetch("data/top.json" + bust).then((r) => r.json()).catch(() => []));
  const sp = new URLSearchParams(location.search);
  if (sp.get("c") && CATS[sp.get("c")]) { st.view = "cat"; st.cat = sp.get("c"); }
  if (sp.get("v") === "deals") st.view = "deals";
  if (sp.get("v") === "mine") st.view = "mine";
  if (sp.get("q")) { st.q = sp.get("q").trim().slice(0, 80); $("#q").value = st.q; }
  landQ = st.q;
  applyLang();
  installPrompt();
  $("#top").innerHTML = top.slice(0, 18).map(card).join("");
  // 🔥 thu mạnh + 📈📉 tăng/giảm mạnh (trang chủ)
  const [boost, movers] = await Promise.all([
    fetch("data/boost.json" + bust).then((r) => r.json()).catch(() => []),
    fetch("data/movers.json" + bust).then((r) => r.json()).catch(() => ({})),
  ]);
  const homeExtra = () => {
    FACETS.enrich(boost);
    $("#boostH").hidden = !boost.length;
    $("#boost").innerHTML = boost.slice(0, 6).map(card).join("");
    $("#movers").innerHTML = moversHtml(movers);
  };
  homeExtra();
  $("#lang").addEventListener("click", homeExtra);
  $("#movers").addEventListener("click", (e) => { const b = e.target.closest(".mv-i"); if (b) { $("#q").value = b.dataset.q; $("#q").dispatchEvent(new Event("input", { bubbles: true })); } });
  render();
  initRecent();
})();
