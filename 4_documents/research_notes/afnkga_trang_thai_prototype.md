# AF-NKGA — trạng thái prototype

Ngày: 2026-11-05. Triển khai thiết kế trong
[kien_truc_nghien_cuu_adaptive_fuzzy_nkga.md](kien_truc_nghien_cuu_adaptive_fuzzy_nkga.md).

## 1. Kết luận trong một đoạn

Phần máy móc **đã đúng và đã được kiểm chứng**: 8 property test đạt, gồm partition
crossover trả về đúng nghiệm tốt nhất trong 2^q tổ hợp (đối chiếu bằng liệt kê vét cạn) và
delta-evaluation khớp chính xác với hai lần chấm đầy đủ. Nhưng **hàm mục tiêu tôi đặt ra
thì sai**, và tôi có bằng chứng dứt khoát: chạy local search **bắt đầu từ chính nhãn thật**
thì nó **rời khỏi nhãn thật** để hạ fitness — trên Pima từ 0.3134 xuống 0.1133 bằng cách
tách 2 lớp thành **43 cụm**. Vậy nhãn thật nằm rất xa tối ưu của hàm mục tiêu này.

Hệ quả: prototype hiện **chưa kiểm nghiệm được giả thuyết trung tâm** của ghi chú (hướng
dẫn fuzzy làm giảm hiện tượng **gộp** cụm), vì nó mắc lỗi **ngược lại** — phân mảnh quá mức.

## 2. Nguồn gốc, và điều không được tuyên bố

Thiết kế **lấy cảm hứng từ** NK hybrid GA for clustering của Tinos, Zhao, Chicano &
Whitley (IEEE TEC; preprint [arXiv:2402.03813](https://arxiv.org/abs/2402.03813)).

Trong session này tôi **đọc được source code đã công bố**
([github.com/rtinos/NKGAclust](https://github.com/rtinos/NKGAclust)) nhưng **không đọc được
bài báo**, vì `arxiv.org` bị chặn. Từ source tôi lấy hai sự thật cụ thể:

- nghiệm là vector nhãn, nhãn 0 nghĩa là nhiễu;
- ba ngưỡng khoảng cách lấy từ quy tắc ba sigma trên khoảng cách của các cạnh, trong `nk.h`
  đặt là `dt0 = mean`, `dt1 = mean + 2sd`, `dt2 = mean + sd` (lưu ý `dt2 < dt1`, không theo
  thứ tự tên gọi).

**Factor trên mỗi cạnh trong `afnkga/model.py` là định nghĩa của riêng tôi. Nó KHÔNG phải
NKCV2 và không được trình bày như NKCV2** — tôi chưa đọc được định nghĩa đầy đủ của NKCV2.
Phần `comp_fi` mà tôi đọc được cho thấy mỗi factor bị chặn bởi `rho[j]`, và tôi giữ lại cận
đó để chuẩn hóa `S_NK` vẫn là một hằng số của dữ liệu.

Local scaling theo Zelnik-Manor & Perona, Self-Tuning Spectral Clustering (NIPS 2004):
`sigma_i` là khoảng cách tới láng giềng thứ `ks`.

## 3. Đã kiểm chứng những gì

`tests/test_afnkga.py`, 8 test, tất cả đạt, chạy với `-W error::RuntimeWarning`:

| Tính chất (mục 5 của ghi chú) | Test | Kết quả |
|---|---|---|
| 1. Bất biến khi hoán vị nhãn dương | `test_label_permutation_invariance` | đạt, cả λ=0 và λ=0.5 |
| 3. Delta-evaluation đúng | `test_delta_matches_full_evaluation` | đạt, 40 phép thử × 2 mức λ, sai số < 1e-12 |
| 4. PX đúng với fitness mới | `test_partition_crossover_is_optimal_over_components` | đạt, đối chiếu liệt kê vét cạn 2^q |
| 5. Không né chi phí fuzzy qua noise | `test_noise_cannot_dodge_fuzzy_cost` | đạt, mọi cạnh |
| Chuẩn hóa nhãn giữ nguyên fitness | `test_canonical_preserves_fitness` | đạt |
| Chuẩn hóa nhãn làm mỗi nhãn liên thông | `test_canonical_makes_labels_connected` | đạt |
| Local search không làm xấu đi | `test_local_search_is_monotone` | đạt |
| Chặn cấu hình sai | `test_configuration_guards` | đạt |

### Hai lỗi do test phát hiện

1. **Chọn láng giềng hoàn toàn vô nghĩa.** Tôi viết `np.argsort(dist + np.eye(n)*np.inf)`
   để loại đường chéo. Nhưng `0 * inf = nan`, nên **mọi ô ngoài đường chéo thành NaN** và
   thứ tự sắp xếp là rác; một điểm còn có thể thành láng giềng của chính nó. Chỉ có một
   `RuntimeWarning` báo. Đã sửa bằng `np.fill_diagonal(masked, np.inf)`, và thêm một
   `ValueError` chặn self-loop để lỗi tương tự không còn im lặng được.
2. **Test PX ban đầu không chạy được.** Hai cha mẹ ngẫu nhiên độc lập khác nhau gần như ở
   mọi vị trí, cho 16 thành phần, tức 65536 tổ hợp phải liệt kê. Đã sửa: chỉ nhiễu 5 đỉnh
   so với cha, nên q nhỏ và liệt kê vét cạn được.

Lỗi thứ nhất là loại lỗi mà nếu không có property test thì sẽ lặng lẽ làm sai toàn bộ kết
quả mà vẫn "chạy được".

## 4. Ablation trên tập dev (Pima, Wifi, 3 run)

| Biến thể | Đồ thị | Fuzzy | Khởi tạo | ARI | Số cụm |
|---|---|---|---|---:|---:|
| A0 | gốc | tắt | ngẫu nhiên | 0.1348 | 156.8 |
| A1 | gốc | tắt | từ bank | **0.3293** | 66.8 |
| A2 | thích nghi | tắt | từ bank | 0.2340 | 37.2 |
| A3 | gốc | **bật** | từ bank | **0.3318** | 67.2 |
| A4 | thích nghi | **bật** | từ bank | 0.2340 | 37.2 |

k thật là 2 (Pima) và 4 (Wifi). **Số cụm tìm được là 37–157.**

Hai cặp có kiểm soát mà ghi chú yêu cầu — cùng đồ thị, cùng bank, cùng quần thể khởi tạo
bit-identical (`init_local_search=False`), chỉ bật/tắt λ:

| Cặp | λ tắt → λ bật | Δ |
|---|---|---:|
| A1 → A3 | 0.3293 → 0.3318 | **+0.0025** |
| A2 → A4 | 0.2340 → 0.2340 | **+0.0000** |

**Hướng dẫn fuzzy gần như không có tác dụng lên phân hoạch**, mặc dù nó hạ fitness rõ rệt
(Wifi: 0.1220 → 0.0731). Tức là nó đổi giá trị hàm mục tiêu nhưng không đổi nghiệm
arg-min về phía tốt hơn.

Đồ thị thích nghi **làm xấu đi**: A1→A2 −0.0953, A3→A4 −0.0978.

Khởi tạo từ bank là yếu tố duy nhất giúp rõ rệt: A0→A1 **+0.1945**.

So với mốc baseline trên cùng hai bộ: DP-GA-PFCM cho Pima 0.1023 và Wifi 0.8500, còn
AF-NKGA tốt nhất cho Pima 0.1000 và Wifi 0.5636. **Prototype còn kém baseline rất xa trên
Wifi.**

## 5. Chẩn đoán: hàm mục tiêu sai, không phải bộ tìm kiếm

Hai phép kiểm tra loại trừ các nguyên nhân khác.

**Không phải do đồ thị rời.** Số thành phần liên thông của đồ thị NK là **1** ở mọi K thử
(3, 5, 8, 12, 20) trên cả Pima và Wifi. Nên `canonical` không bị buộc phải tách vì đồ thị
đứt.

**Là do hàm mục tiêu.** Chấm fitness của chính nhãn thật, rồi chạy local search từ đó:

| Dataset | λ | F(nhãn thật) | F sau local search | Số cụm sau | ARI sau |
|---|---:|---:|---:|---:|---:|
| pima | 0.0 | 0.3134 | **0.1133** | 43 | 0.2755 |
| pima | 0.4 | 0.1881 | **0.0680** | 43 | 0.2755 |
| wifi | 0.0 | 0.1441 | **0.1236** | 23 | 0.8941 |
| wifi | 0.4 | 0.0865 | **0.0742** | 23 | 0.8941 |

Local search **rời khỏi nhãn thật** trong mọi trường hợp, và hạ fitness tới 64% trên Pima.
Nghĩa là nhãn thật không phải nghiệm tốt theo hàm mục tiêu này, thậm chí không phải cực
tiểu địa phương. Bộ tìm kiếm đang làm đúng việc của nó; thứ nó được yêu cầu tối thiểu hóa
là sai.

Lưu ý: con số ARI 0.8941 ở Wifi **không phải một kết quả dùng được** — nó có được bằng
cách khởi tạo từ nhãn thật, tức là đã dùng nhãn.

**Nguyên nhân cụ thể trong factor của tôi.** Nó chỉ ràng buộc các cặp láng giềng trực tiếp:
"cùng nhãn mà xa nhau" bị phạt, "khác nhãn mà gần nhau" bị phạt. Không có số hạng nào
thưởng cho việc một cụm giữ được kích thước lớn. Vì vậy một phân hoạch vỡ thành nhiều đốm
nhỏ nhưng mỗi đốm đều nhất quán **cục bộ** thì có chi phí gần bằng 0. Với K=3, mỗi điểm chỉ
có vài láng giềng nên áp lực giữ cụm lớn càng yếu.

Bản NK gốc hẳn cân bằng việc này theo cách khác, rất có thể qua trọng số mật độ `rho_j` và
logic ngưỡng trong `comp_fi` mà tôi chưa đọc được.

## 6. Việc cần làm tiếp, theo thứ tự

1. **Đọc toàn văn arXiv:2402.03813** để lấy định nghĩa NKCV2 thật. Đây là việc chặn mọi
   việc khác: không có nó thì tôi đang đoán cách cân bằng tách/gộp. Cần mở `arxiv.org`
   trong Network access của environment.
2. **Trước mắt, thêm một số hạng chống phân mảnh** vào factor và đo lại. Ứng viên: cho chi
   phí của "khác nhãn mà gần nhau" tăng theo `rho`, hoặc đưa chi phí theo số nhãn hoạt động
   ở mức cạnh (ghi chú cảnh báo không thêm penalty **toàn cục** theo số cụm vì nó phá tính
   độc lập của các component PX, nên phải là số hạng **trên cạnh**).
3. **Quét K.** K=3 là mức NKGAclust khuyến nghị cho NKCV2 gốc, không nhất thiết đúng cho
   factor của tôi. Số cụm giảm từ 66.8 (đồ thị gốc) xuống 37.2 (thích nghi) cho thấy mật độ
   đồ thị ảnh hưởng mạnh tới mức phân mảnh.
4. **Chỉ sau khi số cụm về đúng thang** thì mới đánh giá được λ. Hiện λ chỉ đổi giá trị hàm
   mục tiêu, không đổi chất lượng, nên RQ1 của ghi chú vẫn chưa được trả lời.

## 7. File

| File | Nội dung |
|---|---|
| `2_models_code/afnkga/model.py` | đồ thị thích nghi, bằng chứng fuzzy theo cặp, fitness, delta, chuẩn hóa nhãn |
| `2_models_code/afnkga/ga.py` | partition crossover, mutation reclassify/merge/split, local search, vòng GA |
| `2_models_code/afnkga/run.py` | CLI ablation A0–A4 |
| `2_models_code/tests/test_afnkga.py` | 8 property test |
| `4_documents/research_notes/data/afnkga_dev.jsonl` | kết quả thô ablation |

Prototype **không** thay đổi bất kỳ phần nào của pipeline DP-GA-PFCM; nó là một package
riêng. Toàn bộ 26 test cũ của dự án vẫn đạt.
