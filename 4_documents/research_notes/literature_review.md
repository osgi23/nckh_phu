# Khảo sát tài liệu — cải tiến DP-GA-PFCM

Ngày lập: 2026-11-05. Phục vụ Giai đoạn 1 của quy trình nghiên cứu.

## 0. Mức xác minh của từng nguồn

Session nghiên cứu này bị giới hạn mạng. Các domain `arxiv.org`, `www.sciencedirect.com`,
`link.springer.com`, `pmc.ncbi.nlm.nih.gov`, `papers.nips.cc`, `dl.acm.org`,
`ieeexplore.ieee.org`, `api.semanticscholar.org` đều **không truy cập được** (DNS
không phân giải, curl trả về mã 000). Vì vậy mỗi nguồn dưới đây được gắn một nhãn
mức xác minh, và nhãn này phải được giữ nguyên khi trích dẫn ở bất kỳ báo cáo nào
sau này:

| Nhãn | Nghĩa |
|---|---|
| **[A] Đã đọc toàn văn** | Đã mở và đọc trực tiếp toàn bộ nội dung trong session này. |
| **[B] Metadata + trích đoạn** | Chỉ có tiêu đề, tác giả, nơi công bố, DOI/URL và các câu trích dẫn do web search trả về. **Chưa đọc toàn văn.** Không được dẫn số liệu cụ thể từ các nguồn này như thể đã kiểm chứng. |
| **[C] Chưa xác minh** | Có dấu hiệu mâu thuẫn giữa các nguồn, cần kiểm tra lại trước khi dùng. |

Chỉ có **2 nguồn ở mức [A]**, và cả hai đều là nguồn nền trực tiếp của dự án. Đây là
hạn chế thật của lượt khảo sát này, không phải lựa chọn thiết kế.

---

## 1. Bảng khảo sát

### 1.1. Nền tảng trực tiếp của dự án (mức [A])

| Paper (tác giả, năm, link) | Ý tưởng chính | Dataset / Metric | Kết quả | Hạn chế | Áp dụng được cho bài toán của tôi? |
|---|---|---|---|---|---|
| **[A]** Kuo R.J. và cộng sự (2023). *Genetic based density peak possibilistic fuzzy c-means algorithms to cluster analysis — a case study on customer segmentation.* Engineering Science and Technology, an International Journal 47:101525. [DOI 10.1016/j.jestch.2023.101525](https://doi.org/10.1016/j.jestch.2023.101525). Đọc từ PDF trong `4_documents/`. | DPC chọn tâm khởi tạo → GA tối ưu đồng thời tâm cụm và bốn tham số PFCM (a, b, w, η) → PFCM tinh chỉnh. Hai giai đoạn thực nghiệm: so với 4 baseline mờ, rồi so với PSO/SCA/FBI và hai phương pháp ngoài. | 14 benchmark UCI + shape datasets. Accuracy (purity, Eq.17), ARI, NMI, Kruskal–Wallis + Dunn–Bonferroni. | Table 11: A2 (DP-GA-PFCM) tổng rank accuracy **31**, thấp nhất trong 7 phương pháp. Iris 0.914, Wine 0.955, Glass 0.581. Table 12 ARI: A2 tổng rank 44, xếp sau A1 (DP-PFCM, 58)? — không, A2 tốt hơn. | **Đây chính là các mâu thuẫn tôi phải xử lý.** (i) Step 6 ghi nguyên văn: *"Evaluate the chromosomes in the population to minimize the within-cluster sum of squared errors using PFCM algorithm (Eq. (6)."* — nhưng Eq.(6) là objective của FCM, objective PFCM nằm ở Eq.(11), và "within-cluster SSE" lại là khái niệm thứ ba. (ii) Table 5 chỉ cho population=80, max iteration=100, crossover=0.8, mutation=0.1; **không có miền tìm kiếm cho a, b, w, η**. (iii) Table 11 ghi Glass/A1 = 0.066 còn Table 6 ghi 0.566 — gần như chắc là lỗi in. (iv) Mutation rate 0.1 ở Table 5 không nằm trong hai mức 0.01/0.03 của phần tuning. | Có — là baseline bắt buộc. Nhưng **không thể tái tạo trung thực nếu không công bố giả định**, vì fitness và miền tham số đều chưa xác định. |
| **[A]** Tinós R., Zhao L., Chicano F., Whitley D. (2018). *NK Hybrid Genetic Algorithm for Clustering.* IEEE Transactions on Evolutionary Computation. Preprint [arXiv:2402.03813](https://arxiv.org/abs/2402.03813) (trang abstract **không mở được**; metadata lấy từ search). **Source code đã clone và đọc toàn văn:** [github.com/rtinos/NKGAclust](https://github.com/rtinos/NKGAclust). | Biểu diễn nghiệm bằng vector nhãn N chiều (0 = nhiễu). Fitness NKCV2 phân rã thành các factor cục bộ trên đồ thị K+1 láng giềng. Partition crossover (PX) tách fitness thành q thành phần độc lập và trả về nghiệm tốt nhất trong 2^q con. | Trong repo code: `Compound.dat` (Zahn's Compound). Nghiệm khởi tạo mẫu từ k-means, DBSCAN và DP clustering. | Abstract (mức [B]): phát hiện cụm hình dạng bất kỳ, tự động xác định số cụm, PX có độ phức tạp O(N). | Code xác nhận các chi tiết mà bài báo không nhấn mạnh: ngưỡng `dt0, dt1, dt2` được đặt bằng `threeSigmaRule` trên **khoảng cách Euclidean của các cạnh** (`dt0 = mean`, `dt1 = mean + 2σ`, `dt2 = mean + σ` — lưu ý dt2 < dt1, khác thứ tự tên gọi), nên mọi thay đổi thang đo khoảng cách đều buộc phải tính lại ba ngưỡng này. | Có. Đây là nền của hướng AF-NKGA trong `kien_truc_nghien_cuu_adaptive_fuzzy_nkga.md`. Các hàm `fixLabels`, `dfElement`, `LsFi`, `mutationMerge`, `mutationSplit`, `px` đều tồn tại thật trong `nk.h`, nên thiết kế trong ghi chú đó có cơ sở code, không phải suy diễn. |

### 1.2. Nền tảng phương pháp PFCM và DPC (mức [B])

| Paper | Ý tưởng chính | Dataset / Metric | Kết quả | Hạn chế | Áp dụng được? |
|---|---|---|---|---|---|
| **[B][C]** Pal N.R., Pal K., Keller J.M., Bezdek J.C. (2005). *A possibilistic fuzzy c-means clustering algorithm.* IEEE Trans. Fuzzy Systems 13(4):517–530. [IEEE record](https://ieeexplore.ieee.org/document/1492404). | Kết hợp membership (FCM) và typicality (PCM); bỏ ràng buộc tổng typicality theo cột của FPCM. | Không rõ từ trích đoạn. | Trích đoạn abstract: PFCM "thường tránh được các vấn đề của PCM, FCM và FPCM"; tâm cụm ít nhạy cảm với ngoại lai hơn và tránh được cụm trùng. | **[C]** Hai nguồn cho hai DOI khác nhau: `10.1109/TFUZZ.2004.840845` và `10.1109/TFUZZ.2004.840099`. **Phải kiểm tra lại trước khi trích dẫn DOI.** | Có — đây là định nghĩa gốc của a, b, w, η mà GA đang tối ưu. Cần đọc toàn văn để biết tác giả gốc khuyến nghị miền giá trị nào. |
| **[B]** *Revisiting Possibilistic Fuzzy C-Means Clustering Using the Majorization-Minimization Method* (2024). [PMC11353294](https://pmc.ncbi.nlm.nih.gov/articles/PMC11353294/). | Dùng majorization–minimization thay cho cập nhật luân phiên của PFCM. | Không rõ. | Trích đoạn: PFCM "có xu hướng tìm được cực tiểu địa phương dưới mức tối ưu, làm giảm hiệu năng". | Chưa đọc toàn văn, chưa biết mức cải thiện. | **Rất liên quan.** Đây là bằng chứng độc lập cho lý do chính đáng của việc gắn một bộ tối ưu toàn cục vào PFCM — tức là lý do tồn tại của cả dòng DP-GA-PFCM. |
| **[B]** Rodriguez A., Laio A. (2014). *Clustering by fast search and find of density peaks.* Science 344(6191):1492–1496. [DOI 10.1126/science.1242072](https://doi.org/10.1126/science.1242072). | Tâm cụm = cực đại mật độ địa phương nằm xa mọi điểm có mật độ cao hơn. | Không rõ từ trích đoạn. | Abstract: số cụm tự xuất hiện, ngoại lai tự được loại, cụm có hình dạng bất kỳ. | Tài liệu package R `densityClust` ghi tác giả khuyến nghị neighbor rate 1–2%; đây là **heuristic**, không phải quy tắc. Khớp với con số "cutoff 2%" của bài Kuo nhưng vẫn không xác định 2% là phân vị của đại lượng nào. | Có — là thành phần DPC trong pipeline. |
| **[B]** *Fuzzy weighted natural nearest neighbor based density peak clustering* (2025). [PMC12855208](https://pmc.ncbi.nlm.nih.gov/articles/PMC12855208/). | Thay mật độ theo cutoff bằng mật độ theo láng giềng tự nhiên có trọng số mờ. | Không rõ. | Không rõ. | Chưa đọc toàn văn. | Có. Nêu đúng hai điểm yếu của DPC mà dự án đang gặp: nhạy cảm với cutoff tùy ý, và "domino effect" ở bước gán nhãn. |
| **[B]** *Density peaks clustering based on balance density and connectivity* (2022). Pattern Recognition. [S0031320322005325](https://www.sciencedirect.com/science/article/abs/pii/S0031320322005325). | Cân bằng mật độ và tính liên thông. | Không rõ. | Không rõ. | Chưa đọc toàn văn. | Có. Trích đoạn nêu: DPC "không cho kết quả tốt trên dữ liệu có chênh lệch mật độ lớn giữa các cụm" — đúng trường hợp Glass và Ecoli. |
| **[B]** *Adaptive density peak clustering based on Delaunay graph* (2025). PLOS ONE. [DOI 10.1371/journal.pone.0325161](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0325161). | Dùng đồ thị Delaunay để bỏ tham số đặt tay, kể cả cutoff và số cụm. | Không rõ. | Không rõ. | Chưa đọc toàn văn; PLOS ONE không chuyên về clustering. | Có thể — là một hướng thay thế cho việc chọn cutoff, nhưng đổi nhiều cơ chế một lúc. |
| **[B]** *Optimization of Density Peak Clustering Algorithm Based on Improved Black Widow Algorithm* (2024). [PMC11154350](https://pmc.ncbi.nlm.nih.gov/articles/PMC11154350/). | Metaheuristic chọn cutoff d_c tự động. | Không rõ. | Không rõ. | Trích đoạn tự nhận: tự động hóa được d_c nhưng **số tâm cụm K vẫn phải đặt tay**. | Hạn chế — không giải quyết phần khó. |

### 1.3. Chọn fuzzifier và tham số mờ (mức [B])

| Paper | Ý tưởng chính | Dataset / Metric | Kết quả | Hạn chế | Áp dụng được? |
|---|---|---|---|---|---|
| **[B]** Zhou K., Fu C., Yang S. *Fuzziness parameter selection in fuzzy c-means: The perspective of cluster validation.* Science China Information Sciences. [DOI 10.1007/s11432-014-5146-0](https://doi.org/10.1007/s11432-014-5146-0). | Chọn m bằng cách tối thiểu hóa chỉ số validity. | Không rõ. | Trích đoạn: miền m là [2, 3.5], khoảng tối ưu [2.5, 3]. | Công bố khoảng 2014, chỉ cho FCM thuần. | **Rất liên quan.** Cho một miền có cơ sở văn liệu cho `w`, thay vì miền [1.1, 5] tự đặt trong `configs/`. |
| **[B]** Wu K.-L. *Analysis of parameter selections for fuzzy c-means.* Pattern Recognition. [S0031320311003001](https://www.sciencedirect.com/science/article/abs/pii/S0031320311003001). | Phân tích độ bền vững theo m. | Không rõ. | Trích đoạn: m lớn làm FCM bền hơn với nhiễu và ngoại lai; khuyến nghị m=4 cho dữ liệu nhiễu. | Hướng ngược với Zhou và cộng sự. | **Quan trọng và mâu thuẫn.** Hai nguồn này chỉ ra `w` lớn có thể là *lựa chọn hợp lý* trên dữ liệu nhiễu, nên không được mặc định coi `w` sát cận trên là dấu hiệu sai. Phải phân biệt "w lớn vì bền với nhiễu" và "w lớn vì hạ được thang loss". |
| **[B]** *Fuzzifier Selection in Fuzzy C-Means from Cluster Size Distribution Perspective.* Informatica. [informatica.vu.lt](https://informatica.vu.lt/journal/INFORMATICA/article/1124/text). | Chọn m theo mức thay đổi của phân bố kích thước cụm. | Không rõ. | Không rõ. | Chưa đọc toàn văn. | Có thể — là một tiêu chí **không dùng nhãn thật**, phù hợp yêu cầu không gian lận. |
| **[B]** *A feature-weighted suppressed possibilistic fuzzy c-means clustering algorithm* (2023). Expert Systems with Applications. [S0957417423027720](https://www.sciencedirect.com/science/article/abs/pii/S0957417423027720). | PFCM có trọng số đặc trưng và cơ chế suppression. | Không rõ (ứng dụng phân vùng ảnh màu). | Không rõ. | Chưa đọc toàn văn; miền ứng dụng là ảnh. | Có thể — hướng mở rộng PFCM theo trọng số đặc trưng. |

### 1.4. Lai metaheuristic với clustering mờ (mức [B])

| Paper | Ý tưởng chính | Dataset / Metric | Kết quả | Hạn chế | Áp dụng được? |
|---|---|---|---|---|---|
| **[B]** *Optimizing kernel possibilistic fuzzy C-means clustering using metaheuristic algorithms* (2023). Evolving Systems. [DOI 10.1007/s12530-023-09542-9](https://doi.org/10.1007/s12530-023-09542-9). | GA / metaheuristic tối ưu KPFCM. | Không rõ. | Trích đoạn: có biến thể GA-KPFCM, báo cải thiện so với PFCM và KPFCM truyền thống. | Không có thành phần density peak. Chưa đọc toàn văn. | Có — là công trình gần nhất về mặt "GA tối ưu PFCM", cần đọc để biết họ chọn fitness nào. |
| **[B]** *Hybrid fuzzy clustering technique ... intuitionistic modified fuzzy c-means and improved genetic algorithm* (2023). [ResearchGate](https://www.researchgate.net/publication/376519760_Hybrid_fuzzy_clustering_technique_to_enhance_the_performance_based_on_a_fusion_of_intuitionistic_modified_fuzzy_c-means_and_improved_genetic_algorithm). | Lai IFCM với GA cải tiến để giảm phụ thuộc tâm khởi tạo. | Không rõ. | Không rõ. | Không dùng PFCM hay density peak. | Liên quan gián tiếp — cùng dòng với A6 (GA-IFWCOM) mà bài Kuo so sánh nhưng dự án chưa triển khai. |
| **[B]** *Recombinator-k-means: An evolutionary algorithm that exploits k-means++ for recombination.* [arXiv:1905.00531](https://arxiv.org/abs/1905.00531) (không mở được). | Tái tổ hợp bằng cách thay hai tâm của một nghiệm bằng hai tâm của nghiệm khác, rồi tinh chỉnh bằng Lloyd. | Không rõ. | Không rõ. | Chưa đọc toàn văn. | **Rất liên quan.** Thiết kế này **tránh lai số học trên tọa độ tâm** — đúng vấn đề tôi nghi ngờ ở `dp_ga_pfcm.py`, và theo trích đoạn thì tái tổ hợp luôn đi kèm bước tinh chỉnh, tức là theo kiểu Lamarckian. |

### 1.5. Vấn đề hoán vị nhãn và toán tử lai (mức [B])

| Paper | Ý tưởng chính | Dataset / Metric | Kết quả | Hạn chế | Áp dụng được? |
|---|---|---|---|---|---|
| **[B]** *Hierarchical clustering with discrete latent variable models and the integrated classification likelihood.* [arXiv:2002.11577](https://arxiv.org/abs/2002.11577) (không mở được). | Hàm mục tiêu ICL bất biến với hoán vị chỉ số cụm, nên biểu diễn bị **dư thừa nặng**; đề xuất toán tử "cross-partition" không bị label switching. | Không rõ. | Không rõ. | Chưa đọc toàn văn; bài toán là mô hình biến tiềm ẩn, không phải PFCM. | **Rất liên quan.** Trích đoạn nói thẳng: các toán tử crossover theo điểm cắt "sẽ không xét tới đặc thù này và sẽ phá hoàn toàn cấu trúc của nghiệm". Đây là cơ sở văn liệu cho giả thuyết H2. |
| **[B]** *Genetic algorithms and permutation problems: a comparison of recombination operators for neural net structure specification* (1992). [IEEE 273944](https://ieeexplore.ieee.org/document/273944/). | Vấn đề "competing conventions" / hoán vị trong GA. | Mạng nơ-ron. | Trích đoạn: toán tử sắp xếp các đơn vị ẩn theo độ chồng lấn trước khi lai cho kết quả tốt nhất, **nhưng crossover đơn giản cũng làm khá tốt**, gợi ý rằng vấn đề hoán vị "không nghiêm trọng trong thực tế". | Rất cũ, miền khác. | **Phải dẫn như bằng chứng đối lập.** Nó cảnh báo rằng H2 có thể không cho cải thiện, nên H2 bắt buộc phải kiểm chứng thực nghiệm chứ không được giả định. |
| **[B]** *Clumppling: cluster matching and permutation program with integer linear programming* (2024). [PMC10766593](https://pmc.ncbi.nlm.nih.gov/articles/PMC10766593/). | Khớp nhãn cụm giữa các lần chạy bằng ILP, có xử lý khi số cụm lệch nhau. | Di truyền quần thể. | Không rõ. | Miền khác. | Có — là tham chiếu kỹ thuật cho bước khớp tâm bằng Hungarian/ILP. |
| **[B]** *Clustering Using A Genetic Algorithm Combining Validation Criteria.* ESANN 2007. [PDF](https://www.esann.org/sites/default/files/proceedings/legacy/es2007-76.pdf). | GA clustering với crossover theo tâm: phân phối ngẫu nhiên các tâm của hai cá thể vào hai con. | Không rõ. | Không rõ. | Không xử lý khớp hoán vị. | Có — một dạng crossover thay thế cho lai số học. |

### 1.6. Memetic và Lamarckian (mức [B])

| Paper | Ý tưởng chính | Dataset / Metric | Kết quả | Hạn chế | Áp dụng được? |
|---|---|---|---|---|---|
| **[B]** *Baldwin effect and Lamarckian evolution in a memetic algorithm for Euclidean Steiner tree problem* (2018). Memetic Computing. [DOI 10.1007/s12293-018-0256-7](https://doi.org/10.1007/s12293-018-0256-7). | So sánh trực tiếp Baldwin và Lamarck: ghi gene đã cải thiện trở lại nhiễm sắc thể với một xác suất đặt trước. | Euclidean Steiner tree. | Trích đoạn: xét cả hiệu năng trung bình và số lần tìm được nghiệm tốt nhất, **nên chọn biến thể Lamarckian**. | **Miền hoàn toàn khác** (bài toán cây Steiner, không phải clustering). Không chuyển kết luận sang đây được. | Có, như **cơ sở cơ chế** cho H1: ghi ngược kết quả local search vào gene thường tốt hơn. Nhưng kết luận phải tự kiểm chứng trên dữ liệu của mình. |
| **[B]** *An improved adaptive memetic differential evolution optimization algorithms for data clustering problems* (2019). PLOS ONE. [DOI 10.1371/journal.pone.0216906](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0216906). | DE memetic cho clustering. | Không rõ. | Trích đoạn liên quan: các bước memetic cải thiện hiệu quả bằng cách tránh hội tụ sớm. | Chưa đọc toàn văn. | Có — cùng cơ chế với H1. |

### 1.7. Chỉ số validity làm fitness, và cách đánh giá trung thực (mức [B])

| Paper | Ý tưởng chính | Dataset / Metric | Kết quả | Hạn chế | Áp dụng được? |
|---|---|---|---|---|---|
| **[B]** *Cluster validity indices for automatic clustering: A comprehensive review* (2025). Heliyon. [PMC11787482](https://pmc.ncbi.nlm.nih.gov/articles/PMC11787482/). | Tổng quan hệ thống các chỉ số validity nội tại dùng làm fitness trong clustering bằng metaheuristic. | Nhiều. | Không rõ. | Chưa đọc toàn văn. | **Rất liên quan.** Khẳng định việc dùng CVI làm fitness là một dòng nghiên cứu đã có, nên thay fitness của bài Kuo bằng một CVI là hướng có cơ sở. |
| **[B]** *A survey of cluster validity indices for automatic data clustering using differential evolution* (2021). GECCO. [DOI 10.1145/3449639.3459341](https://doi.org/10.1145/3449639.3459341). | Thử 22 CVI làm fitness trong ACDE. | Nhiều bộ tổng hợp và thực. | Trích đoạn: Silhouette tốt ổn định trên dữ liệu phân tách tuyến tính; Calinski–Harabasz, Davies–Bouldin và generalized Dunn tốt trên cả dữ liệu tổng hợp và thực. | Chưa đọc toàn văn; kết quả phụ thuộc ACDE. | **Rất liên quan.** Cho một danh sách CVI ứng viên đã được xếp hạng thực nghiệm, thay vì tôi tự chọn. |
| **[B]** *Benchmarking validity indices for evolutionary K-means clustering performance* (2025). Scientific Reports. [s41598-025-08473-6](https://www.nature.com/articles/s41598-025-08473-6). | So sánh 15 CVI làm fitness cho Enhanced Firefly-K-means. | Không rõ. | Trích đoạn: việc chọn một chỉ số validity nội tại cụ thể "có thể ảnh hưởng nghiêm trọng" tới chất lượng cụm thu được. | Chưa đọc toàn văn. | Có — củng cố rằng chọn fitness là quyết định thiết kế quan trọng, cần ablation. |
| **[B]** *An Evaluative Measure of Clustering Methods Incorporating Hyperparameter Sensitivity* (2022). AAAI. [ojs.aaai.org](https://ojs.aaai.org/index.php/AAAI/article/view/20747). | Đề xuất báo cáo độ nhạy siêu tham số song song với hiệu năng tối ưu. | Không rõ. | Trích đoạn: xếp hạng phương pháp theo điểm tốt nhất sau khi tinh chỉnh trên các metric dùng nhãn như Rand index và NMI là "không khớp với cách các thuật toán này được dùng trong thực tế", nơi không có nhãn và việc tinh chỉnh phần lớn là phỏng đoán. | Chưa đọc toàn văn. | **Rất liên quan — ràng buộc trực tiếp lên protocol của tôi.** Đây là cơ sở văn liệu cho việc tôi không được chọn cấu hình bằng ARI trên 10 bộ chính. |
| **[B]** *On the benchmarking of clustering algorithms and hyperparameter influence for cell type detection in single-cell RNA sequencing data* (2025, preprint). [bioRxiv 10.1101/2025.08.20.671270](https://www.biorxiv.org/content/10.1101/2025.08.20.671270v1.full). | Đánh giá trên toàn không gian siêu tham số thay vì một cấu hình đã tinh chỉnh. | scRNA-seq. | Trích đoạn: "dựa vào giá trị mặc định, phỏng đoán 'mù', hoặc tinh chỉnh siêu tham số để khớp với số cụm vốn chưa biết trong nhãn, đều làm hỏng tính công bằng của đánh giá"; đề xuất báo cáo cả độ bền vững, hiệu năng kỳ vọng và hiệu năng tốt nhất. | **Preprint, chưa peer-review.** Miền sinh học. | Có, như cơ sở phương pháp luận. Trực tiếp hỗ trợ việc tách Mean-run và Best-run, và việc báo cáo cả ngân sách lẫn độ phân tán. |

---

## 2. Tổng hợp xu hướng

1. **Gắn bộ tối ưu toàn cục vào PFCM là hướng có cơ sở, không phải lai ghép tùy ý.** Nguồn độc lập [PMC11353294] nêu PFCM có xu hướng rơi vào cực tiểu địa phương dưới mức tối ưu. Dòng DP-GA-PFCM, GA-KPFCM và DP-PSO/SCA/FBI-PFCM đều nằm trong xu hướng này.
2. **Fitness là biến thiết kế quan trọng nhất, và văn liệu đã chuyển sang dùng CVI.** Ba nguồn độc lập về CVI-làm-fitness cho thấy việc chọn chỉ số ảnh hưởng mạnh tới kết quả, và đã có xếp hạng thực nghiệm giữa các chỉ số. Trong khi đó bài Kuo dùng một objective của chính thuật toán clustering (Eq.6 hoặc Eq.11) làm fitness — cách làm cũ hơn và, như phần 3 sẽ chỉ ra, có lỗ hổng khi fuzzifier cũng là biến tối ưu.
3. **Hoán vị nhãn/tâm làm biểu diễn dư thừa, nhưng mức độ nghiêm trọng còn tranh cãi.** Nguồn 2020 nói crossover theo điểm cắt "phá hoàn toàn cấu trúc nghiệm"; nguồn 1992 lại nói vấn đề này "không nghiêm trọng trong thực tế". Cách lành mạnh duy nhất là thử nghiệm trên chính dữ liệu của mình.
4. **DPC có hai điểm yếu được ghi nhận rộng rãi**: phụ thuộc cutoff tùy ý và kém trên dữ liệu chênh lệch mật độ lớn giữa các cụm. Các cải tiến đi theo hai nhánh: tự động chọn cutoff, hoặc bỏ cutoff bằng mật độ theo láng giềng.
5. **Cộng đồng đang siết lại chuẩn đánh giá clustering.** Hai nguồn (AAAI 2022 và bioRxiv 2025) nói rõ việc tinh chỉnh siêu tham số theo metric có nhãn làm mất ý nghĩa của so sánh. Điều này ràng buộc trực tiếp protocol của dự án.

## 3. Những gì văn liệu **không** trả lời được cho tôi

Phải ghi rõ để không lấp bằng suy diễn:

- **Không nguồn nào cho biết Kuo và cộng sự thực sự dùng fitness nào.** Mâu thuẫn Eq.(6) / Eq.(11) / "within-cluster SSE" chỉ có thể giải quyết bằng cách liên hệ tác giả hoặc xin code gốc.
- **Không có head-to-head Lamarckian vs Baldwinian cho FCM/PFCM.** Nguồn gần nhất là bài toán cây Steiner.
- **Không có nguồn nào chỉ ra miền tìm kiếm hợp lý cho (a, b, η) của PFCM** khi chúng là biến tối ưu. Văn liệu về fuzzifier chỉ bàn `m` (tương ứng `w`), và hai nguồn còn mâu thuẫn nhau.
- **Chưa truy cập được toàn văn của 18/20 nguồn.** Mọi số liệu ở mức [B] trong tài liệu này là trích đoạn do search trả về, không phải kết quả tôi đã đọc và kiểm tra trong ngữ cảnh.

## 4. Việc cần làm để nâng mức xác minh

1. Mở `arxiv.org`, `www.sciencedirect.com`, `link.springer.com`, `pmc.ncbi.nlm.nih.gov`, `papers.nips.cc`, `dl.acm.org`, `ieeexplore.ieee.org` trong Network access của environment, rồi đọc lại toàn văn các nguồn đánh dấu **Rất liên quan**.
2. Ưu tiên đọc toàn văn theo thứ tự: (i) Pal và cộng sự 2005 để lấy miền tham số gốc, (ii) GECCO 2021 để chọn CVI ứng viên, (iii) arXiv 2402.03813 để đối chiếu với code NKGAclust đã đọc, (iv) AAAI 2022 để chốt cách báo cáo độ nhạy.
3. Kiểm tra lại DOI của Pal và cộng sự 2005 (hai nguồn cho hai số khác nhau).
