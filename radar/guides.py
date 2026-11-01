"""Bài hướng dẫn tiếng Nhật (SEO) — bảng giá trong bài lấy từ dữ liệu mới nhất, sinh lại mỗi lần deploy.

/guide/                      danh sách bài
/guide/iphone-18-kaitori/    iPhone 18シリーズを一番高く売る方法
/guide/pokeca-box-kaitori/   ポケカBOXの買取価格比較
/guide/yoyaku-kaitori/       予約買取とは？
Nội dung chỉ nêu sự thật/lời khuyên chung, không bịa trải nghiệm cá nhân.
"""
from __future__ import annotations

import re


def _yen(n: int) -> str:
    return f"{n:,}円"


def _table(rows: list, shops: dict, e) -> str:
    trs = []
    for it in rows:
        ps = sorted(it["prices"].items(), key=lambda kv: -kv[1]["price"])
        (s1, p1), second = ps[0], (ps[1] if len(ps) > 1 else None)
        name = e(it["name"])
        link = f'<a href="/p/{it["_slug"]}/">{name}</a>' if it.get("_slug") else name
        trs.append(
            f"<tr><td>{link}</td><td><b>{_yen(p1['price'])}</b><br><small>{e(shops.get(s1, {}).get('name', s1))}</small></td>"
            f"<td>{_yen(second[1]['price']) + '<br><small>' + e(shops.get(second[0], {}).get('name', second[0])) + '</small>' if second else '—'}</td>"
            f"<td>{_yen(it['spread']) if it.get('spread') else '—'}</td><td>{it['n_shops']}店</td></tr>")
    return ('<div class="tw"><table class="pt"><thead><tr><th>商品</th><th>最高買取価格</th><th>2番目</th><th>店舗間の差</th><th>比較店舗</th></tr></thead>'
            f"<tbody>{''.join(trs)}</tbody></table></div>")


def _iphone_order(it) -> tuple:
    k = it["key"].split("|")[0]
    m = re.match(r"iPhone (18|Duo|Air)(?: (Pro Max|Pro|Plus))?(?: (\d+)(GB|TB))?", k)
    if not m:
        return (9, 0, 0)
    model = {"Duo": 0, "18": 1, "Air": 2}[m.group(1)]
    sub = {"Pro Max": 0, "Pro": 1, "Plus": 2, None: 3}[m.group(2)]
    cap = int(m.group(3) or 0) * (1024 if m.group(4) == "TB" else 1)
    return (model, sub, cap)


def build(items: dict, shops: dict, updated: str, page, e, site, base: str) -> list:
    """items: {cat: [item,...]} (đã có _slug nếu có trang /p/). Trả về list (path, changefreq)."""
    phones = items.get("phone", [])
    ip18 = [i for i in phones if re.match(r"iPhone (18|Duo)\b", i["key"]) and i["n_shops"] >= 2]
    ip18.sort(key=_iphone_order)
    boxes = [i for i in items.get("card", []) if i["key"].startswith("box:") and i["n_shops"] >= 3]
    boxes.sort(key=lambda i: (-i["n_shops"], -i["best"]))
    boxes = boxes[:30]
    n_shops = len(shops)
    upd = e(updated)
    guides = []

    def write(path, title, desc, h1, body, faq=None):
        ld = [{"@context": "https://schema.org", "@type": "Article", "headline": h1, "dateModified": (updated or "")[:10],
               "author": {"@type": "Organization", "name": "買取プライス"}, "publisher": {"@type": "Organization", "name": "買取プライス"}}]
        if faq:
            ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
            body += "<section><h2>よくある質問</h2>" + "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in faq) + "</section>"
        full = (f'<nav class="bc"><a href="/">トップ</a> › <a href="/guide/">買取ガイド</a> › {e(h1)}</nav>'
                f"<article class=\"guide\"><h1>{e(h1)}</h1><p class=\"upd\">価格データ最終更新：{upd} JST（毎時自動更新）</p>{body}</article>")
        out = site / path.strip("/")
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(page(title, desc, path, full, ld, updated), encoding="utf-8")
        guides.append((path, h1, desc))

    # ---------------------------------------------------------------- 1. iPhone 18
    if ip18:
        top = max(ip18, key=lambda i: i.get("spread") or 0)
        body = f"""
<p>iPhone 18シリーズ（iPhone 18 Pro・18 Pro Max・iPhone Duo）の新品・未開封品は、<b>同じモデルでも買取店によって買取価格が数千円〜数万円違います</b>。
下の表は大手買取店{n_shops}社の公開価格を毎時自動で集計した最新の比較です。</p>
<p class="pt-note">現在、店舗間の差が最も大きいのは <b>{e(top['name'])}</b>（最大 {_yen(top.get('spread') or 0)}）です。</p>
<h2>iPhone 18シリーズ 買取価格比較表（新品・未開封）</h2>
{_table(ip18, shops, e)}
<p class="small">※モデル名をタップすると、全店舗の価格と価格推移を確認できます。</p>
<h2>iPhoneを一番高く売るための5つのポイント</h2>
<ol class="tips">
<li><b>売る直前に複数店舗の価格を比べる</b><br>買取価格は在庫状況や相場で1日に何度も変わります。1店舗だけ見て決めず、直前に比較するのが基本です。</li>
<li><b>色による減額を確認する</b><br>同じモデルでも色によって「-5,000円」「-10,000円」などの減額がある店舗が多くあります。当サイトの各モデルのページでは、店舗が掲載している色別の減額も表示しています。</li>
<li><b>「未開封」の条件を守る</b><br>シュリンク（フィルム）が破れている・開封済みの場合は「開封済未使用品」扱いとなり、買取価格が大きく下がります。</li>
<li><b>店頭か郵送かで選ぶ</b><br>店頭買取は即日現金化できるのが利点です。郵送買取は店舗が近くになくても利用でき、送料無料の店舗もあります。郵送の場合は「到着日の価格」が適用されるなど、価格保証の条件を確認しましょう。</li>
<li><b>予約買取（価格の確保）を活用する</b><br>一部の店舗では、Webで予約するとその時点の価格で一定時間買い取ってもらえます。詳しくは<a href="/guide/yoyaku-kaitori/">予約買取とは？</a>をご覧ください。</li>
</ol>
<h2>必要なもの</h2>
<ul><li>本人確認書類（運転免許証・マイナンバーカード・在留カードなど）</li><li>商品本体（付属品・箱すべて）</li><li>18歳未満は保護者の同意書が必要な店舗が多いです</li></ul>
<p class="cta"><a href="/c/phone/">スマホ・iPhoneの買取価格をすべて見る →</a></p>"""
        write("/guide/iphone-18-kaitori/",
              "iPhone 18 Pro・Pro Max・Duoを一番高く売る方法｜買取価格を大手買取店で比較 - 買取プライス",
              f"iPhone 18 Pro／Pro Max／iPhone Duoの新品・未開封の買取価格を大手買取店{n_shops}社で毎時比較。最高価格の店舗、色による減額、高く売るコツを解説。",
              "iPhone 18シリーズを一番高く売る方法｜買取店比較",
              body,
              [("iPhone 18の買取価格はどこが一番高い？", "モデル・容量・時間帯によって最高値の店舗は変わります。本ページの比較表は大手買取店の公開価格を毎時更新しています。"),
               ("色によって買取価格は変わりますか？", "多くの買取店で色ごとの減額があります。各店舗の掲載情報で確認してください。"),
               ("開封済みのiPhoneも買い取ってもらえますか？", "多くの店舗で「開封済未使用品」として買取していますが、未開封より価格は下がります。")])

    # ---------------------------------------------------------------- 2. ポケカBOX
    if boxes:
        body = f"""
<p>ポケモンカードの未開封BOXは、<b>同じBOXでも買取店によって買取価格が異なります</b>。
下の表は、複数の大手買取店が買取している人気BOXを、毎時自動で比較したものです（3店舗以上で価格がある商品）。</p>
<h2>ポケカ・トレカBOX 買取価格比較表（未開封・シュリンク付き）</h2>
{_table(boxes, shops, e)}
<h2>BOXを高く売るためのポイント</h2>
<ol class="tips">
<li><b>シュリンク付き・未開封が前提</b><br>多くの買取店は「シュリンク付き未開封」を条件にしています。シュリンクなし・破れは大きく減額されるか、買取不可になることがあります。</li>
<li><b>BOXとカートンは別価格</b><br>カートン（BOXが複数入った輸送箱）単位で高く買い取る店舗もあります。複数BOXある場合は、カートン価格も確認しましょう。</li>
<li><b>発売直後と再販時は相場が動きやすい</b><br>新弾の発売直後や再販・再録の発表時は、買取価格が短期間で大きく変わることがあります。売る直前に比較するのが安全です。</li>
<li><b>状態の確認</b><br>箱のへこみ・傷・日焼けで減額される場合があります。保管時は直射日光と湿気を避けましょう。</li>
</ol>
<p class="cta"><a href="/c/card/">トレカ・ポケカBOXの買取価格をすべて見る →</a></p>"""
        write("/guide/pokeca-box-kaitori/",
              "ポケカBOX買取価格比較｜未開封BOXを一番高く売れる店は？ - 買取プライス",
              "ポケモンカードの未開封BOX（シュリンク付き）の買取価格を大手買取店で毎時比較。151・ブラックボルトなど人気BOXの最高買取価格と高く売るコツ。",
              "ポケカBOXの買取価格比較｜一番高く売れる店は？",
              body,
              [("シュリンクなしのBOXも買い取ってもらえますか？", "店舗によっては買取可能ですが、多くの場合シュリンク付きより大きく減額されます。"),
               ("BOXの買取価格はいつ変わりますか？", "在庫状況や相場により毎日変動します。発売直後や再販の発表時は特に動きやすいです。")])

    # ---------------------------------------------------------------- 3. 予約買取
    body = """
<p>買取店の「予約買取」（店舗により「価格予約」「買取予約」などの名称）は、<b>Webや電話で予約した時点の買取価格を、一定時間確保してもらえる仕組み</b>です。
買取価格は1日に何度も変わるため、価格が下がる前に確保したいときに便利です。</p>
<h2>予約買取の一般的な流れ</h2>
<ol class="tips">
<li>買取店のWebサイトで商品・数量を選んで予約する</li>
<li>予約番号や確保された価格を確認する</li>
<li>期限内に店頭へ持ち込む（郵送の場合は期限内に発送・到着）</li>
<li>検品後、確保した価格で買取・支払い</li>
</ol>
<h2>利用前に確認したい注意点</h2>
<ul class="tips">
<li><b>有効期限</b>：当日中、数時間以内など、店舗ごとに異なります。</li>
<li><b>キャンセル・持ち込みなしの扱い</b>：キャンセル料や、今後の予約制限などの規定がある店舗もあります。必ず各店舗の規約を確認してください。</li>
<li><b>検品で条件を満たさない場合</b>：開封・傷・色の違いなどがあると、確保した価格から減額されることがあります。</li>
<li><b>数量制限</b>：1人あたりの上限が設定されていることがあります。</li>
</ul>
<h2>予約前に「どの店が一番高いか」を比べる</h2>
<p>予約買取は「その店の価格を確保する」仕組みなので、<b>予約する前に複数店舗の価格を比べておくこと</b>が大切です。
<a href="/">買取プライス</a>では大手買取店の新品・未開封品の買取価格を毎時比較しています。</p>
<p class="cta"><a href="/guide/iphone-18-kaitori/">iPhone 18シリーズの買取価格比較を見る →</a></p>"""
    write("/guide/yoyaku-kaitori/",
          "予約買取とは？価格を確保する仕組みと注意点（キャンセル・期限） - 買取プライス",
          "買取店の予約買取（価格予約）とは何か、流れ、有効期限・キャンセル規定・検品時の減額など利用前の注意点をわかりやすく解説。",
          "予約買取とは？仕組みと利用前の注意点",
          body,
          [("予約買取をキャンセルするとどうなりますか？", "店舗によって異なります。キャンセル料や今後の予約制限がある場合もあるため、各店舗の規約を確認してください。"),
           ("予約した価格は必ずもらえますか？", "期限内に持ち込み、検品で条件を満たした場合に適用されるのが一般的です。")])

    # ---------------------------------------------------------------- danh sách
    lis = "".join(f'<li><a href="{p}">{e(h)}</a><p>{e(d)}</p></li>' for p, h, d in guides)
    idx_body = (f'<nav class="bc"><a href="/">トップ</a> › 買取ガイド</nav><h1>買取ガイド</h1>'
                f'<p>買取価格の比較データをもとに、高く売るためのポイントをまとめています。</p><ul class="glist">{lis}</ul>')
    out = site / "guide"
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page("買取ガイド｜高く売るためのポイント - 買取プライス",
                                         "iPhone・ポケカBOXなどを高く売るための買取ガイド。大手買取店の価格比較データをもとに解説。",
                                         "/guide/", idx_body, [], updated), encoding="utf-8")
    return [("/guide/", "weekly")] + [(p, "daily") for p, _, _ in guides]
