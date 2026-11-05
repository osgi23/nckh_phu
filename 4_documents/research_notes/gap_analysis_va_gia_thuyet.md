# Phân tích khoảng trống và đề xuất giả thuyết — DP-GA-PFCM

Ngày lập: 2026-11-05. Tiếp nối [literature_review.md](literature_review.md).

Mọi số liệu trong tài liệu này do tôi tự chạy trong session này, trên bản code tại
`2_models_code/` không sửa đổi, với `configs/corrected_reference.json` ở ngân sách
của bài báo (population 80, 100 thế hệ). Các script chẩn đoán và dữ liệu thô được
liệt kê ở mục 6.

---

## 1. Bối cảnh bài toán (phần còn trống của prompt, điền từ repo)

| Hạng mục | Nội dung |
|---|---|
| **Lĩnh vực** | Machine learning — học không giám sát: phân cụm mờ (fuzzy clustering) kết hợp tối ưu tiến hóa. |
| **Bài toán** | Cho ma trận đặc trưng X (N×d) **không có nhãn**, phân N điểm thành K cụm. Nhãn thật chỉ dùng để đánh giá sau khi thuật toán đã chạy xong. Mục tiêu kép: (a) tái tạo trung thực DP-GA-PFCM của Kuo và cộng sự 2023, (b) tìm một cải tiến vượt baseline. |
| **Dataset / benchmark** | 14 bộ. **10 bộ của bài báo** (`1_datasets/10_datasets_bai_bao/`): Iris (150×4, K=3), Flame (240×2, K=2), Jain (373×2, K=2), Wine (178×13, K=3), Glass (214×9, K=7), Ecoli (336×7, K=8), Compound (399×2, K=6), Seed (210×7, K=3), Breast Tissue (106×9, K=6), Aggregation (788×2, K=7). **4 bộ mở rộng** (`04_datasets_mo_rong/`): Pima (768×8, K=2), Room Occupancy (20560×5, K=2), Rice (3810×7, K=2), Wifi (2000×7, K=4). |
| **Cách chia dữ liệu** | **Không có chia train/val/test theo dòng** — đây là phân cụm toàn bộ dataset, đúng như giao thức của bài báo. Việc chia dev/test diễn ra **ở mức dataset**, xem mục 2. MinMax theo từng đặc trưng trên toàn dataset. |
| **Baseline** | Chính: **DP-GA-PFCM** như đã tái tạo. Đối chứng cùng ngân sách và cùng fitness: DP-PSO-PFCM, DP-SCA-PFCM, DP-FBI-PFCM. Đối chứng cơ sở: K-means, FCM, PFCM, DP-FCM, DP-PFCM. Mốc công bố: Table 11–13 của bài báo. |
| **Chỉ số baseline** (tôi chạy, 10 bộ, 5 seed, ngân sách bài báo) | ARI trung bình: chỉ tâm DPC **0.4659** → DP-GA-PFCM **0.5413** → DP-PSO-PFCM **0.5512** → DP-SCA-PFCM **0.5413**. Purity trung bình DP-GA-PFCM 0.780. |
| **Chỉ số mục tiêu** | Chính: **ARI**. Phụ: Purity (Eq.17), NMI. Không được làm xấu đáng kể số cụm quan sát được, runtime và số lần chấm fitness. |
| **Ràng buộc** | 4 CPU, 15 GB RAM, **không có GPU** (`torch` không được cài; nhánh `gpu_evaluator.py` không chạy trong môi trường này). Python 3.12–3.13, numpy/scipy/scikit-learn. Không dùng dữ liệu ngoài 14 bộ đã có hash. Không dùng nhãn thật bên trong thuật toán. |

---

## 2. Protocol đánh giá (chốt trước khi chạy bất kỳ thí nghiệm tuyển chọn nào)

Đây là phần tôi bổ sung so với trạng thái hiện tại của dự án. Cơ sở: [AAAI 2022](https://ojs.aaai.org/index.php/AAAI/article/view/20747)
cảnh báo rằng xếp hạng phương pháp theo điểm tốt nhất sau khi tinh chỉnh trên các
metric dùng nhãn "không khớp với cách các thuật toán này được dùng trong thực tế";
[bioRxiv 2025](https://www.biorxiv.org/content/10.1101/2025.08.20.671270v1.full) nói
việc tinh chỉnh siêu tham số để khớp nhãn "làm hỏng tính công bằng của đánh giá".

**Chia ở mức dataset, không phải mức dòng:**

- **Tập phát triển (dev)** — được phép dùng nhãn để ra quyết định thiết kế: 4 bộ mở
  rộng (Pima, Room Occupancy, Rice, Wifi), cộng dữ liệu Gaussian tổng hợp của
  `gaussian_data.py`. Lý do chọn: chúng **không nằm trong 10 bộ dùng để đối chiếu
  Table 11–13**, và việc tách 10+4 đã có sẵn trong dự án từ trước, không phải tôi
  đặt ra sau khi thấy kết quả.
- **Tập kiểm tra (test)** — chỉ báo cáo một lần, không dùng để chọn: 10 bộ của bài báo.

**Hai loại tiêu chí, phải phân biệt rõ:**

1. **Tiêu chí không dùng nhãn** (được phép đo trên cả 14 bộ, kể cả test, vì không
   rò rỉ thông tin nhãn): mức giảm fitness tương đối
   `(f_gen0 − f_gen100) / |f_gen0|`, số run đứng yên, số lần chấm fitness, runtime,
   số cụm quan sát được.
2. **Tiêu chí dùng nhãn** (ARI, Purity, NMI): chỉ dùng để **ra quyết định** trên tập
   dev; trên tập test chỉ **báo cáo kết quả cuối**.

**Quy tắc quyết định, đăng ký trước:** một biến thể được chấp nhận đưa vào đánh giá
trên tập test khi và chỉ khi nó (a) **tăng** mức giảm fitness trung bình trên tập dev,
và (b) **không làm giảm** ARI trung bình trên tập dev. Nếu chỉ thỏa (a) mà không thỏa
(b), đó là kết quả âm và phải được ghi lại như kết quả âm.

**Thống kê:** tối thiểu 5 seed cho bước sàng lọc, 30 seed cho kết quả công bố. Báo cáo
mean ± sample SD. Chỉ gọi là "vượt trội" khi mức cải thiện lớn hơn độ dao động giữa các
seed, và được kiểm định ghép cặp theo từng dataset (seed đã ghép cặp sẵn: `seed =
SeedSequence([cfg.seed, table1_order, run])` dùng chung cho mọi phương pháp).

**Mỗi lần một biến.** Mọi biến thể lưu profile và artifact riêng, không ghi đè baseline.

---

## 3. Chẩn đoán baseline (error analysis)

### 3.1. Thí nghiệm

10 bộ của bài báo × 5 seed × {DP-GA-PFCM, DP-PSO-PFCM, DP-SCA-PFCM}, population 80,
100 thế hệ, **cùng fitness, cùng tâm DPC khởi tạo, cùng seed, cùng 8080 lần chấm
fitness**. Thêm một phép đo tham chiếu: gán mỗi điểm vào tâm DPC gần nhất, không chạy
bất kỳ bộ tối ưu nào (`DPC-init-only`, tất định).

### 3.2. Phát hiện 1 — GA gần như không di chuyển trên chính hàm mục tiêu của nó

Mức giảm fitness tương đối sau 100 thế hệ, trung bình 5 seed:

| Dataset | GA | PSO | SCA | GA/PSO |
|---|---:|---:|---:|---:|
| aggregation | 0.58% | 2.01% | 0.17% | 0.29 |
| breast_tissue | 0.85% | 40.30% | 35.47% | 0.02 |
| compound | 0.46% | 1.39% | 0.00% | 0.34 |
| ecoli | 0.06% | 10.12% | 6.29% | 0.006 |
| flame | 0.04% | 0.08% | 0.04% | 0.47 |
| glass | 0.07% | 10.54% | 5.12% | 0.007 |
| iris | 1.28% | 36.04% | 35.65% | 0.035 |
| jain | 0.49% | 1.46% | 1.43% | 0.33 |
| seed | 0.05% | 0.23% | 0.00% | 0.21 |
| wine | 0.08% | 0.56% | 0.08% | 0.15 |
| **Trung bình** | **0.40%** | **10.27%** | **8.42%** | |

Ngoài ra **7/50 run của GA hoàn toàn không cải thiện** so với thế hệ 0 (fitness cuối
bằng fitness khởi tạo), so với **0/50** của PSO.

Đây là **tiêu chí không dùng nhãn**, nên kết luận này không phụ thuộc vào cách đánh giá:
với cùng hàm mục tiêu và cùng ngân sách, các toán tử GA hiện tại kém hơn PSO và SCA
khoảng **20 lần** về khả năng hạ hàm mục tiêu. Bốn nguyên nhân khả dĩ, đều nằm trong
`purple_main_model/dp_ga_pfcm.py`:

1. **Không ghi ngược tâm vào nhiễm sắc thể** (`lamarckian: false` trong config). Fitness
   được chấm *sau* một bước PFCM, nhưng nhiễm sắc thể vẫn giữ tâm trước bước đó
   (`meta_pfcm.py`, nhánh `if self.cfg["lamarckian"]`). Cải thiện do PFCM tạo ra bị bỏ
   đi ở mỗi thế hệ.
2. **Lai số học trên tọa độ tâm chưa căn chỉnh thứ tự** (`dp_ga_pfcm.py:21–26`): tâm thứ
   j của cha và của mẹ có thể thuộc hai cụm khác nhau; `r*parent[j] + (1−r)*parent[j+1]`
   khi đó nội suy giữa hai cụm khác nhau.
3. **Áp lực chọn lọc gần như bằng không**: roulette theo `1/loss` (`dp_ga_pfcm.py:17–19`).
   Khi các loss trong quần thể gần nhau — đúng trường hợp này, vì quần thể khởi tạo
   bám sát tâm DPC với `seed_jitter = 0.05` — xác suất chọn gần như đều.
4. **Bước đột biến quá nhỏ**: `mutation_rate = 0.1` áp cho **cá thể**, mỗi cá thể chỉ đột
   biến **một gene**, biên độ `mutation_range = 0.1` nhân `2^(−r·10)`, nên bước trung vị
   chỉ khoảng 0.3% miền giá trị.

### 3.3. Phát hiện 2 — hàm fitness không khớp với chất lượng phân cụm

Đây là phát hiện quan trọng hơn phát hiện 1, và nó đi ngược trực giác.

Mặc dù GA hạ fitness kém hơn PSO khoảng 20 lần, **ARI của GA không kém tương ứng**:

| | ARI trung bình trên 10 bộ |
|---|---:|
| Chỉ tâm DPC, không tối ưu | 0.4659 |
| DP-GA-PFCM (giảm fitness 0.40%) | 0.5413 |
| DP-SCA-PFCM (giảm fitness 8.42%) | 0.5413 |
| DP-PSO-PFCM (giảm fitness 10.27%) | 0.5512 |

Thí nghiệm H1 ở mục 5 là **phép kiểm chứng có kiểm soát** cho phát hiện này: trên 4 bộ dev,
chỉ bật một cờ làm GA hạ fitness **tốt hơn 14.1 lần** (0.26% → 3.64%) và ARI thay đổi
**−0.0004**, nhỏ hơn 1/10 độ dao động giữa các seed. Tức là quan hệ nhân quả từ "tối ưu tốt
hơn" sang "phân cụm tốt hơn" **không tồn tại** ở mức ngân sách này.

Hệ số tương quan Pearson giữa mức giảm fitness và mức cải thiện ARI so với tâm DPC, trên
150 lần chạy, là **r = +0.412** — yếu. Tính riêng từng dataset thì nó **đổi dấu**:

| Dataset | r | | Dataset | r |
|---|---:|---|---|---:|
| iris | **+0.771** | | jain | −0.040 |
| compound | +0.413 | | wine | −0.202 |
| flame | +0.268 | | breast_tissue | **−0.398** |
| glass | +0.230 | | ecoli | **−0.803** |
| aggregation | +0.166 | | seed | không tính được (SD = 0) |

Ví dụ rõ nhất là **Ecoli**: GA hạ fitness 0.06% và đạt ARI 0.552; PSO hạ fitness 10.12%
và chỉ đạt ARI 0.371. Tối ưu hàm mục tiêu **tốt hơn 170 lần** lại cho kết quả phân cụm
**xấu hơn 0.18 ARI**.

Cơ chế quan sát được: trên Iris, PSO và SCA đẩy `w` xuống **đúng cận dưới 1.10** của miền
tìm kiếm trong mọi run, làm membership gần như cứng và cho purity 0.887. GA giữ `w` trong
khoảng 1.44–1.62 và chỉ cho purity 0.667 ở 3/5 run. Trên Ecoli, GA làm cụm gộp lại còn
**4 cụm thay vì K=8** và nhờ đó ARI lại cao hơn, vì Ecoli có các lớp rất mất cân bằng.

Nói cách khác: những gì bộ tối ưu "học" được phần lớn là **đi tới biên của miền tham số
`w` do chúng tôi tự đặt** (`ASSUMPTIONS.md`, miền `w ∈ [1.1, 5]`), chứ không phải tìm
được cấu trúc cụm tốt hơn.

### 3.4. Phát hiện 3 — phần lớn chất lượng đến từ DPC, không từ bộ tối ưu

Mức cải thiện ARI mà **toàn bộ** giai đoạn tối ưu (8080 lần chấm fitness) thêm được so
với việc chỉ gán điểm vào tâm DPC gần nhất:

| Dataset | Chỉ DPC | +GA | +PSO | +SCA |
|---|---:|---:|---:|---:|
| aggregation | 0.710 | **−0.003** | +0.006 | +0.005 |
| breast_tissue | 0.193 | +0.120 | +0.106 | +0.110 |
| compound | 0.526 | +0.008 | +0.033 | +0.025 |
| ecoli | 0.294 | +0.259 | +0.077 | +0.095 |
| flame | 0.500 | **−0.030** | +0.017 | +0.007 |
| glass | 0.152 | +0.013 | +0.051 | −0.019 |
| iris | 0.450 | +0.083 | +0.266 | +0.272 |
| jain | 0.337 | +0.242 | +0.244 | +0.203 |
| seed | 0.727 | **−0.022** | −0.022 | −0.022 |
| wine | 0.772 | +0.084 | +0.075 | +0.078 |
| **Trung bình** | **0.466** | **+0.075** | **+0.085** | **+0.075** |

Trên **3/10 bộ, GA làm kết quả xấu hơn so với chỉ dùng tâm DPC**. Trung bình, cả giai
đoạn metaheuristic chỉ đóng góp +0.075 ARI, tức khoảng **14% chất lượng cuối cùng**;
86% còn lại do DPC. Điều này khớp với trích đoạn của các nguồn về DPC trong
literature review: DPC vốn đã là một thuật toán mạnh, và phần yếu của nó nằm ở cutoff
và ở dữ liệu chênh lệch mật độ (Glass 0.152, Breast Tissue 0.193, Ecoli 0.294 — đúng ba
bộ có DPC kém nhất).

### 3.5. Phát hiện 4 — mức tái tạo thực sự tốt hơn đánh giá trước đó, trừ Iris

Báo cáo `code_review_2026-10-10/REVIEW.md` chấm **0/10** cho hạng mục "bằng chứng khớp số
kết quả công bố", dựa trên **một dataset duy nhất là Iris**. Ở ngân sách của bài báo trên
cả 10 bộ, bức tranh khác:

| Dataset | Acc bài | Acc code | Δ | ARI bài | ARI code | Δ |
|---|---:|---:|---:|---:|---:|---:|
| aggregation | 0.910 | 0.900 | −0.010 | 0.695 | 0.706 | +0.011 |
| breast_tissue | 0.615 | 0.574 | −0.041 | 0.370 | 0.313 | −0.057 |
| compound | 0.845 | 0.832 | −0.013 | 0.555 | 0.534 | −0.021 |
| ecoli | 0.777 | 0.731 | −0.046 | 0.352 | 0.552 | **+0.200** |
| flame | 0.848 | 0.843 | −0.005 | 0.482 | 0.470 | −0.012 |
| glass | 0.581 | 0.546 | −0.035 | 0.183 | 0.165 | −0.018 |
| **iris** | 0.914 | 0.749 | **−0.165** | 0.774 | 0.533 | **−0.241** |
| jain | 0.882 | 0.883 | +0.001 | 0.575 | 0.578 | +0.003 |
| seed | 0.900 | 0.890 | −0.010 | 0.730 | 0.705 | −0.025 |
| wine | 0.955 | 0.952 | −0.003 | 0.865 | 0.856 | −0.009 |

Sai lệch tuyệt đối trung bình: accuracy 0.033, ARI 0.060. **Bỏ Iris** thì accuracy còn
**0.018**; bỏ cả Iris và Ecoli thì ARI còn **0.020**. Tức là trên 8/10 bộ, bản tái tạo
khớp bài báo trong khoảng 0.02 — mức hợp lý cho một bản tái tạo có giả định công khai.

**Iris là ngoại lệ duy nhất đáng kể, và nó là một ngoại lệ có thể giải thích được.** Chi
tiết 5 run trên Iris:

| Run | GA gain | GA purity | GA ARI | GA w | PSO purity | PSO ARI | PSO w |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1.19% | 0.667 | 0.429 | 1.49 | 0.887 | 0.716 | 1.10 |
| 2 | 1.29% | 0.667 | 0.429 | 1.62 | 0.887 | 0.716 | 1.10 |
| 3 | 0.48% | 0.873 | 0.690 | 1.62 | 0.887 | 0.716 | 1.14 |
| 4 | 0.34% | 0.667 | 0.426 | 1.44 | 0.887 | 0.716 | 1.10 |
| 5 | 3.08% | 0.873 | 0.690 | 1.59 | 0.887 | 0.716 | 1.10 |

3/5 run bị kẹt ở purity 0.667, tức hai trong ba lớp bị gộp. Đây là **hệ quả trực tiếp của
phát hiện 1**: GA không rời được vùng lân cận nghiệm DPC khởi tạo, mà nghiệm đó trên Iris
chỉ cho ARI 0.450.

**Hệ quả cho việc chấm điểm tái tạo:** nên sửa hạng mục "bằng chứng khớp số kết quả công
bố" từ 0/10 lên khoảng 6/10, và ghi rõ rằng bằng chứng cũ chỉ dựa trên một dataset. Tôi
không tự sửa file REVIEW.md vì đó là biên bản của một lượt đánh giá khác; đề xuất ghi
thành một phụ lục mới.

---

## 4. Năm khoảng trống nghiên cứu

| # | Khoảng trống | Bằng chứng từ văn liệu | Bằng chứng từ error analysis |
|---|---|---|---|
| **G1** | **Fitness của GA trong bài báo không xác định và, ở bất kỳ cách đọc nào, không khớp mục tiêu phân cụm.** **Đây là khoảng trống lớn nhất.** | Step 6 của bài báo ghi nguyên văn *"minimize the within-cluster sum of squared errors using PFCM algorithm (Eq. (6)"* — ba khái niệm khác nhau trong một câu; Eq.(6) là objective FCM, Eq.(11) là của PFCM. Văn liệu đã chuyển sang dùng chỉ số validity nội tại làm fitness ([Heliyon 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC11787482/), [GECCO 2021](https://doi.org/10.1145/3449639.3459341) thử 22 CVI). | Tương quan fitness–ARI chỉ r = +0.412 toàn cục và **đổi dấu trên 4/9 dataset** (Ecoli −0.803). Hạ fitness tốt hơn 170 lần trên Ecoli lại cho ARI xấu hơn 0.18. **Bằng chứng mạnh nhất:** thí nghiệm có kiểm soát H1 làm GA hạ fitness tốt hơn **14.1 lần** trên tập dev và ARI đổi **−0.0004**. |
| **G2** | **Các toán tử GA không tạo được tiến bộ tìm kiếm.** Thật, nhưng **sửa nó không đem lại chất lượng** (xem H1), nên đây là khoảng trống về tính trung thực của việc gọi mô hình là "tối ưu bằng GA", không phải đòn bẩy để vượt baseline. | [arXiv:2002.11577](https://arxiv.org/abs/2002.11577): hàm mục tiêu bất biến với hoán vị cụm làm biểu diễn "dư thừa nặng", crossover theo điểm cắt "phá hoàn toàn cấu trúc nghiệm". [Recombinator-k-means](https://arxiv.org/abs/1905.00531) tránh lai số học, thay tâm rồi tinh chỉnh ngay. | GA giảm fitness 0.40% so với 10.27% của PSO ở **cùng fitness, cùng khởi tạo, cùng 8080 lần chấm**. 7/50 run đứng yên hoàn toàn (PSO: 0/50). |
| **G3** | **Miền tìm kiếm của a, b, w, η là do người tái tạo tự đặt, và bộ tối ưu đang khai thác chính cái biên đó.** | Bài báo chỉ yêu cầu các giá trị > 0, không cho bounds (R02 trong `danh-gia-kha-nang-tai-tao.md`). Văn liệu về fuzzifier **mâu thuẫn nhau**: [Zhou và cộng sự](https://doi.org/10.1007/s11432-014-5146-0) đề xuất m ∈ [2, 3.5]; [Wu](https://www.sciencedirect.com/science/article/abs/pii/S0031320311003001) khuyến nghị m = 4 cho dữ liệu nhiễu. | PSO và SCA đẩy `w` xuống **đúng cận dưới 1.10** trong 10/10 run trên Iris. Nghiệm nằm ở biên nghĩa là kết quả do **chúng tôi chọn biên**, không phải do thuật toán tìm được. |
| **G4** | **Đóng góp của giai đoạn metaheuristic nhỏ so với chi phí, và âm trên một số dataset.** | Không có nguồn nào trong lượt khảo sát báo cáo tách riêng đóng góp của bộ tối ưu so với khởi tạo DPC. Đây là một khoảng trống trong **cách báo cáo** của cả dòng nghiên cứu này. | +0.075 ARI cho 8080 lần chấm fitness, tức ~14% chất lượng cuối. **Âm trên 3/10 bộ** (aggregation, flame, seed). Ba bộ DPC yếu nhất (glass 0.152, breast_tissue 0.193, ecoli 0.294) đúng là ba bộ còn nhiều chỗ để cải thiện nhất. |
| **G5** | **Chuẩn đánh giá: chọn cấu hình theo metric có nhãn, và gộp mean-run với best-run.** | [AAAI 2022](https://ojs.aaai.org/index.php/AAAI/article/view/20747) và [bioRxiv 2025](https://www.biorxiv.org/content/10.1101/2025.08.20.671270v1.full) đều cảnh báo trực tiếp về điều này. | Dự án chưa có tập dev tách biệt; `ASSUMPTIONS.md` liệt kê nhiều lựa chọn nhưng không ghi lựa chọn đó được quyết định bằng tiêu chí nào. Mục 2 của tài liệu này là phần bù. |

---

## 5. Giả thuyết

Sắp theo thứ tự nên làm, không theo mức hấp dẫn.

### H1 — Ghi ngược tâm sau bước PFCM vào nhiễm sắc thể (Lamarckian)

- **Giả thuyết:** Nếu ghi tâm đã cập nhật sau một bước PFCM trở lại nhiễm sắc thể
  (`lamarckian: true`) thì **mức giảm fitness** sẽ tăng, vì GA mới tích lũy được cải
  thiện cục bộ qua các thế hệ thay vì bỏ nó đi ở mỗi thế hệ.
- **Cơ sở:** `meta_pfcm.py` chấm fitness sau một bước PFCM nhưng chỉ ghi lại tâm mới khi
  cờ này bật; baseline đang tắt. [Memetic Computing 2018](https://doi.org/10.1007/s12293-018-0256-7)
  kết luận nên ưu tiên biến thể Lamarckian (miền khác: cây Steiner, nên chỉ là cơ sở
  cơ chế). [Recombinator-k-means](https://arxiv.org/abs/1905.00531) cũng tinh chỉnh ngay
  sau tái tổ hợp.
- **Cách kiểm chứng:** chỉ đổi một cờ config, không sửa code. Chạy trên **tập dev** trước,
  5 seed, so với baseline cùng seed. Áp quy tắc quyết định ở mục 2.

#### Kết quả: ĐÃ CHẠY ĐỦ TẬP DEV — **KẾT QUẢ ÂM**

4 bộ dev × 5 seed ghép cặp, ngân sách bài báo:

| Dataset | Giảm fitness baseline | Giảm fitness H1 | ARI baseline | ARI H1 | ΔARI |
|---|---:|---:|---:|---:|---:|
| pima | 0.05% | 1.34% | 0.1042 ± 0.0019 | 0.1062 ± 0.0025 | +0.0020 |
| rice | 0.03% | 0.16% | 0.6842 ± 0.0015 | 0.6816 ± 0.0030 | −0.0026 |
| room_occupancy | 0.38% | 1.93% | 0.0168 ± 0.0015 | 0.0166 ± 0.0005 | −0.0001 |
| wifi | 0.57% | 11.14% | 0.8558 ± 0.0121 | 0.8547 ± 0.0016 | −0.0011 |
| **Trung bình** | **0.26%** | **3.64%** | **0.4152** | **0.4148** | **−0.0004** |

Chênh lệch ARI theo từng seed ghép cặp (n = 20): mean **−0.00044**, SD 0.00629;
11 cặp tốt hơn, 9 cặp xấu hơn.

Áp quy tắc quyết định đã đăng ký trước ở mục 2:

- (a) tăng mức giảm fitness trên dev: **ĐẠT** — 0.26% → 3.64%, tăng **14.1 lần**.
- (b) không làm giảm ARI trên dev: **KHÔNG ĐẠT** — −0.0004.

→ **Không đưa H1 sang tập test.** Ghi lại như kết quả âm.

**Diễn giải, và một dự đoán của tôi đã sai.** Trước khi chạy đủ tập dev, tôi đã dựa vào
một probe trên Iris ở ngân sách thấp (pop 40, gen 40, 5 seed: purity 0.903 ± 0.013,
ARI 0.748 ± 0.028, so với baseline 0.667/0.423) để dự đoán H1 sẽ cải thiện rõ. Dự đoán đó
**không đúng**. Iris là một bộ thuộc **tập test** và là một trường hợp thuận lợi đơn lẻ;
trên 4 bộ dev được chọn trước, cùng một thay đổi làm GA tối ưu **tốt hơn 14 lần** mà chất
lượng phân cụm **không đổi** (mức thay đổi nhỏ hơn 1/10 độ dao động giữa các seed).

Đây chính là lý do protocol ở mục 2 tồn tại. Nếu chọn H1 dựa trên Iris, tôi đã công bố một
"cải tiến" mà bằng chứng duy nhất là một dataset nằm trong tập dùng để đối chiếu kết quả.

**Giá trị khoa học của kết quả âm này rất cao:** H1 là một thí nghiệm có kiểm soát, chỉ đổi
một biến, và nó **tăng cường độ tối ưu lên 14 lần với chất lượng không đổi**. Đó là bằng
chứng mạnh nhất tôi có cho **G1**: điểm nghẽn của mô hình **không nằm ở bộ tối ưu, mà nằm ở
hàm mục tiêu**. Một quan sát phụ củng cố điều này: H1 kéo `w` về vùng giữa miền
(pima 2.72 → 1.89, room 3.05 → 1.91) thay vì ra biên, nhưng ARI vẫn không đổi.

### H2 — Căn chỉnh thứ tự tâm trước khi lai

- **Giả thuyết:** Nếu khớp các tâm của hai cha mẹ bằng bài toán gán tối ưu (Hungarian trên
  ma trận khoảng cách giữa hai bộ tâm) **trước** khi thực hiện lai số học, thì mức giảm
  fitness sẽ tăng, vì phép lai khi đó nội suy giữa hai tâm cùng mô tả một cụm thay vì
  giữa hai cụm khác nhau.
- **Cơ sở:** `dp_ga_pfcm.py:21–26` lai theo chỉ số gene mà không khớp cụm.
  [arXiv:2002.11577](https://arxiv.org/abs/2002.11577) nêu đúng cơ chế hỏng này.
  `nk.h` của NKGAclust có hàm `fixLabels` làm việc tương đương trong không gian nhãn.
  [Clumppling](https://pmc.ncbi.nlm.nih.gov/articles/PMC10766593/) là tham chiếu kỹ thuật
  cho bước khớp.
- **Bằng chứng đối lập, phải ghi rõ:** [IEEE 1992 về permutation problem](https://ieeexplore.ieee.org/document/273944/)
  báo rằng sắp xếp trước khi lai cho kết quả tốt nhất **nhưng crossover đơn giản cũng
  làm khá tốt**, và kết luận rằng vấn đề hoán vị "không nghiêm trọng trong thực tế".
  Vì vậy H2 **có khả năng cho kết quả âm** và phải được chạy chứ không được giả định.
- **Cách kiểm chứng:** thêm cờ `crossover_align: none|hungarian`. So H2 với H1 đã bật,
  mỗi lần một biến. Tập dev, 5 seed.

### H3 — Tăng áp lực chọn lọc

- **Giả thuyết:** Nếu thay roulette theo `1/loss` bằng tournament kích thước 2–3 thì mức
  giảm fitness sẽ tăng, vì tournament có áp lực chọn lọc không phụ thuộc thang giá trị của
  loss, trong khi `1/loss` cho xác suất gần như đều khi các loss trong quần thể gần nhau.
- **Cơ sở:** `dp_ga_pfcm.py:17–19`; comment trong chính code ghi *"Choice missing in
  paper"*, nên đây là giả định của bản tái tạo chứ không phải quy định của bài báo.
  R06 trong `danh-gia-kha-nang-tai-tao.md` cũng xác nhận bài báo không cho công thức
  chuyển loss thành xác suất.
- **Cách kiểm chứng đi kèm một phép đo trung gian:** đo trực tiếp **độ phân tán xác suất
  chọn** (entropy của phân bố roulette, chuẩn hóa về [0,1]) ở thế hệ 1 và 50. Nếu entropy
  gần 1 thì giả thuyết về nguyên nhân được xác nhận độc lập với kết quả cuối. Đây là phép
  đo không dùng nhãn.

### H4 — Thay fitness bằng một chỉ số validity nội tại

- **Giả thuyết:** Nếu thay fitness `sum(u^w · d²)` bằng một chỉ số validity nội tại không
  phụ thuộc tham số mờ (ưu tiên Calinski–Harabasz hoặc Davies–Bouldin theo xếp hạng của
  GECCO 2021) thì **ARI** sẽ tăng, vì các chỉ số đó đo tỷ lệ giữa độ tách cụm và độ nén
  cụm — tức là chính đại lượng mà ARI phản ánh — thay vì đo một objective mà `w` có thể
  làm thay đổi thang giá trị.
- **Cơ sở:** [GECCO 2021](https://doi.org/10.1145/3449639.3459341) thử 22 CVI làm fitness
  và báo Calinski–Harabasz, Davies–Bouldin, generalized Dunn đạt hiệu năng phù hợp trên cả
  dữ liệu tổng hợp và thực. [Scientific Reports 2025](https://www.nature.com/articles/s41598-025-08473-6)
  xác nhận việc chọn chỉ số "có thể ảnh hưởng nghiêm trọng" tới chất lượng cụm.
  Từ phía dữ liệu: đây là giả thuyết trực tiếp nhắm vào G1, khoảng trống lớn nhất.
- **Rủi ro phải nêu trước:** các CVI này giả định cụm lồi và gần cầu, nên có thể **xấu đi**
  trên Flame, Jain, Compound, Aggregation — đúng những bộ có hình dạng bất kỳ. Phải báo
  cáo riêng nhóm shape datasets, không được gộp vào một con số trung bình.
- **Cách kiểm chứng:** `meta_pfcm.py` đã có cấu trúc `cfg["fitness"]` với 4 nhánh; thêm
  nhánh mới là thay đổi cục bộ. Tập dev + Gaussian tổng hợp có điều khiển độ chồng lấn
  (đã có `gaussian_data.py`), 5 seed, so với H1 đã bật.

### H5 — Dồn ngân sách vào DPC thay vì vào bộ tối ưu

- **Giả thuyết:** Nếu dùng mật độ theo láng giềng có thang đo cục bộ thay cho mật độ
  Gaussian theo một cutoff toàn cục, thì ARI sẽ tăng **nhiều hơn** mức +0.075 mà cả giai
  đoạn metaheuristic đang mang lại, vì 86% chất lượng cuối cùng đã đến từ DPC và ba bộ có
  DPC yếu nhất cũng là ba bộ có kết quả cuối kém nhất.
- **Cơ sở:** Phát hiện 3 ở mục 3.4 (đóng góp +0.075 ARI, âm trên 3/10 bộ).
  [Zelnik-Manor & Perona NIPS 2004](https://papers.nips.cc/paper/2619-self-tuning-spectral-clustering)
  đặt σ_i bằng khoảng cách tới láng giềng thứ k (gợi ý k = 7).
  [Scientific Reports 2025 về natural-NN DPC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12855208/)
  và [Pattern Recognition 2022 về balance density](https://www.sciencedirect.com/science/article/abs/pii/S0031320322005325)
  nêu đúng hai điểm yếu đang gặp: cutoff tùy ý, và chênh lệch mật độ giữa các cụm.
- **Lưu ý triển khai từ code NKGAclust đã đọc:** `threeSigmaRule` tính ba ngưỡng
  `dt0, dt1, dt2` trực tiếp từ khoảng cách Euclidean của các cạnh. Nếu đổi thang đo khoảng
  cách thì **bắt buộc** tính lại ba ngưỡng này trên thang mới; so ngưỡng cũ với khoảng cách
  mới là một lỗi lặng.
- **Cách kiểm chứng:** biến thể DPC là một cờ trong `density_peak.py`. So sánh ở hai mức:
  (a) chỉ tâm DPC, không tối ưu — phép đo sạch nhất về đóng góp của DPC; (b) DPC mới + GA
  baseline. Tập dev trước.

### Thứ tự thực hiện, đã xét lại sau kết quả âm của H1

Thứ tự ban đầu của tôi là H1 → H3 → H2 → H4 → H5, tức sửa bộ tối ưu trước. Kết quả âm của
H1 **làm thứ tự đó mất cơ sở**: tăng cường độ tối ưu 14 lần không đổi được chất lượng, nên
H2 và H3 — vốn cũng chỉ nhằm làm GA tối ưu tốt hơn — có xác suất cao cho cùng một kết quả
âm. Thứ tự đã xét lại:

1. **H4 (thay fitness)** — nay là ưu tiên số một. H1 đã cho bằng chứng có kiểm soát rằng
   hàm mục tiêu là điểm nghẽn. Đây là thay đổi nhắm đúng G1.
2. **H5 (cải thiện DPC)** — ưu tiên số hai, theo phát hiện 3: 86% chất lượng cuối đến từ DPC,
   và ba bộ DPC yếu nhất đúng là ba bộ kết quả cuối kém nhất.
3. **H3 (áp lực chọn lọc)** — hạ xuống, và **chỉ chạy phần đo entropy xác suất chọn**. Phép
   đo đó rẻ, không dùng nhãn, và trả lời được câu hỏi "GA đứng yên vì lý do nào" mà không
   cần kỳ vọng nó cải thiện ARI.
4. **H2 (căn chỉnh tâm)** — hạ xuống thấp nhất. Nó đã có bằng chứng đối lập trong văn liệu,
   và nay có thêm bằng chứng từ chính dự án rằng loại cải tiến này không chuyển thành chất
   lượng. Chỉ chạy nếu H4 đã làm fitness khớp với chất lượng, vì khi đó mới quan sát được
   tác dụng thật của nó.

**Một kết luận quan trọng cho hướng nghiên cứu:** nếu H4 và H5 cũng không cho cải thiện
vượt độ dao động giữa các seed, thì kết luận trung thực là **dòng DP-metaheuristic-PFCM đã
tới giới hạn trên các benchmark này**, vì cả ba optimizer khác nhau (GA, PSO, SCA) cho ARI
trung bình 0.5413 / 0.5512 / 0.5413 — chênh nhau trong khoảng 0.01 — trong khi riêng tâm
DPC đã cho 0.4659. Đó cũng là một kết quả đáng công bố, và nó sẽ là lý do chính đáng để
chuyển sang hướng thay đổi biểu diễn nghiệm (AF-NKGA) thay vì tiếp tục tinh chỉnh.

Hướng **AF-NKGA** trong [kien_truc_nghien_cuu_adaptive_fuzzy_nkga.md](kien_truc_nghien_cuu_adaptive_fuzzy_nkga.md)
nằm sau H5: nó thay cả biểu diễn nghiệm, cả fitness và cả toán tử. Dữ liệu ở mục 3 cho
thấy nên biết rõ mức nền của từng thành phần trước khi thay toàn bộ ba thứ cùng lúc.

---

## 6. Dữ liệu thô và khả năng tái lập

| Nội dung | Vị trí |
|---|---|
| Script chẩn đoán 10 bộ (3 optimizer + DPC-only) | `research_notes/scripts/diag_search.py` |
| Script ablation tập dev | `research_notes/scripts/diag_dev.py` |
| Kết quả thô 10 bộ, 160 bản ghi JSONL | `research_notes/data/diag_main10.jsonl` |
| Kết quả thô tập dev | `research_notes/data/diag_dev.jsonl` |
| Source code NK hybrid GA đã đọc | clone từ `github.com/rtinos/NKGAclust` (không đưa vào repo này) |

Cả hai script dùng đúng cách sinh seed, đúng `k_policy` và đúng file config của
`common/runner.py`, nên kết quả ghép cặp được với các thực nghiệm sẵn có của dự án. Nhãn
thật chỉ được đọc sau khi `fit` đã trả về.

**Đã chạy trong lượt này:** chẩn đoán 10 bộ × 3 optimizer × 5 seed + DPC-only (160 bản ghi);
ablation H1 trên 4 bộ dev × 2 biến thể × 5 seed (40 bản ghi). Tổng 200 lần chạy mô hình ở
ngân sách bài báo.

**Chưa làm trong lượt này:** chưa chạy 30 seed; chưa có kiểm định ghép cặp chính thức
(Wilcoxon/Kruskal–Wallis) — các con số hiện tại chỉ là mean ± SD trên 5 seed, đủ để sàng lọc
nhưng **không đủ để công bố**; chưa chạy H2–H5; chưa đọc toàn văn 18/20 nguồn trong
literature review vì giới hạn mạng.

**Những điều KHÔNG được suy ra từ tài liệu này:**

- Không được kết luận DP-GA-PFCM "kém hơn PSO/SCA" trên 10 bộ: chênh lệch ARI trung bình
  0.5413 so với 0.5512 nằm trong khoảng dao động giữa các seed trên nhiều dataset và chưa
  được kiểm định.
- Không được kết luận bản tái tạo "đã khớp bài báo": Iris lệch −0.241 ARI là một sai lệch
  thật và chưa giải thích hết.
- Không được kết luận fitness hiện tại "sai": bài báo không xác định fitness nào, nên điều
  đã chứng minh là *fitness đang dùng không khớp với ARI*, chứ không phải *tác giả đã dùng
  sai*.
- Không được dùng `lamarckian: true` như một cải tiến. Trên tập dev nó là kết quả âm.
