"""Sinh trang HTML tĩnh cho SEO từ site/data (chạy lúc deploy, không commit).

- /p/<slug>/      : 1 trang / sản phẩm có >= 2 tiệm (bảng giá các tiệm, lịch sử giá, món liên quan)
- /c/<cat>/       : 1 trang / nhóm hàng, liệt kê link tới các trang sản phẩm
- /sitemap.xml, /llms.txt

    python -m radar.pages
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
DATA = SITE / "data"
BASE = "https://kaitoriprice.com"
BRAND = "買取プライス"
MIN_SHOPS = 2  # trang 1 tiệm quá mỏng, không có gì để "so sánh"

CAT_JA = {
    "phone": "スマホ・iPhone", "tablet": "タブレット・iPad", "game": "ゲーム機", "card": "トレカ・ポケカBOX",
    "pc": "パソコン", "camera": "カメラ・レンズ", "audio": "オーディオ", "appliance": "家電",
    "watch": "時計", "hobby": "ホビー・フィギュア", "other": "その他",
}
CAT_ORDER = ["phone", "game", "camera", "card", "tablet", "audio", "watch", "pc", "hobby", "appliance", "other"]

e = lambda s: html.escape(str(s or ""), quote=True)
yen = lambda n: f"{int(n):,}円"


def slug(key: str, name: str) -> str:
    s = unicodedata.normalize("NFKC", name).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60].strip("-")
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()[:6]  # ổn định theo key, tránh trùng
    return f"{s}-{h}" if s else h


def series_of(name: str) -> str:
    """'iPhone 16 Pro 256GB' -> 'iPhone 16 Pro' (gom các dung lượng / màu cùng dòng)."""
    n = unicodedata.normalize("NFKC", name)
    n = re.split(r"\s*\d{2,4}\s*(?:GB|TB)\b", n, maxsplit=1, flags=re.I)[0]
    return n.strip()[:40]


def spark_svg(pts: list) -> str:
    if len(pts) < 2:
        return ""
    v = [p[1] for p in pts]
    mn, mx = min(v), max(v)
    r = (mx - mn) or 1
    xy = " ".join(f"{i / (len(v) - 1) * 296 + 2:.1f},{58 - (y - mn) / r * 52:.1f}" for i, y in enumerate(v))
    col = "#16a34a" if v[-1] >= v[0] else "#dc2626"
    return (f'<svg class="hs" viewBox="0 0 300 62" preserveAspectRatio="none" role="img" aria-label="買取価格の推移">'
            f'<polyline fill="none" stroke="{col}" stroke-width="2" points="{xy}"/></svg>')


def page(title: str, desc: str, path: str, body: str, ld: list, updated: str) -> str:
    url = BASE + path
    lds = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/icon-512.png">
<meta name="twitter:card" content="summary">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon-96.png" sizes="96x96" type="image/png">
<link rel="icon" href="/icon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="theme-color" content="#0f172a">
<link rel="stylesheet" href="/page.css?v=5">
<script src="/ga.js?v=2"></script>
{lds}
</head>
<body>
<header class="hd"><a class="logo" href="/"><img src="/logo-64.png" alt="" width="28" height="28">{BRAND}</a><a class="hd-cta" href="/">全商品を比較 →</a></header>
<main>
{body}
</main>
<footer class="ft">
<nav>{" ".join(f'<a href="/c/{c}/">{e(CAT_JA[c])}</a>' for c in CAT_ORDER)} <a href="/guide/">買取ガイド</a></nav>
<p>価格は各買取店の公開ページから自動取得（最終更新 {e(updated)} JST）。実際の買取額は状態・時期により変わります。必ず各店舗でご確認ください。</p>
<p>© {BRAND} · <a href="/">kaitoriprice.com</a></p>
</footer>
</body>
</html>
"""


def crumbs(items: list[tuple[str, str]]) -> dict:
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + p}
                                for i, (n, p) in enumerate(items)]}


from urllib.parse import quote as _q
_MOSHIMO = {"楽天市場": (5876750, 54, 54, 616, "https://search.rakuten.co.jp/search/mall/{}/"),
            "Yahoo!ショッピング": (5876756, 1225, 1925, 18502, "https://shopping.yahoo.co.jp/search?p={}")}


def buy_html(it, name):
    """Nút mua hàng mới (もしもアフィリエイト), ghi rõ PR theo quy định ステマ."""
    q = re.sub(r"[【\[(（][^】\])）]*[】\])）]", " ", it["key"].split("|")[0] if it["key"].startswith("iPhone") else name)
    q = re.sub(r"\s+", " ", q).strip()[:60]
    links = []
    for label, (a, p, pc, pl, u) in _MOSHIMO.items():
        href = f"https://af.moshimo.com/af/c/click?a_id={a}&p_id={p}&pc_id={pc}&pl_id={pl}&url={_q(u.format(_q(q)), safe='')}"
        links.append(f'<a href="{e(href)}" target="_blank" rel="sponsored nofollow noopener">{label}</a>')
    return f'<p class="buy"><span class="pr">PR</span> 新品を探す：{" ".join(links)}</p>'


def product_page(it: dict, shops: dict, hist: list, related: list, updated: str) -> str:
    cat, name = it["cat"], it["name"]
    rows = sorted(it["prices"].items(), key=lambda kv: -kv[1]["price"])
    best_name = shops.get(it["best_shop"], {}).get("name", it["best_shop"])
    low = rows[-1][1]["price"]
    gap = it["best"] - low
    title = f"{name} 買取価格比較｜最高{yen(it['best'])}（{best_name}）- {BRAND}"
    desc = (f"{name}の新品・未開封買取価格を{it['n_shops']}店で比較。最高は{best_name}の{yen(it['best'])}"
            + (f"、最安店との差は{yen(gap)}。" if gap > 0 else "。")
            + "毎時更新・価格推移グラフ付き。")
    trs = []
    for i, (sid, p) in enumerate(rows):
        sn = shops.get(sid, {}).get("name", sid)
        note = p.get("note", "").strip()
        if p.get("min") and p["min"] != p["price"]:
            note = f"色により{yen(p['min'])}〜"
        href = p["url"] + ("#:~:text=" + _q(p["n"].strip(), safe="").replace("-", "%2D") if p.get("n") else "")
        trs.append(f'<tr class="{"top" if i == 0 else ""}"><td><a href="{e(href)}" target="_blank" rel="noopener nofollow">{e(sn)}</a>'
                   f'{f"<small>{e(note[:40])}</small>" if note else ""}</td><td class="p">{yen(p["price"])}</td>'
                   f'<td class="d">{"最高" if i == 0 else "−" + format(it["best"] - p["price"], ",")}</td></tr>')
    hpts = hist[-60:]
    hv = [p[1] for p in hpts]
    hist_html = ""
    chg_txt = f" / 前日比 {it['chg']:+,}円" if it.get("chg") else ""
    if len(hpts) >= 2:
        hist_html = (f'<section><h2>買取価格の推移</h2>{spark_svg(hpts)}'
                     f'<p class="hm">{e(hpts[0][0])} 〜 {e(hpts[-1][0])}：最高 {yen(max(hv))} / 最低 {yen(min(hv))}'
                     f'{chg_txt}</p></section>')
    rel_html = ""
    if related:
        rel_html = "<section><h2>関連商品の買取価格</h2><ul class=\"rel\">" + "".join(
            f'<li><a href="/p/{r["_slug"]}/">{e(r["name"])}</a><b>{yen(r["best"])}</b></li>' for r in related) + "</ul></section>"
    body = f"""<nav class="bc"><a href="/">トップ</a> › <a href="/c/{cat}/">{e(CAT_JA.get(cat, cat))}</a> › {e(name)}</nav>
<h1>{e(name)} 買取価格比較</h1>
<div class="sum"><div><span class="lb">最高買取価格</span><b class="big">{yen(it['best'])}</b><span class="sh">{e(best_name)}</span></div>
{f'<div class="gap">売る店で最大 <b>{yen(gap)}</b> の差</div>' if gap > 0 else ''}</div>
<p class="lead">{e(name)}（新品・未開封）の買取価格を大手買取店{it['n_shops']}店で比較しました。価格は高い順です。</p>
<table class="pt"><thead><tr><th>買取店</th><th>買取価格</th><th>差額</th></tr></thead><tbody>{''.join(trs)}</tbody></table>
<p class="upd">最終更新：{e(updated)} JST（毎時自動更新）</p>
{hist_html}
{buy_html(it, name)}
<p class="cta"><a href="/?q={e(series_of(name))}">「{e(series_of(name))}」の全モデルを比較する →</a></p>
{rel_html}
<section class="vi" lang="vi"><h2>Tiếng Việt</h2><p>Giá thu mua <b>{e(name)}</b> (hàng mới, chưa mở hộp) tại {it['n_shops']} tiệm kaitori ở Nhật. Cao nhất: <b>{yen(it['best'])}</b> tại {e(best_name)}{f", chênh lệch giữa các tiệm tới {yen(gap)}" if gap > 0 else ""}. Cập nhật mỗi giờ.</p></section>"""
    ld = [crumbs([("トップ", "/"), (CAT_JA.get(cat, cat), f"/c/{cat}/"), (name, f"/p/{it['_slug']}/")])]
    return page(title, desc, f"/p/{it['_slug']}/", body, ld, updated)


def cat_page(cat: str, its: list, n_all: int, updated: str) -> str:
    label = CAT_JA.get(cat, cat)
    title = f"{label}の買取価格比較｜大手買取店を毎時比較 - {BRAND}"
    top = its[0] if its else None
    desc = (f"{label}の新品買取価格を大手買取店で一括比較。{len(its)}商品の最高買取価格と店舗間の差額を毎時更新。"
            + (f"例：{top['name']} 最高{yen(top['best'])}。" if top else ""))
    groups: dict[str, list] = {}
    for it in its:
        groups.setdefault(series_of(it["name"]) or it["name"], []).append(it)
    secs = []
    for g, lst in groups.items():
        lis = "".join(f'<li><a href="/p/{i["_slug"]}/">{e(i["name"])}</a><b>{yen(i["best"])}</b><small>{i["n_shops"]}店</small></li>' for i in lst)
        secs.append(f"<section><h2>{e(g)}</h2><ul class=\"rel\">{lis}</ul></section>")
    body = f"""<nav class="bc"><a href="/">トップ</a> › {e(label)}</nav>
<h1>{e(label)}の買取価格比較</h1>
<p class="lead">{e(label)}（新品・未開封）{n_all:,}商品のうち、複数店で比較できる{len(its):,}商品の最高買取価格です。絞り込み・並び替えは<a href="/?c={cat}">比較ツール</a>で。</p>
<p class="upd">最終更新：{e(updated)} JST</p>
{''.join(secs)}"""
    ld = [crumbs([("トップ", "/"), (label, f"/c/{cat}/")])]
    return page(title, desc, f"/c/{cat}/", body, ld, updated)



VI_TITLE = "Kaitori Price｜So sánh giá thu mua iPhone, máy game, thẻ Pokémon ở Nhật"
VI_DESC = ("So sánh giá thu mua hàng mới (chưa mở hộp) tại 9 tiệm kaitori lớn ở Nhật, cập nhật mỗi giờ: iPhone, PS5, Switch, "
           "hộp thẻ Pokémon, máy ảnh. Biết ngay tiệm nào trả cao nhất trước khi bán. Miễn phí.")


def build_vi():
    """/vi/: bản trang chủ có tiêu đề/mô tả/ảnh xem trước tiếng Việt (Facebook, Zalo không chạy JS nên cần HTML riêng)."""
    s = (SITE / "index.html").read_text(encoding="utf-8")
    rep = [(r"<html lang=\"[a-z]+\">", '<html lang="vi">'),
           (r"<title>[^<]*</title>", f"<title>{e(VI_TITLE)}</title>"),
           (r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{BASE}/vi/">'),
           (r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{BASE}/vi/">'),
           (r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{e(VI_TITLE)}">'),
           (r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{e(VI_DESC)}">'),
           (r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{e(VI_DESC)}">')]
    for a, b in rep:
        s, n = re.subn(a, lambda m, b=b: b, s, count=1)
        assert n == 1, a
    s = s.replace("<head>", '<head>\n<base href="/">', 1)  # file css/js/ảnh dùng đường dẫn tương đối → lấy từ gốc
    s = s.replace('<meta property="og:type" content="website">',
                  '<meta property="og:type" content="website">\n<meta property="og:locale" content="vi_VN">', 1)
    out = SITE / "vi"
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(s, encoding="utf-8")


def build() -> int:
    idx = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    shops, updated = idx.get("shops", {}), idx.get("updated", "")
    all_items: dict[str, list] = {}
    for d in ("p", "c", "guide"):
        shutil.rmtree(SITE / d, ignore_errors=True)
    urls: list[tuple[str, str]] = []
    lastmod = (updated or datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d"))[:10]
    n_pages = 0
    cats_present = []
    seen: set[str] = set()
    for cat in CAT_ORDER:
        fp = DATA / "cat" / f"{cat}.json"
        if not fp.exists():
            continue
        items = json.loads(fp.read_text(encoding="utf-8"))
        all_items[cat] = items
        hp = DATA / "hist" / f"{cat}.json"
        hist = json.loads(hp.read_text(encoding="utf-8")) if hp.exists() else {}
        its = [i for i in items if i.get("n_shops", len(i["prices"])) >= MIN_SHOPS]
        for it in its:
            s = slug(it["key"], it["name"])
            while s in seen:
                s += "x"
            seen.add(s)
            it["_slug"] = s
        by_series: dict[str, list] = {}
        for it in its:
            by_series.setdefault(series_of(it["name"]), []).append(it)
        for it in its:
            rel = [r for r in by_series.get(series_of(it["name"]), []) if r is not it][:10]
            out = SITE / "p" / it["_slug"]
            out.mkdir(parents=True, exist_ok=True)
            (out / "index.html").write_text(product_page(it, shops, hist.get(it["key"], []), rel, updated), encoding="utf-8")
            urls.append((f"/p/{it['_slug']}/", "daily"))
            n_pages += 1
        if its:
            cats_present.append((cat, len(its)))
            out = SITE / "c" / cat
            out.mkdir(parents=True, exist_ok=True)
            (out / "index.html").write_text(cat_page(cat, its, len(items), updated), encoding="utf-8")
    from . import guides
    try:  # ảnh giá + bài viết sẵn cho Facebook (/share/), cần Pillow + font
        from . import share
        print("share images:", share.build(all_items, SITE, updated))
    except Exception as exc:  # noqa: BLE001
        print("share skipped:", exc)
    urls += guides.build(all_items, shops, updated, page, e, SITE, BASE)
    build_vi()
    head = [("/", "hourly"), ("/vi/", "hourly")] + [(f"/c/{c}/", "hourly") for c, _ in cats_present] + [("/?v=deals", "daily")]
    nl = "\n"
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"  <url><loc>{html.escape(BASE + u)}</loc><lastmod>{lastmod}</lastmod><changefreq>{f}</changefreq></url>" for u, f in head + urls]
    sm.append("</urlset>")
    (SITE / "sitemap.xml").write_text(nl.join(sm) + nl, encoding="utf-8")
    llms = [f"# {BRAND} (kaitoriprice.com)", "",
            "> 日本の大手買取店（新品・未開封）の買取価格を毎時自動取得して比較するサイト。"
            "iPhone・スマホ、ゲーム機、カメラ、ポケカBOX、家電など。ベトナム語/日本語対応。", "",
            "Japanese buyback (kaitori) price comparison for new, sealed products across major shops in Japan, updated hourly.", "",
            "## カテゴリ別 買取価格比較", ""]
    llms += [f"- [{CAT_JA[c]}の買取価格比較]({BASE}/c/{c}/): {n:,}商品" for c, n in cats_present]
    llms += ["", "## 注意", "", "- 価格は各店舗の公開ページから自動取得した参考値です。実際の買取額は各店舗でご確認ください。", ""]
    (SITE / "llms.txt").write_text(nl.join(llms), encoding="utf-8")
    print("pages:", n_pages, "categories:", len(cats_present), "sitemap urls:", len(head) + len(urls))
    return 0


if __name__ == "__main__":
    sys.exit(build())
