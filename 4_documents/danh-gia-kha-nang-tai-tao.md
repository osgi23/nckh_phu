# Đánh giá khả năng tái tạo DP-GA-PFCM

**Đánh giá: 65/100 (65%).** Điểm đầy đủ thông tin theo nhận định chuyên gia; không phải xác suất hay mức khớp thực nghiệm. Chưa chạy mô hình.

| Hạng mục | Trọng số | Điểm |
|---|---:|---:|
| Luồng thuật toán và DPC | 20 | 19 |
| Công thức/cấu hình PFCM | 20 | 12 |
| Tối ưu bằng GA | 20 | 10 |
| Dữ liệu và tiền xử lý | 15 | 9 |
| Đánh giá và so sánh | 15 | 12 |
| Code/môi trường/truy vết | 10 | 3 |

Có thể viết bản chạy được với giả định công khai. Chưa bảo đảm khớp số liệu/thứ hạng/p-value/runtime gốc.

## R01 - Hàm fitness của GA chưa xác định nhất quán
- Vị trí: Trang 4, Step 6; đối chiếu Eq. (6),(11)
- Màu: ĐỎ - mâu thuẫn / lỗi ký hiệu cần xác nhận
- Trong bài: Step 6 gọi PFCM nhưng dẫn Eq. (6).
- Thiếu/chưa rõ: Eq. (6) là mục tiêu FCM; mục tiêu PFCM nằm ở Eq. (11). Within-cluster sum of squared errors còn có thể được hiểu là SSE của nhãn cứng. Chưa rõ fitness lấy trước hay sau một bước PFCM.
- Ảnh hưởng: Các cách tính có thể chọn tâm và tham số rất khác nhau.
- Cách xử lý: Xin code/công thức fitness. Nếu chưa có, chạy riêng J_FCM, J_PFCM và SSE; không coi một cách hiểu là bản gốc.

## R02 - Miền tìm kiếm a, b, w và eta bị thiếu
- Vị trí: Trang 4, mô tả nhiễm sắc thể
- Màu: ĐỎ - mâu thuẫn / lỗi ký hiệu cần xác nhận
- Trong bài: Bài chỉ yêu cầu các giá trị lớn hơn 0.
- Thiếu/chưa rõ: Không có bounds hoặc phân phối khởi tạo. Công thức chứa 1/(w-1), 1/(eta-1), nên >0 chưa đủ cho cập nhật PFCM thông thường; w=1 hoặc eta=1 không xác định.
- Ảnh hưởng: Không tái hiện được search space. Nếu dùng J_PFCM mà không kiểm soát thang a,b, GA có thể ưu tiên giảm thang trọng số thay vì cải thiện cụm.
- Cách xử lý: Xin bounds và repair. Ràng buộc w,eta>1 là giả định cần công khai.

## R03 - K và lịch cập nhật gamma chưa được quy định
- Vị trí: Trang 3, Eq. (9); trang 4, đầu cột trái
- Màu: CAM - thiếu chi tiết triển khai
- Trong bài: Eq. (9) dùng gamma_k = K nhân một tỉ số.
- Thiếu/chưa rõ: K không được giải thích hoặc gán giá trị tại đây; không tự đồng nhất với số cụm K ở Table 1. Không rõ gamma tính một lần, mỗi cá thể GA hay mỗi vòng PFCM.
- Ảnh hưởng: Gamma quyết định typicality và ảnh hưởng của điểm ngoại lai.
- Cách xử lý: Xin K, lịch cập nhật gamma và xử lý gamma=0; kiểm tra độ nhạy nếu đặt giả định.

## R04 - Chưa rõ cách tạo 80 cá thể từ tâm DPC
- Vị trí: Trang 4, đoạn khởi tạo và Step 5
- Màu: CAM - thiếu chi tiết triển khai
- Trong bài: Tâm quần thể ban đầu được lấy từ DPC.
- Thiếu/chưa rõ: Không nói sao chép tâm, thêm nhiễu hay trộn tâm ngẫu nhiên. Thiếu biên độ nhiễu, cách sinh tham số và căn chỉnh thứ tự tâm giữa cá thể.
- Ảnh hưởng: Quần thể ban đầu quyết định tính đa dạng; hoán vị tâm có thể làm phép lai tạo tâm trùng.
- Cách xử lý: Công bố công thức sinh cá thể và thứ tự gene; lưu quần thể ban đầu theo seed.

## R05 - Một bước PFCM bên trong GA chưa có trình tự chi tiết
- Vị trí: Trang 3, cuối mục 3.2
- Màu: CAM - thiếu chi tiết triển khai
- Trong bài: PFCM chạy một iteration cho mỗi GA generation.
- Thiếu/chưa rõ: Chưa rõ một bước cho từng chromosome hay cho generation; thứ tự mu,gamma,t,V chưa ghi. Tâm sau PFCM có ghi ngược vào chromosome hay chỉ dùng đánh giá?
- Ảnh hưởng: Có/không ghi ngược tâm tạo hai thuật toán lai khác nhau.
- Cách xử lý: Cần pseudocode cấp cá thể, trạng thái đầu vào/đầu ra và tính xác định khi đánh giá lại cùng cá thể.

## R06 - Roulette wheel thiếu phép chuyển loss thành xác suất
- Vị trí: Trang 4, Step 7
- Màu: CAM - thiếu chi tiết triển khai
- Trong bài: Selection dùng roulette wheel.
- Thiếu/chưa rõ: Không có công thức xác suất cho bài toán tối thiểu hóa, epsilon khi loss=0, elitism, replacement hoặc best-so-far.
- Ảnh hưởng: Dùng trực tiếp loss làm xác suất sẽ ưu tiên nghiệm kém; replacement khác nhau đổi hội tụ.
- Cách xử lý: Xin công thức selection và elitism. Nếu dùng 1/(loss+epsilon), ghi là quyết định của bản tái tạo.

## R07 - Chi tiết operator GA và xử lý biên chưa đủ
- Vị trí: Trang 4, Eq. (14)-(16)
- Màu: CAM - thiếu chi tiết triển khai
- Trong bài: Mutation range 10%; precision k thuộc {4,...,20}.
- Thiếu/chưa rõ: Không chọn precision k cụ thể; range 10% theo bounds hay bước tuyệt đối? Thiếu xác suất theo gene/cá thể, r dùng chung/từng gene, và repair tâm vượt [0,1].
- Ảnh hưởng: Tham số và tọa độ tâm có thang khác nhau; phép đột biến cho hiệu ứng khác nhau.
- Cách xử lý: Xin operator config và repair. Phân biệt mutation range 10% với mutation probability 0.1.

## R08 - Mutation rate không khớp phần tuning
- Vị trí: Trang 5, Table 2; trang 6, Tables 3,5
- Màu: ĐỎ - mâu thuẫn / lỗi ký hiệu cần xác nhận
- Trong bài: Tuning thử 0.01 và 0.03; Table 5 ghi 0.1.
- Thiếu/chưa rõ: 0.1 nằm ngoài hai mức tuning. Từ số in ở Table 3, cột crossover=0.8, mutation=0.01 có trung bình cao nhất.
- Ảnh hưởng: Không biết bảng cuối dùng 0.01,0.03 hay 0.1; 1% và 10% khác đáng kể.
- Cách xử lý: Xin đính chính; chạy 0.01 và 0.1 thành hai config riêng, không tự sửa bài.

## R09 - Ngưỡng dừng và ngân sách PFCM chưa rõ
- Vị trí: Trang 4, Step 13 và Algorithm 1; Table 5
- Màu: CAM - thiếu chi tiết triển khai
- Trong bài: Dừng theo số vòng hoặc accepted threshold.
- Thiếu/chưa rõ: Thiếu epsilon, tuyệt đối/tương đối và mục tiêu để xét hội tụ. Pseudocode chỉ có MAX_ITER. 100 vòng ở Table 5 dành cho metaheuristic, chưa xác nhận riêng PFCM cuối.
- Ảnh hưởng: Ảnh hưởng kết quả và thời gian tính toán.
- Cách xử lý: Tách ga_generations, pfcm_max_iter, tol và tiêu chí hội tụ; xin config gốc.

## R10 - Chưa có quy tắc lấy nhãn cứng
- Vị trí: Trang 4, cuối Algorithm 1
- Màu: CAM - thiếu chi tiết triển khai
- Trong bài: Report L as a set of cluster labels.
- Thiếu/chưa rõ: Không nói argmax(mu), argmax(t), trọng số kết hợp hay tâm gần nhất; thiếu tie rule, cụm rỗng và xử lý điểm có typicality thấp ở mọi cụm.
- Ảnh hưởng: Metric và số khách mỗi cụm đều phụ thuộc rule nhãn.
- Cách xử lý: Xin rule; argmax(mu) chỉ là giả định. Lưu mu,t để kiểm tra các lựa chọn.

## R11 - Cutoff distance 2% chưa đủ xác định dc
- Vị trí: Trang 5, mục 4.2; trang 2, Eq. (2)-(3)
- Màu: CAM - thiếu chi tiết triển khai
- Trong bài: A cutoff distance of 2% is set for DPC.
- Thiếu/chưa rõ: 2% là phân vị khoảng cách cặp, tỉ lệ láng giềng hay 0.02? Thiếu quy ước cặp i<j, xử lý mật độ bằng nhau, điểm trùng và dc=0.
- Ảnh hưởng: dc thay đổi mật độ, thứ tự rho*delta và tâm khởi tạo.
- Cách xử lý: Xin quy tắc. Phân vị 2% khoảng cách cặp là một giả định có thể thử, chưa phải cấu hình đã công bố.

## R12 - Một số công thức có dấu hiệu lỗi chỉ số
- Vị trí: Trang 2, Eq. (4),(6),(7); trang 3, Eq. (12)
- Màu: ĐỎ - mâu thuẫn / lỗi ký hiệu cần xác nhận
- Trong bài: Eq. (7),(12) cộng theo i nhưng tâm vẫn mang k.
- Thiếu/chưa rõ: Đọc đúng ký hiệu in thì mẫu số không đổi theo cụm đang cộng, dẫn membership=1/c khi khoảng cách khác 0. Eq. (6) có cận k=i; Eq. (4) ghi m cột thay vì c cụm; Eq. (10),(11) chưa thống nhất a/alpha.
- Ảnh hưởng: Chép nguyên công thức có thể làm sai thuật toán. Chưa thể suy ra code tác giả cũng sai.
- Cách xử lý: Sửa chỉ số cụm thành l ở mẫu số, membership có c cột; đối chiếu PFCM [10] và xin xác nhận.

## R13 - Tiền xử lý và quy tắc số học chưa đầy đủ
- Vị trí: Trang 3, mục 3.1 và Eq. (8)-(12)
- Màu: CAM - thiếu chi tiết triển khai
- Trong bài: Mỗi thuộc tính được MinMax về [0,1].
- Thiếu/chưa rõ: Thiếu xử lý cột hằng, missing benchmark, ID/ngày tháng và kiểu dữ liệu. Khoảng cách 0, mẫu số 0 và lũy thừa lớn cần quy tắc epsilon, precision, cụm rỗng.
- Ảnh hưởng: Có thể gây NaN/Inf hoặc thay đổi kết quả trên điểm trùng.
- Cách xử lý: Lập schema dữ liệu và xử lý số học; công khai mọi lựa chọn thêm vào.

## R14 - Tệp của 14 benchmark chưa được định danh
- Vị trí: Trang 5, mục 4.1 và Table 1
- Màu: VÀNG - thiếu thông tin đối chiếu thí nghiệm
- Trong bài: Có tên, K, số thuộc tính và số bản ghi.
- Thiếu/chưa rõ: Chỉ có trang chủ UCI; thiếu dataset ID, URL tệp, version, checksum, thứ tự dòng và schema. Flame,Jain,Compound,Aggregation,Room Occupancy cần xác nhận tệp cụ thể.
- Ảnh hưởng: Cùng tên hoặc cùng N,F chưa đủ bảo đảm đúng dữ liệu/cột.
- Cách xử lý: Tạo manifest nguồn/hash/features/labels; chỉ coi là tái hiện dữ liệu khi manifest khớp.

## R15 - Glass K=7 cần giải thích
- Vị trí: Trang 5, Table 1, Glass
- Màu: ĐỎ - mâu thuẫn / lỗi ký hiệu cần xác nhận
- Trong bài: Glass có K=7, F=9, N=214.
- Thiếu/chưa rõ: UCI chính thức mô tả 6 lớp có dữ liệu; nhãn 4 vắng mặt. K=7 có thể là lựa chọn chủ động, nhưng bài không giải thích có dùng max(label) thay số lớp thực hay không.
- Ảnh hưởng: 6 và 7 cụm cho kết quả khác nhau; không tự sửa K để làm đẹp metric.
- Cách xử lý: Chế độ paper giữ k=7; thử k=6 riêng và xin xác nhận. Nguồn đối chiếu: UCI dataset 42.

## R16 - Thiếu cấu hình các baseline
- Vị trí: Trang 6, mục 4.3.1 và Table 5
- Màu: CAM - thiếu chi tiết triển khai
- Trong bài: So sánh K-means, FCM, PFCM, DP-FCM, DP-PFCM.
- Thiếu/chưa rõ: Thiếu n_init/init/tol K-means; w/số vòng FCM; a,b,w,eta,K cho PFCM/DP-PFCM không GA. Table 5 không đủ thông số riêng SCA,FBI,A6,A7.
- Ảnh hưởng: Tái tạo mô hình chính tốt vẫn có thể khác bảng vì baseline khác cấu hình.
- Cách xử lý: Xin mọi config; dùng cùng preprocessing/seed/metric; ghi rõ giới hạn so sánh ngân sách.

## R17 - Không có seed và kết quả thô 30 lần chạy
- Vị trí: Trang 6, mục 4.3.1; trang 8, mục 4.3.2
- Màu: VÀNG - thiếu thông tin đối chiếu thí nghiệm
- Trong bài: Các số là trung bình của 30 lần thực thi.
- Thiếu/chưa rõ: Thiếu seed, nhãn từng run, tâm, tham số tốt nhất, fitness trace và 30 giá trị gốc.
- Ảnh hưởng: Không thể xác nhận khởi tạo, dao động và kiểm định đúng như tác giả.
- Cách xử lý: Công bố 30 seed cố định và per-run CSV/tâm/nhãn/trace; xin raw results.

## R18 - Cách tính Accuracy cần xác nhận implementation
- Vị trí: Trang 5, Eq. (17)-(19)
- Màu: CAM - thiếu chi tiết triển khai
- Trong bài: Accuracy cộng max(a_i) theo cụm.
- Thiếu/chưa rõ: Công thức nghiêng về purity nhưng corresponding true class chưa nêu mapping từng cụm hay một-một. NMI Eq. (19) đã rõ là geometric; thiếu code nên chưa xác minh implementation có đúng công thức.
- Ảnh hưởng: Purity khác Hungarian accuracy; NMI arithmetic khác geometric.
- Cách xử lý: Báo cáo purity theo cách hiểu Eq. (17); thêm Hungarian riêng, ARI chuẩn, NMI geometric. Xin code metric.

## R19 - Table 15 chưa rõ cách tổng hợp SD
- Vị trí: Trang 11, Table 15
- Màu: VÀNG - thiếu thông tin đối chiếu thí nghiệm
- Trong bài: Mỗi thuật toán có một SD cho mỗi metric.
- Thiếu/chưa rõ: Có 14 dataset nhưng không ghi SD từng bộ: trung bình các SD, gộp 420 runs, hay SD của 14 means? Thiếu ddof; bảng không có hàng DP-FBI-PFCM.
- Ảnh hưởng: Không tái tính được 0.012,0.010,0.059 từ bảng trung bình.
- Cách xử lý: Xin raw runs và aggregation; báo cáo SD từng dataset trước.

## R20 - Kiểm định thiếu input và cấu hình
- Vị trí: Trang 6, Kruskal-Wallis; trang 8, Dunn-Bonferroni
- Màu: VÀNG - thiếu thông tin đối chiếu thí nghiệm
- Trong bài: Mức ý nghĩa 5%, Kruskal-Wallis và Dunn-Bonferroni.
- Thiếu/chưa rõ: Thiếu raw runs, tên normality test, library/config, phạm vi family Bonferroni và cách xử lý seed ghép cặp. p-value làm tròn không đủ tái hiện.
- Ảnh hưởng: Không tính lại đầy đủ Tables 9,10,14. Khác biệt thống kê tự nó không chỉ ra hướng tốt hơn.
- Cách xử lý: Lưu per-run, đơn vị mẫu và family hiệu chỉnh; đối chiếu mean/effect size cùng p-value.

## R21 - Glass Accuracy 0.066 mâu thuẫn 0.566
- Vị trí: Trang 8, Table 11 A1; trang 6, Table 6 (5)
- Màu: ĐỎ - mâu thuẫn / lỗi ký hiệu cần xác nhận
- Trong bài: Cùng DP-PFCM: Table 6=0.566; Table 11=0.066.
- Thiếu/chưa rõ: 0.066 còn thấp hơn cận 1/C của purity với các lớp Glass, không phù hợp cách hiểu Eq. (17). Có dấu hiệu lỗi in, chưa có đính chính.
- Ảnh hưởng: Không dùng ô này làm mục tiêu khớp tuyệt đối hoặc tự sửa số liệu bài báo.
- Cách xử lý: Giữ cả hai số với cờ conflict; xin xác nhận và kiểm tra lại hạng A1 nếu đính chính.

## R22 - Xếp hạng khi hòa điểm chưa rõ
- Vị trí: Trang 6, Table 6 Seed; trang 8, Table 11 Jain
- Màu: VÀNG - thiếu thông tin đối chiếu thí nghiệm
- Trong bài: Số in bằng nhau có thể có hạng khác hoặc cùng hạng.
- Thiếu/chưa rõ: Seed FCM/DP-PFCM cùng 0.899 nhưng hạng 2/1; Jain ba số 0.881 cùng hạng 2. Thiếu full precision, tie rule và quy tắc phá hòa.
- Ảnh hưởng: Không tái tính được sum-of-ranks chỉ từ số đã làm tròn.
- Cách xử lý: Xin số chưa làm tròn và rule; xếp hạng full precision, công bố sensitivity.

## R23 - Dẫn nguồn baseline A6,A7 bị đảo
- Vị trí: Trang 8, mục 4.3.2; trang 13, [14],[28]
- Màu: ĐỎ - mâu thuẫn / lỗi ký hiệu cần xác nhận
- Trong bài: GA-IFWCOM dẫn [14]; SCA-FPCOM dẫn [28].
- Thiếu/chưa rõ: Danh mục cho thấy [14] là SCA-FPCOM, [28] là GA-IFWCOM.
- Ảnh hưởng: Có thể lấy nhầm bài nguồn khi viết lại baseline.
- Cách xử lý: Đối chiếu tên bài/thuật toán thay số reference; xin config/code từng baseline.

## R24 - Code, môi trường và đo runtime chưa đủ
- Vị trí: Trang 5, đầu mục 4; trang 11, Table 16
- Màu: VÀNG - thiếu thông tin đối chiếu thí nghiệm
- Trong bài: Python, Windows 10, Intel Core i7, RAM 20 GB.
- Thiếu/chưa rõ: PDF không có URL repo/config, Python/library versions, model CPU hoặc số luồng. Không rõ timer gồm DPC/preprocessing/tuning hay tổng 30 runs.
- Ảnh hưởng: Không so được chính xác runtime/defaults. Không thấy link trong PDF không chứng minh code không tồn tại nơi khác.
- Cách xử lý: Xin repo/commit/requirements/hardware/timer scope; công bố môi trường bản tái tạo.

## R25 - Dữ liệu RFM và cleaning log chưa truy vết được
- Vị trí: Trang 11, mục 5; trang 12, mục 5.1
- Màu: VÀNG - thiếu thông tin đối chiếu thí nghiệm
- Trong bài: Mendeley Data; 1288 khách, còn 1281 sau làm sạch.
- Thiếu/chưa rõ: Thiếu DOI/URL/version, tên tệp, đơn vị Monetary, mốc Recency, ID 7 dòng bị loại. Điều kiện missing/âm áp dụng cho tất cả cột hay RFM?
- Ảnh hưởng: Không bảo đảm cùng 1281 khách và số thành viên 6 cụm.
- Cách xử lý: Xin DOI/checksum/cleaning log; chỉ R,F,M là features, ID giữ ngoài mô hình.

## R26 - Elbow và output case study chưa đủ chi tiết
- Vị trí: Trang 12, mục 5.1 và Table 18
- Màu: CAM - thiếu chi tiết triển khai
- Trong bài: Elbow chọn 6 cụm; bảng cho số khách và mức RFM.
- Thiếu/chưa rõ: Không ghi thuật toán tạo Elbow, mục tiêu trục y, seed/n_init; thiếu tâm số, nhãn khách và a,b,w,eta cuối. Cụm 4/6 cùng Medium chưa đủ nhận diện lại.
- Ảnh hưởng: Có thể dùng k=6, chưa tái hiện đường Elbow và Table 18.
- Cách xử lý: Xin code Elbow và nhãn/tâm. Matching cụm qua tâm vì số hiệu cụm có thể hoán vị.

## R27 - Abstract ghi 11 benchmark, thực nghiệm có 14
- Vị trí: Trang 1, Abstract; trang 5, mục 4.1
- Màu: ĐỎ - mâu thuẫn / lỗi ký hiệu cần xác nhận
- Trong bài: Abstract ghi eleven; Table 1 có 14 bộ.
- Thiếu/chưa rõ: Mâu thuẫn trình bày; ít nghiêm trọng hơn vấn đề fitness/GA.
- Ảnh hưởng: Có thể chọn thiếu Room Occupancy,Rice,Wifi nếu chỉ theo Abstract.
- Cách xử lý: Theo 14 bộ trong thực nghiệm; ghi discrepancy trong báo cáo.

## Nguồn ngoài
- [UCI Glass](https://archive.ics.uci.edu/dataset/42/glass%2Bidentification)
- [NMI API](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.normalized_mutual_info_score.html)

Không thấy URL code trong PDF không chứng minh code không tồn tại ở nơi khác.