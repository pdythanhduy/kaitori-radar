// Trích "hãng / dòng máy / dung lượng" từ tên sản phẩm để làm bộ lọc (faceted search).
(function () {
  const N = (s) => (s || "").normalize("NFKC");
  const BRANDS = {
    phone: [["iPhone", /iPhone/i], ["Samsung Galaxy", /Galaxy|SAMSUNG|\bSC-|\bSCG\d/i], ["Google Pixel", /Pixel/i], ["Sony Xperia", /Xperia|\bSO-|\bSOG\d/i],
      ["AQUOS (SHARP)", /AQUOS|SHARP|シャープ|\bSH-|\bSHG\d/i], ["OPPO", /OPPO/i], ["Xiaomi", /Xiaomi|Redmi|POCO/i], ["Motorola", /motorola|\bmoto\b/i],
      ["arrows", /arrows|\bF-\d/i], ["ASUS", /Zenfone|ROG Phone|ASUS/i], ["Nothing", /Nothing Phone|\bCMF\b/i]],
    tablet: [["iPad", /iPad/i], ["Galaxy Tab", /Galaxy Tab/i], ["Kindle / Fire", /Kindle|Fire HD|Fire TV/i], ["Pixel Tablet", /Pixel Tablet/i], ["Xiaomi", /Xiaomi|Redmi/i], ["LAVIE / NEC", /LAVIE|NEC/i]],
    game: [["Nintendo Switch 2", /Switch\s?2/i], ["Nintendo Switch", /Switch/i], ["PlayStation 5", /PlayStation\s?5|PS5|プレイステーション5|プレステ5|CFI-/i],
      ["PS VR2 / Portal", /VR2|Portal/i], ["Xbox", /Xbox/i], ["Steam", /Steam/i], ["Meta Quest", /Quest/i], ["ROG Ally", /ROG|Ally/i], ["Nintendo (khác)", /Nintendo|任天堂/i]],
    camera: [["Canon", /Canon|キヤノン|キャノン|EOS|\bRF\d/i], ["Nikon", /Nikon|ニコン|\bZ\s?\d|NIKKOR/i], ["Sony", /SONY|ソニー|ILCE|α\d|\bSEL\d|\bFE\s?\d/i],
      ["Fujifilm", /FUJIFILM|富士フイルム|\bX-[A-Z]\d|instax|チェキ/i], ["Panasonic", /Panasonic|LUMIX/i], ["OM / Olympus", /OM SYSTEM|OLYMPUS|オリンパス/i],
      ["Ricoh / Pentax", /RICOH|リコー|PENTAX|\bGR\s?I/i], ["SIGMA", /SIGMA/i], ["TAMRON", /TAMRON/i], ["DJI", /DJI|Osmo/i], ["GoPro", /GoPro/i], ["Insta360", /Insta360/i],
      ["Hasselblad", /ハッセルブラッド|Hasselblad/i], ["Leica", /Leica|ライカ/i]],
    card: [["Pokémon", /ポケモン|ポケカ|Pokémon|Pokemon/i], ["ONE PIECE", /ONE PIECE|ワンピース|\bOP-\d|\bEB-\d|\bST-?\d/i], ["遊戯王", /遊戯王|YU-GI-OH/i],
      ["Dragon Ball", /ドラゴンボール|DRAGON BALL|\bFB\d/i], ["Duel Masters", /デュエル/i]],
    audio: [["Apple AirPods", /AirPods|Beats/i], ["Sony", /SONY|ソニー|\bWF-|\bWH-|LinkBuds|INZONE/i], ["Bose", /Bose/i], ["Sennheiser", /Sennheiser|ゼンハイザー|MOMENTUM/i],
      ["Anker", /Anker|Soundcore/i], ["JBL", /JBL/i], ["Jabra", /Jabra|Elite/i], ["Samsung", /Galaxy Buds/i], ["Google", /Pixel Buds/i]],
    watch: [["Apple Watch", /Apple Watch/i], ["Galaxy Watch", /Galaxy Watch/i], ["Pixel Watch", /Pixel Watch/i], ["Garmin", /Garmin|ガーミン/i], ["Casio / G-SHOCK", /CASIO|カシオ|G-SHOCK/i],
      ["Seiko", /SEIKO|セイコー|Grand Seiko/i], ["Citizen", /CITIZEN|シチズン/i]],
    pc: [["Apple Mac", /MacBook|Mac mini|iMac|Mac Studio/i], ["NVIDIA GPU", /GeForce|RTX/i], ["AMD", /Radeon|Ryzen/i], ["Microsoft Surface", /Surface/i], ["ASUS", /ASUS/i], ["Lenovo", /Lenovo|ThinkPad/i], ["Dell", /Dell|Alienware/i], ["HP", /\bHP\b/i]],
  };
  const GENERIC = [["Apple", /Apple|AirTag|Apple TV|HomePod/i], ["Dyson", /dyson|ダイソン/i], ["Panasonic", /Panasonic|パナソニック/i], ["SHARP", /SHARP|シャープ/i],
    ["日立 Hitachi", /日立|HITACHI/i], ["東芝 Toshiba", /東芝|TOSHIBA/i], ["iRobot", /iRobot|ルンバ|Roomba/i], ["ReFa", /ReFa|リファ/i], ["Philips", /PHILIPS|フィリップス/i],
    ["BALMUDA", /BALMUDA|バルミューダ/i], ["De'Longhi", /DeLonghi|デロンギ/i], ["Sony", /SONY|ソニー/i], ["Nintendo", /Nintendo|任天堂/i], ["Amazon", /Echo|Fire TV|Kindle/i],
    ["Anker", /Anker/i], ["SwitchBot", /SwitchBot/i], ["Canon", /Canon|キヤノン/i], ["EPSON", /EPSON|エプソン/i], ["BANDAI", /BANDAI|バンダイ/i]];

  function brand(cat, name) {
    const n = N(name);
    for (const [b, re] of (BRANDS[cat] || GENERIC)) if (re.test(n)) return b;
    if (BRANDS[cat]) for (const [b, re] of GENERIC) if (re.test(n)) return b;
    return "Khác";
  }

  function series(cat, it) {
    const n = N(it.key.startsWith("iPhone") ? it.key : it.name);
    let m;
    if ((m = n.match(/iPhone\s*(\d{1,2}e?|Air|Duo|SE)(\s*(Pro\s*Max|Pro|Plus|mini))?/i))) return "iPhone " + m[1] + (m[3] ? " " + m[3].replace(/\s+/g, " ") : "");
    if ((m = n.match(/iPad\s*(Pro|Air|mini)?/i))) {
      const size = (n.match(/(\d{2}(\.\d)?)\s*(インチ|inch|型)/i) || [])[1];
      return "iPad" + (m[1] ? " " + m[1] : "") + (size && m[1] !== "mini" ? ` ${Math.round(+size)}"` : "");
    }
    if ((m = n.match(/Galaxy\s+(Z\s*(Fold|Flip)\s*\d+|S\d{2}\s*(Ultra|\+|FE|Edge)?|A\d{2,3}|Tab\s*S\d+)/i))) return "Galaxy " + m[1].replace(/\s+/g, " ").trim();
    if ((m = n.match(/Pixel\s*(\d+a?)\s*(Pro\s*XL|Pro\s*Fold|Pro|XL)?/i))) return "Pixel " + m[1] + (m[2] ? " " + m[2].replace(/\s+/g, " ") : "");
    if ((m = n.match(/Xperia\s*(1|5|10|Ace)\s*(I{1,3}V?|IV|V|VI|VII|Ⅶ|Ⅵ|Ⅴ)?/i))) return "Xperia " + m[1] + (m[2] ? " " + m[2] : "");
    if ((m = n.match(/Apple Watch\s*(Ultra\s*\d?|Series\s*\d+|SE)/i))) return "Apple Watch " + m[1].replace(/\s+/g, " ");
    if ((m = n.match(/AirPods\s*(Pro\s*\d?|Max|4|3)?/i))) return "AirPods" + (m[1] ? " " + m[1].trim() : "");
    if (cat === "game") {
      if (/Pro/i.test(n) && /PlayStation\s?5|PS5|CFI-7/i.test(n)) return "PS5 Pro";
      if (/デジタル|Digital/i.test(n) && /PlayStation\s?5|PS5|CFI-/i.test(n)) return "PS5 Digital";
      if (/PlayStation\s?5|PS5|CFI-[12]/i.test(n)) return "PS5";
      if (/Switch\s?2/i.test(n)) return /セット|同梱/i.test(n) ? "Switch 2 (bộ kèm game)" : "Switch 2";
      if (/有機EL|OLED/i.test(n)) return "Switch OLED";
      if (/Switch\s?Lite/i.test(n)) return "Switch Lite";
      if (/コントローラー|DualSense|Controller|Pro\s?コン/i.test(n)) return "Tay cầm";
    }
    if (cat === "card") return /BOX|ボックス/i.test(n) ? "BOX" : /PSA/i.test(n) ? "PSA" : "Khác";
    return "";
  }

  // "1024GB" → 1024, "1TB" → 1024
  function capGB(label) {
    const m = /^(\d+)(GB|TB)$/.exec(label || "");
    return m ? +m[1] * (m[2] === "TB" ? 1024 : 1) : 0;
  }
  function capLabel(gb) {
    return gb >= 1024 && gb % 1024 === 0 ? gb / 1024 + "TB" : gb + "GB";
  }
  function capacity(it) {
    // key iPhone dạng "iPhone 12 64GB|iphone1264gb": chỉ lấy phần trước "|" (phần sau mất dấu cách → "1264GB")
    // key name:… cũng mất dấu cách → dùng tên sản phẩm
    const src = it.key.startsWith("iPhone") ? it.key.split("|")[0] : it.name;
    // số GB/TB đứng riêng, không dính chữ cái phía trước (bỏ mã máy kiểu "FMVL75GB")
    const all = [...N(src).matchAll(/(?:^|[^\dA-Za-z])(\d{1,4})\s*(GB|TB)\b/gi)]
      .map((m) => +m[1] * (m[2].toUpperCase() === "TB" ? 1024 : 1))
      .filter((gb) => gb >= 8 && gb <= 8192);
    // viết tắt "256G" (không có B), chỉ nhận các mức dung lượng chuẩn để không nhầm "5G"
    for (const m of N(src).matchAll(/(?:^|[^\dA-Za-z])(32|64|128|256|512)G(?![A-Za-z])/g)) all.push(+m[1]);
    if (!all.length) return "";
    // nhiều số (vd "8GB/256GB", "12GB+512GB") → số lớn nhất là bộ nhớ lưu trữ, số nhỏ là RAM
    return capLabel(Math.max(...all));
  }
  const capSort = (a, b) => capGB(a) - capGB(b);

  // khoá sắp xếp tự nhiên: số lớn (đời mới) lên trước
  const SPECIAL = { Duo: 18.9, Air: 17.05 };
  function ver(s) {
    const words = s.split(/\s+/);
    for (const k in SPECIAL) if (words.includes(k)) return SPECIAL[k];
    return +(s.match(/\d+/) || [0])[0];
  }
  function seriesSort(a, b) {
    return ver(b) - ver(a) || a.localeCompare(b);
  }
  const CAP_ORDER = ["64GB", "128GB", "256GB", "512GB", "1TB", "2TB"];

  window.FACETS = {
    enrich(items) {
      for (const it of items) {
        if (it._f) continue;
        it._f = { brand: brand(it.cat, it.name), series: series(it.cat, it), cap: ["phone", "tablet"].includes(it.cat) ? capacity(it) : "" };
      }
      return items;
    },
    seriesSort, CAP_ORDER, capSort,
  };
})();
