// kaitori-push: cảnh báo giá qua Web Push (không cần đăng nhập).
// - Trình duyệt đăng ký: POST /sub {sub, items:[{cat,key,name,target}]}  → lưu KV "s:<hash>"
// - Huỷ:                POST /unsub {endpoint}
// - Service worker hỏi nội dung: POST /msg {endpoint} → {title, body, url} (push gửi đi KHÔNG kèm dữ liệu → khỏi mã hoá)
// - Cron (sau mỗi lượt cập nhật giá): đọc giá mới trên kaitoriprice.com, món nào đạt điều kiện → gửi push.
// Bindings: KV namespace "KV"; secret VAPID_PRIVATE_JWK (JSON JWK P-256); var VAPID_PUBLIC (base64url).
// Điều kiện báo: có target → giá cao nhất ≥ target (báo 1 lần, rồi chờ giá xuống dưới target mới báo lại);
//                không target → giá cao nhất đổi ≥ 2% so với lần báo trước.
// - Sự kiện ẩn danh từ web: POST /ev {e,a,b,p,l} → Durable Object "Stats" (SQLite) cộng dồn theo ngày JST.
//   Đọc báo cáo: GET /stats?key=<EV_KEY>&days=7  (EV_KEY là secret). Không lưu IP / định danh.
import { DurableObject } from "cloudflare:workers";

export class Stats extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.sql.exec("CREATE TABLE IF NOT EXISTS ev (day TEXT, e TEXT, a TEXT, b TEXT, p TEXT, l TEXT, c TEXT, n INTEGER, PRIMARY KEY (day, e, a, b, p, l, c))");
  }
  add(r) {
    const day = new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
    this.sql.exec("INSERT INTO ev VALUES (?, ?, ?, ?, ?, ?, ?, 1) ON CONFLICT DO UPDATE SET n = n + 1", day, r.e, r.a, r.b, r.p, r.l, r.c);
  }
  rows(days) {
    const from = new Date(Date.now() + 9 * 3600e3 - (days - 1) * 86400e3).toISOString().slice(0, 10);
    this.sql.exec("DELETE FROM ev WHERE day < ?", new Date(Date.now() - 120 * 86400e3).toISOString().slice(0, 10));  // giữ 120 ngày
    return this.sql.exec("SELECT day, e, a, b, p, l, c, n FROM ev WHERE day >= ? ORDER BY day, n DESC", from).toArray();
  }
}

const SITE = "https://kaitoriprice.com";
const MOVE = 0.02;
const MAX_ITEMS = 30;
const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET, POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type" };
const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { "Content-Type": "application/json", ...CORS } });

const b64u = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const enc = new TextEncoder();
async function idOf(endpoint) {
  return "s:" + b64u(await crypto.subtle.digest("SHA-256", enc.encode(endpoint))).slice(0, 32);
}

let KEY = null;
async function vapidJwt(env, aud) {
  if (!KEY) KEY = await crypto.subtle.importKey("jwk", { ...JSON.parse(env.VAPID_PRIVATE_JWK), ext: true }, { name: "ECDSA", namedCurve: "P-256" }, false, ["sign"]);
  const h = b64u(enc.encode(JSON.stringify({ typ: "JWT", alg: "ES256" })));
  const c = b64u(enc.encode(JSON.stringify({ aud, exp: Math.floor(Date.now() / 1000) + 12 * 3600, sub: "https://kaitoriprice.com" })));
  const sig = await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, KEY, enc.encode(h + "." + c));
  return h + "." + c + "." + b64u(sig);
}
async function push(env, endpoint) {
  const aud = new URL(endpoint).origin;
  const r = await fetch(endpoint, { method: "POST", headers: {
    Authorization: `vapid t=${await vapidJwt(env, aud)}, k=${env.VAPID_PUBLIC}`, TTL: "43200", Urgency: "normal", "Content-Length": "0" } });
  return r.status;
}

function clean(items) {
  return (Array.isArray(items) ? items : []).slice(0, MAX_ITEMS).filter((i) => i && i.cat && i.key).map((i) => ({
    cat: String(i.cat).slice(0, 20), key: String(i.key).slice(0, 200), name: String(i.name || i.key).slice(0, 120),
    target: Math.max(0, Math.round(+i.target || 0)), last: Math.round(+i.last || 0) }));
}

async function check(env) {
  const cache = {};
  const cat = async (c) => (cache[c] ??= fetch(`${SITE}/data/cat/${encodeURIComponent(c)}.json`, { cf: { cacheTtl: 60 } })
    .then((r) => (r.ok ? r.json() : [])).then((a) => new Map((Array.isArray(a) ? a : a.items || []).map((it) => [it.key, it]))).catch(() => new Map()));
  let cursor, sent = 0, gone = 0;
  do {
    const page = await env.KV.list({ prefix: "s:", cursor });
    for (const k of page.keys) {
      const rec = await env.KV.get(k.name, "json");
      if (!rec) continue;
      const hits = [];
      for (const it of rec.items) {
        const cur = (await cat(it.cat)).get(it.key);
        if (!cur || !cur.best) continue;
        const p = cur.best, shop = cur.best_shop;
        if (it.target) {
          if (p >= it.target && !it.fired) { hits.push({ it, p, shop, up: true }); it.fired = true; }
          else if (p < it.target) it.fired = false;
        } else if (it.last && Math.abs(p - it.last) / it.last >= MOVE) hits.push({ it, p, shop, up: p > it.last });
        if (!it.last || hits.some((h) => h.it === it)) it.last = p;
      }
      if (hits.length) {
        const vi = rec.lang !== "ja";
        const f = (h) => `${h.it.name}: ${h.p.toLocaleString("ja-JP")}円 ${h.up ? "▲" : "▼"}${h.it.target && h.up ? (vi ? " (đạt mức bạn đặt)" : "（目標到達）") : ""}`;
        rec.msg = { title: vi ? `🔔 ${hits.length} món bạn theo dõi đổi giá` : `🔔 ウォッチ中の${hits.length}商品の価格が変わりました`,
                    body: hits.slice(0, 4).map(f).join("\n"), url: (vi ? "/vi/" : "/") + "?v=mine&src=push", at: Date.now() };
        const st = await push(env, rec.sub.endpoint).catch(() => 0);
        if (st === 404 || st === 410) { await env.KV.delete(k.name); gone++; continue; }
        sent++;
      }
      await env.KV.put(k.name, JSON.stringify(rec));
    }
    cursor = page.list_complete ? null : page.cursor;
  } while (cursor);
  return { sent, gone };
}

export default {
  async scheduled(event, env, ctx) {
    console.log("push check", JSON.stringify(await check(env)));
  },
  async fetch(request, env, ctx) {
    const u = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });
    if (u.pathname === "/stats") {
      if (!env.EV_KEY || u.searchParams.get("key") !== env.EV_KEY) return json({ error: "forbidden" }, 403);
      const days = Math.max(1, Math.min(120, parseInt(u.searchParams.get("days") || "7", 10) || 7));
      return json({ rows: await env.STATS.get(env.STATS.idFromName("main")).rows(days) });
    }
    if (request.method === "GET") return json({ ok: true, kv: !!env.KV, vapid: !!env.VAPID_PRIVATE_JWK, stats: !!env.STATS });
    if (u.pathname === "/ev") {  // sự kiện ẩn danh từ web (tìm kiếm, bấm sang tiệm…): không lưu IP, không định danh
      const src = request.headers.get("Origin") || request.headers.get("Referer") || "";
      const dev = /^http:\/\/localhost(:\d+)?/.test(src);
      if (env.STATS && (dev || /^https:\/\/(www\.)?kaitoriprice\.com/.test(src))) {
        let e = {}; try { e = JSON.parse((await request.text()).slice(0, 2000)); } catch {}
        const s = (v, n) => String(v ?? "").replace(/[\u0000-\u001f]/g, " ").trim().slice(0, n);
        const name = s(e.e, 40);
        if (/^[a-z_0-9]{2,40}$/.test(name)) {
          const stub = env.STATS.get(env.STATS.idFromName("main"));
          ctx.waitUntil(stub.add({ e: dev ? "dev_" + name : name, a: s(e.a, 100), b: s(e.b, 100), p: s(e.p, 60), l: s(e.l, 4), c: s(request.cf?.country, 4) }));
        }
      }
      return new Response(null, { status: 204, headers: CORS });
    }
    let b; try { b = await request.json(); } catch { return json({ error: "bad json" }, 400); }
    const ep = b?.sub?.endpoint || b?.endpoint;
    if (!ep || !/^https:\/\//.test(ep) || ep.length > 1000) return json({ error: "bad endpoint" }, 400);
    const id = await idOf(ep);
    if (u.pathname === "/sub") {
      const old = (await env.KV.get(id, "json")) || {};
      const prev = new Map((old.items || []).map((i) => [i.cat + "|" + i.key, i]));
      const items = clean(b.items).map((i) => { const o = prev.get(i.cat + "|" + i.key); return o && o.target === i.target ? { ...i, last: o.last || i.last, fired: o.fired } : i; });
      if (!items.length) { await env.KV.delete(id); return json({ ok: true, n: 0 }); }
      const sub = { endpoint: ep, keys: b.sub.keys || {} };
      await env.KV.put(id, JSON.stringify({ sub, items, lang: b.lang === "ja" ? "ja" : "vi", msg: old.msg || null }));
      return json({ ok: true, n: items.length });
    }
    if (u.pathname === "/unsub") { await env.KV.delete(id); return json({ ok: true }); }
    if (u.pathname === "/msg") {
      const rec = await env.KV.get(id, "json");
      return json(rec?.msg || { title: "買取プライス", body: "Giá thu mua đã cập nhật", url: "/vi/?v=mine" });
    }
    if (u.pathname === "/test") {  // gửi thử 1 thông báo cho chính trình duyệt này
      const rec = await env.KV.get(id, "json");
      if (!rec) return json({ error: "not subscribed" }, 404);
      rec.msg = { title: "🔔 買取プライス", body: rec.lang === "ja" ? "通知テストOK" : "Thông báo đã bật! Web sẽ báo khi giá đổi.", url: "/vi/?v=mine" };
      await env.KV.put(id, JSON.stringify(rec));
      return json({ status: await push(env, ep) });
    }
    return json({ error: "not found" }, 404);
  },
};
