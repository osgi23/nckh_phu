"""PURPLE | Main DP-GA-PFCM: Sec.3.2, Eqs.(14)-(16), Table 5.
Underspecified choices are exposed in configs and ASSUMPTIONS.md.
"""
import numpy as np
from common.meta_pfcm import fit_meta

def genetic_algorithm(problem, initial, rng, cfg):
    pop, fitness = problem.evaluate(initial)
    size, width = pop.shape
    index = int(fitness.argmin())
    best, best_cost = pop[index].copy(), float(fitness[index])
    trace = [{"generation": 0, "best_fitness": best_cost,
              "evaluations": problem.evaluations}]
    for generation in range(1, cfg["generations"]+1):
        # Step 7: Roulette wheel selection for minimization problem.
        # [CHÚ THÍCH BỔ SUNG - KHÔNG CÓ SẴN TRONG BÀI BÁO]:
        # Bài báo chỉ ghi "roulette wheel selection" mà không cung cấp công thức chuyển đổi từ hàm loss (cần cực tiểu hóa)
        # sang xác suất chọn lọc. Nếu dùng trực tiếp 1/loss thì khi loss chênh lệch nhỏ sẽ bị mất áp lực chọn lọc (gần như ngẫu nhiên đều),
        # hoặc khi w lớn loss -> 0 sẽ bị bùng nổ xác suất. Ta áp dụng phép chuẩn hóa tuyến tính (linear scaling):
        # w_i = (f_max - f_i) / (f_max - f_min + eps) + 0.05 để đảm bảo áp lực chọn lọc ổn định.
        f_max = fitness.max()
        f_min = fitness.min()
        if f_max > f_min:
            weights = (f_max - fitness) / (f_max - f_min + 1e-12) + 0.05
        else:
            weights = np.ones(size)
        probabilities = weights / weights.sum()
        parents = pop[rng.choice(size, size=size, p=probabilities)].copy()
        children = parents.copy()
        for j in range(0, size-1, 2):
            if rng.random() < cfg["crossover_rate"]:
                r = rng.random()  # Eq.(14)-(15)
                children[j] = r*parents[j]+(1-r)*parents[j+1]
                children[j+1] = r*parents[j+1]+(1-r)*parents[j]
        # Sec.2.3 & Eq.(16): mutate one randomly selected gene per selected chromosome.
        # [CHÚ THÍCH BỔ SUNG]: Eq.(16) quy định k thuộc {4, 5, ..., 20}.
        for i in range(size):
            if rng.random() < cfg["mutation_rate"]:
                j = int(rng.integers(width))
                sign = rng.choice([-1.0, 1.0])
                k_prec = rng.integers(4, 21) if cfg.get("mutation_precision_range", True) else cfg.get("mutation_precision", 10)
                q = 2.0**(-rng.random()*k_prec)
                extent = cfg["mutation_range"]*(problem.high[j]-problem.low[j])
                children[i, j] += sign*extent*q
        children, next_fitness = problem.evaluate(children)
        elite = cfg["elite_count"]
        if elite:
            top = np.argsort(fitness, kind="stable")[:elite]
            worst = np.argsort(-next_fitness, kind="stable")[:elite]
            children[worst], next_fitness[worst] = pop[top], fitness[top]
        pop, fitness = children, next_fitness
        index = int(fitness.argmin())
        if fitness[index] < best_cost:
            best, best_cost = pop[index].copy(), float(fitness[index])
        trace.append({"generation": generation, "best_fitness": best_cost,
                      "evaluations": problem.evaluations})
    return best, best_cost, trace

def fit(X, k, rng, cfg):
    return fit_meta(X, k, rng, cfg, genetic_algorithm)
