# Dự án Tái tạo và So sánh các Mô hình Phân cụm DP-GA-PFCM

Dự án nghiên cứu và tái tạo thực nghiệm bài báo khoa học về thuật toán phân cụm lai **DP-GA-PFCM** (*Density Peak Clustering + Genetic Algorithm + Possibilistic Fuzzy C-Means*).

Toàn bộ dự án đã được tái cấu trúc thành **3 thư mục cốt lõi** (+ tài liệu đính kèm) giúp dễ dàng theo dõi, chạy thử và đánh giá kết quả:

---

## 1. Cấu trúc tổng thể của Dự án

```text
D:\DA_NCKHphu\
│
├── 📁 1_datasets/               # THƯ MỤC 1: TOÀN BỘ TẬP DỮ LIỆU THỰC NGHIỆM
│   ├── 10_datasets_bai_bao/     # 10 benchmark chính theo Table 1 bài báo (Iris, Wine, Flame, Jain,...)
│   ├── 04_datasets_mo_rong/     # 4 tập dữ liệu dùng đánh giá mở rộng (Pima, Rice, Wifi,...)
│   ├── BreastTissue.xls         # Dữ liệu gốc Excel
│   ├── summary.csv              # Bảng tóm tắt số mẫu (N), số chiều (D), số cụm (K)
│   ├── manifest.json            # Metadata và mã băm SHA-256 toàn vẹn dữ liệu
│   └── README.md                # Đặc tả chi tiết từng tập dữ liệu theo Bảng 1
│
├── 📁 2_models_code/            # THƯ MỤC 2: TOÀN BỘ MÃ NGUỒN CÁC MÔ HÌNH THUẬT TOÁN
│   ├── blue_baselines/          # 5 mô hình cơ sở: K-means, FCM, PFCM, DP-FCM, DP-PFCM
│   ├── orange_comparisons/      # 3 mô hình so sánh metaheuristic: DP-PSO-PFCM, DP-SCA-PFCM, DP-FBI-PFCM
│   ├── purple_main_model/       # Mô hình chính đề xuất: DP-GA-PFCM (DPC -> GA -> PFCM)
│   ├── common/                  # Module thư viện: DPC, PFCM, Toán tử GA, Metrics (Purity, ARI, NMI), Thống kê
│   ├── configs/                 # Cấu hình tham số thực nghiệm (corrected_reference.json, paper_table5.json)
│   ├── tests/                   # Bộ kiểm thử 18 unit tests
│   ├── run_compare_all.py       # Script so sánh tất cả các mô hình
│   ├── run_visual_comparison.py # Script chạy thực nghiệm trực quan 10 datasets x 9 mô hình x 30 runs
│   ├── run_gaussian_outliers.py # Script chạy thử nghiệm độ bền vững nhiễu Gaussian (Nc=2, L=5, 0-20% outliers)
│   ├── requirements.txt         # Thư viện Python phụ thuộc
│   └── README.md                # Hướng dẫn chi tiết kiến trúc thuật toán
│
├── 📁 3_comparison_outputs/     # THƯ MỤC 3: ĐẦU RA ẢNH SO SÁNH CÁC MÔ HÌNH THEO THAM SỐ BÀI BÁO
│   ├── 00_XEM_NHANH_HTML/       # Dashboard trực quan HTML tương tác + file nhấp đúp MO_KET_QUA.cmd
│   ├── 01_tong_quan_cac_mo_hinh/# Heatmap 3 chỉ số Purity/ARI/NMI trên 10 bộ dữ liệu, biểu đồ xếp hạng tổng thể
│   ├── 02_so_sanh_tung_dataset_10_bo/
│   │   ├── bieu_do_chi_so_metrics/ # 10 biểu đồ cột so sánh Purity, ARI, NMI của từng dataset
│   │   └── hinh_anh_phan_cum_2d_pca/# 10 biểu đồ scatter plot phân cụm 2D PCA của từng dataset
│   ├── 03_so_sanh_do_ben_vung_ngoai_lai_gaussian/ # Đánh giá ngoại lai Gaussian (Nc=2, L=5, 0-20% outliers)
│   │   ├── 01_bang_ari_nc2_l5_outliers.png (Bảng Mean/Best ARI + Wilcoxon)
│   │   ├── 02_do_thi_bien_thien_ari_theo_outliers.png
│   │   ├── metrics_outliers_00_den_20pct.png
│   │   └── phan_cum_ngoai_lai_pca/
│   ├── 04_do_hoi_tu_va_thoi_gian_chay/ # Đồ thị hội tụ GA (100 thế hệ) & Biểu đồ Runtime (giây)
│   └── HUONG_DAN_DANH_GIA_KET_QUA.md # Hướng dẫn chi tiết đối chiếu ảnh với Bảng 6-8, 11-13 bài báo
│
├── 📁 4_documents/              # THƯ MỤC 4: TÀI LIỆU BÀI BÁO VÀ BÁO CÁO NGHIÊN CỨU
│   ├── 1-s2.0-S2215098623002033-main.pdf    # Bài báo gốc Elsevier
│   ├── 1-s2.0-S2215098623002033-main-vi.pdf # Bản dịch tiếng Việt bài báo
│   ├── danh-gia-kha-nang-tai-tao.md         # Báo cáo đánh giá mức độ tái tạo (65/100)
│   ├── DP-GA-PFCM-danh-dau-va-danh-gia-tai-tao.pdf # Bản PDF có đánh dấu phân tích chuyên gia
│   └── research_notes/                      # Ghi chú kiến trúc, bằng chứng thẩm định code
│
├── ⚡ XEM_KET_QUA.cmd            # Nhấp đúp: Mở ngay dashboard xem toàn bộ ảnh và kết quả so sánh
├── ⚡ CHAY_SO_SANH_10_DATASET.cmd # Nhấp đúp: Chạy lại thực nghiệm trực quan trên 10 datasets
└── ⚡ CHAY_THU_NGHIEM_GAUSSIAN.cmd# Nhấp đúp: Chạy thực nghiệm độ bền vững nhiễu ngoại lai
```

---

## 2. Hướng dẫn nhanh cho Người đánh giá

### Cách 1: Xem ngay toàn bộ ảnh và biểu đồ so sánh
- Nhấp đúp chuột vào file **`XEM_KET_QUA.cmd`** tại thư mục gốc, HOẶC
- Mở thư mục **`3_comparison_outputs/`** để xem trực tiếp các ảnh PNG được phân loại khoa học theo từng tham số:
  - Xem Heatmap tổng thể 10 bộ dữ liệu: `3_comparison_outputs/01_tong_quan_cac_mo_hinh/`
  - Xem chi tiết từng bộ dữ liệu: `3_comparison_outputs/02_so_sanh_tung_dataset_10_bo/`
  - Xem thử nghiệm chống nhiễu ngoại lai: `3_comparison_outputs/03_so_sanh_do_ben_vung_ngoai_lai_gaussian/`
  - Xem độ hội tụ GA & thời gian chạy: `3_comparison_outputs/04_do_hoi_tu_va_thoi_gian_chay/`
  - Đọc file hướng dẫn tra cứu đối chiếu bài báo: **`3_comparison_outputs/HUONG_DAN_DANH_GIA_KET_QUA.md`**

### Cách 2: Chạy lại thực nghiệm từ mã nguồn
- Chạy toàn diện 10 dataset chính: Nhấp đúp **`CHAY_SO_SANH_10_DATASET.cmd`**
- Chạy thử nghiệm Gaussian ngoại lai: Nhấp đúp **`CHAY_THU_NGHIEM_GAUSSIAN.cmd`**
- Chạy từ PowerShell / Terminal:
  ```powershell
  cd 2_models_code
  .venv\Scripts\python.exe run_visual_comparison.py
  ```

---

## 3. Các chỉ số đánh giá cốt lõi theo Bài báo
1. **Purity / Accuracy (Độ thuần khiết - Eq. 17)**: Tỷ lệ phân cụm chính xác (tối đa $1.0$).
2. **ARI (Adjusted Rand Index)**: Đo độ khớp phân cụm có hiệu chỉnh ngẫu nhiên (tối đa $1.0$).
3. **NMI (Normalized Mutual Information)**: Thông tin tương hỗ chuẩn hóa (tối đa $1.0$).
4. **Runtime**: Thời gian tính toán (giây).
5. **Độ bền vững ngoại lai**: Đánh giá sự ổn định của ARI khi tỷ lệ ngoại lai tăng từ $0\%$ đến $20\%$.
