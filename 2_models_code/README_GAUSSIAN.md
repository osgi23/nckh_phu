# Gaussian có ngoại lai: bảng ARI theo Nc và L

Trường hợp chính: **Nc=2 cụm, L=5 thuộc tính**, với ngoại lai **0%, 5%, 10%, 20%**. Nc/L là tham số tạo dữ liệu; chỉ số chất lượng chính là ARI.

Chạy từ D:\DA_NCKHphu:

    code/.venv/Scripts/python.exe code/run_gaussian_outliers.py --nc 2 --features 5 --runs 25 --jobs 12

Hoặc nhấp đúp CHAY_GAUSSIAN_NC2_L5.cmd trong code. Mỗi lượt tạo một thư mục dưới results/LUU_TRU; mở index.html của lượt đó, hoặc bấm “Lượt mới nhất” trong results/00_XEM_KET_QUA.html. Không trộn số Gaussian với 10 dataset thật.

## Mean, Best và kiểm định

Mỗi cặp Nc/L có 9 dataset: 3 dataset ngẫu nhiên cho mỗi mức cân bằng cụm. Mỗi dataset được giữ nguyên trong 25 lần khởi tạo độc lập của thuật toán. Mọi phương pháp nhận đúng cùng dữ liệu và seed của lần chạy. Các mức ngoại lai dùng cùng dữ liệu gốc và mặt nạ thay thế lồng nhau.

- Mean ARI: trung bình của toàn bộ 9 × 25 = 225 ARI, SD mẫu trên 225 giá trị.
- Best ARI: lấy ARI lớn nhất trong 25 lần của từng dataset; tính mean và SD mẫu trên 9 giá trị cực đại. Best là thống kê benchmark dùng nhãn thật để chọn sau chạy, không phải cách chọn mô hình khi triển khai.
- Wilcoxon: so sánh K-means với DP-GA-PFCM trên 9 cặp mean ARI theo dataset. Kiểm định hai phía, alpha=0.05, hoán vị dấu chính xác, xử lý đồng hạng; làm tròn chênh lệch đến 12 chữ số chỉ trong phép kiểm định. Nếu p<0.05, mean cao hơn của cặp được in đậm và có (s).
- Bốn phép kiểm định tương ứng bốn tỷ lệ ngoại lai được báo cáo riêng, không hiệu chỉnh đa kiểm định; không diễn giải thành kết luận đồng thời cho mọi mức.
- Bảng tất cả 9 phương pháp có cùng Mean/Best, nhưng (s) chỉ đề cập cặp so sánh đã chọn trước K-means / DP-GA-PFCM.

Đoạn mẫu người dùng đưa không định nghĩa cách lấy SD và ba tỷ lệ cân bằng; các định nghĩa trên là lựa chọn rõ ràng của thí nghiệm này. Không sao chép số CGA/NKhybridGA và không coi các thuật toán đó là K-means/DP-GA-PFCM.

## Giả định sinh dữ liệu

Các giá trị sau do thí nghiệm tự chọn, chưa được xác nhận từ bài nguồn của bảng mẫu:

| Thông số | Giá trị |
|---|---|
| Tổng điểm mỗi dataset / mức ngoại lai | 500 |
| Ba mức cân bằng khi Nc=2 | 50/50, 70/30, 90/10 |
| Số dataset mỗi mức cân bằng | 3 |
| Số lần thuật toán / dataset | 25 |
| Gaussian mỗi cụm | Hiệp phương sai I_5, độ lệch chuẩn 1 |
| Khoảng cách hai mean | 4 theo Euclidean, hướng (1,...,1)/sqrt(L) |
| Ngoại lai | Thay thế 0, 25, 50, 100 điểm; tổng vẫn 500 |
| Phân phối ngoại lai | Uniform trong [-8,8]^5, điều kiện cách mọi mean thật ít nhất 4 |
| Cân bằng sau thay thế | Giữ gần tỷ lệ ban đầu, sai số do số điểm nguyên |
| Chuẩn hóa | Min-max từng thuộc tính trên cả Gaussian và ngoại lai |
| K truyền cho thuật toán | K=Nc=2; không đánh giá tự tìm số cụm |

Các điểm ngoại lai có nhãn -1. **ARI, Purity, NMI chỉ tính trên các điểm Gaussian thật**; mô hình vẫn fit trên toàn bộ 500 điểm. Không đánh giá phát hiện ngoại lai vì các phương pháp hiện tại luôn gán cụm cho mọi điểm. RMSE tâm dùng đơn vị dữ liệu gốc sau ghép tâm với mean thật, thấp hơn tốt hơn.

Seed sinh dataset, sinh ngoại lai và seed thuật toán được tách, ghi trong runs.csv. Cùng dataset dùng xuyên suốt 25 lần thuật toán; dữ liệu của 9 dataset khác nhau. Population=80 và generations=100 theo cấu hình hiện tại; fitness tham chiếu có giả định như ASSUMPTIONS.md, chưa xác nhận trùng tác giả. GA-IFWCOM và SCA-FPCOM vẫn chưa triển khai đầy đủ.

## Kết quả và kiểm tra

- nc_l_ari.csv: bảng Nc/L, tỷ lệ ngoại lai, Mean/Best ARI.
- ari_by_dataset.csv: mean, best, run tốt nhất của từng dataset.
- wilcoxon.csv: p-value và đơn vị ghép cặp.
- runs.csv: mỗi lần fit và đường dẫn artifact.
- data/dataset_NNN.npz: dữ liệu gốc, dữ liệu sau nhiễu, nhãn thật, chuẩn hóa.
- artifacts/: nhãn dự đoán, tâm, U/T và nhật ký thuật toán.
- gaussian_protocol.json và experiment.json: toàn bộ giả định, cấu hình, hash mã nguồn.
- degradation_vs_clean.csv: chênh lệch ghép cặp so với mức 0%.

Hình PCA chỉ để hiển thị; toàn bộ thuật toán và chỉ số dùng đủ L=5 thuộc tính. Hình phân cụm lấy dataset đầu và lần chạy đầu, không chọn lần đẹp nhất. Biểu đồ dùng mean ± SD mô tả, không phải khoảng tin cậy.

Lượt kiểm tra nhanh (không dùng để kết luận):

    code/.venv/Scripts/python.exe code/run_gaussian_outliers.py --quick --output tmp/gaussian_smoke

Chỉ thay cặp Nc/L khi cần bằng --nc và --features; mặc định vẫn dùng cặp 2/5 đã yêu cầu. Các tỷ lệ cân bằng khi Nc>2 giữ một cụm 70%/90% và chia đều phần còn lại, đây cũng là lựa chọn bổ sung.

## Nguồn của bảng mẫu và phạm vi so sánh

Nguồn đã đối chiếu: [NK Hybrid Genetic Algorithm for Clustering, Section V-A1 và Table IV](https://arxiv.org/html/2402.03813v1#S5).

Bảng mẫu của nguồn dùng N=800, nhiễu uniform 1%, Gaussian đa biến cắt ngọn với biên cụm không chồng lấn ở các chiều ngoài chiều đầu. Ba mức cân bằng khi Nc=2 tương ứng gần 50/50, 10/90, 60/40. Thí nghiệm hiện tại áp dụng cấu trúc 9 dataset × 25 lần và cách trình bày Mean/Best cho các thuật toán trong dự án; không tái hiện trực tiếp bộ sinh và số công bố của NK hybrid GA.

Các khác biệt chủ động của lượt hiện tại: N=500; Gaussian không cắt ngọn, hiệp phương sai đơn vị và khoảng cách mean bằng 4; mức cân bằng 50/50,70/30,90/10; ngoại lai 0/5/10/20% theo yêu cầu; điểm chính chỉ chấm trên Gaussian thật; K=Nc được cho trước; ngân sách 80 cá thể × 100 thế hệ. Vì thế không so số ARI hiện tại với 0.97 của bảng nguồn để kết luận phương pháp nào tốt hơn giữa hai nghiên cứu.

Các mức cân bằng và cách sinh Gaussian của nguồn được bổ sung ở đây sau khi tra được toàn bài; giả định đã ghi trong gaussian_protocol.json của lượt đang chạy vẫn được giữ nguyên để bảo toàn cấu hình thí nghiệm.

## Lượt đầy đủ đã hoàn tất: Nc=2, L=5

Mở [bảng kết quả](results/LUU_TRU/gaussian_nc2_l5_9data_25runs_2026-10-17/index.html), hoặc mở results/00_XEM_KET_QUA.html và bấm **Gaussian · bảng Nc/L**.

Lượt này đã fit đủ 4 mức ngoại lai × 9 dataset × 25 lần × 9 phương pháp = 8.100 kết quả. Kiểm tra độc lập đã tính lại chỉ số từ toàn bộ nhãn dự đoán, đối chiếu Mean/Best, p-value, seed, checksum dữ liệu và mã nguồn. Giao diện và liên kết của báo cáo đã kiểm tra trong trình duyệt; 18 kiểm thử của dự án đạt.

| Ngoại lai | K-means Mean ARI | K-means Best ARI | DP-GA-PFCM Mean ARI | DP-GA-PFCM Best ARI | p Wilcoxon |
|---|---|---|---|---|---|
| 0% | **0.8543 ± 0.0706 (s)** | 0.8775 ± 0.0482 | 0.6051 ± 0.3588 | 0.6456 ± 0.3764 | 0.0078125 |
| 5% | 0.7909 ± 0.2432 | 0.8719 ± 0.0590 | 0.5799 ± 0.3360 | 0.6569 ± 0.3308 | 0.1640625 |
| 10% | 0.7796 ± 0.2850 | 0.8898 ± 0.0359 | 0.5800 ± 0.3241 | 0.6441 ± 0.3556 | 0.25 |
| 20% | 0.7450 ± 0.3343 | 0.9061 ± 0.0436 | 0.5918 ± 0.3044 | 0.6753 ± 0.2914 | 0.359375 |

K-means có Mean ARI lớn hơn trên cả bốn mức trong cấu hình hiện tại; chênh lệch đạt mức kiểm định 0.05 chỉ ở điều kiện 0% ngoại lai. Các điều kiện khác chưa đủ bằng chứng Wilcoxon để kết luận có khác biệt; không diễn giải p>0.05 thành hai thuật toán tương đương.

Kiểm tra lại:

    code/.venv/Scripts/python.exe code/tools/verify_gaussian_artifacts.py code/results/LUU_TRU/gaussian_nc2_l5_9data_25runs_2026-10-17 --current-sources

Nếu chỉ cần cặp chính cho lần chạy sau, có thể giới hạn phương pháp, giữ nguyên giao thức 9 dataset × 25 lần:

    code/.venv/Scripts/python.exe code/run_gaussian_outliers.py --methods K-means DP-GA-PFCM

Tệp ga_history.csv dùng số lần chạy liên tiếp 1..225 cho mỗi điều kiện: dataset_id = floor((run-1)/25)+1, lần khởi tạo trong dataset = ((run-1) mod 25)+1. Đường dẫn artifact trong runs.csv giữ đầy đủ hai chỉ số này.
