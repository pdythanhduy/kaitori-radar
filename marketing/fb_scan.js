// Quét bài trong 1 nhóm FB đang mở (sắp xếp "Phù hợp nhất"), lấy nội dung + lượt cảm xúc + bình luận.
// Dùng: mở https://www.facebook.com/groups/<id>/ trong Chrome, dán TOÀN BỘ file này vào javascript_tool,
// gọi lại 3–4 lần (mỗi lần cuộn thêm ~10 màn hình, cộng dồn vào window._pkm), lần cuối đặt window._pkDone = true để in kết quả.
// Không đăng gì, không bấm gì: chỉ đọc.
window._pkm = window._pkm || new Map();
const _grab = () => document.querySelectorAll('div[aria-posinset]').forEach((a) => {
  const m = a.querySelector('div[data-ad-rendering-role=story_message], div[data-ad-preview=message]');
  const txt = (m ? m.innerText : '').replace(/\s+/g, ' ').trim();
  const labs = [...a.querySelectorAll('[aria-label]')].map((x) => x.getAttribute('aria-label'));
  const cm = +(((labs.find((l) => /^Bình luận về bài viết của/.test(l)) || '').match(/(\d[\d.,]*) bình luận/) || [0, '0'])[1]).replace(/[.,]/g, '');
  const re = labs.filter((l) => /^(Thích|Yêu thích|Thương thương|Haha|Wow|Buồn|Phẫn nộ): \d/.test(l))
    .reduce((s, l) => s + +l.match(/: ([\d.,]+)/)[1].replace(/[.,]/g, ''), 0);
  const age = (a.innerText.match(/(\d+ (phút|giờ|ngày))/) || [])[1] || '';
  const key = txt.slice(0, 80) || ('img-' + re + '-' + cm);
  if (!window._pkm.has(key)) window._pkm.set(key, { txt: txt.slice(0, 200), re, cm, age });
});
for (let i = 0; i < 10; i++) { _grab(); window.scrollBy(0, 1600); await new Promise((r) => setTimeout(r, 1100)); }
_grab();
window._pkDone
  ? [...window._pkm.values()].sort((a, b) => (b.re + 2 * b.cm) - (a.re + 2 * a.cm)).slice(0, 40)
      .map((x) => `${x.re}❤ ${x.cm}💬 ${x.age} | ${x.txt || '(chỉ ảnh)'}`).join('\n')
  : 'đã gom ' + window._pkm.size + ' bài';
