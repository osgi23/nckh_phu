# Hướng Dẫn Đánh Giá Kết Quả và Biểu Đồ So Sánh Các Mô Hình

Thư mục `3_comparison_outputs/` tập hợp toàn bộ các kết quả trực quan hóa, biểu đồ so sánh, và bảng tổng hợp hiệu năng của các thuật toán phân cụm được thực nghiệm và tái tạo theo bài báo nghiên cứu **DP-GA-PFCM**.

---

## 1. Cấu trúc thư mục đầu ra

```text
3_comparison_outputs/
├── 00_XEM_NHANH_HTML/
│   ├── 00_XEM_KET_QUA.html            # Dashboard tương tác xem tất cả biểu đồ & bảng dữ liệu
│   └── MO_KET_QUA.cmd                 # Nhấp đúp để mở dashboard trên trình duyệt
│
├── 01_tong_quan_cac_mo_hinh/          # Tổng quan so sánh toàn bộ 9 mô hình
│   ├── 01_heatmap_tong_quan_10_bo.png # Heatmap Purity, ARI, NMI trên 10 bộ dữ liệu
│   ├── 02_bieu_do_xep_hang_tong_the.png # Biểu đồ cột tổng hợp xếp hạng hiệu năng
│   └── 03_so_sanh_2_bo_cuc_tri_kmeans.png # So sánh sâu 2 bộ dữ liệu cực trị (Wine vs Glass)
│
├── 02_so_sanh_tung_dataset_10_bo/     # Chi tiết từng bộ trong 10 dataset benchmark
│   ├── bieu_do_chi_so_metrics/        # 10 biểu đồ cột Purity, ARI, NMI của từng dataset
│   │   ├── metrics_aggregation.png
│   │   ├── metrics_breast_tissue.png
│   │   ├── metrics_compound.png
│   │   ├── metrics_ecoli.png
│   │   ├── metrics_flame.png
│   │   ├── metrics_glass.png
│   │   ├── metrics_iris.png
│   │   ├── metrics_jain.png
│   │   ├── metrics_seed.png
│   │   └── metrics_wine.png
│   └── hinh_anh_phan_cum_2d_pca/      # 10 ảnh scatter plot phân cụm trên không gian PCA 2D
│       ├── clusters_aggregation.png
│       ├── clusters_breast_tissue.png
│       ├── clusters_compound.png
│       ├── clusters_ecoli.png
│       ├── clusters_flame.png
│       ├── clusters_glass.png
│       ├── clusters_iris.png
│       ├── clusters_jain.png
│       ├── clusters_seed.png
│       └── clusters_wine.png
│
├── 03_so_sanh_do_ben_vung_ngoai_lai_gaussian/ # Thử nghiệm độ bền vững với nhiễu ngoại lai
│   ├── 01_bang_ari_nc2_l5_outliers.png        # Bảng Mean/Best ARI và kiểm định Wilcoxon
│   ├── 02_do_thi_bien_thien_ari_theo_outliers.png # Đồ thị ARI suy giảm theo tỷ lệ 0% -> 20%
│   ├── metrics_outliers_00pct.png             # So sánh chỉ số tại 0% ngoại lai
│   ├── metrics_outliers_05pct.png             # So sánh chỉ số tại 5% ngoại lai
│   ├── metrics_outliers_10pct.png             # So sánh chỉ số tại 10% ngoại lai
│   ├── metrics_outliers_20pct.png             # So sánh chỉ số tại 20% ngoại lai
│   └── phan_cum_ngoai_lai_pca/                # Trực quan hóa phân cụm khi có ngoại lai
│       ├── clusters_outliers_00pct.png
│       ├── clusters_outliers_05pct.png
│       ├── clusters_outliers_10pct.png
│       └── clusters_outliers_20pct.png
│
├── 04_do_hoi_tu_va_thoi_gian_chay/            # Đánh giá hội tụ và chi phí tính toán
│   ├── 01_do_thi_hoi_tu_ga_convergence.png    # Đường cong hội tụ GA qua 100 thế hệ
│   └── 02_so_sanh_thoi_gian_chay_runtime.png  # Biểu đồ thời gian thực thi (giây) các mô hình
│
└── HUONG_DAN_DANH_GIA_KET_QUA.md              # File hướng dẫn này
```

---

## 2. Các tham số và chỉ số đánh giá theo Bài báo

| Chỉ số / Tham số | Ký hiệu | Ý nghĩa trong bài báo | Giá trị tốt nhất |
|:---|:---:|:---|:---:|
| **Purity / Accuracy** | Purity / Acc | Độ thuần khiết phân cụm (Công thức Eq. 17). Tỷ lệ mẫu được gán đúng cụm lớn nhất. | Càng cao càng tốt ($1.0 = 100\%$) |
| **Adjusted Rand Index** | ARI | Đo độ tương đồng giữa nhãn phân cụm và nhãn thực tế, có hiệu chỉnh ngẫu nhiên. | Càng cao càng tốt ($1.0$) |
| **Normalized Mutual Info** | NMI | Lượng thông tin tương hỗ chuẩn hóa giữa phân cụm và nhãn thực tế. | Càng cao càng tốt ($1.0$) |
| **Runtime** | Giây (s) | Thời gian thực thi thuật toán trên cùng một tập dữ liệu và phần cứng. | Càng thấp càng tốt |
| **GA Generations** | Gen | Số thế hệ tiến hóa của thuật toán di truyền ($100$ thế hệ theo Table 5). | Quan sát đường hội tụ ổn định |
| **Outlier Ratio** | $\%$ | Tỷ lệ nhiễu ngoại lai thay thế ($0\%, 5\%, 10\%, 20\%$) trong dữ liệu Gaussian ($N_c=2, L=5$). | Đánh giá độ dốc suy giảm ARI |

---

## 3. Danh sách các mô hình thuật toán so sánh

Bài báo chia thực nghiệm thành 2 giai đoạn so sánh chính:

### Giai đoạn 1: Các mô hình cơ sở (Baselines - Nhóm Xanh Dương)
1. **K-means**: Thuật toán phân cụm truyền thống cơ sở.
2. **FCM (Fuzzy C-Means)**: Thuật toán phân cụm mờ cổ điển.
3. **PFCM (Possibilistic Fuzzy C-Means)**: Kết hợp độ thuộc mờ (membership) và độ khả năng (typicality) nhằm giảm nhạy cảm với ngoại lai.
4. **DP-FCM**: Tích hợp thuật toán đỉnh mật độ (DPC) để tìm tâm ban đầu cho FCM.
5. **DP-PFCM**: Tích hợp DPC để khởi tạo tâm cho PFCM.

### Giai đoạn 2: Các mô hình tối ưu hóa siêu nghiệm (Comparisons - Nhóm Cam & Tím)
6. **DP-PSO-PFCM**: Khởi tạo bằng DPC + Tối ưu hóa bầy đàn hạt (PSO) + PFCM.
7. **DP-SCA-PFCM**: Khởi tạo bằng DPC + Thuật toán Sine Cosine (SCA) + PFCM.
8. **DP-FBI-PFCM**: Khởi tạo bằng DPC + Thuật toán điều tra pháp y (FBI) + PFCM.
9. **DP-GA-PFCM (Mô hình chính đề xuất)**: Khởi tạo bằng DPC + Giải thuật di truyền (GA) tối ưu hóa đồng thời tâm cụm và các tham số PFCM ($a, b, w, \eta$) + PFCM tinh chỉnh.

---

## 4. Chi tiết các nhóm ảnh so sánh và đối chiếu bài báo

### Nhóm 1: Tổng quan các mô hình (`01_tong_quan_cac_mo_hinh/`)
- **`01_heatmap_tong_quan_10_bo.png`**:
  - *Đối chiếu bài báo*: Tổng hợp kết quả từ **Bảng 6, 7, 8** (Purity, ARI, NMI của Baselines) và **Bảng 11, 12, 13** (Purity, ARI, NMI của Metaheuristics).
  - *Đánh giá*: Cho phép quan sát toàn cảnh hiệu năng của 9 mô hình trên 10 bộ dữ liệu cùng lúc. Các ô có màu sáng biểu thị giá trị chỉ số cao.
- **`02_bieu_do_xep_hang_tong_the.png`**:
  - *Đánh giá*: So sánh mean rank tổng thể. Các thuật toán lai tối ưu siêu nghiệm (đặc biệt là DP-GA-PFCM) đạt thứ hạng vượt trội so với các thuật toán mờ thuần túy.
- **`03_so_sanh_2_bo_cuc_tri_kmeans.png`**:
  - *Đánh giá*: Chọn ra 2 bộ dữ liệu có kết quả K-means phân cực nhất: **Wine** (K-means đạt Purity cao nhất $\approx 94.68\%$) và **Glass** (K-means đạt Purity thấp nhất $\approx 55.92\%$). Cho thấy trên các bộ dữ liệu phức tạp/nhiều cụm như Glass, các mô hình dựa trên DPC và tối ưu GA cải thiện chất lượng rõ rệt.

### Nhóm 2: So sánh chi tiết từng bộ dữ liệu (`02_so_sanh_tung_dataset_10_bo/`)
- **`bieu_do_chi_so_metrics/` (10 ảnh)**:
  - Mỗi ảnh là biểu đồ cột so sánh trực tiếp 3 chỉ số Purity, ARI, NMI của 9 mô hình trên một bộ dữ liệu cụ thể (Iris, Wine, Flame, Jain, Glass, Ecoli, Compound, Seed, Breast Tissue, Aggregation).
  - Có thanh sai số (Standard Deviation) phản ánh độ ổn định qua các lần chạy độc lập.
- **`hinh_anh_phan_cum_2d_pca/` (10 ảnh)**:
  - Không gian đặc trưng được chiếu xuống 2 thành phần chính (PCA 1 & PCA 2).
  - Màu sắc các điểm biểu thị cụm mà mô hình gán vào, giúp trực quan hóa ranh giới phân cụm và hình dạng cụm phức tạp (như hình lưỡi liềm của Flame, hai cụm lồng của Jain).

### Nhóm 3: So sánh độ bền vững với nhiễu ngoại lai (`03_so_sanh_do_ben_vung_ngoai_lai_gaussian/`)
- **`01_bang_ari_nc2_l5_outliers.png`**:
  - *Tham số*: Tạo 9 dataset tổng hợp Gaussian với $N_c = 2$ cụm, $L = 5$ thuộc tính, tổng $500$ điểm.
  - *4 mức ngoại lai*: $0\%, 5\%, 10\%, 20\%$ điểm ngoại lai đồng nhất.
  - *Bảng dữ liệu*: Trình bày Mean ARI và Best ARI qua 25 lần chạy, kèm kiểm định cặp Wilcoxon signed-rank test giữa K-means và DP-GA-PFCM.
- **`02_do_thi_bien_thien_ari_theo_outliers.png`**:
  - *Đánh giá*: Đồ thị đường thể hiện sự suy giảm của chỉ số ARI khi tỷ lệ nhiễu tăng từ $0\%$ lên $20\%$. K-means suy giảm mạnh nhất do độ nhạy cảm cao với điểm ngoại lai; các mô hình PFCM và GA giữ được ARI ổn định hơn.

### Nhóm 4: Độ hội tụ và thời gian thực thi (`04_do_hoi_tu_va_thoi_gian_chay/`)
- **`01_do_thi_hoi_tu_ga_convergence.png`**:
  - *Tham số*: Quần thể $80$ cá thể, $100$ thế hệ (theo Table 5).
  - *Đánh giá*: Đường cong fitness hội tụ nhanh trong khoảng 20-30 thế hệ đầu tiên và sau đó ổn định, chứng minh hiệu quả tìm kiếm không gian nghiệm của giải thuật di truyền.
- **`02_so_sanh_thoi_gian_chay_runtime.png`**:
  - *Đánh giá*: K-means và FCM có thời gian tính toán nhỏ nhất ($\approx 0.01 - 0.05$s). Các mô hình tối ưu hóa siêu nghiệm (DP-GA-PFCM, DP-PSO-PFCM, DP-FBI-PFCM) mất nhiều thời gian hơn ($\approx 0.5 - 2$s) do phải đánh giá quần thể qua nhiều thế hệ, đây là sự đánh đổi hợp lý để đạt chất lượng phân cụm tối ưu.

---

## 5. Hướng dẫn mở Dashboard tương tác nhanh

Để xem toàn bộ kết quả, biểu đồ và số liệu một cách trực quan trên trình duyệt:
1. Vào thư mục `3_comparison_outputs/00_XEM_NHANH_HTML/`.
2. Nhấp đúp chuột vào file **`MO_KET_QUA.cmd`** (hoặc mở trực tiếp file `00_XEM_KET_QUA.html` bằng trình duyệt Chrome, Edge, Firefox).
3. Tại giao diện web:
   - Chuyển đổi giữa các chỉ số **Purity**, **ARI**, **NMI** để xem heatmap và bảng đối chiếu.
   - Chọn từng dataset để xem chi tiết mean $\pm$ standard deviation và ảnh phân cụm PCA.
