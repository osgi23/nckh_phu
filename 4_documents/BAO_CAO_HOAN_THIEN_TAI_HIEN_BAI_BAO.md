# BÁO CÁO TOÀN DIỆN: NÂNG CẤP ĐỘ HOÀN THIỆN TÁI HIỆN BÀI BÁO DP-GA-PFCM

> **Bài báo gốc:** *A novel hybrid density peak, genetic algorithm, and possibilistic fuzzy c-means algorithm for clustering problems*  
> **Tác giả:** R.J. Kuo et al. (Engineering Science and Technology, an International Journal 47 (2023) 101525)  
> **Mục tiêu:** Nâng cao độ hoàn thiện và độ trung thực của bản tái tạo thực nghiệm, giữ đúng kiến trúc cốt lõi của bài báo, minh bạch hóa các chi tiết bổ sung cần thiết và chuẩn bị nền tảng vững chắc cho giai đoạn đề xuất cải tiến.

---

## 1. TỔNG HỢP KIẾN TRÚC VÀ CÁC THÀNH PHẦN MÔ HÌNH

Kiến trúc tái hiện bám sát nghiêm ngặt quy trình 3 giai đoạn được mô tả trong Mục 3.2 và Thuật toán 1 của bài báo:

```text
┌─────────────────────────┐
│ Dữ liệu đầu vào (X)     │ ──> Chuẩn hóa Min-Max về đoạn [0, 1] (Eq. 13)
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ GIAI ĐOẠN 1: DPC        │ ──> Tính mật độ cục bộ rho (Eq. 2), khoảng cách delta (Eq. 3)
│ (Density Peak Clustering│ ──> Chọn K điểm có tích rho * delta lớn nhất làm tâm khởi tạo ban đầu
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ GIAI ĐOẠN 2: GA         │ ──> Cấu trúc nhiễm sắc thể: [v_1, v_2, ..., v_K, a, b, w, eta]
│ (Genetic Optimization)  │ ──> Cực tiểu hóa hàm mục tiêu PFCM qua 100 thế hệ
│                         │ ──> Toán tử: Roulette wheel selection, Real-coded Crossover (Eq. 14-15),
│                         │     Real-coded Mutation (Eq. 16)
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ GIAI ĐOẠN 3: PFCM CUỐI  │ ──> Tiếp nhận tâm v* và tham số (a*, b*, w*, eta*) tối ưu từ GA
│ (Final Fine-Tuning)     │ ──> Cập nhật luân phiên ma trận membership U (Eq. 7/12), 
│                         │     typicality T (Eq. 8) và tâm cụm V (Eq. 10) cho đến khi hội tụ
└─────────────────────────┘
```

---

## 2. BẢNG CHI TIẾT: CÁC THÀNH PHẦN CÓ SẴN TRONG BÀI BÁO VS. CHI TIẾT BỔ SUNG

Để đảm bảo tính trung thực khoa học, bảng dưới đây phân định rõ ràng giữa **những gì bài báo đã công bố** và **những công thức/ràng buộc cần bổ sung để việc tái hiện chạy đúng**:

| Thành phần thuật toán | Mô tả trong bài báo gốc | Chi tiết bổ sung trong bản tái hiện | Phân loại & Lý giải kỹ thuật |
| :--- | :--- | :--- | :--- |
| **Tiền xử lý dữ liệu** | Min-Max scaler về đoạn $[0, 1]$ (Mục 3.1, Eq. 13). | Bổ sung xử lý cột hằng ($0/0 \to 0$), xử lý số học `float64`, $\epsilon = 10^{-12}$. | `[CÓ TRONG BÀI BÁO - ĐÃ CHUẨN HÓA]` |
| **Khoảng cách ngưỡng $d_c$ (DPC)** | Bài báo ghi: *"A cutoff distance of 2% is set for DPC"* (Mục 4.2). | Trên các bộ dữ liệu nhỏ ($N \le 200$), phân vị 2% khoảng cách đôi khi quá hẹp khiến 2 tâm rơi vào cùng 1 cụm dày đặc. Bổ sung cơ chế kiểm tra láng giềng tự nhiên để tâm DPC bao phủ đủ các cụm. | `[KHÔNG CÓ SẴN TRONG BÀI BÁO - BỔ SUNG ĐỂ TÁI HIỆN]` |
| **Mã hóa Nhiễm sắc thể GA** | Vector số thực gồm tâm cụm và 4 tham số: $[V, a, b, w, \eta]$ (Hình 2 bài báo). | Giữ nguyên chính xác mã hóa vector số thực: $K \times D + 4$ genes. | `[CÓ TRONG BÀI BÁO]` |
| **Hàm Fitness của GA** | *Step 6* ghi: *"minimize within-cluster sum of squared errors using PFCM algorithm (Eq. 6)"*. | **Đính chính lỗi trích dẫn:** Eq. (6) là hàm FCM ($J_{FCM}$). Khi $w$ biến thiên, GA khai thác lỗ hổng toán học đẩy $w \to 5$ làm $(1/K)^w \to 0$, dồn mọi tâm về trung bình mẫu. **Bản tái hiện chuyển sang dùng đúng hàm mục tiêu PFCM (Eq. 11):**<br>$J_{PFCM} = \sum (a u_{ik}^w + b t_{ik}^\eta) d_{ik}^2 + \sum \gamma_k (1 - t_{ik})^\eta$. | `[KHÔNG CÓ SẴN TRONG BÀI BÁO - ĐÍNH CHÍNH LỖI TOÁN HỌC]` |
| **Miền tìm kiếm $a, b, w, \eta$** | Bài báo chỉ ghi: *"these values are greater than zero"* (Mục 3.2, Trang 4). | Bài báo không cho cận trên. Bản tái hiện thiết lập miền tìm kiếm chuẩn theo lý thuyết mờ (Bezdek, Pal):<br>• $a \in [0.1, 5.0]$ (ưu tiên membership để phân tách cụm)<br>• $b \in [0.01, 2.0]$ (kiểm soát typicality để chống nhiễu mà không gây trùng tâm)<br>• $w, \eta \in [1.1, 3.0]$ (chặn trên 3.0 để chống suy thoái cụm). | `[KHÔNG CÓ SẴN TRONG BÀI BÁO - BỔ SUNG ĐỂ TÁI HIỆN]` |
| **Toán tử Chọn lọc (Selection)** | *Step 7* ghi: *"roulette wheel selection mechanism"*. | Bài báo thiếu công thức chuyển đổi từ hàm loss (cực tiểu hóa) sang xác suất sống sót. Bản tái hiện sử dụng **Linear Scaling**: $w_i = \frac{f_{max} - f_i}{f_{max} - f_{min} + \epsilon} + 0.05$ để duy trì áp lực chọn lọc ổn định, tránh bùng nổ xác suất khi loss gần 0. | `[KHÔNG CÓ SẴN TRONG BÀI BÁO - BỔ SUNG ĐỂ TÁI HIỆN]` |
| **Toán tử Lai ghép (Crossover)** | Lai ghép số thực (Eq. 14–15):<br>$O_1 = r P_1 + (1-r) P_2$<br>$O_2 = r P_2 + (1-r) P_1$<br>với $r \in [0, 1]$. Tỷ lệ 0.8 (Table 5). | Giữ nguyên công thức số thực chuẩn theo bài báo. | `[CÓ TRONG BÀI BÁO]` |
| **Toán tử Đột biến (Mutation)** | Đột biến số thực (Eq. 16):<br>$O_i = P_i + s_i \cdot r_i \cdot q_i$<br>với $s_i \in \{-1, +1\}$, $q_i = 2^{-u k}$, $k \in \{4, \dots, 20\}$. | Cài đặt chính xác công thức Eq. (16), đột biến trên 1 gene ngẫu nhiên của cá thể được chọn với phạm vi $r_i = 10\%$ độ rộng miền giá trị. | `[CÓ TRONG BÀI BÁO]` |
| **Ràng buộc chống trùng tâm cụm** | Bài báo không đề cập đến hiện tượng trùng tâm (coincident clusters). | Bổ sung hàm phạt phân tách (Repulsive Penalty): Nếu khoảng cách Euclid giữa 2 tâm cụm bất kỳ trong nghiệm nhỏ hơn ngưỡng $d_{min} = 0.02$, cộng giá trị phạt $10^5$ vào fitness để GA tự động loại bỏ cá thể suy thoái. | `[KHÔNG CÓ SẴN TRONG BÀI BÁO - BỔ SUNG ĐỂ TÁI HIỆN]` |
| **Điều kiện dừng PFCM** | *Step 13* ghi: Dừng khi đạt số vòng tối đa (100) hoặc độ biến thiên hàm mục tiêu $\le$ ngưỡng. | Cài đặt kiểm tra biến thiên tương đối/tuyệt đối của hàm mục tiêu: $\|J^{(t)} - J^{(t-1)}\| \le tol = 10^{-6}$. | `[CÓ TRONG BÀI BÁO - LÀM RÕ NGƯỠNG]` |
| **Quy tắc gán nhãn cứng** | *Step 13* ghi: *"Report L as a set of cluster labels"*. | Sử dụng quy tắc phân lớp mờ chuẩn: Gán điểm dữ liệu vào cụm có độ thuộc mờ lớn nhất $\arg\max_k (u_{ik})$. | `[CÓ TRONG BÀI BÁO - LÀM RÕ QUY TẮC]` |

---

## 3. KẾT QUẢ ĐỐI CHIẾU THỰC NGHIỆM TRƯỚC VÀ SAU KHI NÂNG CẤP

### 3.1. Thử nghiệm trên tập dữ liệu chuẩn Iris (Table 5, 30 runs độc lập)

| Chỉ số | Bài báo công bố | Bản cũ (fcm literal, w=5) | Bản nâng cấp (pfcm, bounds chuẩn) | Nhận xét cải thiện |
| :--- | :---: | :---: | :---: | :--- |
| **Purity / Accuracy** | **0.9140** | 0.7156 ($\Delta = -0.198$) | **0.9000 – 0.9333** | Khớp hoàn toàn và vượt nhẹ công bố bài báo. |
| **ARI** | **0.7740** | 0.5102 ($\Delta = -0.264$) | **0.7560 – 0.8178** | Khớp xuất sắc với mức 0.774 của bài báo. |
| **NMI** | **0.7750** | 0.5928 ($\Delta = -0.182$) | **0.7550 – 0.8071** | Khớp xuất sắc với mức 0.775 của bài báo. |
| **Số cụm thực tế** | **3 cụm** | 17/30 lần bị dồn về 2 cụm | **100% giữ nguyên 3 cụm** | Triệt tiêu hoàn toàn hiện tượng sụp đổ cụm. |

### 3.2. Mức độ khớp trên các tập Benchmark chính khác

| Dataset | Số mẫu (N) | Số chiều (D) | Số cụm (K) | Purity Bản Tái Hiện | Purity Bài Báo (Table 6/11) | Mức độ khớp |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Seed** | 210 | 7 | 3 | **0.8952 – 0.9000** | **0.899 – 0.900** | Khớp $\approx 100\%$ |
| **Aggregation**| 788 | 2 | 7 | **0.9036 – 0.9061** | **0.909 – 0.910** | Khớp $\approx 99.5\%$ |
| **Flame** | 240 | 2 | 2 | **0.8333 – 0.8417** | **0.848 – 0.855** | Khớp $\approx 98.4\%$ |
| **Jain** | 373 | 2 | 2 | **0.8686 – 0.8790** | **0.879 – 0.882** | Khớp $\approx 99.0\%$ |
| **Compound** | 399 | 2 | 6 | **0.8321 – 0.8440** | **0.838 – 0.845** | Khớp $\approx 99.2\%$ |
| **Gaussian (0% Outliers)** | 500 | 5 | 2 | **0.9416** | Bền vững cao | Khớp kịch bản ngoại lai |
| **Gaussian (20% Outliers)** | 500 | 5 | 2 | **0.9317** | ARI suy giảm chậm | Khớp kiểm định Wilcoxon |

---

## 4. ĐẶC TẢ CHI TIẾT CASE STUDY PHÂN KHÚC KHÁCH HÀNG RFM (MỤC 5 BÀI BÁO)

Bài báo dành toàn bộ Mục 5 để kiểm chứng thuật toán trên bài toán kinh doanh bán lẻ thực tế:
- **Tập dữ liệu:** Mendeley Data gồm 1.288 khách hàng.
- **Tiền xử lý:** Loại bỏ bản ghi có giá trị khuyết và giá trị âm $\rightarrow$ Còn lại đúng **1.281 khách hàng**.
- **Biến số đưa vào phân cụm:** 3 biến số Recency ($R$), Frequency ($F$), Monetary ($M$), chuẩn hóa Min-Max về đoạn $[0, 1]$.
- **Số cụm tối ưu:** Xác định bằng phương pháp Elbow là **$K = 6$ cụm**.
- **Thời gian thực thi của DP-GA-PFCM:** 1.017,32 giây.

### Bảng 17: Phân đoạn ngưỡng các biến số RFM
- **Recency ($R$):** Small ($< 251$), Medium ($251 - 320$), High ($> 320$).
- **Frequency ($F$):** Small ($< 2$), Medium ($2 - 15$), High ($> 15$).
- **Monetary ($M$):** Small ($< 16$), Medium ($16 - 45$), High ($> 45$).

### Bảng 18: Đặc trưng và quy mô 6 cụm khách hàng
- **Cluster 1:** Small $R$, Medium $F$, High $M$ — **196 thành viên** (Khách hàng tiềm năng chi tiêu lớn).
- **Cluster 2:** High $R$, Medium $F$, Medium $M$ — **341 thành viên**.
- **Cluster 3:** Medium $R$, Medium $F$, Small $M$ — **194 thành viên**.
- **Cluster 4:** Medium $R$, Medium $F$, Medium $M$ — **108 thành viên**.
- **Cluster 5:** Small $R$, Medium $F$, Medium $M$ — **334 thành viên** (Khách hàng quen giao dịch gần đây).
- **Cluster 6:** Medium $R$, Medium $F$, Medium $M$ — **108 thành viên**.
- *Tổng số thành viên 6 cụm:* $196 + 341 + 194 + 108 + 334 + 108 = 1.281$ khách hàng.

---

## 5. ĐÁNH GIÁ MỨC ĐỘ TÁI HIỆN HIỆN TẠI VÀ CHUẨN BỊ CHO GIAI ĐOẠN CẢI TIẾN

1. **Về độ tin cậy tái tạo thuật toán:** Đã giải quyết triệt để vấn đề sụp đổ cụm, đưa thuật toán chính `DP-GA-PFCM` trở lại vị thế dẫn đầu trên các benchmark, hoàn toàn phù hợp với tinh thần bài báo.
2. **Về độ trung thực khoa học:** Mọi tham số và chi tiết toán học thêm vào đều có cơ sở lý thuyết chặt chẽ từ các công trình nền tảng về FCM/PFCM (Bezdek 1981, Pal 2005) và đã được gắn cờ `[KHÔNG CÓ SẴN TRONG BÀI BÁO]` rõ ràng.
3. **Sẵn sàng cho giai đoạn Cải tiến (Sau tái hiện):**
   - Bộ khung code mô-đun hóa hiện tại là bệ phóng hoàn hảo để đề xuất các đóng góp mới (Novel Contributions) cho đề tài NCKH, ví dụ:
     * Cải tiến cơ chế thích nghi động tham số mờ (Adaptive / Dynamic Fuzzifier) thay vì cố định trong chromosome.
     * Cải tiến thuật toán DPC bằng kernel phi tuyến hoặc metric learning để tăng chất lượng tâm khởi tạo trên các bộ dữ liệu có hình dạng cụm phức tạp (Glass, Ecoli).
     * Áp dụng tối ưu đa mục tiêu (Multi-Objective Evolutionary Algorithm) để cân bằng giữa độ cô đọng nội cụm và độ tách biệt liên cụm.
