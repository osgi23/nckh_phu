# Xem kết quả ở một nơi

Nhấp đúp **MO_KET_QUA.cmd** trong thư mục code, hoặc mở **results/00_XEM_KET_QUA.html** bằng trình duyệt.

Thư mục results chỉ có bốn mục để xem hằng ngày:

    results/
      00_XEM_KET_QUA.html          Trang xem và so sánh chính
      01_TONG_QUAN_10_BO.png       Heatmap ba chỉ số trên 10 bộ
      02_SO_SANH_2_BO_KMEANS.png   So sánh hai bộ K-means cao / thấp
      LUU_TRU/                    Toàn bộ lượt chạy, CSV, cấu hình và artifact

Trang HTML mặc định chọn lượt hoàn tất đủ 10 bộ × 9 phương pháp × ít nhất 30 lần. Nếu có nhiều lượt như vậy, chọn lượt mới nhất. Nút “Lượt mới nhất” và danh sách chọn cho phép xem cả lượt thử hoặc phạm vi riêng; các lượt không trộn số liệu với nhau.

Trong trang:
- Đổi Purity / ARI / NMI để xem bảng và chênh lệch với K-means.
- Hai bộ cao / thấp luôn chọn theo Purity trung bình của K-means, trên các bộ của đúng lượt đang xem.
- Bảng màu hiển thị mọi bộ và mọi phương pháp; ô viền xanh là tốt nhất trong từng bộ.
- Chọn một dataset để xem đầy đủ mean ± sample SD và hình phân cụm.
- Mở mục lượt chạy khác hoặc tải CSV nếu cần kiểm tra chi tiết.

## Chạy lại

Nhấp đúp **CHAY_SO_SANH.cmd**, hoặc chạy từ D:\DA_NCKHphu:

    code/.venv/Scripts/python.exe code/run_visual_comparison.py --jobs 4

Lệnh chính dùng 10 dataset, 9 phương pháp, 30 lần mỗi tổ hợp; population=80, generations=100. Mỗi lượt mặc định lưu ở results/LUU_TRU/<tên_thời_gian>. Khi hoàn tất, trang xem và hai ảnh xem nhanh tự cập nhật. Các lệnh run_compare_all.py và run.py của ba nhóm cũng lưu lượt mới vào LUU_TRU và làm mới trang.

Có thể chỉ định --output để tự chọn đường dẫn; đường dẫn chỉ định được giữ nguyên. Đặt nó dưới results/LUU_TRU nếu muốn lượt đó có trong danh sách của trang xem.

Để làm mới trang từ kết quả đã có, không chạy lại mô hình:

    code/.venv/Scripts/python.exe code/result_portal.py

Để gom các thư mục kết quả cũ nằm trực tiếp dưới results vào LUU_TRU:

    code/.venv/Scripts/python.exe code/result_portal.py --organize

Lệnh gom kiểm tra đường dẫn và SHA-256 toàn bộ file trước/sau khi chuyển, từ chối ghi đè thư mục trùng tên. Nhật ký chuyển nằm ở results/LUU_TRU/_sap_xep.json.

## Kết quả chính hiện có

Lượt visual_main10_2026-10-16 có 2.700 lần chạy thực tế. Theo Purity trung bình K-means: Wine cao nhất (0.9468), Glass thấp nhất (0.5592). DP-GA-PFCM đạt Purity 0.9504 trên Wine và 0.5380 trên Glass. Điểm số không bị thay đổi khi sắp xếp thư mục.

Màu xanh: phương pháp cơ sở; cam: thuật toán so sánh; tím: DP-GA-PFCM. GA-IFWCOM và SCA-FPCOM còn thiếu nguồn để triển khai trung thực; số công bố chỉ nằm trong bảng đối chiếu.

Profile corrected_reference.json dùng fitness FCM với w tham chiếu chung bằng 2 khi chấm optimizer; đây là hiệu chỉnh thực nghiệm chưa xác nhận trùng tác giả. Profile paper_table5.json giữ cách đọc FCM Eq.(6) literal. Các giới hạn còn lại ở ASSUMPTIONS.md.

Bốn bộ Pima, Room Occupancy, Rice và Wifi dành đánh giá riêng, không tham gia chọn hai bộ trong lượt chính. Hình PCA chỉ để quan sát; chỉ số tính từ nhãn phân cụm ở toàn bộ không gian đặc trưng.
