"""Nc/L ARI protocol: all-run mean, dataset-wise best, paired Wilcoxon."""
import numpy as np
from scipy.stats import wilcoxon, PermutationMethod
from common.reporting import write_csv

def sample_sd(values):
    return float(np.std(values, ddof=1)) if len(values)>1 else None

def signed_rank(first, second):
    # Round only test differences, to prevent floating-point pseudo-differences.
    difference = np.round(np.asarray(first)-np.asarray(second), 12)
    if not np.any(difference):
        return 1.
    return float(wilcoxon(difference, alternative="two-sided", zero_method="wilcox",
                          method=PermutationMethod(n_resamples=np.inf)).pvalue)

def protocol_tables(output, rows, study, methods):
    dataset_ids = list(range(1,study["n_datasets"]+1))
    grouped, table, tests = [], [], []
    for condition in study["conditions"]:
        slug = condition["slug"]
        by_method = {}
        for method in methods:
            records = []
            for data_id in dataset_ids:
                block = [r for r in rows if r["dataset"]==slug and r["method"]==method and r["dataset_id"]==data_id]
                if len(block)!=study["runs_per_dataset"]:
                    raise ValueError(f"Wrong number of restarts for {slug}/{method}/{data_id}")
                values = [r["ari"] for r in block]
                best = max(block,key=lambda r:(r["ari"],-r["run"]))
                record = {"Nc":study["Nc"],"L":study["L"],"outlier_ratio":condition["actual_ratio"],
                          "dataset":slug,"method":method,"dataset_id":data_id,
                          "balance_level":block[0]["balance_level"],"n_runs":len(block),
                          "ari_mean":float(np.mean(values)),"ari_std":sample_sd(values),
                          "ari_best":best["ari"],"best_run":best["run"]}
                records.append(record);grouped.append(record)
            by_method[method] = records
        winner, pvalue = "", None
        if "K-means" in by_method and "DP-GA-PFCM" in by_method:
            first = [r["ari_mean"] for r in by_method["K-means"]]
            second = [r["ari_mean"] for r in by_method["DP-GA-PFCM"]]
            pvalue = signed_rank(first,second)
            if pvalue < .05:
                winner = "K-means" if np.mean(first)>np.mean(second) else "DP-GA-PFCM"
            tests.append({"Nc":study["Nc"],"L":study["L"],"outlier_ratio":condition["actual_ratio"],
                          "reference":"K-means","method":"DP-GA-PFCM","n_pairs":len(first),
                          "p_value":pvalue,"significant_0p05":pvalue<.05,"winner":winner,
                          "test_unit":"Paired dataset mean ARI, averaging algorithm restarts",
                          "test":"Two-sided Wilcoxon signed-rank; exact sign permutations; no multiple-testing adjustment"})
        for method in methods:
            all_values = [r["ari"] for r in rows if r["dataset"]==slug and r["method"]==method]
            best_values = [r["ari_best"] for r in by_method[method]]
            table.append({"Nc":study["Nc"],"L":study["L"],"outlier_ratio":condition["actual_ratio"],
                          "method":method,"datasets":len(dataset_ids),"runs_per_dataset":study["runs_per_dataset"],
                          "n_total_runs":len(all_values),"ari_mean":float(np.mean(all_values)),
                          "ari_std":sample_sd(all_values),"ari_best_mean":float(np.mean(best_values)),
                          "ari_best_std":sample_sd(best_values),
                          "wilcoxon_p":pvalue if method in ("K-means","DP-GA-PFCM") else None,
                          "highlight_mean":method==winner,
                          "s_marker":"s" if method==winner else ""})
    write_csv(output/"ari_by_dataset.csv",grouped)
    write_csv(output/"nc_l_ari.csv",table)
    write_csv(output/"wilcoxon.csv",tests,("Nc","L","outlier_ratio","p_value"))
    return table
