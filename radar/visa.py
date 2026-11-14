"""Mục "Visa & thủ tục" (tiếng Việt) — trang tĩnh + công cụ chạy hoàn toàn trong trình duyệt (không gửi dữ liệu đi đâu).

/visa/            trang chủ mục
/visa/vinh-tru/   kiểm tra điều kiện vĩnh trú (永住)
/visa/ve-nuoc/    đếm ngược hạn lưu trú + checklist về nước/chuyển nhà + gợi ý bán đồ

Nguyên tắc: chỉ đưa thông tin có nguồn, ghi ngày rà soát; chỗ nào chỉ có nguồn thứ cấp thì nói rõ; không hứa "đậu/rớt".
Khi quy định đổi: sửa REVIEWED + các khối dữ liệu bên dưới rồi deploy.
"""
from __future__ import annotations

REVIEWED = "14/11/2026"

CSS = """<style>
.vz{--fg:#0a0a0a;--mut:#737373;--bd:#e5e5e5;--bg2:#f5f5f5;--ac:#2563eb;--ok:#16a34a;--wn:#d97706;--no:#dc2626;color:var(--fg);letter-spacing:-.005em}
.vz h1{font-size:1.75rem;line-height:1.2;letter-spacing:-.025em;font-weight:700;margin:.4rem 0 .5rem}
.vz h2{font-size:1.05rem;letter-spacing:-.01em;font-weight:650;margin:2rem 0 .75rem}
.vz .lead{color:var(--mut);font-size:1rem;line-height:1.6;margin:0 0 1rem}
.vz .info{border:1px solid var(--bd);border-radius:10px;background:#fff;margin:0 0 1.25rem;font-size:.82rem;color:var(--mut)}
.vz .info summary{cursor:pointer;padding:.55rem .8rem;list-style:none;display:flex;gap:.5rem;align-items:center}
.vz .info summary::-webkit-details-marker{display:none}.vz .info summary::after{content:"Xem thêm";margin-left:auto;color:var(--ac);font-weight:600}
.vz .info[open] summary::after{content:"Thu gọn"}
.vz .info p{margin:0;padding:0 .8rem .7rem;line-height:1.6}
.vz .card{background:#fff;border:1px solid var(--bd);border-radius:14px;padding:4px 20px 20px;margin:0 0 1rem}
.vz .sec-t{font-size:.72rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--mut);margin:1.4rem 0 .1rem;padding-top:1.1rem;border-top:1px solid var(--bg2)}
.vz .sec-t:first-child{border-top:0;padding-top:.9rem;margin-top:.2rem}
.vz label{display:block;font-weight:600;font-size:.88rem;margin:1rem 0 .4rem}
.vz label.chk{display:flex;gap:.6rem;align-items:flex-start;font-weight:500;line-height:1.45;margin:.7rem 0;cursor:pointer}
.vz label.chk input{margin-top:.2rem;width:18px;height:18px;accent-color:var(--fg);flex:none}
.vz .note{font-size:.78rem;color:var(--mut);font-weight:400}
.vz select,.vz input[type=number],.vz input[type=date]{width:100%;height:44px;font-size:16px;padding:0 .8rem;border:1px solid var(--bd);border-radius:10px;background:#fff;color:var(--fg);transition:border-color .15s,box-shadow .15s}
.vz select:focus,.vz input:focus{outline:0;border-color:var(--ac);box-shadow:0 0 0 3px rgba(37,99,235,.18)}
.vz .row2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.vz .seg{display:flex;gap:4px;background:var(--bg2);border-radius:10px;padding:4px}
.vz .seg button{flex:1;border:0;background:transparent;border-radius:7px;padding:.5rem .3rem;font:inherit;font-size:.86rem;font-weight:600;color:var(--mut);cursor:pointer;transition:all .15s}
.vz .seg button.on{background:#fff;color:var(--fg);box-shadow:0 0 0 1px var(--bd),0 1px 2px rgba(0,0,0,.06)}
.vz button.go{margin-top:1.4rem;width:100%;height:48px;background:var(--fg);color:#fff;border:0;border-radius:10px;font-size:1rem;font-weight:650;cursor:pointer;transition:opacity .15s}.vz button.go:hover{opacity:.88}
.vz .sumbox{display:flex;gap:12px;align-items:flex-start;font-weight:650;font-size:1.02rem;line-height:1.45;padding:16px 18px;border-radius:14px;margin:1.25rem 0 .5rem;border:1px solid var(--bd);background:#fff}
.vz .sumbox::before{flex:none;width:28px;height:28px;border-radius:50%;display:grid;place-items:center;font-size:.9rem;font-weight:800;color:#fff;content:"i";background:var(--mut)}
.vz .sumbox.ok{border-color:#bbf7d0;background:#f6fef9}.vz .sumbox.ok::before{content:"✓";background:var(--ok)}
.vz .sumbox.wn{border-color:#fde68a;background:#fffdf5}.vz .sumbox.wn::before{content:"!";background:var(--wn)}
.vz .sumbox.no{border-color:#fecaca;background:#fffafa}.vz .sumbox.no::before{content:"✕";background:var(--no)}
.vz .sumbox .big{display:block;margin:0}
.vz .res{list-style:none;padding:0;margin:0 0 .5rem;background:#fff;border:1px solid var(--bd);border-radius:14px;overflow:hidden}
.vz .res li{display:grid;grid-template-columns:22px 1fr;gap:12px;padding:13px 16px;border-top:1px solid var(--bg2);font-size:.9rem;line-height:1.6}
.vz .res li:first-child{border-top:0}
.vz .res li::before{width:22px;height:22px;border-radius:50%;display:grid;place-items:center;font-size:.72rem;font-weight:800;color:#fff;content:"i";background:#a3a3a3;margin-top:1px}
.vz .res li.ok::before{content:"✓";background:var(--ok)}.vz .res li.wn::before{content:"!";background:var(--wn)}.vz .res li.no::before{content:"✕";background:var(--no)}
.vz .res li b{font-weight:650}
.vz .hide{display:none}
.vz .big{font-size:2.4rem;line-height:1.1;font-weight:700;letter-spacing:-.03em;font-variant-numeric:tabular-nums}
.vz .score{position:sticky;top:0;z-index:4;background:rgba(255,255,255,.92);backdrop-filter:blur(8px);border:1px solid var(--bd);border-radius:14px;padding:12px 16px;margin:0 0 1rem;display:grid;grid-template-columns:auto 1fr;gap:4px 14px;align-items:center}
.vz .score .n{font-size:2rem;font-weight:700;letter-spacing:-.03em;font-variant-numeric:tabular-nums;line-height:1}.vz .score .n small{font-size:.9rem;color:var(--mut);font-weight:500}
.vz .score .bar{height:8px;background:var(--bg2);border-radius:99px;overflow:hidden;position:relative}
.vz .score .bar i{display:block;height:100%;background:var(--ac);border-radius:99px;transition:width .25s ease,background .25s}
.vz .score .bar::after{content:"";position:absolute;left:87.5%;top:0;bottom:0;width:2px;background:#fff}
.vz .score .m{grid-column:1/-1;font-size:.84rem;color:var(--mut);line-height:1.5}
.vz .hubgrid{display:grid;gap:12px;grid-template-columns:1fr}
.vz .hub{display:flex;gap:14px;align-items:center;background:#fff;border:1px solid var(--bd);border-radius:14px;padding:16px;color:inherit;text-decoration:none;transition:border-color .15s,transform .15s}
.vz .hub:hover{border-color:#a3a3a3;transform:translateY(-1px);text-decoration:none}
.vz .hub .ic{flex:none;width:44px;height:44px;border-radius:12px;display:grid;place-items:center;font-size:1.3rem;background:var(--bg2)}
.vz .hub b{display:block;font-size:.98rem;font-weight:650;letter-spacing:-.01em}.vz .hub small{display:block;color:var(--mut);font-size:.84rem;line-height:1.5;margin-top:2px}
.vz .hub .go2{margin-left:auto;color:var(--mut);font-size:1.1rem}
.vz .tl{list-style:none;margin:0;padding:0 0 0 14px;border-left:2px solid var(--bd)}
.vz .tl li{position:relative;padding:0 0 18px 18px;line-height:1.65;font-size:.92rem}
.vz .tl li::before{content:"";position:absolute;left:-22px;top:.45rem;width:10px;height:10px;border-radius:50%;background:#fff;border:2px solid var(--fg)}
.vz .tl .dt{display:inline-block;font-size:.72rem;font-weight:700;letter-spacing:.03em;background:var(--bg2);border-radius:6px;padding:1px 7px;margin-right:6px;color:var(--fg)}
.vz .tl .tag{display:inline-block;font-size:.7rem;font-weight:600;border-radius:6px;padding:1px 7px;margin-left:4px;background:#ecfdf5;color:#15803d}.vz .tl .tag.u{background:#fffbeb;color:#b45309}
.vz .src{border:1px solid var(--bd);border-radius:10px;background:#fff;margin:2rem 0 0;font-size:.82rem}
.vz .src summary{cursor:pointer;padding:.65rem .85rem;font-weight:600}
.vz .src ul{margin:0;padding:0 .85rem .75rem 1.9rem;color:var(--mut);line-height:1.7}
.vz details.more{border:1px solid var(--bd);border-radius:12px;background:#fff;margin:.5rem 0;padding:0 14px}
.vz details.more summary{cursor:pointer;padding:12px 0;font-weight:600;font-size:.92rem}
.vz details.more ul{margin:0 0 12px;padding-left:1.2rem;line-height:1.7;font-size:.9rem}.vz details.more li{margin:.35rem 0}
.vz .tips,.vz .ck{line-height:1.75;font-size:.92rem}.vz .ck li{margin:.45rem 0}
.vz .btn2{display:inline-flex;align-items:center;height:40px;background:#fff;color:var(--fg);border:1px solid var(--bd);border-radius:10px;padding:0 14px;font-weight:600;font-size:.88rem;margin:.25rem .35rem .25rem 0;text-decoration:none;transition:border-color .15s}.vz .btn2:hover{border-color:#a3a3a3;text-decoration:none}
.vz .btn2.pri{background:var(--fg);color:#fff;border-color:var(--fg)}
.vz .cta a{display:inline-flex;align-items:center;height:42px;background:var(--fg);color:#fff;border-radius:10px;padding:0 16px;font-weight:600;font-size:.9rem}
.vz .app{display:flex;gap:14px;align-items:center;background:var(--fg);color:#fff;border-radius:14px;padding:16px 18px;margin:1.5rem 0 .75rem}
.vz .app .ic{flex:none;width:48px;height:48px;border-radius:12px;background:#262626;display:grid;place-items:center;font-size:1.5rem}
.vz .app b{display:block;font-size:1rem;font-weight:650;letter-spacing:-.01em}.vz .app small{display:block;color:#a3a3a3;font-size:.84rem;line-height:1.5;margin-top:2px}
.vz .app a.dl{flex:none;margin-left:auto;background:#fff;color:var(--fg);border-radius:10px;padding:.55rem .95rem;font-weight:650;font-size:.88rem;white-space:nowrap;text-decoration:none}.vz .app a.dl:hover{opacity:.9;text-decoration:none}
.vz .reads{list-style:none;margin:0 0 .5rem;padding:0;background:#fff;border:1px solid var(--bd);border-radius:14px;overflow:hidden}
.vz .reads li+li{border-top:1px solid var(--bg2)}
.vz .reads a{display:flex;justify-content:space-between;gap:10px;padding:12px 16px;color:var(--fg);font-size:.9rem;text-decoration:none}.vz .reads a:hover{background:#fafafa;text-decoration:none}.vz .reads a span{color:var(--mut)}
@media(max-width:560px){.vz .app{flex-wrap:wrap}.vz .app a.dl{width:100%;text-align:center}}
@media(min-width:720px){.vz .hubgrid{grid-template-columns:1fr 1fr}.vz .hubgrid .hub:last-child{grid-column:1/-1}}
@media(prefers-reduced-motion:reduce){.vz *{transition:none!important}}
</style>"""

DISCLAIMER = (f"<details class=\"info\"><summary>ℹ️ Chỉ để tham khảo, không phải tư vấn pháp lý · rà soát {REVIEWED}</summary>"
              "<p>Quy định xin vĩnh trú đang được siết lại trong năm 2026 và có thể thay đổi tiếp. Quyết định cuối cùng thuộc Cục Quản lý Xuất nhập cảnh (出入国在留管理庁). "
              "Với hồ sơ thật, hãy hỏi cơ quan hoặc 行政書士 (hành chính thư sĩ) có giấy phép. Mọi phép tính chạy ngay trên máy bạn, <b>không gửi dữ liệu đi đâu</b>.</p></details>")

SOURCES = """<details class="src"><summary>Nguồn tham khảo</summary><ul>
<li><a href="https://www.moj.go.jp/hisho/kouhou/hisho08_00905.html" rel="nofollow noopener" target="_blank">Bộ Tư pháp: họp báo 4/8/2026 về sửa đổi ガイドライン vĩnh trú (nguồn chính thức)</a></li>
<li><a href="https://www.moj.go.jp/isa/" rel="nofollow noopener" target="_blank">出入国在留管理庁 (Cục Quản lý Xuất nhập cảnh) — trang chính thức, nên kiểm tra ガイドライン mới nhất tại đây</a></li>
<li>Báo chí về bản sửa đổi 1/10/2026: <a href="https://www.sakigake.jp/news/article/20261001CO0007/" rel="nofollow noopener" target="_blank">Sakigake/Kyodo</a> (thu nhập trên trung bình hộ Nhật, lương hưu, tiếng Nhật, diện vợ/chồng 5+3)</li>
<li>Nguồn thứ cấp (văn phòng hành chính thư sĩ, chưa phải văn bản chính thức): <a href="https://office-tree.jp/blog/immigration/eizyu-nenshu-suijun-setai-ninzu-kasan-2026/" rel="nofollow noopener" target="_blank">office-tree.jp (thu nhập theo số người)</a>, <a href="https://office-tree.jp/blog/immigration/koudo-senmonshoku-1go-point-simulation/" rel="nofollow noopener" target="_blank">office-tree.jp (điểm 高度人材)</a>, <a href="https://asjas.org/com/JpHrPoint.html" rel="nofollow noopener" target="_blank">asjas.org (bảng điểm)</a>,  <a href="https://office-tree.jp/blog/immigration/permanent-residence-requirements/" rel="nofollow noopener" target="_blank">office-tree.jp</a>, <a href="https://dsg.or.jp/column/other-visas/16479/" rel="nofollow noopener" target="_blank">dsg.or.jp</a></li>
</ul></details>"""

HUB = """<nav class="bc"><a href="/vi/">Trang chủ</a> › Visa & thủ tục</nav>
<div class="vz"><h1>Visa & thủ tục ở Nhật</h1>
<p class="lead">Công cụ miễn phí cho người Việt ở Nhật: kiểm tra vĩnh trú, nhắc hạn lưu trú, và chuẩn bị khi về nước hoặc chuyển nhà.</p>
__DISC__
<div class="hubgrid">
<a class="hub" href="/visa/vinh-tru/"><span class="ic">🏠</span><span><b>Kiểm tra điều kiện vĩnh trú</b><small>Trả lời vài câu, xem đã đủ hay còn thiếu gì theo ガイドライン 2026.</small></span><span class="go2">→</span></a>
<a class="hub" href="/visa/koudo/"><span class="ic">🎓</span><span><b>Tính điểm 高度人材</b><small>70 điểm xin vĩnh trú sau 3 năm, 80 điểm sau 1 năm. Điểm cập nhật ngay khi bạn chọn.</small></span><span class="go2">→</span></a>
<a class="hub" href="/visa/ve-nuoc/"><span class="ic">⏳</span><span><b>Hạn lưu trú, về nước, chuyển nhà</b><small>Đếm ngược ngày hết hạn, nhắc vào Google Calendar, checklist thủ tục và gợi ý bán đồ giá cao.</small></span><span class="go2">→</span></a>
</div>
<h2>Thay đổi chính sách cần biết</h2>
<ul class="tl">
<li><span class="dt">4/8/2026</span>Bộ Tư pháp công bố sửa ガイドライン vĩnh trú: xét thu nhập hộ <b>liên tục trên mức trung bình hộ gia đình Nhật</b>, thêm yếu tố <b>lương hưu dự kiến</b>, siết điều kiện "không thành gánh nặng công".<span class="tag">nguồn chính thức</span></li>
<li><span class="dt">1/10/2026</span>Phần thu nhập có hiệu lực (hồ sơ từ 4/2026 bị áp dụng hồi tố). Theo báo chí: hộ từ 5 người được cộng thêm; lương hưu tương đương <b>30 năm 厚生年金</b>; tiếng Nhật mức <b>B1</b>; diện vợ/chồng nâng lên <b>kết hôn 5 năm + ở 3 năm</b>.<span class="tag u">báo chí, chưa chắc</span> Một số văn phòng nói bản chính thức không có con số yên và không đòi đúng "30 năm".</li>
<li><span class="dt">1/10/2026</span>Phí xin vĩnh trú tăng lên <b>200.000 yên</b> (trước 10.000 yên; hồ sơ nộp đến 30/9 vẫn phí cũ).<span class="tag u">chưa xác nhận trên trang Cục</span></li>
<li><span class="dt">1/4/2027</span>Toàn bộ hướng dẫn mới có hiệu lực. Thời hạn lưu trú "3 năm" không còn được chấp nhận khi xin vĩnh trú, về nguyên tắc cần 5 năm.<span class="tag u">nguồn thứ cấp</span></li>
</ul>
<p class="cta"><a href="https://www.facebook.com/groups/1118827834446963" target="_blank" rel="noopener">👥 Hỏi đáp trong nhóm Facebook "Săn Giá Kaitori Nhật Bản" →</a></p>
__SRC__</div>""".replace("__DISC__", DISCLAIMER).replace("__REV__", REVIEWED).replace("__SRC__", SOURCES)

PR = """<nav class="bc"><a href="/vi/">Trang chủ</a> › <a href="/visa/">Visa & thủ tục</a> › Kiểm tra vĩnh trú</nav>
<div class="vz"><h1>Kiểm tra điều kiện xin vĩnh trú</h1>
<p class="lead">Trả lời vài câu để xem mình <b>có vẻ đủ</b> hay <b>còn thiếu</b> điều kiện nào. Đây là bảng tự kiểm tra, không phải kết quả xét duyệt.</p>
__DISC__
<div class="card">
<div class="sec-t">Tình trạng lưu trú</div>
<label for="st">Tư cách lưu trú hiện tại</label>
<select id="st">
<option value="work">Lao động / Kỹ sư, Nhân văn, Quốc tế (技人国) hoặc visa làm việc khác</option>
<option value="hs70">Nhân tài cao cấp (高度人材) từ 70 điểm</option>
<option value="hs80">Nhân tài cao cấp (高度人材) từ 80 điểm</option>
<option value="spouse">Vợ/chồng của người Nhật hoặc người vĩnh trú</option>
<option value="teiju">Định trú (定住者)</option>
<option value="tokutei1">Đặc định kỹ năng 1 (特定技能1号)</option>
<option value="tokutei2">Đặc định kỹ năng 2 (特定技能2号)</option>
<option value="jisshu">Thực tập kỹ năng / Ikusei shuro</option>
<option value="student">Du học (留学)</option>
<option value="family">Gia đình đi theo (家族滞在)</option>
<option value="other">Khác</option>
</select>
<div class="row2">
<div><label for="yrs">Đã ở Nhật liên tục bao nhiêu năm?</label><input id="yrs" type="number" min="0" max="60" step="0.5" value="6"></div>
<div id="wk"><label for="wyrs">Trong đó bao nhiêu năm có visa làm việc/cư trú? <span class="note">(không tính thực tập, 特定技能1, du học, gia đình đi theo)</span></label><input id="wyrs" type="number" min="0" max="60" step="0.5" value="5"></div>
</div>
<div id="mar" class="hide"><label for="myrs">Đã kết hôn bao nhiêu năm?</label><input id="myrs" type="number" min="0" max="60" step="0.5" value="3"></div>
<label for="per">Thời hạn lưu trú ghi trên thẻ cư trú</label>
<select id="per" class="seg"><option value="5">5 năm</option><option value="3" selected>3 năm</option><option value="1">1 năm trở xuống</option></select>
<div class="sec-t">Thu nhập</div>
<div class="row2">
<div><label for="inc">Thu nhập hộ gia đình/năm (vạn yên, tổng trước thuế)</label><input id="inc" type="number" min="0" step="10" value="400"></div>
<div><label for="hh">Số người trong hộ (cả bản thân)</label><input id="hh" type="number" min="1" max="12" value="1"></div>
</div>
<div class="sec-t">Nghĩa vụ và hồ sơ</div>
<label for="tax">Thuế cư trú, lương hưu, bảo hiểm y tế</label>
<select id="tax" class="seg"><option value="ok">Đúng hạn</option><option value="late">Từng trễ (đã bù)</option><option value="debt">Đang nợ</option></select>
<label for="pen">Lương hưu đang đóng <span class="note">(厚生年金 = nenkin công ty; 国民年金 = tự đóng)</span></label>
<select id="pen" class="seg"><option value="kosei">厚生年金</option><option value="kokumin">国民年金</option><option value="gap">Có khoảng trống</option></select>
<label for="crime">Án hình sự hoặc vi phạm giao thông nghiêm trọng/lặp lại gần đây?</label>
<select id="crime" class="seg"><option value="no">Không</option><option value="yes">Có</option></select>
<label for="gar">Có người bảo lãnh (người Nhật hoặc vĩnh trú, thu nhập ổn định)?</label>
<select id="gar" class="seg"><option value="yes">Có</option><option value="no">Chưa</option></select>
<label for="jp">Trình độ tiếng Nhật</label>
<select id="jp" class="seg"><option value="n2">N2 trở lên</option><option value="n3">N3</option><option value="n4">N4 trở xuống</option></select>
<button class="go" id="go" type="button">Xem kết quả</button>
</div>
<div id="out" aria-live="polite"></div>
<details class="more"><summary>Cách tính (để bạn tự kiểm chứng)</summary>
<ul>
<li><b>Thời gian ở:</b> thường cần liên tục từ 10 năm, trong đó ít nhất 5 năm có visa làm việc hoặc cư trú (thực tập và 特定技能1 không tính). Ngoại lệ: vợ/chồng người Nhật hoặc vĩnh trú (cũ: kết hôn 3 năm + ở 1 năm; mới theo báo chí: 5 năm + 3 năm), 定住者 (5 năm), 高度人材 70/80 điểm (3 năm / 1 năm, duy trì liên tục).</li>
<li><b>Thu nhập:</b> công cụ dùng <u>mức tham khảo thực tế do văn phòng hành chính thư sĩ nêu</u> (không phải số chính thức): 1 người ≥ 300 vạn, 2 người 360–380 vạn, 3 người 420–460 vạn, 4 người 480–540 vạn, mỗi người phụ thuộc thêm khoảng +70 vạn. Từ 1/10/2026 tiêu chuẩn là <b>trên mức trung bình hộ gia đình Nhật theo số người</b> (hộ từ 5 người cộng thêm), và Cục <b>không công bố con số yên cụ thể</b>, nên công cụ chỉ báo "chưa thể kết luận đạt", không bao giờ báo "đủ" về thu nhập.</li>
<li><b>Nghĩa vụ công:</b> nộp trễ hạn gốc bị đánh giá tiêu cực dù đã bù (từ 24/2/2026). Hồ sơ cần thuế cư trú 5 năm, thuế quốc gia, lương hưu và bảo hiểm y tế 2 năm. <i>(nguồn thứ cấp)</i></li>
<li>Vợ/chồng và con của người Nhật hoặc vĩnh trú được miễn điều kiện sinh kế và tư cách hành xử, nhưng vẫn xét thuế/lương hưu/bảo hiểm.</li>
</ul></details>
__SRC__</div>
<script>
(function(){
var $=function(i){return document.getElementById(i)};
function sync(){var s=$("st").value;$("mar").className=s==="spouse"?"":"hide";$("wk").className=(s==="work"||s==="tokutei1"||s==="tokutei2"||s==="jisshu"||s==="student"||s==="family"||s==="other")?"":"hide";}
$("st").addEventListener("change",sync);sync();
function refInc(n){var t={1:[300,300],2:[360,380],3:[420,460],4:[480,540]};if(n<=4)return t[n];var b=t[4];var x=(n-4)*70;return [b[0]+x,b[1]+x];}
function li(c,h){return '<li class="'+c+'"><span>'+h+'</span></li>';}
function run(){
 var s=$("st").value,y=parseFloat($("yrs").value)||0,w=parseFloat($("wyrs").value)||0,m=parseFloat($("myrs").value)||0;
 var pen=$("pen").value,per=$("per").value,inc=parseFloat($("inc").value)||0,hh=parseInt($("hh").value)||1,tax=$("tax").value,crime=$("crime").value,gar=$("gar").value,jp=$("jp").value;
 var out=[],bad=0,warn=0;
 function add(c,h){out.push(li(c,h));if(c==="no")bad++;if(c==="wn")warn++;}
 // 1. thời gian cư trú
 if(s==="spouse"){
  if(m>=5&&y>=3)add("ok","<b>Thời gian:</b> kết hôn "+m+" năm, ở Nhật "+y+" năm. Đạt cả mức cũ (3+1) lẫn mức mới theo báo chí (kết hôn ≥5 năm + ở ≥3 năm).");
  else if(m>=3&&y>=1)add("wn","<b>Thời gian:</b> đạt mức cũ (kết hôn ≥3 năm, ở ≥1 năm) nhưng <u>chưa đạt mức mới</u> theo báo chí (kết hôn ≥5 năm, ở ≥3 năm, áp dụng từ 4/2027). Nên nộp sớm hoặc kiểm tra lại với Cục.");
  else add("no","<b>Thời gian:</b> cần kết hôn ≥3 năm và ở ≥1 năm (mức cũ), mức mới theo báo chí là 5+3. Bạn mới "+m+" năm kết hôn / "+y+" năm ở Nhật.");
 }else if(s==="teiju"){
  if(y>=5)add("ok","<b>Thời gian:</b> 定住者 cần ≥5 năm, bạn có "+y+" năm."); else add("no","<b>Thời gian:</b> 定住者 cần ≥5 năm, còn thiếu khoảng "+(5-y).toFixed(1)+" năm.");
 }else if(s==="hs70"){
  if(y>=3)add("ok","<b>Thời gian:</b> 高度人材 70 điểm cần duy trì liên tục ≥3 năm, bạn có "+y+" năm."); else add("no","<b>Thời gian:</b> 70 điểm cần ≥3 năm, còn thiếu khoảng "+(3-y).toFixed(1)+" năm. Điểm phải duy trì liên tục.");
 }else if(s==="hs80"){
  if(y>=1)add("ok","<b>Thời gian:</b> 高度人材 80 điểm cần duy trì liên tục ≥1 năm, bạn có "+y+" năm."); else add("no","<b>Thời gian:</b> 80 điểm cần ≥1 năm.");
 }else{
  if(y>=10)add("ok","<b>Thời gian ở:</b> "+y+" năm liên tục, đạt mốc 10 năm."); else add("no","<b>Thời gian ở:</b> thường cần ≥10 năm liên tục, bạn mới "+y+" năm (còn khoảng "+(10-y).toFixed(1)+" năm).");
  if(s==="tokutei1"||s==="jisshu"){add("no","<b>Visa làm việc ≥5 năm:</b> thực tập kỹ năng và 特定技能1号 <u>không được tính</u> vào 5 năm này. Cần chuyển sang visa được tính (ví dụ 技人国, 特定技能2号) trước.");}
  else if(s==="student"||s==="family"){add("wn","<b>Visa làm việc ≥5 năm:</b> du học / gia đình đi theo không tính vào 5 năm này. Bạn đã nhập "+w+" năm, hãy chắc chỉ tính phần có visa làm việc/cư trú.");}
  else if(w>=5)add("ok","<b>Visa làm việc/cư trú:</b> "+w+" năm, đạt ≥5 năm."); else add("no","<b>Visa làm việc/cư trú:</b> cần ≥5 năm trong 10 năm, bạn có "+w+" năm.");
 }
 // 2. thời hạn lưu trú
 if(per==="5")add("ok","<b>Thời hạn lưu trú:</b> 5 năm, đạt yêu cầu “dài nhất”.");
 else if(per==="3")add("wn","<b>Thời hạn lưu trú:</b> 3 năm. Theo nguồn thứ cấp vẫn được chấp nhận khi nộp <b>đến hết 31/3/2027</b>; sau đó về nguyên tắc cần 5 năm.");
 else add("no","<b>Thời hạn lưu trú:</b> 1 năm hoặc ngắn hơn thường chưa đủ. Cần thời hạn dài nhất của tư cách hiện tại.");
 // 3. thu nhập
 var exempt=(s==="spouse");
 if(exempt){add("in","<b>Thu nhập:</b> diện vợ/chồng được miễn điều kiện sinh kế độc lập theo hướng dẫn cũ. Bản mới có thể thay đổi, hãy kiểm tra lại.");}
 else{var r=refInc(hh);
  if(inc>=r[1])add("wn","<b>Thu nhập:</b> "+inc+" vạn/năm cho hộ "+hh+" người, đạt mức tham khảo <u>cũ</u> ("+(r[0]===r[1]?r[0]:r[0]+"–"+r[1])+" vạn). Từ 1/10/2026 phải <b>vượt mức trung bình hộ Nhật theo số người</b>, chưa có con số chính thức nên <b>chưa thể kết luận đạt</b>. Mức này thường cao hơn nhiều so với bảng cũ.");
  else if(inc>=r[0])add("no","<b>Thu nhập:</b> "+inc+" vạn nằm trong khoảng mức tham khảo <u>cũ</u> ("+(r[0]===r[1]?r[0]:r[0]+"–"+r[1])+" vạn) cho hộ "+hh+" người, nhiều khả năng <b>chưa đủ</b> theo tiêu chuẩn mới (trên trung bình hộ Nhật).");
  else add("no","<b>Thu nhập:</b> "+inc+" vạn thấp hơn cả mức tham khảo cũ ("+r[0]+" vạn) cho hộ "+hh+" người.");
 }
 if(!exempt){
  if(pen==="kosei")add("wn","<b>Lương hưu dự kiến:</b> đang đóng 厚生年金. Bản mới xét mức lương hưu tương lai, theo báo chí tương đương 30 năm đóng 厚生年金 theo thu nhập hiện tại. Thiếu thì xét tài sản.");
  else add("no","<b>Lương hưu dự kiến:</b> "+(pen==="kokumin"?"国民年金 có mức lương hưu thấp hơn":"có khoảng trống đóng hưu")+", rất bất lợi với tiêu chí lương hưu dự kiến mới (áp dụng từ 4/2027). Cân nhắc tài sản bù đắp và hỏi chuyên gia.");
 }
 // 4. nghĩa vụ công
 if(tax==="ok")add("ok","<b>Thuế, lương hưu, bảo hiểm:</b> đóng đủ đúng hạn. Chuẩn bị chứng từ: thuế cư trú 5 năm, lương hưu và bảo hiểm y tế 2 năm gần nhất.");
 else if(tax==="late")add("wn","<b>Thuế, lương hưu, bảo hiểm:</b> có lần trễ hạn. Từ 24/2/2026 nộp trễ bị đánh giá tiêu cực dù đã bù. Nên hỏi chuyên gia trước khi nộp.");
 else add("no","<b>Thuế, lương hưu, bảo hiểm:</b> đang nợ/bị truy thu là lý do dễ bị từ chối. Hãy xử lý xong và duy trì đóng đúng hạn trước.");
 // 5. hành xử
 if(crime==="yes")add("no","<b>Tư cách hành xử:</b> án hình sự hoặc vi phạm giao thông nghiêm trọng/lặp lại rất bất lợi.");
 else add("ok","<b>Tư cách hành xử:</b> không có vấn đề được nêu.");
 // 6. bảo lãnh
 if(gar==="yes")add("ok","<b>Người bảo lãnh:</b> có. Cần thư bảo lãnh, giấy xác nhận nghề nghiệp, thu nhập 1 năm, phiếu cư trú của người đó.");
 else add("wn","<b>Người bảo lãnh:</b> cần người Nhật hoặc người vĩnh trú có thu nhập ổn định.");
 // 7. tiếng Nhật
 if(jp==="n4")add("wn","<b>Tiếng Nhật:</b> là yếu tố trong đánh giá tổng hợp. Bản mới yêu cầu mức “người dùng ngôn ngữ độc lập” (B1, áp dụng từ 4/2027). Nên có chứng chỉ (JLPT N3 trở lên).");
 else add("ok","<b>Tiếng Nhật:</b> "+(jp==="n2"?"N2 trở lên":"N3")+", thuận lợi.");
 var cls,msg;
 if(bad>0){cls="no";msg="Hiện còn thiếu "+bad+" điều kiện rõ ràng"+(warn?" và "+warn+" mục cần lưu ý":"")+". Xem các mục đỏ bên dưới.";}
 else if(warn>0){cls="wn";msg="Có thể đủ, nhưng còn "+warn+" mục cần kiểm tra kỹ trước khi nộp.";}
 else{cls="ok";msg="Có vẻ đủ các mục cơ bản. Vẫn cần xác nhận với cơ quan hoặc 行政書士.";}
 $("out").innerHTML='<div class="sumbox '+cls+'">'+msg+'</div><ul class="res">'+out.join("")+'</ul>'
  +'<p class="note">Đây là tự kiểm tra theo các tiêu chí công khai, không phải kết quả xét duyệt và không đảm bảo được cấp phép. Phí xin vĩnh trú: xem mục "Thay đổi chính sách" ở <a href="/visa/">trang Visa</a>.</p>'
  +'<p class="cta"><a href="/visa/ve-nuoc/">⏳ Đặt nhắc hạn lưu trú →</a></p>';
 if(!ran){ran=true;$("out").scrollIntoView({behavior:"smooth",block:"start"});}
}
var ran=false;
$("go").addEventListener("click",run);
document.querySelector(".card").addEventListener("change",function(){if(ran)run();});
})();
</script>""".replace("__DISC__", DISCLAIMER).replace("__SRC__", SOURCES)

BACK = """<nav class="bc"><a href="/vi/">Trang chủ</a> › <a href="/visa/">Visa & thủ tục</a> › Hạn lưu trú & về nước</nav>
<div class="vz"><h1>Hạn lưu trú, về nước, chuyển nhà</h1>
<p class="lead">Nhập ngày hết hạn thẻ cư trú để xem còn bao lâu và khi nào nộp được gia hạn. Phần dưới là checklist khi sắp về nước hoặc chuyển nhà, kèm cách bán đồ được giá cao.</p>
__DISC__
<div class="card">
<label for="exp">Ngày hết hạn trên thẻ cư trú (在留期間の満了日)</label>
<input id="exp" type="date">
<p class="note">Ngày được lưu ngay trong trình duyệt của bạn (localStorage), không gửi lên server.</p>
<div id="cd"></div>
</div>
<h2>Gia hạn visa: làm gì và khi nào</h2>
<ul class="tips">
<li>Có thể nộp xin gia hạn (在留期間更新) từ <b>3 tháng trước ngày hết hạn</b> tại Cục Xuất nhập cảnh khu vực. Nên nộp sớm, không để sát ngày.</li>
<li>Nộp đúng hạn thì được ở tiếp trong lúc chờ kết quả (tối đa 2 tháng sau ngày hết hạn). Nếu <b>đã quá hạn</b>, hãy liên hệ Cục Xuất nhập cảnh hoặc 行政書士 ngay.</li>
<li>Chuẩn bị sớm: giấy tờ công ty/trường, giấy nộp thuế (納税証明書, 課税証明書), bằng chứng đóng lương hưu và bảo hiểm y tế. Thuế và bảo hiểm nợ làm gia hạn khó hơn.</li>
</ul>
<h2>Sắp về nước? Checklist tham khảo</h2>
<ol class="tips ck">
<li><b>Báo chuyển đi tại quận/thị xã (転出届)</b> trước khi về, lấy giấy 転出証明書 nếu cần.</li>
<li><b>Lương hưu:</b> người đã đóng đủ điều kiện có thể xin <b>trả lại một lần (脱退一時金)</b> <u>trong vòng 2 năm</u> sau khi rời Nhật. Hỏi Sở Hưu trí (年金事務所) về điều kiện và mức tiền hiện hành.</li>
<li><b>Thuế cư trú (住民税):</b> lập người quản lý thuế (納税管理人) hoặc đóng hết trước khi đi, tránh nợ.</li>
<li><b>Hủy:</b> bảo hiểm y tế quốc dân, điện/gas/nước, internet, điện thoại, tài khoản/thẻ tín dụng, hợp đồng thuê nhà (báo trước theo hợp đồng).</li>
<li><b>Thẻ cư trú:</b> nộp lại ở sân bay khi xuất cảnh nếu không xin tái nhập cảnh.</li>
<li><b>Dọn đồ và bán đồ</b>: xem phần dưới.</li>
</ol>
<p class="note">Danh sách mang tính tổng quát, mỗi địa phương có thể khác. Hãy hỏi quận/thị xã nơi bạn ở.</p>
<h2>📦 Bán đồ trước khi đi: so giá để không bán hớ</h2>
<p>Đồ <b>mới, chưa mở hộp</b> (iPhone, máy game, thẻ Pokémon, máy ảnh...) được các tiệm kaitori trả khác nhau tới hàng nghìn đến hàng vạn yên cho cùng một món. Giá của máy mới thường giảm dần theo thời gian, nên đừng để sát ngày bay mới bán.</p>
<p><a class="btn2 pri" href="/vi/">So giá 9 tiệm kaitori →</a><a class="btn2" href="/c/phone/">iPhone</a><a class="btn2" href="/c/game/">Máy game</a><a class="btn2" href="/c/card/">Thẻ Pokémon</a><a class="btn2" href="/guide/vi/">Mẹo bán kaitori</a></p>
<p class="cta"><a href="https://www.facebook.com/groups/1118827834446963" target="_blank" rel="noopener">👥 Hỏi đáp trong nhóm Facebook "Săn Giá Kaitori Nhật Bản" →</a></p>
__SRC__</div>
<script>
(function(){
var K="ktp_visa_exp",$=function(i){return document.getElementById(i)};
function get(){try{return localStorage.getItem(K)||""}catch(e){return ""}}
function set(v){try{if(v)localStorage.setItem(K,v);else localStorage.removeItem(K)}catch(e){}}
function ymd(d){return d.getFullYear()+("0"+(d.getMonth()+1)).slice(-2)+("0"+d.getDate()).slice(-2)}
function fmt(d){return d.getDate()+"/"+(d.getMonth()+1)+"/"+d.getFullYear()}
function render(){
 var v=$("exp").value,box=$("cd");
 if(!v){box.innerHTML="";return;}
 var p=v.split("-"),exp=new Date(+p[0],+p[1]-1,+p[2]),now=new Date();now.setHours(0,0,0,0);
 var days=Math.round((exp-now)/86400000);
 var open=new Date(exp);open.setMonth(open.getMonth()-3);
 var h="",cls="in";
 if(days<0){cls="no";h='<div class="big">Đã quá hạn '+(-days)+' ngày</div><p>Hãy liên hệ Cục Xuất nhập cảnh hoặc 行政書士 ngay.</p>';}
 else{
  h='<div class="big">Còn '+days+' ngày</div><p>Hết hạn ngày <b>'+fmt(exp)+'</b>.</p>';
  if(now>=open){cls=days<=30?"no":"wn";h+='<p>✅ Đã đến lúc <b>nộp xin gia hạn</b> (mở từ '+fmt(open)+').'+(days<=30?' <b>Còn dưới 1 tháng, nên nộp ngay.</b>':'')+'</p>';}
  else h+='<p>Có thể nộp gia hạn từ ngày <b>'+fmt(open)+'</b> (3 tháng trước hạn).</p>';
 }
 var ev=new Date(open);if(ev<now)ev=now;var ev2=new Date(ev);ev2.setDate(ev2.getDate()+1);
 var cal="https://calendar.google.com/calendar/render?action=TEMPLATE&text="+encodeURIComponent("Nộp gia hạn visa (在留期間更新)")+"&details="+encodeURIComponent("Thẻ cư trú hết hạn "+fmt(exp)+". Chuẩn bị giấy tờ và nộp tại Cục Xuất nhập cảnh. kaitoriprice.com/visa/")+"&dates="+ymd(ev)+"/"+ymd(ev2);
 box.innerHTML='<div class="sumbox '+cls+'">'+h+'</div><p><a class="btn2" href="'+cal+'" target="_blank" rel="noopener">📅 Thêm nhắc vào Google Calendar</a></p>';
}
$("exp").value=get();render();
$("exp").addEventListener("change",function(){set(this.value);render();});
})();
</script>""".replace("__DISC__", DISCLAIMER).replace("__SRC__", SOURCES)

KOUDO = """<nav class="bc"><a href="/vi/">Trang chủ</a> › <a href="/visa/">Visa & thủ tục</a> › Tính điểm 高度人材</nav>
<div class="vz"><h1>Tính điểm Nhân lực trình độ cao</h1>
<p class="lead">Bảng điểm <b>高度専門職1号ロ</b> (diện kỹ sư, nhân văn, quốc tế: phổ biến nhất). Đạt <b>70 điểm</b> được ưu đãi và có thể xin vĩnh trú sau <b>3 năm</b>; đạt <b>80 điểm</b> sau <b>1 năm</b>. Diện 1号イ (nghiên cứu) và 1号ハ (quản lý) có bảng điểm khác, công cụ này chưa gồm.</p>
__DISC__
<div class="score" id="score"><div class="n"><span id="scn">0</span><small> / 70</small></div><div class="bar"><i id="scb" style="width:0"></i></div><div class="m" id="scm"></div></div>
<div class="card">
<div class="sec-t">Cơ bản</div>
<label for="edu">Học vấn cao nhất</label>
<select id="edu"><option value="0">Dưới đại học / bằng 専門士</option><option value="10" selected>Đại học (hoặc cao đẳng, 高度専門士)</option><option value="20">Thạc sĩ hoặc bằng chuyên môn (専門職学位)</option><option value="25">MBA / MOT (chuyên môn quản trị kinh doanh)</option><option value="30">Tiến sĩ</option></select>
<label class="chk"><input type="checkbox" id="multi"> Có từ 2 bằng thạc sĩ/tiến sĩ/chuyên môn ở các lĩnh vực khác nhau (+5)</label>
<div class="row2">
<div><label for="exp">Số năm kinh nghiệm đúng ngành sẽ làm</label><input id="exp" type="number" min="0" max="50" step="0.5" value="5"></div>
<div><label for="age">Tuổi</label><input id="age" type="number" min="18" max="80" value="30"></div>
</div>
<label for="inc">Thu nhập năm dự kiến (vạn yên, gồm thưởng, không gồm tăng ca và các phụ cấp)</label><input id="inc" type="number" min="0" step="10" value="500">
<div class="sec-t">Bằng cấp và tiếng Nhật</div>
<label for="qual">Bằng quốc gia Nhật liên quan công việc / chứng chỉ IT theo thông báo</label>
<select id="qual" class="seg"><option value="0">Không</option><option value="5">1 bằng (+5)</option><option value="10">2 bằng trở lên (+10)</option></select>
<label for="jl">Tiếng Nhật <span class="note">(N1 gồm cả chuyên ngành tiếng Nhật ở đại học nước ngoài)</span></label>
<select id="jl" class="seg"><option value="0">Dưới N2</option><option value="10">N2 (+10)</option><option value="15">N1 (+15)</option></select>
<div class="sec-t">Điểm cộng khác (tích nếu đúng)</div>
<label class="chk"><input type="checkbox" class="bo" data-p="15" data-n="Thành tích nghiên cứu"> Thành tích nghiên cứu: có bằng sáng chế, hoặc 3 bài báo khoa học trở lên (+15)</label>
<label class="chk"><input type="checkbox" class="bo" data-p="10" data-n="Tốt nghiệp ở Nhật" id="jpu"> Tốt nghiệp đại học/sau đại học tại Nhật (+10)</label>
<label class="chk"><input type="checkbox" class="bo" data-p="10" data-n="Công ty thuộc diện hỗ trợ đổi mới"> Công ty đang nhận hỗ trợ đổi mới theo thông báo Bộ Tư pháp (+10)</label>
<label class="chk"><input type="checkbox" class="bo" data-p="10" data-n="Doanh nghiệp vừa và nhỏ loại Ⅰ"> Doanh nghiệp vừa và nhỏ đạt điều kiện theo Luật cơ bản về SME (+10)</label>
<label class="chk"><input type="checkbox" class="bo" data-p="5" data-n="SME chi nghiên cứu >3%"> SME có chi phí nghiên cứu trên 3% doanh thu (+5)</label>
<label class="chk"><input type="checkbox" class="bo" data-p="5" data-n="Bằng/giải thưởng nước ngoài được công nhận"> Bằng/giải thưởng nước ngoài được Bộ Tư pháp công nhận (+5)</label>
<label class="chk"><input type="checkbox" class="bo" data-p="10" data-n="Dự án ngành tăng trưởng của bộ"> Tham gia dự án ngành tăng trưởng tiên tiến do bộ hỗ trợ (+10)</label>
<label class="chk"><input type="checkbox" class="bo" data-p="10" data-n="Đại học nước ngoài xếp hạng cao"> Tốt nghiệp đại học nước ngoài top 300 ở ít nhất 2 bảng QS/THE/ARWU (+10)</label>
<label class="chk"><input type="checkbox" class="bo" data-p="5" data-n="Khóa đào tạo JICA (Innovative Asia)"> Hoàn thành khóa JICA 1 năm trở lên theo Innovative Asia (+5)</label>
</div>
<div id="out" aria-live="polite"></div>
<details class="more" open><summary>Nhớ gì khi dùng điểm để xin vĩnh trú</summary>
<ul>
<li>Điểm phải đạt <b>cả lúc nộp hồ sơ lẫn tại thời điểm 3 năm trước</b> (với 70 điểm) hoặc 1 năm trước (với 80 điểm), tính liên tục. Cần chứng minh bằng hồ sơ cũ.</li>
<li>Thu nhập dự kiến tối thiểu của 1号ロ là <b>300 vạn yên</b>, dưới mức này không đạt dù đủ điểm.</li>
<li>Người từ 40 tuổi trở lên chỉ được điểm thu nhập khi từ 800 vạn trở lên. Điểm tuổi: dưới 30 = 15, 30–34 = 10, 35–39 = 5, từ 40 = 0.</li>
<li>Điểm tiếng Nhật N2 không cộng chung với điểm tốt nghiệp ở Nhật hoặc N1.</li>
<li>Các siết chặt 2026 về thu nhập hộ, lương hưu và tiếng Nhật có thể vẫn áp dụng cho cả diện này. Chưa có xác nhận rõ, hãy hỏi Cục hoặc 行政書士 trước khi nộp.</li>
</ul></details>
<p class="note">Bảng điểm lấy từ các trang tổng hợp của văn phòng hành chính thư sĩ (không phải bảng chính thức) và đối chiếu giữa hai nguồn. Chỗ hai nguồn lệch nhau (thu nhập 800 vạn cho người từ 40 tuổi) công cụ lấy theo nguồn khớp với chú thích của bảng.</p>
__SRC__</div>
<script>
(function(){
var $=function(i){return document.getElementById(i)};
function incPts(inc,age){
 var rows=[[1000,40,200],[900,35,200],[800,30,200],[700,25,39],[600,20,39],[500,15,34],[400,10,29]];
 for(var i=0;i<rows.length;i++){if(inc>=rows[i][0]&&age<=rows[i][2])return rows[i][1];}
 return 0;
}
function run(){
 var edu=parseInt($("edu").value),exp=parseFloat($("exp").value)||0,age=parseInt($("age").value)||0,inc=parseFloat($("inc").value)||0;
 var rows=[],tot=0;
 function add(n,p){rows.push([n,p]);tot+=p;}
 add("Học vấn",edu);
 if($("multi").checked&&edu>=20)add("Có từ 2 bằng sau đại học khác lĩnh vực",5);
 add("Kinh nghiệm "+exp+" năm",exp>=10?20:exp>=7?15:exp>=5?10:exp>=3?5:0);
 add("Tuổi "+age,age<30?15:age<35?10:age<40?5:0);
 add("Thu nhập "+inc+" vạn",incPts(inc,age));
 add("Bằng/chứng chỉ Nhật liên quan",parseInt($("qual").value));
 var jl=parseInt($("jl").value),jpu=$("jpu").checked,jn=0,jnote="";
 if(jl===10&&jpu){jnote=" (N2 không cộng chung với tốt nghiệp ở Nhật)";}else jn=jl;
 add("Tiếng Nhật"+jnote,jn);
 var bs=document.querySelectorAll(".bo");
 for(var i=0;i<bs.length;i++){if(bs[i].checked)add(bs[i].getAttribute("data-n"),parseInt(bs[i].getAttribute("data-p")));}
 var html='<ul class="res">';
 for(var j=0;j<rows.length;j++){html+='<li class="'+(rows[j][1]>0?"ok":"in")+'"><span><b>'+rows[j][1]+' điểm</b> · '+rows[j][0]+'</span></li>';}
 html+='</ul>';
 var cls,msg;
 if(inc<300){cls="no";msg="Tổng "+tot+" điểm, nhưng thu nhập dưới 300 vạn yên nên <b>không đạt</b> 1号ロ dù đủ điểm.";}
 else if(tot>=80){cls="ok";msg="Đạt mức 80. Có thể xin vĩnh trú sau 1 năm nếu duy trì điểm liên tục.";}
 else if(tot>=70){cls="ok";msg="Đạt mức 70. Có thể xin vĩnh trú sau 3 năm nếu duy trì điểm liên tục. Còn "+(80-tot)+" điểm nữa là tới mức 80.";}
 else{cls="wn";msg="Còn thiếu "+(70-tot)+" điểm để đạt 70.";}
 $("scn").textContent=tot;$("scb").style.width=Math.min(100,tot/80*100)+"%";$("scb").style.background=(inc<300)?"#dc2626":tot>=70?"#16a34a":"#2563eb";
 $("scm").innerHTML=msg;
 $("out").innerHTML='<div class="sumbox '+cls+'"><span>Chi tiết từng mục</span></div>'+html+'<p class="note">Kết quả tự tính theo bảng tham khảo, không phải xác nhận của Cục. <a href="/visa/vinh-tru/">Kiểm tra điều kiện vĩnh trú →</a></p>';
}
document.querySelector(".card").addEventListener("input",run);
document.querySelector(".card").addEventListener("change",run);
run();
})();
</script>""".replace("__DISC__", DISCLAIMER).replace("__SRC__", SOURCES)


COMMON_JS = """<script>
(function(){document.querySelectorAll("select.seg").forEach(function(s){
 var w=document.createElement("div");w.className="seg";
 function sync(){Array.prototype.forEach.call(w.children,function(b){b.className=b.dataset.v===s.value?"on":""});}
 Array.prototype.forEach.call(s.options,function(o){var b=document.createElement("button");b.type="button";b.textContent=o.textContent;b.dataset.v=o.value;
  b.addEventListener("click",function(){s.value=o.value;s.dispatchEvent(new Event("change",{bubbles:true}));sync();});w.appendChild(b);});
 s.style.display="none";s.parentNode.insertBefore(w,s.nextSibling);sync();s.addEventListener("change",sync);});})();
</script>"""


APP_URL = "https://apps.apple.com/jp/app/id6762459919"
CN = "https://pdythanhduy.github.io/camnang-viet-nhat/"
CN_TITLES = {
    "permanent-residency-eijuu": "Xin vĩnh trú Nhật (永住): điều kiện, hồ sơ, cách điền đơn",
    "japan-policy-update-2026-foreign-residents": "Cập nhật chính sách Nhật 2026 cho người nước ngoài",
    "visa-fee-increase-2025-2026": "Phí gia hạn / đổi visa / vĩnh trú mới từ 01/10/2026",
    "highly-skilled-professional": "Visa 高度専門職 (Highly Skilled Professional)",
    "residence-card-validity": "Gia hạn thẻ cư trú (在留カード): khi nào làm, làm thế nào",
    "visa-status-overview": "Tổng quan các loại visa ở Nhật",
}


def app_box(slugs) -> str:
    reads = "".join(f'<li><a href="{CN}{sl}/" target="_blank" rel="noopener">{CN_TITLES[sl]}<span>↗</span></a></li>' for sl in slugs)
    return (f'<div class="app"><span class="ic">📱</span><span><b>Cẩm Nang Việt Nhật</b>'
            f'<small>127 hướng dẫn gia hạn visa, vĩnh trú, nenkin, thuế, bảo hiểm, sinh con… cho người Việt ở Nhật. Có nguồn chính thức.</small></span>'
            f'<a class="dl" href="{APP_URL}" target="_blank" rel="noopener">Tải app miễn phí</a></div>'
            f'<h2 style="margin-top:1.25rem">Đọc thêm trong Cẩm Nang</h2><ul class="reads">{reads}</ul>')


def build(page, e, site, updated: str) -> list:
    pages = [
        ("/visa/", "Visa & thủ tục ở Nhật: công cụ miễn phí cho người Việt | Kaitori Price",
         "Kiểm tra điều kiện vĩnh trú, nhắc hạn lưu trú, checklist về nước/chuyển nhà. Có ghi nguồn và ngày rà soát.", HUB),
        ("/visa/vinh-tru/", "Kiểm tra điều kiện xin vĩnh trú Nhật (永住) 2026 | Kaitori Price",
         "Tự kiểm tra bạn đã đủ điều kiện xin vĩnh trú ở Nhật chưa: số năm, visa, thu nhập, thuế, lương hưu, theo ガイドライン mới 2026.", PR),
        ("/visa/koudo/", "Tính điểm Nhân lực trình độ cao 高度人材 (70/80 điểm) | Kaitori Price",
         "Tính điểm 高度専門職1号ロ: học vấn, kinh nghiệm, tuổi, thu nhập, tiếng Nhật, điểm cộng. 70 điểm xin vĩnh trú sau 3 năm, 80 điểm sau 1 năm.", KOUDO),
        ("/visa/ve-nuoc/", "Đếm ngược hạn lưu trú, checklist về nước & bán đồ | Kaitori Price",
         "Nhập ngày hết hạn thẻ cư trú để biết khi nào nộp gia hạn, checklist thủ tục khi về nước/chuyển nhà và cách bán đồ giá cao.", BACK),
    ]
    out = []
    reads = {
        "/visa/": ["permanent-residency-eijuu", "japan-policy-update-2026-foreign-residents", "visa-fee-increase-2025-2026"],
        "/visa/vinh-tru/": ["permanent-residency-eijuu", "japan-policy-update-2026-foreign-residents", "visa-fee-increase-2025-2026"],
        "/visa/koudo/": ["highly-skilled-professional", "permanent-residency-eijuu", "visa-status-overview"],
        "/visa/ve-nuoc/": ["residence-card-validity", "visa-fee-increase-2025-2026", "visa-status-overview"],
    }
    for path, title, desc, body in pages:
        marker = '<details class="src">'
        assert marker in body, path
        body = body.replace(marker, app_box(reads[path]) + marker, 1)
        html = page(title, desc, path, CSS + body + COMMON_JS, [], updated)
        html = html.replace('<html lang="ja">', '<html lang="vi">', 1).replace(
            '<a class="hd-cta" href="/">全商品を比較 →</a>', '<a class="hd-cta" href="/vi/">So giá 9 tiệm →</a>', 1)
        d = site / path.strip("/")
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(html, encoding="utf-8")
        out.append((path, "weekly"))
    return out
