# Kaitori Price（買取価格比較） (kaitori-radar)

ポケカ未開封BOX・iPhone新品の買取価格を大手買取店の公開ページから取得して比較する静的サイト（人気商品は10〜22時半の30分ごと、全商品は毎日10時台）。

- radar/shops.py — 各店舗のスクレイパー（リクエスト間隔1.8秒）
- radar/run.py — 集計 → site/data/latest.json, site/data/history.json
- site/ — 静的サイト
