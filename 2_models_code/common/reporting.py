"""Colored console/HTML, CSV means, sample SD, rankings and paper deltas."""
import csv
import html
from pathlib import Path
import numpy as np
from scipy.stats import rankdata
from common.registry import GROUPS, METHODS
from common.statistics import METRICS

def write_csv(path, rows, fallback=()):
    fields = list(dict.fromkeys(key for row in rows for key in row)) or list(fallback)
    with Path(path).open("w",encoding="utf-8-sig",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def aggregate(rows, datasets, methods):
    summary=[]
    for dataset in datasets:
        for method in methods:
            subset=[r for r in rows if r["dataset"]==dataset and r["method"]==method]
            if not subset:
                continue
            record={"dataset":dataset,"method":method,"group":METHODS[method][0],"runs":len(subset),"k":subset[0]["k"]}
            for metric in (*METRICS,"accuracy_hungarian","runtime_seconds","fitness_evaluations"):
                values=np.array([r[metric] for r in subset])
                record[metric+"_mean"]=float(values.mean())
                record[metric+"_std"]=float(values.std(ddof=1)) if len(values)>1 else None
            record["observed_clusters_min"]=min(r["observed_clusters"] for r in subset)
            record["observed_clusters_max"]=max(r["observed_clusters"] for r in subset)
            summary.append(record)
    for dataset in datasets:
        subset=[r for r in summary if r["dataset"]==dataset]
        for metric in METRICS:
            ranks=rankdata([-r[metric+"_mean"] for r in subset],method="average")
            for row,rank in zip(subset,ranks):
                row[metric+"_rank"]=float(rank)
    totals=[]
    for method in methods:
        subset=[r for r in summary if r["method"]==method]
        if subset:
            totals.append({"method":method,"datasets":len(subset),**{
                m+"_rank_sum":float(sum(r[m+"_rank"] for r in subset)) for m in METRICS}})
    return summary,totals

def paper_differences(summary, code_root):
    path=code_root/"reference"/"paper_metrics.csv"
    if not path.exists():
        return [],[]
    with path.open(encoding="utf-8-sig",newline="") as stream:
        references=list(csv.DictReader(stream))
    actual={(r["dataset"],r["method"]):r for r in summary}
    differences=[]
    for ref in references:
        row=actual.get((ref["dataset"],ref["method"]))
        if row:
            metric=ref["metric"]
            mean=float(ref["mean"])
            differences.append({"stage":ref["stage"],"table":ref["table"],"dataset":ref["dataset"],
                "method":ref["method"],"metric":metric,"paper_mean":mean,
                "actual_mean":row[metric+"_mean"],"difference":row[metric+"_mean"]-mean,
                "paper_rank":ref["rank_reported"],"note":ref["note"]})
    return references,differences

def print_summary(summary,ranks,color=False):
    print("\nAccuracy = purity Eq.(17); NMI = geometric. Mean +/- sample SD.")
    print(f"{'Dataset':<15} {'Method':<16} {'Accuracy':>17} {'ARI':>17} {'NMI':>17} {'Time(s)':>10}")
    for row in summary:
        prefix=GROUPS[row["group"]]["ansi"] if color else ""
        reset="\033[0m" if color else ""
        def cell(m):
            sd=row[m+"_std"]
            return f"{row[m+'_mean']:.4f} +/- {sd:.4f}" if sd is not None else f"{row[m+'_mean']:.4f} +/- NA"
        print(prefix+f"{row['dataset']:<15} {row['method']:<16} {cell('accuracy_purity'):>17} "
              f"{cell('ari'):>17} {cell('nmi'):>17} {row['runtime_seconds_mean']:>10.3f}"+reset)
    print("\nRank sums: actual methods and selected datasets only.")
    for row in ranks:
        print(row["method"]," ".join(f"{m}={row[m+'_rank_sum']:.1f}" for m in METRICS))

def report_html(path,summary,ranks,references,differences,experiment):
    e=lambda s:html.escape(str(s))
    cfg=experiment["config"]
    out=['''<!doctype html><html lang="vi"><meta charset="utf-8">
<title>So sánh DP-GA-PFCM</title><style>
body{font:15px Segoe UI,Arial;background:#f4f6fa;color:#182033;margin:0}
main{max-width:1400px;margin:auto;padding:28px}section{background:white;padding:22px;margin:18px 0;border-radius:12px;overflow:auto}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:9px;border-bottom:1px solid #e3e8f1;text-align:left}
th{background:#eef2f7}.badge{padding:5px 12px;border-radius:20px;color:white;margin:4px;display:inline-block}
.note{border-left:5px solid #9333ea;padding:14px;background:#faf5ff}small{color:#546176}svg{max-width:100%}
select{padding:8px}tr[hidden]{display:none}a{color:#2563eb}
</style><main><h1>Tái tạo và so sánh DP-GA-PFCM</h1>''']
    for g in GROUPS.values():
        out.append(f'<span class="badge" style="background:{g["color"]}">{e(g["label"])}</span>')
    out.append(f'<p>Profile: <b>{e(cfg["profile"])}</b> · {cfg["runs"]} lần chạy · '
        f'population={cfg["population"]} · generations={cfg["generations"]} · fitness={e(cfg["fitness"])}</p>')
    out.append('<p class="note">Kết quả code tái tạo với giả định đã ghi trong ASSUMPTIONS.md. '
        'Chưa chứng minh khớp code gốc. GA-IFWCOM và SCA-FPCOM chưa triển khai; số tham khảo của chúng '
        'là mean bài báo công bố, không phải kết quả chạy. Accuracy = purity; NMI = geometric. '
        'SD lấy ddof=1; NA khi một lần chạy. Quick là kiểm tra chương trình, không phải ngân sách bài báo.</p>')
    out.append('<section><h2>Chất lượng thực tế</h2><label>Dataset <select id="dataset"><option value="">Tất cả</option>')
    for d in dict.fromkeys(r["dataset"] for r in summary):
        out.append(f'<option>{e(d)}</option>')
    out.append('</select></label><table id="actual"><thead><tr><th>Dataset</th><th>Phương pháp</th>'
        '<th>Accuracy / purity</th><th>ARI</th><th>NMI</th><th>Giây</th><th>Cụm thực / K</th><th>Số lần</th></tr></thead><tbody>')
    for r in summary:
        color=GROUPS[r["group"]]["color"]
        out.append(f'<tr data-dataset="{e(r["dataset"])}"><td>{e(r["dataset"])}</td>'
            f'<td style="color:{color};border-left:4px solid {color}">{e(r["method"])}</td>')
        for m in METRICS:
            sd=r[m+"_std"]
            text=f'{r[m+"_mean"]:.4f} ± {sd:.4f}' if sd is not None else f'{r[m+"_mean"]:.4f} ± NA'
            out.append(f'<td>{text}</td>')
        out.append(f'<td>{r["runtime_seconds_mean"]:.3f}</td><td>{r["observed_clusters_min"]}–'
            f'{r["observed_clusters_max"]} / {r["k"]}</td><td>{r["runs"]}</td></tr>')
    out.append('</tbody></table></section><section><h2>Tổng thứ hạng (thấp hơn tốt hơn)</h2>'
        '<p><small>Rank bằng số chưa làm tròn; đồng hạng trung bình. Chỉ các phương pháp thực sự chạy '
        'trên cùng danh sách dataset; không gộp số tham khảo vào rank.</small></p>')
    if ranks:
        height=55+len(ranks)*42
        maximum=max(r[m+"_rank_sum"] for r in ranks for m in METRICS)
        out.append(f'<svg viewBox="0 0 1100 {height}" role="img" aria-label="Tổng thứ hạng">')
        for j,m in enumerate(METRICS):
            out.append(f'<text x="{180+j*300}" y="20">{e(m)}</text>')
        for i,r in enumerate(ranks):
            y=45+i*42
            color=GROUPS[METHODS[r["method"]][0]]["color"]
            out.append(f'<text x="0" y="{y+16}" fill="{color}">{e(r["method"])}</text>')
            for j,m in enumerate(METRICS):
                value=r[m+"_rank_sum"]
                x=180+j*300
                width=235*value/max(maximum,1)
                out.append(f'<rect x="{x}" y="{y}" width="{width}" height="23" fill="{color}" rx="4"/>'
                    f'<text x="{x+width+5}" y="{y+16}">{value:.1f}</text>')
        out.append('</svg>')
    out.append('</section><section><h2>Độ lệch so với số bài báo</h2>'
        '<p>Δ = kết quả chạy − số công bố. Giữ nguyên số đáng nghi 0.066 của Glass / DP-PFCM / Table 11.</p>'
        '<table><tr><th>Bảng</th><th>Dataset</th><th>Phương pháp</th><th>Chỉ số</th><th>Bài báo</th>'
        '<th>Chạy</th><th>Δ</th><th>Ghi chú</th></tr>')
    for r in differences:
        out.append('<tr>'+''.join(f'<td>{e(r[k])}</td>' for k in ("table","dataset","method","metric"))
            +f'<td>{r["paper_mean"]:.4f}</td><td>{r["actual_mean"]:.4f}</td>'
            +f'<td>{r["difference"]:+.4f}</td><td>{e(r["note"])}</td></tr>')
    out.append('</table></section><section><h2>Tham khảo Table 11–13: số công bố, không phải kết quả chạy</h2>'
        '<table><tr><th>Dataset</th><th>Phương pháp</th><th>Chỉ số</th><th>Mean công bố</th><th>Code</th></tr>')
    datasets=set(r["dataset"] for r in summary)
    for ref in references:
        if ref["stage"]=="2" and ref["dataset"] in datasets:
            g,module,available=METHODS[ref["method"]]
            status="Có, với giả định" if available else "Thiếu nguồn đầy đủ, chưa triển khai"
            out.append(f'<tr><td>{e(ref["dataset"])}</td><td style="color:{GROUPS[g]["color"]}">'
                f'{e(ref["method"])}</td><td>{e(ref["metric"])}</td><td>{e(ref["mean"])}</td><td>{status}</td></tr>')
    out.append('</table></section><section><h2>Tệp chi tiết</h2><p>'
        '<a href="runs.csv">Từng lần chạy</a> · <a href="summary.csv">Mean, SD, rank</a> · '
        '<a href="kruskal_wallis.csv">Kruskal-Wallis</a> · <a href="dunn_bonferroni.csv">Dunn-Bonferroni</a> · '
        '<a href="experiment.json">Cấu hình, seed, hash, môi trường</a></p></section>'
        '<script>document.getElementById("dataset").onchange=function(){'
        'document.querySelectorAll("#actual tbody tr").forEach(r=>r.hidden=!!this.value&&r.dataset.dataset!==this.value)}'
        '</script></main></html>')
    Path(path).write_text("\n".join(out),encoding="utf-8")
