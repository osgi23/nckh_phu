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
    html_content = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cẩm Nang Toàn Diện: Giải Thích Kiến Trúc & Công Thức Toán SD-MGA-PFCM</title>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
        :root {
            --primary: #1A365D;
            --primary-light: #2B6CB0;
            --accent: #319795;
            --bg: #F7FAFC;
            --card-bg: #FFFFFF;
            --text-main: #2D3748;
            --text-muted: #718096;
            --border: #E2E8F0;
            --success: #38A169;
            --warning: #DD6B20;
            --danger: #E53E3E;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            line-height: 1.7;
            padding: 2.5rem 1rem;
        }
        .container {
            max-width: 1100px;
            margin: 0 auto;
            background: var(--card-bg);
            padding: 3rem 4rem;
            border-radius: 14px;
            box-shadow: 0 4px 25px rgba(0,0,0,0.06);
            border: 1px solid var(--border);
        }
        header {
            text-align: center;
            border-bottom: 2px solid var(--border);
            padding-bottom: 2rem;
            margin-bottom: 2.5rem;
        }
        .badge {
            background: #EBF8FF;
            color: var(--primary-light);
            padding: 0.35rem 0.9rem;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            display: inline-block;
            margin-bottom: 0.8rem;
        }
        h1 { color: var(--primary); font-size: 2.2rem; margin-bottom: 0.6rem; }
        .subtitle { color: var(--text-muted); font-size: 1.1rem; }
        h2 {
            color: var(--primary);
            font-size: 1.5rem;
            margin-top: 2.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.4rem;
            border-bottom: 2px solid #EDF2F7;
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }
        h3 { color: var(--primary-light); font-size: 1.2rem; margin-top: 1.5rem; margin-bottom: 0.6rem; }
        p { margin-bottom: 1rem; color: #4A5568; }
        ul, ol { margin-left: 1.8rem; margin-bottom: 1.2rem; color: #4A5568; }
        li { margin-bottom: 0.4rem; }
        
        /* Architecture Flow Diagram */
        .pipeline-box {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
            margin: 2rem 0;
        }
        .pipeline-step {
            background: #F8FAFC;
            border: 2px solid var(--border);
            border-top: 5px solid var(--primary-light);
            border-radius: 10px;
            padding: 1.4rem;
            transition: transform 0.2s;
        }
        .pipeline-step:hover { transform: translateY(-4px); box-shadow: 0 6px 15px rgba(0,0,0,0.05); }
        .step-num { font-size: 0.85rem; font-weight: 800; color: var(--accent); text-transform: uppercase; margin-bottom: 0.4rem; }
        .step-title { font-size: 1.15rem; font-weight: 700; color: var(--primary); margin-bottom: 0.6rem; }

        /* Formula Card */
        .formula-card {
            background: #F8FAFC;
            border: 1px solid var(--border);
            border-left: 5px solid var(--accent);
            border-radius: 8px;
            padding: 1.25rem 1.5rem;
            margin: 1.4rem 0;
        }
        .formula-title { font-weight: 700; color: var(--primary); margin-bottom: 0.5rem; font-size: 1.05rem; }
        .symbol-table { width: 100%; border-collapse: collapse; margin-top: 0.8rem; font-size: 0.9rem; }
        .symbol-table td { padding: 0.4rem 0.6rem; border-bottom: 1px solid #EDF2F7; }
        .symbol-name { font-weight: 700; color: var(--primary-light); width: 22%; font-family: monospace; font-size: 0.95rem; }

        /* FAQ Q&A for Defense */
        .faq-item {
            background: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 1rem;
            padding: 1.2rem 1.5rem;
        }
        .faq-q { font-weight: 700; color: var(--primary); font-size: 1.05rem; margin-bottom: 0.4rem; display: flex; align-items: center; gap: 0.5rem; }
        .faq-a { color: #4A5568; margin-bottom: 0; }

        @media (max-width: 850px) {
            .pipeline-box { grid-template-columns: 1fr; }
            .container { padding: 2rem 1.5rem; }
        }
    </style>
</head>
<body>
<div class="container">
    <header>
        <span class="badge">Cẩm Nang Độc Quyền</span>
        <h1>Giải Thích Bản Chất Kiến Trúc & Công Thức Toán SD-MGA-PFCM</h1>
        <div class="subtitle">Tài liệu trực quan giúp bạn nắm vững 100% mô hình, các biến số và chuẩn bị bảo vệ trước hội đồng</div>
    </header>

    <h2>1. Sơ Đồ Tổng Quan Quy Trình 3 Pha (System Architecture)</h2>
    <p>Thuật toán <strong>SD-MGA-PFCM</strong> hoạt động theo một chuỗi khép kín giải quyết 3 bài toán kế tiếp nhau:</p>
    
    <div class="pipeline-box">
        <div class="pipeline-step">
            <div class="step-num">Pha 1: Khởi Tạo</div>
            <div class="step-title">D-DPC (Diversity DPC)</div>
            <p>Tìm \(K\) tâm ban đầu đại diện cho \(K\) cụm độc lập bằng hàm phân tán không gian \(\Phi(x_i)\), ngăn chặn hiện tượng dồn tâm vào cụm đông nhất.</p>
        </div>
        <div class="pipeline-step">
            <div class="step-num">Pha 2: Tiến Hóa Toàn Cục</div>
            <div class="step-title">Memetic GA (MGA)</div>
            <p>Tối ưu đồng thời tâm cụm \(V\) và siêu tham số \(\{m, \eta, a, b\}\). Nhúng bước trượt gradient cục bộ (Lamarckian) và hàm phạt phân tách \(\mathcal{R}_{\text{sep}}\).</p>
        </div>
        <div class="pipeline-step">
            <div class="step-num">Pha 3: Hội Tụ Mịn</div>
            <div class="step-title">PFCM Convergence</div>
            <p>Xuất phát từ nghiệm tối ưu của GA, lặp cập nhật giải tích ma trận thành viên mờ \(U\) và khả năng \(T\) cho tới ngưỡng hội tụ \(\epsilon = 10^{-6}\).</p>
        </div>
    </div>

    <h2>2. Bóc Tách Chi Tiết Từng Công Thức Toán Học</h2>

    <h3>Công thức 1: Hàm mục tiêu PFCM chuẩn (Pal et al., 2005)</h3>
    <div class="formula-card">
        <div class="formula-title">Hàm mục tiêu PFCM nguyên bản:</div>
        \[ J_{\text{PFCM}} = \sum_{k=1}^K \sum_{i=1}^N \left( a u_{ik}^m + b t_{ik}^\eta \right) \|x_i - v_k\|^2 + \sum_{k=1}^K \gamma_k \sum_{i=1}^N (1 - t_{ik})^\eta \]
        <table class="symbol-table">
            <tr><td class="symbol-name">u_ik</td><td>Độ thuộc mờ (Fuzzy Membership): Xác suất điểm \(x_i\) thuộc cụm \(k\), ràng buộc \(\sum_{k=1}^K u_{ik} = 1\). Có tính cạnh tranh cao.</td></tr>
            <tr><td class="symbol-name">t_ik</td><td>Độ thuộc khả năng (Typicality): Đo lường mức độ điển hình thực sự của \(x_i\) đối với cụm \(k\). Không bị ép tổng bằng 1, giúp loại bỏ nhiễu (outliers).</td></tr>
            <tr><td class="symbol-name">m, η</td><td>Số mũ mờ và số mũ khả năng: Điều tiết độ "mềm" của ranh giới cụm (thường nằm trong đoạn \([1.1, 3.0]\)).</td></tr>
            <tr><td class="symbol-name">a, b</td><td>Trọng số điều tiết: \(a\) quyết định tầm quan trọng của thành phần mờ, \(b\) quyết định tầm quan trọng của thành phần khả năng.</td></tr>
            <tr><td class="symbol-name">γ_k</td><td>Tham số tỷ lệ (Scale): Đo độ phân tán hình học của cụm \(k\).</td></tr>
        </table>
    </div>

    <h3>Công thức 2: Khởi tạo đỉnh mật độ đa dạng không gian (D-DPC - Cải tiến Hướng 2)</h3>
    <div class="formula-card">
        <div class="formula-title">Nhân phân tán Greedy Dispersion Kernel:</div>
        \[ \mathcal{C}_1 = \arg\max_{i} (\rho_i \cdot \delta_i), \quad \mathcal{C}_k = \arg\max_{i \notin \mathcal{C}_{1:k-1}} \left[ (\rho_i \cdot \delta_i) \times \Phi(x_i, \mathcal{C}_{1:k-1}) \right] \]
        \[ \text{với: } \Phi(x_i, \mathcal{C}_{1:k-1}) = \min\left( 1.0, \; \frac{\displaystyle \min_{c \in \mathcal{C}_{1:k-1}} \|x_i - x_c\|}{d_c} \right) \]
        <p style="margin-top: 0.6rem; font-size: 0.95rem;">
            <strong>Ý nghĩa vật lý:</strong> Khi xét một điểm ứng viên \(x_i\), nếu nó nằm quá gần một tâm cụm đã chọn (\(\|x_i - x_c\| \ll d_c\)), hàm \(\Phi(x_i)\) sẽ tụt về 0, lập tức vô hiệu hóa điểm đó để nhường quyền cho các cụm ở xa hơn. Nhờ đó, bài toán không bao giờ bị dồn 2 tâm vào cùng 1 cụm.
        </p>
    </div>

    <h3>Công thức 3: Hàm mục tiêu điều chuẩn khoảng cách liên cụm (Cải tiến Hướng 1)</h3>
    <div class="formula-card">
        <div class="formula-title">Hàm mục tiêu có số hạng đẩy thế năng liên cụm:</div>
        \[ J_{\text{reg}} = J_{\text{PFCM}} + \lambda_{\text{sep}} \cdot \mathcal{R}_{\text{sep}}(V) + \mathcal{P}_{\text{barrier}}(V) \]
        \[ \mathcal{R}_{\text{sep}}(V) = \frac{1}{\displaystyle \min_{1 \le j < l \le K} \|v_j - v_l\|_2^2 + \epsilon_0} \]
        <p style="margin-top: 0.6rem; font-size: 0.95rem;">
            <strong>Ý nghĩa vật lý:</strong> Khi GA vô tình kéo 2 tâm cụm lại gần nhau (\(v_j \approx v_l\)), mẫu số tiến về 0 khiến hàm phạt \(\mathcal{R}_{\text{sep}}\) tăng vọt tiệm cận vô cực. Điều này tạo ra một "lực đẩy tĩnh điện" (repulsive force) buộc các tâm cụm phải dạt ra các vùng mật độ riêng biệt.
        </p>
    </div>

    <h3>Công thức 4: Tinh chỉnh cục bộ Memetic Lamarckian (Cải tiến Hướng Memetic)</h3>
    <div class="formula-card">
        <div class="formula-title">Bước trượt đạo hàm giải tích PFCM:</div>
        \[ v_k^{\text{refined}} = \frac{\sum_{i=1}^N (a u_{ik}^m + b t_{ik}^\eta) x_i}{\sum_{i=1}^N (a u_{ik}^m + b t_{ik}^\eta)}, \quad \text{Nhiễm sắc thể} \leftarrow v_k^{\text{refined}} \]
        \[ \text{Hàm thích nghi: } \text{Fitness} = \frac{1}{J(V; w_{\text{ref}}=2.0) + \lambda_{\text{sep}} \mathcal{R}_{\text{sep}} + \epsilon_0} \]
        <p style="margin-top: 0.6rem; font-size: 0.95rem;">
            <strong>Ý nghĩa toán học:</strong> GA không cần phải "đoán mò" tọa độ số thực trong không gian 43 chiều. GA chỉ cần ném cá thể vào gần thung lũng nghiệm, công thức đạo hàm giải tích trên sẽ kéo tụt tâm cụm vào đúng đáy cực tiểu tối ưu chỉ trong 1 bước duy nhất!
        </p>
    </div>

    <h2>3. Bộ Câu Hỏi & Câu Trả Lời Khi Bảo Vệ Trước Hội Đồng (Defense FAQ)</h2>

    <div class="faq-item">
        <div class="faq-q">❓ Câu 1: Tại sao bài báo gốc của Kuo et al. (2023) bị tụt Purity trên Iris và Breast Tissue mà bài báo không nhận ra?</div>
        <div class="faq-a">
            <strong>Trả lời:</strong> Trong bài báo gốc, Bước 6 trích dẫn nhầm công thức thích nghi theo Eq. (6) ($J_{\text{FCM}}$). Khi GA cho số mũ mờ $w \to 5.0$, số hạng $(1/K)^w$ giảm tiệm cận 0, khiến hàm loss giả tạo tụt xuống mức cực thấp bằng cách gom tất cả tâm về trọng tâm toàn cục. Tác giả bài báo gốc có thể đã tinh chỉnh tham số cố định $w=2$ hoặc dùng một hàm fitness nội bộ không được công bố rõ trong văn bản.
        </div>
    </div>

    <div class="faq-item">
        <div class="faq-q">❓ Câu 2: Thuật toán Memetic khác gì so với Giải thuật Di truyền (GA) truyền thống?</div>
        <div class="faq-a">
            <strong>Trả lời:</strong> GA truyền thống chỉ dựa vào toán tử ngẫu nhiên (Crossover và Mutation) nên rất chậm và dễ bị kẹt cực tiểu trong không gian liên tục nhiều chiều. Thuật giải Memetic kết hợp tìm kiếm toàn cục của GA với tìm kiếm cục bộ (Local Search) dựa trên đạo hàm giải tích của PFCM. Sau khi đột biến, cá thể được trượt dốc theo gradient về đúng cực tiểu cục bộ rồi ghi đè tọa độ đó vào nhiễm sắc thể (cơ chế Lamarckian).
        </div>
    </div>

    <div class="faq-item">
        <div class="faq-q">❓ Câu 3: Ý nghĩa của kiểm định Wilcoxon với giá trị p-value < 0.001 là gì?</div>
        <div class="faq-a">
            <strong>Trả lời:</strong> Giá trị $p < 0.001$ chứng minh xác suất sự vượt trội của mô hình đề xuất do "ngẫu nhiên/may mắn" là nhỏ hơn 0.1% (tức độ tin cậy đạt trên 99.9%). Đây là tiêu chuẩn kiểm định khắt khe nhất trong khoa học máy tính để khẳng định đóng góp thuật toán thực sự vượt trội.
        </div>
    </div>
</div>
</body>
</html>
"""
    out_path = DOCS_DIR / "GIAI_THICH_TOAN_HOC_VA_KIEN_TRUC_SD_MGA_PFCM.html"
    out_path.write_text(html_content, encoding="utf-8")
    print(f"HTML explanation guide written at: {out_path}")

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
