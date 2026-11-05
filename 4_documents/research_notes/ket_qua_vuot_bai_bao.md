# Mục tiêu vượt bài báo — kết quả và vị trí hiện tại

Ngày: 2026-11-05. Mục tiêu: ARI trung bình trên 10 bộ của bài báo phải vượt **0.5581**
(Table 12, cột A2 của [DOI 10.1016/j.jestch.2023.101525](https://doi.org/10.1016/j.jestch.2023.101525)).

## 1. Kết luận: chưa đạt

30 seed trên cả 10 bộ, ngân sách bài báo (population 80, 100 thế hệ), 900 lần chạy mô hình.

| Phương pháp | ARI trung bình | Δ so bài báo | Thắng | p (mức dataset, n=10) |
|---|---:|---:|---:|---:|
| **Bài báo (A2)** | **0.5581** | — | — | — |
| w-sweep (chọn fuzzifier, không GA) | 0.5443 | −0.0138 | 2/10 | 0.1055 |
| w-pinned GA (đề xuất mới) | 0.5395 | −0.0186 | 3/10 | 0.1309 |
| Baseline DP-GA-PFCM tái tạo | 0.5368 | −0.0213 | 3/10 | 0.1602 |

**Cả ba đều dưới bài báo**, và không cái nào khác biệt có ý nghĩa ở mức dataset
(p = 0.11–0.16). Phát biểu trung thực nhất: ba phương pháp **không phân biệt được** với số
công bố của bài báo về mặt thống kê, nhưng **đều thấp hơn về con số**. Chưa vượt.

## 2. Phương pháp mới đã thử: w-pinned GA

Dựa trên hai phát hiện đã đo của dự án:

- Fuzzifier quyết định việc gộp cụm, và biên độ rất lớn (Wifi: ARI 0.365 với 2 cụm ở
  `w=2` so với 0.872 với 4 cụm ở `w=1.1`, cùng tâm DPC).
- Ràng buộc "chỉ xét nghiệm cho ra đúng k cụm" làm tiêu chí chọn mô hình không dùng nhãn
  hoạt động được: độ ổn định khi lấy lại mẫu từ 0.4418 lên **0.5398** trên tập dev, tức
  98.8% của oracle biết nhãn.

**Thiết kế:** chọn `w` bằng độ ổn định có ràng buộc đúng k cụm (không dùng nhãn), rồi ghim
`w` tại đó và để GA dồn toàn bộ ngân sách vào tâm cụm và a, b, η.

**Sàng lọc trên tập dev:** +0.0033 ARI (26 tốt hơn / 20 xấu hơn trên 50 cặp), và SD giảm
rõ. Mức tăng nhỏ, chưa có ý nghĩa, nhưng đủ qua quy tắc quyết định nên được chạy test.

**Trên tập test, Wilcoxon ghép cặp từng dataset (n=30, hiệu chỉnh Holm):**

| Dataset | Δ so baseline | Holm p |
|---|---:|---:|
| **iris** | **+0.1517** | 9.1e-04 ✱ |
| **glass** | **+0.0218** | 2.1e-02 ✱ |
| **aggregation** | **+0.0092** | 3.4e-04 ✱ |
| compound | +0.0039 | 1.00 |
| seed | +0.0000 | 1.00 |
| breast_tissue | −0.0024 | 1.00 |
| jain | −0.0024 | 1.00 |
| flame | −0.0051 | 0.29 |
| wine | −0.0064 | 0.30 |
| **ecoli** | **−0.1430** | 9.3e-08 ✱ |

Ở mức dataset: +0.0028, thắng 4/10, **p = 0.82**. Tức là **một sự đánh đổi, không phải cải
tiến**: nó sửa được Iris (0.549 → 0.701) nhưng mất Ecoli (0.506 → 0.363).

Lý do mất Ecoli đã rõ và đã được ghi từ trước: baseline trên Ecoli cho **4 cụm khi k=8**, và
trên bộ này việc gộp cụm **vô tình có lợi** cho ARI vì các lớp rất mất cân bằng. Ràng buộc
đúng k cụm **cấm** đúng nghiệm có lợi đó. Đây là hạn chế thật của ràng buộc, không phải nhiễu.

Mặt được không nằm ở trung bình: **SD trung bình giảm từ 0.0342 xuống 0.0249**, và trên Iris
từ 0.143 xuống 0.115. Chi phí 3.42 s so với 2.61 s mỗi lần chạy.

## 3. Những chỗ ĐÃ vượt bài báo, theo từng dataset

Dù trung bình chưa vượt, có bốn bộ vượt rõ với 30 seed:

| Dataset | Bài báo | Tốt nhất của tôi | Δ | Phương pháp |
|---|---:|---:|---:|---|
| **ecoli** | 0.352 | **0.5061** | **+0.154** | baseline (gộp cụm có lợi) |
| **breast_tissue** | 0.370 | **0.4310** | **+0.061** | w-sweep |
| **aggregation** | 0.695 | **0.7157** | **+0.021** | w-pinned GA |
| **glass** | 0.183 | **0.1849** | **+0.002** | w-pinned GA |

Và oracle chọn phương pháp tốt nhất cho từng dataset cho **0.5735 > 0.5581**. Nghĩa là **tổ
hợp vượt bài báo có tồn tại trong các nghiệm tôi đã sinh ra** — nhưng chọn theo ARI là dùng
nhãn, nên không được tính. Đây là biên trên của việc "chọn đúng", không phải một kết quả.

## 4. Vì sao mức tăng lớn không có, và điều này có nghĩa gì

Tám can thiệp trước đó (xem [thuc_nghiem_cai_tien.md](thuc_nghiem_cai_tien.md)) đều null,
cộng consensus clustering (−0.006 đến −0.008 trên dev) và w-pinned GA (+0.0028 trên test,
p=0.82). Tổng cộng **mười một can thiệp**, không cái nào tăng ARI trung bình đáng kể.

Nguyên nhân đã đo được, không phải suy đoán:

1. **Baseline đã nằm ở trần không gian tham số của nó.** Trên 10 bộ dev, baseline đạt
   0.5463 còn oracle biết nhãn chọn fuzzifier tốt nhất từng bộ đạt 0.5464.
2. **Trần của cả giai đoạn tìm kiếm là 0.012–0.072 ARI**, đo bằng cách lấy 200–400 nhiễm
   sắc thể và so nghiệm fitness chọn với nghiệm tốt nhất có trong mẫu.
3. **Mọi tiêu chí không dùng nhãn đều thiên về nghiệm đã gộp cụm** (CH, DB, silhouette, độ
   ổn định). Ràng buộc đúng k cụm sửa được điều đó, nhưng chính nó lại cấm nghiệm gộp cụm
   vô tình có lợi trên Ecoli.

**Giải thích khả dĩ nhất cho khoảng cách còn lại là chính các khoảng trống của bài báo**, đã
ghi trong [literature_review.md](literature_review.md) và `ASSUMPTIONS.md`:

- Step 6 ghi nguyên văn *"minimize the within-cluster sum of squared errors using PFCM
  algorithm (Eq. (6)"* — ba khái niệm khác nhau trong một câu, nên **không ai biết tác giả
  dùng fitness nào**.
- Bài báo **không cho miền tìm kiếm** cho a, b, w, η; miền `w ∈ [1.1, 5]` là tự đặt, và
  chính miền này quyết định kết quả.
- Mutation rate Table 5 ghi 0.1 nhưng phần tuning chỉ thử 0.01 và 0.03.
- Table 11 ghi Glass/A1 = 0.066 còn Table 6 ghi 0.566 — gần như chắc là lỗi in.

Tức là **"vượt số công bố" và "vượt thuật toán của tác giả" không phải cùng một việc**, vì
cấu hình thật của tác giả chưa biết. Tôi không có cách nào xác nhận mình đang so với đúng
thuật toán của họ.

## 5. Ba lựa chọn tiếp theo, kèm đánh giá thật về khả năng thành công

**(a) Xin cấu hình gốc từ tác giả.** Email tác giả tương ứng xin fitness và bounds. Đây là
việc có khả năng thay đổi kết quả nhiều nhất với chi phí thấp nhất. Nếu fitness thật khác
cách đọc hiện tại, toàn bộ bảng có thể dịch chuyển.

**(b) Đổi họ mô hình (AF-NKGA).** Số liệu ở mục 4 nói rõ: muốn tăng đáng kể thì phải ra khỏi
họ DP-metaheuristic-PFCM. Prototype đã có, máy móc đã kiểm chứng (8 property test, PX đúng
trên 2^q, delta chính xác), nhưng hàm mục tiêu còn sai: local search bắt đầu từ chính nhãn
thật lại rời khỏi nhãn thật, tách 2 lớp thành 43 cụm trên Pima. Việc chặn đường là **đọc
toàn văn arXiv:2402.03813** để lấy định nghĩa NKCV2 thật; `arxiv.org` hiện bị chặn trong
environment này.

**(c) Đổi mục tiêu công bố cho khớp với bằng chứng.** Những gì đã chứng minh được, và đều có
giá trị khoa học:
- Ba kết quả âm có kiểm soát, giải thích được cơ chế, cho thấy bộ tối ưu **không** phải điểm
  nghẽn của dòng DP-GA-PFCM.
- Ràng buộc đúng k cụm đáng **+0.10 ARI** cho việc chọn mô hình không dùng nhãn, và nếu
  không có nó thì mọi chỉ số nội tại đều **tệ hơn** việc không chọn gì.
- Một phương pháp **rẻ hơn 150 lần** đạt chất lượng tương đương baseline.
- Bốn dataset vượt bài báo, trong đó Ecoli +0.154.

Đây là một bài báo về **giới hạn và cách đánh giá đúng** của dòng nghiên cứu này, không phải
bài báo "thuật toán mới tốt hơn". Theo bằng chứng hiện có, đó là phát biểu tôi bảo vệ được.

## 6. Dữ liệu thô

| Nội dung | Vị trí |
|---|---|
| 30 seed, 3 phương pháp, 10 bộ test | `data/final_test.jsonl` (300 bản ghi) |
| Sàng lọc w-pinned trên dev | `data/screen4/` |
| Sàng lọc consensus trên dev | `data/screen3/` |
| Script test cuối | `scripts/final_test.py` |
| Chọn fuzzifier + ghim | `2_models_code/common/consensus.py` |

Không thay đổi hành vi mặc định của pipeline cũ: mọi thứ mới là module riêng hoặc cờ
config mặc định tắt. Cả 4 bộ test của dự án vẫn đạt.
