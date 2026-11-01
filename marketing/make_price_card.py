"""Tạo ảnh 1080x1350 so giá thu mua 1 sản phẩm ở các tiệm (để đăng Facebook).
Dùng: python marketing/make_price_card.py "iPhone Duo 256GB" [phone]
"""
import json, sys
from PIL import Image, ImageDraw, ImageFont

KEY = sys.argv[1] if len(sys.argv) > 1 else "iPhone Duo 256GB"
CAT = sys.argv[2] if len(sys.argv) > 2 else "phone"
SHOP = {"rudeya": "買取ルデヤ", "panda": "PANDA買取", "mobile_ichiban": "モバイル一番", "morimori": "森森買取",
        "toban": "買取当番", "guestmobile": "ゲストモバイル", "keitaigod": "ケータイゴッド", "homura": "買取ホムラ", "ichome": "買取1丁目"}

d = json.load(open(f"site/data/cat/{CAT}.json", encoding="utf-8"))
items = d["items"] if isinstance(d, dict) else d
it = next(i for i in items if i["key"].split("|")[0] == KEY)
rows = sorted(((SHOP.get(s, s), p["price"], p.get("ts", "")) for s, p in it["prices"].items()), key=lambda r: -r[1])
ts = max(r[2] for r in rows)

F = "C:/Windows/Fonts/"
def vi(sz, b=False): return ImageFont.truetype(F + ("segoeuib.ttf" if b else "segoeui.ttf"), sz)
def ja(sz, b=False): return ImageFont.truetype(F + ("YuGothB.ttc" if b else "YuGothM.ttc"), sz)

W, H = 1080, 1350
INK, INK2, MUTED, GRID = "#0f172a", "#475569", "#94a3b8", "#e2e8f0"
BAR, BAR_TOP, BG = "#93c5fd", "#1d4ed8", "#ffffff"
img = Image.new("RGB", (W, H), BG)
g = ImageDraw.Draw(img)

# tiêu đề
g.rectangle([0, 0, W, 250], fill="#0f172a")
g.text((60, 48), "Bán ở đâu được giá nhất?", font=vi(40), fill="#cbd5e1")
g.text((60, 100), KEY, font=vi(76, True), fill="#ffffff")
g.text((60, 190), f"Giá thu mua hàng mới chưa mở hộp · {len(rows)} tiệm · {ts[:10].replace('-', '/')} {ts[11:16]}",
       font=vi(28), fill="#94a3b8")

def yen(x, y, n, col):  # số (Segoe) + chữ 円 (Yu Gothic, Segoe không có chữ này)
    t = f"{n:,}"; g.text((x, y), t, font=vi(84, True), fill=col)
    g.text((x + g.textlength(t, font=vi(84, True)) + 6, y + 30), "円", font=ja(48, True), fill=col)

# số nổi bật
best, worst = rows[0][1], rows[-1][1]
g.text((60, 270), "Cao nhất", font=vi(30), fill=INK2)
yen(60, 308, best, INK)
g.text((60, 410), rows[0][0], font=ja(36, True), fill=BAR_TOP)
g.text((600, 270), "Chênh lệch cao – thấp", font=vi(30), fill=INK2)
yen(600, 308, best - worst, "#b91c1c")
g.text((600, 410), "cùng 1 máy, khác tiệm", font=vi(30), fill=INK2)

# thanh ngang: bắt đầu từ 0, nhãn giá + chênh so với cao nhất
top, x0, x1 = 490, 330, 860
rh = min(96, (H - 150 - 20 - top) // len(rows))  # co dòng khi nhiều tiệm để không tràn chân trang
g.line([x0, top - 10, x0, top + rh * len(rows)], fill=GRID, width=2)
for i, (name, price, _) in enumerate(rows):
    y = top + i * rh
    g.text((60, y + 22), name, font=ja(34, i == 0), fill=INK if i == 0 else INK2)
    bw = int((x1 - x0) * price / best)
    g.rounded_rectangle([x0, y + 18, x0 + bw, y + 70], radius=6, fill=BAR_TOP if i == 0 else BAR)
    g.text((x0 + bw + 14, y + 16), f"{price:,}", font=vi(34, True), fill=INK)
    g.text((x0 + bw + 14, y + 56), "cao nhất" if i == 0 else f"−{best - price:,}", font=vi(24),
           fill=BAR_TOP if i == 0 else MUTED)

# chân trang
fy = H - 150
g.line([60, fy, W - 60, fy], fill=GRID, width=2)
g.text((60, fy + 24), "kaitoriprice.com", font=vi(52, True), fill=INK)
g.text((60, fy + 92), "So giá kaitori nhiều tiệm · cập nhật mỗi giờ · miễn phí", font=vi(28), fill=INK2)
g.text((W - 60, fy + 34), "買取プライス", font=ja(34, True), fill=MUTED, anchor="ra")

out = f"marketing/{KEY.replace(' ', '_')}.png"
img.save(out)
print(out)
