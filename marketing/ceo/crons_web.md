# Lịch chạy khi Facebook TẠM DỪNG (user 18/11/2026)

User nói: "chỉ mỗi facebook là dừng thôi, còn lại hoạt động phân tích cải thiện web chạy mỗi ngày mỗi giờ".
Đang bật (prompt gốc trong crons.json, chạy theo cron cùng tên):
- 23 8 * * *     radar thị trường
- 33 13 * * *    radar Hồng Kông
- 13 9 * * 1,4   cập nhật Chuyển mạng 1円
- 47 8 * * *     CEO hằng ngày (bỏ phần comment_log/post_log/nhóm FB)
- 47 11,17 * * * săn trend (BỎ bước 2 đọc nhóm FB bằng Chrome)
- 52 9-22 * * *  kiểm tra + cải thiện web mỗi giờ (mới)
Không bật: bình luận, đăng nhóm, bài nhóm lớn, tin hot, Pokémon, trang cá nhân, canh Chrome.
Gia hạn: một lượt chạy một lần 24/11 tạo lại đúng danh sách này.
Facebook: KHÔNG mở Chrome/Facebook cho tới khi user nói tài khoản đã mở lại.

## Cập nhật 24/11/2026
- Thêm (user 22/11): 17 12 * * * PS5 Pro trên X (chỉ đọc); FB khởi động "Thảo Diệp" CHỈ Chrome Browser 1 — 23 10 xin vào nhóm, 7 11,14,17,20,22 bình luận (fb_warmup.md). Lịch FB cũ (Thành Duy) vẫn TẮT.
- 24/11: lịch lặp của CronCreate hết hạn sau 30 ngày (không phải 7) → giữ nguyên các lịch đang chạy, không xoá/tạo lại. Lượt gia hạn kế tiếp: 30/11 7:41 (đối chiếu CronList, tạo lại lịch nào thiếu).
