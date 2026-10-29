"""Paper Eq.(17) is purity; NMI uses GEOMETRIC entropy normalization."""
import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from sklearn.metrics.cluster import contingency_matrix

def quality(y, labels):
    table = contingency_matrix(y, labels)
    purity = float(table.max(axis=0).sum()/len(y))
    row, col = linear_sum_assignment(-table)
    hungarian = float(table[row, col].sum()/len(y))
    return {
        "accuracy_purity": purity,
        "ari": float(adjusted_rand_score(y, labels)),
        "nmi": float(normalized_mutual_info_score(y, labels, average_method="geometric")),
        "accuracy_hungarian": hungarian,
        "observed_clusters": int(len(np.unique(labels)))
    }
