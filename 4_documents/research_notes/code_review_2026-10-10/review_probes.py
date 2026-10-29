"""Read-only probes of the reproduction; writes evidence only in this folder."""
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[2]
CODE = WORKSPACE / 'code'
sys.path.insert(0, str(CODE))
from common.data import load_dataset
from common.density_peak import density_peak_centers
from common.metrics import quality
from common.numerics import memberships, pfcm_step, solve_pfcm, squared_distance
from common.runner import validate_config


def read_rows(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def main():
    cfg = json.loads((CODE / 'configs/paper_table5.json').read_text())
    X, y, _ = load_dataset('iris')
    centers, _ = density_peak_centers(X, 3, cfg)
    d2 = squared_distance(X, centers)
    fixed_center_probe = []
    for w in (1.5, 2.0, 3.0, 5.0):
        u = memberships(d2, w)
        labels = u.argmax(axis=1)
        fixed_center_probe.append(dict(w=w, fcm_loss=float((u**w*d2).sum()),
                                       label_sha256=hashlib.sha256(labels.tobytes()).hexdigest(),
                                       **quality(y, labels)))

    # Independent scalar implementation on a non-symmetric fixture.
    fixture = np.array([[0., 0.], [1., 2.], [3., 1.], [4., 4.]])
    initial = np.array([[.2, .5], [3.5, 2.5]])
    p = dict(a=1.3, b=.7, w=2.2, eta=1.8, gamma_scale=1.2)
    dist = np.array([[sum((float(x[z])-float(v[z]))**2 for z in range(2))
                      for v in initial] for x in fixture])
    u = np.array([[1/sum((dist[i,j]/dist[i,h])**(1/(p['w']-1)) for h in range(2))
                   for j in range(2)] for i in range(4)])
    gamma = np.array([p['gamma_scale']*sum(u[i,j]**p['w']*dist[i,j] for i in range(4)) /
                      sum(u[i,j]**p['w'] for i in range(4)) for j in range(2)])
    t = np.array([[1/(1+(p['b']*dist[i,j]/gamma[j])**(1/(p['eta']-1)))
                   for j in range(2)] for i in range(4)])
    weights = p['a']*u**p['w'] + p['b']*t**p['eta']
    expected = np.array([[sum(weights[i,j]*fixture[i,z] for i in range(4)) /
                          sum(weights[i,j] for i in range(4))
                          for z in range(2)] for j in range(2)])
    actual, actual_gamma = pfcm_step(fixture, initial, p)
    np.testing.assert_allclose(actual, expected, atol=1e-12, rtol=1e-12)
    np.testing.assert_allclose(actual_gamma, gamma, atol=1e-12, rtol=1e-12)

    root = CODE / 'results/paper_iris30'
    main_rows = [r for r in read_rows(root/'runs.csv') if r['method']=='DP-GA-PFCM']
    details = [json.loads(path.read_text()) for path in
               sorted((root/'artifacts/iris/DP-GA-PFCM').glob('run_*/details.json'))]
    stopping = []
    gamma_replay = []
    for index, item in enumerate(details, 1):
        trace = item['trace']
        if len(trace) > 1:
            stopping.append(dict(run=index, iterations=item['iterations'],
                                 center_shift=trace[-1]['center_shift'],
                                 absolute_objective_change=abs(trace[-1]['objective']-trace[-2]['objective'])))
        # Hold the GA output and parameters constant; change ONLY gamma policy.
        gene = np.array(item['diagnostics']['best_chromosome'])
        initial_centers = gene[:12].reshape(3, 4)
        policies = {}
        for policy in ('each_step', 'fixed'):
            replay = solve_pfcm(X, initial_centers, dict(cfg, **item['params'], gamma_refresh=policy))
            policies[policy] = dict(iterations=replay.iterations, **quality(y, replay.labels()))
        gamma_replay.append(dict(run=index, policies=policies))

    invalid_config = []
    for key in ('tol', 'gamma_scale', 'seed_jitter', 'mutation_range'):
        for tag, value in (('NaN', float('nan')), ('positive_infinity', float('inf'))):
            candidate = dict(cfg, **{key: value})
            try:
                validate_config(candidate)
                status = 'accepted'
            except (ValueError, TypeError) as exc:
                status = f'rejected: {exc}'
            invalid_config.append(dict(key=key, value=tag, status=status))
    infinite_tol_result = solve_pfcm(X, centers, dict(cfg, tol=float('inf')))

    summary_row = next(r for r in read_rows(root/'summary.csv') if r['method']=='DP-GA-PFCM')
    metrics = {'accuracy_purity': .914, 'ari': .774, 'nmi': .775}
    comparisons = {metric: dict(paper=paper, reproduction=float(summary_row[metric+'_mean']),
                                difference=float(summary_row[metric+'_mean'])-paper)
                   for metric, paper in metrics.items()}
    model_paths = ['common/numerics.py', 'common/meta_pfcm.py', 'common/density_peak.py',
                   'purple_main_model/dp_ga_pfcm.py', 'configs/paper_table5.json']
    evidence = dict(
        review_date='2026-10-10', reviewed_directory=str(CODE),
        fixed_centers_vary_w=fixed_center_probe,
        scalar_pfcm_fixture=dict(max_center_error=float(np.max(np.abs(actual-expected))),
                                  max_gamma_error=float(np.max(np.abs(actual_gamma-gamma)))),
        iris30=dict(n_runs=len(main_rows), comparison=comparisons,
                    median_w=float(np.median([r['params']['w'] for r in details])),
                    runs_with_two_observed_clusters=sum(int(r['observed_clusters'])==2 for r in main_rows)),
        stopping_probe=stopping,
        converged_center_but_objective_delta_above_config_tol=sum(
            r['center_shift']<=cfg['tol'] and r['absolute_objective_change']>cfg['tol'] for r in stopping),
        gamma_replay=gamma_replay,
        gamma_replay_mean={policy: {metric: float(np.mean([r['policies'][policy][metric] for r in gamma_replay]))
                                    for metric in metrics} for policy in ('each_step', 'fixed')},
        nonfinite_validation=invalid_config,
        infinite_tol_execution=dict(iterations=infinite_tol_result.iterations,
                                     converged=infinite_tol_result.diagnostics['converged']),
        model_sha256={p: hashlib.sha256((CODE/p).read_bytes()).hexdigest() for p in model_paths},
    )
    target = Path(__file__).with_name('evidence.json')
    target.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({key:evidence[key] for key in (
        'fixed_centers_vary_w', 'scalar_pfcm_fixture', 'iris30',
        'converged_center_but_objective_delta_above_config_tol', 'gamma_replay_mean',
        'nonfinite_validation', 'infinite_tol_execution')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
