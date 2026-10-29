> Cập nhật 16/10/2026: xem [README_VISUAL.md](README_VISUAL.md) để chạy dashboard mới. Những kết quả cũ bên dưới thuộc phiên bản trước khi sửa fitness và điều kiện dừng.

# Code tái tạo DP-GA-PFCM

Mở [FILE_GROUPS.html](FILE_GROUPS.html) để xem **từng file được đánh dấu màu**, và [ASSUMPTIONS.md](ASSUMPTIONS.md) để biết phần bài báo chưa nói rõ, giá trị tự chọn và vị trí trong PDF. Hướng dẫn tải dữ liệu gốc nằm trong [README_DATASETS.md](README_DATASETS.md).

| Màu | Thư mục / file | Nội dung |
|---|---|---|
| 🔵 Xanh | blue_baselines/ | K-means, FCM, PFCM, DP-FCM, DP-PFCM; run.py in chất lượng giai đoạn 1. |
| 🟠 Cam | orange_comparisons/ | DP-PSO-PFCM, DP-SCA-PFCM, DP-FBI-PFCM; run.py so sánh giai đoạn 2 với DP-PFCM và DP-GA-PFCM. |
| 🟣 Tím | purple_main_model/dp_ga_pfcm.py | Mô hình chính của bài: DPC → GA → PFCM; run.py chạy riêng. |
| 🟣 Tím | run_compare_all.py | Chạy và so sánh cả ba nhóm. |

**Đã triển khai 9/11 phương pháp duy nhất trong hai giai đoạn.** ga_ifwcom.py và sca_fpcom.py hiện là giao diện báo thiếu nguồn, chưa có thuật toán. Số tham khảo A6/A7 lấy nguyên Table 11–13, luôn tách khỏi kết quả chạy và không tham gia ranks/kiểm định thực tế. --require-all sẽ dừng nếu cần đủ cả 11. Đây là code tái tạo có giả định, chưa xác nhận khớp code gốc.

## Cài và chạy

Python 3.10–3.12; môi trường đã kiểm tra là Python 3.12 trên máy hiện tại. Từ D:\DA_NCKHphu:

~~~powershell
python -m venv code/.venv
code/.venv/Scripts/python.exe -m pip install -r code/requirements.txt
code/.venv/Scripts/python.exe code/download_datasets.py
~~~

Môi trường code/.venv và đủ 14 dataset đã có trên máy này, có thể chạy ngay:

~~~powershell
# Xem danh sách mô hình và trạng thái triển khai
code/.venv/Scripts/python.exe code/run_compare_all.py --list

# 🔵 Năm phương pháp cơ sở, 10 dataset chính
code/.venv/Scripts/python.exe code/blue_baselines/run.py --profile quick --color always

# 🟠 So sánh đúng nhóm giai đoạn 2
code/.venv/Scripts/python.exe code/orange_comparisons/run.py --profile quick --color always

# 🟣 Chỉ mô hình chính
code/.venv/Scripts/python.exe code/purple_main_model/run.py --profile quick --color always

# 🟣 Toàn bộ chín mô hình chạy được, ba nhóm màu
code/.venv/Scripts/python.exe code/run_compare_all.py --profile quick --color always

# 30 lần, population 80, 100 thế hệ, 10 dataset chính
code/.venv/Scripts/python.exe code/run_compare_all.py --color always

# Chỉ một hoặc vài dataset
code/.venv/Scripts/python.exe code/run_compare_all.py --datasets iris wine --profile quick

# Bốn dataset dành đánh giá riêng; kết quả lưu folder khác
code/.venv/Scripts/python.exe code/run_compare_all.py --group khong_su_dung --profile quick

# Kiểm tra công thức, chỉ số, seed và dữ liệu
code/.venv/Scripts/python.exe code/tests/test_reproduction.py
~~~

Có thể thay code/.venv/Scripts/python.exe bằng python nếu đã cài requirements vào Python đang dùng. Script giải quyết đường dẫn dataset/config theo vị trí code, không phụ thuộc thư mục terminal. Dấu --datasets dùng slug: iris, flame, jain, wine, glass, ecoli, compound, seed, breast_tissue, aggregation; bốn bộ riêng: pima, room_occupancy, rice, wifi.

**quick** = 2 lần, 12 cá thể, 8 thế hệ, PFCM tối đa 100 bước; chỉ kiểm tra chương trình. Mặc định **paper** = 30 lần, 80 cá thể, 100 thế hệ theo Table 5, kèm các giả định đã ghi. Không trộn kết quả quick và paper.

## Điều chỉnh và lưu thí nghiệm

Cấu hình chính: configs/paper_table5.json. Ba cấu hình khác kiểm tra fitness PFCM, SSE và mutation=0.01. Tất cả bounds và quy tắc chưa được bài xác định đều có trong ASSUMPTIONS.md.

~~~powershell
code/.venv/Scripts/python.exe code/purple_main_model/run.py --datasets iris --fitness pfcm
code/.venv/Scripts/python.exe code/purple_main_model/run.py --datasets iris --mutation-rate 0.01
code/.venv/Scripts/python.exe code/run_compare_all.py --datasets glass --k-policy observed --profile quick
code/.venv/Scripts/python.exe code/run_compare_all.py --datasets iris --runs 5 --population 20 --generations 15
~~~

--methods cho phép chỉ chọn vài phương pháp, ví dụ --methods FCM PFCM DP-GA-PFCM. --seed đổi seed gốc; --max-iter đổi bước tinh chỉnh. --set key=JSON sửa chi tiết; config được lưu đúng sau mọi override vào experiment.json. --output chỉ định thư mục trống, code từ chối ghi đè thí nghiệm đã có.

Mỗi lần chạy tạo results/<tên_giai_đoạn_profile_thời_gian>/:

| File | Nội dung |
|---|---|
| report.html | Bảng chất lượng, ba nhóm màu, lọc dataset, biểu đồ tổng rank, chênh lệch với bài. Mở bằng trình duyệt. |
| runs.csv | Seed và metrics từng lần chạy, thời gian, số cụm thực, số lần tính fitness. |
| summary.csv | Mean, sample SD, rank cho từng dataset × phương pháp. |
| rank_sums.csv | Tổng rank trong **đúng danh sách đã chạy**, không cộng số A6/A7 tham khảo. |
| paper_differences.csv | Δ = mean thực tế − mean công bố, chỉ rõ bảng gốc. |
| kruskal_wallis.csv | Omnibus mỗi dataset × metric khi có ≥5 lần/nhóm. |
| dunn_bonferroni.csv | Hậu kiểm tất cả cặp, tie correction, Bonferroni mỗi dataset × metric. |
| experiment.json | Toàn bộ config, source/data hash, môi trường, phạm vi đo thời gian, trạng thái hoàn tất/lỗi. |
| artifacts/<dataset>/<method>/run_NNN/model.npz | Tâm, U, T nếu có, nhãn dự đoán. |
| artifacts/.../details.json | a,b,w,eta, gamma, tâm DPC, chromosome tốt nhất và các trace. |

Accuracy chính là **purity Eq.17**, ARI, NMI hình học; giá trị càng cao càng tốt. accuracy_hungarian xuất riêng để phân biệt cách ánh xạ cụm. Không đưa label hoặc label_original vào X, không dùng nhãn trong optimizer. observed_clusters ít hơn K được giữ nguyên để nhận biết nghiệm nhập cụm, không “sửa” nhãn sau chạy.

MinMax theo feature trên toàn dataset phù hợp thí nghiệm phân cụm của bài. Phân chia 10+4 là lựa chọn của bạn theo **toàn bộ dataset**, không phải chia train/test theo dòng. K của Glass giữ 7; Room Occupancy chỉ có 5 sensor features trong dữ liệu chuẩn bị, khác số 7 của bài. Không tái tạo case study RFM vì thiếu dataset chính xác.

## Kiểm tra thực tế

Kết quả chạy nằm trong results/quick_main10/ (9 mô hình × 10 dataset × 2 lần). Đây là kết quả thật, **không thay mean bằng số bài báo**. Bảng đối chiếu có thể chênh đáng kể; fitness và miền tham số là nguồn bất định lớn. Các lần chạy deterministic của DP-FCM/DP-PFCM có SD=0 do DPC tất định.

Bảng tham khảo reference/paper_metrics.csv giữ 504 mean/rank của Table 6–8,11–13 trên 14 dataset. Số 0.066 Glass/DP-PFCM/Table 11 có note và giữ nguyên; Table 6 là 0.566. Công cụ reference/extract_tables.py dùng bản text trích từ PDF hiện có; không cần công cụ này khi chạy các mô hình.

Màu thống nhất ở tên nhóm, FILE_GROUPS.html, báo cáo và terminal khi --color always. Các file dùng chung thuộc nhóm xám, có mô tả công thức và nguồn. Chi tiết giới hạn tái tạo: [ASSUMPTIONS.md](ASSUMPTIONS.md).
