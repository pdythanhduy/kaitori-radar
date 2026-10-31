# 新品買取価格比較（β版） (kaitori-radar)

ポケカ未開封BOX・iPhone新品の買取価格を大手買取店の公開ページから1日3回取得して比較する静的サイト。

- radar/shops.py — 各店舗のスクレイパー（1.8秒間隔・1日3回のみ）
- radar/run.py — 集計 → site/data/latest.json, site/data/history.json
- site/ — 静的サイト
