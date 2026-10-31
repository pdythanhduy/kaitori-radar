(async function () {
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const yen = (n) => n.toLocaleString("ja-JP") + "円";
  const bust = "?" + Math.floor(Date.now() / 600000);
  let lang = localStorage.getItem("lang") || "vi";  // mặc định tiếng Việt
  const T = () => window.I18N[lang];

  const idx = await fetch("data/index.json" + bust).then((r) => r.json());
  const SH = idx.shops, CATS = idx.cats;
  const cache = {}, hcache = {};
  const ICON = { phone: "📱", tablet: "📲", game: "🎮", card: "🃏", pc: "💻", camera: "📷", audio: "🎧", appliance: "🔌", watch: "⌚", hobby: "🧸", other: "📦" };
  const PRICE = [[0, Infinity], [0, 10000], [10000, 50000], [50000, 200000], [200000, Infinity]];
  const st = { view: "home", cat: null, q: "", shops: new Set(), price: 0, multi: false, gap: false, sort: "rec" };

  const loadCat = async (c) => (cache[c] ||= await fetch(`data/cat/${c}.json` + bust).then((r) => r.json()));
  const loadHist = async (c) => (hcache[c] ||= await fetch(`data/hist/${c}.json` + bust).then((r) => r.json()).catch(() => ({})));

  // ---------------- static text
  function applyLang() {
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach((el) => { const v = T()[el.dataset.i18n]; if (typeof v === "string") el.textContent = v; });
    $("#lang").textContent = lang === "vi" ? "日本語" : "Tiếng Việt";
    $("#q").placeholder = T().search;
    $("#upd").textContent = `${T().upd} ${idx.updated}`;
    $("#heroStat").textContent = T().hero(Object.keys(SH).length, idx.total.toLocaleString());
    $("#shops").innerHTML = T().stores + " " + Object.values(SH).map((s) => `<a href="${s.url}" target="_blank" rel="noopener">${s.name}</a>`).join("・");
    $("#sort").innerHTML = Object.entries(T().sort).map(([k, v]) => `<option value="${k}" ${st.sort === k ? "selected" : ""}>${v}</option>`).join("");
    $("#fPrice").innerHTML = T().price.map((p, i) => `<button class="opt ${st.price === i ? "on" : ""}" data-p="${i}">${p}</button>`).join("");
    $("#fShops").innerHTML = `<button class="opt ${st.shops.size ? "" : "on"}" data-s="">${T().all}</button>` +
      Object.entries(SH).map(([k, s]) => `<button class="opt ${st.shops.has(k) ? "on" : ""}" data-s="${k}">${s.name}</button>`).join("");
    chips();
  }

  function chips() {
    const order = Object.entries(CATS).sort((a, b) => b[1].multi - a[1].multi || b[1].count - a[1].count);
    $("#chips").innerHTML =
      `<button data-v="home" class="${st.view === "home" ? "on" : ""}">${T().home}</button>` +
      order.map(([c, v]) => `<button data-c="${c}" class="${st.view === "cat" && st.cat === c ? "on" : ""}">${ICON[c] || ""} ${T().cats[c] || v.label}<small>${v.count.toLocaleString()}</small></button>`).join("") +
      `<button data-v="deals" class="deal ${st.view === "deals" ? "on" : ""}">${T().deals}</button>`;
  }

  // ---------------- cards
  function spark(it) {
    const s = ((hcache[it.cat] || {})[it.key] || []).slice(-30);
    if (s.length < 2) return "";
    const v = s.map((p) => p[1]), mn = Math.min(...v), mx = Math.max(...v), r = mx - mn || 1;
    const pts = v.map((y, i) => `${((i / (v.length - 1)) * 80 + 2).toFixed(1)},${(30 - ((y - mn) / r) * 26).toFixed(1)}`).join(" ");
    return `<svg class="spark" width="84" height="32" viewBox="0 0 84 32"><polyline fill="none" stroke="${v[v.length - 1] >= v[0] ? "#16a34a" : "#dc2626"}" stroke-width="2" points="${pts}"/></svg>`;
  }
  function card(it) {
    const t = T();
    const shops = Object.entries(it.prices).sort((a, b) => b[1].price - a[1].price);
    const chg = it.chg ? `<span class="chg ${it.chg > 0 ? "up" : "dn"}">${it.chg > 0 ? "▲" : "▼"}${Math.abs(it.chg).toLocaleString()}</span>` : "";
    const rows = shops.map(([sid, p], i) => {
      const extra = p.min && p.min !== p.price ? `<span class="nt">${t.colorFrom} ${yen(p.min)}</span>` : p.note ? `<span class="nt">${esc(p.note.slice(0, 16))}</span>` : "";
      return `<div class="sh ${i === 0 && shops.length > 1 ? "top" : ""}"><span><a href="${esc(p.url)}" target="_blank" rel="noopener nofollow">${SH[sid]?.name || sid}</a>${extra}</span><span class="p">${yen(p.price)}</span></div>`;
    }).join("");
    const diff = it.n_shops > 1 && it.spread > 0 ? `<div class="diff">${t.diff(yen(it.spread))}</div>` : "";
    return `<article class="card">
      <div class="c-top"><div><div class="c-name">${esc(it.name)}</div><div class="c-sub">${ICON[it.cat] || ""} ${t.cats[it.cat] || ""}・${t.newItem}・${t.shopsN(it.n_shops)}</div></div>${spark(it)}</div>
      <div class="best"><span class="best-p">${yen(it.best)}</span><span class="best-s ${it.n_shops > 1 ? "" : "one"}">${it.n_shops > 1 ? t.best + "：" : ""}${SH[it.best_shop]?.name || ""}</span>${chg}</div>
      ${diff}<div class="shops">${rows}</div>
      <label class="calc">${t.calc} <input type="number" inputmode="numeric" placeholder="${Math.round(it.best * 0.9).toLocaleString()}" data-best="${it.best}"> 円 → ${t.profit} <b class="pf">—</b></label>
    </article>`;
  }

  // ---------------- list view
  let view = [], shown = 0;
  const PAGE = 48;
  function filterItems(items) {
    const [lo, hi] = PRICE[st.price];
    return items.filter((i) => {
      if (st.multi && i.n_shops < 2) return false;
      if (st.gap && i.spread < 3000) return false;
      if (st.shops.size && !Object.keys(i.prices).some((s) => st.shops.has(s))) return false;
      return i.best >= lo && i.best < hi;
    });
  }
  function sortItems(items) {
    const f = { rec: (a, b) => (b.n_shops - a.n_shops) || (b.spread - a.spread) || (b.best - a.best), best: (a, b) => b.best - a.best,
      spread: (a, b) => b.spread - a.spread, up: (a, b) => (b.chg || 0) - (a.chg || 0), down: (a, b) => (a.chg || 0) - (b.chg || 0),
      name: (a, b) => a.name.localeCompare(b.name, "ja") }[st.sort];
    return items.sort(f);
  }
  function paint(reset) {
    if (reset) { shown = 0; $("#list").innerHTML = ""; }
    const slice = view.slice(shown, shown + PAGE);
    $("#list").insertAdjacentHTML("beforeend", slice.map(card).join(""));
    shown += slice.length;
    $("#more").hidden = shown >= view.length;
    $("#empty").hidden = view.length > 0;
  }
  function fCount() {
    const n = st.shops.size + (st.price ? 1 : 0) + (st.multi ? 1 : 0) + (st.gap ? 1 : 0);
    $("#fCount").textContent = n ? `(${n})` : "";
  }
  async function render() {
    $("#home").hidden = st.view !== "home" || !!st.q;
    $("#catview").hidden = !(st.view === "cat" || st.q);
    $("#deals").hidden = st.view !== "deals" || !!st.q;
    $("#filters").hidden = !(st.view === "cat" || st.q);
    chips(); fCount();
    if (st.view === "deals" && !st.q) return renderDeals();
    if (!(st.view === "cat" || st.q)) return;
    $("#hint").textContent = "…";
    let items;
    if (st.q) {
      const all = (await Promise.all(Object.keys(CATS).map(loadCat))).flat();
      const q = st.q.toLowerCase().replace(/\s/g, "");
      items = all.filter((i) => (i.name + i.key).toLowerCase().replace(/\s/g, "").includes(q));
    } else {
      items = (await Promise.all([loadCat(st.cat), loadHist(st.cat)]))[0].slice();
    }
    view = sortItems(filterItems(items));
    $("#hint").textContent = st.q ? T().hintQ(st.q, view.length.toLocaleString()) : T().hintCat(T().cats[st.cat], view.length.toLocaleString(), CATS[st.cat].multi.toLocaleString());
    paint(true);
    const u = new URLSearchParams(); if (st.view === "cat") u.set("c", st.cat); if (st.view === "deals") u.set("v", "deals");
    history.replaceState(null, "", u.toString() ? "?" + u : "./");
  }

  // ---------------- deals (PR)
  let deals = null;
  async function renderDeals() {
    deals ||= await fetch("promos.json" + bust).then((r) => r.json()).catch(() => ({ groups: [] }));
    $("#dealList").innerHTML = deals.groups.map((g) => {
      const items = g.items.filter((x) => x.url);
      if (!items.length) return "";
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

  // ---------------- events
  $("#chips").addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    $("#q").value = ""; st.q = "";
    if (b.dataset.c) { st.view = "cat"; st.cat = b.dataset.c; } else st.view = b.dataset.v;
    window.scrollTo({ top: $("#chips").offsetTop - 60, behavior: "smooth" });
    render();
  });
  $("#fShops").addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    const s = b.dataset.s; if (!s) st.shops.clear(); else st.shops.has(s) ? st.shops.delete(s) : st.shops.add(s);
    applyLang(); render();
  });
  $("#fPrice").addEventListener("click", (e) => { const b = e.target.closest("button"); if (!b) return; st.price = +b.dataset.p; applyLang(); render(); });
  $("#multi").addEventListener("change", (e) => { st.multi = e.target.checked; render(); });
  $("#gap").addEventListener("change", (e) => { st.gap = e.target.checked; render(); });
  $("#sort").addEventListener("change", (e) => { st.sort = e.target.value; render(); });
  $("#reset").addEventListener("click", () => { st.shops.clear(); st.price = 0; st.multi = st.gap = false; st.sort = "rec"; $("#multi").checked = $("#gap").checked = false; applyLang(); render(); });
  $("#fToggle").addEventListener("click", () => $("#filters").classList.toggle("open"));
  let qT; $("#q").addEventListener("input", (e) => { clearTimeout(qT); qT = setTimeout(() => { st.q = e.target.value.trim(); render(); }, 250); });
  $("#more").addEventListener("click", () => paint(false));
  $("#lang").addEventListener("click", () => { lang = lang === "vi" ? "ja" : "vi"; localStorage.setItem("lang", lang); applyLang(); render(); $("#top").innerHTML = top.slice(0, 18).map(card).join(""); });
  document.body.addEventListener("input", (e) => {
    if (!e.target.matches(".calc input")) return;
    const v = parseInt(e.target.value, 10), best = +e.target.dataset.best, out = e.target.parentElement.querySelector(".pf");
    if (!v) { out.textContent = "—"; out.style.color = ""; return; }
    const p = best - v; out.textContent = (p >= 0 ? "+" : "") + p.toLocaleString() + "円"; out.style.color = p >= 0 ? "#16a34a" : "#dc2626";
  });

  // ---------------- start
  const top = await fetch("data/top.json" + bust).then((r) => r.json()).catch(() => []);
  const sp = new URLSearchParams(location.search);
  if (sp.get("c") && CATS[sp.get("c")]) { st.view = "cat"; st.cat = sp.get("c"); }
  if (sp.get("v") === "deals") st.view = "deals";
  applyLang();
  $("#top").innerHTML = top.slice(0, 18).map(card).join("");
  render();
})();
