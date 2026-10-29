> Các con số bên dưới là artifact cũ, chạy trước 16/10/2026 bằng fitness FCM literal và điều kiện dừng theo tâm. Dashboard mới lưu kết quả riêng. Mã cũ đã lưu ở output/code/before_fix_2026-10-10.zip.

# Phạm vi kiểm tra và kết quả tái tạo thực tế

Code chạy được **9/11 phương pháp**. GA-IFWCOM và SCA-FPCOM chưa triển khai; không thay bằng thuật toán khác. Đã đối chiếu công thức và chạy dữ liệu thật, nhưng **chưa tái tạo được kết quả công bố**.

## Đã kiểm tra

- 14 kiểm tra trong tests/test_reproduction.py đã đạt: đáp án số của U/T/PFCM, purity khác Hungarian, NMI hình học, DPC nhỏ và tie, seed lặp lại, finite output, membership tổng 1, fitness variants, gamma fixed, Dunn với đáp án biết trước, dữ liệu 10+4, lỗi baseline thiếu nguồn.
- Chạy nhanh: **180 lượt fit** = 9 phương pháp × 10 dataset chính × 2 lần; population=12, generations=8, PFCM tối đa 100. Đây là smoke test, không phải mean 30 lần của bài.
- Iris ngân sách Table 5: **270 lượt fit** = 9 phương pháp × 30 lần; population=80, generations=100. Cấu hình bổ sung vẫn là các giả định trong ASSUMPTIONS.md.
- tools/verify_artifacts.py đã tính lại metrics từ labels của 450 lượt fit chính ở hai thí nghiệm; khớp CSV, seed, code/data hash, số lượt và 504 ô tham khảo.
- Đã kiểm tra cú pháp các module, trạng thái từng runner và pip check: không có dependency lỗi.
- 10 dataset chính dùng dc chính xác. 4 dataset đánh giá riêng được kiểm tra parser/scaling/schema; chưa chạy mô hình trên bốn bộ này trong các bảng kết quả dưới đây.

## Iris: 30 lần, mean thực tế so với bài

Mỗi số dưới đây lấy trực tiếp summary.csv và reference/paper_metrics.csv. Ba chỉ số đều trên [0,1] trong bảng này. ± là sample SD ddof=1.

| Phương pháp | Accuracy / purity ± SD | ARI ± SD | NMI ± SD | Cụm thực / K |
|---|---:|---:|---:|---:|
| K-means | 0.8487 ± 0.0828 | 0.6653 ± 0.1077 | 0.7112 ± 0.0560 | 3–3 / 3 |
| FCM | 0.8933 ± 0.0000 | 0.7287 ± 0.0000 | 0.7433 ± 0.0000 | 3–3 / 3 |
| PFCM | 0.9067 ± 0.0000 | 0.7560 ± 0.0000 | 0.7550 ± 0.0000 | 3–3 / 3 |
| DP-FCM | 0.8933 ± 0.0000 | 0.7287 ± 0.0000 | 0.7433 ± 0.0000 | 3–3 / 3 |
| DP-PFCM | 0.6667 ± 0.0000 | 0.5227 ± 0.0000 | 0.6653 ± 0.0000 | 3–3 / 3 |
| DP-GA-PFCM | 0.7156 ± 0.0982 | 0.5102 ± 0.1258 | 0.5928 ± 0.1146 | 2–3 / 3 |
| DP-PSO-PFCM | 0.9082 ± 0.0155 | 0.7616 ± 0.0336 | 0.7700 ± 0.0194 | 3–3 / 3 |
| DP-SCA-PFCM | 0.8916 ± 0.0473 | 0.7379 ± 0.0542 | 0.7599 ± 0.0319 | 2–3 / 3 |
| DP-FBI-PFCM | 0.9051 ± 0.0156 | 0.7547 ± 0.0338 | 0.7634 ± 0.0225 | 3–3 / 3 |

### Đối chiếu riêng mô hình chính

| Chỉ số | Bài công bố | Mean tái tạo | Δ |
|---|---:|---:|---:|
| accuracy_purity | 0.9140 | 0.7156 | -0.1984 |
| ari | 0.7740 | 0.5102 | -0.2638 |
| nmi | 0.7750 | 0.5928 | -0.1822 |

Trong 30 lần của GA, median w tối ưu là **5.0000** (giới hạn trên tự chọn=5), có **17/30** lần nhãn cứng chỉ có 2 cụm. Đây là dấu hiệu nghiệm gần biên/nhập cụm cần xem xét. Nó phù hợp với rủi ro fitness J_FCM thay đổi thang đo khi tối ưu w, nhưng chưa chứng minh một nguyên nhân duy nhất cho chênh lệch.

## Kiểm tra các cách hiểu fitness

Cùng seeds của 5 lần đầu, cùng population=80 và generations=100. J_FCM phía dưới lấy đúng 5 lần đầu của thí nghiệm 30 lần; hai biến thể chạy 5 lần riêng. Không chọn biến thể theo nhãn để thay cấu hình mặc định.

| Cách hiểu fitness | Mean purity (5 lần) | Mean ARI | Mean NMI |
|---|---:|---:|---:|
| J_FCM Eq.6 | 0.6613 | 0.4254 | 0.5203 |
| J_PFCM Eq.11 | 0.8187 | 0.6306 | 0.6752 |
| SSE tâm gần nhất | 0.6667 | 0.4248 | 0.5879 |

Thay fitness đã làm kết quả đổi đáng kể; chưa biến thể nào ở đây chứng minh khớp code gốc. Vẫn cần xác định đúng bounds, gamma, quần thể và cách cập nhật từ tác giả.

## Giới hạn kết luận

- Chưa chạy đầy đủ 30 lần trên cả 10 dataset cho tất cả phương pháp; lệnh sẵn trong README_REPRODUCTION.md.
- Số tham khảo A6/A7 là số bài chính, không có raw runs để làm SD hoặc kiểm định chung.
- Không dùng thứ hạng của quick để khẳng định phương pháp vượt trội. Tổng rank trên 10 bộ/9 phương pháp khác tổng rank của bài trên 14 bộ/đầy đủ các phương pháp.
- DPC tất định nên DP-FCM và DP-PFCM cho cùng nhãn giữa các lần; không thêm ngẫu nhiên để ép SD khớp Table 15.
- Case study RFM chưa tái tạo vì thiếu tệp chính xác; Room Occupancy có chênh lệch feature và nhánh lấy mẫu dc.
- Màu có trong FILE_GROUPS.html, các report.html và terminal; tài liệu mô tả thiếu thông tin ở ASSUMPTIONS.md.

[Báo cáo 10 dataset chạy nhanh](results/quick_main10/report.html) · [Báo cáo Iris 30 lần](results/paper_iris30/report.html) · [Ghi chú giả định](ASSUMPTIONS.md)
