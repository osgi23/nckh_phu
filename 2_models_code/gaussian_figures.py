"""Static scientific figures for the paired Gaussian contamination experiment."""
import csv
import json
import math
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.decomposition import PCA
from sklearn.metrics.cluster import contingency_matrix
from common.visual_results import (
    plt, save_figure, heatmap, grouped_overview, bar_metrics,
    select_kmeans_extremes, runtime_figure, convergence)
from common.reporting import write_csv

SHADES = {"K-means":"#173f8a", "FCM":"#3b82f6", "PFCM":"#93b8f4",
          "DP-FCM":"#0e7490", "DP-PFCM":"#38bdf8", "DP-GA-PFCM":"#9333ea",
          "DP-PSO-PFCM":"#c2410c", "DP-SCA-PFCM":"#f97316", "DP-FBI-PFCM":"#9a3412"}

def robustness(output, summary, study, methods):
    metrics = [("accuracy_purity","Inlier purity (higher is better)"),
               ("ari","Inlier ARI (higher is better)"), ("nmi","Inlier NMI (higher is better)"),
               ("center_rmse","Center RMSE in original feature units (lower is better)")]
    lookup = {(r["dataset"], r["method"]): r for r in summary}
    x = np.array([100*c["actual_ratio"] for c in study["conditions"]])
    fig, axes = plt.subplots(2, 2, figsize=(16, 10), layout="constrained")
    markers = ["o","s","^","v","D","P","X","*","h"]
    for ax, (metric, title) in zip(axes.ravel(), metrics):
        for i, method in enumerate(methods):
            records = [lookup[(c["slug"], method)] for c in study["conditions"]]
            y = [r[metric+"_mean"] for r in records]
            sd = [r[metric+"_std"] or 0 for r in records]
            main = method=="DP-GA-PFCM"
            ax.errorbar(x, y, yerr=sd, color=SHADES[method], marker=markers[i%len(markers)],
                        linewidth=2.5 if main else 1.25, markersize=7 if main else 5,
                        capsize=2, elinewidth=.8, alpha=1 if main else .85, label=method)
        ax.set_xticks(x, [f"{v:g}%" for v in x])
        ax.set_xlabel("Outlier fraction of all samples")
        ax.set_title(title)
        if metric in ("accuracy_purity", "nmi"):
            ax.set_ylim(0, 1.06)
        if metric=="ari":
            ax.set_ylim(min(-.05, min(r["ari_mean"]-(r["ari_std"] or 0) for r in summary)-.02), 1.06)
        ax.grid(alpha=.2)
    handles, labels = axes[0,0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=5, fontsize=10)
    fig.suptitle(f"Gaussian clusters with replacement outliers | Nc={study['Nc']}, L={study['L']}, n={study['n_samples']}\n"
                 f"{study['n_datasets']} paired datasets x {study['runs_per_dataset']} restarts; mean +/- sample SD; scores exclude outliers",
                 fontsize=14)
    return save_figure(fig, output, "gaussian_robustness")

def cluster_figure(output, slug, rows, study):
    first = [r for r in rows if r["dataset"]==slug and r["run"]==1 and r["dataset_id"]==1]
    with np.load(output/first[0]["data_artifact"]) as source:
        clean = source["X_clean"]
        X, truth = source["X_raw_"+slug], source["y_"+slug]
        true_centers = source["true_centers"]
        all_X = np.concatenate([source["X_raw_"+c["slug"]] for c in study["conditions"]])
    if study["L"] >= 2:
        pca = PCA(n_components=2, svd_solver="full").fit(clean)
        project = pca.transform
        axis = ("PC1 from clean 5D data" if study["L"]==5 else "PC1 from clean data", "PC2 from clean data")
        variance = pca.explained_variance_ratio_.sum()*100
        caption = f"common clean-data PCA ({variance:.1f}% variance)"
    else:
        project = lambda z: np.column_stack((z[:,0], np.zeros(len(z))))
        axis = ("Feature 1", "Display zero axis")
        caption = "one feature; vertical axis for display only"
    points = project(X)
    inliers, outliers = truth>=0, truth<0
    palette = plt.colormaps["tab20"]
    panels = [("True Gaussian classes", truth, true_centers)]
    for row in first:
        with np.load(output/row["artifact"]/"model.npz") as model:
            labels = model["labels"].copy()
            centers = model["centers_raw"].copy()
        table = contingency_matrix(truth[inliers], labels[inliers])
        rr, cc = linear_sum_assignment(-table)
        ids = np.unique(labels[inliers])
        mapping = {int(ids[c]): int(r) for r,c in zip(rr,cc)}
        mapped = np.array([mapping.get(int(v), study["Nc"]+int(v)) for v in labels])
        panels.append((row["method"]+f"\nInlier purity {row['accuracy_purity']:.3f} | ARI {row['ari']:.3f}", mapped, centers))
    fig, axes = plt.subplots(math.ceil(len(panels)/3),3,figsize=(16,math.ceil(len(panels)/3)*3.8),
                             sharex=True,sharey=True,layout="constrained",squeeze=False)
    limits = project(all_X)
    margin = .06*np.maximum(limits.max(axis=0)-limits.min(axis=0), 1.)
    for ax, (title, labels, centers) in zip(axes.ravel(), panels):
        ax.scatter(points[inliers,0],points[inliers,1],
                   c=[palette(int(v)%20) for v in labels[inliers]],s=16,alpha=.7)
        if outliers.any():
            ax.scatter(points[outliers,0],points[outliers,1],c="#9ca3af",marker="x",s=20,alpha=.7)
        projected = project(centers)
        ax.scatter(projected[:,0],projected[:,1],c="black",marker="X",s=85,linewidths=.5)
        ax.set_xlim(limits[:,0].min()-margin[0],limits[:,0].max()+margin[0])
        ax.set_ylim(limits[:,1].min()-margin[1],limits[:,1].max()+margin[1])
        ax.set_title(title,fontsize=10)
        ax.set_xlabel(axis[0]); ax.set_ylabel(axis[1]); ax.grid(alpha=.15)
    for ax in axes.ravel()[len(panels):]:
        ax.set_visible(False)
    fraction = next(c["actual_ratio"] for c in study["conditions"] if c["slug"]==slug)
    fig.suptitle(f"Nc={study['Nc']}, L={study['L']}, outliers={fraction:.0%} | first predefined replicate | {caption}\n"
                 "Gray x = known outliers (display/evaluation only); black X = centers; colors aligned only for display",fontsize=13)
    return save_figure(fig,output,"clusters_"+slug)

def nc_l_table_figure(output, study):
    with (output/"nc_l_ari.csv").open(encoding="utf-8-sig",newline="") as stream:
        rows=list(csv.DictReader(stream))
    if not all(m in {r["method"] for r in rows} for m in ("K-means","DP-GA-PFCM")):
        return None
    headers=["Nc","L","Outliers","K-means\nMean ARI","K-means\nBest ARI",
             "DP-GA-PFCM\nMean ARI","DP-GA-PFCM\nBest ARI","Wilcoxon p"]
    values=[]; winners=[]
    for condition in study["conditions"]:
        block=[r for r in rows if abs(float(r["outlier_ratio"])-condition["actual_ratio"])<1e-10]
        base=next(r for r in block if r["method"]=="K-means")
        main=next(r for r in block if r["method"]=="DP-GA-PFCM")
        def cell(r,best=False):
            m="ari_best_mean" if best else "ari_mean"
            sd="ari_best_std" if best else "ari_std"
            return f"{float(r[m]):.4f} +/- {float(r[sd]):.4f}" if r[sd] else f"{float(r[m]):.4f} +/- NA"
        values.append([study["Nc"],study["L"],f"{condition['actual_ratio']:.0%}",
                       cell(base),cell(base,True),cell(main),cell(main,True),
                       f"{float(main['wilcoxon_p']):.4g}" if main["wilcoxon_p"] else "NA"])
        winners.append(3 if base["s_marker"]=="s" else 5 if main["s_marker"]=="s" else None)
    fig,ax=plt.subplots(figsize=(17,3.8))
    ax.axis("off")
    table=ax.table(cellText=values,colLabels=headers,cellLoc="center",loc="center",
                   colWidths=[.035,.035,.08,.17,.17,.17,.17,.13])
    table.auto_set_font_size(False);table.set_fontsize(10);table.scale(1,2)
    for (r,c),cell in table.get_celld().items():
        cell.set_edgecolor("#dbe3ee")
        if r==0:
            cell.set_facecolor("#eaf0f9");cell.set_text_props(weight="bold")
        elif winners[r-1]==c:
            cell.set_text_props(weight="bold",color="#0f766e")
            cell.get_text().set_text(cell.get_text().get_text()+" (s)")
    fig.suptitle(f"ARI by Nc and L | {study['n_datasets']} datasets x {study['runs_per_dataset']} independent restarts",fontsize=15)
    fig.text(.5,.05,"Mean: all runs; Best: dataset-wise maximum then mean. Sample SD. Scores on Gaussian inliers only.\n"
             "(s): better mean in the K-means / DP-GA-PFCM pair, two-sided paired Wilcoxon p < .05; unadjusted per outlier level.",
             ha="center",fontsize=10)
    fig.tight_layout(rect=(0,.14,1,.90))
    return save_figure(fig,output,"nc_l_ari_table")

def build_gaussian_figures(output, summary, rows, experiment):
    study, methods = experiment["gaussian"], experiment["methods"]
    names = [c["slug"] for c in study["conditions"]]
    selection = select_kmeans_extremes(summary)
    (output/"kmeans_selection.json").write_text(json.dumps(selection,ensure_ascii=False,indent=2),encoding="utf-8")
    write_csv(output/"kmeans_ranking.csv",selection["ranking"],("dataset","method","runs"))
    chosen = [r["dataset"] for r in selection["selected"]]
    lookup = {r["dataset"]:r for r in selection["ranking"]}
    write_csv(output/"extremes_comparison.csv",
              [dict(r,**{m+"_delta_vs_kmeans":r[m+"_mean"]-lookup[r["dataset"]][m+"_mean"]
                         for m in ("accuracy_purity","ari","nmi")}) for r in summary if r["dataset"] in chosen],
              ("dataset","method"))
    figures = [robustness(output,summary,study,methods),
               heatmap(summary,names,methods,output), grouped_overview(summary,names,methods,output)]
    table_figure=nc_l_table_figure(output,study)
    if table_figure: figures.append(table_figure)
    for condition in study["conditions"]:
        slug = condition["slug"]
        figures.append(bar_metrics(summary,[slug],output,"metrics_"+slug,
                                   f"Nc={study['Nc']}, L={study['L']}; outliers={condition['actual_ratio']:.0%}; inliers only"))
        figures.append(cluster_figure(output,slug,rows,study))
    if chosen:
        figures.append(bar_metrics(summary,chosen,output,"kmeans_extremes_comparison",
                                   "Highest / lowest K-means contamination conditions | inlier quality"))
        figures.append(runtime_figure(summary,chosen,output))
    serial_rows=[dict(r,run=(r["dataset_id"]-1)*study["runs_per_dataset"]+r["run"]) for r in rows]
    trace = convergence(output,names,serial_rows)
    if trace:
        figures.append(trace)
    return {"dashboard":"index.html","figures":figures,"selection_metric":"accuracy_purity",
            "selected_datasets":chosen,"metrics_scope":study["metrics_scope"]}
