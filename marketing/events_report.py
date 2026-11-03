"""Báo cáo hành vi người dùng trên kaitoriprice.com (sự kiện ẩn danh từ worker kaitori-push /stats).

Cho biết: người dùng tìm gì, tìm mà không ra gì, bấm sang tiệm nào / món nào, vào từ link nào.
  python marketing/events_report.py            → in báo cáo hôm qua (JST)
  python marketing/events_report.py --today    → hôm nay tính tới giờ
  python marketing/events_report.py --days 7   → 7 ngày gần nhất
  thêm --send để gửi Telegram
daily_traffic.py gọi summary() để gộp vào báo cáo buổi sáng.
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

URL = "https://kaitori-push.thanhduy8vn.workers.dev/stats"
ROOT = Path(__file__).resolve().parent.parent
JST = timezone(timedelta(hours=9))

LABEL = {
    "search": "🔎 Tìm nhiều", "search_none": "❓ Tìm mà KHÔNG ra kết quả", "shop_click": "🏪 Bấm sang tiệm",
    "affiliate_click": "🤝 Bấm link đối tác", "land": "🚪 Vào từ link", "guide_click": "📚 Mở bài hướng dẫn",
    "drill": "🗂 Lọc danh mục", "watch_add": "⭐ Theo dõi giá", "push_on": "🔔 Bật thông báo", "stock_add": "📦 Thêm máy của tôi",
    "share": "📤 Chia sẻ",
}


def key() -> str:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("EV_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("chưa có EV_KEY trong .env (chạy cron/deploy_push.py)")


def fetch(days: int) -> list[dict]:
    r = requests.get(URL, params={"key": key(), "days": days}, timeout=30)
    r.raise_for_status()
    return [x for x in r.json()["rows"] if not x["e"].startswith("dev_")]


def summary(day_from: str, day_to: str, top: int = 6) -> str:
    """Tóm tắt các sự kiện trong khoảng ngày (YYYY-MM-DD, tính cả 2 đầu)."""
    days = (datetime.now(JST).date() - datetime.fromisoformat(day_from).date()).days + 1
    rows = [x for x in fetch(max(1, days)) if day_from <= x["day"] <= day_to]
    if not rows:
        return "🧭 Hành vi: chưa có sự kiện nào (theo dõi mới bật từ 03/11)."
    by = defaultdict(Counter)
    for x in rows:
        a = x["a"].strip()
        if x["e"] in ("search", "search_none"):
            a = a.lower()
        if x["e"] == "shop_click" and x["b"]:
            by["shop_item"][f'{x["b"][:40]} → {a}'] += x["n"]
        if x["e"] == "land":
            by["land_src"][x["b"] or "?"] += x["n"]
        by[x["e"]][a or "(trống)"] += x["n"]
    tot = Counter({e: sum(c.values()) for e, c in by.items() if e in LABEL})
    out = ["🧭 <b>Hành vi người dùng</b>: " + ", ".join(f"{LABEL[e].split(' ', 1)[1].lower()} {n}" for e, n in tot.most_common(5))]
    for e in ("search", "search_none", "shop_click", "land", "guide_click", "affiliate_click"):
        if by.get(e):
            items = by[e].most_common(top)
            out.append(f"{LABEL[e]}: " + ", ".join(f"{k} ({n})" for k, n in items))
    if by.get("shop_item"):
        out.append("🏪 Món + tiệm được bấm nhiều: " + ", ".join(f"{k} ({n})" for k, n in by["shop_item"].most_common(4)))
    if by.get("land_src"):
        out.append("🚪 Nguồn vào: " + ", ".join(f"{k} ({n})" for k, n in by["land_src"].most_common(4)))
    s, c = sum(by["search"].values()) + sum(by["search_none"].values()), sum(by["shop_click"].values())
    if s:
        out.append(f"💡 {sum(by['search_none'].values()) * 100 // s}% lượt tìm không ra kết quả; {c} lượt bấm sang tiệm / {s} lượt tìm.")
    return "\n".join(out)


if __name__ == "__main__":
    now = datetime.now(JST)
    if "--today" in sys.argv:
        a = b = now.strftime("%Y-%m-%d")
    elif "--days" in sys.argv:
        n = int(sys.argv[sys.argv.index("--days") + 1])
        a, b = (now - timedelta(days=n - 1)).strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")
    else:
        a = b = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    msg = f"<b>kaitoriprice.com {a[8:]}/{a[5:7]}" + (f"–{b[8:]}/{b[5:7]}" if a != b else "") + "</b>\n" + summary(a, b)
    if "--send" in sys.argv:
        from daily_traffic import send
        send(msg)
        print("Đã gửi Telegram.")
    else:
        print(msg)
