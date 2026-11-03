"""Soạn 5 bài/ngày cho nhóm FB "Săn Giá Kaitori Nhật Bản" (nhóm của mình → được để link).
Nội dung cho người muốn kiếm thêm tiền từ mua–bán kaitori: số liệu THẬT từ site/data (cập nhật mỗi giờ),
nói rõ lời/lỗ, không hứa hẹn thu nhập.

  python marketing/group_posts.py --slot 1      # in bài khung 1 (1..5)
  python marketing/group_posts.py --all         # xem trước cả 5 bài
  python marketing/group_posts.py --log 1 "<link bài>"   # ghi marketing/post_log.md + gửi Telegram

Khung giờ (JST): 1=08:47 lời/lỗ iPhone giá Apple · 2=11:47 chênh giá giữa tiệm · 3=14:47 biến động giá
                 4=18:47 bài học kiếm tiền (xoay vòng) · 5=21:17 máy game / thẻ Pokémon + câu hỏi
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "site" / "data"
SITE = "https://kaitoriprice.com"
LOG = Path(__file__).resolve().parent / "post_log.md"
SHOPS = {"rudeya": "買取ルデヤ", "panda": "PANDA買取", "mobile_ichiban": "モバイル一番", "morimori": "森森買取", "toban": "買取当番",
         "guestmobile": "ゲストモバイル", "keitaigod": "ケータイゴッド", "homura": "買取ホムラ", "ichome": "買取1丁目"}


def yen(n: int) -> str:
    return f"{n:,}".replace(",", ".") + "円"


def cat(c: str) -> list:
    p = DATA / "cat" / f"{c}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def q(name: str) -> str:
    return f"{SITE}/vi/?q={quote(name)}"


def shop(sid: str) -> str:
    return SHOPS.get(sid, sid)


def low(it) -> tuple[str, int]:
    s, p = min(it["prices"].items(), key=lambda kv: kv[1]["price"])
    return s, p["price"]


def short(name: str) -> str:
    n = re.sub(r"\s+[A-Z0-9]{4,}J/A.*$", "", name)          # bỏ mã model kiểu MDYT4J/A,...
    return re.sub(r"\s+", " ", n).strip()[:60]


def sane(it) -> bool:
    """Bỏ món mà giá cao nhất chỉ 1 tiệm trả, lệch hẳn các tiệm khác (thường do ghép nhầm mẫu/tình trạng)."""
    ps = sorted((p["price"] for p in it["prices"].values()), reverse=True)
    return len(ps) >= 3 and ps[1] >= ps[0] * 0.93 and ps[-1] >= ps[0] * 0.65


def ref(it) -> str:
    return " (森森 nhập mã giới thiệu 75798 được thêm 3.000円)" if it.get("best_shop") == "morimori" else ""


def updated() -> str:
    return json.loads((DATA / "index.json").read_text(encoding="utf-8")).get("updated", "")


FOOT = "\n\n👉 Giá 9 tiệm cập nhật mỗi giờ: {url}\n(Giá công khai trên web các tiệm lúc {upd}. Chưa tính điểm thưởng, phí ship. Bán thật có thể khác một chút.)"


# ------------------------------------------------------------------ 1. lời/lỗ iPhone mua giá Apple
def post1() -> str:
    its = [i for i in cat("phone") if i.get("msrp") and re.match(r"iPhone (18|Duo)\b", i["key"]) and i["n_shops"] >= 2]
    if not its:
        return ""
    its.sort(key=lambda i: i["best"] - i["msrp"], reverse=True)
    win = [i for i in its if i["best"] > i["msrp"]][:5]
    lose = [i for i in its if i["best"] <= i["msrp"]][-2:]
    L = ["💰 HÔM NAY MUA iPHONE GIÁ APPLE RỒI BÁN KAI THÌ LỜI HAY LỖ?", ""]
    if win:
        L.append("✅ Đang có lời:")
        L += [f"• {i['name']}: Apple {yen(i['msrp'])} → kai {yen(i['best'])} ({shop(i['best_shop'])}) = +{yen(i['best'] - i['msrp'])}{ref(i)}" for i in win]
    if lose:
        L += ["", "❌ Đang lỗ, đừng mua để bán:"]
        L += [f"• {i['name']}: Apple {yen(i['msrp'])} → kai {yen(i['best'])} = −{yen(i['msrp'] - i['best'])}" for i in lose]
    L += ["", f"{len(win)}/{len(its)} mẫu đang có lời. Nhiều người mua máy rồi bán cho tiệm trả cao nhất để kiếm thêm, "
               "nhưng giá kai đổi mỗi ngày: mua lúc lời, máy về lúc giá giảm là lỗ. Luôn kiểm tra lại giá ngay trước khi bán."]
    return "\n".join(L) + FOOT.format(url=f"{SITE}/vi/?q=iPhone", upd=updated())


# ------------------------------------------------------------------ 2. chênh giá giữa các tiệm
def post2() -> str:
    pool = [i for c in ("phone", "game", "tablet") for i in cat(c) if i["n_shops"] >= 3 and i["best"] >= 20000 and sane(i)]
    if not pool:
        return ""
    pool.sort(key=lambda i: (i["best"] - low(i)[1]) / i["best"], reverse=True)
    top = pool[:4]
    L = ["🔀 CÙNG 1 MÓN, BÁN SAI TIỆM LÀ MẤT TIỀN", "", "Hôm nay chênh lệch lớn nhất giữa các tiệm:"]
    for i in top:
        ls, lp = low(i)
        L.append(f"• {short(i['name'])}: {shop(i['best_shop'])} trả {yen(i['best'])}, {shop(ls)} chỉ {yen(lp)} → chênh {yen(i['best'] - lp)}{ref(i)}")
    L += ["", "Cách kiếm thêm đơn giản nhất không cần vốn: đồ bạn ĐÃ có (máy cũ, máy game, hộp thẻ…) đừng bán ở tiệm gần nhà theo thói quen. "
              "So giá trước 1 phút, nhiều khi được thêm cả chục nghìn yên. Ở xa thì hầu hết các tiệm nhận gửi bưu điện (郵送買取).",
              "(Mỗi tiệm có điều kiện riêng về tình trạng máy, phụ kiện, bảo hành; xem ghi chú từng tiệm trên web trước khi gửi.)"]
    return "\n".join(L) + FOOT.format(url=q(top[0]["name"]), upd=updated())


# ------------------------------------------------------------------ 3. biến động giá
def post3() -> str:
    mv = json.loads((DATA / "movers.json").read_text(encoding="utf-8"))
    ok = lambda i: i.get("cat") in ("phone", "game", "card", "tablet") and i.get("best", 0) >= 10000
    big = lambda a: sorted([i for i in a if ok(i) and abs(i.get("mv", 0)) >= 1000], key=lambda i: -abs(i["mv"]))[:4]
    up, dn = big(mv.get("up", [])), big(mv.get("down", []))
    if not up and not dn:
        return ""
    L = ["📊 GIÁ KAI ĐỔI GÌ HÔM NAY?", ""]
    if up:
        L.append("📈 Tăng:")
        L += [f"• {short(i['name'])}: {yen(i['best'])} (▲{yen(abs(i['mv']))})" for i in up]
    if dn:
        L += ["", "📉 Giảm:"]
        L += [f"• {short(i['name'])}: {yen(i['best'])} (▼{yen(abs(i['mv']))})" for i in dn]
    L += ["", "Người buôn kai giỏi không đoán giá, họ THEO DÕI giá. Trên web bấm ♡ món bạn quan tâm, vào mục Của tôi bật 🔔 thông báo: "
              "giá đạt mức bạn đặt là điện thoại báo ngay, khỏi phải mở web canh."]
    return "\n".join(L) + FOOT.format(url=f"{SITE}/vi/", upd=updated())


# ------------------------------------------------------------------ 4. bài học kiếm tiền (xoay vòng theo ngày)
LESSONS = [
    ("📐 CÔNG THỨC TÍNH LỜI KHI MUA ĐỂ BÁN KAI",
     "Lời = Giá kai cao nhất − Giá mua + Điểm thưởng nhận được − Phí đi lại/ship.\n\n"
     "Ví dụ dễ quên: mua ở điện máy được 10% điểm thì giá mua thật chỉ còn 90%. Ngược lại đi tàu 2 chiều 1.000円 cũng là chi phí. "
     "Ghi hết vào là biết món nào đáng làm. Trên web có mục 📦 Kho hàng: nhập giá đã mua, mỗi ngày web tính bán ở đâu lời nhất.",
     "/vi/?v=mine"),
    ("🎟 MUA RẺ 20–30% BẰNG PHIẾU CỔ ĐÔNG (株主優待券)",
     "Nhiều chuỗi điện máy và cửa hàng phát phiếu giảm giá cho cổ đông, và phiếu này được bán lại trên mạng với giá rẻ hơn mệnh giá. "
     "Người mua hàng để bán kai hay dùng để hạ giá vốn. Bài hướng dẫn có danh sách chuỗi, cách mua phiếu và 3 điều cần biết.",
     "/guide/phieu-co-dong/"),
    ("⏰ GIỮ GIÁ TRƯỚC KHI MÁY VỀ: 予約買取",
     "Sợ đặt máy xong, lúc máy về giá kai giảm? Một số tiệm cho đặt trước giá thu mua (予約買取): chốt giá hôm nay, mang máy tới sau. "
     "Cần đọc kỹ hạn giữ giá và quy định huỷ, vì mỗi tiệm khác nhau.",
     "/guide/yoyaku-kaitori/"),
    ("🛒 7 CÁCH MUA HÀNG RẺ HƠN Ở NHẬT",
     "Rakuten, Yahoo!ショッピング, Amazon, điểm điện máy, phiếu cổ đông, trang tích điểm (ポイントサイト), điện thoại \"1 yên\"… "
     "Mua rẻ hơn 5–10% là lời của bạn tăng thêm chừng đó. Bài tổng hợp từng cách và điều kiện cần biết.",
     "/guide/meo-mua-re/"),
    ("❌ GIÁ SẬP THÌ HUỶ ĐƠN THẾ NÀO CHO KHỎI MẤT PHÍ",
     "Quy tắc số 1: huỷ TRƯỚC khi hàng gửi đi. Apple Store huỷ ở trang ご注文状況; đã nhận máy thì vẫn trả được trong 14 ngày nếu còn nguyên. "
     "Theo một bài tổng hợp, docomo online không nhận trả iPhone. Người làm lâu năm luôn biết đường lui trước khi mua.",
     "/guide/huy-iphone/"),
    ("📍 Ở XA TIỆM VẪN BÁN ĐƯỢC GIÁ CAO",
     "Hầu hết các tiệm kaitori lớn nhận gửi bưu điện (郵送買取): đăng ký online, gửi hàng, tiệm kiểm tra rồi chuyển khoản. "
     "Ở Nagoya, Fukuoka hay tỉnh lẻ vẫn bán được giá Tokyo. Danh sách tiệm, địa chỉ, giờ mở cửa ở đây.",
     "/guide/tiem-kaitori/"),
    ("🧾 KIẾM THÊM TỪ MUA BÁN CÓ PHẢI ĐÓNG THUẾ KHÔNG?",
     "Bán đồ dùng cá nhân thường không bị tính thuế. Nhưng mua về để bán kiếm lời là có thu nhập. Người đi làm công ty có thu nhập phụ "
     "(lời sau khi trừ chi phí) trên 20万円/năm thì phải 確定申告; dưới mức đó vẫn phải khai thuế cư trú (住民税). "
     "Giữ hoá đơn mua và giấy bán để tính đúng. Trường hợp cụ thể nên hỏi 税務署.",
     "/vi/"),
    ("🪪 KHI NÀO CẦN GIẤY PHÉP 古物商?",
     "Mua đồ CŨ của người khác để bán lại thường xuyên thì cần 古物商許可 (xin ở đồn cảnh sát, 公安委員会). "
     "Tự mua hàng mới ở cửa hàng rồi bán cho tiệm kaitori thì thường không cần. Làm lớn hoặc không chắc, hãy hỏi đồn cảnh sát nơi bạn ở trước khi làm.",
     "/vi/"),
    ("⚠️ 3 SAI LẦM LÀM LỖ CỦA NGƯỜI MỚI",
     "1) Thấy lời hôm nay là mua liền nhiều máy, máy về thì giá đã giảm. 2) Bán ở tiệm đầu tiên, không so giá. "
     "3) Mở hộp, bóc màng, kích hoạt máy, mất giá \"mới chưa mở\". Bắt đầu nhỏ: 1 máy, tính đủ chi phí, bán xong rồi mới làm tiếp.",
     "/vi/"),
    ("🃏 HỘP THẺ POKÉMON: VÌ SAO GIỮ MÀNG CO (シュリンク)?",
     "Hộp thẻ Pokémon còn nguyên màng co mới được giá cao; bóc màng hoặc màng rách là tiệm trả thấp hơn nhiều. "
     "Giá hộp đổi rất nhanh theo đợt phát hành. Bảng so giá nhiều tiệm cho 30 hộp đang được thu mua nhiều nhất.",
     "/guide/pokeca-box-kaitori/"),
    ("🔔 ĐỂ ĐIỆN THOẠI CANH GIÁ GIÙM BẠN",
     "Không cần ngồi F5 cả ngày. Trên kaitoriprice: bấm ♡ món muốn theo dõi → vào Của tôi → bật 🔔 thông báo, đặt mức giá (ví dụ ≥ 380.000円). "
     "Giá chạm mức là điện thoại báo. iPhone thì thêm web vào Màn hình chính trước rồi mới bật được.",
     "/vi/?v=mine"),
    ("💸 ĐỪNG VAY TIỀN ĐỂ BUÔN KAI",
     "Lời mỗi máy thường chỉ vài nghìn tới vài chục nghìn yên, mà giá có thể giảm mạnh trong vài ngày. Dùng tiền nhàn rỗi, "
     "trả thẻ đúng hạn (trễ hạn thẻ tín dụng ảnh hưởng uy tín tín dụng ở Nhật). Kiếm thêm là để dư dả hơn, không phải để ôm nợ.",
     "/vi/"),
]


def post4(day: int) -> str:
    title, body, path = LESSONS[day % len(LESSONS)]
    return f"{title}\n\n{body}\n\n👉 Đọc thêm: {SITE}{path}"


# ------------------------------------------------------------------ 5. máy game / thẻ Pokémon + câu hỏi
def post5(day: int) -> str:
    if day % 2:
        pool = [i for i in cat("card") if i["key"].startswith("box:") and i["n_shops"] >= 3]
        head, ask = "🃏 GIÁ THU MUA HỘP THẺ POKÉMON CAO NHẤT HÔM NAY", "Bạn đang giữ hộp nào? Comment tên hộp, mình xem giá giúp 👇"
    else:
        pool = [i for i in cat("game") if i["n_shops"] >= 3]
        head, ask = "🎮 GIÁ THU MUA MÁY GAME HÔM NAY", "Nhà bạn có máy game nào ít chơi không? Comment tên máy, mình xem đang bán được bao nhiêu 👇"
    if not pool:
        return ""
    pool = [i for i in pool if sane(i)]
    pool.sort(key=lambda i: i["best"], reverse=True)
    L = [head, ""]
    for i in pool[:6]:
        ls, lp = low(i)
        L.append(f"• {short(i['name'])}: {yen(i['best'])} ({shop(i['best_shop'])})" + (f", tiệm thấp nhất {yen(lp)}" if lp < i["best"] else ""))
    L += ["", "Đồ để trong tủ không chơi nữa cũng là tiền. Bán đúng tiệm trả cao nhất là cách kiếm thêm không cần bỏ vốn.", "", ask]
    return "\n".join(L) + FOOT.format(url=f"{SITE}/vi/", upd=updated())


def make(slot: int) -> str:
    day = datetime.now().timetuple().tm_yday
    return {1: post1, 2: post2, 3: post3, 4: lambda: post4(day), 5: lambda: post5(day)}[slot]()


def log(slot: int, link: str) -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from daily_traffic import JST, send
    now = datetime.now(JST)
    first = make(slot).splitlines()[0]
    if not LOG.exists():
        LOG.write_text("# Bài đăng nhóm Săn Giá Kaitori\n\nngày | giờ | khung | tiêu đề | link\n", encoding="utf-8")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{now:%Y-%m-%d} | {now:%H:%M} | {slot} | {first} | {link}\n")
    today = [l for l in LOG.read_text(encoding="utf-8").splitlines() if l.startswith(f"{now:%Y-%m-%d} |")]
    send(f"📝 <b>Nhóm Săn Giá Kaitori: bài {len(today)}/5 hôm nay</b>\n{first}\n{link}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--all"]:
        for s in range(1, 6):
            print(f"===== Khung {s} =====\n{make(s)}\n")
    elif a[:1] == ["--slot"]:
        print(make(int(a[1])))
    elif a[:1] == ["--log"]:
        log(int(a[1]), a[2] if len(a) > 2 else "")
        print("Đã ghi log + gửi Telegram.")
    else:
        print(__doc__)
