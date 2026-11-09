"""Mỗi sáng gửi Telegram: hôm qua (giờ Nhật) kaitoriprice.com có bao nhiêu lượt truy cập + phân tích ngắn.

Cần:
  - C:\\Users\\thanh\\kaitori-radar\\.env có dòng  CF_API_TOKEN=...  (Cloudflare API token quyền "Account Analytics: Read")
  - Telegram dùng chung bot với deal-hunter (C:\\Users\\thanh\\deal-hunter\\.env)
Chạy thử:  python marketing/daily_traffic.py --dry   (in ra màn hình, không gửi)
"""
from __future__ import annotations

import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ACCOUNT = "21186a602ea3d306043c5ea72d4bb8b1"
HOST = "kaitoriprice.com"
ROOT = Path(__file__).resolve().parent.parent
JST = timezone(timedelta(hours=9))


def env(path: Path) -> dict:
    out = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


E = {**env(Path(r"C:\Users\thanh\deal-hunter\.env")), **env(ROOT / ".env")}
H = {"Authorization": f"Bearer {E.get('CF_API_TOKEN', '')}"}


def site_tag() -> str:
    r = requests.get(f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/rum/site_info/list", headers=H, timeout=30).json()
    if not r.get("success"):
        raise RuntimeError("Cloudflare: " + "; ".join(e.get("message", "") for e in r.get("errors", [])))
    for s in r["result"]:
        if s.get("host") == HOST or HOST in str(s.get("ruleset", {}).get("zone_name", "")):
            return s["site_tag"]
    return r["result"][0]["site_tag"]


Q = """query($a:String!,$f:AccountRumPageloadEventsAdaptiveGroupsFilter_InputObject){viewer{accounts(filter:{accountTag:$a}){
 t:rumPageloadEventsAdaptiveGroups(limit:1,filter:$f){count sum{visits}}
 ref:rumPageloadEventsAdaptiveGroups(limit:200,filter:$f){sum{visits} dimensions{refererHost}}
 path:rumPageloadEventsAdaptiveGroups(limit:200,filter:$f){count dimensions{requestPath}}
 dev:rumPageloadEventsAdaptiveGroups(limit:10,filter:$f){sum{visits} dimensions{deviceType}}
 cty:rumPageloadEventsAdaptiveGroups(limit:50,filter:$f){sum{visits} dimensions{countryName}}
}}}"""


def day(tag: str, d0: datetime) -> dict:
    f = {"requestHost": HOST, "bot": 0, "datetime_geq": d0.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
         "datetime_lt": (d0 + timedelta(days=1)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    r = requests.post("https://api.cloudflare.com/client/v4/graphql", headers=H, timeout=60,
                      json={"query": Q, "variables": {"a": ACCOUNT, "f": f}}).json()
    if r.get("errors") and "bot" in str(r["errors"]):  # phòng khi trường bot không lọc được
        f.pop("bot")
        r = requests.post("https://api.cloudflare.com/client/v4/graphql", headers=H, timeout=60,
                          json={"query": Q, "variables": {"a": ACCOUNT, "f": f}}).json()
    if r.get("errors"):
        raise RuntimeError("Cloudflare GraphQL: " + r["errors"][0].get("message", "lỗi"))
    a = r["data"]["viewer"]["accounts"][0]
    t = a["t"][0] if a["t"] else {"count": 0, "sum": {"visits": 0}}
    ref = Counter()
    for g in a["ref"]:
        h = g["dimensions"]["refererHost"] or ""
        h = "Facebook" if "facebook" in h else "Google" if "google" in h else "Gõ thẳng / Zalo / LINE" if not h or HOST in h else h
        ref[h] += g["sum"]["visits"]
    return {"visits": t["sum"]["visits"], "views": t["count"], "ref": ref,
            "path": Counter({g["dimensions"]["requestPath"]: g["count"] for g in a["path"]}),
            "dev": Counter({g["dimensions"]["deviceType"]: g["sum"]["visits"] for g in a["dev"]}),
            "cty": Counter({g["dimensions"]["countryName"]: g["sum"]["visits"] for g in a["cty"]})}


NAMES = {"/": "Trang chủ (JP)", "/vi/": "Trang chủ (VI)", "/guide/vi/": "Mục mẹo (VI)", "/guide/phieu-co-dong/": "Phiếu cổ đông",
         "/guide/tiem-kaitori/": "Danh sách tiệm", "/guide/meo-mua-re/": "Mẹo mua rẻ", "/share/": "Ảnh giá /share/"}


def pct(a, b):
    if not b:
        return ""
    d = (a - b) / b * 100
    return f" ({'▲' if d >= 0 else '▼'}{abs(d):.0f}% so với hôm kia)"


def report() -> str:
    tag = ""
    today = datetime.now(JST).replace(hour=0, minute=0, second=0, microsecond=0)
    y, p = day(tag, today - timedelta(days=1)), day(tag, today - timedelta(days=2))
    dname = (today - timedelta(days=1)).strftime("%d/%m")
    v = y["visits"] or 1
    lines = [f"📊 <b>kaitoriprice.com – hôm qua {dname}</b>",
             f"👥 Lượt truy cập: <b>{y['visits']:,}</b>{pct(y['visits'], p['visits'])}",
             f"📄 Lượt xem trang: {y['views']:,} (TB {y['views'] / v:.1f} trang/lượt)", "",
             "🔗 Nguồn: " + ", ".join(f"{k} {n * 100 // v}%" for k, n in y["ref"].most_common(3)),
             "📱 Điện thoại: " + f"{y['dev'].get('mobile', 0) * 100 // v}%",
             "📄 Xem nhiều: " + ", ".join(f"{NAMES.get(k, k)} {n}" for k, n in y["path"].most_common(4))]
    # phân tích ngắn
    notes = []
    fb, gg = y["ref"].get("Facebook", 0), y["ref"].get("Google", 0)
    if p["visits"] and y["visits"] < p["visits"] * 0.8:
        notes.append("Lượt vào giảm rõ → hôm nay nên đăng 1 bài giá mới trong nhóm/trang.")
    elif p["visits"] and y["visits"] > p["visits"] * 1.2:
        notes.append("Tăng tốt → giữ nhịp đăng bài + bình luận như hôm qua.")
    if fb > v * 0.6:
        notes.append(f"Facebook mang về {fb * 100 // v}% → phụ thuộc FB, nên đều tay bài/bình luận.")
    notes.append("Google: " + (f"{gg} lượt – bắt đầu có khách tìm kiếm 👍" if gg >= 5 else "gần như chưa có, SEO cần thêm thời gian."))
    jp = y["cty"].get("JP", 0) + y["cty"].get("Japan", 0)
    if jp and jp < v * 0.8:
        notes.append(f"Chỉ {jp * 100 // v}% từ Nhật (phần còn lại phần lớn là bot của FB đọc link).")
    lines += ["", "💡 " + "\n💡 ".join(notes[:3])]
    try:  # hành vi: tìm gì, bấm sang tiệm nào (worker kaitori-push /stats)
        from events_report import summary
        d = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        lines += ["", summary(d, d)]
    except Exception as e:
        lines += ["", f"🧭 Hành vi: lỗi đọc sự kiện ({e})"]
    return "\n".join(lines)


def send(text: str):
    tok, chat = E.get("TELEGRAM_BOT_TOKEN"), E.get("TELEGRAM_CHAT_ID")
    import html  # escape mọi thứ, chỉ giữ thẻ <b> (vd '<5s', '>7 ngày' làm Telegram báo 400)
    text = html.escape(text, quote=False).replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
    r = requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", timeout=45,
                      data={"chat_id": chat, "text": text[:4000], "parse_mode": "HTML", "disable_web_page_preview": "true"})
    if not r.ok:
        raise RuntimeError(f"Telegram lỗi {r.status_code}")


if __name__ == "__main__":
    try:
        if not E.get("CF_API_TOKEN"):
            raise RuntimeError("chưa có CF_API_TOKEN trong C:\\Users\\thanh\\kaitori-radar\\.env")
        msg = report()
    except Exception as e:  # báo lỗi qua Telegram để biết mà sửa
        msg = f"⚠️ Báo cáo truy cập kaitoriprice.com lỗi: {e}"
    if "--dry" in sys.argv:
        print(msg)
    else:
        send(msg)
