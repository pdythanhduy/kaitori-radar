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

    # ---------------------------------------------------------------- 4. 株主優待券 (JA + VI)
    src = ('<section><h2>参考 / Nguồn</h2><ul class="small">'
           '<li><a href="https://finance.yahoo.co.jp/quote/3048.T/incentive" rel="nofollow noopener" target="_blank">ビックカメラ 株主優待（Yahoo!ファイナンス）</a></li>'
           '<li><a href="https://finance.yahoo.co.jp/quote/2730.T/incentive" rel="nofollow noopener" target="_blank">エディオン 株主優待（Yahoo!ファイナンス）</a></li>'
           '<li><a href="https://finance.yahoo.co.jp/quote/9831.T/incentive" rel="nofollow noopener" target="_blank">ヤマダHD 株主優待（Yahoo!ファイナンス）</a></li>'
           '<li><a href="https://finance.matsui.co.jp/stock/7936/complimentary/index" rel="nofollow noopener" target="_blank">アシックス 株主優待（松井証券）</a></li>'
           '<li><a href="https://www.nojima.co.jp/ir/stockholder/" rel="nofollow noopener" target="_blank">ノジマ 株主優待（公式）</a></li></ul></section>')
    body = f"""
<p>株主優待券（株主優待割引券・買物券）は、企業が株主に贈る割引券です。使わない株主がヤフオク・メルカリなどで出品することがあり、
<b>家電・ゲーム機・スニーカーなどを割安に購入</b>する方法として注目されています。ここでは仕入れに使われることの多い優待券と、購入前の注意点をまとめます。</p>
<p class="pt-note">※優待の内容・利用条件は毎年変わることがあります。購入・利用前に必ず各社の最新の案内と券面の注意事項をご確認ください。</p>
<h2>よく使われる株主優待券</h2>
<div class="tw"><table class="pt"><thead><tr><th>企業</th><th>内容（目安）</th><th>使える場所</th></tr></thead><tbody>
<tr><td>ビックカメラ</td><td>1,000円の買物優待券</td><td>ビックカメラ・コジマ・ソフマップ（Apple Gift Cardの購入に使う人も）</td></tr>
<tr><td>エディオン</td><td>株主優待ギフトカード（3,000円相当〜）</td><td>エディオン・100満ボルト・エディオンネットショップ（1回10枚まで）</td></tr>
<tr><td>ヤマダHD</td><td>500円の優待券（1,000円ごとに1枚が目安）</td><td>ヤマダデンキ各店（有効期限あり）</td></tr>
<tr><td>アシックス</td><td>20〜40%割引の電子チケット（保有株数・期間による）</td><td>主にアシックス／オニツカタイガーのオンラインストア（登録に株主番号が必要）</td></tr>
</tbody></table></div>
<h2>購入前に必ず確認したい3つのポイント</h2>
<ol class="tips">
<li><b>「株主様ご本人のみ」の券は使えない</b><br>例えばノジマの割引券は株主本人の持参が必要と案内されています。譲渡できない券を買うと無駄になります。</li>
<li><b>有効期限・対象外商品</b><br>券面に有効期限や対象外の商品・支払い方法が書かれています。</li>
<li><b>電子チケットは信頼できる出品者から</b><br>登録に株主番号などが必要なものがあります。評価の多い出品者を選びましょう。</li>
</ol>
<h2>仕入れに使うなら：買取価格も比較</h2>
<p>優待券で安く買った商品を買取店に売る場合は、<b>店によって買取価格が数千円〜数万円違う</b>ことがあります。<a href="/">買取プライス</a>で大手買取店9社の価格を比較してから売りましょう。</p>
<p class="cta"><a href="/?v=deals">お得情報一覧を見る →</a></p>
{src}"""
    write("/guide/kabunushi-yutai/",
          "株主優待券で家電・ゲーム機・スニーカーを安く買う方法と注意点 - 買取プライス",
          "ビックカメラ・エディオン・ヤマダ・アシックス（オニツカタイガー）の株主優待券で安く購入する方法と、譲渡不可の券・有効期限など購入前の注意点を解説。",
          "株主優待券で安く買う方法と注意点（ビックカメラ・エディオン・アシックスほか）",
          body,
          [("株主優待券は誰でも使えますか？", "券によります。譲渡可能な券は誰でも使えますが、「株主様ご本人のみ」と案内されている券は第三者は使えません。"),
           ("オニツカタイガーで株主優待は使えますか？", "アシックスの株主優待はオニツカタイガーでも利用できる案内がありますが、現在は主にオンラインストア向けの電子チケットです。最新の案内をご確認ください。")])

    # bản tiếng Việt (link chia sẻ cho nhóm Facebook)
    body_vi = f"""
<p>Phiếu ưu đãi cổ đông (<b>株主優待券</b>) là phiếu giảm giá mà các công ty tặng cho người nắm cổ phiếu. Nhiều cổ đông không dùng đến nên bán lại trên
ヤフオク / メルカリ với giá rẻ. Người mua lại có thể dùng phiếu để <b>mua đồ điện máy, máy game, giày… rẻ hơn 20–30%</b>.
Đây là lý do gần đây nhiều người khoe mua Onitsuka Tiger "giảm giá", dù hãng gần như không bao giờ sale.</p>
<p class="pt-note">⚠️ Điều kiện của mỗi loại phiếu có thể thay đổi theo năm. Trước khi mua và dùng, luôn đọc kỹ thông báo mới nhất của công ty và phần lưu ý in trên phiếu.</p>
<h2>Các loại phiếu hay dùng</h2>
<div class="tw"><table class="pt"><thead><tr><th>Công ty</th><th>Nội dung</th><th>Dùng ở đâu</th></tr></thead><tbody>
<tr><td>ビックカメラ</td><td>Phiếu 1.000円</td><td>ビックカメラ・コジマ・ソフマップ. Không mua thẳng iPhone được, nhiều người dùng để mua Apple Gift Card</td></tr>
<tr><td>エディオン</td><td>Thẻ quà tặng nạp sẵn tiền (từ 3.000円)</td><td>エディオン・100満ボルト và エディオンネットショップ, tối đa 10 thẻ mỗi lần mua</td></tr>
<tr><td>ヤマダ電機</td><td>Phiếu 500円, thường cứ mua 1.000円 dùng 1 phiếu</td><td>Cửa hàng ヤマダデンキ (có hạn sử dụng)</td></tr>
<tr><td>ASICS / Onitsuka Tiger</td><td>Vé điện tử giảm 20–40% tuỳ số cổ phần</td><td>Hiện chủ yếu dùng ở cửa hàng online ASICS / Onitsuka Tiger, cần mã cổ đông để đăng ký</td></tr>
</tbody></table></div>
<h2>3 điều phải biết trước khi mua phiếu</h2>
<ol class="tips">
<li><b>Có loại CHỈ chính cổ đông dùng được.</b> Ví dụ phiếu ノジマ ghi rõ phải chính cổ đông mang tới cửa hàng (ご本人様のみ), mua lại là mất tiền.</li>
<li><b>Xem hạn sử dụng và hàng bị loại trừ</b> in trên phiếu. Có phiếu không dùng cho thẻ trả trước, sửa chữa…</li>
<li><b>Phiếu điện tử cần mã cổ đông để đăng ký</b>, nên chỉ mua của người bán uy tín, có nhiều đánh giá tốt.</li>
</ol>
<h2>Mua rẻ rồi bán kai: nhớ so giá</h2>
<p>Nếu mua hàng bằng phiếu để bán lại cho tiệm kaitori, các tiệm có thể trả chênh nhau vài nghìn đến vài man yên cho cùng một món.
So giá 9 tiệm lớn, cập nhật mỗi giờ: <a href="/vi/">kaitoriprice.com/vi</a></p>
<p class="cta"><a href="/vi/?v=deals">Xem các ưu đãi khác →</a></p>
<p><a href="https://www.facebook.com/groups/1118827834446963" target="_blank" rel="noopener">👥 Nhóm Facebook "Săn Giá Kaitori Nhật Bản": hỏi đáp, chia sẻ kinh nghiệm →</a></p>
{src}"""
    out = site / "guide" / "phieu-co-dong"
    out.mkdir(parents=True, exist_ok=True)
    pv = page("Mua rẻ 20–30% bằng phiếu cổ đông (株主優待券): Onitsuka Tiger, ビックカメラ, エディオン | Kaitori Price",
              "Cách dùng phiếu ưu đãi cổ đông (株主優待券) mua đồ điện máy, giày Onitsuka Tiger rẻ hơn, và 3 điều phải biết để không mất tiền.",
              "/guide/phieu-co-dong/",
              f'<nav class="bc"><a href="/vi/">Trang chủ</a> › Mẹo mua rẻ</nav><article class="guide" lang="vi"><h1>Mua rẻ 20–30% bằng phiếu cổ đông (株主優待券)</h1>{body_vi}</article>',
              [], updated)
    pv = pv.replace('<html lang="ja">', '<html lang="vi">', 1).replace(
        '<a class="hd-cta" href="/">全商品を比較 →</a>', '<a class="hd-cta" href="/vi/">So giá 9 tiệm →</a>', 1)
    (out / "index.html").write_text(pv, encoding="utf-8")
    extra = [("/guide/phieu-co-dong/", "weekly")]

    # ---------------------------------------------------------------- 5. Mẹo mua hàng giảm giá (VI) — rà soát 01/11/2026
    body_tips = """
<p>Tổng hợp các cách mua hàng rẻ hơn ở Nhật: sale online, điểm thưởng, phiếu cổ đông, trang tích điểm… dùng được khi mua đồ cho mình
hoặc mua hàng để bán lại cho tiệm kaitori. <b>Thông tin rà soát ngày 01/11/2026</b>. Các sự kiện hay đổi điều kiện, nên luôn xem lại trang chính thức trước khi mua.</p>
<nav class="toc"><b>Mục lục</b><ol><li><a href="#rakuten">Rakuten</a></li><li><a href="#yahoo">Yahoo!ショッピング</a></li><li><a href="#amazon">Amazon</a></li>
<li><a href="#denki">Chuỗi điện máy</a></li><li><a href="#yutai">Phiếu cổ đông</a></li><li><a href="#pointsite">Trang tích điểm</a></li><li><a href="#phone">Điện thoại "1 yên"</a></li></ol></nav>

<h2 id="rakuten">1. 🛒 Rakuten (楽天市場)</h2>
<div class="tw"><table class="pt"><thead><tr><th>Sự kiện</th><th>Cách tính</th><th>Lưu ý</th></tr></thead><tbody>
<tr><td>お買い物マラソン / スーパーSALE</td><td>Mua ở càng nhiều shop khác nhau thì điểm thưởng càng cao (tối đa khoảng 10 shop)</td><td>Có giới hạn điểm mỗi đợt (5.000 / 7.000 / 10.000 điểm tuỳ đợt), xem trên trang sự kiện</td></tr>
<tr><td>Ngày 5 và 0 (5, 10, 15, 20, 25, 30)</td><td>Cộng thêm điểm khi trả bằng thẻ 楽天カード</td><td>Giới hạn khoảng 1.000 điểm/tháng</td></tr>
<tr><td>SPU</td><td>Dùng càng nhiều dịch vụ Rakuten thì nhân điểm càng cao</td><td>Trang chính thức ghi tối đa 18,5 lần, giới hạn theo tháng</td></tr>
</tbody></table></div>
<p>💡 <b>Mẹo:</b> gom đồ định mua vào đợt マラソン rơi trúng ngày 5 hoặc 0. ⚠️ Từ 10/2025, ふるさと納税 qua Rakuten không còn được tính điểm マラソン / SPU.</p>

<h2 id="yahoo">2. 🛒 Yahoo!ショッピング (PayPay)</h2>
<ul class="tips">
<li><b>Ngày 5, 15, 25:</b> +4% điểm PayPay (phải bấm đăng ký sự kiện trước). Từ 5/9/2026 giới hạn 2.000 điểm/người.</li>
<li><b>LYPプレミアム</b> (508円/tháng): thêm +2% mỗi ngày.</li>
<li>⚠️ <b>Ngày 25/11/2026 không có sự kiện ngày 5</b> vì trùng Black Friday. Khi có 超PayPay祭 thì các sự kiện thường hay tạm dừng.</li>
</ul>

<h2 id="amazon">3. 🛒 Amazon</h2>
<ul class="tips">
<li><b>Black Friday 2026:</b> chưa có ngày chính thức (các trang dự đoán khoảng 20–23/11 đến cuối tháng 11).</li>
<li>Phải <b>bấm đăng ký nhận điểm</b> thì mới được cộng thêm. Mức cộng thêm giảm dần: năm 2023–24 là +2%, năm 2025 còn +1,5%.</li>
</ul>

<h2 id="denki">4. 🏬 Chuỗi điện máy (ヨドバシ / ビックカメラ)</h2>
<ul class="tips">
<li><b>ヨドバシ:</b> hoàn điểm cơ bản 10%, nhưng <b>hàng Apple (iPhone, iPad, Mac) chỉ 5%</b>. Thẻ ゴールドポイントカード・プラス được thêm điểm.</li>
<li>Trả bằng thẻ tín dụng hãng khác mà không mở app tích điểm thì bị giảm điểm.</li>
<li>Mức hoàn điểm của ビックカメラ hay thay đổi, nên hỏi tại quầy trước khi mua.</li>
</ul>

<h2 id="yutai">5. 🎟 Phiếu cổ đông (株主優待券)</h2>
<p>Phiếu ビックカメラ, エディオン, ヤマダ, ASICS / Onitsuka Tiger mua lại trên ヤフオク / メルカリ để giảm giá.
⚠️ Phiếu ノジマ chỉ chính chủ dùng được; phiếu ABCマート đã bỏ từ năm 2021. 👉 <a href="/guide/phieu-co-dong/">Xem bài chi tiết</a></p>

<h2 id="pointsite">6. 💳 Trang tích điểm (ポイントサイト)</h2>
<ul class="tips">
<li>Vào Rakuten / Yahoo… <b>thông qua trang tích điểm</b> như ハピタス, モッピー thì được hoàn thêm khoảng 1%.</li>
<li>⚠️ Không xoá cookie, không mở shop ở tab khác, không thoát giữa chừng khi đang mua, nếu không sẽ không được cộng điểm.</li>
<li>Mức hoàn thay đổi liên tục, xem trên chính trang tích điểm.</li>
</ul>

<h2 id="phone">7. 📱 Điện thoại "1 yên" (一括1円)</h2>
<ul class="tips">
<li><b>Từ 27/12/2023:</b> giảm giá máy tối đa <b>44.000円</b>, kể cả mua máy không kèm hợp đồng (白ロム). Kiểu "一括1円" gần như không còn, chỉ còn "実質1円" (phải ký hợp đồng và trả lại máy sau một thời gian).</li>
<li>Năm 2026 Bộ Nội vụ (総務省) đang xem xét lại các ưu đãi chuyển mạng, dự kiến có kết luận vào mùa thu 2026, chưa có quy định mới.</li>
</ul>

<h2>📅 Lịch mua gợi ý</h2>
<ul class="tips">
<li><b>Mua online:</b> chờ マラソン trùng ngày 5/0 (Rakuten) hoặc ngày 5 của Yahoo, và luôn vào qua trang tích điểm.</li>
<li><b>Đồ điện máy:</b> dùng phiếu cổ đông ビックカメラ / エディオン, cộng thẻ tích điểm của cửa hàng.</li>
<li><b>Tháng 11:</b> Black Friday (Amazon / Yahoo). Năm nay Yahoo không có ngày 25/11.</li>
<li><b>Mua để bán kai:</b> so giá 9 tiệm trước khi bán 👉 <a href="/vi/">kaitoriprice.com/vi</a></li>
</ul>
<p><a href="https://www.facebook.com/groups/1118827834446963" target="_blank" rel="noopener">👥 Hỏi đáp trong nhóm Facebook "Săn Giá Kaitori Nhật Bản" →</a></p>
<section><h2>Nguồn tham khảo</h2><ul class="small">
<li><a href="https://event.rakuten.co.jp/campaign/point-up/everyday/point/" rel="nofollow noopener" target="_blank">楽天 SPU（公式）</a></li>
<li><a href="https://www.r-zyunin.com/rakuten-tools/maximum-point" rel="nofollow noopener" target="_blank">楽天ポイント上限一覧</a></li>
<li><a href="https://shopping.yahoo.co.jp/promotion/campaign/guide/" rel="nofollow noopener" target="_blank">Yahoo!ショッピング お得ガイド（公式）</a></li>
<li><a href="https://appllio.com/yahoo-shopping-paypay-matsuri-check-list" rel="nofollow noopener" target="_blank">Yahoo!ショッピング 2026年10・11月キャンペーン</a></li>
<li><a href="https://gori.me/amazon/amazon-sale/156809" rel="nofollow noopener" target="_blank">Amazonブラックフライデー2026 予想</a></li>
<li><a href="https://pricey.jp/web/articles/4181" rel="nofollow noopener" target="_blank">ヨドバシ ポイント還元</a></li>
<li><a href="https://pay-route.co.jp/article/?p=4884" rel="nofollow noopener" target="_blank">ポイントサイト経由の注意点</a></li>
<li><a href="https://k-tai.watch.impress.co.jp/docs/news/1544945.html" rel="nofollow noopener" target="_blank">スマホ割引 原則4万円上限・白ロム割規制（ケータイWatch）</a></li>
<li><a href="https://selectra.jp/telecom/news/mnp-restrictions" rel="nofollow noopener" target="_blank">MNP特典規制の見直し 2026</a></li>
</ul></section>"""
    out = site / "guide" / "meo-mua-re"
    out.mkdir(parents=True, exist_ok=True)
    pv = page("7 cách mua hàng giảm giá ở Nhật: Rakuten, Yahoo, Amazon, điện máy, phiếu cổ đông | Kaitori Price",
              "Rà soát 01/11/2026: lịch sale Rakuten, ngày 5 Yahoo, Black Friday Amazon, điểm ヨドバシ, phiếu cổ đông, trang tích điểm, quy định điện thoại 1 yên.",
              "/guide/meo-mua-re/",
              f'<nav class="bc"><a href="/vi/">Trang chủ</a> › <a href="/guide/vi/">Mẹo & Hướng dẫn</a> › Mua hàng giảm giá</nav><article class="guide" lang="vi"><h1>🛒 7 cách mua hàng giảm giá ở Nhật</h1>{body_tips}</article>',
              [], updated)
    pv = pv.replace('<html lang="ja">', '<html lang="vi">', 1).replace(
        '<a class="hd-cta" href="/">全商品を比較 →</a>', '<a class="hd-cta" href="/vi/">So giá 9 tiệm →</a>', 1)
    (out / "index.html").write_text(pv, encoding="utf-8")
    extra.append(("/guide/meo-mua-re/", "weekly"))

    # ---------------------------------------------------------------- 6. Danh sách tiệm (VI) — lấy từ web chính thức 01/11/2026
    from urllib.parse import quote as _qq
    STORES = [  # (khu vực, tiệm, chi nhánh, địa chỉ hoặc "", giờ / ghi chú, trang chính thức)
        ("Tokyo", "森森買取", "秋葉原駅前店", "東京都千代田区神田佐久間町1丁目13 チョムチョム秋葉原 1F", "JR秋葉原駅 中央改札 徒歩1分", "https://www.morimori-kaitori.jp/inviting"),
        ("Tokyo", "森森買取", "新宿店", "東京都新宿区新宿2-7-4 アリサビル1F", "新宿三丁目駅 C5出口 徒歩3分", "https://www.morimori-kaitori.jp/inviting"),
        ("Tokyo", "森森買取", "高田馬場店", "東京都新宿区高田馬場2-14-6 アライビル1階", "高田馬場駅 徒歩2〜3分・不定休", "https://www.morimori-kaitori.jp/inviting"),
        ("Tokyo", "買取ルデヤ", "池袋・秋葉原・新宿・赤羽店", "", "10:00〜19:00（月〜土・祝）・日曜休み", "https://kaitori-rudeya.com/accessmap"),
        ("Tokyo", "ケータイゴッド", "新宿店", "東京都新宿区西新宿1-18-17 ラウンドクロス西新宿7階", "11:00〜20:00・不定休", "https://keitai-god.com/shop.php"),
        ("Tokyo", "ケータイゴッド", "池袋PARCO店", "東京都豊島区南池袋1-28-2 池袋PARCO 本館7F", "11:00〜21:00（買取受付20:00まで）・不定休", "https://keitai-god.com/shop.php"),
        ("Tokyo", "モバイル一番", "池袋駅前店", "東京都豊島区西池袋1-29-5 山の手ビル1F", "TEL 03-6912-6085", "https://www.mobile-ichiban.com/"),
        ("Tokyo", "モバイル一番", "赤羽店", "東京都北区赤羽南1-21-9", "TEL 03-5939-6588", "https://www.mobile-ichiban.com/"),
        ("Tokyo", "モバイル一番", "浮間舟渡店", "東京都北区浮間2-13-10", "TEL 03-6454-5032", "https://www.mobile-ichiban.com/"),
        ("Tokyo", "買取当番", "秋葉原支店", "東京都千代田区外神田1-2-9 ラオックス秋葉原本店 5階", "11:00〜19:00（最終受付18:45）・年中無休", "https://tobansyoji.co.jp/company/"),
        ("Tokyo", "PANDA買取", "日暮里", "東京都荒川区東日暮里1-17-11", "Giờ mở cửa: xem trang tiệm", "http://panda-kaitori.co.jp/shop.html"),
        ("Kanagawa / Saitama", "買取ルデヤ", "川崎店・大宮店", "", "10:00〜19:00（月〜土・祝）・日曜休み", "https://kaitori-rudeya.com/accessmap"),
        ("Kanagawa / Saitama", "買取当番", "川崎支店", "神奈川県川崎市川崎区砂子2-7-5 サン・ラビル1階", "11:00〜19:00（最終受付18:45）・年中無休", "https://tobansyoji.co.jp/company/"),
        ("Kanagawa / Saitama", "ゲストモバイル", "橋本・町田・八王子・相模原", "", "11:30〜19:00", "https://www.guestmobile.jp/%e5%ba%97%e9%a0%ad%e8%b2%b7%e5%8f%96/"),
        ("Osaka", "森森買取", "大阪なんば店", "大阪府大阪市浪速区難波中1-3-15 シャトー中山 1F", "11:00〜20:00・TEL 06-6964-8839", "https://www.morimori-kaitori.jp/inviting"),
        ("Osaka", "モバイル一番", "大阪日本橋店", "大阪府大阪市浪速区日本橋4-10-6", "TEL 06-7507-2600", "https://www.mobile-ichiban.com/"),
        ("Nagoya", "買取1丁目", "名古屋店（2026/10/19 OPEN）", "愛知県名古屋市中区栄2-15-12 大橋ビル1F", "10:00〜19:00", "https://www.1-chome.com/"),
        ("Nagoya", "モバイル一番", "名古屋大須店", "愛知県名古屋市中区大須4丁目1-9 菱水ビル1F", "TEL 052-212-7981", "https://www.mobile-ichiban.com/"),
        ("Fukuoka", "森森買取", "福岡店", "", "天神駅 徒歩6分", "https://www.morimori-kaitori.jp/inviting"),
    ]
    regions = list(dict.fromkeys(r[0] for r in STORES))
    rows_html = []
    for reg in regions:
        cards_ = []
        for _, shop, br, addr, info, url in [r for r in STORES if r[0] == reg]:
            mp = f'<a href="https://www.google.com/maps/search/?api=1&query={_qq(shop + " " + (addr or br))}" target="_blank" rel="noopener nofollow">📍 Bản đồ</a>'
            cards_.append(f'<div class="store"><b>{e(shop)}</b> <span class="br">{e(br)}</span>'
                          f'{f"<p>{e(addr)}</p>" if addr else ""}<p class="small">🕘 {e(info)}</p>'
                          f'<p class="small">{mp} · <a href="{e(url)}" target="_blank" rel="noopener nofollow">Trang tiệm ↗</a></p></div>')
        rows_html.append(f'<h2 id="{e(reg.split()[0].lower())}">{e(reg)}</h2><div class="stores">{"".join(cards_)}</div>')
        if reg == "Osaka":  # tiệm khác ở Osaka (chưa so giá) — theo trang tổng hợp, cần kiểm tra trước khi đi
            OSAKA_MORE = [
                ("イオシス", "大阪買取センター", "大阪府大阪市浪速区難波中2-5-14", "なんば・恵美須町 徒歩6分・11:00〜19:30"),
                ("じゃんぱら", "大阪本店", "大阪府大阪市浪速区難波中2-1-21 じゃんぱら難波ビル1F", "南海なんば 徒歩3分・11:30〜20:00"),
                ("モバックス", "日本橋4丁目本店", "大阪府大阪市浪速区日本橋4-11-10 大南ビル1F", "恵美須町 徒歩約4分・10:30〜20:00"),
                ("モバステ", "大阪店", "大阪府大阪市浪速区日本橋4-11-6", "南海なんば 徒歩6分・11:30〜20:00"),
                ("JCKA", "大阪日本橋店", "大阪府大阪市浪速区日本橋5-13-7 上田ビル", "11:00〜19:00"),
                ("フォンサルドットコム", "大阪なんば日本橋店", "大阪府大阪市浪速区日本橋5-9-12 日本橋総合案内所内", "恵美須町 徒歩3分・11:00〜19:30"),
                ("ODAモバイル", "日本橋三丁目店", "大阪府大阪市浪速区日本橋3-6-1 本田ビル2F", "10:30〜20:00"),
                ("ゲオモバイル", "大阪なんば店", "大阪府大阪市中央区難波千日前7-8", "11:00〜20:00"),
                ("スマートバイヤー", "梅田店", "大阪府大阪市北区梅田1-3-1 大阪駅前第1ビル1F", "梅田 徒歩約5分・12:00〜20:00"),
                ("アメモバ", "大阪・梅田店", "大阪府大阪市北区梅田1-1-3 大阪駅前第3ビル地下2F", "大阪駅 徒歩約3分・11:00〜19:30"),
                ("カウモバイル", "大阪梅田本店", "大阪府大阪市北区角田町1-10 黒船ビル2F", "阪急梅田 徒歩2分・11:30〜14:00 / 15:00〜19:00"),
                ("ゲオモバイル", "大阪駅前第3ビル店", "大阪府大阪市北区梅田1-1-3 B2F", "11:00〜20:00"),
            ]
            more = "".join(
                f'<div class="store"><b>{e(sh)}</b> <span class="br">{e(br)}</span><p>{e(ad)}</p><p class="small">🕘 {e(info)}</p>'
                f'<p class="small"><a href="https://www.google.com/maps/search/?api=1&query={_qq(sh + " " + ad)}" target="_blank" rel="noopener nofollow">📍 Bản đồ</a></p></div>'
                for sh, br, ad, info in OSAKA_MORE)
            rows_html.append('<h3>Osaka: các tiệm khác (web chưa so giá)</h3>'
                             '<p class="small">Khu 日本橋・なんば và 梅田 có rất nhiều tiệm thu mua iPhone, máy game. Thông tin lấy từ '
                             '<a href="https://linx-as.co.jp/buyshops/osaka-city/" target="_blank" rel="noopener nofollow">trang tổng hợp</a> (01/11/2026), '
                             'chưa đối chiếu với web từng tiệm, nên kiểm tra giờ mở cửa và việc tiệm có nhận hàng mới hay không trước khi đi.</p>'
                             f'<div class="stores">{more}</div>')
    toc = " · ".join(f'<a href="#{e(r.split()[0].lower())}">{e(r)}</a>' for r in regions)
    body_st = f"""
<p>Địa chỉ, giờ mở cửa và ga gần nhất của các tiệm kaitori mà web đang so giá. <b>Lấy từ trang chính thức của từng tiệm ngày 01/11/2026.</b>
Giờ mở cửa và ngày nghỉ có thể thay đổi, nên kiểm tra trang tiệm hoặc gọi trước khi đi.</p>
<p class="pt-note">💡 Ở xa tiệm? Hầu hết các tiệm có <b>gửi bưu điện (郵送買取)</b>: gửi hàng đi, tiệm chuyển khoản. Trước khi đi hoặc gửi, so giá 9 tiệm ở <a href="/vi/">kaitoriprice.com/vi</a>.</p>
<nav class="toc"><b>Khu vực:</b> {toc}</nav>
{"".join(rows_html)}
<h2>Mang gì khi đi bán?</h2>
<ul class="tips"><li>Thẻ cư trú (在留カード) hoặc bằng lái xe: bắt buộc</li><li>Máy còn nguyên seal, đủ hộp và phụ kiện</li><li>Nhiều tiệm cần đăng ký thành viên online trước (ví dụ 森森買取)</li></ul>
<p><a href="https://www.facebook.com/groups/1118827834446963" target="_blank" rel="noopener">👥 Hỏi kinh nghiệm bán ở từng tiệm trong nhóm Facebook →</a></p>"""
    out = site / "guide" / "tiem-kaitori"
    out.mkdir(parents=True, exist_ok=True)
    pv = page("Danh sách tiệm kaitori ở Tokyo, Osaka, Nagoya: địa chỉ, giờ mở cửa | Kaitori Price",
              "Địa chỉ, giờ mở cửa, ga gần nhất của 森森買取, 買取ルデヤ, モバイル一番, ケータイゴッド, 買取当番, 買取1丁目… ở Tokyo, Osaka, Nagoya.",
              "/guide/tiem-kaitori/",
              f'<nav class="bc"><a href="/vi/">Trang chủ</a> › <a href="/guide/vi/">Mẹo & Hướng dẫn</a> › Danh sách tiệm</nav><article class="guide" lang="vi"><h1>📍 Danh sách tiệm kaitori (Tokyo, Osaka, Nagoya)</h1>{body_st}</article>',
              [], updated)
    pv = pv.replace('<html lang="ja">', '<html lang="vi">', 1).replace(
        '<a class="hd-cta" href="/">全商品を比較 →</a>', '<a class="hd-cta" href="/vi/">So giá 9 tiệm →</a>', 1)
    (out / "index.html").write_text(pv, encoding="utf-8")
    extra.append(("/guide/tiem-kaitori/", "weekly"))

    # ---------------------------------------------------------------- 7. Huỷ / trả iPhone (VI) — rà soát 02/11/2026
    def vi_page(path, title, desc, crumb, h1, body):
        out = site / path.strip("/")
        out.mkdir(parents=True, exist_ok=True)
        pv = page(title, desc, path,
                  f'<nav class="bc"><a href="/vi/">Trang chủ</a> › <a href="/guide/vi/">Mẹo & Hướng dẫn</a> › {e(crumb)}</nav>'
                  f'<article class="guide" lang="vi"><h1>{e(h1)}</h1>{body}</article>', [], updated)
        pv = pv.replace('<html lang="ja">', '<html lang="vi">', 1).replace(
            '<a class="hd-cta" href="/">全商品を比較 →</a>', '<a class="hd-cta" href="/vi/">So giá 9 tiệm →</a>', 1)
        (out / "index.html").write_text(pv, encoding="utf-8")
        extra.append((path, "daily"))

    SRC = ('<p class="small">Nguồn: <a href="https://www.apple.com/jp/shop/help/returns_refund" target="_blank" rel="noopener nofollow">Apple 返品・返金</a> · '
           '<a href="https://www.softbank.jp/support/faq/view/12278" target="_blank" rel="noopener nofollow">SoftBank FAQ</a> · '
           '<a href="https://www.showcase-tv.com/mobile/iphone-duo-cancel/" target="_blank" rel="noopener nofollow">bài tổng hợp cách huỷ đặt trước (16/10/2026)</a> · '
           '<a href="https://www.soumu.go.jp/main_content/000877865.pdf" target="_blank" rel="noopener nofollow">tài liệu 総務省</a>. '
           'Rà soát ngày 02/11/2026. Quy định có thể thay đổi, nên xem lại trang chính thức trước khi làm.</p>')
    CTA = '<p class="cta"><a href="/vi/?q=iPhone">Xem giá kai iPhone ở 9 tiệm (cập nhật mỗi giờ) →</a></p>'

    body_huy = f"""
<p>Giá kai iPhone giảm, nhiều người muốn <b>huỷ đơn đã đặt</b> để khỏi bán lỗ. Bài này tóm tắt cách huỷ ở Apple Store và các nhà mạng
sao cho <b>không mất phí</b>. Nguyên tắc quan trọng nhất: <b>huỷ trước khi hàng được gửi đi</b>. Sau khi đã giao hàng, việc huỷ sẽ thành
<b>trả hàng</b>, khó hơn nhiều, và ở một số nơi iPhone không được trả.</p>
<nav class="toc"><b>Mục lục</b><ol><li><a href="#apple">Apple Store</a></li><li><a href="#docomo">docomo</a></li><li><a href="#au">au</a></li>
<li><a href="#sb">SoftBank</a></li><li><a href="#rakuten">Rakuten Mobile</a></li><li><a href="#hopdong">Hợp đồng sim đi kèm</a></li><li><a href="#ruiro">Rủi ro huỷ nhiều lần</a></li></ol></nav>

<h2 id="apple">🍎 Apple Store (online)</h2>
<ul class="tips">
<li><b>Chưa gửi hàng:</b> đăng nhập Apple Account → trang <b>ご注文状況</b> → chọn đơn → <b>商品のキャンセル</b>. Đã trả tiền thì Apple hoàn lại số tiền đã thanh toán.</li>
<li>Khi đơn đã chuyển sang <b>出荷準備中</b> hoặc <b>出荷完了</b> thì không tự huỷ được nữa. Lúc đó dùng cách <a href="/guide/tra-iphone-apple/">trả máy trong 14 ngày</a>.</li>
<li>Thanh toán ở konbini hoặc chuyển khoản mà <b>không trả tiền trong 2 tuần</b> thì đơn tự huỷ (theo bài tổng hợp, trang trợ giúp của Apple không ghi rõ).</li>
<li>Apple không công bố hạn chót cụ thể. Muốn huỷ thì <b>huỷ càng sớm càng tốt</b>, đừng đợi tới ngày giao.</li>
</ul>

<h2 id="docomo">📶 docomo</h2>
<ul class="tips">
<li>Huỷ đặt trước: đăng nhập <b>dアカウント</b> → trang <b>予約状況の確認</b> → huỷ.</li>
<li>⚠️ Theo bài tổng hợp, chế độ trả hàng (返品保証) của docomo Online Shop <b>chỉ áp dụng cho Android, iPhone không được trả</b>. Vì vậy iPhone đặt ở docomo phải huỷ trước khi gửi hàng.</li>
</ul>

<h2 id="au">📶 au</h2>
<ul class="tips">
<li>Tự huỷ được <b>tới trước khi bắt đầu chuẩn bị gửi hàng</b>.</li>
<li>Đổi máy (機種変更): đăng nhập bằng <b>au ID</b>. Mở số mới hoặc chuyển mạng (新規・のりかえ): cần <b>số đặt trước (予約番号) và mật khẩu</b> trong email xác nhận. Giữ lại email này tới khi xong việc.</li>
</ul>

<h2 id="sb">📶 SoftBank</h2>
<ul class="tips">
<li>Sau khi đặt, <b>gần như không đổi được</b> màu, dung lượng, số lần trả góp. Muốn đổi thì phải <b>huỷ rồi đặt lại</b>.</li>
<li>Cách huỷ khác nhau tuỳ tình trạng đơn, xem ở trang FAQ của SoftBank Online Shop (cần <b>số tiếp nhận 受付番号</b>). Đặt ở cửa hàng thì liên hệ chính cửa hàng đó.</li>
<li>SoftBank không ghi hạn chót huỷ, nên làm sớm.</li>
</ul>

<h2 id="rakuten">📶 Rakuten Mobile</h2>
<ul class="tips"><li>Chỉ huỷ được <b>trước khi đơn đăng ký được tiếp nhận xong</b>.</li></ul>

<h2 id="hopdong">📄 Hợp đồng sim đi kèm</h2>
<ul class="tips">
<li><b>Trả máy cho Apple không tự huỷ hợp đồng nhà mạng.</b> Hợp đồng sim phải tự huỷ với nhà mạng.</li>
<li><b>初期契約解除 (huỷ trong 8 ngày):</b> là chế độ huỷ <b>hợp đồng sim</b> (ví dụ sóng yếu, giải thích không đủ). Phí tháng tính theo ngày, phí gọi và dữ liệu đã dùng vẫn phải trả. Chế độ này <b>không phải</b> là trả máy.</li>
</ul>

<h2 id="ruiro">⚠️ Rủi ro khi mở rồi huỷ hợp đồng nhiều lần</h2>
<ul class="tips">
<li>Tài liệu của 総務省 (2023) ghi nhận có đại lý nói rằng huỷ sớm (ví dụ trong 3 hoặc 6 tháng) sẽ bị đưa vào <b>danh sách đen</b>. Mở rồi huỷ liên tục có rủi ro bị từ chối hợp đồng sau này.</li>
<li>Theo tin tổng hợp, Y!mobile thu <b>phí huỷ hợp đồng tối đa 1.100円</b> với hợp đồng đăng ký từ 01/07/2026. Xu hướng là các nhà mạng siết chuyện mở rồi huỷ nhanh.</li>
<li>Huỷ <b>đơn đặt trước khi chưa giao</b> đơn giản hơn nhiều so với huỷ hợp đồng sau khi đã nhận máy.</li>
</ul>

<p class="pt-note">💡 Chưa chắc nên huỷ? Đọc <a href="/guide/gia-iphone-giam/">Giá kai iPhone giảm: huỷ, bán ngay hay giữ?</a> và so giá 9 tiệm trước khi quyết định.</p>
{CTA}{SRC}"""
    vi_page("/guide/huy-iphone/", "Cách huỷ đơn iPhone không mất phí: Apple Store, docomo, au, SoftBank | Kaitori Price",
            "Huỷ đơn đặt iPhone trước khi gửi hàng ở Apple Store, docomo, au, SoftBank, Rakuten Mobile. Điều cần biết về hợp đồng sim và rủi ro danh sách đen.",
            "Huỷ đơn iPhone", "❌ Cách huỷ đơn iPhone không mất phí", body_huy)

    body_tra = f"""
<p>Nếu đơn Apple Store đã gửi đi, không huỷ được nữa, vẫn có thể <b>trả máy trong 14 ngày</b>. Đây là điều kiện ghi trên trang chính thức của Apple Nhật.</p>
<h2>Điều kiện trả máy</h2>
<ul class="tips">
<li><b>Trong 14 ngày</b> kể từ khi nhận hàng, iPhone <b>không hư hại</b>, kèm phụ kiện đi kèm.</li>
<li>Phải ở <b>tình trạng ban đầu, đủ linh kiện, phụ kiện và hộp</b>. Giữ lại hộp, giấy, cáp, đừng vứt đi.</li>
<li>Chỉ trả <b>tại Nhật</b> (nước đã mua).</li>
<li>Hoàn tiền qua ngân hàng thì <b>chỉ vào tài khoản đứng tên người mua</b>. Apple có thể kiểm tra máy trước khi hoàn tiền.</li>
</ul>
<h2>Các bước trước khi gửi trả</h2>
<ul class="tips">
<li><b>Tắt "Tìm iPhone" (アクティベーションロック)</b> nếu đã bật. Apple có thể từ chối nhận máy còn khoá.</li>
<li>Nếu có hợp đồng sim đi kèm: <b>tự huỷ hợp đồng với nhà mạng</b>. Trả máy không tự huỷ hợp đồng.</li>
<li>Bắt đầu trả hàng từ trang <b>ご注文状況</b> trên Apple Store online.</li>
</ul>
<h2>⚠️ Khi nào bị trừ phí 15%</h2>
<p>Bình thường trả máy trong 14 ngày không có phí. Nhưng Apple ghi rõ sẽ thu <b>phí trả hàng 15% mỗi sản phẩm</b> với
<b>đơn mua số lượng lớn</b> hoặc khi nghi ngờ trả hàng, huỷ đơn bất thường. Mua nhiều máy để bán lại rồi trả hàng loạt dễ bị phí này.</p>
<h2>Ở nhà mạng thì sao?</h2>
<p>Quy định trả máy của nhà mạng khác Apple. Ví dụ docomo Online Shop không nhận trả iPhone (xem <a href="/guide/huy-iphone/#docomo">bài huỷ đơn</a>).
Với máy mua ở nhà mạng, hãy huỷ trước khi gửi hàng.</p>
{CTA}{SRC}"""
    vi_page("/guide/tra-iphone-apple/", "Trả iPhone cho Apple trong 14 ngày: điều kiện, phí 15% | Kaitori Price",
            "Điều kiện trả iPhone mua ở Apple Store Nhật trong 14 ngày, cần tắt Tìm iPhone, huỷ hợp đồng sim, khi nào bị phí 15%.",
            "Trả iPhone cho Apple", "↩️ Trả iPhone cho Apple trong 14 ngày", body_tra)

    trs = []
    for it in ip18:
        ps = sorted(it["prices"].items(), key=lambda kv: -kv[1]["price"])
        (s1, p1), low = ps[0], ps[-1]
        link = f'<a href="/p/{it["_slug"]}/">{e(it["name"])}</a>' if it.get("_slug") else e(it["name"])
        trs.append(f"<tr><td>{link}</td><td><b>{_yen(p1['price'])}</b><br><small>{e(shops.get(s1, {}).get('name', s1))}</small></td>"
                   f"<td>{_yen(p1['price'] - low[1]['price']) if len(ps) > 1 else '—'}</td><td>{it['n_shops']}</td></tr>")
    tbl = ('<div class="tw"><table class="pt"><thead><tr><th>Mẫu</th><th>Giá kai cao nhất</th><th>Chênh cao–thấp</th><th>Số tiệm</th></tr></thead>'
           f"<tbody>{''.join(trs)}</tbody></table></div>") if trs else ""
    body_gia = f"""
<p class="upd">Giá cập nhật: {upd} JST (tự động mỗi giờ)</p>
<p>Giá kai iPhone giảm thì có 3 lựa chọn: <b>huỷ đơn</b>, <b>bán ngay</b> hoặc <b>giữ chờ giá</b>. Không có cách nào chắc chắn đúng,
nhưng tính đúng con số thì quyết định dễ hơn.</p>
<h2>Giá kai iPhone 18 / Duo mới nhất (máy mới, chưa mở)</h2>
{tbl}
<p class="small">Bấm tên mẫu để xem giá từng tiệm và biểu đồ giá.</p>
<h2>Cách tính nhanh</h2>
<ul class="tips">
<li><b>Lời / lỗ = giá kai cao nhất − (giá mua − điểm thưởng nhận được)</b>. Nhớ trừ cả phí đi lại hoặc phí gửi bưu điện.</li>
<li>Các tiệm lệch nhau có khi vài nghìn tới vài chục nghìn yên, đừng chỉ hỏi 1 tiệm.</li>
<li>Màu, dung lượng có thể bị trừ tiền khác nhau giữa các tiệm, xem ghi chú trên trang giá.</li>
</ul>
<h2>Khi nào nên làm gì?</h2>
<ul class="tips">
<li><b>Huỷ:</b> khi tính ra lỗ và đơn <b>chưa gửi hàng</b>, huỷ được miễn phí. Xem <a href="/guide/huy-iphone/">cách huỷ từng nơi</a>.</li>
<li><b>Trả máy:</b> đã nhận máy ở Apple Store, còn trong 14 ngày, chưa hư hại. Xem <a href="/guide/tra-iphone-apple/">điều kiện trả</a>. Mua số lượng lớn có thể bị phí 15%.</li>
<li><b>Bán ngay:</b> khi vẫn còn lời, hoặc lỗ ít hơn chi phí huỷ. Chọn tiệm giá cao nhất, có thể <a href="/guide/yoyaku-kaitori/">đặt giữ giá (予約買取)</a> trước khi máy về.</li>
<li><b>Giữ chờ giá:</b> là đánh cược. Máy mới thường mất giá theo thời gian, và khi đã mở hộp hoặc kích hoạt thì không còn bán được giá "mới chưa mở".</li>
</ul>
<p class="pt-note">📈 Giá 9 tiệm cập nhật mỗi giờ, theo dõi trước khi quyết định: <a href="/vi/?q=iPhone">kaitoriprice.com/vi</a></p>
<p class="small">Bài chỉ để tham khảo, không phải lời khuyên đầu tư. Giá trong bảng là giá công khai trên web các tiệm, giá thực tế khi bán có thể khác.</p>"""
    vi_page("/guide/gia-iphone-giam/", "Giá kai iPhone giảm: nên huỷ, bán ngay hay giữ? | Kaitori Price",
            "Bảng giá kai iPhone 18 / Duo mới nhất ở 9 tiệm, cách tính lời lỗ và khi nào nên huỷ đơn, trả máy, bán ngay.",
            "Giá iPhone giảm", "📉 Giá kai iPhone giảm: huỷ, bán ngay hay giữ?", body_gia)

    # ---------------------------------------------------------------- 8. Lừa đảo khi giao dịch trực tiếp (VI) — 03/11/2026
    body_lua = f"""
<p>Các nhóm mua bán iPhone giữa người Việt ở Nhật rất tiện, nhưng cũng là chỗ kẻ gian nhắm tới. Dưới đây là những kiểu lừa hay gặp
và cách tự bảo vệ, cho cả <b>người mua</b> lẫn <b>người bán</b>.</p>

<h2 id="vat-la">📦 Hộp còn seal nhưng bên trong là vật lạ, không phải iPhone</h2>
<p>Kiểu lừa nguy hiểm nhất với hàng "nguyên seal": hộp thật, màng co trông như mới, nhưng bên trong là cục đá, xà phòng, hộp giấy
hoặc máy rẻ tiền. Người mua không dám bóc vì sợ mất giá "chưa mở", về nhà mới phát hiện.</p>
<ul class="tips">
<li><b>Hẹn giao dịch ngay tại quầy tiệm kaitori</b> (hoặc gần đó): nhờ tiệm kiểm tra / định giá, hoặc bán thẳng cho tiệm. Kẻ gian thường từ chối đi tiệm.</li>
<li><b>Xem kỹ màng co (シュリンク):</b> màng bị nhăn, có vết keo, mép dán lại bằng nhiệt không đều, dải xé bị lệch là dấu hiệu đã bóc ra dán lại.</li>
<li><b>Đối chiếu số trên nhãn hộp:</b> chụp lại số serial / IMEI in trên nhãn, kiểm tra trên trang của Apple (checkcoverage.apple.com) xem số có thật và đúng mẫu không. Số không tồn tại hoặc sai mẫu → không mua.</li>
<li><b>So cảm giác cầm:</b> hộp quá nhẹ, quá nặng, hoặc lắc nghe tiếng lạ thì dừng lại.</li>
<li><b>Mua nhiều máy:</b> đừng để người bán "cho xem 1 hộp, giao hộp khác". Kiểm tra từng hộp và cầm luôn hộp đã kiểm.</li>
<li><b>Giá rẻ bất thường</b> (thấp hơn giá kai cao nhất nhiều) là dấu hiệu nguy hiểm. Xem giá kai thật trước: <a href="/vi/?q=iPhone">bảng giá 9 tiệm</a>.</li>
</ul>

<h2>💸 Chuyển khoản / PayPay giả</h2>
<ul class="tips">
<li>Ảnh chụp màn hình "đã chuyển khoản" rất dễ làm giả. <b>Chỉ giao máy khi tiền đã vào tài khoản của bạn</b> (mở app ngân hàng của chính bạn để xem).</li>
<li>Người mua hối thúc "chuyển rồi, ngân hàng chậm" → không giao, chờ tiền vào.</li>
<li>Giá trị lớn thì ưu tiên tiền mặt, đếm tại chỗ ở nơi đông người.</li>
</ul>

<h2>🔒 Máy bị khoá hoặc bị chặn mạng</h2>
<ul class="tips">
<li><b>Khoá kích hoạt (Tìm iPhone / iCloud):</b> máy đã kích hoạt mà người bán không đăng xuất được iCloud thì máy gần như vô dụng.</li>
<li><b>利用制限 (hạn chế sử dụng):</b> máy mua trả góp ở nhà mạng chưa trả hết có thể bị đánh dấu △, nếu không trả tiếp sẽ thành × và bị chặn sóng.
Nhiều tiệm kai <b>không mua máy △</b>. Kiểm tra IMEI trên trang 利用制限確認 của docomo / au / SoftBank trước khi mua máy mạng.</li>
</ul>

<h2>🧾 Với người bán</h2>
<ul class="tips">
<li>Người mua "kiểm tra máy" rồi tráo máy khác trả lại: không rời mắt khỏi máy, giao máy cuối cùng sau khi đã nhận đủ tiền.</li>
<li>Không nhận bán hộ máy của người lạ: máy có thể là đồ trộm cắp hoặc mua bằng thẻ gian lận, người bán có thể bị liên luỵ.</li>
<li>Tiệm kaitori luôn yêu cầu giấy tờ (thẻ cư trú…) và ghi lại thông tin người bán. Bán cho tiệm thường an toàn hơn bán cho người lạ.</li>
</ul>

<h2>Bị lừa rồi thì làm gì?</h2>
<ul class="tips">
<li>Giữ lại toàn bộ tin nhắn, ảnh, số tài khoản, ảnh hộp và nhãn hộp.</li>
<li>Báo cảnh sát: gọi <b>110</b> nếu khẩn cấp, hoặc <b>#9110</b> (đường dây tư vấn của cảnh sát) để hỏi cách trình báo.</li>
<li>Báo admin nhóm Facebook để cảnh báo người khác.</li>
</ul>
<p class="pt-note">💡 Cách an toàn nhất để biết giá đúng và tránh bị ép giá: <a href="/vi/">so giá 9 tiệm cập nhật mỗi giờ</a>, rồi bán thẳng cho tiệm trả cao nhất.</p>
<p class="small">Bài tổng hợp kinh nghiệm chung để tham khảo, không phải tư vấn pháp lý. Gặp tình huống cụ thể hãy hỏi cảnh sát (#9110).</p>"""
    vi_page("/guide/lua-dao-iphone/", "Cảnh giác lừa đảo khi mua bán iPhone trực tiếp ở Nhật: hộp seal có vật lạ, chuyển khoản giả | Kaitori Price",
            "Các kiểu lừa khi gặp trực tiếp mua bán iPhone giữa người Việt ở Nhật: hộp nguyên seal bên trong là vật lạ, ảnh chuyển khoản giả, máy bị khoá iCloud hoặc 利用制限. Cách kiểm tra và xử lý.",
            "Cảnh giác lừa đảo", "⚠️ Cảnh giác lừa đảo khi mua bán iPhone trực tiếp", body_lua)

    # ---------------------------------------------------------------- 9. Bán cho người dùng hay bán kai (VI, số liệu thật)
    rows_u = []
    for it in ip18:
        msrp = it.get("msrp")
        if not msrp:
            continue
        ps = sorted(it["prices"].items(), key=lambda kv: -kv[1]["price"])
        s1, p1 = ps[0]
        user = msrp - 5000
        d = p1["price"] - user
        link = f'<a href="/p/{it["_slug"]}/">{e(it["name"])}</a>' if it.get("_slug") else e(it["name"])
        verdict = "Kai cao hơn" if d > 0 else ("Ngang nhau" if d == 0 else "Bán người dùng cao hơn")
        rows_u.append(f"<tr><td>{link}</td><td>{_yen(msrp)}</td><td>{_yen(user)}</td><td><b>{_yen(p1['price'])}</b><br><small>{e(shops.get(s1, {}).get('name', s1))}</small></td>"
                      f"<td>{'+' if d > 0 else ''}{d:,}円<br><small>{verdict}</small></td></tr>")
    tbl_u = ('<div class="tw"><table class="pt"><thead><tr><th>Mẫu</th><th>Giá Apple</th><th>Apple −5.000</th><th>Kai cao nhất</th><th>Kai − (Apple−5.000)</th></tr></thead>'
             f"<tbody>{''.join(rows_u)}</tbody></table></div>") if rows_u else "<p>Chưa có số liệu.</p>"
    body_u = f"""
<p class="upd">Giá cập nhật: {upd} JST (tự động mỗi giờ)</p>
<p>Trong các nhóm hay thấy giá <b>"app −5s"</b> (giá Apple trừ 5.000円) khi bán cho người dùng. Bảng dưới so mức đó với
<b>giá kai cao nhất</b> trong 9 tiệm, để biết bán cho ai lợi hơn.</p>
{tbl_u}
<h2>Đọc bảng thế nào?</h2>
<ul class="tips">
<li><b>Số dương</b>: tiệm kai đang trả cao hơn mức app −5s → bán kai lợi hơn, lại nhanh và an toàn hơn gặp người lạ.</li>
<li><b>Số âm</b>: bán cho người dùng ở mức app −5s được nhiều hơn. Nhưng nhớ rủi ro khi gặp trực tiếp: <a href="/guide/lua-dao-iphone/">cảnh giác lừa đảo</a>.</li>
<li>Giá kai là máy <b>mới, chưa mở</b>. Một số màu bị tiệm trừ tiền, xem <a href="/guide/tru-mau-iphone/">bảng trừ màu</a>.</li>
<li>Giá Apple lấy theo giá niêm yết các tiệm ghi (có thể khác giá Apple Store theo màu).</li>
</ul>
<p class="pt-note">📈 Giá đổi nhiều lần mỗi ngày, xem trước khi chốt: <a href="/vi/?q=iPhone">kaitoriprice.com/vi</a></p>
<p class="small">Chỉ để tham khảo, không phải lời khuyên mua bán.</p>"""
    vi_page("/guide/ban-nguoi-dung-hay-kai/", "Bán iPhone cho người dùng (app −5s) hay bán kai? Bảng so sánh hôm nay | Kaitori Price",
            "So sánh giá Apple −5.000円 với giá kai cao nhất 9 tiệm cho từng mẫu iPhone 18 / Duo, cập nhật mỗi giờ.",
            "Bán người dùng hay kai", "⚖️ Bán cho người dùng (app −5s) hay bán kai?", body_u)

    # ---------------------------------------------------------------- 10. Bảng trừ màu từng tiệm (VI, từ ghi chú của tiệm)
    def _cnote(t):  # chỉ giữ phần trừ màu, bỏ câu điều kiện phía sau (店頭… / 郵送… / △…)
        t = re.sub(r"色減額[:：]?", "", t or "")
        return re.split(r"\s*(?:店頭|郵送|△|※)", t)[0].strip()[:90]
    COLOR = re.compile(r"ブラック|シルバー|グレイシャー|ホワイト|オレンジ|ブルー|ディープ|コズミック|ピンク|グリーン|パープル|レッド|色減額|White|Black|Silver|Blue", re.I)
    rows_c = []
    for it in ip18:
        notes = [(shops.get(s, {}).get("name", s), p.get("note", "")) for s, p in it["prices"].items()
                 if COLOR.search(p.get("note", "") or "") and re.search(r"-\s?[\d,]+", p.get("note", "") or "")]
        if not notes:
            continue
        link = f'<a href="/p/{it["_slug"]}/">{e(it["name"])}</a>' if it.get("_slug") else e(it["name"])
        cell = "<br>".join(f"<b>{e(n)}</b>: {e(_cnote(t))}" for n, t in notes)
        rows_c.append(f"<tr><td>{link}</td><td>{cell}</td></tr>")
    tbl_c = ('<div class="tw"><table class="pt"><thead><tr><th>Mẫu</th><th>Tiệm trừ tiền theo màu (đúng như tiệm ghi)</th></tr></thead>'
             f"<tbody>{''.join(rows_c)}</tbody></table></div>") if rows_c else "<p>Hiện chưa tiệm nào ghi trừ màu.</p>"
    body_c = f"""
<p class="upd">Cập nhật: {upd} JST (tự động mỗi giờ)</p>
<p>Cùng một mẫu iPhone, nhiều tiệm kai <b>trừ tiền theo màu</b> (ví dụ ブラック −9.000円). Màu không có trong ghi chú của tiệm thường được
mua đủ giá. Bảng dưới lấy <b>đúng ghi chú các tiệm đăng trên web</b>; tiệm không có trong bảng là tiệm không ghi trừ màu.</p>
{tbl_c}
<h2>Mẹo</h2>
<ul class="tips">
<li>Máy màu bị trừ ở tiệm A có thể <b>không bị trừ ở tiệm B</b>, nên với màu bị trừ càng phải so nhiều tiệm.</li>
<li>Tên màu tiếng Nhật: ブラック = đen, シルバー = bạc, ホワイト = trắng, ブルー = xanh dương, オレンジ = cam, グレイシャー = xanh băng.</li>
<li>Mức trừ có thể đổi trong ngày, xem lại ngay trước khi mang máy đi bán.</li>
</ul>
<p class="pt-note">📈 Giá và ghi chú từng tiệm: <a href="/vi/?q=iPhone">kaitoriprice.com/vi</a> · So bán người dùng hay kai: <a href="/guide/ban-nguoi-dung-hay-kai/">bảng so sánh</a></p>"""
    vi_page("/guide/tru-mau-iphone/", "Màu iPhone nào bị trừ tiền khi bán kai? Bảng trừ màu từng tiệm | Kaitori Price",
            "Bảng mức trừ tiền theo màu (ブラック, シルバー, グレイシャー, ホワイト…) của từng tiệm kaitori cho iPhone 18 / Duo, lấy từ ghi chú của tiệm, cập nhật mỗi giờ.",
            "Bảng trừ màu", "🎨 Màu iPhone nào bị trừ tiền? Bảng từng tiệm", body_c)

    # ---------------------------------------------------------------- 9. Trang giá hôm nay cho Google (VI) — 05/11/2026
    # Người Việt hay tìm "giá kai iPhone 18 Pro Max hôm nay", "giá kai Duo", "giá box Pokémon"; bảng tự cập nhật mỗi giờ.
    COL_VI = {"red": "Đỏ", "glacier": "Xanh băng", "black": "Đen", "silver": "Bạc", "nightsky": "Đen (ナイトスカイ)", "white": "Trắng",
              "blue": "Xanh", "orange": "Cam", "pink": "Hồng", "green": "Xanh lá", "purple": "Tím", "gold": "Vàng"}
    sname = lambda sid: shops.get(sid, {}).get("name", sid)
    FB = ('<p class="cta"><a href="https://www.facebook.com/groups/1118827834446963" target="_blank" rel="noopener">'
          '👥 Nhận giá mỗi ngày trong nhóm Facebook "Săn Giá Kaitori Nhật Bản" →</a></p>')

    def color_rows(models):
        """1 dòng / dung lượng: giá cao nhất (mọi tiệm) + giá cao nhất từng màu ở các tiệm có bảng giá theo màu."""
        cols, rows = [], []
        for it in models:
            ps = [(sid, pr) for sid, pr in it["prices"].items() if pr and pr.get("price")]
            if not ps:
                continue
            best_sid, best = max(ps, key=lambda kv: kv[1]["price"])
            per = {}
            for sid, pr in ps:
                for ck, v in (pr.get("c") or {}).items():
                    if v and (ck not in per or v > per[ck][1]):
                        per[ck] = (sid, v)
            for ck in per:
                if ck not in cols:
                    cols.append(ck)
            rows.append((it, best_sid, best["price"], per))
        cols.sort(key=lambda k: list(COL_VI).index(k) if k in COL_VI else 99)
        return cols, rows

    def color_table(models):
        cols, rows = color_rows(models)
        if not rows:
            return ""
        head = "".join(f"<th>{e(COL_VI.get(c, c))}</th>" for c in cols)
        trs = []
        for it, bsid, bp, per in rows:
            cap = (re.search(r"(\d+(GB|TB))", it["name"]) or [None, it["name"]])[1]
            link = f'<a href="/p/{it["_slug"]}/">{e(cap)}</a>' if it.get("_slug") else e(cap)
            msrp = it.get("msrp")
            cells = "".join(f"<td>{_yen(per[c][1])}<br><small>{e(sname(per[c][0]))}</small></td>" if c in per else "<td>—</td>" for c in cols)
            trs.append(f"<tr><td>{link}</td><td><b>{_yen(bp)}</b><br><small>{e(sname(bsid))}</small></td>{cells}"
                       f"<td>{_yen(msrp) if msrp else '—'}</td></tr>")
        return ('<div class="tw"><table class="pt"><thead><tr><th>Dung lượng</th><th>Cao nhất (mọi tiệm)</th>'
                f"{head}<th>Giá Apple</th></tr></thead><tbody>{''.join(trs)}</tbody></table></div>")

    def vi_faq(faq):
        return "<section><h2>Câu hỏi thường gặp</h2>" + "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in faq) + "</section>"

    for slug, label, rx, ask in [
        ("gia-kai-iphone-18-pro-max", "iPhone 18 Pro Max", r"iPhone 18 Pro Max \d", "18 Pro Max (hay gọi 18 PRM)"),
        ("gia-kai-iphone-duo", "iPhone Duo", r"iPhone Duo \d", "iPhone Duo"),
    ]:
        models = sorted([i for i in phones if re.match(rx, i["key"]) and i["n_shops"] >= 2], key=_iphone_order)
        if not models:
            continue
        cols, rows = color_rows(models)
        top = rows[0] if rows else None
        top_cap = (re.search(r"(\d+(GB|TB))", top[0]["name"]) or [None, ""])[1] if top else ""
        top_txt = (f"Bản {e(top_cap)} đang được trả cao nhất "
                   f"<b>{_yen(top[2])}</b> ở {e(sname(top[1]))}.") if top else ""
        faq = [
            (f"Giá kai {label} hôm nay bao nhiêu?", f"Xem bảng trên: giá cao nhất từng dung lượng ở {n_shops} tiệm kaitori lớn ở Nhật, cập nhật mỗi giờ (lần cuối {updated} JST)."),
            ("Màu nào bị trừ tiền?", "Mỗi tiệm trừ khác nhau. Cột theo màu là giá đã trừ ở các tiệm có bảng giá riêng từng màu; tiệm khác ghi số trừ trong ghi chú. Xem thêm bài 'Màu iPhone nào bị trừ tiền?'."),
            ("Bán ở tiệm hay bán cho người dùng?", "Bán tiệm nhanh, an toàn, không lo lừa đảo; bán người dùng (thường giá Apple trừ vài nghìn) được hơn nhưng phải tự tìm người và cẩn thận khi giao dịch."),
            ("Cần mang gì khi bán?", "Máy mới chưa mở (còn màng co), giấy tờ tuỳ thân có địa chỉ (thẻ ngoại kiều 在留カード). Một số tiệm cần đặt trước hoặc giới hạn số máy mỗi người."),
        ]
        body = f"""
<p class="upd">Giá cập nhật: {upd} JST (tự động mỗi giờ)</p>
<p>Bảng giá thu mua (kai, 買取) <b>{e(ask)}</b> máy mới chưa mở ở <b>{n_shops} tiệm kaitori</b> lớn ở Nhật. {top_txt}
Cùng một máy mà các tiệm trả lệch nhau vài nghìn tới hơn chục nghìn yên, nên so giá trước khi bán.</p>
<h2>Giá kai {e(label)} hôm nay theo dung lượng và màu</h2>
{color_table(models)}
<p class="small">Cột theo màu: giá cao nhất của màu đó ở các tiệm có bảng giá riêng từng màu (đã trừ màu). "—" là chưa có tiệm nào ghi giá riêng cho màu đó.
Bấm dung lượng để xem giá cả {n_shops} tiệm và biểu đồ giá.</p>
<h2>Mẹo bán được giá cao</h2>
<ul class="tips">
<li><b>Chọn đúng màu:</b> màu bị trừ ít nhất thường có giá cao nhất; xem <a href="/guide/tru-mau-iphone/">bảng trừ màu từng tiệm</a>.</li>
<li><b>Giữ máy nguyên seal:</b> mở hộp hoặc kích hoạt là mất giá "mới chưa mở".</li>
<li><b>Bán xa tiệm:</b> nhiều tiệm nhận gửi bưu điện (郵送買取); để ý điều kiện giữ giá theo ngày hàng tới.</li>
<li><b>Giá kai đang giảm?</b> Xem <a href="/guide/gia-iphone-giam/">nên huỷ, bán ngay hay giữ</a> và <a href="/guide/huy-iphone/">cách huỷ đơn</a>.</li>
<li><b>Giao dịch trực tiếp trong nhóm:</b> đọc <a href="/guide/lua-dao-iphone/">các kiểu lừa hay gặp</a> trước khi gặp.</li>
</ul>
<p class="cta"><a href="/vi/?q={e(label)}">Xem giá {e(label)} ở {n_shops} tiệm, chọn màu để thấy giá đã trừ →</a></p>
{FB}
{vi_faq(faq)}
<p class="small">Giá là giá công khai trên web các tiệm, chưa tính điểm thưởng và phí gửi; giá thực tế khi bán có thể khác. Bài chỉ để tham khảo, không phải lời khuyên đầu tư.</p>"""
        vi_page(f"/guide/{slug}/", f"Giá kai {label} hôm nay ở {n_shops} tiệm (cập nhật mỗi giờ) | Kaitori Price",
                f"Giá thu mua {label} mới chưa mở hôm nay ở {n_shops} tiệm kaitori Nhật: từng dung lượng, từng màu, so với giá Apple. Tự cập nhật mỗi giờ.",
                f"Giá kai {label}", f"📱 Giá kai {label} hôm nay", body)

    # hộp thẻ Pokémon: tên gọi trong nhóm FB → tên tiệm ghi
    NICK = [("Box 30th", "30th CELEBRATION", r"【M6a】"), ("set 9", "9種セット", None), ("dekki mèo", "エーフィ・ブラッキー", None),
            ("Dream", "メガドリームex", None), ("Inferno X", "インフェルノX", None), ("Ninja Spinner", "ニンジャスピナー", None),
            ("Mega Brave", "メガブレイブ", None), ("Mega Symphonia", "メガシンフォニア", None)]
    cards = items.get("card", [])
    nick_rows = []
    for nick, frag, must in NICK:
        hit = [i for i in cards if frag in i["name"] and (not must or must in i["name"]) and not i["name"].startswith("PSA") and i["n_shops"] >= 2]
        if hit:
            it = max(hit, key=lambda i: (i["n_shops"], i["best"]))
            ps = sorted([kv for kv in it["prices"].items() if kv[1] and kv[1].get("price")], key=lambda kv: -kv[1]["price"])
            link = f'<a href="/p/{it["_slug"]}/">{e(it["name"].strip())}</a>' if it.get("_slug") else e(it["name"].strip())
            nick_rows.append(f"<tr><td><b>{e(nick)}</b></td><td>{link}</td><td><b>{_yen(ps[0][1]['price'])}</b><br><small>{e(sname(ps[0][0]))}</small></td>"
                             f"<td>{_yen(ps[-1][1]['price'])}</td><td>{it['n_shops']}</td></tr>")
    box_rows = []
    for it in boxes[:30]:
        ps = sorted([kv for kv in it["prices"].items() if kv[1] and kv[1].get("price")], key=lambda kv: -kv[1]["price"])
        link = f'<a href="/p/{it["_slug"]}/">{e(it["name"].strip())}</a>' if it.get("_slug") else e(it["name"].strip())
        box_rows.append(f"<tr><td>{link}</td><td><b>{_yen(ps[0][1]['price'])}</b><br><small>{e(sname(ps[0][0]))}</small></td>"
                        f"<td>{_yen(ps[0][1]['price'] - ps[-1][1]['price'])}</td><td>{it['n_shops']}</td></tr>")
    if nick_rows or box_rows:
        th = "<thead><tr><th>Tên trong nhóm</th><th>Tên tiệm ghi</th><th>Cao nhất</th><th>Thấp nhất</th><th>Số tiệm</th></tr></thead>"
        th2 = "<thead><tr><th>Hộp</th><th>Cao nhất</th><th>Chênh cao–thấp</th><th>Số tiệm</th></tr></thead>"
        body_box = f"""
<p class="upd">Giá cập nhật: {upd} JST (tự động mỗi giờ)</p>
<p>Giá thu mua <b>hộp thẻ Pokémon (ポケカ BOX)</b> mới, còn màng co, ở các tiệm kaitori lớn ở Nhật. Tên hộp trên web tiệm toàn tiếng Nhật,
nên bảng đầu ghép <b>tên anh em hay gọi trong nhóm</b> với tên tiệm ghi để dễ tìm.</p>
<h2>Hộp đang hot: tên gọi trong nhóm → giá</h2>
{'<div class="tw"><table class="pt">' + th + '<tbody>' + ''.join(nick_rows) + '</tbody></table></div>' if nick_rows else ''}
<h2>30 hộp được nhiều tiệm thu nhất</h2>
{'<div class="tw"><table class="pt">' + th2 + '<tbody>' + ''.join(box_rows) + '</tbody></table></div>' if box_rows else ''}
<h2>Điều kiện thu mua cần biết</h2>
<ul class="tips">
<li><b>Còn màng co (シュリンク付き):</b> đa số tiệm chỉ thu box chưa bóc, còn nguyên màng. Bóc màng hoặc màng rách là giá thấp hơn nhiều hoặc không thu.</li>
<li><b>Hộp móp, hư:</b> có tiệm trừ tiền tuỳ mức. Mua online thì chụp ảnh hộp lúc mở thùng; móp nặng thì hỏi tiệm trước.</li>
<li><b>Giá đổi rất nhanh</b> theo đợt phát hành và tin bán lại (再販), xem giá ngay trước khi mang đi.</li>
</ul>
<p class="cta"><a href="/vi/?c=card">Xem giá tất cả hộp thẻ ở các tiệm →</a></p>
{FB}
{vi_faq([("Box Pokémon nào đang được giá nhất?", "Xem bảng trên, sắp theo số tiệm thu và giá cao nhất, cập nhật mỗi giờ."),
         ("Box mất màng co có bán được không?", "Đa số tiệm chỉ thu box còn màng co; vài tiệm có bảng giá riêng cho box không màng co, thấp hơn hàng còn màng."),
         ("Bán thẻ lẻ PSA ở đâu?", "Một số tiệm thu thẻ đã chấm điểm PSA; tìm tên thẻ trên web để so giá các tiệm.")])}
<p class="small">Giá là giá công khai trên web các tiệm cho box mới còn màng co; giá thực tế có thể khác. Không phải lời khuyên mua bán hay đầu tư.</p>"""
        vi_page("/guide/gia-kai-pokemon-box/", "Giá thu mua hộp thẻ Pokémon (box ポケカ) hôm nay | Kaitori Price",
                "Giá kai box Pokémon mới nhất ở các tiệm Nhật, ghép tên gọi trong nhóm (Box 30th, set 9, dekki mèo…) với tên tiệm ghi. Cập nhật mỗi giờ.",
                "Giá box Pokémon", "🃏 Giá thu mua hộp thẻ Pokémon hôm nay", body_box)

    # ---------------------------------------------------------------- 10. Lịch phát hành / bốc thăm (VI) — 05/11/2026, dữ liệu radar/events.json
    import json as _json
    from pathlib import Path as _Path
    try:
        evs = _json.loads((_Path(__file__).parent / "events.json").read_text(encoding="utf-8")).get("events", [])
    except Exception:
        evs = []
    today = (updated or "")[:10]
    evs = sorted([x for x in evs if (x.get("end") or x.get("date", "")) >= today], key=lambda x: (x.get("date", ""), x.get("time", "")))
    if evs:
        KIND = {"release": ("🆕", "Phát hành"), "lottery": ("🎟", "Bốc thăm"), "online": ("🛒", "Bán online")}
        WD = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
        import datetime as _dt
        allit = [i for c in ("card", "phone", "game") for i in items.get(c, [])]
        def dshow(d):
            try:
                x = _dt.date.fromisoformat(d)
                return f"{x.day}/{x.month} ({WD[x.weekday()]})"
            except Exception:
                return d
        lis = []
        for x in evs:
            ic, kl = KIND.get(x.get("kind"), ("📌", ""))
            when = dshow(x["date"]) + (f" {e(x['time'])}" if x.get("time") else "") + (f" → {dshow(x['end'])}" if x.get("end") else "")
            price = ""
            if x.get("match"):
                hit = sorted([i for i in allit if x["match"] in i["name"] and not i["name"].startswith("PSA")], key=lambda i: (-i["n_shops"], -i["best"]))
                if hit:
                    it = hit[0]
                    nm = f'<a href="/p/{it["_slug"]}/">{e(it["name"].strip())}</a>' if it.get("_slug") else e(it["name"].strip())
                    price = f'<p class="ev-p">💴 Giá kai hiện tại: <b>{_yen(it["best"])}</b> ({e(sname(it["best_shop"]))}, {it["n_shops"]} tiệm) · {nm}</p>'
            src = f' · <a href="{e(x["src"])}" target="_blank" rel="noopener nofollow">nguồn</a>' if x.get("src") else ""
            warn = "" if x.get("confirmed", True) else ' <span class="ev-w">chưa xác nhận</span>'
            lis.append(f'<li class="ev"><div class="ev-d">{ic} <b>{when}</b> · {e(kl)}{warn}</div><div class="ev-t">{e(x["title"])}</div>'
                       f'<p class="ev-n">{e(x.get("where", ""))}{" — " + e(x["note"]) if x.get("note") else ""}{src}</p>{price}</li>')
        body_cal = f"""
<p class="upd">Cập nhật: {upd} JST</p>
<p>Lịch các đợt <b>phát hành, bốc thăm (抽選) và bán online</b> thẻ Pokémon sắp tới ở Nhật, kèm <b>giá kai hiện tại</b> nếu tiệm đã thu.
Mỗi mục có nguồn; lịch bốc thăm của từng cửa hàng hay đổi, nhớ xem lại thông báo chính thức trước khi đăng ký.</p>
<style>.evs{{list-style:none;padding:0;margin:12px 0;display:grid;gap:10px}}.ev{{border:1px solid #e4e4e7;border-radius:12px;padding:10px 12px;background:#fff}}.ev-d{{font-size:.85rem;color:#52525b}}.ev-t{{font-weight:800;margin:2px 0}}.ev-n,.ev-p{{margin:4px 0 0;font-size:.85rem}}.ev-w{{background:#fef3c7;color:#92400e;border-radius:6px;padding:0 6px;font-size:.75rem;font-weight:700}}</style><ul class="evs">{''.join(lis)}</ul>
<h2>Mẹo khi đi bốc thăm / săn hàng</h2>
<ul class="tips">
<li>Pokémon Center Online thường cần tài khoản và xác minh danh tính; đăng ký sẵn trước ngày mở đơn.</li>
<li>Trúng rồi đừng bóc màng co nếu định bán: đa số tiệm chỉ thu box còn màng (xem <a href="/guide/gia-kai-pokemon-box/">giá box Pokémon</a>).</li>
<li>Giá kai box mới thường biến động mạnh vài ngày đầu sau phát hành; xem giá ngay trước khi mang đi.</li>
</ul>
{FB}
<p class="small">Lịch tổng hợp từ thông báo của cửa hàng và trang tin; có thể thay đổi. Không phải lời khuyên mua bán hay đầu tư.</p>"""
        vi_page("/guide/lich-pokemon/", "Lịch phát hành & bốc thăm thẻ Pokémon ở Nhật (cập nhật mỗi ngày) | Kaitori Price",
                "Lịch phát hành box Pokémon, bốc thăm (抽選) Pokémon Center và cửa hàng, bán online sắp tới ở Nhật, kèm giá kai hiện tại.",
                "Lịch Pokémon", "📅 Lịch phát hành & bốc thăm thẻ Pokémon", body_cal)

    # ---------------------------------------------------------------- trang tổng hợp (JA /guide/, VI /guide/vi/)
    # (path, icon, tiêu đề VI, mô tả VI, có bản tiếng Việt?) — nhóm theo mục để dễ tìm
    SECTIONS = [
        ("sell", "💴 売る前に読む", "💴 Trước khi bán"),
        ("buy", "🛒 お得に買う・仕入れる", "🛒 Mua rẻ để bán lại"),
    ]
    META = {
        "/guide/iphone-18-kaitori/": ("sell", "📱", "Bán iPhone 18 ở đâu được giá nhất", "Bảng giá 12 mẫu iPhone 18 / Duo ở 8 tiệm, mẹo màu bị trừ tiền, giấy tờ cần mang", False),
        "/guide/pokeca-box-kaitori/": ("sell", "🃏", "Giá thu mua hộp thẻ Pokémon", "Bảng 30 hộp thẻ so giá nhiều tiệm, mẹo màng co (シュリンク), giá thùng", False),
        "/guide/yoyaku-kaitori/": ("sell", "⏰", "Đặt trước khi bán (予約買取) là gì", "Cách giữ giá, hạn giữ giá, quy định huỷ cần chú ý", False),
        "/guide/kabunushi-yutai/": ("buy", "🎟", "Mua rẻ 20–30% bằng phiếu cổ đông", "ビックカメラ, エディオン, ヤマダ, ASICS / Onitsuka Tiger và 3 điều cần biết", "/guide/phieu-co-dong/"),
    }
    def card(href, icon, title, desc, tag=""):
        return (f'<a class="gcard" href="{href}"><span class="gi">{icon}</span><span class="gt"><b>{e(title)}</b>'
                f'<small>{e(desc)}</small></span>{tag}<span class="ga">→</span></a>')
    ja_html = []
    for sid, ja_t, _ in SECTIONS:
        ja_cards = [card(p, META[p][1], h, d) for p, h, d in guides if META.get(p, ("",))[0] == sid]
        if ja_cards:
            ja_html.append(f'<section class="gsec"><h2>{ja_t}</h2><div class="ggrid">{"".join(ja_cards)}</div></section>')
    # VI: chia theo chủ đề + nút lọc + ô tìm (bài nhiều lên vẫn dễ tìm)
    have = {p for p, _, _ in guides}
    def vcard(p):
        m = META[p]
        return card(m[4], m[1], m[2], m[3]) if m[4] else card(p, m[1], m[2], m[3], '<span class="gl">日本語</span>')
    VI_TOPICS = [
        ("iphone", "📱 iPhone", [card("/guide/gia-kai-iphone-18-pro-max/", "💴", "Giá kai iPhone 18 Pro Max hôm nay", "Từng dung lượng, từng màu, so giá Apple — cập nhật mỗi giờ"),
                               card("/guide/gia-kai-iphone-duo/", "💴", "Giá kai iPhone Duo hôm nay", "Từng dung lượng, đen / trắng, so giá Apple"),
                               card("/guide/gia-iphone-giam/", "📉", "Giá kai iPhone giảm: huỷ, bán hay giữ?", "Bảng giá mới nhất 9 tiệm + cách tính lời lỗ"),
                               card("/guide/huy-iphone/", "❌", "Cách huỷ đơn iPhone không mất phí", "Apple Store, docomo, au, SoftBank, Rakuten: huỷ trước khi gửi hàng"),
                               card("/guide/tra-iphone-apple/", "↩️", "Trả iPhone cho Apple trong 14 ngày", "Điều kiện, tắt Tìm iPhone, khi nào bị phí 15%"),
                               card("/guide/ban-nguoi-dung-hay-kai/", "⚖️", "Bán cho người dùng (app −5s) hay bán kai?", "Bảng so giá Apple −5.000 với giá kai cao nhất từng mẫu"),
                               card("/guide/tru-mau-iphone/", "🎨", "Màu iPhone nào bị trừ tiền?", "Bảng trừ màu từng tiệm, đúng như tiệm ghi"),
                               card("/guide/lua-dao-iphone/", "⚠️", "Cảnh giác lừa đảo khi mua bán trực tiếp", "Hộp seal có vật lạ, chuyển khoản giả, máy khoá iCloud / 利用制限")]
                              + [vcard(p) for p in ["/guide/iphone-18-kaitori/"] if p in have]),
        ("shop", "🏪 Bán cho tiệm", [card("/guide/lich-pokemon/", "📅", "Lịch phát hành & bốc thăm thẻ Pokémon", "Ngày bán, bốc thăm sắp tới + giá kai hiện tại"),
                                   card("/guide/gia-kai-pokemon-box/", "🃏", "Giá thu mua hộp thẻ Pokémon hôm nay", "Tên gọi trong nhóm (Box 30th, set 9…) → giá từng tiệm"),
                                   card("/guide/tiem-kaitori/", "📍", "Danh sách tiệm kaitori (Tokyo, Osaka, Nagoya)",
                                         "Địa chỉ, giờ mở cửa, ga gần nhất, link bản đồ của các tiệm web đang so giá")]
                                   + [vcard(p) for p in ["/guide/yoyaku-kaitori/", "/guide/pokeca-box-kaitori/"] if p in have]),
        ("buy", "🛒 Mua rẻ để bán lại", [card("/guide/meo-mua-re/", "🛒", "7 cách mua hàng giảm giá ở Nhật",
                                             "Rakuten, Yahoo, Amazon, điểm điện máy, phiếu cổ đông, trang tích điểm, điện thoại 1 yên")]
                                       + [vcard(p) for p in ["/guide/kabunushi-yutai/"] if p in have]),
    ]
    vi_bar = ('<div class="gbar"><input id="gq" type="search" placeholder="🔍 Tìm mẹo (vd: huỷ đơn, trả máy, Pokémon…)">'
              '<div class="gtabs"><button class="gtab on" data-t="">Tất cả</button>'
              + "".join(f'<button class="gtab" data-t="{k}">{e(t)}</button>' for k, t, c in VI_TOPICS if c)
              + '</div></div>')
    vi_html = [vi_bar] + [f'<section class="gsec" data-t="{k}"><h2>{e(t)}</h2><div class="ggrid">{"".join(c)}</div></section>'
                          for k, t, c in VI_TOPICS if c]
    vi_html.append('<p class="gnone" hidden>Không tìm thấy bài phù hợp — hỏi trong nhóm Facebook bên dưới nhé.</p>'
                   '<script>(()=>{const q=document.getElementById("gq"),tabs=document.querySelectorAll(".gtab"),secs=document.querySelectorAll(".gsec[data-t]"),none=document.querySelector(".gnone");let t="";'
                   'const norm=s=>s.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g,"").replace(/đ/g,"d");'
                   'function f(){const w=norm(q.value.trim());let n=0;secs.forEach(s=>{let k=0;s.querySelectorAll(".gcard").forEach(c=>{const ok=(!t||s.dataset.t===t)&&(!w||norm(c.textContent).includes(w));c.hidden=!ok;k+=ok});s.hidden=!k;n+=k});none.hidden=!!n}'
                   'tabs.forEach(b=>b.onclick=()=>{t=b.dataset.t;tabs.forEach(x=>x.classList.toggle("on",x===b));f()});q.oninput=f})();</script>')
    idx_body = (f'<nav class="bc"><a href="/">トップ</a> › 買取ガイド</nav><h1>📚 買取ガイド</h1>'
                f'<p class="lead">買取価格の比較データをもとに、高く売る・安く買うためのポイントをまとめています。</p>{"".join(ja_html)}')
    out = site / "guide"
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page("買取ガイド｜高く売る・安く買うためのポイント - 買取プライス",
                                         "iPhone・ポケカBOXを高く売る方法、株主優待券で安く買う方法など。大手買取店の価格比較データをもとに解説。",
                                         "/guide/", idx_body, [], updated), encoding="utf-8")
    vi_body = (f'<nav class="bc"><a href="/vi/">Trang chủ</a> › Mẹo & Hướng dẫn</nav><h1>📚 Mẹo & Hướng dẫn</h1>'
               f'<p class="lead">Kinh nghiệm bán hàng cho tiệm kaitori và mẹo mua rẻ ở Nhật. Bài có nhãn 日本語 hiện chỉ có tiếng Nhật.</p>{"".join(vi_html)}'
               f'<p><a href="https://www.facebook.com/groups/1118827834446963" target="_blank" rel="noopener">👥 Hỏi đáp trong nhóm Facebook "Săn Giá Kaitori Nhật Bản" →</a></p>')
    out = site / "guide" / "vi"
    out.mkdir(parents=True, exist_ok=True)
    pv = page("Mẹo & Hướng dẫn bán kaitori, mua rẻ ở Nhật | Kaitori Price",
              "Kinh nghiệm bán iPhone, máy game, thẻ Pokémon cho tiệm kaitori và mẹo mua rẻ ở Nhật.", "/guide/vi/", vi_body, [], updated)
    pv = pv.replace('<html lang="ja">', '<html lang="vi">', 1).replace(
        '<a class="hd-cta" href="/">全商品を比較 →</a>', '<a class="hd-cta" href="/vi/">So giá 9 tiệm →</a>', 1)
    (out / "index.html").write_text(pv, encoding="utf-8")
    extra.append(("/guide/vi/", "weekly"))
    return [("/guide/", "weekly")] + [(p, "daily") for p, _, _ in guides] + extra
