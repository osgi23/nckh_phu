# Đánh giá code tái tạo DP–GA–PFCM — 10/10/2026

**Kết luận: khoảng 65/100 về mức độ tái hiện bài báo.** Code đã có cấu trúc đúng, chạy được và các công thức lõi được kiểm tra; chưa đủ bằng chứng để gọi là tái hiện đúng toàn bộ mô hình và kết quả của tác giả. Sai lệch đáng chú ý nhất nằm ở fitness khi tối ưu fuzzifier, điều kiện dừng PFCM và phạm vi thực nghiệm còn thiếu.

Đây là điểm đánh giá kỹ thuật theo rubric bên dưới, **không phải xác suất thống kê**, cũng không phải tỷ lệ Accuracy của code chia cho Accuracy của bài. Điểm 65/100 ở báo cáo trước đo mức đầy đủ của thông tin bài báo; điểm ở đây đánh giá bản code hiện tại, bằng các tiêu chí khác.

## Phạm vi và bằng chứng

- Code được xem xét: [D:/DA_NCKHphu/code](D:/DA_NCKHphu/code).
- Bài chính: [DOI 10.1016/j.jestch.2023.101525](https://doi.org/10.1016/j.jestch.2023.101525); [PDF tại workspace](D:/DA_NCKHphu/1-s2.0-S2215098623002033-main.pdf).
- Đã đọc DPC, GA, FCM/PFCM, ba optimizer so sánh, loader, metrics, runner và thống kê; đối chiếu Sec.3.2, Eq.(2)–(19), Table 1,5–16.
- Chạy lại 14 kiểm tra có sẵn: tất cả đạt. `pip check`: không có dependency bị hỏng.
- Kiểm tra lại artifact đã lưu: 180 lần chạy quick trên 10 dataset và 270 lần chạy trên Iris. Nhãn/metrics, seed, checksum dữ liệu và hash mã thuật toán khớp. Điều này xác nhận số đã lưu thuộc bản code đang xem; không chứng minh chúng khớp thuật toán gốc.
- Thêm probe độc lập ở [review_probes.py](D:/DA_NCKHphu/output/code_review_2026-10-10/review_probes.py), ghi số liệu vào [evidence.json](D:/DA_NCKHphu/output/code_review_2026-10-10/evidence.json). Probe chỉ đọc dữ liệu, model và cấu hình; không sửa code mô hình.
- Hash thuật toán hiện tại vẫn trùng hash ghi trong thực nghiệm ngày 08/10. Đánh giá này áp dụng cho bản trong `code/`; không xác nhận một bản chỉnh sửa nằm ngoài thư mục này.

## Các phát hiện, theo mức độ ảnh hưởng

### 1. [P1] Fitness có thể giảm mạnh chỉ do tăng w

Vị trí: [common/meta_pfcm.py:46](D:/DA_NCKHphu/code/common/meta_pfcm.py:46), [configs/paper_table5.json:34](D:/DA_NCKHphu/code/configs/paper_table5.json:34).

GA tối ưu cả tâm và `a,b,w,eta`, nhưng fitness mặc định là `sum(u**w * d²)`. Các chromosome có `w` khác nhau đang được so sánh trực tiếp bằng những giá trị loss có thang đo khác nhau. Tăng `w` có thể làm loss giảm mà không cải thiện nhãn phân cụm.

Probe trên Iris, cố định các tâm DPC, chỉ đổi `w` và tính lại U theo công thức:

| w | Loss FCM | Purity | ARI | NMI |
|---:|---:|---:|---:|---:|
| 1,5 | 17,448104 | 0,666667 | 0,449873 | 0,657015 |
| 2 | 12,798375 | 0,666667 | 0,449873 | 0,657015 |
| 3 | 5,085982 | 0,666667 | 0,449873 | 0,657015 |
| 5 | 0,625824 | 0,666667 | 0,449873 | 0,657015 |

Hash nhãn dự đoán ở cả bốn trường hợp giống hệt nhau. Đây là bằng chứng trực tiếp cho tính chất của fitness; probe không có bước thay đổi tâm.

Trong 30 lần chạy GA đã lưu, trung vị `w=5`, sát cận trên; 17/30 lần chỉ có hai cụm nhận nhãn, dù đặt K=3. Những quan sát này phù hợp với mối lo trên, nhưng chưa chứng minh nó là nguyên nhân duy nhất gây sai lệch kết quả.

**Đối chiếu bài:** Sec.3.2, Step 6 gọi PFCM/SSE nhưng dẫn Eq.(6), là objective FCM; objective PFCM nằm ở Eq.(11). Do đó chưa thể khẳng định tác giả thực sự dùng fitness nào. Code bám một cách đọc có cơ sở, nhưng chưa giải quyết mâu thuẫn và vấn đề so sánh loss giữa fuzzifier khác nhau.

**Hướng xử lý:** cần xác nhận objective và cách xử lý tham số biến thiên. Có thể làm thí nghiệm tách riêng giữ `w` cố định để chẩn đoán, ghi rõ là biến thể kiểm tra. Không tự chọn profile có Accuracy tốt nhất rồi gọi đó là mô hình gốc. Đổi sang `fitness=pfcm` cũng chưa tự giải quyết vấn đề vì `a,b,w,eta` vẫn ảnh hưởng thang loss.

### 2. [P2] Điều kiện dừng PFCM lệch mô tả rõ trong bài

Vị trí: [common/numerics.py:108](D:/DA_NCKHphu/code/common/numerics.py:108), [common/numerics.py:113](D:/DA_NCKHphu/code/common/numerics.py:113).

Sec.3.2, Step 13 yêu cầu dừng khi đạt giới hạn lặp hoặc thay đổi hàm mục tiêu đạt ngưỡng. Code hiện dừng theo `max(abs(V_new - V_old)) <= tol`, tức độ dịch tọa độ tâm.

Đây là **sai lệch đã xác nhận so với văn bản bài**, dù dừng theo tâm là một lựa chọn hợp lý trong nhiều triển khai phân cụm khác. `ASSUMPTIONS.md` đã công bố lựa chọn này; việc công bố không làm nó thành điều kiện dừng của bài.

Trong 30 trace Iris, 7 trường hợp thỏa ngưỡng dịch tâm 1e-6 nhưng thay đổi objective giữa hai bước cuối vẫn lớn hơn 1e-6. Bài không công bố giá trị ngưỡng, nên phép so sánh này minh họa hai quy tắc khác nhau, không khẳng định tác giả sử dụng ngưỡng 1e-6.

**Hướng xử lý:** bổ sung chế độ dừng theo thay đổi J cho profile bám Step 13; ghi rõ dùng sai khác tuyệt đối hay tương đối, ngưỡng và giới hạn lặp. Với gamma cập nhật động, cần xác định nhất quán J được so sánh ở mỗi bước.

### 3. [P2] Chưa khớp kết quả công bố của mô hình chính

Nguồn: [summary.csv](D:/DA_NCKHphu/code/results/paper_iris30/summary.csv), Tables 11–13 cột A2.

| Chỉ số, Iris | Bài báo | Code, trung bình 30 lần | Code − bài |
|---|---:|---:|---:|
| Accuracy theo purity | 0,914 | 0,715556 | −0,198444 |
| ARI | 0,774 | 0,510193 | −0,263807 |
| NMI | 0,775 | 0,592750 | −0,182250 |

Các chênh lệch này đủ lớn để chưa công nhận tái hiện kết quả trên Iris. Code còn xếp GA dưới một số baseline và optimizer khác trong thử nghiệm này. Không được suy rộng kết luận đó sang tất cả dataset.

Độ nhạy fitness đã lưu, cùng năm seed đầu trên Iris, population=80 và generations=100:

| Fitness | Purity | ARI | NMI |
|---|---:|---:|---:|
| FCM | 0,6613 | 0,4254 | 0,5203 |
| PFCM | 0,8187 | 0,6306 | 0,6752 |
| SSE tâm gần nhất | 0,6667 | 0,4248 | 0,5879 |

Thay fitness có ảnh hưởng đáng kể, nhưng năm lần chạy chưa đủ để kết luận chọn PFCM là đúng theo tác giả. Đây là thí nghiệm độ nhạy, không phải xác nhận mô hình gốc.

### 4. [P2] Hai phương pháp so sánh chưa được triển khai

Vị trí: [ga_ifwcom.py:8](D:/DA_NCKHphu/code/orange_comparisons/ga_ifwcom.py:8), [sca_fpcom.py:8](D:/DA_NCKHphu/code/orange_comparisons/sca_fpcom.py:8).

Hai file chỉ có `NotImplementedError`, registry đánh dấu unavailable. Vì vậy có 9/11 phương pháp chạy được trong tổng hai giai đoạn; riêng giai đoạn hai có 5/7. Số của hai phương pháp này trong reference là số công bố, không phải kết quả code chạy.

Code xử lý phần thiếu minh bạch, không thay bằng thuật toán khác. Tuy vậy, chưa thể tái tạo bảng so sánh, tổng hạng và hậu kiểm đầy đủ như bài. Cần nguồn thuật toán đầy đủ, triển khai và kiểm tra độc lập trước khi đưa vào benchmark.

### 5. [P2] Một số lựa chọn ảnh hưởng kết quả vẫn chưa được bài xác nhận

| Lựa chọn trong code | Điều chưa xác nhận và ảnh hưởng |
|---|---|
| `gamma_refresh=each_step`, `gamma_scale=1` | Bài không đủ rõ thời điểm cập nhật gamma và hệ số. Giữ nguyên 30 nghiệm GA, chỉ replay PFCM cuối với gamma fixed làm Purity đổi từ 0,7156 xuống 0,7033; ARI 0,5102 xuống 0,4816; NMI 0,5928 xuống 0,5565. Replay không chạy lại GA và không xác định chính sách nào đúng theo tác giả. |
| Miền `a,b=[0.1,5]`, `w,eta=[1.1,5]` | Đây là miền tự đặt, quyết định khả năng tìm kiếm. Nghiệm w sát biên khiến lựa chọn này đặc biệt quan trọng. |
| `seed_jitter=0.05`, roulette nghịch đảo loss, elitism=1, precision=10 | Những chi tiết không đủ xác định trong bài. Công thức lai/đột biến có cơ sở, nhưng các lựa chọn triển khai này chưa được xác nhận. |
| Mutation mặc định 0,1 | Table 5 ghi 0,1; bảng tuning dùng 0,01/0,03. Không đánh dấu 0,1 là lỗi chắc chắn; phải giữ tách các cấu hình để đối chiếu. |
| Room Occupancy có 5 features; bài ghi 7 | Chưa xác nhận phiên bản/feature schema mà tác giả sử dụng. Bộ này thuộc nhóm đánh giá riêng theo lựa chọn của bạn. |
| DPC trên Room dùng lấy mẫu cặp để tính dc | rho/delta vẫn dùng toàn bộ dữ liệu, nhưng dc là xấp xỉ ngoài mô tả bài. Cả 10 dataset chính dùng dc từ toàn bộ cặp. |

Các điểm này đã được ghi trong [ASSUMPTIONS.md](D:/DA_NCKHphu/code/ASSUMPTIONS.md). Chúng là **giả định cần xác nhận**, không phải tất cả đều là lỗi lập trình.

### 6. [P2] Ngân sách optimizer và thực nghiệm chưa đủ để so sánh toàn diện

- Quick 10 dataset hiện có 2 lần chạy, population=12, generations=8: hữu ích để kiểm tra pipeline, chưa thay thế thực nghiệm 30 lần của bài.
- Đã có 30 lần trên Iris với population=80, generations=100; chưa có đối chiếu cùng mức ngân sách đó cho toàn bộ 10 dataset chính.
- Việc giữ 10 bộ chính và 4 bộ đánh giá riêng đúng yêu cầu của bạn. Đây là phạm vi chủ động lựa chọn, không phải lỗi; để tái tạo toàn bộ bảng 14 dataset cần thêm một experiment riêng với đủ 14 bộ.
- FBI dùng hai đội 80 cá thể. Trên Iris, trung bình có 25.733,7 fitness evaluations so với 8.080 của GA/PSO/SCA. Cùng số vòng lặp không có nghĩa cùng số đánh giá. Bài chưa rõ cách đếm hai đội, nên chưa kết luận code FBI sai; cần báo cả ngân sách đánh giá và thời gian.
- Case study khách hàng RFM và cách tổng hợp SD Table 15 chưa tái tạo. Không dùng SD theo từng dataset để tuyên bố khớp SD gộp của bài.

### 7. [P2] Validation cấu hình chấp nhận NaN/Infinity

Vị trí: [common/runner.py:35](D:/DA_NCKHphu/code/common/runner.py:35).

Các kiểm tra chỉ so dấu chưa loại giá trị không hữu hạn cho `tol`, `gamma_scale`, `seed_jitter`, `mutation_range`. Probe cho thấy cả NaN và +Infinity ở bốn khóa này đều qua `validate_config`.

Ví dụ `tol=Infinity` làm PFCM dừng ngay sau một bước và ghi `converged=True`. Đây là lỗi bảo vệ cấu hình có thể tạo kết quả gây hiểu nhầm khi chỉnh tham số. Cấu hình mặc định dùng số hữu hạn nên lỗi này không giải thích chênh lệch Iris đã lưu.

**Hướng xử lý:** kiểm tra hữu hạn, kiểu dữ liệu và miền hợp lệ cho toàn bộ tham số số học trước khi chạy, bao gồm bounds và tham số optimizer; thêm regression check cho cấu hình NaN/Infinity.

## Những phần đã tái hiện tốt

1. Pipeline đúng ý tưởng Sec.3.2: min–max → DPC → GA trên tâm và a/b/w/eta → PFCM cuối.
2. DPC có Gaussian rho, delta tới điểm mật độ lớn hơn và chọn top rho×delta. Có kiểm tra ví dụ nhỏ và tính bất biến theo block.
3. U, T, gamma và cập nhật tâm theo trọng số `a*U^w + b*T^eta` đúng dạng FCM/PFCM chuẩn. Probe bất đối xứng độc lập bằng vòng lặp vô hướng cho sai số tâm lớn nhất 1,11×10^-16, gamma sai số 0. Probe này bổ sung cho test đối xứng sẵn có, không chỉ kiểm tra code tự khớp chính nó.
4. Một bước PFCM để tính fitness trong GA, sau đó PFCM cuối chạy nhiều bước phù hợp mô tả kiến trúc.
5. Accuracy theo Eq.(17) được tách đúng thành purity; Hungarian accuracy được xuất riêng. ARI và NMI dùng geometric normalization theo Eq.(19).
6. Nhãn thật không đi vào optimizer; chỉ dùng sau fit. Dữ liệu có schema và checksum, các lần chạy có seed và trace; toàn bộ dữ liệu chia 10+4 đúng yêu cầu.
7. Có thư mục màu cho ba nhóm, lệnh chạy và báo cáo so sánh; các phương pháp thiếu được đánh dấu rõ.

14 tests đạt chứng minh một số tính chất và ví dụ số học, không bao phủ hết các giả định của bài. Chẳng hạn test optimizer giữ best loss không tăng không đảm bảo loss đó đo chất lượng phân cụm công bằng khi w biến thiên.

## Cách chấm khoảng 65/100

| Tiêu chí | Điểm | Cơ sở |
|---|---:|---|
| Kiến trúc mô hình DPC → GA → PFCM | 20/20 | Đủ các thành phần và thứ tự chính. |
| Công thức và quy trình số học | 17/20 | U/T/V và objective kiểm tra đạt; quy tắc dừng khác Step 13. |
| Fitness, tìm kiếm và tham số bám bài | 8/20 | Fitness mâu thuẫn trong bài và bị thang w chi phối; bounds/gamma/khởi tạo có giả định quan trọng. |
| Dữ liệu và chỉ số đánh giá | 12/15 | Đúng scaling và ba metrics; phiên bản/feature schema chưa xác nhận hoàn toàn. |
| Phương pháp đối chứng và thiết kế thực nghiệm | 8/15 | 9/11 triển khai; mới có full-budget 30 lần trên Iris; ngân sách FBI và thống kê gộp chưa khớp xác định. |
| Bằng chứng khớp số kết quả công bố | 0/10 | Đối chiếu mô hình chính trên Iris chưa đạt: cả ba mean lệch lớn. Chỉ chấm bằng chứng hiện có, không suy rộng rằng mọi dataset đều thất bại. |
| **Tổng** | **65/100** | Điểm đánh giá có chủ quan; nên diễn giải là khoảng 60–70%, không có độ chính xác tới từng phần trăm. |

Điểm này ghi nhận code đã tái tạo được bộ khung và các phép tính quan trọng, đồng thời chưa công nhận độ trung thành của toàn bộ mô hình/thực nghiệm. Không thay thế một benchmark xác nhận bởi tác giả.

## Thứ tự cải thiện đề xuất

1. Chốt cách hiểu fitness; kiểm tra riêng tác động của w và miền tham số, không dùng nhãn thật làm fitness GA và không chọn biến thể bằng cách ép khớp bảng kết quả.
2. Bổ sung quy tắc dừng theo J bám Step 13 và kiểm tra cấu hình không hữu hạn. Lưu profile và artifact mới riêng để bảo toàn so sánh với bản hiện tại.
3. Xác nhận gamma, khởi tạo và mutation; thực hiện ablation có kiểm soát, đổi một yếu tố mỗi lần và báo cả các trường hợp không cải thiện.
4. Triển khai hai baseline còn thiếu từ nguồn đầy đủ. Chạy 30 lần trên 10 dataset chính; giữ 4 bộ riêng để đánh giá theo yêu cầu. Nếu cần khớp bảng 14 bộ, tạo experiment khác với phạm vi đó.
5. Chỉ sau các bước trên mới chấm lại độ khớp mean/SD/rank, cùng số fitness evaluations và thời gian. Sai khác runtime giữa máy không tự chứng minh thuật toán nhanh hay chậm hơn bài.

**Lượt này chỉ đánh giá và ghi bằng chứng; code mô hình, cấu hình và các kết quả cũ được giữ nguyên.**
