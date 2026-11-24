# HƯỚNG DẪN TẢI LÊN VÀ BIÊN DỊCH TRÊN OVERLEAF

Thư mục này chứa mã nguồn LaTeX chuẩn mực của bài báo khoa học theo định dạng Elsevier / JESTECH.

## 1. Các file trong thư mục:
- `main.tex`: Toàn bộ nội dung bài báo khoa học hoàn chỉnh (Tiêu đề, Tóm tắt, Cơ sở lý thuyết, Bóc tách lỗ hổng toán học, Phương pháp đề xuất SD-MGA-PFCM, Bảng thực nghiệm 30 runs, Kiểm định Wilcoxon, Kết luận).
- `references.bib`: Danh mục tài liệu tham khảo chuẩn BibTeX (Kuo et al. 2023, Rodriguez & Laio 2014, Pal et al. 2005, v.v.).

## 2. Cách tải lên Overleaf (2 cách đơn giản):

### Cách 1: Nén ZIP và tải lên trực tiếp (Khuyên dùng - 30 giây)
1. Chọn cả 2 file `main.tex` và `references.bib`, nén thành file `paper_sd_mga_pfcm.zip`.
2. Truy cập [Overleaf](https://www.overleaf.com), bấm **New Project** $\to$ **Upload Project**.
3. Chọn file `paper_sd_mga_pfcm.zip` vừa tạo.
4. Bấm **Recompile** trên Overleaf: Bài báo sẽ được xuất ra bản PDF 2 cột hoặc 1 cột chuẩn mực của Elsevier!

### Cách 2: Sao chép thủ công (Copy - Paste)
1. Trên Overleaf, tạo một **Blank Project**.
2. Mở file `main.tex` trên máy tính, copy toàn bộ nội dung và dán đè vào file `main.tex` trên Overleaf.
3. Trên Overleaf, bấm nút **New File** (biểu tượng trang giấy), đặt tên là `references.bib`.
4. Mở file `references.bib` trên máy tính, copy toàn bộ nội dung và dán vào `references.bib` trên Overleaf.
5. Bấm **Recompile** để xem bản PDF.
