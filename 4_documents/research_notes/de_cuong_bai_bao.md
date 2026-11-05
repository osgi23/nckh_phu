# Đề cương bài báo — khớp với bằng chứng đã có

Ngày: 2026-11-05. Đây là hướng (3) mà bạn chọn: đổi luận điểm công bố cho khớp với những
gì dự án **đã chứng minh được**, thay vì cố công bố một thuật toán tốt hơn mà số liệu không
hậu thuẫn.

---

## 1. Vì sao phải đổi luận điểm

Sau 11 can thiệp và khoảng 2000 lần chạy mô hình ở ngân sách bài báo, **không can thiệp nào
tăng ARI trung bình đáng kể**, và lý do đã được đo chứ không suy đoán:

- Baseline DP-GA-PFCM **đã nằm ở trần của chính không gian tham số của nó**: trên 10 bộ dev,
  baseline 0.5463 so với oracle biết nhãn 0.5464.
- Trần của **cả giai đoạn tìm kiếm** chỉ là 0.012–0.072 ARI, đo bằng cách lấy 200–400 nhiễm
  sắc thể và so nghiệm mà fitness chọn với nghiệm tốt nhất có trong mẫu.
- Ba phương pháp tốt nhất của tôi đạt 0.5368 / 0.5395 / 0.5443, đều dưới 0.5581 của bài báo
  và **không khác biệt có ý nghĩa** ở mức dataset (p = 0.11–0.16).

Một bài báo tuyên bố "thuật toán mới tốt hơn" sẽ không có bằng chứng. Nhưng bốn kết quả
dưới đây **có** bằng chứng, và chúng trả lời những câu hỏi mà dòng nghiên cứu này đang bỏ
ngỏ.

---

## 2. Tên và luận điểm đề xuất

**Tên tiếng Việt:** Giới hạn của việc tối ưu bằng metaheuristic trong phân cụm mờ lai, và
một tiêu chí chọn mô hình không dùng nhãn cho họ DP-PFCM.

**Tên tiếng Anh:** What Metaheuristic Optimisation Can and Cannot Add to Hybrid Fuzzy
Clustering: A Controlled Study of DP-GA-PFCM.

**Luận điểm chính (một câu):** Trong họ DP-metaheuristic-PFCM, bộ tối ưu **không** phải
điểm nghẽn — hàm mục tiêu và việc chọn tham số mờ mới là, và một tiêu chí không dùng nhãn có
ràng buộc số cụm thu được gần như toàn bộ phần chất lượng mà cả một giải thuật di truyền
8080 lần chấm fitness mang lại, với chi phí nhỏ hơn 150 lần.

**Loại đóng góp:** bài báo thực nghiệm và phương pháp luận, không phải bài báo thuật toán
mới. Đóng góp nằm ở việc **bác bỏ có kiểm soát** một giả định phổ biến, cộng một công cụ
chọn mô hình dùng được.

---

## 3. Bốn đóng góp, kèm bằng chứng tương ứng

### C1. Bộ tối ưu không phải điểm nghẽn — bác bỏ có kiểm soát

Bằng chứng mạnh nhất là một thí nghiệm đổi **một** biến: bật ghi ngược tâm sau bước PFCM
vào nhiễm sắc thể làm GA hạ hàm mục tiêu **tốt hơn 14.1 lần** trên tập dev (0.26% → 3.64%),
và ARI đổi **−0.0004**, nhỏ hơn 1/10 độ dao động giữa các seed.

Củng cố bằng ba quan sát độc lập:
- Ở cùng fitness, cùng tâm DPC khởi tạo, cùng seed và cùng 8080 lần chấm, GA hạ fitness
  0.40% còn PSO 10.27% và SCA 8.42% — chênh khoảng 25 lần — nhưng ARI lần lượt 0.5413 /
  0.5512 / 0.5413, chênh trong 0.01.
- Trên Ecoli, PSO hạ fitness tốt hơn GA **170 lần** mà ARI **xấu hơn 0.18**.
- Tương quan Spearman giữa fitness và ARI là −0.40…−0.51 (đúng hướng), và fitness một bước
  là proxy tốt cho trạng thái hội tụ (+0.83…+0.85). Vậy fitness không sai hướng; **trần
  quá thấp**.

Đây là loại kết quả âm mà văn liệu về metaheuristic clustering hầu như không báo cáo, trong
khi nó quyết định việc có nên đầu tư vào toán tử tìm kiếm hay không.

### C2. Mọi tiêu chí không dùng nhãn đều thiên về nghiệm đã gộp cụm, và ràng buộc số cụm sửa được

Trên 10 bộ dev, chọn trong 6 giá trị fuzzifier:

| Tiêu chí | ARI trung bình |
|---|---:|
| Cứ dùng `w=2`, không chọn gì | 0.4390 |
| Calinski–Harabasz | **0.4157** |
| Davies–Bouldin | 0.4158 |
| Silhouette | 0.4159 |
| Độ ổn định khi lấy lại mẫu | 0.4418 |
| **Calinski–Harabasz + ràng buộc đúng k cụm** | **0.5339** |
| **Độ ổn định + ràng buộc đúng k cụm** | **0.5398** |
| oracle (biết nhãn) | 0.5464 |

Ba chỉ số nội tại **tệ hơn việc không chọn gì**. Cơ chế đã xác định: fuzzifier lớn gộp cụm,
và nghiệm đã gộp vừa chặt hơn vừa dễ tái lập hơn, nên mọi tiêu chí đều thưởng cho nó. Ví dụ
đo được: cùng tâm DPC, `wifi` cho ARI 0.872 với 4 cụm ở `w=1.1` nhưng **0.365 với 2 cụm** ở
`w=2`.

Ràng buộc "chỉ xét nghiệm cho ra đúng k cụm" đáng **+0.10 ARI** và đưa độ ổn định tới
**98.8% của oracle**. Vì k được cho trước trong thiết lập này, ràng buộc không dùng nhãn.

Đây là đóng góp dùng được ngay, và nó cảnh báo một lỗi mà nhiều bài dùng CVI làm tiêu chí
đang mắc.

### C3. Một phương pháp rẻ hơn 150 lần đạt chất lượng tương đương

30 seed, 10 bộ của bài báo:

| | ARI | Số lần giải | Thời gian/run |
|---|---:|---:|---:|
| DP-GA-PFCM | 0.5368 | 8080 lần chấm fitness | 2.60 s |
| Quét 6 fuzzifier + chọn theo độ ổn định có ràng buộc k | 0.5443 | **54** lần giải PFCM | **0.80 s** |

Wilcoxon ở mức dataset (n=10): **p = 0.4316**, không phân biệt được. Từng dataset thì 9/10
có ý nghĩa — đây đúng là trường hợp hai mức kiểm định cho hai câu trả lời khác nhau, và
phần Phương pháp của bài phải nói rõ mức dataset mới là mức được dùng để so sánh hai
phương pháp.

### C4. Bốn dataset vượt số công bố của bài báo gốc

| Dataset | Bài báo | Của tôi | Δ |
|---|---:|---:|---:|
| Ecoli | 0.352 | **0.5061** | **+0.154** |
| Breast Tissue | 0.370 | **0.4310** | **+0.061** |
| Aggregation | 0.695 | **0.7157** | **+0.021** |
| Glass | 0.183 | 0.1849 | +0.002 |

Và một kết quả phải nêu kèm vì nó quan trọng về phương pháp luận: oracle chọn phương pháp
tốt nhất cho từng dataset cho **0.5735 > 0.5581**. Tức tổ hợp vượt bài báo **tồn tại** trong
các nghiệm đã sinh ra, nhưng không có tiêu chí không dùng nhãn nào tôi thử tới được nó. Đây
là một phát biểu về **giới hạn của việc chọn mô hình không giám sát**, và nó định lượng
được: khoảng cách giữa oracle và tiêu chí tốt nhất là 0.5735 − 0.5443 = **0.029**.

---

## 4. Phần phải nói về tính tái tạo của bài gốc

Không trình bày như cáo buộc, mà như điều kiện biên của mọi so sánh:

- Step 6 ghi nguyên văn *"minimize the within-cluster sum of squared errors using PFCM
  algorithm (Eq. (6)"* — ba khái niệm khác nhau trong một câu; Eq.(6) là objective FCM,
  objective PFCM ở Eq.(11), còn "within-cluster SSE" là khái niệm thứ ba. **Không ai biết
  tác giả dùng fitness nào.**
- Bài **không cho miền tìm kiếm** cho a, b, w, η, mà chính miền `w` quyết định kết quả: PSO
  và SCA đẩy `w` xuống đúng cận dưới 1.10 trong 10/10 run trên Iris.
- Mutation rate Table 5 ghi 0.1 nhưng phần tuning chỉ thử 0.01 và 0.03.
- Table 11 ghi Glass/A1 = 0.066 còn Table 6 ghi 0.566 — gần như chắc là lỗi in.

Kết luận phải viết rõ: **"vượt số công bố" và "vượt thuật toán của tác giả" không phải cùng
một việc**, vì cấu hình thật của tác giả chưa biết. Nên bài này báo cáo khoảng cách so với
**số công bố**, kèm toàn bộ giả định của bản tái tạo.

---

## 5. Bố cục đề xuất

1. **Introduction** — dòng DP-metaheuristic-PFCM và giả định ngầm rằng bộ tối ưu tốt hơn thì
   cụm tốt hơn. Nêu luận điểm bác bỏ.
2. **Background** — DPC (Rodriguez & Laio 2014), PFCM (Pal và cộng sự 2005), DP-GA-PFCM
   (Kuo và cộng sự 2023), và CVI làm fitness.
3. **Reproduction and its assumptions** — bảng giả định công khai, bốn điểm ở mục 4, và
   mức khớp: sai lệch tuyệt đối trung bình 0.033 accuracy và 0.060 ARI; bỏ Iris thì
   accuracy còn 0.018.
4. **Protocol** — chia dev/test ở **mức dataset**, quy tắc quyết định đăng ký trước, phân
   biệt tiêu chí dùng nhãn và không dùng nhãn, kiểm định ở mức dataset. Dẫn AAAI 2022 về độ
   nhạy siêu tham số.
5. **Is the optimiser the bottleneck?** — C1, gồm bảng 11 can thiệp và các kết quả âm.
6. **Why label-free model selection fails, and how to fix it** — C2.
7. **A 150x cheaper alternative** — C3.
8. **Per-dataset results and the oracle gap** — C4.
9. **Limitations** — ràng buộc k cụm chỉ dùng được khi k cho trước, và nó cấm nghiệm gộp cụm
   vô tình có lợi trên Ecoli (−0.143). Chỉ 10+4 dataset. Chưa tái tạo case study RFM. Hai
   phương pháp đối chứng (GA-IFWCOM, SCA-FPCOM) chưa triển khai nên 9/11.
10. **Conclusion** — khuyến nghị cho dòng nghiên cứu: báo cáo riêng đóng góp của khởi tạo và
    của bộ tối ưu; không dùng CVI không ràng buộc làm tiêu chí; kiểm định ở mức dataset.

---

## 6. Hình và bảng cần chuẩn bị

| # | Nội dung | Dữ liệu đã có |
|---|---|---|
| H1 | Mức giảm fitness GA/PSO/SCA ở cùng ngân sách | `data/diag_main10.jsonl` |
| H2 | Phân tán fitness ↔ ARI, kèm r theo từng dataset | `data/diag_main10.jsonl` |
| H3 | Đóng góp của DPC so với giai đoạn metaheuristic | `data/diag_main10.jsonl` |
| H4 | ARI theo fuzzifier, kèm số cụm — minh họa cơ chế gộp cụm | `scripts/probe_wsweep.py` |
| B1 | 11 can thiệp và ΔARI trên dev | `data/screen*/` |
| B2 | Tiêu chí chọn mô hình, có và không ràng buộc k | `scripts/probe_select_k.py` |
| B3 | 30 seed, 3 phương pháp, Wilcoxon + Holm, và mức dataset | `data/final_test.jsonl` |
| B4 | Đối chiếu từng dataset với Table 11–13 | `data/final_test.jsonl` |

Toàn bộ số liệu đã có trong repo; không cần chạy lại để viết bài. Việc còn thiếu trước khi
gửi: 30 seed cho các biến thể ở B1 (hiện là 5 seed, đủ sàng lọc nhưng không đủ công bố), và
đọc toàn văn các nguồn còn ở mức metadata trong [literature_review.md](literature_review.md).

---

## 7. Điều bài báo này KHÔNG được nói

- Không nói đã cải tiến DP-GA-PFCM. Về ARI trung bình thì không.
- Không nói DP-GA-PFCM kém hơn PSO/SCA: chênh 0.5413 / 0.5512 / 0.5413 nằm trong dao động
  giữa các seed và chưa kiểm định.
- Không nói fitness của bài báo "sai": điều đã chứng minh là *fitness đang dùng trong bản
  tái tạo không khớp với ARI*, chứ không phải *tác giả đã dùng sai*.
- Không dùng p-value của từng dataset để tuyên bố một phương pháp tốt hơn; ở mức dataset,
  p = 0.4316.
