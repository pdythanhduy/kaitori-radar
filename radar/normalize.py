"""Chuẩn hoá tên sản phẩm để ghép cùng một món giữa các tiệm."""
import re
import unicodedata

_BOX_DROP = ["ポケモンカードゲーム", "ポケモンカード", "ポケモン", "ポケカ", "スカーレット&バイオレット", "ソード&シールド",
             "強化拡張パック", "拡張パック", "ハイクラスパック", "MEGA", "BOX", "ボックス", "シュリンク付き", "シュリンク付",
             "未開封", "新品"]


def box_key(name: str) -> str:
    s = unicodedata.normalize("NFKC", name)
    s = re.sub(r"[\[【(（][^\]】)）]*[\]】)）]", "", s)
    for w in _BOX_DROP:
        s = s.replace(w, "").replace(w.lower(), "")
    s = re.sub(r"[\s・･,、。!！?？\-ー―‐「」『』\"']", "", s).lower()
    s = re.sub(r"^カード(?=\d)", "", s)  # 「ポケモンカード151」 -> 151
    return s


_IP = re.compile(r"iPhone\s*(\d{1,2}e?|Air|Duo|SE\s*\(?第?\d?世代?\)?|SE)\s*(Pro\s*Max|ProMax|Pro|Plus|mini|Air)?", re.I)
_CAP = re.compile(r"(\d+)\s*(GB|TB)", re.I)


def iphone_key(name: str) -> str | None:
    s = unicodedata.normalize("NFKC", name)
    m, c = _IP.search(s), _CAP.search(s)
    if not (m and c):
        return None
    model = m.group(1).strip()
    model = {"air": "Air", "duo": "Duo"}.get(model.lower(), model)
    sub = (m.group(2) or "").replace(" ", "").lower()
    sub = {"promax": " Pro Max", "pro": " Pro", "plus": " Plus", "mini": " mini", "air": " Air", "": ""}[sub]
    return f"iPhone {model}{sub} {c.group(1)}{c.group(2).upper()}"
