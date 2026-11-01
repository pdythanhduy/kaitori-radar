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
    if m and not c:
        # tiệm ghi thiếu đơn vị, vd PANDA "iPhone Duo 512" → hiểu là 512GB (chỉ các mức dung lượng chuẩn)
        b = re.match(r"\s*(64|128|256|512)(?![\dA-Za-z])", s[m.end():])
        if b:
            return iphone_key(s[: m.end()] + f" {b.group(1)}GB" + s[m.end() + b.end():])
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


_TOKEN = re.compile(r"[A-Z0-9][A-Z0-9.\-/]*[A-Z0-9]")
_NOT_MODEL = re.compile(r"^(\d+(GB|TB|MB|MM|W|V|HZ|K|P|CM|INCH|インチ)?|F\d[\d.\-]*|M\d|[A-Z]\d|20\d\d|\d+\.\d+)$")


def model_code(name: str) -> str | None:
    """Số model đầy đủ: lấy NGUYÊN token có cả chữ và số (giữ phần gạch nối), vd RF100-400MM, CFI-7100B01, ILCE-7M4.
    Trước đây chỉ lấy 'RF100' → mọi ống kính RF100-xxx bị gộp nhầm."""
    s = unicodedata.normalize("NFKC", name).upper()
    s = re.sub(r"[\[\]【】()（）「」\"'、,]", " ", s)
    cands = []
    for t in _TOKEN.findall(s):
        t = t.strip("-./")
        if len(t) < 5 or t in _MODEL_BAD or _NOT_MODEL.match(t):
            continue
        if not (re.search(r"[A-Z]", t) and re.search(r"\d", t)):
            continue
        cands.append(t)
    if not cands:
        return None
    # ưu tiên token có gạch nối (dạng model chuẩn), sau đó token dài nhất
    return max(cands, key=lambda c: ("-" in c, len(c)))


def name_key(name: str) -> str:
    s = unicodedata.normalize("NFKC", name).lower()
    s = re.sub(r"[\[【(（][^\]】)）]*[\]】)）]", "", s)
    return re.sub(r"[^0-9a-zぁ-んァ-ヶ一-龠]", "", s)[:60]


# mã bộ thẻ: SV2a, S7R, SM12a, SV11B-D (デラックス), OP-11, EB-02, PRB-02, ST-21
_SET = re.compile(r"(?<![A-Za-z0-9])(SV\d{1,2}[A-Za-z]?|SM\d{1,2}[A-Za-z]?|S\d{1,2}[A-Za-z]?|OP-?\d{2}|EB-?\d{2}|PRB-?\d{2}|ST-?\d{2})"
                  r"(?:[-_](D|DX))?(?![A-Za-z0-9])", re.I)
_SET_DROP = ["遊戯王オフィシャルカードゲーム", "遊戯王 OCG", "遊戯王OCG", "デュエルモンスターズ", "ONE PIECEカードゲーム", "ONE PIECE カードゲーム", "カードゲーム", "サン&ムーン", "ソード&シールド", "S&V", "TAG TEAM GX",
             "エクストラブースター", "ブースターパック", "プレミアムブースター", "強化", "ハイクラス", "ポケモンカード"]
_CARTON = r"カートン|ケース|carton|\d+\s*BOX(入|セット)|BOXセット"


def card_set(name: str):
    """(mã bộ hoặc None, tên lõi) của 1 hộp thẻ. Hộp デラックス có hậu tố 'dx'. None nếu không phải hộp/bộ."""
    s = unicodedata.normalize("NFKC", name)
    if re.search(r"PSA|BGS|ARS\d|鑑定|\d+/\d+|\d{3}-\d{3}", s) or re.search(_CARTON, s, re.I):
        return None
    dx = bool(re.search(r"デラックス|\bDX\b", s, re.I))
    m = _SET.search(s)
    code = None
    if m:
        code = re.sub(r"-", "", m.group(1)).lower()
        dx = dx or bool(m.group(2))
    core = _SET.sub(" ", s)
    for w in _SET_DROP:
        core = core.replace(w, " ")
    core = re.sub(r"デラックス|\bDX\b", " ", core, flags=re.I)
    core = box_key(core)
    if dx:
        core += "dx"
        code = code and code + "dx"
    return code, core


def make_key(cat: str, name: str) -> str:
    if "iphone" in name.lower():
        k = iphone_key(name)
        if k:
            return k
    # hộp thẻ: tên có BOX, hoặc kiểu 買取当番 「【SV11B】ブラックボルト」 (mã bộ trong 【】, không ghi BOX)
    if cat == "card" and (re.search(r"BOX|ボックス", name, re.I) or re.match(r"\s*【[A-Za-z]{1,3}-?\d{1,2}[A-Za-z]?(-D)?】", name)):
        cs = card_set(name)
        if cs:
            return "box:" + (cs[0] or cs[1])
    if re.search(r"キット|セット|同梱|バンドル|kit", name, re.I):
        return "name:" + name_key(name)  # bộ kit/set: số model của 1 linh kiện không đại diện cả bộ
    mc = model_code(name)
    if mc:
        return "model:" + mc
    return "name:" + name_key(name)


_REFINE = [
    ("card", r"PSA\s?10|ポケモンカード|ポケカ|遊戯王|ONE PIECE|ワンピースカード|デュエル|拡張パック"),
    ("phone", r"iPhone|Galaxy (S|Z|A)\d|Pixel \d|Xperia|AQUOS (sense|R|wish)|arrows"),
    ("tablet", r"iPad|Galaxy Tab|Kindle|Fire HD|Pixel Tablet"),
    ("game", r"Nintendo Switch|PlayStation|PS5|Xbox|Steam Deck|Steam Machine|Meta Quest|ROG Ally|DualSense|PS VR"),
    ("camera", r"ボディ|レンズキット|ダブルレンズ|ズームレンズ|交換レンズ|\d+(-\d+)?\s?mm(?![a-z])|\bF\d(\.\d)?\b|一眼|ミラーレス|コンデジ|"
               r"デジタルカメラ|サイバーショット|VLOGCAM|\bDSC-|\bZV-(E|1)|\bILCE|\bILME|α\d|RICOH GR|\bGR\s?I|PENTAX|PowerShot|"
               r"\bIXY\b|COOLPIX|NIKKOR|ニコン|Nikon|LUMIX|\bDC-[GSTF]|\bX-(T|S|H|E|M|Pro)\d|\bXF\d|\bGFX|EOS|\bE?F-?S?\d+-\d+|"
               r"\bRF-?S?\d+|\bZ\s?\d+-\d+|\bOM-\d|\bE-M\d|FUJIFILM|富士フイルム|SIGMA|TAMRON|OM SYSTEM|ハッセルブラッド|Hasselblad|"
               r"Leica|ライカ|GoPro|Insta360|DJI|Osmo|instax|チェキ|カメラ"),
    ("audio", r"AirPods|WF-1000|WH-1000|イヤホン|ヘッドホン|Earbuds|スピーカー|Bose|Sennheiser"),
    ("watch", r"Apple Watch|Galaxy Watch|Pixel Watch|G-SHOCK|Garmin|腕時計"),
    ("pc", r"MacBook|Mac mini|iMac|Surface|ノートPC|LIFEBOOK|ThinkPad|GeForce|RTX ?\d{4}|Radeon"),
]
# máy in, định vị ô tô… giữ ở gia dụng (tên có chữ Canon / mm dễ bị nhầm sang máy ảnh)
_KEEP_APPLIANCE = r"プリンター|PIXUS|Satera|\bG\d{4}\b|インクジェット|カーナビ|楽ナビ|AVIC|ALPINE|アルパイン|フローティング"


def refine_cat(cat: str, name: str) -> str:
    """Món bị xếp vào 'appliance'/'other' nhưng tên cho thấy rõ nhóm khác → chuyển nhóm."""
    if re.search(r"instax|チェキ|インスタックス|INSTAXフィルム", name, re.I):
        return "camera"  # phim/máy chụp lấy liền (vd "PASTEL GALAXY" từng bị nhầm sang điện thoại Galaxy)
    if cat not in ("appliance", "other"):
        return cat
    if re.search(_KEEP_APPLIANCE, name, re.I):
        return cat
    for c, pat in _REFINE:
        if re.search(pat, name, re.I):
            return c
    return cat
