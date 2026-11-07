# Lịch tự động (khôi phục khi mở phiên Claude mới)

Lịch tạo bằng CronCreate chỉ sống trong 1 phiên Claude Code (tắt phiên là mất, tối đa 7 ngày).
Toàn bộ lịch đang chạy được lưu ở `marketing/ceo/crons.json` (cron + prompt đầy đủ, bản mới nhất).

Mở phiên mới trong thư mục kaitori-radar rồi gõ:

    khôi phục lịch tự động từ marketing/ceo/crons.json

Claude sẽ tạo lại từng lịch bằng CronCreate (giờ local, recurring). Khi sửa prompt một lịch, cập nhật luôn file json.
Không gồm các lịch X えにし神社 một lần (②④⑤).
