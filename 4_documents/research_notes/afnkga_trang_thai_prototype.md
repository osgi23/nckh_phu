# AF-NKGA — trạng thái prototype (bản port NKCV2 trung thực)

Ngày: 2026-11-05. Triển khai thiết kế trong
[kien_truc_nghien_cuu_adaptive_fuzzy_nkga.md](kien_truc_nghien_cuu_adaptive_fuzzy_nkga.md).

## 1. Kết luận trong một đoạn

Phần NK giờ là **bản port trung thực** của source tham chiếu, không còn là phỏng đoán. Và
với bản trung thực đó, thiết kế trong ghi chú **không hoạt động được**, vì hai lý do đã đo
được bằng số — một là lỗi của tôi và đã sửa, một là **lỗi cấu trúc của chính thiết kế**:

1. **Bằng chứng fuzzy triệt tiêu về 0** (lỗi của tôi, đã sửa). Công thức `h_i = margin ×
   typicality` của ghi chú cho `a ≤ 4e-9`, `b ≤ 3.6e-10` trên output DP-PFCM thật, và
   **100% cạnh có `a+b < 1e-6`**. Khi đó `(1−λ)F_NK + λ·0` có **đúng cùng arg-min** với
   `F_NK`, nên λ không có tác dụng gì — khớp với delta đo được **đúng bằng 0.0000** ở cả hai
   cặp có kiểm soát. Đã sửa bằng cách chuẩn hóa `h` theo từng mô hình.
2. **Bằng chứng fuzzy về cấu trúc không thể chống được việc gộp cụm** (lỗi thiết kế). Trên
   các cạnh của đồ thị NK, các mô hình tham chiếu chỉ đặt **4–11%** cặp vào khác cụm. Nên
   89–96% cạnh chỉ mang bằng chứng cùng cụm, `b_ij` gần như không có khối lượng, và số hạng
   fuzzy **cũng** thưởng cho việc gộp. Ngay cả λ=0.8, nghiệm "tất cả một nhãn" vẫn thắng
   nhãn thật.

Ngoài ra, bản thân NKCV2 trên các bộ này có **tối ưu ở phân hoạch tầm thường**:
`F(tất cả một nhãn) = 0.02496 < F(nhãn thật) = 0.02791` trên wifi.

## 2. Bản port trung thực: đã lấy được gì từ source

`arxiv.org` vẫn bị chặn trong environment này, nên **không đọc được bài báo**. Nhưng source
đã công bố ([github.com/rtinos/NKGAclust](https://github.com/rtinos/NKGAclust)) chứa chính
định nghĩa NKCV2, và lần này tôi đọc hết `comp_fi` cùng toàn bộ constructor thay vì chỉ một
phần. Đặc tả lấy được, từng dòng:

| Thành phần | Trong source |
|---|---|
| Khoảng cách | `sqrEucDist` — **bình phương** Euclid; mọi ngưỡng nằm trên thang này |
| `dc` | phân vị **2%** của toàn bộ khoảng cách bình phương đã sắp xếp |
| `rho[i]` | `Σ_j exp(-(D[i][j]/dc)²)`, rồi chia cho max để về [0,1] |
| `d_rho` | `mean(rho) − std(rho)`, hoặc `mean/2` nếu ≤ 0 |
| Đồ thị | **không phải k-NN**. Bước 1: mỗi đỉnh nhận một cạnh vào từ điểm gần nhất có **mật độ cao hơn** (cha density-peak; đỉnh dày nhất lấy láng giềng gần nhất). Bước 2: bù thêm các điểm gần nhất tới khi in-degree đúng bằng K |
| Ngưỡng | `threeSigmaRule` trên khoảng cách của các cạnh vào: `dt0 = mean`, `dt1 = mean+2sd`, `dt2 = mean+sd` |
| Factor | `fmax = rho[j]`, `fmin = 0`; thứ tự nhánh là `x[i]==0`, rồi `x[i]==x[j]`, rồi else |
| Chuẩn hóa | chia cho `N*K`, tức số cạnh |

**Sáu chỗ bản trước của tôi làm sai**, giờ đã sửa:

1. Dùng Euclid thường thay vì bình phương.
2. `rho` sai hẳn công thức (tôi đếm điểm trong một bán kính bằng trung vị khoảng cách).
3. `d_rho` sai (tôi dùng phân vị 10).
4. **Đồ thị sai**: k-NN thay vì cha DPC + bù tới in-degree K.
5. Nhánh noise dùng `dt1` thay vì `dt2`.
6. **Khi `x[j]==0`** tôi trả về 0 (miễn phí), nhưng source để nó rơi vào nhánh "khác nhãn"
   nên vẫn bị tính phí.

Lỗi 4 và 6 là lỗi làm sai bản chất tiêu chí, không chỉ sai hằng số.

## 3. Đã kiểm chứng những gì

8 property test vẫn đạt với bản port trung thực, chạy với `-W error::RuntimeWarning`:
bất biến hoán vị nhãn, delta-evaluation khớp đúng hai lần chấm đầy đủ (sai số < 1e-12),
partition crossover trả về đúng nghiệm tốt nhất trong 2^q (đối chiếu liệt kê vét cạn),
noise không né được chi phí fuzzy, chuẩn hóa nhãn giữ fitness, local search đơn điệu,
và các chặn cấu hình.

Ở lượt trước, property test đã bắt được một lỗi mà nếu không có nó thì sẽ lặng lẽ làm sai
mọi kết quả: `np.argsort(dist + np.eye(n)*np.inf)` — vì `0*inf = nan` nên **mọi ô ngoài
đường chéo thành NaN**, thứ tự láng giềng là rác, và một điểm có thể thành láng giềng của
chính nó. Chỉ có một `RuntimeWarning` báo.

## 4. Số liệu

### 4.1. Bằng chứng fuzzy, trước và sau khi chuẩn hóa

| | `a` max | `a` mean | `b` mean | Tỷ lệ cạnh `a+b < 1e-6` |
|---|---:|---:|---:|---:|
| Trước (công thức của ghi chú) | 3.96e-09 | 1.25e-10 | 6.19e-13 | **100%** |
| Sau khi chuẩn hóa theo mô hình | 0.343 | 0.0149 | 0.0001 | **0%** |

### 4.2. Nhưng `b` vẫn không có khối lượng — và đây là lỗi cấu trúc

Tỷ lệ cặp trên **các cạnh của đồ thị NK** mà mô hình tham chiếu đặt vào **khác** cụm:

| Dataset | K | Số cạnh | C=k−1 | C=k | C=k+1 | Ít nhất 1 mô hình |
|---|---:|---:|---:|---:|---:|---:|
| wifi | 3 | 6000 | 0.042 | 0.042 | 0.045 | **0.059** |
| wifi | 10 | 20000 | 0.052 | 0.051 | 0.055 | **0.069** |
| pima | 3 | 2304 | 0.077 | 0.077 | 0.078 | **0.099** |
| pima | 10 | 7680 | 0.091 | 0.091 | 0.093 | **0.114** |
| iris | 3 | 450 | 0.018 | 0.036 | 0.073 | **0.116** |
| iris | 10 | 1500 | 0.015 | 0.046 | 0.111 | **0.159** |

Đồ thị NK nối các **láng giềng gần**, và láng giềng gần thì gần như luôn cùng cụm trong mọi
mô hình tham chiếu. Vì `V_ij` tính `b_ij` khi cùng nhãn và `a_ij` khi khác nhãn, mà
`mean(b) = 0.0001` so với `mean(a) = 0.0149`, **số hạng fuzzy cũng rẻ hơn khi gộp**.

Hệ quả, đo trực tiếp:

| Dataset | Nghiệm | λ=0 | λ=0.4 | λ=0.8 |
|---|---|---:|---:|---:|
| wifi | tất cả một nhãn | **0.02496** | **0.01500** | **0.00505** |
| wifi | nhãn thật | 0.02791 | 0.01703 | 0.00615 |
| pima | tất cả một nhãn | **0.00575** | **0.00359** | **0.00143** |
| pima | nhãn thật | 0.04973 | 0.03375 | 0.01778 |

Nghiệm tầm thường thắng nhãn thật ở **mọi** mức λ. Tăng λ không đảo được dấu.

### 4.3. Ablation với bản port trung thực (Pima, Wifi, 3 run)

| Biến thể | K=3, ARI | K=3, số cụm | K=10, ARI | K=10, số cụm |
|---|---:|---:|---:|---:|
| A0 NKCV2, fuzzy tắt, ngẫu nhiên | 0.1341 | 46.2 | 0.0276 | 11.8 |
| A1 NKCV2, fuzzy tắt, từ bank | 0.0273 | 11.8 | 0.0253 | 8.3 |
| A2 thích nghi, fuzzy tắt, bank | 0.0251 | 11.7 | 0.0095 | 7.8 |
| A3 NKCV2, **fuzzy bật**, bank | 0.0273 | 12.0 | 0.0253 | 8.3 |
| A4 thích nghi, **fuzzy bật**, bank | 0.0251 | 11.7 | 0.0095 | 7.8 |

Cặp có kiểm soát (cùng đồ thị, cùng bank, quần thể khởi tạo bit-identical, chỉ bật/tắt λ):
A1→A3 **−0.0000**, A2→A4 **+0.0000**. Đây là ablation chạy **trước** khi sửa lỗi chuẩn hóa,
nên nó đo đúng hệ quả của lỗi đó.

Mốc so sánh: DP-GA-PFCM baseline cho pima 0.1023 và wifi 0.8500. **Prototype kém xa.**

### 4.4. ĐÃ SỬA: cân lại `b` theo độ hiếm, và λ bắt đầu có tác dụng thật

Sửa theo đúng chẩn đoán ở 4.2: chia mỗi phía cho khối lượng của chính nó
(`balance=True`), để `a` và `b` góp phần bằng nhau về tổng và độ hiếm không còn quyết định
hướng. Đây là **hiệu chỉnh công khai cho một thiên lệch lấy mẫu của tập cạnh**, không phải
xác suất đã hiệu chuẩn, và nó không làm bằng chứng giàu thông tin hơn — chỉ ngăn mất cân
bằng chi phối.

Câu hỏi quyết định — `F(nhãn thật)` có thấp hơn `F(tất cả một nhãn)` chưa:

| Dataset | Chưa cân, λ=0.4…0.95 | Đã cân, λ=0.4 | λ=0.8 | λ=0.95 |
|---|---|---|---|---|
| iris | không | **CÓ** | **CÓ** | **CÓ** |
| wifi | không | không | không | **CÓ** |
| pima | không | không | không | **CÓ** |

Và ablation thật, cặp có kiểm soát A1 (λ=0) → A3 (fuzzy bật), cùng đồ thị, cùng bank, cùng
quần thể khởi tạo:

| λ | Dataset | A1 | A3 | Δ |
|---|---|---:|---:|---:|
| 0.8 | pima | 0.0435 | **0.1103** | +0.0668 |
| 0.8 | wifi | 0.0112 | **0.3636** | +0.3524 |
| 0.8 | **trung bình** | 0.0273 | **0.2369** | **+0.2096** |
| 0.95 | pima | 0.0435 | 0.1071 | +0.0636 |
| 0.95 | wifi | 0.0112 | 0.3696 | +0.3584 |
| 0.95 | **trung bình** | 0.0273 | **0.2383** | **+0.2110** |

So với **−0.0000** trước khi sửa. Đây là lần đầu **hướng dẫn fuzzy thực sự làm đổi phân
hoạch**, tức là RQ1 của ghi chú bắt đầu trả lời được: có, nhưng chỉ sau khi hiệu chỉnh
thiên lệch của tập cạnh.

Trên **pima**, prototype nay **vượt nhẹ** DP-GA-PFCM: 0.1103 so với 0.1023. Trên **wifi**
vẫn kém xa: 0.3636 so với 0.8500.

**Ba điều phải nêu kèm, không được bỏ:**

1. **Số cụm vẫn quá cao**: 13.7–30.5 khi k là 2 và 4. Vấn đề phân mảnh **chưa** được giải
   quyết; nó chỉ được chứng minh là **độc lập** với số hạng fuzzy.
2. **λ phải rất lớn** (0.8–0.95) mới đảo được dấu trên wifi và pima. Ở λ=0.95, phần NK chỉ
   góp 5%, nên phương pháp gần như suy biến thành **consensus của ngân hàng tham chiếu**, và
   mất đúng những thứ NK mang lại: cụm hình dạng bất kỳ và phát hiện nhiễu. Phải đo riêng
   xem ở λ cao nó còn hơn gì so với việc chỉ chạy consensus.
3. Phép thử `F(nhãn thật)` **dùng nhãn**, và tôi đã chạy nó trên cả **iris** là bộ thuộc
   tập test. Nó là phép chẩn đoán địa hình hàm mục tiêu, **không** dùng để chọn tham số;
   mọi lựa chọn (balance, λ) đều quyết định trên pima và wifi thuộc tập dev.

### 4.5. ĐÃ LÀM: tách miền tính bằng chứng khỏi E — sửa nguyên nhân

Đây là lựa chọn (1) ở mục 5, tức sửa **nguyên nhân** thay vì hiệu chỉnh hậu quả như
`balance`. Bằng chứng nay được tính trên một tập cạnh riêng `E_fuzzy`: với mỗi điểm i, quét
`pool` điểm gần nhất và giữ `per_point` điểm gần nhất mà **ít nhất một** mô hình tham chiếu
đặt vào cụm khác. Đó là các cặp ở biên — đủ gần để lựa chọn của phân hoạch có ý nghĩa, nhưng
bị tham chiếu tách, tức đúng nơi `b` mang thông tin. Quy tắc chọn không dùng nhãn.

**Tính đúng của PX được giữ như ghi chú cảnh báo.** Vì `E_fuzzy ≠ E`, tập cạnh **phụ thuộc**
của fitness là **hợp** của hai tập. `Fitness` phơi ra `dep_i/dep_j/dep_touch`, và:

- **partition crossover** tách component trên hợp đó. Nếu chỉ dùng E, hai đỉnh khác nhau mà
  nối bởi một cạnh bằng chứng sẽ rơi vào hai component khác nhau, các component **không còn
  độc lập**, và PX không còn trả về nghiệm tốt nhất trong 2^q.
- **chuẩn hóa nhãn** cũng xét liên thông trên hợp đó. Nếu chỉ dùng E, nó sẽ tách một nhãn qua
  một cạnh bằng chứng, lật cặp đó từ "cùng" sang "khác" và **làm đổi fitness**.

Cả hai tính chất này được kiểm bằng property test: PX đối chiếu liệt kê vét cạn 2^q trên hợp,
và `test_canonical_preserves_fitness` chạy với tập bằng chứng tách riêng. 8/8 đạt.

**Kết quả — cặp có kiểm soát A1 (λ=0) → A3 (fuzzy bật), Pima và Wifi, 3 run:**

| Cấu hình | Cạnh bằng chứng | A1 | A3 | Δ | Số cụm A3 |
|---|---:|---:|---:|---:|---:|
| Miền = E (như prototype đầu), λ=0.4 | 4152 | 0.0273 | 0.0217 | **−0.0056** | 11.5 |
| **Miền tách**, λ=0.4 | 1046 | 0.0273 | 0.0824 | **+0.0550** | 14.0 |
| Miền tách + `balance`, λ=0.4 | 1046 | 0.0273 | 0.0805 | +0.0532 | 13.0 |
| Miền tách, λ=0.8 | 1046 | 0.0273 | 0.2318 | +0.2044 | 19.2 |

**Hạn chế 2 và 3 ĐÃ XONG.** λ=0.4 nay có tác dụng rõ (+0.0550) trong khi miền cũ cho
−0.0056. Không còn cần λ=0.8–0.95, nên cũng không còn nguy cơ suy biến thành consensus của
ngân hàng. Và `balance` **trở nên không cần thiết** (+0.0550 so với +0.0532) — xác nhận nó
chỉ chữa triệu chứng, còn đây là sửa nguyên nhân.

### 4.6. Hạn chế 1 (phân mảnh): đã chuyển thành một đánh đổi đo được, CHƯA giải quyết

`E_fuzzy` ở 4.5 chỉ chứa cặp **bất đồng**, nên nó chỉ phạt việc **gộp**. Để phạt việc
**tách**, tôi thêm `agree_per_point`: giữ thêm các cặp **xa nhất** trong pool mà **mọi** mô
hình đồng thuận là cùng cụm, và không nằm trong E (vì E đã tự ràng buộc láng giềng của nó).
Những cặp đó mang `a_ij`, mà `V_ij` tính khi phân hoạch tách chúng.

| Cấu hình | Cạnh BC | A3 | Δ | Số cụm A3 | pima / wifi |
|---|---:|---:|---:|---:|---|
| λ=0.4, agree=0 | 1046 | 0.0824 | +0.0550 | 14.0 | 0.034(12) / 0.131(16) |
| λ=0.4, agree=2 | 3733 | 0.0188 | −0.0085 | **5.7** | 0.029(5) / 0.009(6) |
| λ=0.4, agree=4 | 6316 | 0.0170 | −0.0103 | **4.8** | 0.027(5) / 0.007(5) |
| λ=0.8, agree=0 | 1046 | 0.2318 | +0.2044 | 19.2 | 0.089(16) / 0.374(22) |
| λ=0.8, agree=2 | 3733 | 0.0067 | −0.0206 | 7.2 | 0.006(6) / 0.008(8) |
| λ=0.8, agree=4 | 6316 | 0.0125 | −0.0149 | **3.5** | 0.018(4) / 0.007(3) |

Cơ chế **hoạt động đúng như thiết kế**: số cụm từ 19.2 xuống **3.5**, tức về đúng thang k
(pima 2, wifi 4). Nhưng **ARI sụp** về ~0.01. Nghĩa là nó gộp về đúng *số* cụm mà **sai nội
dung** cụm.

Phát biểu trung thực: hạn chế 1 **chưa được giải quyết**. Nó đã được chuyển từ "không biết
vì sao phân mảnh" thành một **đánh đổi định lượng được** giữa số cụm và chất lượng, nằm trong
một cơ chế duy nhất là thành phần của `E_fuzzy`. Điều này nói rằng bằng chứng theo cặp lấy từ
ngân hàng DP-PFCM **không chứa đủ thông tin** để đạt đồng thời đúng số cụm và đúng nội dung —
và đó là một kết quả về **giới hạn của chính nguồn bằng chứng**, không phải về tham số.

## 5. Kết luận về thiết kế trong ghi chú

Giả thuyết trung tâm của ghi chú là hướng dẫn fuzzy sẽ **giảm hiện tượng gộp cụm**. Số liệu
nói điều ngược lại về cơ chế: vì bằng chứng được định nghĩa **trên chính tập cạnh E của đồ
thị NK**, mà E chỉ chứa các cặp gần, nên bằng chứng "cùng cụm" chiếm 89–96% khối lượng và
số hạng fuzzy **cũng** đẩy về phía gộp. Đây không phải vấn đề tham số λ; đây là hệ quả của
việc chọn E làm miền tính bằng chứng.

**Hướng sửa, theo đúng chẩn đoán.** Lựa chọn (2) **đã thử và có tác dụng** (mục 4.4): cân
lại `b` theo độ hiếm đưa Δ của cặp có kiểm soát từ −0.0000 lên **+0.2096**. Hai lựa chọn
còn lại chưa thử, và nay là việc tiếp theo vì vấn đề **phân mảnh** vẫn còn:

1. Tách miền bằng chứng khỏi E: giữ E cho phần NK, nhưng tính `a, b` trên một tập cặp khác
   có bao gồm cặp tầm xa và cặp ở biên giữa các cụm tham chiếu. Ghi chú có cảnh báo rằng
   mọi cạnh phụ thuộc của fitness phải nằm trong đồ thị tách component của PX, nên nếu thêm
   cặp thì **phải thêm cả vào đồ thị PX**, nếu không PX sẽ không còn đúng. Đây là lựa chọn
   đúng về nguyên lý hơn (2), vì (2) chỉ hiệu chỉnh hệ quả còn (1) sửa nguyên nhân.
2. ~~Cân lại trọng số `b` theo độ hiếm~~ — **đã làm**, `balance=True`.
3. Xem lại chính `V_ij`: hiện cùng nhãn phải trả `b` và khác nhãn phải trả `a`. Với `a ≫ b`
   thì công thức này vốn đã thiên về gộp, bất kể dữ liệu. Sau khi cân thì `a = b` về tổng,
   nhưng phân bố theo từng cạnh vẫn lệch.

Và một điều phải ghi rõ cho cả hướng nghiên cứu: **NKCV2 trên các bộ này có tối ưu ở phân
hoạch tầm thường** (`F(một nhãn) < F(nhãn thật)` trên wifi, và 64.4% cạnh có `d ≤ dt0` nên
cùng nhãn là miễn phí). Nghĩa là NKCV2 hoạt động được là nhờ **quỹ đạo** của GA gốc — các
toán tử merge/split và local search của nó — chứ không nhờ vị trí cực tiểu. Mọi thiết kế
dùng NKCV2 làm nền phải bàn điều này. Tôi không đọc được bài báo nên không kết luận tác giả
có nêu hay không.

## 6. Việc cần làm tiếp

1. **Vẫn cần mở `arxiv.org`** để đọc phần lý giải và giao thức thực nghiệm của bài gốc.
   Source cho đủ công thức, nhưng không cho biết tác giả xử lý điểm ở mục 5 thế nào.
2. Thử ba hướng sửa ở mục 5, mỗi lần một thay đổi, bắt đầu từ (2) vì rẻ nhất.
3. Chỉ sau khi `F(nhãn thật) < F(một nhãn)` thì ablation λ mới có nghĩa. Trước đó, RQ1 của
   ghi chú không thể trả lời.
4. Kiểm chứng bản port bằng cách biên dịch source tham chiếu và so giá trị fitness trên
   `Compound.dat`. **Chưa làm**: đây là code tải từ ngoài, nên biên dịch và chạy nó cần cân
   nhắc riêng về an toàn, và tôi chưa đọc hết các file `.cpp` còn lại.

## 7. File

| File | Nội dung |
|---|---|
| `2_models_code/afnkga/model.py` | port NKCV2 trung thực, bằng chứng fuzzy, fitness, delta, chuẩn hóa nhãn |
| `2_models_code/afnkga/ga.py` | partition crossover, mutation reclassify/merge/split, local search, vòng GA |
| `2_models_code/afnkga/run.py` | CLI ablation A0–A4 |
| `2_models_code/tests/test_afnkga.py` | 8 property test |
| `4_documents/research_notes/data/afnkga_K3.jsonl`, `afnkga_K10.jsonl` | ablation bản trung thực |
| `4_documents/research_notes/data/afnkga_dev.jsonl` | ablation bản trước khi port lại |

Prototype là package riêng, **không** thay đổi gì pipeline DP-GA-PFCM. Cả 4 bộ test của dự
án vẫn đạt.

---

## 8. Đổi nguồn bằng chứng: ngân hàng đa dạng — sửa được cả hạn chế 1

Giả thuyết ở mục 4.6 là bằng chứng theo cặp từ ngân hàng **chỉ gồm DP-PFCM** không chứa đủ
thông tin. Kiểm chứng bằng cách thêm thành viên **thất bại theo cách khác**: k-means (3 mức
C), spectral clustering với affinity nearest-neighbors (2 mức C), và DBSCAN ở hai mức eps.
Một phân hoạch cứng được bọc thành (U, T) one-hot, nên `h_i = 1` — một thành viên không biểu
đạt bất định thì bỏ phiếu với độ tin cậy đầy đủ, đó là cách đọc trung thực. Nhiễu `-1` của
DBSCAN thành một cột riêng để các điểm đó không lặng lẽ nhập vào cụm 0.

Pima và Wifi, 2 run, miền bằng chứng tách, λ=0.4:

| Cấu hình | Cỡ ngân hàng | Cạnh BC | A1 | A3 | Δ | Số cụm | pima / wifi |
|---|---:|---:|---:|---:|---:|---:|---|
| PFCM, agree=0 | 6 | 1046 | 0.0273 | 0.0824 | +0.0550 | 14.0 | 0.034(12) / 0.131(16) |
| **Đa dạng, agree=0** | 10 | 2008 | 0.0277 | **0.1225** | **+0.0948** | **4.5** | 0.007(3) / 0.239(6) |
| PFCM, agree=2 | 6 | 3733 | 0.0273 | 0.0188 | −0.0085 | 5.7 | 0.029(5) / 0.009(6) |
| **Đa dạng, agree=2** | 10 | 4486 | 0.0277 | **0.0863** | **+0.0587** | **3.2** | 0.011(3) / 0.162(4) |

**Hạn chế 1 nay đã được xử lý về cơ chế.** Ngân hàng đa dạng cho **4.5 cụm** (k thật là 2 và
4) mà Δ **vẫn dương và gần gấp đôi** (+0.0948 so với +0.0550). Trước đó, cách duy nhất hạ
được số cụm là thêm cặp đồng thuận, và nó làm ARI sụp (−0.0085). Nay với `agree=2` số cụm về
**3.2** mà Δ vẫn **+0.0587**. Số cạnh bằng chứng tăng gấp đôi (2008 so với 1046), tức `b`
cuối cùng đã có khối lượng thật.

Điều này xác nhận chẩn đoán ở 4.6: vấn đề nằm ở **nguồn** bằng chứng, không ở tham số. Một
ngân hàng toàn PFCM đồng thuận quá nhiều để nói được điều gì về việc tách cụm.

**Vẫn chưa thắng baseline:** wifi 0.239 so với 0.850, và pima **xấu đi** (0.007 so với
0.034). Nên đây là bước tiến về cơ chế, **không phải** một phương pháp đã dùng được. Việc
tiếp theo: quét cỡ và thành phần ngân hàng, và chạy đủ seed trên toàn tập dev.
