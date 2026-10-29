# 🟣 Mô hình chính DP-GA-PFCM

`dp_ga_pfcm.py`: DPC chọn tâm → GA tối ưu tâm và a, b, w, eta → PFCM cuối. GA dùng chọn roulette, lai số thực Eq.14–15 và đột biến Eq.16.

Từ thư mục dự án: `python code/purple_main_model/run.py --profile quick --color always`.

So sánh toàn bộ: `python code/run_compare_all.py --profile quick --color always`.

Ngân sách Table 5: bỏ `--profile quick` (30 lần, 80 cá thể, 100 thế hệ). Đây là tái tạo theo công thức và giả định đã ghi, chưa xác nhận khớp code gốc. Xem [ASSUMPTIONS.md](../ASSUMPTIONS.md).
