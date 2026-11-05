# Bảng B1 — phân bố kết quả của mọi can thiệp trên tập dev

Ngày: 2026-11-05. Bảng này phục vụ đóng góp C1 trong [de_cuong_bai_bao.md](de_cuong_bai_bao.md).

## 1. Cách đọc, và một lỗi phân tích đã sửa

Mỗi dòng là **một** thay đổi so với baseline DP-GA-PFCM, so sánh **ghép cặp theo đúng cùng
dataset và cùng seed**. Cột `bo` là số dataset mà biến thể đã bao phủ; cột `ARI base` là
trung bình của baseline **trên đúng tập dataset đó**, không phải trên toàn bộ 10 bộ.

**Lỗi đã sửa:** ở lần dựng bảng đầu, tôi so trung bình của biến thể (chạy dở, mới bao phủ
2–3 bộ) với trung bình baseline trên **toàn bộ** 10 bộ. Việc đó cho `ga_wpinned` = **−0.1486**,
một con số hoàn toàn là ảo, chỉ vì nó mới chạy xong `pima` (ARI ~0.10) trong khi baseline đã
có cả `wifi` (ARI ~0.85). Khi so trên đúng cùng tập, con số thật là **+0.0009**. Tôi đã báo
con số sai đó ra ngoài trước khi phát hiện, nên ghi lại đây.

Bài học cho bảng B1 khi công bố: **không được đọc một dòng nào có dấu `CHƯA ĐỦ BỘ`** như một
so sánh hoàn chỉnh, dù nó đã ghép cặp đúng.

## 2. B1 — 5 seed, đã đủ dữ liệu

Baseline trên 10 bộ dev: **0.5463**.

| Biến thể | Bộ | ΔARI | Tốt/xấu | p Wilcoxon |
|---|---:|---:|---:|---:|
| `ga_wpinned` (ghim fuzzifier) | 10 | **+0.0033** | 26/20 | 0.27 |
| `pso_wpinned` | 10 | +0.0023 | 28/22 | 0.40 |
| `final_guard` | 10 | 0.0000 | 0/0 | 1.00 |
| `anticollapse_pen` / `_rep` / `_both` | 7 | 0.0000 | 0/0 | 1.00 |
| `dpc_localscaled` | 7 | −0.0011 | 16/18 | 0.60 |
| `horizon5_gen20` | 10 | −0.0016 | 24/26 | 0.18 |
| `guard_plus_h5g20` | 10 | −0.0016 | 24/26 | 0.18 |
| `init_diverse` | 7 | −0.0027 | 12/21 | 0.33 |
| `cons_sub12_fcm` | 10 | −0.0064 | 23/27 | 0.14 |
| `cons_sub12` | 10 | −0.0067 | 23/26 | 0.15 |
| `cons_basic` | 10 | −0.0082 | 19/31 | 0.057 |
| `fit_ch` | 7 | −0.0181 | 15/18 | 0.47 |
| `fit_db` | 7 | −0.0246 | 14/20 | 0.41 |
| `cons_nofilter` | 10 | −0.0258 | 21/28 | **0.022** |
| `lamarckian` (đo riêng, 4 bộ dev gốc) | 4 | −0.0004 | 11/9 | — |

**Phân bố ΔARI trải từ −0.0258 đến +0.0033.** Không dòng nào dương có ý nghĩa. Dòng **duy
nhất** có ý nghĩa thống kê là `cons_nofilter` (p = 0.022) và nó **âm** — tức việc **bỏ** ràng
buộc đúng k cụm làm xấu đi, đúng chiều với phát hiện C2.

Ba biến thể chống sập cụm cho **0.0000 bit-identical**: trên toàn tập dev pipeline không bao
giờ sập cụm (số cụm quan sát bằng đúng k ở cả 10 bộ, kể cả hai bộ k=8), nên không có gì để
phạt hoặc sửa. Đã kiểm tra riêng rằng code có hoạt động.

## 3. B1 — 30 seed, đang chạy

| Biến thể | Bộ đã phủ | Seed/bộ | ΔARI (trên tập đã phủ) | Tốt/xấu | p |
|---|---:|---:|---:|---:|---:|
| `cons_sub12` | 7 | 27 | −0.0074 | 95/96 | 0.0088 |
| `ga_wpinned` | 2 | 28 | +0.0009 | 32/19 | 0.036 |
| `fit_db` | 3 | 26 | −0.0325 | 33/45 | 0.55 |
| `collapse_penalty` | 6 | 30 | 0.0000 | 0/0 | 1.00 |

Còn thiếu: `lamarckian`, `fit_ch`, `dpc_localscaled`, `init_diverse`, `final_guard`,
`horizon5_gen20`. Lượt chạy đầu bị worker restart giết giữa đường; đã khởi động lại ở chế
độ `setsid` để tách khỏi session.

Hiện tượng đáng chú ý ở `cons_sub12`: 95 cặp tốt hơn và 96 cặp xấu hơn, gần như hoàn toàn
cân, nhưng p = 0.0088. Đó là vì Wilcoxon xét **độ lớn** của chênh lệch chứ không chỉ dấu —
các lần xấu hơn xấu nhiều hơn các lần tốt hơn tốt. Khi viết bài phải nêu cả tỷ lệ dấu và
p, không chỉ p.

## 4. Kết luận từ bảng

Mười một can thiệp, phân bố ΔARI nằm trong **[−0.026, +0.003]**, và dòng có ý nghĩa duy nhất
là một dòng âm. Đây là bằng chứng chính cho phát biểu: trong họ DP-metaheuristic-PFCM, **không
có đòn bẩy nào ở phía bộ tối ưu, hàm fitness, khởi tạo hay DPC tạo được mức tăng đáng kể**,
và lý do đã đo riêng — baseline nằm ở trần không gian tham số của nó (dev 0.5463 so với
oracle 0.5464).

## 5. Dữ liệu thô

| Nội dung | Vị trí |
|---|---|
| 5 seed, 7 bộ (đợt đầu) | `data/screen/` |
| 5 seed, 10 bộ (đợt mở rộng k=6,8) | `data/screen2/` |
| 5 seed, consensus | `data/screen3/` |
| 5 seed, ghim fuzzifier | `data/screen4/` |
| 30 seed (đang chạy) | `data/b1/` |
| Ablation Lamarckian, 4 bộ dev gốc | `data/diag_dev.jsonl` |
