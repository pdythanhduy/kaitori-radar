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


def _row(shop, cat, name, price, url, note=""):
    return {"shop": shop, "cat": cat, "name": name, "key": make_key(cat, name), "price": price, "url": url, "note": note}


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
        out.append({"url": MM + nm.group(1), "name": _clean(nm.group(2)), "cond": _clean(rk.group(1)) if rk else "",
                    "price": int(pr.group(1).replace(",", ""))})
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
            rows.append(_row("morimori", cat, name, x["price"], x["url"]))
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
    if re.search(r"カメラ|EOS|α|LUMIX|Z ?\d|GoPro|ILCE|DJI", name, re.I):
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


SHOPS = {
    "morimori": {"name": "森森買取", "url": MM, "fn": morimori_scope, "scopes": MM_SCOPES, "hot": MM_HOT},
    "mobile_ichiban": {"name": "モバイル一番", "url": MI, "fn": mobile_ichiban_scope, "scopes": MI_SCOPES, "hot": MI_HOT},
    "homura": {"name": "買取ホムラ", "url": "https://kaitori-homura.com", "fn": homura_scope, "scopes": ["box"], "hot": ["box"]},
}
