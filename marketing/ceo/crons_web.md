# Lịch chạy khi Facebook TẠM DỪNG (user 18/11/2026)

User nói: "chỉ mỗi facebook là dừng thôi, còn lại hoạt động phân tích cải thiện web chạy mỗi ngày mỗi giờ".
Đang bật (prompt gốc trong crons.json, chạy theo cron cùng tên):
- 23 8 * * *     radar thị trường
- 33 13 * * *    radar Hồng Kông
- 13 9 * * 1,4   cập nhật Chuyển mạng 1円
- 47 8 * * *     CEO hằng ngày (bỏ phần comment_log/post_log/nhóm FB)
- 47 11,17 * * * săn trend (BỎ bước 2 đọc nhóm FB bằng Chrome)
- 52 9-22 * * *  kiểm tra + cải thiện web mỗi giờ (mới)
- 11,41 9-23 * * * canh PS5 Pro (user 22/11) — marketing/ps5pro_watch.py, nguồn Goal.com, báo Telegram khi 5 tiệm đổi trạng thái
Không bật: bình luận, đăng nhóm, bài nhóm lớn, tin hot, Pokémon, trang cá nhân, canh Chrome.
Gia hạn: một lượt chạy một lần 24/11 tạo lại đúng danh sách này.
Facebook: KHÔNG mở Chrome/Facebook cho tới khi user nói tài khoản đã mở lại.
