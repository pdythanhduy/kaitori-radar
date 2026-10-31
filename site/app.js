(async function () {
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const yen = (n) => n.toLocaleString("ja-JP") + "円";
  const bust = "?" + Math.floor(Date.now() / 600000);
  let lang = localStorage.getItem("lang") || "vi";
  const T = () => window.I18N[lang];

  const idx = await fetch("data/index.json" + bust).then((r) => r.json());
  const SH = idx.shops, CATS = idx.cats;
  const cache = {}, hcache = {};
  const ICON = { phone: "📱", tablet: "📲", game: "🎮", card: "🃏", pc: "💻", camera: "📷", audio: "🎧", appliance: "🔌", watch: "⌚", hobby: "🧸", other: "📦" };
  const PRICE = [[0, Infinity], [0, 10000], [10000, 50000], [50000, 200000], [200000, Infinity]];
  const st = { view: "home", cat: null, q: "", f: { cat: new Set(), brand: new Set(), series: new Set(), cap: new Set(), shop: new Set() },
    price: 0, multi: false, gap: false, sort: "rec", layout: localStorage.getItem("layout") || "card" };

  const promos = await fetch("promos.json" + bust).then((r) => r.json()).catch(() => ({ groups: [], inline: {} }));
  const AFF = promos.inline || {};
  const pxSeen = new Set();
  function pixel(src) {  // ảnh 1x1 đo lượt hiển thị A8 — mỗi chương trình 1 lần/trang
    if (!src || pxSeen.has(src)) return;
    pxSeen.add(src);
    const i = new Image(1, 1); i.src = src; i.alt = ""; i.style.cssText = "position:absolute;width:1px;height:1px;opacity:0"; document.body.appendChild(i);
  }
  function affBox(cat) {
    const a = AFF[cat]; if (!a) return "";
    pixel(a.px + "?a8mat=" + a.a8mat);
    return `<div class="aff"><span class="pr">PR</span><span>${T().affText}</span><a href="https://px.a8.net/svt/ejp?a8mat=${a.a8mat}" target="_blank" rel="sponsored nofollow noopener">${esc(a.name)} →</a></div>`;
  }
  const loadCat = async (c) => (cache[c] ||= FACETS.enrich(await fetch(`data/cat/${c}.json` + bust).then((r) => r.json())));
  const loadHist = async (c) => (hcache[c] ||= await fetch(`data/hist/${c}.json` + bust).then((r) => r.json()).catch(() => ({})));

  // ================= static text
  function applyLang() {
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach((el) => { const v = T()[el.dataset.i18n]; if (typeof v === "string") el.textContent = v; });
    $("#lang").textContent = lang === "vi" ? "日本語" : "Tiếng Việt";
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
    const cur = st.view === "cat" && !st.q ? `${ICON[st.cat] || ""} ${t.cats[st.cat] || ""}` : t.pickCat;
    $("#mcLabel").textContent = cur;
    $("#mcPick").classList.toggle("on", st.view === "cat" && !st.q);
    $("#mcat .mc-home").classList.toggle("on", st.view === "home" && !st.q);
    $("#mcDeal").textContent = t.deals;
    $("#mcDeal").classList.toggle("on", st.view === "deals" && !st.q);
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
  function shopLink(sid, p, it) {
    const lst = SH[sid]?.list;
    return lst
      ? `<a href="${esc(p.url)}" target="_blank" rel="noopener nofollow" class="lst" data-copy="${esc(it.name)}" title="${esc(T().listTip)}">${SH[sid]?.name || sid} 🔍</a>`
      : `<a href="${esc(p.url)}" target="_blank" rel="noopener nofollow">${SH[sid]?.name || sid}</a>`;
  }
  function card(it) {
    const t = T();
    const shops = Object.entries(it.prices).sort((a, b) => b[1].price - a[1].price);
    const chg = it.chg ? `<span class="chg ${it.chg > 0 ? "up" : "dn"}">${it.chg > 0 ? "▲" : "▼"}${Math.abs(it.chg).toLocaleString()}</span>` : "";
    const rows = shops.map(([sid, p], i) => {
      const extra = p.min && p.min !== p.price ? `<span class="nt">${t.colorFrom} ${yen(p.min)}</span>` : p.note ? `<span class="nt">${esc(p.note.slice(0, 16))}</span>` : "";
      return `<div class="sh ${i === 0 && shops.length > 1 ? "top" : ""}"><span>${shopLink(sid, p, it)}${extra}</span><span class="p">${yen(p.price)}</span></div>`;
    }).join("");
    const diff = it.n_shops > 1 && it.spread > 0 ? `<div class="diff">${t.diff(yen(it.spread))}</div>` : "";
    const br = it._f?.brand !== "Khác" ? it._f?.brand : "";
    const tag = [br && !(it._f?.series || "").startsWith(br.split(" ")[0]) ? br : "", it._f?.series, it._f?.cap].filter(Boolean).join(" · ");
    return `<article class="card">
      <div class="c-top"><div><div class="c-name">${esc(it.name)}</div><div class="c-sub">${ICON[it.cat] || ""} ${esc(tag || t.cats[it.cat] || "")}・${t.shopsN(it.n_shops)}</div></div>${spark(it)}</div>
      <div class="best"><span class="best-p">${yen(it.best)}</span><span class="best-s ${it.n_shops > 1 ? "" : "one"}">${it.n_shops > 1 ? t.best + "：" : ""}${SH[it.best_shop]?.name || ""}</span>${chg}</div>
      ${diff}<div class="shops">${rows}</div>
      ${affBox(it.cat)}
      <label class="calc">${t.calc} <input type="number" inputmode="numeric" placeholder="${Math.round(it.best * 0.9).toLocaleString()}" data-best="${it.best}"> 円 → ${t.profit} <b class="pf">—</b></label>
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
      <span class="tg">${it.spread ? "+" + it.spread.toLocaleString() : "—"}</span></div>`;
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
    return `<div class="fg"><div class="fg-t">${title}</div>${rows}${more}</div>`;
  }
  function renderFacets() {
    const t = T();
    let h = "";
    if (st.q) h += facetBlock("cat", t.fCat, counts("cat", (i) => i.cat), { labels: (c) => `${ICON[c] || ""} ${t.cats[c] || c}` });
    h += facetBlock("brand", t.fBrand, counts("brand", (i) => i._f.brand), { labels: (v) => (v === "Khác" ? t.otherB : v), sort: (a, b) => (a === "Khác") - (b === "Khác") || (cnt.brand.get(b) || 0) - (cnt.brand.get(a) || 0) });
    const sc = counts("series", (i) => i._f.series);
    h += facetBlock("series", t.fSeries, sc, { sort: st.f.brand.size ? FACETS.seriesSort : (a, b) => (sc.get(b) || 0) - (sc.get(a) || 0), limit: 12 });
    h += facetBlock("cap", t.fCap, counts("cap", (i) => i._f.cap), { sort: (a, b) => FACETS.CAP_ORDER.indexOf(a) - FACETS.CAP_ORDER.indexOf(b) });
    h += facetBlock("shop", t.fShop, counts("shop", (i) => Object.keys(i.prices)), { labels: (s) => SH[s]?.name || s, limit: 12 });
    h += `<div class="fg"><div class="fg-t">${t.fPrice}</div>${t.price.map((p, i) => `<label class="fo"><input type="radio" name="pr" data-p="${i}" ${st.price === i ? "checked" : ""}><span>${p}</span></label>`).join("")}</div>`;
    h += `<div class="fg"><div class="fg-t">${t.fMore}</div>
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
  function sortItems(items) {
    const f = { rec: (a, b) => (b.n_shops - a.n_shops) || (b.spread - a.spread) || (b.best - a.best), best: (a, b) => b.best - a.best,
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
    $("#hint").textContent = st.q ? T().hintQ(st.q, view.length.toLocaleString()) : T().hintCat(T().cats[st.cat], view.length.toLocaleString(), CATS[st.cat]?.multi?.toLocaleString() || 0);
    renderFacets(); renderActive(); paint(true);
  }
  async function render() {
    const listMode = st.view === "cat" || !!st.q;
    $("#home").hidden = st.view !== "home" || !!st.q;
    $("#catview").hidden = !listMode;
    $("#deals").hidden = st.view !== "deals" || !!st.q;
    chips();
    if (st.view === "deals" && !st.q) return renderDeals();
    if (!listMode) { history.replaceState(null, "", "./"); return; }
    $("#hint").textContent = "…";
    if (st.q) {
      const all = (await Promise.all(Object.keys(CATS).map(loadCat))).flat();
      const q = st.q.toLowerCase().replace(/\s/g, "");
      base = all.filter((i) => (i.name + i.key + (i._f.series || "")).toLowerCase().replace(/\s/g, "").includes(q));
    } else {
      base = (await Promise.all([loadCat(st.cat), loadHist(st.cat)]))[0];
    }
    refresh();
    history.replaceState(null, "", st.view === "cat" && !st.q ? "?c=" + st.cat : "./");
  }
  function clearFilters() { for (const k in st.f) st.f[k].clear(); st.price = 0; st.multi = st.gap = false; }

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
    history.replaceState(null, "", "?v=deals");
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
  $("#mcat").addEventListener("click", pickNav);
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
    st.layout = b.dataset.v; localStorage.setItem("layout", st.layout);
    document.querySelectorAll("#vtog button").forEach((x) => x.classList.toggle("on", x === b)); paint(true);
  });
  const openSide = (o) => { document.body.classList.toggle("side-open", o); };
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
    $("#chips").classList.toggle("stuck", $("#chips").getBoundingClientRect().top <= 53 && window.scrollY > 60);
  }, { passive: true });
  $("#scrim").addEventListener("click", () => openSide(false));
  let qT; $("#q").addEventListener("input", (e) => { clearTimeout(qT); qT = setTimeout(() => { st.q = e.target.value.trim(); clearFilters(); render(); }, 250); });
  $("#more").addEventListener("click", () => paint(false));
  $("#lang").addEventListener("click", () => { lang = lang === "vi" ? "ja" : "vi"; localStorage.setItem("lang", lang); applyLang(); render(); $("#top").innerHTML = top.slice(0, 18).map(card).join(""); });
  document.body.addEventListener("click", (e) => {
    const a = e.target.closest("a.lst"); if (!a) return;
    navigator.clipboard?.writeText(a.dataset.copy).catch(() => {});
    toast(T().copied);
  });
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

  // ================= start
  const top = FACETS.enrich(await fetch("data/top.json" + bust).then((r) => r.json()).catch(() => []));
  const sp = new URLSearchParams(location.search);
  if (sp.get("c") && CATS[sp.get("c")]) { st.view = "cat"; st.cat = sp.get("c"); }
  if (sp.get("v") === "deals") st.view = "deals";
  applyLang();
  $("#top").innerHTML = top.slice(0, 18).map(card).join("");
  render();
})();
