import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import json
import numpy as np
from common.data import load_dataset
from common.registry import fit_method
from common.metrics import quality

datasets = ['iris', 'wine', 'flame', 'seed', 'glass', 'ecoli', 'breast_tissue', 'jain']

cfg_orig = json.loads((Path(__file__).parent / "configs" / "paper_table5.json").read_text(encoding="utf-8"))
cfg_impr = json.loads((Path(__file__).parent / "configs" / "improved_h1_h2.json").read_text(encoding="utf-8"))

# Load paper published metrics
import csv
paper_pub = {}
with open(Path(__file__).parent / "reference" / "paper_metrics.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        if row['method'] == 'DP-GA-PFCM' and row['metric'] == 'accuracy_purity':
            paper_pub[row['dataset']] = float(row['mean'])

methods_to_compare = [
    'K-means', 'FCM', 'PFCM', 'DP-PFCM',
    'DP-PSO-PFCM', 'DP-SCA-PFCM', 'DP-FBI-PFCM',
    'DP-GA-PFCM-Orig', 'DP-GA-PFCM-Improved'
]

print("="*120)
print(f"{'Dataset':15s} | {'K-means':8s} | {'FCM':8s} | {'PFCM':8s} | {'DP-PFCM':8s} | {'DP-PSO':8s} | {'DP-FBI':8s} | {'GA-Gốc':8s} | {'GA-CảiTiến':10s} | {'BàiBáo(Pub)':11s}")
print("="*120)

results = {}

for dname in datasets:
    X, y, meta = load_dataset(dname)
    k = meta['paper_k']
    results[dname] = {}
    
    # K-means
    res = fit_method('K-means', X, k, np.random.default_rng(2026), cfg_orig)
    results[dname]['K-means'] = quality(y, res.labels())['accuracy_purity']
    
    # FCM
    res = fit_method('FCM', X, k, np.random.default_rng(2026), cfg_orig)
    results[dname]['FCM'] = quality(y, res.labels())['accuracy_purity']
    
    # PFCM
    res = fit_method('PFCM', X, k, np.random.default_rng(2026), cfg_orig)
    results[dname]['PFCM'] = quality(y, res.labels())['accuracy_purity']
    
    # DP-PFCM
    res = fit_method('DP-PFCM', X, k, np.random.default_rng(2026), cfg_orig)
    results[dname]['DP-PFCM'] = quality(y, res.labels())['accuracy_purity']
    
    # DP-PSO
    res = fit_method('DP-PSO-PFCM', X, k, np.random.default_rng(2026), cfg_impr)
    results[dname]['DP-PSO'] = quality(y, res.labels())['accuracy_purity']
    
    # DP-FBI
    res = fit_method('DP-FBI-PFCM', X, k, np.random.default_rng(2026), cfg_impr)
    results[dname]['DP-FBI'] = quality(y, res.labels())['accuracy_purity']
    
    # DP-GA-PFCM Orig
    res = fit_method('DP-GA-PFCM', X, k, np.random.default_rng(2026), cfg_orig)
    results[dname]['GA-Gốc'] = quality(y, res.labels())['accuracy_purity']
    
    # DP-GA-PFCM Improved
    res = fit_method('DP-GA-PFCM', X, k, np.random.default_rng(2026), cfg_impr)
    results[dname]['GA-CảiTiến'] = quality(y, res.labels())['accuracy_purity']
    
    r = results[dname]
    pub = paper_pub.get(dname, 0.0)
    print(f"{dname:15s} | {r['K-means']:8.4f} | {r['FCM']:8.4f} | {r['PFCM']:8.4f} | {r['DP-PFCM']:8.4f} | {r['DP-PSO']:8.4f} | {r['DP-FBI']:8.4f} | {r['GA-Gốc']:8.4f} | {r['GA-CảiTiến']:10.4f} | {pub:11.4f}")

print("="*120)
