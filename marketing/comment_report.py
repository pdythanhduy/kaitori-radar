"""Ghi bình luận FB vào comment_log.md và gửi báo cáo bình luận hôm nay qua Telegram.

Ghi 1 bình luận mới (giờ JST hiện tại) rồi gửi báo cáo:
  python marketing/comment_report.py --add "32K (807826924656140)" "permalink/123..." "so giá kai"
Chỉ gửi báo cáo (không ghi thêm):
  python marketing/comment_report.py
Thêm --dry để in ra màn hình, không gửi.
Telegram dùng chung bot/chat với daily_traffic.py.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from daily_traffic import JST, send

LOG = Path(__file__).resolve().parent / "comment_log.md"
LIMIT = 8
ROW = re.compile(r"^(\d{4}-\d{2}-\d{2}) \| ([\d:-]{5}) \| (.+?) \| (.+?) \| (.+)$")


def rows() -> list[tuple[str, str, str, str, str]]:
    return [m.groups() for line in LOG.read_text(encoding="utf-8").splitlines() if (m := ROW.match(line.strip()))]


def add(group: str, post: str, note: str) -> None:
    now = datetime.now(JST)
    text = LOG.read_text(encoding="utf-8").rstrip("\n")
    LOG.write_text(text + f"\n{now:%Y-%m-%d} | {now:%H:%M} | {group} | {post} | {note}\n", encoding="utf-8")


def report() -> str:
    today = datetime.now(JST).strftime("%Y-%m-%d")
    all_rows = rows()
    t = [r for r in all_rows if r[0] == today]
    n = len(t)
    lines = [f"💬 <b>Bình luận FB hôm nay {today[8:]}/{today[5:7]}</b>",
             f"Đã bình luận: <b>{n}/{LIMIT}</b> – còn {max(LIMIT - n, 0)}", ""]
    for _, hm, g, post, note in t:
        lines.append(f"• {hm} · {g.split(' (')[0]} · {post[:60]} → {note[:60]}")

    warn = []
    if n > LIMIT:
        warn.append(f"Vượt giới hạn {LIMIT} bình luận/ngày!")
    groups = Counter(r[2] for r in t)
    if groups:
        g, c = groups.most_common(1)[0]
        if n >= 3 and c / n > 0.6:
            warn.append(f"{c}/{n} bình luận dồn vào nhóm {g.split(' (')[0]} → lần tới chuyển nhóm khác.")
    times = sorted(r[1] for r in t if r[1] != "--:--")
    for a, b in zip(times, times[1:]):
        gap = (int(b[:2]) * 60 + int(b[3:])) - (int(a[:2]) * 60 + int(a[3:]))
        if gap < 20:
            warn.append(f"{a} → {b} chỉ cách {gap} phút, nên giãn ≥ 20 phút.")
            break
    posts = Counter(r[3] for r in all_rows)
    dup = [p for p, c in posts.items() if c > 1]
    if dup:
        warn.append("Bình luận trùng bài: " + ", ".join(p[:40] for p in dup))
    if any(r[1] == "--:--" for r in t):
        warn.append("Có dòng chưa ghi giờ.")
    if warn:
        lines += ["", "⚠️ " + "\n⚠️ ".join(warn)]
    return "\n".join(lines)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--dry"]
    if args and args[0] == "--add":
        if len(args) != 4:
            sys.exit('Cách dùng: --add "nhóm" "bài" "nội dung"')
        add(*args[1:])
    msg = report()
    if "--dry" in sys.argv:
        print(msg)
    else:
        send(msg)
        print("Đã gửi Telegram.")
