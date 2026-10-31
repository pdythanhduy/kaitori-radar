"""Chuẩn hoá tên sản phẩm để ghép cùng một món giữa các tiệm.

Thứ tự ưu tiên tạo khoá (key):
  1. iPhone        -> "iPhone 18 Pro Max 256GB"
  2. Hộp ポケカ      -> box:<tên rút gọn>
  3. Số model      -> model:<CFI-7100B01>  (PS5, Switch, máy ảnh, PC... ghi giống nhau ở mọi tiệm)
  4. Tên rút gọn   -> name:<...>
"""
import re
import unicodedata

# ------------------------------------------------------------------ danh mục chung
CATS = {
    "phone": "スマホ", "tablet": "タブレット", "game": "ゲーム機", "card": "トレカ", "pc": "パソコン",
    "camera": "カメラ", "audio": "オーディオ", "appliance": "家電・美容", "watch": "腕時計", "hobby": "ホビー・フィギュア",
    "other": "その他",
}

_BOX_DROP = ["ポケモンカードゲーム", "ポケモンカード", "ポケモン", "ポケカ", "スカーレット&バイオレット", "ソード&シールド",
             "強化拡張パック", "拡張パック", "ハイクラスパック", "MEGA", "BOX", "ボックス", "シュリンク付き", "シュリンク付",
             "未開封", "新品"]


def box_key(name: str) -> str:
    s = unicodedata.normalize("NFKC", name)
    s = re.sub(r"[\[【(（][^\]】)）]*[\]】)）]", "", s)
    s = re.sub(r"\s+m\d+[a-z]?\s*$", "", s, flags=re.I)  # mã bản "m6a" ở cuối (モバイル一番)
    for w in _BOX_DROP:
        s = s.replace(w, "").replace(w.lower(), "")
    s = re.sub(r"[\s・･,、。!！?？\-ー―‐「」『』\"']", "", s).lower()
    s = re.sub(r"^カード(?=\d)", "", s)
    return s


_IP = re.compile(r"iPhone\s*(\d{1,2}e?|Air|Duo|SE)\s*(Pro\s*Max|ProMax|Pro|Plus|mini|Air)?", re.I)
_CAP = re.compile(r"(\d+)\s*(GB|TB)", re.I)


def iphone_key(name: str) -> str | None:
    s = unicodedata.normalize("NFKC", name)
    m, c = _IP.search(s), _CAP.search(s)
    if not (m and c):
        return None
    model = m.group(1).strip()
    model = {"air": "Air", "duo": "Duo", "se": "SE"}.get(model.lower(), model)
    sub = (m.group(2) or "").replace(" ", "").lower()
    sub = {"promax": " Pro Max", "pro": " Pro", "plus": " Plus", "mini": " mini", "air": " Air", "": ""}[sub]
    return f"iPhone {model}{sub} {c.group(1)}{c.group(2).upper()}"


# số model: chữ + số, có gạch nối, ví dụ CFI-7100B01, HEG-S-KAAAA, BEE-001, ILCE-7M4, WH-1000XM5, MacBook A2681
_MODEL = re.compile(r"(?<![A-Za-z0-9])([A-Z]{2,6}-[A-Z0-9]{2,10}(?:-[A-Z0-9]{1,8})*|[A-Z]{2,5}\d{3,5}[A-Z0-9]{0,6})(?![A-Za-z0-9])")
_MODEL_BAD = {"SIM", "USB", "LTE", "BOX", "HDMI", "OLED", "SSD", "HDD", "RAM", "ROM", "CPU", "GPU"}


def model_code(name: str) -> str | None:
    s = unicodedata.normalize("NFKC", name).upper()
    s = re.sub(r"\d+\s*(GB|TB|MB)", " ", s)
    cands = [c for c in _MODEL.findall(s) if c not in _MODEL_BAD and re.search(r"\d", c) and len(c) >= 5]
    return max(cands, key=len) if cands else None


def name_key(name: str) -> str:
    s = unicodedata.normalize("NFKC", name).lower()
    s = re.sub(r"[\[【(（][^\]】)）]*[\]】)）]", "", s)
    return re.sub(r"[^0-9a-zぁ-んァ-ヶ一-龠]", "", s)[:60]


def make_key(cat: str, name: str) -> str:
    if "iphone" in name.lower():
        k = iphone_key(name)
        if k:
            return k
    if cat == "card" and re.search(r"BOX|ボックス", name, re.I):
        return "box:" + box_key(name)
    mc = model_code(name)
    if mc:
        return "model:" + mc
    return "name:" + name_key(name)
