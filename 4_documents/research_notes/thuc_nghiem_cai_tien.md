# Thực nghiệm tìm cải tiến DP-GA-PFCM — kết quả và kết luận

Ngày: 2026-11-05. Tiếp nối [gap_analysis_va_gia_thuyet.md](gap_analysis_va_gia_thuyet.md).
Protocol dev/test và quy tắc quyết định giữ nguyên như mục 2 của tài liệu đó.

---

## 1. Kết luận trong một đoạn

Tôi đã thử **tám can thiệp** vào mô hình và **không can thiệp nào cải thiện ARI trung bình**.
Nguyên nhân đã đo được: **baseline DP-GA-PFCM đã nằm đúng ở trần của chính không gian
tham số của nó.** Trên 10 bộ dev, baseline đạt ARI 0.5463 còn oracle (biết nhãn, chọn
fuzzifier tốt nhất cho từng bộ) đạt 0.5464. Vì vậy không có cải tiến nào về bộ tối ưu,
hàm fitness, khởi tạo hay DPC có thể tạo ra mức tăng lớn về chất lượng.

Mức khác biệt lớn **có thật** nằm ở hai chỗ khác:

- **Chi phí:** một phương pháp quét 6 giá trị fuzzifier rồi chọn bằng độ ổn định có ràng
  buộc đúng k cụm đạt ARI **0.5395** so với **0.5413** của baseline trên 10 bộ của bài báo
  — không phân biệt được trong nhiễu — với **150 lần giải PFCM thay vì 8080 lần chấm
  fitness**, nhanh hơn 3.2 lần.
- **Từng dataset:** cùng phương pháp đó cho Iris **+0.208 ARI** (0.533 → 0.741, gần khớp
  0.774 của bài báo) và Breast Tissue **+0.116** (0.313 → 0.429, **vượt** 0.370 của bài báo),
  hoàn toàn không dùng nhãn.
- **Tiêu chí chọn mô hình:** ràng buộc "chỉ xét nghiệm có đúng k cụm" đáng **+0.10 ARI**
  trên dev (0.4390 → 0.5398). Không có ràng buộc này, mọi chỉ số nội tại tôi thử đều làm
  **xấu đi** so với việc cứ dùng `w=2`.

---

## 2. Tám can thiệp và kết quả trên tập dev

Mỗi biến thể đổi **một** yếu tố so với baseline, 5 seed ghép cặp, ngân sách bài báo
(population 80, 100 thế hệ). Baseline mọi lần đều được chạy lại trong cùng điều kiện.

| # | Biến thể | Cơ chế nhằm sửa | ΔARI trên dev | Kết luận |
|---|---|---|---:|---|
| 1 | `lamarckian=true` | GA không tích lũy cải thiện của bước PFCM | **−0.0004** | âm |
| 2 | `fitness=ch` | fitness không khớp chất lượng | **−0.0181** | âm |
| 3 | `fitness=db` | như trên | **−0.0246** | âm |
| 4 | `density_mode=local_scaled` | DPC phụ thuộc một cutoff toàn cục | **−0.0011** | trung tính |
| 5 | `init_mode=diverse` | quần thể bám sát một bộ tâm DPC | **−0.0027** | âm |
| 6 | `collapse_penalty=1.0` | fitness thưởng cho gộp cụm | **0.0000** | không kích hoạt |
| 7 | `final_collapse_guard=true` | sập cụm ở bước tinh chỉnh cuối | **0.0000** | không kích hoạt |
| 8 | `fitness_horizon=5, generations=20` | fitness một bước không thấy xu hướng gộp cụm | **−0.0016** | trung tính |

Biến thể 6 và 7 cho kết quả **bit-identical** với baseline. Tôi đã kiểm tra riêng rằng
code có hoạt động: `repair_collapsed` đưa một ví dụ 2 cụm về đúng 3 cụm. Nguyên nhân thật
là **trên toàn tập dev, pipeline không bao giờ sập cụm** — số cụm quan sát được bằng đúng k
ở cả 10 bộ, kể cả hai bộ k=8. Nên không có gì để phạt hoặc để sửa.

Điều này cũng phát hiện một sai sót trong thiết kế ban đầu của tôi: biến thể 6 nhằm phạt
sập cụm **tại bước chấm fitness**, nhưng fitness chỉ chạy **một** bước PFCM, còn gộp cụm
chỉ xuất hiện sau **100 vòng** của bước tinh chỉnh cuối. Phạt ở chỗ không có hiện tượng là
vô ích. Đó là lý do tôi thêm biến thể 7 và 8.

---

## 3. Vì sao mọi can thiệp đều null: trần của không gian tìm kiếm

### 3.1. Fitness thực ra **có** khớp chất lượng, chỉ là trần quá thấp

Lấy 200 nhiễm sắc thể đúng theo cách quần thể được sinh, rồi với mỗi cái chạy `solve_pfcm`
tới hội tụ. Spearman giữa điểm fitness (là loss) và ARI:

| Dataset | ρ(fitness, ARI) | ρ(fitness, loss hội tụ) | ARI mà fitness chọn | ARI tốt nhất có trong 200 mẫu | Trần |
|---|---:|---:|---:|---:|---:|
| pima | −0.513 | +0.845 | 0.1030 | 0.1167 | 0.014 |
| rice | −0.473 | +0.829 | 0.6842 | 0.6938 | 0.010 |
| wifi | −0.396 | +0.849 | 0.8529 | 0.8731 | 0.020 |

Fitness là loss, nên tương quan **âm** với ARI nghĩa là giảm loss thì ARI tăng — fitness
**đúng hướng**. Và ρ(fitness một bước, loss hội tụ) = +0.83…+0.85, nên cách chấm một bước
là một proxy tốt, không phải vấn đề.

Vấn đề là **trần**: một bộ tìm kiếm *hoàn hảo* trên quần thể đó cũng chỉ hơn baseline
0.010–0.020 ARI. Trên 4 bộ Gaussian với 400 mẫu, trần là 0.072 / 0.035 / 0.016 / 0.012.

### 3.2. Baseline đã đạt oracle của chính nó

Quét fuzzifier với tâm DPC, không có tìm kiếm nào:

| Dataset | k | w=1.1 | w=1.5 | w=2.0 | w=3.0 | w=5.0 | oracle |
|---|---:|---:|---:|---:|---:|---:|---:|
| wifi | 4 | 0.872 | 0.874 | **0.365** | 0.362 | 0.361 | 0.874 |
| rice | 2 | 0.688 | 0.685 | 0.674 | 0.636 | 0.594 | 0.688 |
| pima | 2 | 0.093 | 0.103 | 0.103 | 0.095 | 0.084 | 0.103 |
| gauss nc4 L5 sep3.0 | 4 | 0.762 | 0.743 | 0.501 | 0.425 | 0.418 | 0.763 |
| gauss nc3 L2 sep1.5 | 3 | 0.281 | 0.318 | **0.344** | 0.332 | 0.332 | 0.344 |

Fuzzifier tốt nhất **khác nhau theo từng bộ** và biên độ rất lớn (wifi: 0.365 ↔ 0.874).
Trung bình oracle trên 10 bộ dev là **0.5464**; baseline DP-GA-PFCM đạt **0.5463**.

Đây là một phát biểu **tích cực** về bài báo: đóng góp mà bài báo tuyên bố — để GA tự tìm
(a, b, w, η) cho từng dataset — **đã hoạt động đúng như vậy**. Và chính vì vậy mà không còn
chỗ để cải thiện bằng cách sửa GA.

### 3.3. Cơ chế phá chất lượng là gộp cụm, do fuzzifier điều khiển

Cột số cụm trong phép quét giải thích mọi thứ: ở `wifi`, `w=2` làm 4 cụm gộp còn **2**;
ở `gauss nc8 L5`, `w=3` và `w=5` làm 8 cụm gộp còn **2**. Hàm mục tiêu mờ **thưởng** cho
việc này, vì ít cụm và chặt hơn thì tổng bình phương nhỏ hơn.

---

## 4. Phát hiện dùng được: ràng buộc đúng k cụm cho việc chọn mô hình

Hệ quả của 3.3: **mọi tiêu chí không dùng nhãn đều thiên về nghiệm đã gộp cụm.** Đo trên
10 bộ dev, chọn trong 6 giá trị w:

| Tiêu chí chọn | ARI trung bình |
|---|---:|
| Cứ dùng `w=2` | 0.4390 |
| Calinski–Harabasz, không ràng buộc | **0.4157** |
| Davies–Bouldin, không ràng buộc | 0.4158 |
| Silhouette, không ràng buộc | 0.4159 |
| Độ ổn định khi lấy lại mẫu, không ràng buộc | 0.4418 |
| **Calinski–Harabasz + ràng buộc đúng k cụm** | **0.5339** |
| **Độ ổn định + ràng buộc đúng k cụm** | **0.5398** |
| oracle (biết nhãn) | 0.5464 |

Ba chỉ số nội tại không ràng buộc đều **tệ hơn** việc không chọn gì. Độ ổn định không ràng
buộc gần như vô dụng: nó thắng lớn ở `wifi` (+0.51) nhưng thua nặng ở k lớn
(`gauss nc8 L5`: 0.234 so với 0.516 của `w=2`), vì nghiệm đã gộp cụm là nghiệm **dễ tái
lập nhất**.

Ràng buộc "chỉ xét nghiệm cho ra đúng k cụm" loại bỏ đúng đường thoát đó. Vì k **được cho
trước** trong bài toán này (`paper_k`), ràng buộc này **không dùng nhãn**. Nó đưa độ ổn
định từ 0.4418 lên **0.5398**, tức **98.8% của oracle**.

---

## 5b. Kết quả chính thức: 30 seed và Wilcoxon ghép cặp

Mục 5 dưới đây là vòng 5 seed. Sau đó tôi chạy lại **30 seed** trên cả 10 bộ (300 lần chạy
mỗi phương pháp) và kiểm định đúng cách. Đây là số nên dùng khi công bố.

| Dataset | ARI GA baseline | ARI phương pháp rẻ | Δ | Wilcoxon p (thô) | p sau Holm |
|---|---:|---:|---:|---:|---:|
| **iris** | 0.5488 ± 0.143 | **0.7484 ± 0.027** | **+0.1997** | 2.2e-06 | 1.4e-05 ✱ |
| **breast_tissue** | 0.2995 ± 0.039 | **0.4310 ± 0.007** | **+0.1315** | 1.8e-06 | 1.4e-05 ✱ |
| seed | 0.7052 ± 0.002 | 0.7056 ± 0.004 | +0.0004 | 0.99 | 0.99 |
| compound | 0.5343 ± 0.016 | 0.5300 ± 0.007 | −0.0043 | 6.8e-03 | 2.0e-02 ✱ |
| glass | 0.1631 ± 0.018 | 0.1548 ± 0.000 | −0.0083 | 8.2e-03 | 2.0e-02 ✱ |
| flame | 0.4753 ± 0.014 | 0.4649 ± 0.000 | −0.0104 | 7.0e-04 | 2.8e-03 ✱ |
| jain | 0.5768 ± 0.004 | 0.5507 ± 0.053 | −0.0261 | 1.5e-06 | 1.4e-05 ✱ |
| aggregation | 0.7064 ± 0.010 | 0.6761 ± 0.000 | −0.0304 | 1.7e-06 | 1.4e-05 ✱ |
| wine | 0.8525 ± 0.013 | 0.8160 ± 0.013 | −0.0365 | 2.2e-06 | 1.4e-05 ✱ |
| **ecoli** | **0.5061 ± 0.084** | 0.3651 ± 0.000 | **−0.1410** | 2.6e-08 | 2.6e-07 ✱ |
| **Trung bình** | **0.5368** | **0.5443** | **+0.0075** | | |

(✱ = có ý nghĩa ở mức 0.05 sau hiệu chỉnh Holm cho 10 so sánh. Trung bình bài báo: 0.5581.)

**Kiểm định ở mức dataset** — đây là đơn vị phân tích đúng, như chính ghi chú nghiên cứu
của dự án yêu cầu ("không coi 30 seed của cùng một dataset là 30 dataset độc lập"):

> Wilcoxon signed-rank trên 10 trung bình mỗi dataset: **p = 0.4316**.
> Phương pháp rẻ tốt hơn ở **3/10** dataset.

**Kết luận thống kê: hai phương pháp không phân biệt được ở mức dataset** (p = 0.43), dù
chênh lệch trên từng dataset gần như đều có ý nghĩa (9/10 bộ) — vì phương sai trong mỗi
dataset rất nhỏ. Đây đúng là tình huống mà hai mức kiểm định cho hai câu trả lời khác nhau,
và câu trả lời ở mức dataset mới là câu được phép dùng để so sánh hai phương pháp.

Chi phí giữ nguyên như vòng 5 seed: 8080 lần chấm fitness và 2.60 s so với **54** lần giải
PFCM và **0.80 s**.

---

## 5. Xác nhận trên 10 bộ của bài báo (vòng 5 seed, giữ lại để đối chiếu)

So baseline DP-GA-PFCM với phương pháp rẻ: 6 giá trị w từ cùng tâm DPC, chọn bằng độ ổn
định có ràng buộc đúng k cụm. 5 seed ghép cặp, không dùng nhãn ở cả hai bên.

| Dataset | k | ARI bài báo | ARI GA baseline | ARI phương pháp rẻ | Δ |
|---|---:|---:|---:|---:|---:|
| **iris** | 3 | 0.774 | 0.5326 ± 0.143 | **0.7408 ± 0.026** | **+0.2082** |
| **breast_tissue** | 6 | 0.370 | 0.3130 ± 0.027 | **0.4290 ± 0.008** | **+0.1160** |
| seed | 3 | 0.730 | 0.7049 ± 0.000 | 0.7094 ± 0.010 | +0.0045 |
| compound | 6 | 0.555 | 0.5342 ± 0.004 | 0.5303 ± 0.008 | −0.0039 |
| flame | 2 | 0.482 | 0.4696 ± 0.017 | 0.4649 ± 0.000 | −0.0047 |
| glass | 7 | 0.183 | 0.1652 ± 0.009 | 0.1548 ± 0.000 | −0.0104 |
| aggregation | 7 | 0.695 | 0.7064 ± 0.009 | 0.6760 ± 0.001 | −0.0304 |
| wine | 3 | 0.865 | 0.8562 ± 0.014 | 0.8237 ± 0.014 | −0.0326 |
| jain | 2 | 0.575 | 0.5784 ± 0.004 | 0.5013 ± 0.126 | −0.0771 |
| **ecoli** | 8 | 0.352 | **0.5525 ± 0.072** | 0.3651 ± 0.000 | **−0.1873** |
| **Trung bình** | | **0.558** | **0.5413** | **0.5395** | **−0.0018** |

Ghép cặp (n = 50): mean **−0.0018**, SD 0.1188; phương pháp rẻ tốt hơn 15 cặp, GA tốt hơn
30 cặp. **Hai phương pháp không phân biệt được về chất lượng trung bình.**

Chi phí:

| | Số lần giải | Thời gian / run |
|---|---:|---:|
| DP-GA-PFCM | 8080 lần chấm fitness | 2.58 s |
| Phương pháp rẻ | **54** lần giải PFCM | **0.81 s** |
| Tỷ lệ | **150× ít hơn** | **3.2× nhanh hơn** |

### Giải thích hai ngoại lệ lớn

- **Iris +0.208.** Baseline GA kẹt ở nghiệm gộp hai lớp trong 3/5 run (purity 0.667). Phép
  quét luôn xét được vùng w mà GA không tới, nên không bị kẹt. Độ lệch chuẩn giảm từ 0.143
  xuống 0.026, tức ổn định hơn nhiều.
- **Ecoli −0.187.** Baseline GA cho **4 cụm** khi k=8, và trên Ecoli việc gộp cụm lại **có
  lợi** cho ARI vì các lớp rất mất cân bằng. Ràng buộc đúng k cụm của tôi **cấm** đúng cái
  nghiệm có lợi đó. Đây là một hạn chế thật của ràng buộc này, không phải nhiễu: SD của
  phương pháp rẻ trên Ecoli là 0.000.

---

## 6. Những điều KHÔNG được suy ra

- **Không được nói tôi đã cải thiện DP-GA-PFCM.** Về ARI trung bình thì không: −0.0018 trên
  test, trong nhiễu. Điều đã chứng minh là một phương pháp **rẻ hơn 150 lần** đạt chất
  lượng tương đương, cộng với hai dataset được cải thiện lớn.
- **Không được nói GA là vô dụng.** Nó đạt oracle của không gian tham số của nó, và thắng
  phương pháp rẻ ở 30/50 cặp.
- **Không được dùng con số 5 seed để công bố** — đã có 30 seed ở mục 5b, dùng số đó.
  Và không được dẫn p-value của từng dataset như bằng chứng rằng một phương pháp tốt hơn:
  ở mức dataset, p = 0.4316, tức **không phân biệt được**.
- **Ràng buộc đúng k cụm chỉ dùng được khi k được cho trước.** Với bài toán tự xác định số
  cụm, nó không áp dụng được, và kết quả Ecoli cho thấy nó có thể cấm mất nghiệm tốt.
- **Chưa thử:** ensemble/consensus nhiều lần chạy, và hướng AF-NKGA (đổi hẳn biểu diễn
  nghiệm). Dữ liệu ở mục 3 nói rằng muốn tăng chất lượng đáng kể thì phải **ra khỏi họ mô
  hình này**, vì trần của nó đã bị baseline chạm tới.

---

## 7. Thay đổi code

Mọi thay đổi đều **mặc định giữ nguyên hành vi baseline**; đã xác nhận Iris vẫn cho
0.6667 / 0.4290 / 0.5904 và 18/18 test đạt sau mỗi lần sửa.

| File | Cờ config mới | Mặc định |
|---|---|---|
| `common/density_peak.py` | `density_mode`, `ks_neighbors`, `candidate_pool` | `gaussian`, 7, 4 |
| `common/meta_pfcm.py` | `fitness` thêm `ch`/`db`/`silhouette`; `init_mode`; `collapse_penalty`; `collapse_repair`; `fitness_horizon`; `final_collapse_guard` | giữ nguyên |
| `common/runner.py` | kiểm tra hợp lệ cho các cờ trên | — |

| Script | Nội dung |
|---|---|
| `scripts/screen.py` | sàng lọc một biến thể trên tập dev mở rộng |
| `scripts/probe_surrogate.py` | tương quan fitness ↔ chất lượng, và trần không gian tìm kiếm |
| `scripts/probe_wsweep.py` | quét fuzzifier với tâm DPC, không tìm kiếm |
| `scripts/probe_select_k.py` | so sánh tiêu chí chọn mô hình, có và không ràng buộc k |
| `scripts/probe_stability.py` | chọn theo độ ổnh định khi lấy lại mẫu |
| `scripts/confirm_test.py` | xác nhận trên 10 bộ của bài báo |

Tập dev đã được mở rộng hai lần, mỗi lần công bố lý do **trước** khi chạy biến thể trên
phần mới: (a) thêm Gaussian có điều khiển độ chồng lấn, vì 4 bộ dev thật đều bão hòa
(rice 0.684, wifi 0.856) hoặc gần sàn (pima 0.104, room_occupancy 0.017); (b) thêm ca k=6
và k=8, vì dev chỉ có k ≤ 4 còn test có k = 6, 7, 8 và gộp cụm là lỗi phụ thuộc k.
Room Occupancy bị loại khỏi vòng sàng lọc vì 20560 mẫu ở 78 s/run và ARI 0.017 không mang
tín hiệu; nó vẫn nằm trong vòng xác nhận của H1.
