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
    ja_html, vi_html = [], []
    for sid, ja_t, vi_t in SECTIONS:
        ja_cards = [card(p, META[p][1], h, d) for p, h, d in guides if META.get(p, ("",))[0] == sid]
        vi_cards = []
        for p, h, d in guides:
            m = META.get(p)
            if not m or m[0] != sid:
                continue
            if m[4]:
                vi_cards.append(card(m[4], m[1], m[2], m[3]))
            else:
                vi_cards.append(card(p, m[1], m[2], m[3], '<span class="gl">日本語</span>'))
        if ja_cards:
            ja_html.append(f'<section class="gsec"><h2>{ja_t}</h2><div class="ggrid">{"".join(ja_cards)}</div></section>')
        if vi_cards:
            vi_html.append(f'<section class="gsec"><h2>{vi_t}</h2><div class="ggrid">{"".join(vi_cards)}</div></section>')
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
