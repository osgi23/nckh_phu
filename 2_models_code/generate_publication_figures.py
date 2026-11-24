# -*- coding: utf-8 -*-
"""
Generate publication-quality figures for the LaTeX paper:
1. figures/boxplot_30runs.pdf & .png: 2x2 Boxplots across 30 runs for Wine, Seed, Ecoli, Breast Tissue.
2. figures/convergence_curves.pdf & .png: Fitness convergence across 60 generations for M0, M3, M4.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

# Publication-grade styling (Elsevier / IEEE style)
mpl.rcParams['font.family'] = 'DejaVu Sans'
mpl.rcParams['font.size'] = 10
mpl.rcParams['axes.labelsize'] = 11
mpl.rcParams['axes.titlesize'] = 12
mpl.rcParams['xtick.labelsize'] = 9.5
mpl.rcParams['ytick.labelsize'] = 9.5
mpl.rcParams['legend.fontsize'] = 9.5
mpl.rcParams['figure.titlesize'] = 13

FIG_DIR = Path("d:/nckh_phu/4_documents/overleaf_paper/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)
RAW_CSV = Path("d:/nckh_phu/3_comparison_outputs/ablation_30runs_raw.csv")

# -------------------------------------------------------------
# 1. FIGURE 1: BOXPLOT COMPARISON OVER 30 RUNS
# -------------------------------------------------------------
def generate_boxplot():
    print("Generating Boxplot from raw CSV...")
    df = pd.read_csv(RAW_CSV)
    
    target_datasets = [
        ("wine", "Wine (D=13, K=3)", 0.9550),
        ("ecoli", "Ecoli (K=8, N=336)", 0.7770),
        ("seed", "Seed (D=7, K=3)", 0.9000),
        ("breast_tissue", "Breast Tissue (K=6)", 0.6150)
    ]
    
    variant_order = ["M0_Goc", "M1_H1_Sep", "M2_H2_DivDPC", "M3_H1_H2", "M4_Proposed"]
    variant_labels = ["M0 (Gốc)", "M1 (+H1)", "M2 (+H2)", "M3 (+H1+H2)", "M4 (Đề Xuất)"]
    palette = ["#E2E8F0", "#CBD5E0", "#BEE3F8", "#90CDF4", "#3182CE"]

    fig, axes = plt.subplots(2, 2, figsize=(10, 7.5), sharey=False)
    axes = axes.flatten()

    for idx, (dname, title, pub_val) in enumerate(target_datasets):
        ax = axes[idx]
        sub = df[df['dataset'] == dname]
        data_to_plot = [sub[sub['variant'] == v]['purity'].values for v in variant_order]
        
        bp = ax.boxplot(
            data_to_plot,
            patch_artist=True,
            widths=0.6,
            medianprops=dict(color='black', linewidth=1.5),
            flierprops=dict(marker='o', markersize=4, alpha=0.5)
        )
        
        for patch, color in zip(bp['boxes'], palette):
            patch.set_facecolor(color)
            patch.set_edgecolor('#2D3748')
            patch.set_linewidth(1.2)
            
        # Draw paper published line
        ax.axhline(pub_val, color='#C53030', linestyle='--', linewidth=1.4, alpha=0.9, label=f'Bài Báo Gốc ({pub_val:.3f})')
        
        ax.set_title(title, fontweight='bold', pad=8)
        ax.set_xticklabels(variant_labels, rotation=15, ha='right')
        ax.set_ylabel("Độ thuần khiết (Purity)")
        ax.grid(axis='y', linestyle=':', alpha=0.6)
        if idx == 0:
            ax.legend(loc='lower right', framealpha=0.9)

    plt.tight_layout()
    pdf_out = FIG_DIR / "boxplot_30runs.pdf"
    png_out = FIG_DIR / "boxplot_30runs.png"
    plt.savefig(pdf_out, bbox_inches='tight', dpi=300)
    plt.savefig(png_out, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"--> Saved: {pdf_out}")
    print(f"--> Saved: {png_out}")

# -------------------------------------------------------------
# 2. FIGURE 2: CONVERGENCE TRACE ACROSS 60 GENERATIONS
# -------------------------------------------------------------
def generate_convergence_curves():
    print("Generating Convergence Curves across GA generations...")
    from common.data import load_dataset
    from common.registry import fit_method

    CFG_DIR = Path(__file__).parent / "configs"
    cfg_paper = json.loads((CFG_DIR / "paper_table5.json").read_text(encoding="utf-8"))
    cfg_h1_h2 = json.loads((CFG_DIR / "improved_h1_h2.json").read_text(encoding="utf-8"))
    cfg_proposed = json.loads((CFG_DIR / "proposed_sd_mga_pfcm.json").read_text(encoding="utf-8"))

    models_to_test = {
        "M0 (Gốc)": (dict(cfg_paper, runs=1, generations=60, population=50), "#E53E3E", "--"),
        "M3 (+H1+H2)": (dict(cfg_h1_h2, runs=1, generations=60, population=50), "#DD6B20", "-."),
        "M4 (Đề Xuất SD-MGA)": (dict(cfg_proposed, runs=1, generations=60, population=50), "#2B6CB0", "-")
    }

    datasets_to_plot = [
        ("wine", "Wine (D=13, K=3)"),
        ("ecoli", "Ecoli (K=8, N=336)"),
        ("glass", "Glass (D=9, K=6)"),
        ("iris", "Iris (D=4, K=3)")
    ]

    fig, axes = plt.subplots(2, 2, figsize=(10, 7.5), sharex=True)
    axes = axes.flatten()

    for idx, (dname, title) in enumerate(datasets_to_plot):
        ax = axes[idx]
        X, y, meta = load_dataset(dname)
        k = meta['paper_k']
        
        for mname, (mcfg, color, lstyle) in models_to_test.items():
            rng = np.random.default_rng(2026)
            res = fit_method("DP-GA-PFCM", X, k, rng, mcfg)
            trace = res.diagnostics.get("optimizer_trace", [])
            gens = [t["generation"] for t in trace]
            # Normalize fitness to relative loss [0, 1] for visual comparability
            costs = np.array([t["best_fitness"] for t in trace])
            # Min-Max normalize within the trace to show trajectory
            c_norm = (costs - costs.min()) / (costs.max() - costs.min() + 1e-12)
            
            ax.plot(gens, c_norm, label=mname, color=color, linestyle=lstyle, linewidth=2.0)
            
        ax.set_title(title, fontweight='bold', pad=8)
        ax.set_ylabel("Hàm mất mát chuẩn hóa")
        ax.grid(True, linestyle=':', alpha=0.6)
        if idx >= 2:
            ax.set_xlabel("Thế hệ di truyền (Generations)")
        if idx == 0:
            ax.legend(loc='upper right', framealpha=0.9)

    plt.tight_layout()
    pdf_out = FIG_DIR / "convergence_curves.pdf"
    png_out = FIG_DIR / "convergence_curves.png"
    plt.savefig(pdf_out, bbox_inches='tight', dpi=300)
    plt.savefig(png_out, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"--> Saved: {pdf_out}")
    print(f"--> Saved: {png_out}")

if __name__ == "__main__":
    generate_boxplot()
    generate_convergence_curves()
