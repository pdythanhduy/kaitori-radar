"""Số liệu thật cho bài Pokémon hằng ngày: box nóng (nhiều tiệm), biến động N ngày, tiếng lóng nhóm FB → tên SP.

Chạy:  PYTHONUTF8=1 python marketing/pokemon_insight.py            (in bảng, dùng để viết bài)
       PYTHONUTF8=1 python marketing/pokemon_insight.py --json     (JSON cho script khác)
Chỉ in số có trong site/data (giá cao nhất các tiệm, máy/hộp mới chưa bóc). Không suy đoán.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "site" / "data"

# tiếng lóng trong nhóm "POKEMON NHẬT BẢN" → mẩu tên SP trong card.json (khớp chuỗi con)
SLANG = {
    "set 9": "30th CELEBRATION カードセット 9種セット",
    "30th (box)": "【M6a】  30th CELEBRATION",
    "dekki mèo": "30th CELEBRATION プレミアムデッキセット エーフィ・ブラッキー",
    "Dream": "メガドリームex",
    "Inferno X": "【M2】インフェルノX",
    "Ninja Spinner": "ニンジャスピナー",
    "Mega Brave": "メガブレイブ",
    "Mega Symphonia": "メガシンフォニア",
}


def load():
    items = json.loads((DATA / "cat" / "card.json").read_text(encoding="utf-8"))
    hist = json.loads((DATA / "hist" / "card.json").read_text(encoding="utf-8"))
    idx = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    return items, hist, idx


def row(it, hist, shops):
    s = [x for x in hist.get(it["key"], []) if len(x) > 2]  # 10/11: bỏ điểm đầu không ghi tiệm (dữ liệu ngày đầu chưa đủ tiệm)
    first = s[0][1] if s else it["best"]
    top = sorted(it["prices"].items(), key=lambda x: -x[1]["price"])[:3]
    return {
        "name": it["name"].strip(), "best": it["best"], "shop": shops.get(it["best_shop"], {}).get("name", it["best_shop"]),
        "n_shops": it["n_shops"], "from_day": s[0][0] if s else "", "from": first, "chg_n": it["best"] - first,
        "pct_n": round((it["best"] - first) / first * 100, 1) if first else 0.0, "days": len(s),
        "chg_1d": it.get("chg", 0), "top3": [(shops.get(k, {}).get("name", k), p["price"]) for k, p in top],
    }


def main():
    items, hist, idx = load()
    shops = idx["shops"]
    import re
    # 10/11: bỏ ONE PIECE (OP-/EB-/PRB-/ST-) — bài là Pokémon; OP-03/06/17 từng báo −90% do ghép nhầm
    boxes = [i for i in items if i["n_shops"] >= 3 and "PSA" not in i["name"] and not i["key"].startswith("single")
             and not re.match(r"(box|name):(op|eb|prb|st)\d", i["key"]) and not re.search(r"【(OP|EB|PRB|ST)-?\d", i["name"])
             and "ONE PIECE" not in i["name"].upper()]
    rows = [row(i, hist, shops) for i in boxes]
    # biến động > ±40% trong vài ngày gần như luôn là lỗi ghép mẫu → để riêng, không đưa vào bài
    sus = [r for r in rows if abs(r["pct_n"]) > 40]
    movers = sorted([r for r in rows if r["days"] >= 3 and r["from"] and abs(r["pct_n"]) <= 40], key=lambda r: r["pct_n"])
    slang = {}
    for k, frag in SLANG.items():
        hit = sorted([i for i in items if frag in i["name"]], key=lambda x: -x["n_shops"])
        if hit:
            slang[k] = row(hit[0], hist, shops)
    out = {"updated": idx.get("updated"), "down": [r for r in movers if r["pct_n"] < 0][:8],
           "up": [r for r in movers[::-1] if r["pct_n"] > 0][:8], "slang": slang, "suspect": sus}
    if "--json" in sys.argv:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return
    y = lambda n: f"{n:,}円"
    print(f"Cập nhật {out['updated']} · box có ≥3 tiệm: {len(rows)}")
    for title, arr in (("📉 Giảm mạnh nhất", out["down"]), ("📈 Tăng mạnh nhất", out["up"])):
        print(f"\n{title} ({arr[0]['from_day'] if arr else ''} → nay):")
        for r in arr:
            print(f"  • {r['name'][:38]}: {y(r['from'])} → {y(r['best'])} ({r['chg_n']:+,}円, {r['pct_n']:+}%) · {r['shop']} · {r['n_shops']} tiệm")
    print("\n🗣 Tiếng lóng nhóm → giá kai hiện tại:")
    for k, r in slang.items():
        print(f"  • {k}: {y(r['best'])} ({r['shop']}), {r['from_day']} {y(r['from'])} → nay · top3 {', '.join(f'{a} {y(b)}' for a, b in r['top3'])}")


if __name__ == "__main__":
    main()
