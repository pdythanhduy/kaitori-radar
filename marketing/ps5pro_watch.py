"""Canh PS5 Pro (user 22/11/2026): báo Telegram khi Yodobashi / Joshin / Edion / BicCamera.com / AEON đổi trạng thái bán.

Trang tiệm chặn truy cập tự động (403 / Cloudflare / Akamai) → KHÔNG đọc thẳng, không lách chống bot.
Nguồn: bài tổng hợp công khai của Goal.com (cập nhật trạng thái từng tiệm, thường mỗi ngày).
Chạy:  PYTHONUTF8=1 python marketing/ps5pro_watch.py          (báo khi có thay đổi)
       PYTHONUTF8=1 python marketing/ps5pro_watch.py --show   (in trạng thái, không gửi)
"""
import html
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from daily_traffic import send  # noqa: E402

URL = "https://www.goal.com/jp/%E3%83%8B%E3%83%A5%E3%83%BC%E3%82%B9/where-to-buy-ps5-pro/blt8304e88ea34434c3"
STATE = Path(__file__).parent / "ps5pro_state.json"
JST = timezone(timedelta(hours=9))

# tên trong bảng Goal.com → tên ngắn + link trang tiệm
STORES = {
    "ヨドバシ・ドット・コム": ("Yodobashi", "https://www.yodobashi.com/product/100000001008732356/"),
    "Joshin webショップ": ("Joshin", "https://joshinweb.jp/game/56666/4948872417075.html"),
    "エディオン": ("Edion", "https://www.edion.com/detail.html?p_cd=00084715654"),
    "ビックカメラ.com": ("BicCamera.com", "https://www.biccamera.com/bc/item/14719703/"),
    "イオンスタイルオンライン": ("AEON", "https://www.aeonretail.com/"),
}
SOLD_OUT = ("完売", "売り切れ", "販売終了", "販売休止", "入荷待ち", "受付終了", "終了")


def fetch_lines() -> list[str]:
    r = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0 (compatible; kaitori-radar-watch/1.0)"})
    r.raise_for_status()
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", r.text, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", t))
    return [x.strip() for x in t.split("\n") if x.strip()]


def parse(lines: list[str]) -> dict:
    st = {}
    for i, x in enumerate(lines[:-2]):
        if x in STORES and "ネット" in lines[i + 1] and x not in st:  # bảng: tiệm / kiểu bán / trạng thái
            st[x] = lines[i + 2]
    upd = next((m.group(1) for x in lines if (m := re.search(r"【(\d+月\d+日)更新】", x))), "")
    # mục bốc thăm: lấy đoạn sau tiêu đề "抽選・招待" để phát hiện đợt mới
    lot = ""
    for i, x in enumerate(lines):
        if "抽選・招待" in x and len(x) < 60:
            lot = " | ".join(lines[i + 1:i + 40])
            lot = re.sub(r"\d+月\d+日\(.\)時点で?", "", lot)  # câu "11月20日(金)時点" đổi mỗi ngày, không phải tin mới
            break
    return {"stores": st, "updated": upd, "lottery": lot}


def main():
    cur = parse(fetch_lines())
    if len(cur["stores"]) < 3:  # trang đổi bố cục → báo 1 lần để sửa parser
        msg = f"⚠️ Bot PS5 Pro: không đọc được bảng tiệm trên Goal.com (thấy {len(cur['stores'])}/5) — cần sửa parser."
        old = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
        if old.get("parse_err") != datetime.now(JST).strftime("%F") and "--show" not in sys.argv:
            send(msg)
            old["parse_err"] = datetime.now(JST).strftime("%F")
            STATE.write_text(json.dumps(old, ensure_ascii=False, indent=1), encoding="utf-8")
        print(msg)
        return
    if "--show" in sys.argv:
        print(json.dumps(cur, ensure_ascii=False, indent=1)[:1500])
        return
    old = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else None
    STATE.write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8")
    if old is None:
        print("lần đầu: đã lưu trạng thái", cur["stores"])
        return
    out = []
    for k, (short, link) in STORES.items():
        a, b = old.get("stores", {}).get(k), cur["stores"].get(k)
        if b and a != b:
            hot = not any(w in b for w in SOLD_OUT)
            out.append(f"{'🟢' if hot else '⚪'} <b>{short}</b>: {a or '?'} → <b>{b}</b>{'  ← CÓ THỂ ĐANG BÁN' if hot else ''}\n{link}")
    if cur["lottery"] and old.get("lottery") and cur["lottery"] != old["lottery"]:
        out.append("🎟 Mục bốc thăm/mời mua trên bài tổng hợp vừa thay đổi — có thể có đợt bốc thăm mới.")
    if out:
        send("🎮 <b>PS5 Pro — có thay đổi</b>\n" + "\n".join(out)
             + f"\n(nguồn: Goal.com, bài cập nhật {cur['updated'] or '?'}; kiểm tra lại trên trang tiệm)\n{URL}")
        print("đã gửi:", out)
    else:
        print("không đổi", cur["updated"], cur["stores"])


if __name__ == "__main__":
    main()
