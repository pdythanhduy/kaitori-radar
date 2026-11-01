"""Ảnh so giá 1080x1350 để đăng Facebook + trang /share/ (ảnh + bài viết sẵn, sinh lại mỗi lần deploy).

Mở https://kaitoriprice.com/share/ trên điện thoại → giữ ảnh để lưu → bấm "Chép bài" → dán vào Facebook.
Chạy được trên Windows (Segoe/Yu Gothic) và Ubuntu (Noto, cài ở workflow).
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

SHOP = {"rudeya": "買取ルデヤ", "panda": "PANDA買取", "mobile_ichiban": "モバイル一番", "morimori": "森森買取",
        "toban": "買取当番", "guestmobile": "ゲストモバイル", "keitaigod": "ケータイゴッド", "homura": "買取ホムラ",
        "ichome": "買取1丁目"}
_FONTS = {  # (latin+tiếng Việt thường, đậm), (tiếng Nhật thường, đậm)
    "win": (("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/segoeuib.ttf"),
            ("C:/Windows/Fonts/YuGothM.ttc", "C:/Windows/Fonts/YuGothB.ttc")),
    "linux": (("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),
              ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")),
}
_JA = re.compile(r"[\u3000-\u30ff\u3400-\u9fff\uff00-\uffef]")


def _fonts():
    for k in ("win", "linux"):
        if all(Path(p).exists() for pair in _FONTS[k] for p in pair):
            return _FONTS[k]
    return None


def render(name: str, prices: dict, out: Path) -> bool:
    from PIL import Image, ImageDraw, ImageFont
    fp = _fonts()
    if not fp:
        return False
    (vr, vb), (jr, jb) = fp
    vi = lambda sz, b=False: ImageFont.truetype(vb if b else vr, sz)  # noqa: E731
    ja = lambda sz, b=False: ImageFont.truetype(jb if b else jr, sz)  # noqa: E731
    rows = sorted(((SHOP.get(s, s), p["price"], p.get("ts", "")) for s, p in prices.items()), key=lambda r: -r[1])
    ts = max(r[2] for r in rows)
    W, H = 1080, 1350
    INK, INK2, MUTED, GRID, BAR, TOP = "#0f172a", "#475569", "#94a3b8", "#e2e8f0", "#93c5fd", "#1d4ed8"
    img = Image.new("RGB", (W, H), "#ffffff")
    g = ImageDraw.Draw(img)
    g.rectangle([0, 0, W, 250], fill="#0f172a")
    g.text((60, 48), "Bán ở đâu được giá nhất?", font=vi(40), fill="#cbd5e1")
    # tên sản phẩm: co chữ cho vừa 1 dòng (tên tiếng Nhật dùng font Nhật)
    tf = ja if _JA.search(name) else vi
    sz, t = 76, name
    while sz > 40 and g.textlength(t, font=tf(sz, True)) > W - 120:
        sz -= 4
    while g.textlength(t, font=tf(sz, True)) > W - 120 and len(t) > 10:
        t = t[:-2].rstrip() + "…" if not t.endswith("…") else t[:-2] + "…"
    g.text((60, 100 + (76 - sz) // 2), t, font=tf(sz, True), fill="#ffffff")
    g.text((60, 190), f"Giá thu mua hàng mới chưa mở hộp · {len(rows)} tiệm · {ts[:10].replace('-', '/')} {ts[11:16]}",
           font=vi(28), fill="#94a3b8")

    def yen(x, y, n, col):
        s = f"{n:,}"
        g.text((x, y), s, font=vi(84, True), fill=col)
        g.text((x + g.textlength(s, font=vi(84, True)) + 6, y + 30), "円", font=ja(48, True), fill=col)

    best, worst = rows[0][1], rows[-1][1]
    g.text((60, 270), "Cao nhất", font=vi(30), fill=INK2)
    yen(60, 308, best, INK)
    g.text((60, 410), rows[0][0], font=ja(36, True), fill=TOP)
    g.text((600, 270), "Chênh lệch cao – thấp", font=vi(30), fill=INK2)
    yen(600, 308, best - worst, "#b91c1c")
    g.text((600, 410), "cùng 1 món, khác tiệm", font=vi(30), fill=INK2)
    top, x0, x1 = 490, 330, 860
    rh = min(96, (H - 170 - top) // len(rows))
    g.line([x0, top - 10, x0, top + rh * len(rows)], fill=GRID, width=2)
    for i, (shop, price, _) in enumerate(rows):
        y = top + i * rh
        g.text((60, y + 22), shop, font=ja(34, i == 0), fill=INK if i == 0 else INK2)
        bw = int((x1 - x0) * price / best)
        g.rounded_rectangle([x0, y + 18, x0 + bw, y + 70], radius=6, fill=TOP if i == 0 else BAR)
        g.text((x0 + bw + 14, y + 16), f"{price:,}", font=vi(34, True), fill=INK)
        g.text((x0 + bw + 14, y + 56), "cao nhất" if i == 0 else f"−{best - price:,}", font=vi(24),
               fill=TOP if i == 0 else MUTED)
    fy = H - 150
    g.line([60, fy, W - 60, fy], fill=GRID, width=2)
    g.text((60, fy + 24), "kaitoriprice.com/vi", font=vi(52, True), fill=INK)
    g.text((60, fy + 92), "So giá kaitori 9 tiệm · cập nhật mỗi giờ · miễn phí", font=vi(28), fill=INK2)
    g.text((W - 60, fy + 34), "買取プライス", font=ja(34, True), fill=MUTED, anchor="ra")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, optimize=True)
    return True


def title(it) -> str:
    """Tên hiển thị gọn: bỏ 【mã】, hộp thẻ thêm chữ BOX."""
    t = re.sub(r"【[^】]*】", " ", it["name"]).strip()
    if it["key"].startswith("box:") and not re.search(r"BOX|ボックス", t, re.I):
        t += " BOX"
    return re.sub(r"\s+", " ", t)


def _caption(it, label):
    ps = sorted(it["prices"].items(), key=lambda kv: -kv[1]["price"])
    (s1, p1), (sl, pl) = ps[0], ps[-1]
    gap = p1["price"] - pl["price"]
    man = f"{gap / 10000:.1f}".rstrip("0").rstrip(".").replace(".", ",")
    f = lambda n: f"{n:,}".replace(",", ".")  # noqa: E731  (kiểu số Việt: 236.000)
    tail = f" → chọn nhầm tiệm mất tới {man} man!" if gap >= 10000 else f" → chênh {f(gap)}円."
    return (f"📊 {label}: {title(it)} – {len(ps)} tiệm kai\n"
            f"Cao nhất {SHOP.get(s1, s1)} {f(p1['price'])}円, thấp nhất {f(pl['price'])}円{tail}\n"
            "Giá 9 tiệm cập nhật mỗi giờ 👉 https://kaitoriprice.com/vi/\n"
            "Anh em hôm nay bán được bao nhiêu, ở tiệm nào? Comment chia sẻ nhé 👇")


def pick(items: dict) -> list:
    """Chọn 3 món đáng đăng hôm nay: iPhone 18/Duo, hộp thẻ, máy game — món có chênh lệch giữa các tiệm lớn nhất."""
    out = []
    rules = [("Giá thu mua iPhone hôm nay", "phone", lambda i: re.match(r"iPhone (18|Duo)\b", i["key"]) and i["n_shops"] >= 5),
             ("Giá thu mua hộp thẻ hôm nay", "card", lambda i: i["key"].startswith("box:") and i["n_shops"] >= 4),
             ("Giá thu mua máy game hôm nay", "game", lambda i: re.search(r"Switch\s?2|PS5|PlayStation\s?5|プレイステーション5", i["name"]) and i["n_shops"] >= 4)]
    for label, cat, ok in rules:
        cand = [i for i in items.get(cat, []) if ok(i) and i.get("spread")]
        if cand:
            out.append((label, max(cand, key=lambda i: i["spread"])))
    return out


def build(items: dict, site: Path, updated: str) -> int:
    try:
        import PIL  # noqa: F401
    except ImportError:
        return 0
    e = lambda s: html.escape(str(s), quote=True)  # noqa: E731
    cards, n = [], 0
    for k, (label, it) in enumerate(pick(items), 1):
        if not render(title(it), it["prices"], site / "share" / f"{k}.png"):
            return 0
        n += 1
        cap = _caption(it, label)
        cards.append(f'<section><img src="{k}.png?t={e(updated[:16])}" alt="{e(it["name"])}" width="540" height="675">'
                     f'<textarea readonly id="c{k}">{e(cap)}</textarea>'
                     f'<button onclick="navigator.clipboard.writeText(document.getElementById(\'c{k}\').value);this.textContent=\'✓ Đã chép\'">📋 Chép bài</button></section>')
    page = f"""<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Ảnh giá hôm nay – Kaitori Price</title>
<style>body{{font-family:system-ui,sans-serif;max-width:600px;margin:0 auto;padding:12px;background:#f8fafc;color:#0f172a}}
section{{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:10px;margin:14px 0}}img{{width:100%;height:auto;border-radius:8px}}
textarea{{width:100%;height:120px;margin-top:8px;font-size:14px;box-sizing:border-box}}button{{width:100%;padding:12px;font-size:16px;font-weight:700;border:0;border-radius:10px;background:#1877f2;color:#fff;margin-top:6px}}</style></head>
<body><h1 style="font-size:20px">📸 Ảnh giá hôm nay</h1><p style="color:#64748b;font-size:14px">Cập nhật {e(updated)} JST. Giữ ảnh để lưu → bấm "Chép bài" → dán vào Facebook.</p>
{''.join(cards)}</body></html>"""
    (site / "share").mkdir(parents=True, exist_ok=True)
    (site / "share" / "index.html").write_text(page, encoding="utf-8")
    return n


if __name__ == "__main__":  # chạy thử trên máy: python -m radar.share
    root = Path(__file__).resolve().parent.parent / "site"
    data = {}
    for f in (root / "data" / "cat").glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        data[f.stem] = d["items"] if isinstance(d, dict) else d
    print("images:", build(data, root, json.loads((root / "data" / "index.json").read_text(encoding="utf-8")).get("updated", "")))
