"""Generate an evidence-based validation note from saved actual experiments."""
import csv
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def read_csv(path):
    with path.open(encoding="utf-8-sig",newline="") as stream:
        return list(csv.DictReader(stream))
quick=read_csv(ROOT/"results"/"quick_main10"/"runs.csv")
iris=read_csv(ROOT/"results"/"paper_iris30"/"summary.csv")
comparisons=read_csv(ROOT/"results"/"paper_iris30"/"paper_differences.csv")
out=["# Phạm vi kiểm tra và kết quả tái tạo thực tế","",
"Code chạy được **9/11 phương pháp**. GA-IFWCOM và SCA-FPCOM chưa triển khai; không thay bằng thuật toán khác. "
"Đã đối chiếu công thức và chạy dữ liệu thật, nhưng **chưa tái tạo được kết quả công bố**.","",
"## Đã kiểm tra","",
"- 14 kiểm tra trong tests/test_reproduction.py đã đạt: đáp án số của U/T/PFCM, "
"purity khác Hungarian, NMI hình học, DPC nhỏ và tie, seed lặp lại, "
"finite output, membership tổng 1, fitness variants, gamma fixed, Dunn với đáp án biết trước, dữ liệu 10+4, lỗi baseline thiếu nguồn.",
f"- Chạy nhanh: **{len(quick)} lượt fit** = 9 phương pháp × 10 dataset chính × 2 lần; "
"population=12, generations=8, PFCM tối đa 100. Đây là smoke test, không phải mean 30 lần của bài.",
"- Iris ngân sách Table 5: **270 lượt fit** = 9 phương pháp × 30 lần; "
"population=80, generations=100. Cấu hình bổ sung vẫn là các giả định trong ASSUMPTIONS.md.",
"- tools/verify_artifacts.py đã tính lại metrics từ labels của 450 lượt fit chính ở hai thí nghiệm; "
"khớp CSV, seed, code/data hash, số lượt và 504 ô tham khảo.",
"- Đã kiểm tra cú pháp các module, trạng thái từng runner và pip check: không có dependency lỗi.",
"- 10 dataset chính dùng dc chính xác. 4 dataset đánh giá riêng được kiểm tra parser/scaling/schema; "
"chưa chạy mô hình trên bốn bộ này trong các bảng kết quả dưới đây.","",
"## Iris: 30 lần, mean thực tế so với bài","",
"Mỗi số dưới đây lấy trực tiếp summary.csv và reference/paper_metrics.csv. "
"Ba chỉ số đều trên [0,1] trong bảng này. ± là sample SD ddof=1.","",
"| Phương pháp | Accuracy / purity ± SD | ARI ± SD | NMI ± SD | Cụm thực / K |",
"|---|---:|---:|---:|---:|"]
for r in iris:
    cells=[f'{float(r[m+"_mean"]):.4f} ± {float(r[m+"_std"]):.4f}' for m in ("accuracy_purity","ari","nmi")]
    out.append("| "+r["method"]+" | "+" | ".join(cells)+f' | {r["observed_clusters_min"]}–{r["observed_clusters_max"]} / {r["k"]} |')
out.extend(["","### Đối chiếu riêng mô hình chính","",
"| Chỉ số | Bài công bố | Mean tái tạo | Δ |","|---|---:|---:|---:|"])
for r in comparisons:
    if r["method"]=="DP-GA-PFCM":
        out.append(f'| {r["metric"]} | {float(r["paper_mean"]):.4f} | {float(r["actual_mean"]):.4f} | {float(r["difference"]):+.4f} |')
params=[]
collapsed=0
for p in (ROOT/"results"/"paper_iris30"/"artifacts"/"iris"/"DP-GA-PFCM").glob("run_*"):
    details=json.loads((p/"details.json").read_text(encoding="utf-8"))
    model=np.load(p/"model.npz")
    params.append(details["params"]["w"])
    collapsed+=int(len(np.unique(model["labels"]))<3)
out.extend(["",
f"Trong 30 lần của GA, median w tối ưu là **{np.median(params):.4f}** "
f"(giới hạn trên tự chọn=5), có **{collapsed}/30** lần nhãn cứng chỉ có 2 cụm. "
"Đây là dấu hiệu nghiệm gần biên/nhập cụm cần xem xét. Nó phù hợp với rủi ro "
"fitness J_FCM thay đổi thang đo khi tối ưu w, nhưng chưa chứng minh một nguyên nhân duy nhất cho chênh lệch.",
"",
"## Kiểm tra các cách hiểu fitness","",
"Cùng seeds của 5 lần đầu, cùng population=80 và generations=100. "
"J_FCM phía dưới lấy đúng 5 lần đầu của thí nghiệm 30 lần; hai biến thể chạy 5 lần riêng. "
"Không chọn biến thể theo nhãn để thay cấu hình mặc định.","",
"| Cách hiểu fitness | Mean purity (5 lần) | Mean ARI | Mean NMI |",
"|---|---:|---:|---:|"])
iris_runs=read_csv(ROOT/"results"/"paper_iris30"/"runs.csv")
first=[r for r in iris_runs if r["method"]=="DP-GA-PFCM" and int(r["run"])<=5]
means=[float(np.mean([float(r[m]) for r in first])) for m in ("accuracy_purity","ari","nmi")]
out.append("| J_FCM Eq.6 | "+" | ".join(f"{v:.4f}" for v in means)+" |")
for folder,title in [("sensitivity_pfcm_iris5","J_PFCM Eq.11"),("sensitivity_sse_iris5","SSE tâm gần nhất")]:
    path=ROOT/"results"/folder/"summary.csv"
    if path.exists():
        r=read_csv(path)[0]
        out.append("| "+title+" | "+" | ".join(f'{float(r[m+"_mean"]):.4f}' for m in ("accuracy_purity","ari","nmi"))+" |")
out.extend(["",
"Thay fitness đã làm kết quả đổi đáng kể; chưa biến thể nào ở đây chứng minh khớp code gốc. "
"Vẫn cần xác định đúng bounds, gamma, quần thể và cách cập nhật từ tác giả.",
"",
"## Giới hạn kết luận","",
"- Chưa chạy đầy đủ 30 lần trên cả 10 dataset cho tất cả phương pháp; lệnh sẵn trong README_REPRODUCTION.md.",
"- Số tham khảo A6/A7 là số bài chính, không có raw runs để làm SD hoặc kiểm định chung.",
"- Không dùng thứ hạng của quick để khẳng định phương pháp vượt trội. Tổng rank trên 10 bộ/9 phương pháp "
"khác tổng rank của bài trên 14 bộ/đầy đủ các phương pháp.",
"- DPC tất định nên DP-FCM và DP-PFCM cho cùng nhãn giữa các lần; không thêm ngẫu nhiên để ép SD khớp Table 15.",
"- Case study RFM chưa tái tạo vì thiếu tệp chính xác; Room Occupancy có chênh lệch feature và nhánh lấy mẫu dc.",
"- Màu có trong FILE_GROUPS.html, các report.html và terminal; tài liệu mô tả thiếu thông tin ở ASSUMPTIONS.md.",
"",
"[Báo cáo 10 dataset chạy nhanh](results/quick_main10/report.html) · "
"[Báo cáo Iris 30 lần](results/paper_iris30/report.html) · "
"[Ghi chú giả định](ASSUMPTIONS.md)"])
(ROOT/"VALIDATION.md").write_text("\n".join(out)+"\n",encoding="utf-8")
print("Generated VALIDATION.md from actual saved predictions and metrics.")
