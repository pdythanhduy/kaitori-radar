(async function () {
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const yen = (n) => n.toLocaleString("ja-JP") + "円";
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
    $("#upd").textContent = `${T().upd} ${idx.updated}`;
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
    $("#cgrid").innerHTML = order.map(([c, v]) =>
      `<button data-c="${c}" class="${st.view === "cat" && st.cat === c && !st.q ? "on" : ""}"><span class="ci">${ICON[c] || "📦"}</span><span class="cn">${short[c] || T().cats[c] || v.label}</span><span class="cc">${v.count.toLocaleString()}</span></button>`).join("");
  }

  // ================= card / table
  function spark(it) {
    const s = ((hcache[it.cat] || {})[it.key] || []).slice(-30);
    if (s.length < 2) return "";
    const v = s.map((p) => p[1]), mn = Math.min(...v), mx = Math.max(...v), r = mx - mn || 1;
    const pts = v.map((y, i) => `${((i / (v.length - 1)) * 80 + 2).toFixed(1)},${(30 - ((y - mn) / r) * 26).toFixed(1)}`).join(" ");
    return `<svg class="spark" width="84" height="32" viewBox="0 0 84 32"><polyline fill="none" stroke="${v[v.length - 1] >= v[0] ? "#16a34a" : "#dc2626"}" stroke-width="2" points="${pts}"/></svg>`;
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
    return shops.map(([sid, p], i) => {
      const extra = p.min && p.min !== p.price ? `<span class="nt">${t.colorFrom} ${yen(p.min)}</span>` : p.note ? `<span class="nt">${esc(p.note.slice(0, 16))}</span>` : "";
      const lst = SH[sid]?.list, nm = SH[sid]?.name || sid;
      // cả dòng là 1 link sang trang tiệm (có ↗ ở cuối để người dùng biết bấm được)
      return `<a class="sh ${i === 0 && shops.length > 1 ? "top" : ""} ${lst ? "lst" : ""}" href="${esc(lst ? lstUrl(p, it) : p.url)}" target="_blank" rel="noopener nofollow"${lst ? ` data-copy="${esc(p.n || it.name)}" title="${esc(t.listTip)}"` : ""}>`
        + `<span class="sn"><b>${nm}</b>${lst ? `<i class="sq">${t.searchTag}</i>` : ""}${extra}</span><span class="p">${yen(p.price)}</span><span class="go" aria-hidden="true">↗</span></a>`;
    }).join("");
  }
  // 🍎 so với giá niêm yết Apple (chỉ đời Apple đang bán: iPhone 18 / Duo)
  function msrpLine(it) {
    if (!it.msrp || !/^iPhone (18|Duo)\b/.test(it.key)) return "";
    const d = it.best - it.msrp, cls = d >= 0 ? "up" : "dn";
    return `<div class="msrp ${cls}" title="${esc(T().msrpTip)}">${T().msrpLine(yen(it.msrp), `<b>${d >= 0 ? "+" : "−"}${yen(Math.abs(d))}</b>`)}</div>`;
  }
  function boostTag(it) {
    const b = Object.entries(it.prices).filter(([, p]) => p.b).map(([s]) => SH[s]?.name || s);
    return b.length ? `<div class="boost">${esc(T().boostTag(b.join("・")))}</div>` : "";
  }
  function moversHtml(mv) {
    const t = T(), row = (i) => `<button class="mv-i" data-q="${esc(i.name)}"><span>${esc(i.name)}</span><b class="${i.mv > 0 ? "up" : "dn"}">${i.mv > 0 ? "▲" : "▼"}${Math.abs(i.mv).toLocaleString()}円</b><small>${yen(i.best)}</small></button>`;
    const col = (title, arr) => arr.length ? `<div class="mv-c"><h3>${title}</h3>${arr.slice(0, 5).map(row).join("")}</div>` : "";
    const h = col(t.upTitle, mv.up || []) + col(t.downTitle, mv.down || []);
    return h ? `<div class="movers">${h}</div>` : "";
  }
  function card(it) {
    const t = T();
    const shops = Object.entries(it.prices).sort((a, b) => b[1].price - a[1].price);
    const chg = it.chg ? `<span class="chg ${it.chg > 0 ? "up" : "dn"}">${it.chg > 0 ? "▲" : "▼"}${Math.abs(it.chg).toLocaleString()}</span>` : "";
    const rows = shopRows(it, shops);
    const diff = it.n_shops > 1 && it.spread > 0 ? `<div class="diff">${t.diff(yen(it.spread))}</div>` : "";
    const br = it._f?.brand !== "Khác" ? it._f?.brand : "";
    const tag = [br && !(it._f?.series || "").startsWith(br.split(" ")[0]) ? br : "", it._f?.series, it._f?.cap].filter(Boolean).join(" · ");
    const id = idOf(it); REG.set(id, it);
    const fav = mine.watch[id] ? "on" : "";
    return `<article class="card">
      <div class="c-top"><div><div class="c-name">${esc(it.name)}</div><div class="c-sub">${ICON[it.cat] || ""} ${esc(tag || t.cats[it.cat] || "")}・${t.shopsN(it.n_shops)}</div></div>${spark(it)}<div class="c-act"><button class="shr" data-id="${esc(id)}" aria-label="${esc(t.share)}" title="${esc(t.share)}"><svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7"/><path d="M12 3v12"/><path d="m7 8 5-5 5 5"/></svg></button><button class="fav ${fav}" data-id="${esc(id)}" aria-label="${esc(t.watch)}" title="${esc(t.watch)}">${fav ? "♥" : "♡"}</button></div></div>
      <div class="best"><span class="best-p">${yen(it.best)}</span><span class="best-s ${it.n_shops > 1 ? "" : "one"}">${it.n_shops > 1 ? t.best + "：" : ""}${SH[it.best_shop]?.name || ""}</span>${chg}</div>
      ${boostTag(it)}${msrpLine(it)}${diff}<div class="shops">${rows}</div>
      ${affBox(it.cat, it.key)}${buyBox(it)}
      <div class="calc-row"><label class="calc">${t.calc} <input type="number" inputmode="numeric" placeholder="${Math.round(it.best * 0.9).toLocaleString()}" data-best="${it.best}"> 円 → ${t.profit} <b class="pf">—</b></label><button class="stk ${mine.stock[id] ? "on" : ""}" data-id="${esc(id)}">${mine.stock[id] ? t.inStock : t.addStock}</button></div>
    </article>`;
  }
  function tableHead() {
    const t = T();
    return `<div class="tbl"><div class="tr th"><span>${t.colName}</span><span>${t.colBest}</span><span>${t.colShop}</span><span>${t.col2nd}</span><span>${t.colGap}</span></div>`;
  }
  function trow(it) {
    const shops = Object.entries(it.prices).sort((a, b) => b[1].price - a[1].price);
    const [s1, p1] = shops[0], s2 = shops[1];
    const chg = it.chg ? `<i class="${it.chg > 0 ? "up" : "dn"}">${it.chg > 0 ? "▲" : "▼"}${Math.abs(it.chg).toLocaleString()}</i>` : "";
    return `<div class="tr"><span class="tn">${esc(it.name)}<small>${esc([it._f?.series, it._f?.cap].filter(Boolean).join(" · "))} · ${T().shopsN(it.n_shops)}</small></span>
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
  function renderFacets() {
    const t = T();
    let h = "";
    if (st.q) h += facetBlock("cat", t.fCat, counts("cat", (i) => i.cat), { labels: (c) => `${ICON[c] || ""} ${t.cats[c] || c}` });
    h += facetBlock("brand", t.fBrand, counts("brand", (i) => i._f.brand), { labels: (v) => (v === "Khác" ? t.otherB : v), sort: (a, b) => (a === "Khác") - (b === "Khác") || (cnt.brand.get(b) || 0) - (cnt.brand.get(a) || 0) });
    const sc = counts("series", (i) => i._f.series);
    h += facetBlock("series", t.fSeries, sc, { sort: st.f.brand.size ? FACETS.seriesSort : (a, b) => (sc.get(b) || 0) - (sc.get(a) || 0), limit: 12 });
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
    const lab = (k, set) => { const v = [...set]; return v.length ? (v.length === 1 ? (k === "brand" && v[0] === "Khác" ? t.otherB : v[0]) : `${v[0]} +${v.length - 1}`) : ""; };
    const chip = (key, name, has) => { const v = has || ""; return `<button class="qc dd ${v ? "on" : ""}" data-open="${key}">${esc(v || name)}<i>▾</i></button>`; };
    if (counts("brand", (i) => i._f.brand).size > 1 || st.f.brand.size) q.push(chip("brand", t.qBrand, lab("brand", st.f.brand)));
    if (counts("series", (i) => i._f.series).size > 1 || st.f.series.size) q.push(chip("series", t.qSeries, lab("series", st.f.series)));
    if (counts("cap", (i) => i._f.cap).size > 1 || st.f.cap.size) q.push(chip("cap", t.qCap, lab("cap", st.f.cap)));
    q.push(chip("price", t.qPrice, st.price ? t.price[st.price] : ""));
    q.push(`<button class="qc tg ${st.multi ? "on" : ""}" data-k="multi" ${st.multi ? "" : 'data-add="1"'}>${st.multi ? "✓ " : ""}${t.qMulti}</button>`);
    if (st.f.shop.size) q.push(chip("shop", t.fShop, lab("shop", new Set([...st.f.shop].map((x) => SH[x]?.name || x)))));
    $("#quick").innerHTML = q.join("");
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
    target.insertAdjacentHTML("beforeend", slice.map(tbl ? trow : card).join(""));
    shown += slice.length;
    $("#more").hidden = shown >= view.length;
    $("#empty").hidden = view.length > 0;
  }
  function refresh() {
    cnt.brand = counts("brand", (i) => i._f.brand);
    view = sortItems(base.filter((i) => passes(i)));
    $("#hint").textContent = $("#mhint").textContent = st.q ? T().hintQ(st.q, view.length.toLocaleString()) : T().hintCat(T().cats[st.cat], view.length.toLocaleString(), CATS[st.cat]?.multi?.toLocaleString() || 0);
    renderFacets(); renderActive(); renderQuick(); paint(true);
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
    chips();
    // thống kê: 1 page_view mỗi lần đổi màn hình, gửi SAU khi URL đã cập nhật
    const pv = (url) => { history.replaceState(null, "", new URL(url, location.href).href); if (url !== lastPv) { lastPv = url; window.kpPage?.(); } };
    if (st.view === "deals" && !st.q) { pv("?v=deals"); return renderDeals(); }
    if (st.view === "mine" && !st.q) { pv("?v=mine"); return renderMine(); }
    if (st.view === "home" && !st.q) renderNews();
    if (!listMode) { pv("./"); return; }
    $("#hint").textContent = "…";
    if (st.q) {
      const all = (await Promise.all(Object.keys(CATS).map(loadCat))).flat();
      const q = st.q.toLowerCase().replace(/\s/g, "");
      base = all.filter((i) => (i.name + i.key + (i._f.series || "")).toLowerCase().replace(/\s/g, "").includes(q));
    } else {
      base = (await Promise.all([loadCat(st.cat), loadHist(st.cat)]))[0];
    }
    refresh();
    pv(st.q ? "./?q=" + encodeURIComponent(st.q) : "?c=" + st.cat);
  }
  let lastPv = null;
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
        <button class="sdel" data-id="${esc(id)}" aria-label="delete">✕</button></div>`;
    }).join("");
    const watch = Object.entries(mine.watch).map(([id, w]) => ({ id, w, it: m.get(id) }));
    const wcards = watch.filter((x) => x.it).map((x) => card(x.it)).join("");
    const gone = watch.filter((x) => !x.it).map((x) => `<li>${esc(x.w.name)} — ${t.noPrice} <button class="wdel" data-id="${esc(x.id)}">✕</button></li>`).join("");
    $("#mineBody").innerHTML = `
      <h2 class="sec">📦 ${t.stockTitle}</h2>
      ${stock.length ? `<div class="ssum"><span>${t.stockSum(cnt)}</span><b class="${sum >= 0 ? "up" : "dn"}">${sum >= 0 ? "+" : ""}${sum.toLocaleString()}円</b></div><div class="slist">${rows}</div>` : `<p class="mempty">${t.stockEmpty}</p>`}
      <h2 class="sec">♥ ${t.watchTitle}</h2>
      ${watch.length ? `<div class="list">${wcards}</div>${gone ? `<ul class="wgone">${gone}</ul>` : ""}` : `<p class="mempty">${t.watchEmpty}</p>`}`;
    // đã xem → cập nhật mốc "lần trước"
    for (const { id, it } of watch) if (it) mine.watch[id].seen = it.best;
    saveMine(); updMineBadge(0);
  }
  function toggleWatch(id) {
    const it = REG.get(id);
    if (mine.watch[id]) delete mine.watch[id];
    else if (it) mine.watch[id] = { cat: it.cat, key: it.key, name: it.name, seen: it.best, at: it.best };
    saveMine();
    document.querySelectorAll(`.fav[data-id="${CSS.escape(id)}"]`).forEach((b) => { const on = !!mine.watch[id]; b.classList.toggle("on", on); b.textContent = on ? "♥" : "♡"; });
    toast(mine.watch[id] ? T().watchAdded : T().watchRemoved);
    window.kpTrack?.(mine.watch[id] ? "watch_add" : "watch_remove", { item: it?.name || id });
    updMineBadge(0);
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
    const sh = e.target.closest(".shr"); if (sh) { e.preventDefault(); return shareItem(REG.get(sh.dataset.id)); }
    const f = e.target.closest(".fav"); if (f) { e.preventDefault(); return toggleWatch(f.dataset.id); }
    const k = e.target.closest(".stk"); if (k) { e.preventDefault(); return addStock(k.dataset.id, k); }
    const d = e.target.closest(".sdel"); if (d) { delete mine.stock[d.dataset.id]; saveMine(); return renderMine(); }
    const w = e.target.closest(".wdel"); if (w) { delete mine.watch[w.dataset.id]; saveMine(); return renderMine(); }
    const n = e.target.closest(".news,[data-v=mine]");
    if (n && !n.closest("#chips,#mcat")) { st.view = "mine"; $("#q").value = ""; st.q = ""; window.scrollTo({ top: 0 }); return render(); }
  });
  document.addEventListener("change", (e) => {
    const q = e.target.closest(".sq-in"); if (!q) return;
    const s = mine.stock[q.dataset.id]; if (!s) return;
    s.qty = Math.max(1, Math.round(+q.value || 1)); saveMine(); renderMine();
  });

  // ================= deals (PR)
  let deals = null;
  async function renderDeals() {
    deals ||= promos;
    $("#dealList").innerHTML = deals.groups.map((g) => {
      const items = g.items.filter((x) => x.url);
      if (!items.length) return "";
      items.forEach((x) => x.px && pixel(x.px));
      return `<h3 class="dg">${esc(g.title[lang] || g.title.vi)}</h3><div class="dlist">` + items.map((x) => `
        <a class="deal-card" href="${esc(x.url)}" target="_blank" rel="sponsored noopener">
          <span class="pr">${x.affiliate ? "PR" : "LINK"}</span>
          ${x.badge ? `<span class="badge">${esc(x.badge[lang] || x.badge.vi)}</span>` : ""}
          <b>${esc(x.name)}</b><span>${esc((x.desc && (x.desc[lang] || x.desc.vi)) || "")}</span>
          <span class="go">${lang === "vi" ? "Xem chi tiết →" : "詳しく見る →"}</span>
        </a>`).join("") + "</div>";
    }).join("");
    history.replaceState(null, "", new URL("?v=deals", location.href).href);
  }

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
    qL = setTimeout(() => { const v = e.target.value.trim(); if (v.length >= 2) window.kpTrack?.("search", { search_term: v.slice(0, 80) }); }, 1500); });
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
})();
