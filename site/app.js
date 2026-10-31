(async function () {
  const $ = (s) => document.querySelector(s);
  const yen = (n) => n.toLocaleString("ja-JP") + "円";
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const bust = "?" + Math.floor(Date.now() / 600000);
  const idx = await fetch("data/index.json" + bust).then((r) => r.json());
  const SH = idx.shops, CATS = idx.cats;
  const cache = {}, hcache = {};
  const ICON = { phone: "📱", tablet: "📲", game: "🎮", card: "🃏", pc: "💻", camera: "📷", audio: "🎧", appliance: "🔌", watch: "⌚", hobby: "🧸", other: "📦" };

  $("#upd").textContent = "最終更新 " + idx.updated;
  $("#heroStat").textContent = `${Object.keys(SH).length}店舗・${idx.total.toLocaleString()}商品の買取価格（新品・未開封）を毎日チェック。最高値の店と値動きがひと目でわかります。`;
  $("#shops").innerHTML = "掲載店舗：" + Object.values(SH).map((s) => `<a href="${s.url}" target="_blank" rel="noopener">${s.name}</a>`).join("・");

  const loadCat = async (c) => (cache[c] ||= await fetch(`data/cat/${c}.json` + bust).then((r) => r.json()));
  const loadHist = async (c) => (hcache[c] ||= await fetch(`data/hist/${c}.json` + bust).then((r) => r.json()).catch(() => ({})));

  function spark(c, it) {
    const s = ((hcache[c] || {})[it.key] || []).slice(-30);
    if (s.length < 2) return "";
    const v = s.map((p) => p[1]), mn = Math.min(...v), mx = Math.max(...v), r = mx - mn || 1;
    const pts = v.map((y, i) => `${((i / (v.length - 1)) * 80 + 2).toFixed(1)},${(30 - ((y - mn) / r) * 26).toFixed(1)}`).join(" ");
    return `<svg class="spark" width="84" height="32" viewBox="0 0 84 32"><polyline fill="none" stroke="${v[v.length - 1] >= v[0] ? "#16a34a" : "#dc2626"}" stroke-width="2" points="${pts}"/></svg>`;
  }

  function card(it) {
    const shops = Object.entries(it.prices).sort((a, b) => b[1].price - a[1].price);
    const chg = it.chg ? `<span class="chg ${it.chg > 0 ? "up" : "dn"}">${it.chg > 0 ? "▲" : "▼"}${Math.abs(it.chg).toLocaleString()}</span>` : "";
    const rows = shops.map(([sid, p], i) => {
      const extra = p.min && p.min !== p.price ? `<span class="nt">色等で${yen(p.min)}〜</span>` : p.note ? `<span class="nt">${esc(p.note.slice(0, 16))}</span>` : "";
      return `<div class="sh ${i === 0 && shops.length > 1 ? "top" : ""}"><span><a href="${esc(p.url)}" target="_blank" rel="noopener nofollow">${SH[sid].name}</a>${extra}</span><span class="p">${yen(p.price)}</span></div>`;
    }).join("");
    const diff = it.n_shops > 1 && it.spread > 0 ? `<div class="diff">💡 店によって最大 <b>${yen(it.spread)}</b> の差</div>` : "";
    return `<article class="card">
      <div class="c-top"><div><div class="c-name">${esc(it.name)}</div><div class="c-sub">${ICON[it.cat] || ""} ${CATS[it.cat]?.label || ""}・新品/未開封・${it.n_shops}店</div></div>${spark(it.cat, it)}</div>
      <div class="best"><span class="best-p">${yen(it.best)}</span>${it.n_shops > 1 ? `<span class="best-s">最高値：${SH[it.best_shop].name}</span>` : `<span class="best-s one">${SH[it.best_shop].name}</span>`}${chg}</div>
      ${diff}<div class="shops">${rows}</div>
      <label class="calc">仕入れ値 <input type="number" inputmode="numeric" placeholder="例 ${Math.round(it.best * 0.9).toLocaleString()}" data-best="${it.best}"> 円 → 利益 <b class="pf">—</b></label>
    </article>`;
  }

  // ---------------- state & routing
  let cur = null, view = [], shown = 0;
  const PAGE = 60;
  function chips() {
    const order = Object.entries(CATS).sort((a, b) => b[1].multi - a[1].multi || b[1].count - a[1].count);
    $("#chips").innerHTML = `<button data-c="" class="${cur ? "" : "on"}">🏠 トップ</button>` +
      order.map(([c, v]) => `<button data-c="${c}" class="${cur === c ? "on" : ""}">${ICON[c] || ""} ${v.label}<small>${v.count.toLocaleString()}</small></button>`).join("");
  }
  function sortItems(items) {
    const s = $("#sort").value;
    const f = { rec: (a, b) => (b.n_shops - a.n_shops) || (b.spread - a.spread) || (b.best - a.best), best: (a, b) => b.best - a.best,
      spread: (a, b) => b.spread - a.spread, up: (a, b) => (b.chg || 0) - (a.chg || 0), down: (a, b) => (a.chg || 0) - (b.chg || 0),
      name: (a, b) => a.name.localeCompare(b.name, "ja") }[s];
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
  async function openCat(c) {
    cur = c; chips();
    $("#home").hidden = !!c; $("#catview").hidden = !c;
    history.replaceState(null, "", c ? "?c=" + c : "./");
    if (!c) return;
    $("#hint").textContent = "読み込み中…";
    const [items] = await Promise.all([loadCat(c), loadHist(c)]);
    let v = items.slice();
    if ($("#multi").checked) v = v.filter((i) => i.n_shops > 1);
    view = sortItems(v);
    $("#hint").textContent = `${CATS[c].label}：${view.length.toLocaleString()}件（複数店比較 ${CATS[c].multi.toLocaleString()}件）`;
    paint(true);
  }
  let qTimer;
  async function search(q) {
    q = q.trim().toLowerCase().replace(/\s/g, "");
    if (!q) return openCat(cur);
    $("#home").hidden = true; $("#catview").hidden = false;
    $("#hint").textContent = "全カテゴリを検索中…";
    const all = (await Promise.all(Object.keys(CATS).map(loadCat))).flat();
    let v = all.filter((i) => (i.name + i.key).toLowerCase().replace(/\s/g, "").includes(q));
    if ($("#multi").checked) v = v.filter((i) => i.n_shops > 1);
    view = sortItems(v);
    $("#hint").textContent = `「${q}」の検索結果：${view.length.toLocaleString()}件`;
    paint(true);
  }

  // ---------------- home
  const top = await fetch("data/top.json" + bust).then((r) => r.json()).catch(() => []);
  $("#top").innerHTML = top.slice(0, 18).map(card).join("");

  $("#chips").addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) { $("#q").value = ""; openCat(b.dataset.c || null); } });
  $("#sort").addEventListener("input", () => ($("#q").value ? search($("#q").value) : openCat(cur)));
  $("#multi").addEventListener("input", () => ($("#q").value ? search($("#q").value) : openCat(cur)));
  $("#q").addEventListener("input", (e) => { clearTimeout(qTimer); qTimer = setTimeout(() => search(e.target.value), 250); });
  $("#more").addEventListener("click", () => paint(false));
  document.body.addEventListener("input", (e) => {
    if (!e.target.matches(".calc input")) return;
    const v = parseInt(e.target.value, 10), best = +e.target.dataset.best, out = e.target.parentElement.querySelector(".pf");
    if (!v) { out.textContent = "—"; out.style.color = ""; return; }
    const p = best - v; out.textContent = (p >= 0 ? "+" : "") + p.toLocaleString() + "円"; out.style.color = p >= 0 ? "#16a34a" : "#dc2626";
  });
  const start = new URLSearchParams(location.search).get("c");
  chips();
  if (start && CATS[start]) openCat(start);
})();
