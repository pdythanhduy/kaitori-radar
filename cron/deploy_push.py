"""Deploy worker kaitori-push (cron/push.js) bằng Cloudflare API.

Giữ nguyên: KV "KV", VAPID_PUBLIC (đọc từ .env), secret VAPID_PRIVATE_JWK (keep_bindings), cron triggers.
Thêm: Durable Object "STATS" (class Stats, SQLite) đếm sự kiện ẩn danh từ web; secret EV_KEY (đọc /stats) lấy từ .env (tự tạo nếu chưa có).
Chạy:  python cron/deploy_push.py
"""
from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
ACCOUNT = "21186a602ea3d306043c5ea72d4bb8b1"
SCRIPT = "kaitori-push"
KV_ID = "1909f999564d432ca17a4c85bdba8bde"


def env() -> dict:
    out = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def main() -> None:
    e = env()
    h = {"Authorization": "Bearer " + e["CF_WORKER_TOKEN"]}
    base = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/workers/scripts/{SCRIPT}"
    cur = requests.get(base + "/settings", headers=h, timeout=30).json()
    compat = (cur.get("result") or {}).get("compatibility_date") or "2024-09-23"
    meta = {
        "main_module": "push.js",
        "compatibility_date": compat,
        "bindings": [
            {"type": "kv_namespace", "name": "KV", "namespace_id": KV_ID},
            {"type": "plain_text", "name": "VAPID_PUBLIC", "text": e["VAPID_PUBLIC"]},
            {"type": "durable_object_namespace", "name": "STATS", "class_name": "Stats"},
        ],
        "keep_bindings": ["secret_text"],
    }
    tags = [b.get("class_name") for b in (cur.get("result") or {}).get("bindings", []) if b["type"] == "durable_object_namespace"]
    if "Stats" not in tags:
        meta["migrations"] = {"new_tag": "v1", "new_sqlite_classes": ["Stats"]}
    code = (ROOT / "cron" / "push.js").read_bytes()
    r = requests.put(base, headers=h, timeout=60, files={
        "metadata": (None, json.dumps(meta), "application/json"),
        "push.js": ("push.js", code, "application/javascript+module"),
    }).json()
    print("deploy:", r.get("success"), r.get("errors") or "")
    if r.get("success"):
        key = e.get("EV_KEY")
        if not key:
            import secrets
            key = secrets.token_urlsafe(24)
            with open(ROOT / ".env", "a", encoding="utf-8") as f:
                f.write("\nEV_KEY=" + key + "\n")
            print("EV_KEY: đã tạo mới và ghi vào .env")
        s = requests.put(base + "/secrets", headers=h, timeout=30, json={"name": "EV_KEY", "text": key, "type": "secret_text"}).json()
        print("secret EV_KEY:", s.get("success"), s.get("errors") or "")
    st = requests.get(base + "/settings", headers=h, timeout=30).json()
    print("bindings:", [(b["type"], b["name"]) for b in st["result"]["bindings"]])
    sch = requests.get(base + "/schedules", headers=h, timeout=30).json()
    print("crons:", [s["cron"] for s in (sch.get("result") or {}).get("schedules", [])])


if __name__ == "__main__":
    main()
