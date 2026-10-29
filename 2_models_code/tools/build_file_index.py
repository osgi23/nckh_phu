"""Build a colored, clickable inventory for the three code groups."""
import html
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GROUPS=[
("blue_baselines","🔵 Phương pháp cơ sở","#2563eb"),
("orange_comparisons","🟠 Phương pháp so sánh","#c2410c"),
("purple_main_model","🟣 Mô hình chính","#9333ea")]
e=lambda value:html.escape(str(value))
out=['''<!doctype html><html lang="vi"><meta charset="utf-8"><title>Nhóm file code</title>
<style>body{font:16px Segoe UI,Arial;background:#f3f5fa;color:#182033;margin:0}
main{max-width:1100px;margin:auto;padding:32px}section{background:white;padding:24px;margin:20px 0;border-radius:12px}
table{border-collapse:collapse;width:100%}td,th{padding:12px;text-align:left;border-bottom:1px solid #e5eaf2}
a{color:inherit}small{color:#596579}code{background:#edf1f7;padding:4px}h2{margin-top:0}
.notice{border-left:5px solid #9333ea;padding:18px;background:#faf5ff}</style><main>
<h1>Code tái tạo DP-GA-PFCM</h1><p>Chọn file trong nhóm màu để mở nội dung.
Màu xanh/cam/tím thống nhất với lệnh chạy và bảng kết quả.</p>
<p class="notice"><b>9 phương pháp chạy được.</b> GA-IFWCOM và SCA-FPCOM chưa triển khai,
hai file chỉ báo thiếu nguồn. Không dùng số công bố của chúng làm kết quả chạy.</p>''']
inventory=[]
for folder,label,color in GROUPS:
    out.append(f'<section style="border-top:6px solid {color}"><h2 style="color:{color}">{label}</h2>'
               '<table><tr><th>File</th><th>Nội dung / trạng thái</th></tr>')
    for path in sorted((ROOT/folder).glob("*")):
        if not path.is_file() or path.suffix not in (".py",".md"):
            continue
        relative=path.relative_to(ROOT).as_posix()
        description="Lệnh chạy và in chất lượng" if path.name=="run.py" else "Mô hình đã triển khai"
        if path.name in ("ga_ifwcom.py","sca_fpcom.py"):
            description="CHƯA TRIỂN KHAI — thiếu công thức đầy đủ từ bài tham khảo"
        elif path.name=="__init__.py":
            description="Khai báo package"
        elif path.suffix==".md":
            description="Hướng dẫn nhóm"
        inventory.append({"file":relative,"group":folder,"color":color,"description":description})
        out.append(f'<tr><td style="color:{color}"><a href="{e(relative)}">{e(path.name)}</a></td>'
                   f'<td>{e(description)}</td></tr>')
    out.append('</table></section>')
out.append('''<section style="border-top:6px solid #9333ea"><h2 style="color:#9333ea">🟣 Chạy so sánh toàn bộ</h2>
<p><a href="run_compare_all.py">run_compare_all.py</a></p>
<code>python code/run_compare_all.py --profile quick --color always</code></section>
<section><h2>Tài liệu và kết quả đã chạy</h2><p>
<a href="README_REPRODUCTION.md">Hướng dẫn chạy</a> ·
<a href="ASSUMPTIONS.md">Thông tin thiếu và các tham số tự chọn</a> ·
<a href="VALIDATION.md">Phạm vi đã kiểm tra và chênh lệch thực tế</a></p>
<p><a href="results/quick_main10/report.html">Chạy nhanh trên 10 dataset</a> ·
<a href="results/paper_iris30/report.html">Iris, 30 lần với ngân sách Table 5</a></p></section>
<section><h2>⚪ Code dùng chung và cấu hình</h2><table><tr><th>File</th><th>Vai trò</th></tr>''')
for folder in ("common","configs","reference","tests","tools"):
    for path in sorted((ROOT/folder).glob("*")):
        if path.is_file() and path.suffix in (".py",".json",".md",".csv"):
            relative=path.relative_to(ROOT).as_posix()
            inventory.append({"file":relative,"group":"shared","color":"#64748b","description":folder})
            out.append(f'<tr><td><a href="{e(relative)}">{e(relative)}</a></td><td>{e(folder)}</td></tr>')
out.append('</table></section></main></html>')
(ROOT/"FILE_GROUPS.html").write_text("\n".join(out),encoding="utf-8")
(ROOT/"file_groups.json").write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"Colored index: {len(inventory)} files.")
