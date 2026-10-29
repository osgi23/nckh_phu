"""Scientific PNG/PDF figures and an offline dashboard from ACTUAL saved runs."""
import html
import json
import math
import os
from pathlib import Path
import numpy as np
os.environ.setdefault("MPLCONFIGDIR",str((Path(__file__).resolve().parents[2]/"tmp"/"matplotlib_cache").resolve()))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from scipy.optimize import linear_sum_assignment
from sklearn.metrics.cluster import contingency_matrix
from common.data import load_dataset
from common.metrics import quality
from common.registry import GROUPS, METHODS
from common.reporting import write_csv
from common.statistics import METRICS

TITLES = {"accuracy_purity": "Accuracy / purity", "ari": "ARI", "nmi": "NMI (geometric)"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "pdf.fonttype": 42, "svg.fonttype": "none"})

def select_kmeans_extremes(summary, metric="accuracy_purity"):
    if metric not in METRICS:
        raise ValueError("Selection metric must be purity, ARI or NMI.")
    candidates = [dict(r) for r in summary if r["method"] == "K-means"]
    if not candidates:
        return {"metric": metric, "status": "no_kmeans", "ranking": [], "selected": []}
    counts = {int(r["runs"]) for r in candidates}
    if len(counts) != 1 or len({r["dataset"] for r in candidates}) != len(candidates):
        raise ValueError("Selection needs one comparable K-means summary per dataset and equal run counts.")
    key = metric+"_mean"
    candidates.sort(key=lambda r: (-float(r[key]), r["dataset"]))
    selected = [{"role": "highest", **candidates[0]}]
    if len(candidates) > 1:
        selected.append({"role": "lowest", **candidates[-1]})
    return {"metric": metric, "status": "ok", "ranking": candidates, "selected": selected,
            "rule": "Mean of all K-means runs; ties ordered by dataset slug; no GA scores used for selection.",
            "highest_ties": [r["dataset"] for r in candidates if float(r[key]) == float(candidates[0][key])],
            "lowest_ties": [r["dataset"] for r in candidates if float(r[key]) == float(candidates[-1][key])]}

def color(method):
    return GROUPS[METHODS[method][0]]["color"]

def save_figure(fig, folder, name):
    fig.savefig(folder/(name+".png"), dpi=165, bbox_inches="tight", facecolor="white")
    fig.savefig(folder/(name+".pdf"), bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return name

def bar_metrics(summary, datasets, folder, name, title):
    fig, axes = plt.subplots(len(datasets), 3, figsize=(19, max(4.6, len(datasets)*4.6)),
                             squeeze=False, layout="constrained")
    for i, dataset in enumerate(datasets):
        subset = [r for r in summary if r["dataset"] == dataset]
        for j, metric in enumerate(METRICS):
            ax = axes[i,j]
            means = [float(r[metric+"_mean"]) for r in subset]
            sd = [float(r[metric+"_std"]) if r[metric+"_std"] is not None else 0 for r in subset]
            y = np.arange(len(subset))
            ax.barh(y, means, xerr=sd, color=[color(r["method"]) for r in subset],
                    capsize=2.5, error_kw={"elinewidth": 1}, alpha=.9)
            ax.set_yticks(y, [r["method"] for r in subset], fontsize=9)
            ax.invert_yaxis()
            ax.set_xlim(-1.03 if metric=="ari" and min(means,default=0)<0 else 0,1.23)
            for k,v in enumerate(means):
                ax.text(max(v,0)+sd[k]+.025,k,f"{v:.3f}",va="center",fontsize=9)
            ax.axvline(0,color="#64748b",lw=.8)
            ax.grid(axis="x",alpha=.17)
            ax.set_axisbelow(True)
            ax.set_title(dataset+" | "+TITLES[metric])
            ax.set_xlabel("Mean; error bars = sample SD")
    fig.suptitle(title,fontsize=16)
    return save_figure(fig,folder,name)

def heatmap(summary, datasets, methods, folder):
    fig, axes = plt.subplots(1,3,figsize=(max(23,len(methods)*2.7),max(6,len(datasets)*.62)),
                             layout="constrained")
    lookup = {(r["dataset"],r["method"]):r for r in summary}
    for ax,metric in zip(axes,METRICS):
        matrix = np.array([[float(lookup[(d,m)][metric+"_mean"]) if (d,m) in lookup else np.nan
                            for m in methods] for d in datasets])
        cmap = plt.colormaps["Blues"].copy(); cmap.set_bad("#e5e7eb")
        im=ax.imshow(np.ma.masked_invalid(matrix),vmin=-1 if metric=="ari" else 0,vmax=1,
                     cmap=cmap,aspect="auto")
        ax.set_xticks(range(len(methods)),methods,rotation=58,ha="right",fontsize=9)
        ax.set_yticks(range(len(datasets)),datasets,fontsize=10)
        for tick,m in zip(ax.get_xticklabels(),methods): tick.set_color(color(m))
        for i in range(len(datasets)):
            for j in range(len(methods)):
                v=matrix[i,j]
                tone="white" if np.isfinite(v) and (v>.5 if metric!="ari" else v>0) else "#172033"
                ax.text(j,i,f"{v:.3f}" if np.isfinite(v) else "NA",ha="center",va="center",
                        color=tone,fontsize=9)
        ax.set_title(TITLES[metric],fontsize=13)
        fig.colorbar(im,ax=ax,shrink=.75)
    fig.suptitle("All datasets and implemented methods | measured means",fontsize=17)
    return save_figure(fig,folder,"all_models_heatmap")

def grouped_overview(summary, datasets, methods, folder):
    fig, axes=plt.subplots(3,1,figsize=(max(17,len(datasets)*1.6),13),sharex=True,layout="constrained")
    lookup={(r["dataset"],r["method"]):r for r in summary}
    # Keep the overview readable; all methods are included in the heatmap.
    shown=[m for m in ("K-means","FCM","PFCM","DP-GA-PFCM") if m in methods]
    width=.8/max(len(shown),1); x=np.arange(len(datasets))
    shades={"K-means":"#334155","FCM":"#60a5fa","PFCM":"#2563eb","DP-GA-PFCM":"#9333ea"}
    for ax,metric in zip(axes,METRICS):
        for j,m in enumerate(shown):
            means=[lookup.get((d,m),{}).get(metric+"_mean",np.nan) for d in datasets]
            sd=[lookup.get((d,m),{}).get(metric+"_std",0) or 0 for d in datasets]
            ax.bar(x+(j-(len(shown)-1)/2)*width,means,width,yerr=sd,capsize=2,
                   color=shades[m],label=m,error_kw={"elinewidth":.8})
        ax.set_ylabel(TITLES[metric]); ax.set_ylim(-1.05 if metric=="ari" and any(
            r["ari_mean"]<0 for r in summary) else 0,1.08)
        ax.grid(axis="y",alpha=.2); ax.set_axisbelow(True)
    axes[0].legend(ncol=max(len(shown),1),loc="upper center",bbox_to_anchor=(.5,1.18),frameon=False)
    axes[-1].set_xticks(x,datasets,rotation=32,ha="right")
    fig.suptitle("K-means, FCM, PFCM and DP-GA-PFCM | mean +/- sample SD",fontsize=16)
    return save_figure(fig,folder,"main_comparison")

def cluster_figure(folder, dataset, rows, data_root):
    X,y,meta=load_dataset(dataset,data_root)
    if X.shape[1]>2:
        pca=PCA(n_components=2,svd_solver="full").fit(X); projected=pca.transform(X)
        project=pca.transform
        axis_names=("PC1","PC2")
        description=f"Common PCA projection ({pca.explained_variance_ratio_.sum()*100:.1f}% variance)"
    else:
        projected=np.column_stack((X[:,0],X[:,1] if X.shape[1]>1 else np.zeros(len(X))))
        project=lambda c: np.column_stack((c[:,0],c[:,1] if c.shape[1]>1 else np.zeros(len(c))))
        axis_names=("Feature 1 (min-max)","Feature 2 (min-max)")
        description="Common feature coordinates"
    first=[r for r in rows if r["dataset"]==dataset and int(r["run"])==1]
    ncols=3; nrows=math.ceil((len(first)+1)/ncols)
    fig,axes=plt.subplots(nrows,ncols,figsize=(16,nrows*3.8),sharex=True,sharey=True,
                          squeeze=False,layout="constrained")
    palette=plt.colormaps["tab20"]
    unique_y=np.unique(y); true_map={int(v):i for i,v in enumerate(unique_y)}
    truth=np.array([true_map[int(v)] for v in y])
    panels=[("True labels (evaluation only)",truth,None,None)]
    for row in first:
        with np.load(folder/row["artifact"]/"model.npz") as saved:
            labels=saved["labels"].copy(); centers=saved["centers"].copy()
        # Display-only permutation for easier viewing; stored labels/metrics remain untouched.
        table=contingency_matrix(y,labels); rr,cc=linear_sum_assignment(-table)
        pred_ids=np.unique(labels)
        mapping={int(pred_ids[c]):int(r) for r,c in zip(rr,cc)}
        extra=len(unique_y)
        for v in range(len(centers)):
            if v not in mapping: mapping[v]=extra; extra+=1
        mapped=np.array([mapping[int(v)] for v in labels])
        score=quality(y,labels)
        title=row["method"]+f"\nPurity {score['accuracy_purity']:.3f} | ARI {score['ari']:.3f}"
        panels.append((title,mapped,project(centers),np.array([mapping[v] for v in range(len(centers))])))
    for ax,panel in zip(axes.ravel(),panels):
        title,labels,centers,center_labels=panel
        ax.scatter(projected[:,0],projected[:,1],c=[palette(int(v)%20) for v in labels],
                   s=19,alpha=.78,linewidths=.2,edgecolors="white")
        if centers is not None:
            ax.scatter(centers[:,0],centers[:,1],c=[palette(int(v)%20) for v in center_labels],
                       marker="X",s=100,edgecolors="black",linewidths=.9)
        ax.set_title(title,fontsize=10); ax.set_xlabel(axis_names[0]); ax.set_ylabel(axis_names[1])
        ax.grid(alpha=.12)
    for ax in axes.ravel()[len(panels):]: ax.set_visible(False)
    fig.suptitle(dataset+" | first predefined run; "+description+
                 "\nColors aligned for display only; X = centers",fontsize=13)
    return save_figure(fig,folder,"clusters_"+dataset)

def convergence(folder, datasets, rows):
    traces=[]
    for row in rows:
        if row["method"]!="DP-GA-PFCM": continue
        detail=json.loads((folder/row["artifact"]/"details.json").read_text(encoding="utf-8"))
        for t in detail["diagnostics"].get("optimizer_trace",[]):
            traces.append(dict(dataset=row["dataset"],run=int(row["run"]),**t))
    write_csv(folder/"ga_history.csv",traces,("dataset","run","generation","best_fitness","evaluations"))
    if not traces: return None
    shown=[d for d in datasets if any(t["dataset"]==d for t in traces)]
    fig,axes=plt.subplots(math.ceil(len(shown)/2),2,figsize=(15,max(4,math.ceil(len(shown)/2)*3.3)),
                          squeeze=False,layout="constrained")
    for ax,d in zip(axes.ravel(),shown):
        subset=[t for t in traces if t["dataset"]==d]; generations=sorted({t["generation"] for t in subset})
        median=[]; lower=[]; upper=[]
        for g in generations:
            values=[t["best_fitness"] for t in subset if t["generation"]==g]
            q=np.percentile(values,[25,50,75]); lower.append(q[0]); median.append(q[1]); upper.append(q[2])
        ax.plot(generations,median,color="#9333ea"); ax.fill_between(generations,lower,upper,color="#9333ea",alpha=.16)
        ax.set_title(d); ax.set_xlabel("Generation"); ax.set_ylabel("Best fitness"); ax.grid(alpha=.2)
    for ax in axes.ravel()[len(shown):]: ax.set_visible(False)
    fig.suptitle("GA convergence | median and interquartile band across runs",fontsize=15)
    return save_figure(fig,folder,"ga_convergence")

def runtime_figure(summary, datasets, folder):
    fig,axes=plt.subplots(len(datasets),2,figsize=(15,max(4,len(datasets)*4.4)),squeeze=False,layout="constrained")
    for i,d in enumerate(datasets):
        subset=[r for r in summary if r["dataset"]==d]
        for j,metric in enumerate(("runtime_seconds","fitness_evaluations")):
            ax=axes[i,j]; means=[r[metric+"_mean"] for r in subset]
            sd=[r[metric+"_std"] or 0 for r in subset]
            y=np.arange(len(subset)); ax.barh(y,means,xerr=sd,capsize=2,color=[color(r["method"]) for r in subset])
            ax.set_yticks(y,[r["method"] for r in subset],fontsize=9); ax.invert_yaxis()
            ax.set_title(d+" | "+("fit time (seconds)" if j==0 else "fitness evaluations"))
            ax.grid(axis="x",alpha=.2); ax.set_axisbelow(True)
    fig.suptitle("Runtime and evaluation budget | mean +/- sample SD",fontsize=15)
    return save_figure(fig,folder,"runtime_comparison")

def summary_table(summary, dataset=None):
    e=lambda x:html.escape(str(x))
    rows=[r for r in summary if dataset is None or r["dataset"]==dataset]
    out=["<table><thead><tr><th>Dataset</th><th>Phương pháp</th><th>Purity</th><th>ARI</th><th>NMI</th><th>Δ purity / K-means</th><th>Số lần</th></tr></thead><tbody>"]
    baseline={r["dataset"]:r["accuracy_purity_mean"] for r in summary if r["method"]=="K-means"}
    for r in rows:
        out.append(f'<tr data-dataset="{e(r["dataset"])}"><td>{e(r["dataset"])}</td><td style="color:{color(r["method"])}">{e(r["method"])}</td>')
        for m in METRICS:
            sd=r[m+"_std"]
            out.append(f'<td>{r[m+"_mean"]:.4f} ± {sd:.4f}</td>' if sd is not None else f'<td>{r[m+"_mean"]:.4f} ± NA</td>')
        delta=r["accuracy_purity_mean"]-baseline[r["dataset"]] if r["dataset"] in baseline else None
        out.append(f'<td>{delta:+.4f}</td>' if delta is not None else "<td>NA</td>")
        out.append(f'<td>{r["runs"]}</td></tr>')
    return "".join(out)+"</tbody></table>"

def dashboard(folder, summary, experiment, selection, figures):
    e=lambda x:html.escape(str(x)); cfg=experiment["config"]
    names=list(dict.fromkeys(r["dataset"] for r in summary)); methods=list(dict.fromkeys(r["method"] for r in summary))
    selected=selection["selected"]
    def figure(name,caption):
        return f'<figure><a href="{e(name)}.pdf"><img src="{e(name)}.png" alt="{e(caption)}" loading="lazy"></a><figcaption>{e(caption)} · <a href="{e(name)}.png">PNG</a> · <a href="{e(name)}.pdf">PDF</a></figcaption></figure>'
    out=['''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kết quả phân cụm | DP-GA-PFCM</title><style>
:root{--blue:#2563eb;--orange:#c2410c;--purple:#9333ea}
*{box-sizing:border-box}body{margin:0;background:#f1f5f9;color:#172033;font:15px/1.55 "Segoe UI",Arial,sans-serif}
main{max-width:1540px;margin:auto;padding:32px 24px}header{padding:28px 0 18px}h1{font-size:34px;line-height:1.15;margin:8px 0}
h2{font-size:23px;margin:0 0 12px}h3{margin:0 0 10px}.eyebrow{color:var(--purple);font-weight:700;letter-spacing:.1em}
nav{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}nav a,button{background:white;border:1px solid #dbe3ed;border-radius:8px;padding:9px 14px;text-decoration:none;color:#172033}
section{background:white;border:1px solid #e2e8f0;border-radius:14px;padding:24px;margin:22px 0}a{color:var(--blue)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}.card{padding:20px;border:1px solid #dbe3ed;border-radius:12px;background:#fafcff}
.big{font-size:34px;font-weight:700;margin:4px 0}.chip{display:inline-block;padding:4px 11px;border-radius:18px;color:white;font-size:13px;margin-right:6px}
.note{border-left:4px solid var(--purple);padding:14px 18px;background:#faf5ff;border-radius:6px;color:#374151}
small,figcaption{color:#526078}figure{margin:18px 0}img{display:block;width:100%;height:auto;border-radius:6px}
.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #e2e8f0;white-space:nowrap}
th{background:#f8fafc;position:sticky;top:0}.heat td{text-align:center;font-weight:600}.heat th:first-child{min-width:120px}
select{padding:9px;border:1px solid #cbd5e1;border-radius:8px;font:inherit}button{cursor:pointer}button.active{background:var(--purple);color:white}
[hidden]{display:none!important}.metric-controls{display:flex;gap:8px;margin:12px 0}
.footer{font-size:13px;color:#64748b}details{margin:12px 0}summary{cursor:pointer;font-weight:600}
@media(max-width:700px){main{padding:16px 10px}section{padding:16px}h1{font-size:26px}}
</style></head><body><main><header><div class="eyebrow">KẾT QUẢ THỰC NGHIỆM</div>
<h1>So sánh các phương pháp phân cụm</h1>''']
    out.append(f'<p>{len(names)} dataset · {len(methods)} phương pháp chạy được · {cfg["runs"]} lần / dataset / phương pháp</p>')
    for g in GROUPS.values(): out.append(f'<span class="chip" style="background:{g["color"]}">{e(g["label"])}</span>')
    out.append('<nav><a href="#overview">Tổng quan</a><a href="#extremes">Hai bộ cao / thấp</a><a href="#datasets">Từng dataset</a><a href="#convergence">Hội tụ và thời gian</a><a href="report.html">Bảng đối chiếu bài báo</a></nav></header>')
    fit_text=("Fitness tham chiếu FCM với w cố định khi chấm điểm; w của chromosome vẫn được tìm kiếm. Đây là hiệu chỉnh thực nghiệm, chưa xác nhận là objective tác giả dùng."
              if cfg["fitness"]=="fcm_reference" else "Fitness "+str(cfg["fitness"])+" là một cách đọc objective trong bài; tham số biến thiên có thể thay đổi thang loss.")
    out.append(f'<div class="note">{e(fit_text)}<br>Profile: {e(cfg["profile"])} · population={cfg["population"]}, generations={cfg["generations"]}, stop={e(cfg.get("stop_criterion","objective"))}. '
               'Purity/NMI: 0–1; ARI: −1–1; cao hơn tốt hơn. ± là sample SD, không phải khoảng tin cậy.</div>')
    if experiment.get("unimplemented"):
        out.append('<p><small>Chưa triển khai: '+e(", ".join(experiment["unimplemented"]))+'. Số công bố không tham gia bảng chất lượng hoặc xếp hạng thực tế.</small></p>')
    if "quick" in str(cfg["profile"]):
        out.append('<p class="note">Đây là lượt chạy nhanh để kiểm tra chương trình, ngân sách chưa bằng bài báo.</p>')
    if experiment.get("parallel_dataset_jobs",1)>1:
        out.append('<p><small>Các dataset chạy song song; thời gian fit có thể chịu ảnh hưởng cạnh tranh tài nguyên. Không dùng số giây này để khẳng định nhanh hơn máy của tác giả.</small></p>')
    out.append('<section id="overview"><h2>Chất lượng trên toàn bộ dataset</h2><p>Chọn chỉ số để xem bảng màu; rê chuột lên ô để xem mean và SD.</p><div class="metric-controls">')
    for i,m in enumerate(METRICS):
        out.append(f'<button class="metric-button {"active" if i==0 else ""}" data-metric="{m}">{e(TITLES[m])}</button>')
    out.append('</div>')
    lookup={(r["dataset"],r["method"]):r for r in summary}
    for i,m in enumerate(METRICS):
        out.append(f'<div class="scroll heat-panel" data-metric="{m}"{"" if i==0 else " hidden"}><table class="heat"><tr><th>Dataset</th>')
        for method in methods: out.append(f'<th style="color:{color(method)}">{e(method)}</th>')
        out.append('</tr>')
        for d in names:
            out.append(f'<tr><th>{e(d)}</th>')
            for method in methods:
                r=lookup.get((d,method))
                if r is None: out.append('<td>NA</td>'); continue
                v=r[m+"_mean"]; frac=(v+1)/2 if m=="ari" else v
                rgba=plt.colormaps["Blues"](np.clip(frac,0,1))
                bg="#%02x%02x%02x"%tuple(int(c*255) for c in rgba[:3]); fg="white" if frac>.5 else "#172033"
                sd=r[m+"_std"]; info=f'Mean={v:.6f}; SD={sd if sd is not None else "NA"}; n={r["runs"]}'
                out.append(f'<td title="{e(info)}" style="background:{bg};color:{fg}">{v:.3f}</td>')
            out.append('</tr>')
        out.append('</table></div>')
    out.append(figure("all_models_heatmap","Heatmap của các mean thực đo"))
    out.append(figure("main_comparison","K-means, FCM, PFCM và mô hình chính trên cùng dataset"))
    out.append('</section><section id="extremes"><h2>Hai dataset có K-means cao nhất và thấp nhất</h2>')
    if selected:
        out.append(f'<p>Chọn theo <b>{e(TITLES[selection["metric"]])}</b> trung bình của K-means trên {len(selection["ranking"])} dataset. Không dùng kết quả GA để chọn bộ.</p><div class="cards">')
        for r in selected:
            out.append(f'<div class="card"><small>{"CAO NHẤT" if r["role"]=="highest" else "THẤP NHẤT"} · K-MEANS</small><h3>{e(r["dataset"])}</h3>'
                       f'<div class="big">{r[selection["metric"]+"_mean"]:.4f}</div><p>Purity {r["accuracy_purity_mean"]:.4f} · ARI {r["ari_mean"]:.4f}<br>NMI {r["nmi_mean"]:.4f} · {r["runs"]} lần</p></div>')
        out.append('</div>'+figure("kmeans_extremes_comparison","Tất cả phương pháp trên hai bộ đã chọn; mean ± sample SD"))
        for r in selected:
            out.append(f'<details open><summary>{e(r["dataset"])} — bảng và độ lệch so với K-means</summary><div class="scroll">{summary_table(summary,r["dataset"])}</div></details>')
    else: out.append('<p>Experiment này không có K-means, nên chưa xác định được hai bộ.</p>')
    out.append('</section><section id="datasets"><h2>Chỉ số và phân cụm của từng dataset</h2><label>Dataset <select id="dataset-filter"><option value="">Tất cả</option>')
    for d in names: out.append(f'<option value="{e(d)}">{e(d)}</option>')
    out.append('</select></label><div class="scroll">'+summary_table(summary)+'</div>')
    out.append('<p><small>Hình phân cụm dùng lần chạy đầu đã định trước. Dataset nhiều chiều dùng chung PCA 2D; chỉ số chất lượng vẫn tính từ nhãn phân cụm ở toàn bộ không gian đặc trưng. Đổi màu để đối chiếu chỉ áp dụng khi vẽ.</small></p>')
    for d in names:
        out.append(f'<details class="dataset-detail" data-dataset="{e(d)}"><summary>{e(d)} — biểu đồ chất lượng và hình phân cụm</summary>')
        out.append(figure("metrics_"+d,"Ba chỉ số chất lượng: "+d))
        if "clusters_"+d in figures: out.append(figure("clusters_"+d,"Phân cụm ở lần chạy đầu: "+d))
        out.append('</details>')
    out.append('</section><section id="convergence"><h2>Hội tụ GA và ngân sách tính toán</h2>')
    if "ga_convergence" in figures: out.append(figure("ga_convergence","Trung vị best fitness và dải tứ phân vị theo thế hệ"))
    if "runtime_comparison" in figures: out.append(figure("runtime_comparison","Thời gian fit và số fitness evaluations trên hai bộ"))
    out.append('</section><section><h2>Tệp số liệu</h2><p>')
    for name,label in (("summary.csv","Mean / SD / rank"),("runs.csv","Mỗi lần chạy"),("kmeans_selection.json","Quy tắc chọn hai bộ"),
                       ("kmeans_ranking.csv","Thứ tự K-means"),("extremes_comparison.csv","So sánh hai bộ"),
                       ("table_accuracy.csv","Bảng purity"),("table_ari.csv","Bảng ARI"),("table_nmi.csv","Bảng NMI"),
                       ("ga_history.csv","Lịch sử GA"),("experiment.json","Cấu hình và môi trường")):
        out.append(f'<a href="{name}">{label}</a> · ')
    out.append('''</p></section><p class="footer">Số liệu được tính từ các lần chạy thực tế; hình mẫu Drive chỉ dùng tham khảo cách trình bày.</p>
<script>
document.querySelectorAll('.metric-button').forEach(b=>b.onclick=()=>{
 document.querySelectorAll('.metric-button').forEach(x=>x.classList.toggle('active',x===b));
 document.querySelectorAll('.heat-panel').forEach(x=>x.hidden=x.dataset.metric!==b.dataset.metric);
});
document.getElementById('dataset-filter').onchange=function(){
 document.querySelectorAll('#datasets tr[data-dataset],.dataset-detail').forEach(x=>x.hidden=!!this.value&&x.dataset.dataset!==this.value);
 if(this.value)document.querySelectorAll('.dataset-detail').forEach(x=>x.open=x.dataset.dataset===this.value);
};
</script></main></body></html>''')
    (folder/"index.html").write_text("\n".join(out),encoding="utf-8")

def build_visual_results(folder, summary, rows, experiment, selection_metric="accuracy_purity"):
    folder=Path(folder)
    datasets=list(dict.fromkeys(r["dataset"] for r in summary)); methods=list(dict.fromkeys(r["method"] for r in summary))
    selection=select_kmeans_extremes(summary,selection_metric)
    (folder/"kmeans_selection.json").write_text(json.dumps(selection,ensure_ascii=False,indent=2),encoding="utf-8")
    write_csv(folder/"kmeans_ranking.csv",selection["ranking"],("dataset","method","runs",selection_metric+"_mean"))
    chosen=[r["dataset"] for r in selection["selected"]]
    extremes=[dict(r,**{m+"_delta_vs_kmeans":r[m+"_mean"]-next(
        b[m+"_mean"] for b in selection["ranking"] if b["dataset"]==r["dataset"]) for m in METRICS})
              for r in summary if r["dataset"] in chosen]
    write_csv(folder/"extremes_comparison.csv",extremes,("dataset","method"))
    for metric,name in (("accuracy_purity","accuracy"),("ari","ari"),("nmi","nmi"),("runtime_seconds","time_seconds")):
        table=[]
        lookup={(r["dataset"],r["method"]):r for r in summary}
        for d in datasets:
            record={"dataset":d}
            for m in methods:
                r=lookup.get((d,m))
                if r is None: record[m]="NA"; continue
                sd=r[metric+"_std"]
                record[m]=f'{r[metric+"_mean"]:.6f} +/- {sd:.6f}' if sd is not None else f'{r[metric+"_mean"]:.6f} +/- NA'
            table.append(record)
        write_csv(folder/("table_"+name+".csv"),table)
    figures=[heatmap(summary,datasets,methods,folder),grouped_overview(summary,datasets,methods,folder)]
    for d in datasets:
        figures.append(bar_metrics(summary,[d],folder,"metrics_"+d,d+" | all implemented methods"))
        figures.append(cluster_figure(folder,d,rows,Path(experiment.get("data_root",Path(__file__).resolve().parents[1]/"datasets"))))
    if chosen:
        figures.append(bar_metrics(summary,chosen,folder,"kmeans_extremes_comparison",
                                   "Highest / lowest K-means datasets | all implemented methods"))
        figures.append(runtime_figure(summary,chosen,folder))
    trace=convergence(folder,datasets,rows)
    if trace: figures.append(trace)
    dashboard(folder,summary,experiment,selection,figures)
    return {"dashboard":"index.html","selection_metric":selection_metric,
            "selected_datasets":chosen,"figures":figures,
            "cluster_plot_rule":"First run; display-only color mapping; common PCA if dimension > 2."}
