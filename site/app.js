(async function () {
  const $ = (s) => document.querySelector(s);
  const yen = (n) => n.toLocaleString("ja-JP") + "円";
  const [data, hist] = await Promise.all([
    fetch("data/latest.json?" + Date.now()).then((r) => r.json()),
    fetch("data/history.json?" + Date.now()).then((r) => r.json()).catch(() => ({})),
  ]);
  const SH = data.shops;
  $("#upd").textContent = "最終更新 " + data.updated;
  $("#shops").innerHTML = "掲載店舗：" + Object.values(SH).map((s) => `<a href="${s.url}" target="_blank" rel="noopener">${s.name}</a>`).join("・");

  let cat = new URLSearchParams(location.search).get("cat") || "pokebox";
  const series = (it) => hist[`${it.cat}|${it.key}`] || [];
  const change = (it) => { const s = series(it); return s.length >= 2 ? s[s.length - 1][1] - s[s.length - 2][1] : 0; };

  function spark(it) {
    const s = series(it).slice(-30);
    if (s.length < 2) return '<svg class="spark" width="84" height="32"></svg>';
    const v = s.map((p) => p[1]), mn = Math.min(...v), mx = Math.max(...v), r = mx - mn || 1;
    const pts = v.map((y, i) => `${(i / (v.length - 1)) * 80 + 2},${30 - ((y - mn) / r) * 26}`).join(" ");
    const col = v[v.length - 1] >= v[0] ? "#16a34a" : "#dc2626";
    return `<svg class="spark" width="84" height="32" viewBox="0 0 84 32"><polyline fill="none" stroke="${col}" stroke-width="2" points="${pts}"/></svg>`;
  }

  function card(it) {
    const shops = Object.entries(it.prices).sort((a, b) => b[1].price - a[1].price);
    const ch = change(it);
    const chHtml = ch ? `<span class="chg ${ch > 0 ? "up" : "dn"}">${ch > 0 ? "▲" : "▼"}${Math.abs(ch).toLocaleString()}（前日比）</span>` : "";
    const rows = shops.map(([sid, p], i) => {
      const range = p.min && p.min !== p.price ? `<span class="nt">色により${yen(p.min)}〜</span>` : (p.note ? `<span class="nt">${p.note.slice(0, 18)}</span>` : "");
      return `<div class="sh ${i === 0 ? "top" : ""}"><span><a href="${p.url}" target="_blank" rel="noopener nofollow">${SH[sid].name}</a>${range}</span><span class="p">${yen(p.price)}</span></div>`;
    }).join("");
    const diff = it.n_shops > 1 && it.spread > 0 ? `<div class="diff">💡 店によって最大 <b>${yen(it.spread)}</b> の差</div>` : "";
    const sub = it.cat === "pokebox" ? "未開封・シュリンク付き" : "新品未開封・SIMフリー";
    return `<article class="card">
      <div class="c-top"><div><div class="c-name">${it.name}</div><div class="c-sub">${sub}・${it.n_shops}店比較</div></div>${spark(it)}</div>
      <div class="best"><span class="best-p">${yen(it.best)}</span><span class="best-s">最高値：${SH[it.best_shop].name}</span>${chHtml}</div>
      ${diff}
      <div class="shops">${rows}</div>
      <label class="calc">仕入れ値 <input type="number" inputmode="numeric" placeholder="${it.cat === "pokebox" ? "例 5400" : "例 239800"}" data-best="${it.best}"> 円 → 利益 <b class="pf">—</b></label>
    </article>`;
  }

  function render() {
    const q = $("#q").value.trim().toLowerCase().replace(/\s/g, "");
    let items = data.items.filter((i) => i.cat === cat);
    if ($("#multi").checked) items = items.filter((i) => i.n_shops > 1);
    if (q) items = items.filter((i) => (i.name + i.key).toLowerCase().replace(/\s/g, "").includes(q));
    const s = $("#sort").value;
    const cmp = { rec: (a, b) => (b.n_shops - a.n_shops) || (b.best - a.best), best: (a, b) => b.best - a.best, spread: (a, b) => b.spread - a.spread, change: (a, b) => change(b) - change(a),
      drop: (a, b) => change(a) - change(b), name: (a, b) => a.name.localeCompare(b.name, "ja") }[s];
    items.sort(cmp);
    $("#list").innerHTML = items.map(card).join("");
    $("#empty").hidden = items.length > 0;
    $("#hint").textContent = `${items.length}件表示・価格は各店の公開買取価格（税込）。カードをタップで店舗サイトへ。`;
    document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("on", b.dataset.cat === cat));
  }

  $("#tabs").addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    cat = b.dataset.cat; history.replaceState(null, "", "?cat=" + cat); render();
  });
  ["#q", "#sort", "#multi"].forEach((id) => $(id).addEventListener("input", render));
  $("#list").addEventListener("input", (e) => {
    if (!e.target.matches(".calc input")) return;
    const v = parseInt(e.target.value, 10), best = +e.target.dataset.best, out = e.target.parentElement.querySelector(".pf");
    if (!v) { out.textContent = "—"; out.style.color = ""; return; }
    const p = best - v; out.textContent = (p >= 0 ? "+" : "") + p.toLocaleString() + "円"; out.style.color = p >= 0 ? "#16a34a" : "#dc2626";
  });
  render();
})();
