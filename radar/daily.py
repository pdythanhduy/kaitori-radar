"""Bài "giá thu mua hôm nay" mỗi ngày (user 22/11/2026: viết bài mỗi ngày để người ta tìm Google ra web).

/tin/<YYYY-MM-DD>/   tiếng Việt  — "Giá kai hôm nay dd/mm/yyyy"
/news/<YYYY-MM-DD>/  tiếng Nhật  — "【yyyy年m月d日】本日の買取価格まとめ"
/tin/, /news/        danh sách ngày

Chỉ dùng số liệu thật: site/data/cat (giá hiện tại) + site/data/hist (giá cao nhất mỗi ngày, [ngày, giá, tiệm]).
Bài các ngày cũ sinh lại từ hist nên ổn định; bài hôm nay cập nhật mỗi lần build. Không dự đoán, không khuyên mua bán.
"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta

DAYS = 30  # số ngày giữ bài
HOT_PHONE = re.compile(r"^iPhone (Duo|18 Pro Max|18 Pro) (\d+)(GB|TB)$")


def _yen(n: int) -> str:
    return f"{n:,}円"


def _on(h: list, d: str):
    """(giá, tiệm) của ngày d (điểm cuối cùng ≤ d) và của ngày trước đó."""
    pts = [p for p in h if p[0] <= d]
    if not pts:
        return None, None
    cur = pts[-1] if pts[-1][0] == d else None
    prev = next((p for p in reversed(pts) if p[0] < d), None)
    return cur, prev


def _watch(all_items: dict) -> list:
    """Danh sách món hot cố định: iPhone 18 Pro/Pro Max/Duo, Switch 2, PS5 Pro, box Pokémon nhiều tiệm."""
    out = []
    ph = [i for i in all_items.get("phone", []) if HOT_PHONE.match(i["key"])]
    order = {"Duo": 0, "18 Pro Max": 1, "18 Pro": 2}

    def cap(i):
        m = HOT_PHONE.match(i["key"])
        return (order[m.group(1)], int(m.group(2)) * (1024 if m.group(3) == "TB" else 1))
    out += sorted(ph, key=cap)
    bad = re.compile(r"コントローラ|ケース|カバー|30周年|Controller|ソフト|パッケージ版")
    games = [i for i in all_items.get("game", []) if i.get("n_shops", 0) >= 3 and not bad.search(i["name"])]
    out += sorted([i for i in games if re.search(r"Switch ?2(?!\d)", i["name"])], key=lambda i: -i["best"])[:4]
    out += sorted([i for i in games if re.search(r"PlayStation ?5 Pro|PS5 Pro", i["name"])], key=lambda i: -i["n_shops"])[:2]
    bx = [i for i in all_items.get("card", []) if i["key"].startswith("box:") and i.get("n_shops", 0) >= 4
          and not re.search(r"(OP|EB|ST|PRB)-\d", i["name"])]  # chỉ box Pokémon
    out += sorted(bx, key=lambda i: -i["best"])[:12]
    return out


def _movers(all_items: dict, all_hist: dict, d: str, n: int = 6):
    ch = []
    for cat, items in all_items.items():
        h = all_hist.get(cat, {})
        for it in items:
            if it.get("n_shops", 0) < 3:
                continue
            cur, prev = _on(h.get(it["key"], []), d)
            if not cur or not prev or not prev[1]:
                continue
            dv = cur[1] - prev[1]
            pct = dv / prev[1]
            if abs(pct) > 0.4:  # lệch quá lớn: thường là lỗi ghép, bỏ
                continue
            if abs(dv) >= 3000 or abs(pct) >= 0.05:
                ch.append((pct, dv, it, cur))
    up = sorted([c for c in ch if c[1] > 0], key=lambda c: -c[0])[:n]
    dn = sorted([c for c in ch if c[1] < 0], key=lambda c: c[0])[:n]
    return up, dn


def build(all_items: dict, all_hist: dict, shops: dict, updated: str, page, e, site) -> list:
    today = (updated or str(date.today()))[:10]
    t0 = date.fromisoformat(today)
    first = min((p[0] for h in all_hist.values() for v in h.values() for p in v[:1]), default=today)
    days = [str(t0 - timedelta(days=k)) for k in range(DAYS) if str(t0 - timedelta(days=k)) >= first]
    watch = _watch(all_items)
    sname = lambda s: shops.get(s, {}).get("name", s)  # noqa: E731
    href = lambda it: f'/p/{it["_slug"]}/' if it.get("_slug") else None  # noqa: E731
    urls = []

    def rows_for(d, lang):
        rows, n_up, n_dn, big = [], 0, 0, []
        for it in watch:
            h = all_hist.get(it["cat"], {}).get(it["key"], [])
            cur, prev = _on(h, d)
            if d == today:
                price, shop = it["best"], it.get("best_shop", "")
            elif cur:
                price, shop = cur[1], (cur[2] if len(cur) > 2 else "")
            else:
                continue
            dv = price - prev[1] if prev else 0
            n_up += dv > 0
            n_dn += dv < 0
            if dv:
                big.append((abs(dv), dv, it))
            nm = e(it["name"])
            link = f'<a href="{href(it)}">{nm}</a>' if href(it) else nm
            img = f'<img src="{e(it["img"])}" alt="" width="40" height="41" loading="lazy" style="vertical-align:middle;margin-right:6px;object-fit:contain">' if it.get("img") else ""
            chg = (f'<b style="color:{"#15803d" if dv > 0 else "#b91c1c"}">{"▲" if dv > 0 else "▼"}{abs(dv):,}</b>' if dv
                   else "—")
            msrp = ""
            if d == today and it.get("msrp") and it["key"].startswith("iPhone"):
                g = price - it["msrp"]
                msrp = f'<br><small>Apple {"+" if g >= 0 else "−"}{abs(g):,}円</small>'
            rows.append(f"<tr><td>{img}{link}</td><td><b>{_yen(price)}</b>{msrp}<br><small>{e(sname(shop))}</small></td><td>{chg}</td></tr>")
        big.sort(key=lambda x: -x[0])
        return rows, n_up, n_dn, big[:3]

    def mv_list(lst, lang):
        if not lst:
            return f"<p>{'Không có món nào đổi ≥3.000円 hoặc ≥5%.' if lang == 'vi' else '3,000円以上・5%以上の変動はありませんでした。'}</p>"
        li = []
        for pct, dv, it, cur in lst:
            nm = e(it["name"])
            link = f'<a href="{href(it)}">{nm}</a>' if href(it) else nm
            li.append(f"<li>{link}: {_yen(cur[1] - dv)} → <b>{_yen(cur[1])}</b> ({'+' if dv > 0 else '−'}{abs(dv):,}円, {pct * 100:+.1f}%)</li>")
        return "<ul>" + "".join(li) + "</ul>"

    for lang, base in (("vi", "tin"), ("ja", "news")):
        idx = []
        for d in days:
            y, m, dd = d.split("-")
            rows, n_up, n_dn, big = rows_for(d, lang)
            if not rows:
                continue
            up, dn = _movers(all_items, all_hist, d)
            prev_d, next_d = str(date.fromisoformat(d) - timedelta(days=1)), str(date.fromisoformat(d) + timedelta(days=1))
            nav = " · ".join(x for x in [
                f'<a href="/{base}/{prev_d}/">← {prev_d[5:].replace("-", "/")}</a>' if prev_d in days else "",
                f'<a href="/{base}/">{"Tất cả các ngày" if lang == "vi" else "日付一覧"}</a>',
                f'<a href="/{base}/{next_d}/">{next_d[5:].replace("-", "/")} →</a>' if next_d in days else ""] if x)
            hot = ", ".join(f'{e(it["name"])} ({"+" if dv > 0 else "−"}{abs(dv):,}円)' for _, dv, it in big)
            if lang == "vi":
                title = f"Giá kai hôm nay {dd}/{m}/{y}: iPhone 18, Duo, Switch 2, box Pokémon | Kaitori Price"
                desc = f"Giá thu mua (kai) ngày {dd}/{m}/{y} ở 9 tiệm Nhật: iPhone 18 Pro/Pro Max, Duo, Switch 2, PS5 Pro, box Pokémon. {n_up} món tăng, {n_dn} món giảm so với hôm trước."
                h1 = f"Giá kai ngày {dd}/{m}/{y}"
                lead = (f"<p>Trong {len(rows)} món đang được quan tâm nhất, ngày {dd}/{m} có <b>{n_up} món tăng</b> và <b>{n_dn} món giảm</b> so với hôm trước"
                        + (f". Đổi nhiều nhất: {hot}." if hot else ".") + "</p>"
                        + ("<p class=\"small\">Bài hôm nay tự cập nhật mỗi giờ theo giá mới nhất.</p>" if d == today else ""))
                th = "<tr><th>Món</th><th>Giá thu cao nhất</th><th>So hôm trước</th></tr>"
                body = (f"{lead}<h2>Bảng giá các món hot</h2><div class=\"tw\"><table class=\"pt\"><thead>{th}</thead><tbody>{''.join(rows)}</tbody></table></div>"
                        f"<h2>Tăng mạnh trong ngày</h2>{mv_list(up, lang)}<h2>Giảm mạnh trong ngày</h2>{mv_list(dn, lang)}"
                        '<p class="cta"><a href="/vi/">Xem giá tất cả sản phẩm ở 9 tiệm →</a></p>'
                        '<p class="small">Giá là giá thu cao nhất công khai trên web các tiệm cho hàng mới chưa mở; giá thực tế có thể khác. '
                        "Không phải lời khuyên mua bán hay đầu tư.</p>"
                        f"<p>{nav}</p>")
                bc = f'<nav class="bc"><a href="/vi/">Trang chủ</a> › <a href="/tin/">Giá kai mỗi ngày</a> › {dd}/{m}</nav>'
            else:
                title = f"【{y}年{int(m)}月{int(dd)}日】本日の買取価格まとめ｜iPhone 18・Duo・Switch 2・ポケカBOX"
                desc = f"{y}年{int(m)}月{int(dd)}日の買取価格（新品・未開封）を大手買取店9社で比較。iPhone 18 Pro/Pro Max、iPhone Duo、Switch 2、PS5 Pro、ポケカBOX。前日比で{n_up}品目が上昇、{n_dn}品目が下落。"
                h1 = f"{y}年{int(m)}月{int(dd)}日の買取価格まとめ"
                lead = (f"<p>注目の{len(rows)}品目のうち、前日比で<b>{n_up}品目が上昇</b>、<b>{n_dn}品目が下落</b>しました"
                        + (f"。主な変動：{hot}。" if hot else "。") + "</p>"
                        + ("<p class=\"small\">本日の記事は最新価格で毎時自動更新されます。</p>" if d == today else ""))
                th = "<tr><th>商品</th><th>最高買取価格</th><th>前日比</th></tr>"
                body = (f"{lead}<h2>注目商品の買取価格</h2><div class=\"tw\"><table class=\"pt\"><thead>{th}</thead><tbody>{''.join(rows)}</tbody></table></div>"
                        f"<h2>値上がりした商品</h2>{mv_list(up, lang)}<h2>値下がりした商品</h2>{mv_list(dn, lang)}"
                        '<p class="cta"><a href="/">全商品の買取価格を比較する →</a></p>'
                        '<p class="small">各買取店の公開ページから自動取得した新品・未開封の最高買取価格です。実際の買取額は各店舗でご確認ください。</p>'
                        f"<p>{nav}</p>")
                bc = f'<nav class="bc"><a href="/">ホーム</a> › <a href="/news/">毎日の買取価格</a> › {int(m)}/{int(dd)}</nav>'
            ld = [{"@context": "https://schema.org", "@type": "Article", "headline": h1, "datePublished": d,
                   "dateModified": (updated[:10] if d == today else d), "inLanguage": lang,
                   "author": {"@type": "Organization", "name": "Kaitori Price"}}]
            pv = page(title, desc, f"/{base}/{d}/", f'{bc}<article class="guide" lang="{lang}"><h1>{e(h1)}</h1>{body}</article>', ld, updated)
            if lang == "vi":
                pv = pv.replace('<html lang="ja">', '<html lang="vi">', 1).replace(
                    '<a class="hd-cta" href="/">全商品を比較 →</a>', '<a class="hd-cta" href="/vi/">So giá 9 tiệm →</a>', 1)
            out = site / base / d
            out.mkdir(parents=True, exist_ok=True)
            (out / "index.html").write_text(pv, encoding="utf-8")
            urls.append((f"/{base}/{d}/", "hourly" if d == today else "monthly"))
            idx.append((d, n_up, n_dn))
        if not idx:
            continue
        if lang == "vi":
            li = "".join(f'<li><a href="/tin/{d}/">Giá kai ngày {d[8:]}/{d[5:7]}/{d[:4]}</a> — {u} tăng, {n} giảm</li>' for d, u, n in idx)
            body = f'<nav class="bc"><a href="/vi/">Trang chủ</a> › Giá kai mỗi ngày</nav><article class="guide" lang="vi"><h1>Giá kai mỗi ngày</h1><p>Bảng giá thu mua các món hot (iPhone 18, Duo, Switch 2, PS5 Pro, box Pokémon) ở 9 tiệm Nhật, mỗi ngày 1 bài.</p><ul>{li}</ul></article>'
            pv = page("Giá kai mỗi ngày – iPhone, Switch 2, box Pokémon | Kaitori Price",
                      "Bảng giá thu mua (kai) mỗi ngày ở 9 tiệm Nhật: iPhone 18, Duo, Switch 2, PS5 Pro, box Pokémon. Món nào tăng, món nào giảm.",
                      "/tin/", body, [], updated)
            pv = pv.replace('<html lang="ja">', '<html lang="vi">', 1).replace(
                '<a class="hd-cta" href="/">全商品を比較 →</a>', '<a class="hd-cta" href="/vi/">So giá 9 tiệm →</a>', 1)
        else:
            li = "".join(f'<li><a href="/news/{d}/">{d[:4]}年{int(d[5:7])}月{int(d[8:])}日の買取価格まとめ</a>（上昇{u}・下落{n}）</li>' for d, u, n in idx)
            body = f'<nav class="bc"><a href="/">ホーム</a> › 毎日の買取価格</nav><article class="guide" lang="ja"><h1>毎日の買取価格まとめ</h1><p>iPhone 18・Duo・Switch 2・PS5 Pro・ポケカBOXなど注目商品の買取価格を、大手買取店9社から毎日まとめています。</p><ul>{li}</ul></article>'
            pv = page("毎日の買取価格まとめ｜iPhone・Switch 2・ポケカBOX", "注目商品の買取価格を大手買取店9社から毎日まとめ。前日比の値上がり・値下がりも。",
                      "/news/", body, [], updated)
        (site / base).mkdir(parents=True, exist_ok=True)
        (site / base / "index.html").write_text(pv, encoding="utf-8")
        urls.insert(0, (f"/{base}/", "daily"))
    return urls
