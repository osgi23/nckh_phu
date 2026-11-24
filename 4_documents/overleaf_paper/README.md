# SD-MGA-PFCM Research Paper

> **Spatial-Diversity Memetic Genetic Algorithm Possibilistic Fuzzy C-Means (SD-MGA-PFCM): Overcoming Mathematical Vulnerabilities in Density Peak Evolutionary Clustering**

📄 **[Đọc trực tiếp bài báo hoàn chỉnh (PDF)](./SD_MGA_PFCM_Research_Paper.pdf)**

---

## Tóm tắt đóng góp (Key Contributions)

Bài báo phân tích 3 lỗ hổng toán học hệ thống trong khung phân cụm lai **DP-GA-PFCM** (Kuo et al., 2023 - JESTECH, Elsevier) và đề xuất mô hình **SD-MGA-PFCM** với 3 đóng góp độc lập:

1. **Diversity-Preserving DPC (D-DPC):** Tích hợp nhân phân tán tham lam (*Greedy Dispersion Kernel*) nhằm đảm bảo đa dạng không gian khi chọn $K$ đỉnh mật độ ban đầu, ngăn chặn tình trạng dồn nhiều tâm vào cụm có mật độ cao nhất.
2. **Inter-Cluster Separation Regularizer & Repulsion Barrier:** Bổ sung số hạng điều chuẩn phân tách liên cụm $\mathcal{R}_{\text{sep}}(V)$ và rào cản phạt suy biến $\mathcal{P}_{\text{barrier}}(V)$, triệt tiêu hoàn toàn hiện tượng sụp đổ tâm cụm (*coincident clusters*).
3. **Memetic Lamarckian Local Search & Reference Fuzzifier:** Nhúng bước cập nhật đạo hàm giải tích PFCM trực tiếp vào quá trình tiến hóa của GA kèm đánh giá hàm thích nghi theo số mũ mờ chuẩn hóa ($w_{\text{ref}} = 2.0$), giúp hội tụ nhanh và ổn định trên không gian nhiều chiều.

Thử nghiệm kiểm định Ablation Study trên **8 bộ dữ liệu chuẩn** với **30 lần chạy độc lập** (tổng 1.200 thực nghiệm) và kiểm định phi tham số **Wilcoxon signed-rank test** khẳng định sự vượt trội có ý nghĩa thống kê trên toàn bộ 8/8 tập dữ liệu ($p < 0.001$).

---

## Cấu trúc thư mục

- [`SD_MGA_PFCM_Research_Paper.pdf`](./SD_MGA_PFCM_Research_Paper.pdf): Bản PDF hoàn chỉnh của bài báo (xem trực tiếp trên GitHub).
- [`main.tex`](./main.tex): Mã nguồn LaTeX hoàn chỉnh theo định dạng `elsarticle` (Elsevier / JESTECH).
- [`references.bib`](./references.bib): Danh mục tài liệu tham khảo chuẩn BibTeX.
- [`COVER_LETTER.tex`](./COVER_LETTER.tex): Thư gửi Tổng biên tập (Cover Letter) theo mẫu nộp tạp chí.
- [`figures/`](./figures/): Các biểu đồ vector (`.pdf` và `.png`) sử dụng trong bài báo (`boxplot_30runs`, `convergence_curves`).
