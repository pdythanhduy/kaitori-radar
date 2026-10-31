"""Thu thập giá → site/data/*.json (+ Telegram tuỳ chọn).

    python -m radar.run --full       # toàn bộ danh mục (1–2 lần/ngày, ~30 phút)
    python -m radar.run --hot        # chỉ hàng hot: iPhone, ポケカBOX, PS5, Switch (mỗi 1–2 tiếng)
    python -m radar.run --hot --telegram
    python -m radar.run --only morimori:0301   # chạy 1 scope (debug)
Dữ liệu thô từng scope lưu ở data_raw/, web chỉ đọc file đã tổng hợp trong site/data/.
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

from .normalize import CATS
from .shops import SHOPS

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data_raw"
OUT = ROOT / "site" / "data"
JST = timezone(timedelta(hours=9))


def now_jst():
    return datetime.now(JST)


# ------------------------------------------------------------------ scrape
def scrape(mode: str, only: str | None):
    RAW.mkdir(parents=True, exist_ok=True)
    sess = requests.Session()
    status = json.loads((RAW / "_status.json").read_text(encoding="utf-8")) if (RAW / "_status.json").exists() else {}
    jobs = []
    for sid, meta in SHOPS.items():
        scopes = meta["hot"] if mode == "hot" else meta["scopes"]
        for sc in scopes:
            if only and only != f"{sid}:{sc}":
                continue
            jobs.append((sid, sc))
    for sid, sc in jobs:
        ts = now_jst().strftime("%Y-%m-%d %H:%M")
        try:
            rows = SHOPS[sid]["fn"](sess, sc)
            for r in rows:
                r["ts"] = ts
            (RAW / f"{sid}_{sc}.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
            status[f"{sid}:{sc}"] = {"ok": True, "n": len(rows), "ts": ts}
            print(f"[{sid}:{sc}] {len(rows)}")
        except Exception as exc:  # noqa: BLE001
            status[f"{sid}:{sc}"] = {"ok": False, "err": str(exc)[:200], "ts": ts}
            print(f"[{sid}:{sc}] ERROR {exc}")
            traceback.print_exc()
    (RAW / "_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")
    return status


# ------------------------------------------------------------------ aggregate
def load_rows():
    latest = {}
    for f in RAW.glob("*.json"):
        if f.name.startswith("_"):
            continue
        for r in json.loads(f.read_text(encoding="utf-8")):
            k = (r["shop"], r["url"], r["name"])
            if k not in latest or r["ts"] > latest[k]["ts"]:
                latest[k] = r
    from .normalize import make_key, refine_cat
    for r in latest.values():
        r["cat"] = refine_cat(r["cat"], r["name"])
        r["key"] = make_key(r["cat"], r["name"])  # luôn tính lại theo luật ghép mới nhất
    return list(latest.values())


def _display(cat, key, names):
    if key.startswith("iPhone"):
        return key
    best = min(names, key=lambda n: (len(n) < 6, len(n)))
    best = re.sub(r"^(Apple|ポケモン)\s*(ポケモンカードゲーム)?\s*", "", best).replace("　", " ").strip()
    return best


def _key_rank(k):
    return 0 if k.startswith("iPhone") else 1 if k.startswith(("model:", "box:")) else 2


def unify_by_jan(rows):
    """Cùng mã JAN = cùng sản phẩm: gom về một khoá (ưu tiên iPhone/model/box hơn name)."""
    best = {}
    for r in rows:
        j = r.get("jan")
        if j and (j not in best or _key_rank(r["key"]) < _key_rank(best[j][1])):
            best[j] = (r["cat"], r["key"])
    cat_pref = {}
    for r in rows:  # danh mục cụ thể (không phải appliance/other) được ưu tiên
        j = r.get("jan")
        if j and r["cat"] not in ("appliance", "other"):
            cat_pref.setdefault(j, r["cat"])
    best = {j: (cat_pref.get(j, c), k) for j, (c, k) in best.items()}
    # khoá name: -> khoá tốt hơn qua JAN (để cả các dòng KHÔNG có JAN nhưng trùng khoá name cũng gộp theo)
    remap = {}
    for r in rows:
        j = r.get("jan")
        if j and best[j][1] != r["key"]:
            remap[(r["cat"], r["key"])] = best[j]
    for r in rows:
        if (r["cat"], r["key"]) in remap:
            r["cat"], r["key"] = remap[(r["cat"], r["key"])]
    return rows


def split_mixed(rows, ratio=1.3):
    """Trong CÙNG một tiệm, nếu một khoá chứa các dòng giá chênh > 1.3 lần → khoá quá thô (gộp nhầm nhiều SP):
    tách theo tên đầy đủ. (Khác màu thường chỉ lệch < 15%.)"""
    from .normalize import name_key
    rng = {}
    for r in rows:
        k = (r["shop"], r["cat"], r["key"])
        lo, hi = rng.get(k, (r["price"], r["price"]))
        rng[k] = (min(lo, r["price"]), max(hi, r["price"]))
    bad = {(c, k) for (s, c, k), (lo, hi) in rng.items() if hi > lo * ratio}
    for r in rows:
        if (r["cat"], r["key"]) in bad:
            r["key"] = f'{r["key"]}|{name_key(r["name"])}'
    return rows


def aggregate(rows):
    rows = unify_by_jan(rows)
    rows = split_mixed(rows)
    groups = {}
    for r in rows:
        g = groups.setdefault((r["cat"], r["key"]), {"names": [], "prices": {}})
        g["names"].append(r["name"])
        cur = g["prices"].get(r["shop"])
        if cur is None:
            g["prices"][r["shop"]] = {"price": r["price"], "url": r["url"], "note": r.get("note", "")[:40], "min": r["price"], "ts": r["ts"]}
        else:
            cur["min"] = min(cur["min"], r["price"])
            if r["price"] > cur["price"]:
                cur.update(price=r["price"], url=r["url"], note=r.get("note", "")[:40], ts=r["ts"])
    # Chống ghép sai: cùng khoá nhưng giá chênh > 1.8 lần giữa các tiệm => gần như chắc là 2 sản phẩm khác
    # (vd ống kính trùng số model, 1 BOX vs 1 thùng). Giữ nhóm giá cao, tách các tiệm giá thấp thành món riêng.
    RATIO = 1.8
    for (cat, key), g in list(groups.items()):
        ps = g["prices"]
        if len(ps) < 2:
            continue
        top = max(v["price"] for v in ps.values())
        low = {s: v for s, v in ps.items() if v["price"] * RATIO < top}
        if not low:
            continue
        for s, v in low.items():
            del ps[s]
            groups[(cat, f"{key}#{s}")] = {"names": g["names"][:1], "prices": {s: v}}
    items = []
    for (cat, key), g in groups.items():
        best_shop = max(g["prices"], key=lambda s: g["prices"][s]["price"])
        vals = sorted(v["price"] for v in g["prices"].values())
        med = vals[len(vals) // 2]
        core = [v for v in vals if med * 0.85 <= v <= med * 1.2]  # bỏ giá thấp bất thường khi tính chênh lệch
        items.append({"cat": cat, "key": key, "name": _display(cat, key, g["names"]), "prices": g["prices"],
                      "best_shop": best_shop, "best": vals[-1], "n_shops": len(vals),
                      "spread": core[-1] - core[0] if len(core) > 1 else 0})
    return items


def write_outputs(items, status):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "cat").mkdir(exist_ok=True)
    (OUT / "hist").mkdir(exist_ok=True)
    today = now_jst().strftime("%Y-%m-%d")
    cats = {}
    for cat, label in CATS.items():
        its = sorted([i for i in items if i["cat"] == cat], key=lambda x: (-x["n_shops"], -x["best"]))
        if not its:
            continue
        hp = OUT / "hist" / f"{cat}.json"
        hist = json.loads(hp.read_text(encoding="utf-8")) if hp.exists() else {}
        for it in its:
            s = [p for p in hist.get(it["key"], []) if p[0] != today]
            s.append([today, it["best"]])
            hist[it["key"]] = s[-120:]
            if len(s) >= 2:
                it["chg"] = s[-1][1] - s[-2][1]
        hp.write_text(json.dumps(hist, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        (OUT / "cat" / f"{cat}.json").write_text(json.dumps(its, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        cats[cat] = {"label": label, "count": len(its), "multi": sum(1 for i in its if i["n_shops"] > 1)}
    idx = {"updated": now_jst().strftime("%Y-%m-%d %H:%M"),
           "shops": {k: {"name": v["name"], "url": v["url"], "list": v.get("list", False)} for k, v in SHOPS.items()},
           "cats": cats, "total": len(items), "status": status}
    (OUT / "index.json").write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    # top chênh lệch để hiển thị trang chủ
    # top chênh lệch: đa dạng nhóm hàng (tối đa 3 món/nhóm), bỏ thẻ PSA lẻ giá cực cao
    pool = sorted([i for i in items if i["n_shops"] > 1 and i["spread"] > 0 and "PSA" not in i["name"]],
                  key=lambda x: -x["spread"])
    top, per = [], {}
    for i in pool:
        if per.get(i["cat"], 0) >= 3:
            continue
        per[i["cat"]] = per.get(i["cat"], 0) + 1
        top.append(i)
        if len(top) >= 30:
            break
    (OUT / "top.json").write_text(json.dumps(top, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    # sitemap cho Google (trang chủ + từng nhóm hàng)
    urls = ["https://kaitoriprice.com/"] + [f"https://kaitoriprice.com/?c={c}" for c in cats] + ["https://kaitoriprice.com/?v=deals"]
    lastmod = now_jst().strftime("%Y-%m-%d")
    nl = chr(10)
    sm = '<?xml version="1.0" encoding="UTF-8"?>' + nl + '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + nl
    sm += "".join(f"  <url><loc>{u.replace('&', '&amp;')}</loc><lastmod>{lastmod}</lastmod><changefreq>hourly</changefreq></url>{nl}" for u in urls)
    sm += "</urlset>" + nl
    (OUT.parent / "sitemap.xml").write_text(sm, encoding="utf-8")
    for old in ("latest.json", "history.json"):
        (OUT / old).unlink(missing_ok=True)
    return cats


# ------------------------------------------------------------------ telegram (cá nhân)
def _tg_creds():
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    env = Path(r"C:\Users\thanh\japan-news-bot\.env")
    if (not token or not chat) and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                token = line.split("=", 1)[1].strip()
            elif line.startswith("TELEGRAM_CHAT_ID="):
                chat = line.split("=", 1)[1].strip()
    return token, chat


def telegram(items):
    token, chat = _tg_creds()
    if not token or not chat:
        return
    shop = {k: v["name"] for k, v in SHOPS.items()}
    lines = [f"📡 <b>新品買取価格比較（β版） {now_jst():%m/%d %H:%M}</b>"]
    for title, pick in (("🃏 ポケカBOX", lambda i: i["cat"] == "card" and i["key"].startswith("box:")),
                        ("📱 iPhone mới SIMフリー", lambda i: i["key"].startswith("iPhone")),
                        ("🎮 Game", lambda i: i["cat"] == "game")):
        top = sorted([i for i in items if pick(i)], key=lambda x: (-x["n_shops"], -x["best"]))[:6]
        if top:
            lines.append(f"\n<b>{title}</b>")
            for it in top:
                ch = it.get("chg")
                d = f" ({'▲' if ch > 0 else '▼'}{abs(ch):,})" if ch else ""
                lines.append(f"• {it['name'][:26]}: <b>{it['best']:,}円</b> @{shop[it['best_shop']]}{d}")
    gap = sorted([i for i in items if i["n_shops"] > 1], key=lambda x: -x["spread"])[:5]
    if gap:
        lines.append("\n<b>💡 Chênh lệch giữa tiệm lớn nhất</b>")
        lines += [f"• {i['name'][:26]}: +{i['spread']:,}円 → bán ở {shop[i['best_shop']]}" for i in gap]
    drops = [i for i in items if i.get("chg") and i["best"] and -i["chg"] / (i["best"] - i["chg"]) >= 0.05][:8]
    if drops:
        lines.append("\n<b>⚠️ Giảm ≥5% so với hôm trước</b>")
        lines += [f"• {i['name'][:26]}: ▼{-i['chg']:,}円" for i in drops]
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", timeout=45,
                  data={"chat_id": chat, "text": "\n".join(lines), "parse_mode": "HTML", "disable_web_page_preview": "true"})


def main():
    mode = "hot" if "--hot" in sys.argv else "full"
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    if "--no-scrape" not in sys.argv:
        status = scrape(mode, only)
    else:
        status = json.loads((RAW / "_status.json").read_text(encoding="utf-8"))
    items = aggregate(load_rows())
    if not items:
        print("no data")
        return 1
    cats = write_outputs(items, status)
    print("TOTAL", len(items), {k: (v["count"], v["multi"]) for k, v in cats.items()})
    if "--telegram" in sys.argv:
        telegram(items)
    return 0


if __name__ == "__main__":
    sys.exit(main())
