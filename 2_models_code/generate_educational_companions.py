# -*- coding: utf-8 -*-
"""
Generate educational companion files for the user:
1. GIAI_THICH_TOAN_HOC_VA_KIEN_TRUC_SD_MGA_PFCM.html (Interactive visual web guide)
2. CAM_NANG_HOC_THUAT_VA_BAO_VE_BAI_BAO.docx (Word handbook for defense preparation)
"""
from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

DOCS_DIR = Path("d:/nckh_phu/4_documents")
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------------
# 1. BUILD INTERACTIVE HTML EXPLANATION GUIDE
# -------------------------------------------------------------------
def build_html_guide():
    from fix_html_mathjax import generate_giai_thich_html
    generate_giai_thich_html()
    print('HTML guide updated successfully via fix_html_mathjax.')

# -------------------------------------------------------------------
# 2. BUILD DOCX DEFENSE MANUAL
# -------------------------------------------------------------------
def build_docx_handbook():
    doc = docx.Document()
    for s in doc.sections:
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_title.add_run("TÀI LIỆU HƯỚNG DẪN BẢO VỆ & NẮM VỮNG BÀI BÁO\n")
    r_sub.font.bold = True
    r_sub.font.size = Pt(11)
    r_sub.font.color.rgb = RGBColor(0x71, 0x80, 0x96)

    r_main = p_title.add_run("CẨM NANG TOÀN DIỆN MÔ HÌNH PHÂN CỤM SD-MGA-PFCM")
    r_main.font.bold = True
    r_main.font.size = Pt(17)
    r_main.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)

    doc.add_heading("1. KIẾN TRÚC MÔ HÌNH: 3 PHA VÀ VAI TRÒ CỦA TỪNG THÀNH PHẦN", level=1)
    doc.add_paragraph(
        "Mô hình SD-MGA-PFCM được chia thành 3 giai đoạn liên kết chặt chẽ:\n"
        "• Pha 1 - D-DPC (Khởi tạo đỉnh mật độ phân tán): Trách nhiệm là tìm ra K điểm xuất phát nằm rải đều trên K cụm khác nhau. D-DPC khắc phục hiện tượng DPC truyền thống bị dồn toàn bộ tâm vào cụm đông nhất.\n"
        "• Pha 2 - Memetic GA (Tối ưu hóa toàn cục & cục bộ lai ghép): Nhiễm sắc thể mã hóa K tâm cụm và 4 tham số {m, eta, a, b}. Điểm đột phá là mỗi cá thể được trượt dốc đạo hàm PFCM 1 bước (Lamarckian) và bị kiểm soát bởi hàm phạt đẩy phân tách R_sep, ngăn ngừa tuyệt đối hiện tượng sụp đổ tâm cụm.\n"
        "• Pha 3 - PFCM Hội tụ mịn: Nhận nghiệm tối ưu từ GA và chạy tiếp các vòng lặp cập nhật ma trận thành viên U và khả năng T cho đến khi hàm mất mát không đổi."
    )

    doc.add_heading("2. GIẢI NGHĨA CÁC KÝ HIỆU TOÁN HỌC TRONG BÀI BÁO", level=1)
    doc.add_paragraph(
        "1. u_ik (Membership): Độ thuộc mờ. Điểm x_i thuộc cụm k với xác suất bao nhiêu. Ràng buộc tổng theo k bằng 1.\n"
        "2. t_ik (Typicality): Độ điển hình khả năng. Đo mức độ điểm x_i có thực sự là một mẫu chuẩn của cụm k hay chỉ là điểm nhiễu. Không bị ép tổng bằng 1.\n"
        "3. m (Fuzzifier): Số mũ mờ (1.1 đến 3.0). Càng lớn thì ranh giới giữa các cụm càng nhòe (mờ).\n"
        "4. eta (Typicality exponent): Số mũ khả năng (1.1 đến 3.0).\n"
        "5. a và b: Trọng số điều hòa giữa thành phần mờ và khả năng. Nếu b quá lớn trên không gian nhiều chiều (như Wine), typicality không cạnh tranh sẽ kéo tâm cụm sụp đổ.\n"
        "6. lambda_sep: Hệ số phạt đẩy liên cụm (chọn 0.05). Khi 2 tâm tiến sát nhau, số hạng này tăng vọt lên vô cực để đẩy chúng ra xa.\n"
        "7. Phi(x_i): Hàm trọng số khoảng cách phân tán trong D-DPC. Giúp triệt tiêu các đỉnh mật độ trùng lặp."
    )

    doc.add_heading("3. BỘ CÂU HỎI PHẢN BIỆN THƯỜNG GẶP KHI BẢO VỆ", level=1)
    doc.add_paragraph(
        "Hỏi: Tại sao lại gọi là thuật toán Memetic thay vì GA thuần túy?\n"
        "Đáp: GA thuần túy chỉ dùng toán tử lai ghép và đột biến ngẫu nhiên để tìm nghiệm. Thuật toán Memetic là sự kết hợp giữa tìm kiếm toàn cục của GA và một thuật toán tìm kiếm cục bộ (Local Search). Ở đây, ta nhúng chính công thức cập nhật đạo hàm của PFCM vào làm bước tìm kiếm cục bộ Lamarckian.\n\n"
        "Hỏi: Tại sao tập Wine trước đây chỉ đạt 0.76 mà nay vọt lên 0.9438?\n"
        "Đáp: Tập Wine có 13 chiều không gian. Nhiễm sắc thể có tới 43 biến liên tục. GA thuần túy không thể đoán mò được 43 tọa độ số thực. Khi nhúng bước trượt đạo hàm giải tích PFCM, tâm cụm được kéo thẳng vào đáy cực tiểu, đồng thời chuẩn hóa số mũ mờ w_ref=2.0 giúp hàm mục tiêu không bị méo mó số học.\n\n"
        "Hỏi: 30 runs độc lập và kiểm định Wilcoxon có ý nghĩa gì?\n"
        "Đáp: Đây là tiêu chuẩn vàng của các bài báo Scopus Q1/Q2. Nó chứng minh thuật toán của ta không phải ăn may trên 1 seed ngẫu nhiên, mà trên 30 seed khác nhau, mô hình đều vượt trội mô hình gốc với độ tin cậy p < 0.001 (độ tin cậy > 99.9%)."
    )

    out_path = DOCS_DIR / "CAM_NANG_HOC_THUAT_VA_BAO_VE_BAI_BAO.docx"
    doc.save(str(out_path))
    print(f"DOCX defense handbook written at: {out_path}")

if __name__ == "__main__":
    build_html_guide()
    build_docx_handbook()
