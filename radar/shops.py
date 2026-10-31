"""Scrapers cho các tiệm thu mua (買取). Mỗi hàm trả về list dict:
{shop, cat, name, key, price, cond, url, jan, note}
cat: "pokebox" (ポケカ未開封BOX) | "iphone_new" (iPhone 新品未開封 SIMフリー)
Lịch sự với máy chủ: nghỉ 1.5–2s giữa các request, chỉ chạy vài lần/ngày.
"""
from __future__ import annotations

import html
import re
import time

import requests

from .normalize import box_key, iphone_key

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/130 Safari/537.36 kaitori-radar/0.1"}
DELAY = 1.8


def _get(sess, url, **kw):
    r = sess.get(url, headers=UA, timeout=40, **kw)
    r.raise_for_status()
    time.sleep(DELAY)
    return r.text


def _clean(s: str) -> str:
    return html.unescape(" ".join(re.sub(r"<[^>]+>", " ", s).split()))


# ------------------------------------------------------------------ 森森買取
MM = "https://www.morimori-kaitori.jp"


def _mm_parse(s):
    out = []
    for blk in s.split('class="mm1551-prow__info"')[1:]:
        nm = re.search(r'mm1551-prow__name">\s*<a href="([^"]+)">(.*?)</a>', blk, re.S)
        pr = re.search(r'mm1551-prow__cur-val">([\d,]+)', blk)
        if not (nm and pr):
            continue
        jan = re.search(r"JAN:(\d+)", blk)
        rk = re.search(r'class="rk">(.*?)</span>', blk)
        out.append({"url": MM + nm.group(1), "name": _clean(nm.group(2)), "jan": jan.group(1) if jan else None,
                    "cond": _clean(rk.group(1)) if rk else "", "price": int(pr.group(1).replace(",", ""))})
    return out


def _mm_category(sess, cat_id, max_pages=25):
    items, seen = [], set()
    for p in range(1, max_pages + 1):
        s = _get(sess, f"{MM}/category/{cat_id}" + (f"?page={p}" if p > 1 else ""))
        new = [x for x in _mm_parse(s) if x["url"] not in seen]
        if not new:
            break
        for x in new:
            seen.add(x["url"])
        items += new
        if f"page={p + 1}" not in s:
            break
    return items


def morimori(sess):
    res = []
    # ポケカ BOX: mục BOX + mục SV/SWSH (lọc những món có chữ BOX)
    for cid in ("2401010", "2401001", "2401002"):
        for x in _mm_category(sess, cid):
            if "BOX" not in x["name"].upper() or x["cond"] not in ("新品", ""):
                continue
            res.append({"shop": "morimori", "cat": "pokebox", "name": x["name"], "key": box_key(x["name"]),
                        "price": x["price"], "cond": "シュリンク付き", "url": x["url"], "jan": x["jan"], "note": ""})
    for x in _mm_category(sess, "0301"):
        if x["cond"] != "新品" or "SIMフリー" not in x["name"].replace("SIMﾌﾘｰ", "SIMフリー"):
            continue
        k = iphone_key(x["name"])
        if k:
            color = re.sub(r".*?\d+(GB|TB)\s*", "", x["name"]).replace("SIMフリー", "").strip()
            res.append({"shop": "morimori", "cat": "iphone_new", "name": x["name"], "key": k, "price": x["price"],
                        "cond": "新品未開封", "url": x["url"], "jan": x["jan"], "note": color})
    return res


# ------------------------------------------------------------------ モバイル一番
MI = "https://www.mobile-ichiban.com"


def _mi_cards(s):
    out = []
    for c in s.split('<div class="card" style="flex-direction: row')[1:]:
        titles = re.findall(r'title="([^"]*)" style="height:21px">', c)
        price = re.search(r'id="NewPrice_[^"]+">\s*([\d,]+)円', c)
        remark = re.search(r'my-prod-remarks"[^>]*>(.*?)</small>', c, re.S)
        if len(titles) >= 2 and price:
            out.append({"model": html.unescape(titles[0]).strip(), "cond": html.unescape(titles[1]).strip(),
                        "price": int(price.group(1).replace(",", "")),
                        "remark": _clean(remark.group(1)) if remark else ""})
    return out


def mobile_ichiban(sess):
    first = _get(sess, f"{MI}/Prod/1")
    tok = re.search(r"fromPager=([^\"&]+)", first)
    pages = int(re.search(r'data-pagecount="(\d+)"', first).group(1)) if 'data-pagecount' in first else 1
    f = first.find('id="G01_ProdutShow_searchForm"')
    form = {}
    for m in re.finditer(r"<input[^>]+>", first[f:first.find("</form>", f)]):
        n, v = re.search(r'name="([^"]+)"', m.group(0)), re.search(r'value="([^"]*)"', m.group(0))
        if n:
            form[n.group(1)] = html.unescape(v.group(1)) if v else ""
    cards = _mi_cards(first)
    hdr = dict(UA, **{"X-Requested-With": "XMLHttpRequest", "Referer": f"{MI}/Prod/1"})
    for p in range(2, min(pages, 60) + 1):
        r = sess.post(f"{MI}/G01_ProdutShow/Index/{p}?kid=1&fromPager={tok.group(1)}", data=form, headers=hdr, timeout=40)
        time.sleep(DELAY)
        got = _mi_cards(r.text)
        if not got:
            break
        cards += got
    res = []
    for c in cards:
        if not c["model"].startswith("iPhone") or "未開封" not in c["cond"] or "simfree" not in c["cond"].lower():
            continue
        k = iphone_key(c["model"])
        if k:
            res.append({"shop": "mobile_ichiban", "cat": "iphone_new", "name": c["model"], "key": k, "price": c["price"],
                        "cond": "新品未開封", "url": f"{MI}/Prod/1", "jan": None, "note": c["remark"]})
    return res


# ------------------------------------------------------------------ 買取ホムラ (bảng giá BOX cập nhật mỗi ngày)
HOMURA_TABLE = "https://kaitori-homura.com/column/2026/10/21/pokemon-box-buyback-price-list/"


def homura(sess):
    s = _get(sess, HOMURA_TABLE)
    res = []
    for t in re.findall(r"<table.*?</table>", s, re.S):
        for row in re.findall(r"<tr.*?</tr>", t, re.S):
            cells = [_clean(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
            if len(cells) < 3 or cells[1] in ("BOX", ""):
                continue
            m = re.search(r"([\d,]+)円", cells[2])
            if not m:
                continue
            link = re.search(r'href="(https://kaitori-homura\.com/products/\d+)"', row)
            name = cells[1].replace(" ", "")
            res.append({"shop": "homura", "cat": "pokebox", "name": name, "key": box_key(name),
                        "price": int(m.group(1).replace(",", "")), "cond": "シュリンク付き",
                        "url": link.group(1) if link else HOMURA_TABLE, "jan": None,
                        "note": ("シュリンク無し " + cells[3]) if len(cells) > 3 else ""})
    return res


SHOPS = {
    "morimori": {"name": "森森買取", "url": MM, "fn": morimori},
    "mobile_ichiban": {"name": "モバイル一番", "url": MI, "fn": mobile_ichiban},
    "homura": {"name": "買取ホムラ", "url": "https://kaitori-homura.com", "fn": homura},
}
