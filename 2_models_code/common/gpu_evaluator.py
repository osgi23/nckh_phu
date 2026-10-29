"""GPU-accelerated batched evaluation of PFCM chromosomes using PyTorch CUDA.

Accelerates DP-GA-PFCM, DP-PSO-PFCM, DP-SCA-PFCM, DP-FBI-PFCM by computing
the entire population (e.g. 80 chromosomes) simultaneously in parallel on
NVIDIA Tensor Cores instead of sequential CPU for-loops.
"""

from typing import Tuple
import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
    CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    TORCH_AVAILABLE = False
    CUDA_AVAILABLE = False

EPS = 1e-12

def is_gpu_supported() -> bool:
    """Return True if PyTorch with CUDA is available and functional."""
    return TORCH_AVAILABLE and CUDA_AVAILABLE

def get_device(requested: str = "auto") -> str:
    """Resolve device to 'cuda' or 'cpu'."""
    if requested in ("cuda", "gpu"):
        if not is_gpu_supported():
            raise RuntimeError("CUDA is requested but PyTorch CUDA is not available.")
        return "cuda"
    if requested == "cpu":
        return "cpu"
    # Auto
    return "cuda" if is_gpu_supported() else "cpu"

class GPUBatchedPFCM:
    """Evaluates all B chromosomes in parallel on GPU tensor cores."""
    def __init__(self, X: np.ndarray, k: int, cfg: dict, device: str = "cuda", dtype=None):
        self.k = k
        self.d = X.shape[1]
        self.cfg = cfg
        self.device = torch.device(device)
        if dtype is None:
            # float32 runs at maximum speed on RTX 4060 Tensor Cores
            # float64 can be selected via cfg if strict double precision is required
            use_double = cfg.get("gpu_double_precision", False)
            self.dtype = torch.float64 if use_double else torch.float32
        else:
            self.dtype = dtype

        # X on GPU: shape (1, N, D)
        self.X = torch.tensor(X, device=self.device, dtype=self.dtype).unsqueeze(0)
        self.N = X.shape[0]

        # Bounds on GPU
        bounds = cfg["parameter_bounds"]
        low_cpu = np.r_[np.tile(X.min(axis=0), k), [bounds[q][0] for q in ("a", "b", "w", "eta")]]
        high_cpu = np.r_[np.tile(X.max(axis=0), k), [bounds[q][1] for q in ("a", "b", "w", "eta")]]
        self.low = torch.tensor(low_cpu, device=self.device, dtype=self.dtype)
        self.high = torch.tensor(high_cpu, device=self.device, dtype=self.dtype)

        self.gamma_scale = float(cfg.get("gamma_scale", 1.0))
        self.gamma_refresh = cfg.get("gamma_refresh", "each_step")
        self.fitness_kind = cfg.get("fitness", "fcm_reference")
        self.ref_w = float(cfg.get("fitness_reference_w", 2.0))
        self.lamarckian = bool(cfg.get("lamarckian", False))

    def evaluate(self, genes_np: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Evaluate B chromosomes in a single batched GPU kernel execution.
        
        Args:
            genes_np: numpy array of shape (B, K*D + 4)
            
        Returns:
            updated_genes: numpy array of shape (B, K*D + 4)
            scores: numpy array of shape (B,)
        """
        B = len(genes_np)
        genes = torch.tensor(genes_np, device=self.device, dtype=self.dtype)
        # Repair bounds on GPU
        genes = torch.clamp(genes, self.low, self.high)

        # Unpack genes: centers (B, K, D), params (B, 1, 1)
        centers = genes[:, :self.k * self.d].reshape(B, self.k, self.d)
        a = genes[:, -4].view(B, 1, 1)
        b = genes[:, -3].view(B, 1, 1)
        w = genes[:, -2].view(B, 1, 1)
        eta = genes[:, -1].view(B, 1, 1)

        # 1. Batched pairwise squared distance: ||X - V||^2 -> shape (B, N, K)
        # self.X is (1, N, D), centers is (B, K, D)
        # torch.cdist computes (B, N, K) distance
        d2 = torch.cdist(self.X.expand(B, self.N, self.d), centers).pow(2)
        d2 = torch.clamp(d2, min=EPS)

        # 2. Memberships U (B, N, K)
        log_u = -torch.log(d2) / (w - 1.0)
        log_u = log_u - log_u.max(dim=2, keepdim=True).values
        u = torch.exp(log_u)
        u = u / torch.clamp(u.sum(dim=2, keepdim=True), min=EPS)

        # Handle exact coincident points if any
        zeros = d2 <= EPS
        if zeros.any():
            u = torch.where(zeros, zeros.float() / torch.clamp(zeros.float().sum(dim=2, keepdim=True), min=EPS), u)

        # 3. Gamma values: shape (B, 1, K)
        u_w = torch.pow(u, w)
        gamma_num = (u_w * d2).sum(dim=1, keepdim=True)
        gamma_den = torch.clamp(u_w.sum(dim=1, keepdim=True), min=EPS)
        gamma = torch.clamp(self.gamma_scale * (gamma_num / gamma_den), min=EPS)

        # 4. Typicalities T: shape (B, N, K)
        log_ratio = (torch.log(torch.clamp(b * d2, min=EPS)) - torch.log(gamma)) / (eta - 1.0)
        # t = 1 / (1 + exp(log_ratio)) = exp(-logaddexp(0, log_ratio))
        t = torch.exp(-torch.logaddexp(torch.zeros_like(log_ratio), log_ratio))
        t = torch.where(d2 <= EPS, torch.ones_like(t), t)

        # 5. One-step updated Centers: shape (B, K, D)
        t_eta = torch.pow(t, eta)
        weights = a * u_w + b * t_eta  # shape (B, N, K)
        total_weights = torch.clamp(weights.sum(dim=1, keepdim=True), min=EPS)  # shape (B, 1, K)

        # Batch matrix multiply: (B, K, N) @ (B, N, D) -> (B, K, D)
        new_centers = torch.bmm(weights.transpose(1, 2), self.X.expand(B, self.N, self.d))
        new_centers = new_centers / total_weights.transpose(1, 2)

        # 6. Evaluation objective on updated centers
        d2_new = torch.cdist(self.X.expand(B, self.N, self.d), new_centers).pow(2)
        d2_new = torch.clamp(d2_new, min=EPS)

        if self.fitness_kind == "fcm_reference":
            # Reference fuzzifier w=2.0
            log_ref_u = -torch.log(d2_new) / (self.ref_w - 1.0)
            log_ref_u = log_ref_u - log_ref_u.max(dim=2, keepdim=True).values
            ref_u = torch.exp(log_ref_u)
            ref_u = ref_u / torch.clamp(ref_u.sum(dim=2, keepdim=True), min=EPS)
            scores = (torch.pow(ref_u, self.ref_w) * d2_new).sum(dim=(1, 2))
        elif self.fitness_kind == "fcm":
            # Using current w
            log_u_new = -torch.log(d2_new) / (w - 1.0)
            log_u_new = log_u_new - log_u_new.max(dim=2, keepdim=True).values
            u_new = torch.exp(log_u_new)
            u_new = u_new / torch.clamp(u_new.sum(dim=2, keepdim=True), min=EPS)
            scores = (torch.pow(u_new, w) * d2_new).sum(dim=(1, 2))
        elif self.fitness_kind == "sse":
            scores = d2_new.min(dim=2).values.sum(dim=1)
        elif self.fitness_kind == "pfcm":
            # Eq. 11
            scores = (weights * d2_new).sum(dim=(1, 2)) + (gamma.squeeze(1) * torch.pow(1.0 - t, eta).sum(dim=1)).sum(dim=1)
        else:
            raise ValueError(f"Unknown fitness_kind: {self.fitness_kind}")

        # Lamarckian update if enabled
        if self.lamarckian:
            genes[:, :self.k * self.d] = new_centers.reshape(B, self.k * self.d)

        return genes.cpu().numpy(), scores.cpu().numpy()
