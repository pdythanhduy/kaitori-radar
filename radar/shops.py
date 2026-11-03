"""Scrapers cho các tiệm thu mua (買取).

Mỗi tiệm chia thành nhiều "scope" (nhóm trang). Mỗi scope trả về list dict:
  {shop, cat, name, key, price, url, note}
Chỉ lấy giá hàng MỚI (新品/未開封) — đúng nhu cầu mua mới → bán cho 買取店.
Lịch sự với máy chủ: nghỉ DELAY giây giữa các request.
"""
from __future__ import annotations

import html
import re
import time

import requests

from .normalize import make_key

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/130 Safari/537.36 kaitori-radar/0.2"}
DELAY = 1.8


def _get(sess, url):
    r = sess.get(url, headers=UA, timeout=40)
    r.raise_for_status()
    time.sleep(DELAY)
    return r.text


def _clean(s: str) -> str:
    return html.unescape(" ".join(re.sub(r"<[^>]+>", " ", s).split()))


def _row(shop, cat, name, price, url, note="", jan=None):
    return {"shop": shop, "cat": cat, "name": name, "key": make_key(cat, name), "price": price, "url": url, "note": note,
            "jan": jan}


# ================================================================== 森森買取
MM = "https://www.morimori-kaitori.jp"
MM_SCOPES = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "12", "13", "14", "15", "16", "18", "19", "24",
             "27", "31", "99"]
MM_HOT = ["0301", "0101", "0104", "2401010", "2401001"]
_MM_CAT = [("0112", "card"), ("01", "game"), ("02", "pc"), ("0301", "phone"), ("0304", "phone"), ("03", "other"),
           ("04", "tablet"), ("05", "camera"), ("0602", "audio"), ("06", "appliance"), ("10", "watch"), ("19", "hobby"),
           ("31", "hobby"), ("24", "card")]
_MM_NEW = {"新品", "未開封", "未使用", "新品未開封", ""}


def _mm_cat(url: str) -> str:
    m = re.search(r"/category/(\d+)/", url)
    leaf = m.group(1) if m else ""
    for pre, cat in _MM_CAT:
        if leaf.startswith(pre):
            return cat
    return "other"


def _mm_parse(s):
    out = []
    for blk in s.split('class="mm1551-prow__info"')[1:]:
        nm = re.search(r'mm1551-prow__name">\s*<a href="([^"]+)">(.*?)</a>', blk, re.S)
        pr = re.search(r'mm1551-prow__cur-val">([\d,]+)', blk)
        if not (nm and pr):
            continue
        rk = re.search(r'class="rk">(.*?)</span>', blk)
        jan = re.search(r"JAN:(\d{8,14})", blk)
        out.append({"url": MM + nm.group(1), "name": _clean(nm.group(2)), "cond": _clean(rk.group(1)) if rk else "",
                    "price": int(pr.group(1).replace(",", "")), "jan": jan.group(1) if jan else None})
    return out


def morimori_scope(sess, cid, max_pages=250):
    rows, seen = [], set()
    for p in range(1, max_pages + 1):
        s = _get(sess, f"{MM}/category/{cid}" + (f"?page={p}" if p > 1 else ""))
        new = [x for x in _mm_parse(s) if x["url"] not in seen]
        if not new:
            break
        for x in new:
            seen.add(x["url"])
            if x["cond"] not in _MM_NEW or x["price"] <= 0:
                continue
            cat = _mm_cat(x["url"])
            name = x["name"]
            if cat == "phone" and "iPhone" in name and "SIMフリー" not in name.replace("SIMﾌﾘｰ", "SIMフリー"):
                continue  # iPhone: chỉ so bản SIMフリー
            rows.append(_row("morimori", cat, name, x["price"], x["url"], jan=x["jan"]))
        if f"page={p + 1}" not in s:
            break
    return rows


# ================================================================== モバイル一番
MI = "https://www.mobile-ichiban.com"
MI_SCOPES = ["1", "2", "3"]          # 1=スマホ(新品), 2=家電・ゲーム, 3=おもちゃ(ポケカ) ; 4=中古 bỏ qua
MI_HOT = ["1", "3"]


def _mi_cards(s):
    out = []
    for c in s.split('<div class="card" style="flex-direction: row')[1:]:
        titles = [html.unescape(t).strip() for t in re.findall(r'title="([^"]*)" style="height:21px">', c)]
        price = re.search(r'id="NewPrice_[^"]+">\s*([\d,]+)円', c)
        remark = re.search(r'my-prod-remarks"[^>]*>(.*?)</small>', c, re.S)
        if titles and price:
            out.append({"t1": titles[0], "t2": titles[1] if len(titles) > 1 else "",
                        "price": int(price.group(1).replace(",", "")), "remark": _clean(remark.group(1)) if remark else ""})
    return out


def _mi_cat(kid, name):
    if kid == "1":
        return "phone"
    if kid == "3":
        return "card" if re.search(r"BOX|カード", name) else "hobby"
    if re.search(r"PlayStation|Nintendo|Switch|Xbox|PSVR|ROG Ally|Steam|Meta Quest|PS5|PS4", name, re.I):
        return "game"
    if re.search(r"iPad|タブレット|Galaxy Tab", name, re.I):
        return "tablet"
    if re.search(r"MacBook|Surface|ノートPC|パソコン", name, re.I):
        return "pc"
    if re.search(r"Apple Watch|ウォッチ", name, re.I):
        return "watch"
    if re.search(r"AirPods|イヤホン|ヘッドホン|スピーカー|WH-|WF-", name, re.I):
        return "audio"
    if re.search(r"カメラ|EOS|α|LUMIX|Z ?\d|GoPro|ILCE|DJI|\d+(-\d+)?\s?mm|F\d(\.\d)?|SIGMA|TAMRON|Insta360", name, re.I):
        return "camera"
    return "appliance"


def mobile_ichiban_scope(sess, kid, max_pages=150):
    first = _get(sess, f"{MI}/Prod/{kid}")
    tok = re.search(r"fromPager=([^\"&]+)", first)
    pages = int(re.search(r'data-pagecount="(\d+)"', first).group(1)) if "data-pagecount" in first else 1
    f = first.find('id="G01_ProdutShow_searchForm"')
    form = {}
    for m in re.finditer(r"<input[^>]+>", first[f:first.find("</form>", f)]):
        n, v = re.search(r'name="([^"]+)"', m.group(0)), re.search(r'value="([^"]*)"', m.group(0))
        if n:
            form[n.group(1)] = html.unescape(v.group(1)) if v else ""
    cards = _mi_cards(first)
    hdr = dict(UA, **{"X-Requested-With": "XMLHttpRequest", "Referer": f"{MI}/Prod/{kid}"})
    for p in range(2, min(pages, max_pages) + 1):
        if not tok:
            break
        r = sess.post(f"{MI}/G01_ProdutShow/Index/{p}?kid={kid}&fromPager={tok.group(1)}", data=form, headers=hdr, timeout=40)
        time.sleep(DELAY)
        got = _mi_cards(r.text)
        if not got:
            break
        cards += got
    rows = []
    for c in cards:
        if kid == "1":
            if "未開封" not in c["t2"]:
                continue  # chỉ hàng mới chưa khui
            if c["t1"].startswith("iPhone") and "simfree" not in c["t2"].lower():
                continue  # iPhone: chỉ so bản SIMフリー
            name = c["t1"]
        else:
            name = (c["t1"] + " " + c["t2"]).strip()
        rows.append(_row("mobile_ichiban", _mi_cat(kid, name), name, c["price"], f"{MI}/Prod/{kid}", c["remark"]))
    return rows


# ================================================================== 買取ホムラ (bảng giá BOX, cập nhật mỗi ngày)
HOMURA_TABLE = "https://kaitori-homura.com/column/2026/10/21/pokemon-box-buyback-price-list/"


def homura_scope(sess, _scope="box"):
    s = _get(sess, HOMURA_TABLE)
    rows = []
    for t in re.findall(r"<table.*?</table>", s, re.S):
        for row in re.findall(r"<tr.*?</tr>", t, re.S):
            cells = [_clean(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
            if len(cells) < 3 or cells[1] in ("BOX", ""):
                continue
            m = re.search(r"([\d,]+)円", cells[2])
            if not m:
                continue
            link = re.search(r'href="(https://kaitori-homura\.com/products/\d+)"', row)
            name = cells[1].replace(" ", "") + " BOX"
            rows.append(_row("homura", "card", name, int(m.group(1).replace(",", "")),
                             link.group(1) if link else HOMURA_TABLE,
                             ("シュリンク無し " + cells[3]) if len(cells) > 3 else ""))
    return rows


# ================================================================== 買取ルデヤ (robots: Allow /)
RD = "https://kaitori-rudeya.com"
RD_HOT = ["255", "253", "254", "220", "219", "221", "218", "232", "214", "1", "2", "114"]


def _rd_cat(cat_name, name):
    t = cat_name + " " + name
    if re.search(r"PSA\s?10|ポケモンカード|ポケカ|遊戯王|ONE PIECE|ワンピース.*カード|デュエル|TCG|トレカ|拡張パック", t, re.I):
        return "card"
    if re.search(r"iPhone", name, re.I):
        return "phone"
    if re.search(r"スマートフォン|携帯電話", cat_name):
        return "phone"
    if re.search(r"iPhone|Google|Pixel|OPPO|Motorola|SHARP|AQUOS|Xperia|SAMSUNG|Galaxy|FCNT|arrows|スマホ", t, re.I):
        return "tablet" if re.search(r"iPad|Tab", t) else "phone"
    if re.search(r"ポケモンカード|ワンピースカード|ドラゴンボールカード|遊戯王|トレカ", t):
        return "card"
    if re.search(r"\d+(-\d+)?\s?mm|F\d(\.\d)?|一眼|ミラーレス|EOS|LUMIX|FUJIFILM|富士フイルム|ニコン|Nikon|ILCE|SIGMA|TAMRON|OM SYSTEM|ハッセルブラッド|GoPro|Insta360|DJI|instax|チェキ", t, re.I):
        return "camera"
    if re.search(r"Switch|PlayStation|Xbox|Steam|ROG|Meta Quest|PSVR|ゲーム", t, re.I):
        return "game"
    if re.search(r"iPad|Kindle|タブレット", t, re.I):
        return "tablet"
    if re.search(r"カメラ|レンズ|チェキ", t):
        return "camera"
    if re.search(r"AirPods|WF-|WH-|イヤホン|ヘッドホン|スピーカー|オーディオ", t, re.I):
        return "audio"
    if re.search(r"Apple Watch|ウォッチ|腕時計", t, re.I):
        return "watch"
    if re.search(r"MacBook|パソコン|PC", t):
        return "pc"
    if re.search(r"フィギュア|プラモ|ホビー|おもちゃ", t):
        return "hobby"
    return "appliance"


def _rd_parse(s, cat_name):
    out = []
    for blk in s.split('<article class="pgrid-card"')[1:]:
        cond = re.search(r'product-card-cond-badge[^"]*">([^<]+)<', blk)
        nm = re.search(r'product-card-name-link" href="([^"]+)">(.*?)</a>', blk, re.S)
        pr = re.search(r'product-card-price-value">([\d,]+)', blk)
        if not (nm and pr):
            continue
        if cond and cond.group(1).strip() not in ("新品", "未開封", "未使用"):
            continue
        jan = re.search(r"JAN:\s*(\d{8,14})", blk)
        memo = re.search(r'product-card-memo">(.*?)</span>', blk, re.S)
        name = _clean(nm.group(2))
        out.append(_row("rudeya", _rd_cat(cat_name, name), name, int(pr.group(1).replace(",", "")), nm.group(1),
                        _clean(memo.group(1))[:40] if memo else "", jan.group(1) if jan else None))
    return out


def rudeya_scope(sess, scope):
    if scope == "hot":
        ids = RD_HOT
    else:
        sm = _get(sess, f"{RD}/sitemap.xml")
        ids = sorted(set(re.findall(r"/category/detail/(\d+)", sm)), key=int)
    rows, seen = [], set()
    for cid in ids:
        try:
            s = _get(sess, f"{RD}/category/detail/{cid}")
        except Exception as exc:  # noqa: BLE001
            print(f"  rudeya {cid}: {exc}")
            continue
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
        for r in _rd_parse(s, _clean(h1.group(1)) if h1 else ""):
            if r["url"] not in seen:
                seen.add(r["url"])
                rows.append(r)
    return rows


_JAN_RE = re.compile(r"(?<!\d)(45\d{11}|49\d{11}|0\d{12}|\d{13})(?!\d)")


def _jan_in(text):
    m = _JAN_RE.search(text or "")
    return m.group(1) if m else None


# ================================================================== PANDA買取 (robots: chỉ cấm /wp-admin, /link)
PD = "https://panda-kaitori.co.jp"
PD_HOT = ["iphone", "game", "nintendo", "playstation"]


def panda_scope(sess, scope):
    if scope == "hot":
        slugs = PD_HOT
    else:
        home = _get(sess, f"{PD}/?cpro=game")
        slugs = sorted(set(re.findall(r"cpro=([a-z0-9_-]+)", home)))
    rows, seen = [], set()
    for slug in slugs:
        for p in range(1, 40):
            s = _get(sess, f"{PD}/?cpro={slug}" + (f"&nowpage={p}" if p > 1 else ""))
            got = 0
            for tr in re.findall(r"<tr>\s*<td class=\"tb-var\">.*?</tr>", s, re.S):
                jan = re.search(r'tb-var"><span>(\d*)</span>', tr)
                nm = re.search(r'product-name">(.*?)</div>', tr, re.S)
                pr = re.search(r"<ins>¥([\d,]+)</ins>", tr)
                if not (nm and pr):
                    continue
                name = _clean(nm.group(1))
                boost = name.startswith("強化")  # PANDA ghi "強化" (đang thu mạnh) ở đầu tên
                name = re.sub(r"^強化\s*", "", name)
                k = (jan.group(1) if jan else "", name)
                got += 1
                if k in seen:
                    continue
                seen.add(k)
                rows.append(_row("panda", _rd_cat(slug, name), name, int(pr.group(1).replace(",", "")),
                                 f"{PD}/?cpro={slug}", "", (jan.group(1) or None) if jan else None))
                if boost:
                    rows[-1]["boost"] = True
            if not got or f"nowpage={p + 1}" not in s:
                break
    return rows


# ================================================================== ゲストモバイル (WordPress, bảng giá)
GM = "https://www.guestmobile.jp"


def guestmobile_scope(sess, scope):
    home = _get(sess, GM + "/")
    pages = sorted(set(u for u in re.findall(r'href="(https://www\.guestmobile\.jp/[^"#?]+/)"', home)
                       if "%e8%b2%b7%e5%8f%96%e4%be%a1%e6%a0%bc" in u.lower()  # "買取価格"
                       and "%e4%b8%ad%e5%8f%a4" not in u.lower()             # bỏ trang "中古"
                       and "/category/" not in u))
    pages.append(GM + "/%e3%83%94%e3%83%83%e3%82%af%e3%82%a2%e3%83%83%e3%83%97%e8%b2%b7%e5%8f%96%e6%a9%9f%e7%a8%ae/")  # ピックアップ
    if scope == "hot":
        pages = [u for u in pages if "iphone" in u.lower()] or pages[:3]
    rows, seen = [], set()
    for u in pages:
        s = _get(sess, u)
        for tb in re.findall(r"<table.*?</table>", s, re.S):
            trs = re.findall(r"<tr.*?</tr>", tb, re.S)
            hcol, hlen = None, 0
            for tr in trs:
                cells = [_clean(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
                if not any(re.search(r"\d円", c) for c in cells):  # dòng tiêu đề (không có giá)
                    for i, c in enumerate(cells):
                        if "未開封" in c or "未使用" in c or c == "新品":
                            hcol, hlen = i, len(cells)
                            break
                    continue
                if hcol is None:
                    continue
                col = hcol + max(0, len(cells) - hlen)  # tiêu đề thường thiếu cột ghi chú
                if len(cells) <= col:
                    continue
                m = re.search(r"([\d,]{3,})\s*円", cells[col])
                if not m or not cells[0]:
                    continue
                name = cells[0]
                if name in seen:
                    continue
                seen.add(name)
                note = cells[1][:40] if col > 1 else ""
                rows.append(_row("guestmobile", _rd_cat("", name), name, int(m.group(1).replace(",", "")), u, note,
                                 _jan_in(name)))
    return rows


# ================================================================== 買取当番 (WooCommerce Store API công khai)
TB = "https://tobansyoji.co.jp"


def toban_scope(sess, scope):
    rows = []
    for p in range(1, 60):
        r = sess.get(f"{TB}/wp-json/wc/store/v1/products", params={"per_page": 100, "page": p}, headers=UA, timeout=40)
        time.sleep(DELAY)
        if r.status_code != 200:
            break
        items = r.json()
        if not items:
            break
        for it in items:
            pr = it.get("prices") or {}
            rng = pr.get("price_range") or {}
            val = rng.get("max_amount") or pr.get("price")
            try:
                price = int(val) // (10 ** int(pr.get("currency_minor_unit", 0)))
            except (TypeError, ValueError):
                continue
            if price <= 0:
                continue
            name = html.unescape(it.get("name", ""))
            desc = _clean(it.get("description", "") + " " + it.get("short_description", ""))
            if "中古" in desc and "新品" not in desc:
                continue
            cats = " ".join(c.get("name", "") for c in it.get("categories", []))
            rows.append(_row("toban", _rd_cat(cats, name), name.replace("来店専用", "").strip(), price,
                             it.get("permalink", TB), "来店専用" if "来店専用" in name else "", _jan_in(desc) or _jan_in(name)))
        if len(items) < 100:
            break
    return rows


# ================================================================== ケータイゴッド (bảng danh sách 20 máy/trang)
KG = "https://keitai-god.com"
KG_HOT = ["1", "8"]


def keitaigod_scope(sess, scope):
    if scope == "hot":
        cis = KG_HOT
    else:
        idx = _get(sess, f"{KG}/price/index.php")
        cis = sorted(set(re.findall(r'index\.php\?ci=(\d+)"', idx)), key=int)
    rows, seen = [], set()
    for ci in cis:
        for p in range(1, 80):
            s = _get(sess, f"{KG}/price/index.php?ci={ci}" + (f"&page={p}" if p > 1 else ""))
            tb = re.search(r'id="price_table">(.*?)</table>', s, re.S)
            if not tb:
                break
            got = 0
            for tr in re.findall(r"<tr>(.*?)</tr>", tb.group(1), re.S):
                tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
                if len(tds) < 3:
                    continue
                name = _clean(tds[1])
                m = re.search(r"([\d,]+)円", tds[2])
                link = re.search(r'href="([^"]+model\.php\?moid=\d+)"', tr)
                if not m:
                    continue
                got += 1
                url = link.group(1) if link else f"{KG}/price/index.php?ci={ci}"
                if url in seen:
                    continue
                seen.add(url)
                jan = _jan_in(name)
                clean_name = _JAN_RE.sub("", name).strip()
                rows.append(_row("keitaigod", _rd_cat("", clean_name), clean_name, int(m.group(1).replace(",", "")), url,
                                 "新品上限", jan))
            if not got or f"page={p + 1}&" not in s:
                break
    return rows


# ================================================================== 買取1丁目 (SPA, JSON công khai mà trang web tự gọi)
IC = "https://www.1-chome.com"
# (cateCode, danh mục của mình, loại API). "other" → refine_cat tự xếp (MacBook→pc, iPad→tablet, AirPods→audio…)
IC_CATES = {"iphone": ("RGNg976kptBN7UjF", "phone", "keitai"), "android": ("WkCcKCxwC6NInC5c", "phone", "keitai"),
            "apple": ("20748358", "other", "goods"), "camera": ("10000001", "camera", "goods"),
            "card": ("4IE7zlA4XkiWSxy8", "card", "goods"), "earphone": ("10000004", "audio", "goods"),
            "game": ("10000005", "game", "goods"), "tablet": ("20030016", "tablet", "goods")}
_IC_OK = re.compile(r"未開封|新品|箱付|シュリンク")
_IC_BAD = re.compile(r"開封済|中古|箱な|シュリンクな|難あり|ジャンク")


def ichome_scope(sess, scope):
    import json as _json
    cates = ["iphone", "card", "game"] if scope == "hot" else list(IC_CATES)
    rows, seen = [], set()
    for c in cates:
        code, cat, api = IC_CATES[c]
        for page in range(1, 60):
            url = (f"{IC}/api/{api}/listPage?accCode=&page={page}&size=60&keyword=&isImpo=false&isCampaign=false"
                   f"&cateCode={code}&kbNames=&cateName=" + ("&isImpoCate=false" if api == "keitai" else ""))
            d = (_json.loads(_get(sess, url)).get("data") or {})
            content = d.get("content") or []
            for g in content:
                if _IC_BAD.search(g.get("kbName") or ""):
                    continue
                prices = [x.get("kbDetailPrice") or 0 for x in g.get("goodsKbDetails") or []
                          if _IC_OK.search(x.get("kbDetailName") or "") and not _IC_BAD.search(x.get("kbDetailName") or "")]
                price = max(prices or [0])
                if price <= 0:
                    continue
                link = f"{IC}/productDetail/{g['goodsId']}/{g.get('allGoodsKbId', '')}"
                if link in seen:
                    continue
                seen.add(link)
                jan = g.get("jan") or next((o.get("jan") for o in g.get("keitaiColorOptions") or [] if o.get("jan")), None)
                name = _clean(g.get("title") or "")
                note = _clean(g.get("kbDesc") or "")[:40]
                rows.append(_row("ichome", cat, name, int(price), link, note, jan))
                if g.get("impo"):  # 買取強化 (1丁目 tự đánh dấu đang thu mạnh)
                    rows[-1]["boost"] = True
                pp = [o.get("publicPrice") for o in g.get("keitaiColorOptions") or [] if o.get("publicPrice")]
                if pp:  # giá niêm yết Apple/nhà sản xuất (税込) — để tính "mua giá Apple bán kai lời bao nhiêu"
                    rows[-1]["msrp"] = int(min(pp))
            if page >= (d.get("totalPages") or 1) or not content:
                break
    return rows


# ================================================================== モバステ (株式会社パステック, 13 cửa hàng) — bảng giá HTML tĩnh
MS = "https://pastec.net"
MS_PAGES = {"iphone": "phone"}  # iPad: tiệm ghi số model A3355 dùng chung nhiều dung lượng → chưa ghép được với mã MDYL4J/A của tiệm khác


def _ms_note(t: str) -> str:
    """'グレイシャー -7,000(開封済・未開封)\\nブラック -9,000(…)' → 'グレイシャー-7,000/ブラック-9,000'"""
    t = re.sub(r"[（(][^)）]*[)）]", "", html.unescape(t or ""))
    parts = [re.sub(r"\s+", "", p) for p in re.split(r"[\n/]+", t) if p.strip()]
    return "/".join(parts)[:80]


def mobasute_scope(sess, scope):
    rows, seen = [], set()
    for page, cat in MS_PAGES.items():
        if scope == "hot" and page != "iphone":
            continue
        s = _get(sess, f"{MS}/{page}")
        for body in re.findall(r'<tr\s+id="device-\d+"[^>]*>(.*?)</tr>', s, re.S):
            nm = re.search(r'p-priceTable__name">\s*(?:<[^>]+>\s*)*<span>([^<]+)</span>', body)
            pr = re.search(r'price--unopened">\s*([\d,]+)\s*円', body)   # chỉ lấy giá 未開封 (máy mới chưa mở hộp)
            if not nm or not pr:
                continue
            name = _clean(nm.group(1))
            link = re.search(rf'href="({re.escape(MS)}/{page}/[^"?]+)', body)
            url = link.group(1) if link else f"{MS}/{page}"
            if url in seen:
                continue
            seen.add(url)
            cau = re.search(r'p-priceTable__caution[^"]*">(.*?)</div>', body, re.S)
            rows.append(_row("mobasute", cat, name, int(pr.group(1).replace(",", "")), url, _ms_note(cau.group(1) if cau else "")))
    return rows


SHOPS = {
    "morimori": {"name": "森森買取", "url": MM, "fn": morimori_scope, "scopes": MM_SCOPES, "hot": MM_HOT},
    "rudeya": {"name": "買取ルデヤ", "url": RD, "fn": rudeya_scope, "scopes": ["full"], "hot": ["hot"]},
    "panda": {"name": "PANDA買取", "url": PD, "list": True, "fn": panda_scope, "scopes": ["full"], "hot": ["hot"]},
    "guestmobile": {"name": "ゲストモバイル", "url": GM, "list": True, "fn": guestmobile_scope, "scopes": ["full"], "hot": ["hot"]},
    "toban": {"name": "買取当番", "url": TB, "fn": toban_scope, "scopes": ["full"], "hot": ["hot"]},
    "keitaigod": {"name": "ケータイゴッド", "url": KG, "fn": keitaigod_scope, "scopes": ["full"], "hot": ["hot"]},
    "mobile_ichiban": {"name": "モバイル一番", "url": MI, "list": True, "fn": mobile_ichiban_scope, "scopes": MI_SCOPES, "hot": MI_HOT},
    "ichome": {"name": "買取1丁目", "url": IC, "fn": ichome_scope, "scopes": ["full"], "hot": ["hot"]},
    # "mobasute": {"name": "モバステ", "url": MS, "fn": mobasute_scope, "scopes": ["full"], "hot": ["hot"]},
    #   ↑ tắt 03/11/2026: pastec.net trả 403 cho máy chủ GitHub Actions (chặn truy cập tự động từ datacenter). Không lách.
    "homura": {"name": "買取ホムラ", "url": "https://kaitori-homura.com", "fn": homura_scope, "scopes": ["box"], "hot": ["box"]},
}
