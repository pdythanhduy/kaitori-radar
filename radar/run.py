"""Thu thập giá → data/latest.json + data/history.json (+ Telegram tuỳ chọn).
    python -m radar.run            # chạy tất cả tiệm
    python -m radar.run --telegram # kèm gửi tóm tắt Telegram
"""
from __future__ import annotations

import json
import os
import re
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from .shops import SHOPS

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "site" / "data"
JST = timezone(timedelta(hours=9))


def display_name(cat, names):
    if cat == "iphone_new":
        return None
    best = min(names, key=len)
    best = re.sub(r"^ポケモン\s*(ポケモンカードゲーム)?\s*", "", best)
    return best.replace("　", " ").strip()


def collect():
    sess = requests.Session()
    rows, status = [], {}
    for sid, meta in SHOPS.items():
        try:
            got = meta["fn"](sess)
            rows += got
            status[sid] = {"ok": True, "count": len(got)}
            print(f"[{sid}] {len(got)} items")
        except Exception as exc:  # noqa: BLE001
            status[sid] = {"ok": False, "error": str(exc)[:200]}
            print(f"[{sid}] ERROR {exc}")
            traceback.print_exc()
    return rows, status


def aggregate(rows):
    groups = {}
    for r in rows:
        g = groups.setdefault((r["cat"], r["key"]), {"cat": r["cat"], "key": r["key"], "names": [], "prices": {}})
        g["names"].append(r["name"])
        cur = g["prices"].get(r["shop"])
        if cur is None or r["price"] > cur["price"]:
            g["prices"][r["shop"]] = {"price": r["price"], "url": r["url"], "note": r["note"],
                                      "min": min(r["price"], cur["min"]) if cur else r["price"]}
        else:
            cur["min"] = min(cur["min"], r["price"])
    items = []
    for g in groups.values():
        best_shop = max(g["prices"], key=lambda s: g["prices"][s]["price"])
        vals = [v["price"] for v in g["prices"].values()]
        items.append({"cat": g["cat"], "key": g["key"],
                      "name": display_name(g["cat"], g["names"]) or g["key"],
                      "jan": None, "prices": g["prices"], "best_shop": best_shop, "best": max(vals),
                      "spread": max(vals) - min(vals) if len(vals) > 1 else 0, "n_shops": len(vals)})
    items.sort(key=lambda x: (x["cat"], -x["n_shops"], -x["best"]))
    return items


def update_history(items, today):
    path = DATA / "history.json"
    hist = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for it in items:
        k = f'{it["cat"]}|{it["key"]}'
        series = [p for p in hist.get(k, []) if p[0] != today]
        series.append([today, it["best"]])
        hist[k] = series[-120:]
    path.write_text(json.dumps(hist, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return hist


def telegram(items, hist, today):
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token:
        env = Path(r"C:\Users\thanh\japan-news-bot\.env")
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    token = line.split("=", 1)[1].strip()
                elif line.startswith("TELEGRAM_CHAT_ID="):
                    chat = line.split("=", 1)[1].strip()
    if not token or not chat:
        print("no telegram creds")
        return
    lines = [f"📡 <b>Kaitori Radar {today}</b>"]
    for cat, title, n in (("pokebox", "🃏 ポケカBOX (giá thu mua cao nhất)", 8), ("iphone_new", "📱 iPhone mới SIMフリー", 6)):
        top = [i for i in items if i["cat"] == cat][:n]
        if not top:
            continue
        lines.append(f"\n<b>{title}</b>")
        for it in top:
            series = hist.get(f'{it["cat"]}|{it["key"]}', [])
            delta = ""
            if len(series) >= 2:
                d = series[-1][1] - series[-2][1]
                delta = f" ({'▲' if d > 0 else '▼'}{abs(d):,})" if d else ""
            shop = SHOPS[it["best_shop"]]["name"]
            lines.append(f"• {it['name'][:28]}: <b>{it['best']:,}円</b> @{shop}{delta}")
    drops = []
    for it in items:
        s = hist.get(f'{it["cat"]}|{it["key"]}', [])
        if len(s) >= 2 and s[-2][1] and (s[-2][1] - s[-1][1]) / s[-2][1] >= 0.05:
            drops.append(f"⚠️ {it['name'][:30]} giảm {s[-2][1] - s[-1][1]:,}円 ({(s[-2][1] - s[-1][1]) / s[-2][1]:.0%})")
    if drops:
        lines.append("\n<b>Giảm mạnh ≥5%:</b>\n" + "\n".join(drops[:10]))
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", timeout=45,
                  data={"chat_id": chat, "text": "\n".join(lines), "parse_mode": "HTML", "disable_web_page_preview": "true"})


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    now = datetime.now(JST)
    today = now.strftime("%Y-%m-%d")
    rows, status = collect()
    items = aggregate(rows)
    if not items:
        print("no data — giữ file cũ")
        return 1
    out = {"updated": now.strftime("%Y-%m-%d %H:%M"), "shops": {k: {"name": v["name"], "url": v["url"]} for k, v in SHOPS.items()},
           "status": status, "items": items}
    (DATA / "latest.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    hist = update_history(items, today)
    print(f"items: {len(items)} | multi-shop: {sum(1 for i in items if i['n_shops'] > 1)}")
    if "--telegram" in sys.argv:
        telegram(items, hist, today)
    return 0


if __name__ == "__main__":
    sys.exit(main())
