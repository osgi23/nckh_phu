# Danh mục và Đặc tả Dữ liệu Thực nghiệm (Datasets)

Thư mục này lưu trữ toàn bộ **14 bộ dữ liệu thực nghiệm benchmark** được sử dụng để tái tạo và đánh giá các mô hình thuật toán phân cụm theo bài báo nghiên cứu **DP-GA-PFCM** (đối chiếu Bảng 1 trong bài báo).

---

## 1. Cấu trúc thư mục

```text
1_datasets/
├── 10_datasets_bai_bao/       # 10 bộ dữ liệu thực nghiệm chính của bài báo
│   ├── aggregation/           # Aggregation (N=788, D=2, K=7)
│   ├── breast_tissue/         # Breast Tissue (N=106, D=9, K=6)
│   ├── compound/              # Compound (N=399, D=2, K=6)
│   ├── ecoli/                 # Ecoli (N=336, D=7, K=8)
│   ├── flame/                 # Flame (N=240, D=2, K=2)
│   ├── glass/                 # Glass (N=214, D=9, K=7)
│   ├── iris/                  # Iris (N=150, D=4, K=3)
│   ├── jain/                  # Jain (N=373, D=2, K=2)
│   ├── seed/                  # Seed (N=210, D=7, K=3)
│   └── wine/                  # Wine (N=178, D=13, K=3)
├── 04_datasets_mo_rong/       # 4 bộ dữ liệu dùng đánh giá mở rộng / kiểm chứng bổ sung
│   ├── pima/                  # Pima Indians Diabetes (N=768, D=8, K=2)
│   ├── rice/                  # Rice Cammeo & Osmancik (N=3810, D=7, K=2)
│   ├── room_occupancy/        # Room Occupancy Detection (N=20560, D=5, K=2)
│   └── wifi/                  # Wireless Indoor Localization (N=2000, D=7, K=4)
├── BreastTissue.xls           # File Excel gốc của Breast Tissue
├── manifest.json              # File manifest kỹ thuật, mã băm SHA-256 và URL nguồn
├── summary.csv                # Bảng tóm tắt thông số toàn bộ 14 bộ dữ liệu
└── README.md                  # Tài liệu hướng dẫn này
```

---

## 2. Bảng đối chiếu thông số theo Bảng 1 của Bài báo

| STT | Tên Dataset | Thư mục | Số mẫu ($N$) | Số chiều ($D$) | Số cụm ($K$) | Số lớp thực tế | Nguồn dữ liệu |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---|
| 1 | **Iris** | `10_datasets_bai_bao/iris` | 150 | 4 | 3 | 3 | UCI ML Repository |
| 2 | **Flame** | `10_datasets_bai_bao/flame` | 240 | 2 | 2 | 2 | SIPU Shape Sets |
| 3 | **Jain** | `10_datasets_bai_bao/jain` | 373 | 2 | 2 | 2 | SIPU Shape Sets |
| 4 | **Wine** | `10_datasets_bai_bao/wine` | 178 | 13 | 3 | 3 | UCI ML Repository |
| 5 | **Glass** | `10_datasets_bai_bao/glass` | 214 | 9 | 7 | 6 | UCI ML Repository |
| 6 | **Ecoli** | `10_datasets_bai_bao/ecoli` | 336 | 7 | 8 | 8 | UCI ML Repository |
| 7 | **Compound** | `10_datasets_bai_bao/compound` | 399 | 2 | 6 | 6 | SIPU Shape Sets |
| 8 | **Seed** | `10_datasets_bai_bao/seed` | 210 | 7 | 3 | 3 | UCI ML Repository |
| 9 | **Breast Tissue** | `10_datasets_bai_bao/breast_tissue` | 106 | 9 | 6 | 6 | UCI ML Repository |
| 10 | **Aggregation** | `10_datasets_bai_bao/aggregation` | 788 | 2 | 7 | 7 | SIPU Shape Sets |
| 11 | **Pima** | `04_datasets_mo_rong/pima` | 768 | 8 | 2 | 2 | UCI / Kaggle Mirror |
| 12 | **Room Occupancy** | `04_datasets_mo_rong/room_occupancy` | 20560 | 5 | 2 | 2 | UCI ML Repository |
| 13 | **Rice** | `04_datasets_mo_rong/rice` | 3810 | 7 | 2 | 2 | UCI ML Repository |
| 14 | **Wifi** | `04_datasets_mo_rong/wifi` | 2000 | 7 | 4 | 4 | UCI ML Repository |

---

## 3. Quy chuẩn file trong từng thư mục dataset

Mỗi thư mục dataset con (ví dụ `10_datasets_bai_bao/iris/`) bao gồm:
1. `data.csv`: Chứa dữ liệu bảng đã xử lý tách nhãn:
   - Các cột thuộc tính đặc trưng số (`feature_columns`).
   - Cột `label`: Nhãn số nguyên từ $0$ đến $K-1$ dùng để đánh giá độ chính xác (Purity, ARI, NMI), **không** được đưa vào làm đầu vào cho thuật toán phân cụm.
   - Cột `label_original`: Nhãn chuỗi gốc ban đầu.
2. `metadata.json`: Chứa định nghĩa đặc trưng, số mẫu, số chiều, ánh xạ nhãn và checksum SHA-256 bảo đảm tính toàn vẹn dữ liệu.
3. `raw/`: Lưu trữ file dữ liệu gốc tải về từ nguồn (tệp zip, txt, data) và lịch sử tải.

---

## 4. Cách tải dữ liệu trong Python

```python
import csv
import json
from pathlib import Path

# Đường dẫn đến thư mục dataset
dataset_path = Path("1_datasets/10_datasets_bai_bao/iris")

# Đọc metadata
with open(dataset_path / "metadata.json", "r", encoding="utf-8") as f:
    meta = json.load(f)

# Đọc đặc trưng và nhãn
with open(dataset_path / "data.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    X = [[float(row[col]) for col in meta["feature_columns"]] for row in reader]

print(f"Loaded {meta['dataset_name']}: {len(X)} samples, {len(meta['feature_columns'])} features, K={meta['paper_k']}")
```
