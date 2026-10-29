# Thông tin thiếu, mâu thuẫn và các lựa chọn trong code

Đây là bản tái tạo công thức, **không phải code gốc của tác giả**. Có 9 thuật toán chạy được; GA-IFWCOM và SCA-FPCOM chưa triển khai vì thiếu toàn văn/công thức từ hai bài tham khảo. Không thay chúng bằng một biến thể PFCM.

Bài chính: [DOI 10.1016/j.jestch.2023.101525](https://doi.org/10.1016/j.jestch.2023.101525). Trang dưới đây tính theo 13 trang PDF. [Bản bài đã đánh dấu màu và đánh giá](../output/pdf/DP-GA-PFCM-danh-dau-va-danh-gia-tai-tao.pdf) chứa các vị trí R01–R27.

## Những chỉ số đánh giá cần phân biệt

| Chỉ số | Bài cung cấp | Code dùng | Điều chưa xác nhận |
|---|---|---|---|
| Accuracy | Eq.(17), trang 5; Table 6,11 | **Purity**: tổng số điểm thuộc lớp lớn nhất trong từng cụm / N | Thuật ngữ “accuracy” dễ bị hiểu thành ánh xạ nhãn một-một; code còn xuất accuracy_hungarian riêng, không thay purity bằng nó. |
| ARI | Eq.(18), Table 7,12 | adjusted_rand_score của scikit-learn | Thiếu code đánh giá gốc và nhãn dự đoán của 30 lần chạy. |
| NMI | Eq.(19), Table 8,13 | MI / sqrt(H_true × H_cluster); average_method="geometric" | Không dùng mặc định arithmetic của scikit-learn. |
| SD | Table 15, trang 11 | SD từng dataset trên các lần chạy, **ddof=1** | Bài không giải thích gộp 14 dataset để ra mỗi số trong Table 15, cũng không nêu ddof. Không khẳng định SD này bằng Table 15. |
| Thứ hạng, tổng hạng | Table 6–8,11–13 | Cao hơn tốt hơn; rank 1 tốt nhất; đồng hạng lấy trung bình bằng số chưa làm tròn | Quy tắc tie trong bài thiếu/không nhất quán. Hạng thay đổi khi chỉ chạy 10 dataset hoặc 9 phương pháp. |
| Thời gian | Table 16, trang 11 | perf_counter: toàn bộ fit gồm DPC + optimizer + PFCM; bỏ đọc CSV, scaling, tính metric, ghi tệp | Thiếu phạm vi đo, môi trường đủ chi tiết; không so giây giữa hai máy để kết luận nhanh hơn. |
| Kruskal–Wallis | Table 9 và mô tả Sec.4.3 | Từng dataset × metric trên các phương pháp thực sự chạy | Thiếu dữ liệu thô. Tối thiểu 5 lần/nhóm trong code để bật kiểm định, không phải yêu cầu nêu trong bài. |
| Dunn–Bonferroni | Table 10,14 | Hai phía, tie correction, Bonferroni tất cả cặp trong mỗi dataset × metric | Bài chưa nêu family điều chỉnh chính xác. Chỉ diễn giải hậu kiểm khi omnibus bác bỏ H0; p nhỏ không tự chứng minh thuật toán tốt hơn. |

accuracy_hungarian, observed_clusters, số lần đánh giá fitness, objective và trace là thông tin bổ sung để kiểm tra code; không phải ba chỉ số chất lượng chính của bài. **Objective giữa các chromosome có a,b,w,eta khác nhau không có cùng thang đo.**

## Tham số và chi tiết triển khai phải tự chọn

Các tên trong cột “Code” là khóa của hai profile configs/paper_table5.json và configs/corrected_reference.json. --set KEY=JSON sửa được từng khóa, kể cả khóa lồng nhau.

| ID / vị trí | Bài chưa rõ hoặc mâu thuẫn | Lựa chọn thực thi và cách điều chỉnh |
|---|---|---|
| R01 — trang 4 Step 6; Eq.(6),(11) | Gọi PFCM nhưng dẫn Eq.(6) của FCM; chưa rõ fitness trước/sau bước cập nhật | Cấu hình literal dùng fitness=fcm: J_FCM sau 1 bước PFCM. Cấu hình mặc định dùng fitness=fcm_reference: cùng w tham chiếu 2 để chấm mọi gene sau bước PFCM. Có --fitness pfcm và --fitness sse. Mỗi lựa chọn là giả định riêng. |
| R02 — trang 4, chromosome | Chỉ nói a,b,w,eta >0; không nêu giới hạn | a,b ∈ [0.1,5], w,eta ∈ [1.1,5]. Các số này **tự chọn**, w,eta phải >1 để công thức có nghĩa. Tâm nằm trong min/max từng feature sau scaling, cột hằng có tâm=0. Sửa parameter_bounds.a/b/w/eta. |
| R03 — trang 3 Eq.(9), trang 4 | Không định nghĩa K và thời điểm cập nhật gamma | gamma_scale=1; K ở Eq.9 là hệ số scale, **không lấy số cụm làm K**. gamma_refresh=each_step; thay bằng fixed để cố định gamma từ tâm đầu. |
| R04 — trang 4 Step 5 | Chưa rõ 80 chromosome đều lấy tâm DPC hay tạo đa dạng thế nào | Cá thể đầu giữ đúng tâm DPC và tham số baseline; các cá thể khác jitter Gaussian quanh tâm với seed_jitter=0.05, a/b/w/eta uniform trong bounds; clip về miền hợp lệ. |
| R05 — trang 3–4, GA chứa PFCM | Nêu PFCM chạy 1 iteration, chưa nói ghi tâm cập nhật trở lại chromosome | lamarckian=false: bước PFCM chỉ tính fitness; giữ chromosome để lai/đột biến. lamarckian=true cho biến thể ghi tâm sau bước cập nhật vào gene. |
| R06 — trang 4 Step 7 | Roulette cho loss nhỏ tốt hơn; elitism/replacement thiếu | P chọn ∝ 1/max(loss,1e-12); thay thế thế hệ; elite_count=1; lưu best-so-far kể cả elite_count=0. Đây là lựa chọn triển khai, không do bài xác nhận. |
| R07 — trang 4 Eq.(14)–(16) | Chưa rõ r theo gene hay chromosome, phạm vi 10%, precision 4..20, sửa biên | Một r chung cho cặp lai; khi chromosome trúng mutation thì đổi **một gene** ngẫu nhiên theo Sec.2.3. mutation_range=0.1 × độ rộng miền gene; mutation_precision=10; s ngẫu nhiên ±1, u uniform[0,1]; clip biên. |
| R08 — trang 5–6 Table 2,3,5 | Table 5: mutation=0.1; phần tuning dùng 0.01/0.03 | Mặc định theo Table 5: 0.1. configs/sensitivity_mutation001.json dùng 0.01; --mutation-rate sửa trực tiếp. Crossover=0.8; population=80; generations=100 lấy Table 5. |
| R09 — trang 2–4, stop | Ngưỡng và maximum iteration cho PFCM benchmark không xác định rõ | max_iter=100; dừng theo sai khác objective tuyệt đối ≤ tol=1e-6 hoặc đạt số bước. stop_criterion=centers giữ biến thể cũ; stop_mode=relative là lựa chọn khác. Ngưỡng cụ thể vẫn tự chọn. |
| R10 — trang 3, phân cụm cuối | Thiếu quy tắc biến U/T thành nhãn cứng | hard_labels=membership, argmax U; argmax chọn cụm chỉ số nhỏ nhất khi hòa. Có hard_labels=typicality; K-means vẫn dùng partition cứng. |
| R11 — trang 2 Eq.(2),(3), trang 4 | dc “2%”, hòa rho/score, khoảng cách 0 | dc_quantile=0.02 của tất cả cặp khác chỉ số; rho Gaussian; delta tới điểm **rho lớn hơn nghiêm ngặt**. Các điểm có rho cực đại dùng khoảng cách xa nhất. Top rho×delta, tie theo thứ tự dữ liệu, tâm là vector khác nhau. dc=0 dùng khoảng cách dương nhỏ nhất, dữ liệu toàn trùng dừng nếu K>1. |
| R12 — Eq.(4),(6),(7),(11),(12) | Một số ký hiệu/chỉ số sai hoặc không nhất quán | Sửa mẫu số membership cộng theo cụm; khoảng cách bình phương theo feature; α ở Eq.11 hiểu là a. Dùng dạng chuẩn FCM/PFCM thay vì đọc literal lỗi chỉ số. |
| R13 — Sec.3.1, Eq.(13) | Cột hằng, chia 0, underflow, cụm rỗng thiếu | Cột hằng ->0; float64; EPS=1e-12; log-normalization cho U và T. Khi nhiều tâm trùng điểm, chia đều U; T=1. Tâm có tổng trọng số ≤EPS giữ tâm cũ; K-means reseed cụm rỗng bằng điểm có residual lớn. Không xóa outlier hoặc impute benchmark. |
| R14 — Table 1, Sec.4.1 | Thiếu version/hash/tệp dữ liệu cụ thể | Nguồn, feature_columns, nhãn, SHA256 lưu trong datasets/*/*/metadata.json. Loader xác minh hash data.csv. Iris dùng iris.data; không coi đây là xác nhận đúng biến thể tác giả dùng. |
| R15 — Table 1, Glass | Bài K=7 nhưng UCI có 6 lớp thực | Mặc định k_policy=paper, giữ K=7. --k-policy observed chạy một thí nghiệm khác với K=6; không sửa nhãn để ép khớp. |
| R16 — Sec.4.3.1 | Không nêu tham số/khởi tạo đủ cho các baseline | FCM/PFCM random membership đã chuẩn hóa hàng, lấy tâm theo U^w; a=b=1,w=eta=2; K-means random sample centers, một restart mỗi run. DP-FCM/DP-PFCM dùng cùng DPC, **tất định**, nên SD=0 là có thể xảy ra. Không thêm jitter vào baseline DP để giả lập SD bài. |
| R17 — Tables 6–13 | Có mean 30 lần nhưng thiếu seeds/outputs thô | runs=30; seed gốc=2026. Seed mỗi run phụ thuộc Table 1 order và run; cùng seed giữa phương pháp, không phụ thuộc thứ tự chạy. Lưu toàn bộ labels,U,T,tâm,params,trace,hash và môi trường. |
| R18 — Eq.(17)–(19) | Mã đánh giá gốc không có | Dùng định nghĩa ở bảng chỉ số trên; purity không cần ánh xạ nhãn cụm bằng tên lớp. |
| R19 — Table 15 | Cách gộp SD và thiếu hàng FBI | Xuất SD riêng từng dataset; không sinh số SD giả cho bài. FBI có SD thực tế nếu đủ số run. |
| R20 — Sec.4.3 / Table 9,10,14 | Thiếu normality/raw runs/family/pairing | Kruskal–Wallis + Dunn theo cách ghi ở trên. Cùng seed hỗ trợ đối chiếu nhưng kiểm định này giả định các nhóm độc lập; không coi đây là kiểm định ghép cặp. Chạy quick chỉ kiểm tra pipeline. |
| R21 — Table 6 vs 11, Glass A1 | 0.566 vs 0.066 cho cùng DP-PFCM | reference/paper_metrics.csv giữ **cả hai số đúng như in**; note đánh dấu 0.066, không tự sửa bảng gốc. |
| R22 — Tables 6,11–13, rank | Có tie sau làm tròn nhưng ranks khác nhau hoặc không nhất quán | Code rank trung bình bằng mean chưa làm tròn; giữ rank_reported ở reference riêng. Không ép tổng hạng khớp bài. |
| R23 — trang 8, A6/A7 và refs[14],[28] | Hai số tham khảo bị đảo; bài chính không đưa đầy đủ thuật toán ordered means | A6 là GA-IFWCOM: DOI 10.1007/s10115-021-01574-4; A7 là SCA-FPCOM: DOI 10.1007/s00500-020-05380-y. Hai file hiện raise NotImplementedError, registry marked unavailable. |
| R24 — Sec.4.2 / Table 16 | Thiếu code/env/phạm vi timer | requirements pin phiên bản; float64, threads=1. Mỗi experiment.json ghi OS, Python, packages, BLAS pools, config và code/data hash; thời gian đo phạm vi đã nêu. |
| R25 — Sec.5, RFM | Thiếu DOI/tệp, 1288 ->1281 không có danh sách dòng | Case study RFM **chưa tái tạo**; phạm vi hiện tại là 14 benchmark công khai và phân chia 10+4 theo bạn. |
| R26 — Fig.5 / Sec.5.1 | Thiếu cách chạy elbow, seeds, SSE từng K | Dùng K Table 1 cho benchmark; không giả lập elbow/RFM. |
| R27 — abstract vs Table 1 | Abstract nói 11, bảng thực nghiệm có 14 | Dữ liệu tải đủ 14. Nhóm chính 10; bốn Pima, Room Occupancy, Rice, Wifi chỉ chạy khi yêu cầu group khong_su_dung hoặc all. |

## Ba optimizer so sánh: lựa chọn tích hợp

- **DP-PSO-PFCM:** inertia tăng tuyến tính 0.4→0.9 theo mô tả trang 5, c1=c2=2, population=80, generations=100. Tự chọn velocity ban đầu uniform ±0.2 độ rộng gene; clamp cùng phạm vi, pso_velocity_fraction=0.2; clip vị trí.
- **DP-SCA-PFCM:** phương trình sine/cosine chuẩn, sca_amplitude=2 giảm tuyến tính về 0; r2∈[0,2π], r3∈[0,2], r4 quyết định sin/cos với xác suất 1/2, ngẫu nhiên theo gene. Không greedy-replace từng cá thể; lưu best-so-far. Bài chính chỉ nêu population/generations, thiếu integration chi tiết.
- **DP-FBI-PFCM:** hai đội A,B khởi tạo từ cùng quần thể DPC; A1/A2/B1/B2, cập nhật greedy và clip biên. Dùng 80 cá thể **mỗi đội**; bài chính không nói cách đếm hai đội. Cập nhật đồng thời trong mỗi substep, chọn peer khác cá thể hiện tại. A2 thực hiện khi còn độ phân tán fitness, thay gene với mask rand<rand; loss tốt có xác suất ít relocate. Số fitness evaluations **khác** GA/PSO/SCA; xuất riêng để nhận ra ngân sách không ngang nhau.
- Cả ba tối ưu **cùng chromosome, fitness, một bước PFCM và PFCM cuối** như GA nhằm kiểm soát sự khác biệt optimizer. Đây là giả định tích hợp có công bố, không chứng minh trùng code tác giả.

FBI dùng cấu trúc của [Chou & Nguyen 2020](https://doi.org/10.1016/j.asoc.2020.106339); công thức bản FBI gốc được đối chiếu với mục “Overview (FBI and SMA)”, Eq.(1)–(6) của [Qiu et al. 2024](https://doi.org/10.1038/s41598-024-59064-w). **Không thêm thành phần SMA**. SCA: [Mirjalili 2016](https://doi.org/10.1016/j.knosys.2015.12.022).

Hai baseline ngoài bài chính hiện chưa thể viết trung thực từ phần abstract: cần đầy đủ objective, membership/typicality/intuitionistic, Huber M-estimator, OWA/order weights, feature weights, cập nhật tâm, bounds và cấu hình optimizer. Trang [GA-IFWCOM](https://link.springer.com/article/10.1007/s10115-021-01574-4) và [SCA-FPCOM](https://link.springer.com/article/10.1007/s00500-020-05380-y) chỉ hiển thị preview subscription trong lượt tra cứu này.

## DPC trên dataset lớn và đánh giá riêng

N≤5000: dc tính chính xác bằng tất cả cặp; toàn bộ 10 dataset chính đi nhánh này. Room Occupancy có 20.560 mẫu: mặc định dc lấy quantile từ 200.000 cặp với seed=0 riêng; **rho và delta vẫn tính trên toàn bộ N**, theo block 512 để không lưu ma trận N×N. Đây là thay đổi tính toán **ngoài mô tả bài**, có ghi dc_mode trong artifact. Muốn dc chính xác toàn bộ dùng --set dc_exact_limit=25000; riêng mảng khoảng cách cặp của Room Occupancy đã cần khoảng 1.69 GB RAM.

Room Occupancy dùng 5 sensor numeric, bài ghi 7 features nhưng không rõ mã hóa; ID, date, label không vào X. Nhóm khong_su_dung không tham gia lệnh chạy mặc định. Không điều chỉnh tham số bằng nhãn bốn bộ này rồi vẫn gọi chúng là đánh giá riêng.

## Cập nhật mô hình và báo cáo 16/10/2026

Fitness tham chiếu có thang đo chung giữa các gene dù w vẫn ảnh hưởng bước PFCM. Đây là hiệu chỉnh chẩn đoán, chưa chứng minh là objective tác giả. Cấu hình cũ literal FCM được giữ riêng. Cả hai profile hiện dừng PFCM theo thay đổi objective như Step 13; validation loại NaN/Infinity. Báo cáo trực quan, hai bộ cao/thấp theo K-means và cách chạy được mô tả trong README_VISUAL.md. Artifact trước ngày sửa phản ánh mã cũ, không trộn với lượt mới.

## Cách chạy kiểm tra độ nhạy

Từ thư mục dự án, thay python bằng code\.venv\Scripts\python.exe nếu dùng môi trường đã tạo:

    python code/purple_main_model/run.py --datasets iris --config code/configs/paper_table5.json
    python code/purple_main_model/run.py --datasets iris --config code/configs/sensitivity_fitness_pfcm.json
    python code/purple_main_model/run.py --datasets iris --config code/configs/sensitivity_fitness_sse.json
    python code/purple_main_model/run.py --datasets iris --config code/configs/sensitivity_mutation001.json
    python code/purple_main_model/run.py --datasets iris --set gamma_refresh='"fixed"'
    python code/purple_main_model/run.py --datasets iris --set lamarckian=true

PowerShell xử lý quoting khác giữa phiên bản. Nếu --set chuỗi không tiện, sửa JSON cấu hình rồi truyền --config; các tùy chọn --fitness và --mutation-rate không cần quote JSON.

Không chọn profile có Accuracy lớn nhất rồi gọi đó là code gốc. Đặc biệt J_FCM với w biến thiên có thể giảm vì membership được lũy thừa lớn hơn, và J_PFCM với a/b biến thiên có thể giảm do thang trọng số; không đồng nghĩa phân cụm tốt hơn. Trace, params tối ưu và observed_clusters cho phép kiểm tra tâm nhập cụm hoặc nghiệm sát biên.

## Khả năng tái tạo

Đánh giá thông tin của bài ở bước trước là **65/100**, là điểm hoàn chỉnh tài liệu, không phải xác suất thống kê. Viết được code chạy và kiểm tra công thức không làm các thông tin còn thiếu trở nên xác định. Hiện chưa thể khẳng định tái tạo chính xác các mean, SD, ranks và thời gian công bố; kết quả chạy thật phải đọc cùng các giả định trên.
