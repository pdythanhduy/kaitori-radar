"""📡 Radar thị trường: các tín hiệu có thể đi trước giá kai iPhone ở Nhật (hàng mới chủ yếu xuất sang HK/TQ).

Mỗi ngày ghi vào marketing/market_log.csv và (tuỳ chọn) gửi Telegram:
  1. Tỷ giá JPY→CNY/HKD (frankfurter.app, dữ liệu ECB). Yên yếu → hàng Nhật rẻ với người mua TQ/HK.
  2. Giá Apple chính hãng ở Trung Quốc và Hồng Kông (apple.com.cn / apple.com/hk). Apple TQ giảm giá → hàng xuất từ Nhật kém hấp dẫn.
  3. Xu hướng giá kai của chính web (site/data/hist/phone.json), các mẫu iPhone 18 / Duo.
Đây là CHỈ BÁO để theo dõi, không phải dự đoán chắc chắn. Sau vài tuần đủ dữ liệu sẽ kiểm tra chỉ báo nào thật sự đi trước giá kai.

  python marketing/market_watch.py --dry     # in ra, không gửi, không ghi
  python marketing/market_watch.py           # ghi log + gửi Telegram
  python marketing/market_watch.py --news "tóm tắt tin TQ/HK hôm nay"   # kèm phần tin tức (do Claude tìm mỗi ngày)
"""
from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LOG = HERE / "market_log.csv"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
APPLE = {"cn": ("https://www.apple.com.cn/shop/buy-iphone/iphone-18-pro", r"RMB\s?([0-9,]{4,})"),
         "hk": ("https://www.apple.com/hk/shop/buy-iphone/iphone-18-pro", r"HK\$\s?([0-9,]{4,})")}
WATCH = ["iPhone Duo 256GB", "iPhone Duo 512GB", "iPhone 18 Pro Max 256GB", "iPhone 18 Pro 256GB"]


def fx() -> dict:
    r = requests.get("https://api.frankfurter.app/latest?from=JPY&to=CNY,HKD,USD", timeout=30).json()
    d = r["date"]
    old = requests.get(f"https://api.frankfurter.app/{(datetime.fromisoformat(d) - timedelta(days=7)).date()}?from=JPY&to=CNY,HKD",
                       timeout=30).json()
    # 1 CNY = ? JPY  (dễ đọc hơn)
    return {"date": d, "cny": 1 / r["rates"]["CNY"], "hkd": 1 / r["rates"]["HKD"], "usd": 1 / r["rates"]["USD"],
            "cny_7d": 1 / old["rates"]["CNY"], "hkd_7d": 1 / old["rates"]["HKD"]}


def apple(region: str) -> list[int]:
    url, pat = APPLE[region]
    t = requests.get(url, headers=UA, timeout=40).text
    return sorted({v for x in re.findall(pat, t) if (v := int(x.replace(",", ""))) >= 5000})  # bỏ giá trả góp/tháng


def kai_trend() -> list[tuple[str, int, int | None, int | None]]:
    """(tên, giá nay, giá 1 ngày trước, giá 7 ngày trước hoặc ngày cũ nhất có)"""
    h = json.loads((ROOT / "site" / "data" / "hist" / "phone.json").read_text(encoding="utf-8"))
    out = []
    for name in WATCH:
        k = next((k for k in h if k.split("|")[0] == name), None)
        if not k or not h[k]:
            continue
        s = h[k]
        now = s[-1][1]
        d1 = s[-2][1] if len(s) >= 2 else None
        d7 = s[-8][1] if len(s) >= 8 else s[0][1] if len(s) >= 2 else None
        out.append((name, now, d1, d7))
    return out


def last_row() -> dict | None:
    if not LOG.exists():
        return None
    rows = list(csv.DictReader(LOG.open(encoding="utf-8")))
    return rows[-1] if rows else None


def pct(a, b) -> str:
    if not b:
        return ""
    d = (a - b) / b * 100
    return f"{'▲' if d >= 0 else '▼'}{abs(d):.1f}%"


def report(news: str = "") -> tuple[str, dict]:
    f = fx()
    cn, hk = apple("cn"), apple("hk")
    prev = last_row()
    row = {"date": datetime.now().strftime("%Y-%m-%d"), "jpy_per_cny": f"{f['cny']:.3f}", "jpy_per_hkd": f"{f['hkd']:.3f}",
           "apple_cn": " ".join(map(str, cn)), "apple_hk": " ".join(map(str, hk))}
    tr = kai_trend()
    for name, now, _, _ in tr:
        row[name] = now
    L = [f"📡 <b>Radar thị trường {row['date'][8:]}/{row['date'][5:7]}</b>", ""]
    L.append(f"💱 1 CNY = {f['cny']:.2f}円 ({pct(f['cny'], f['cny_7d'])} 7 ngày) · 1 HKD = {f['hkd']:.2f}円 ({pct(f['hkd'], f['hkd_7d'])})")
    L.append("   Yên yếu đi (số tăng) → hàng Nhật rẻ hơn với người mua TQ/HK → thường đỡ giá kai.")
    def chg(region, cur, name):
        if not cur:
            return f"🍎 Apple {name}: không lấy được giá"
        if prev and prev.get(f"apple_{region}") and prev[f"apple_{region}"] != " ".join(map(str, cur)):
            return f"🚨 <b>Apple {name} ĐỔI GIÁ</b>: trước {prev[f'apple_{region}']} → nay {' '.join(map(str, cur))}. Theo dõi sát giá kai mấy ngày tới."
        return f"🍎 Apple {name}: bảng giá trang iPhone 18 Pro không đổi ({len(cur)} mức giá, cao nhất {cur[-1]:,})"
    L.append(chg("cn", cn, "Trung Quốc"))
    L.append(chg("hk", hk, "Hồng Kông"))
    if tr:
        L += ["", "📈 Giá kai (cao nhất 9 tiệm):"]
        for name, now, d1, d7 in tr:
            L.append(f"• {name}: {now:,}円 {('· 1 ngày ' + pct(now, d1)) if d1 else ''} {('· dài hạn ' + pct(now, d7)) if d7 else ''}")
    if news:
        L += ["", "📰 Tin TQ/HK:", news.strip()]
    L += ["", "<i>Chỉ báo để tham khảo, chưa phải dự đoán. Sau 2–3 tuần mình sẽ kiểm tra chỉ báo nào đi trước giá kai.</i>"]
    return "\n".join(L), row


def save(row: dict) -> None:
    rows = list(csv.DictReader(LOG.open(encoding="utf-8"))) if LOG.exists() else []
    rows = [r for r in rows if r.get("date") != row["date"]] + [row]
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with LOG.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    a = sys.argv[1:]
    news = a[a.index("--news") + 1] if "--news" in a else ""
    msg, row = report(news)
    if "--dry" in a:
        print(msg)
    else:
        save(row)
        sys.path.insert(0, str(HERE))
        from daily_traffic import send
        send(msg)
        print("Đã ghi market_log.csv + gửi Telegram.")
