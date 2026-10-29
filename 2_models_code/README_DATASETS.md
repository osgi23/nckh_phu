# Tải dataset cho DP-GA-PFCM

Script chính: `download_datasets.py`. Yêu cầu Python 3.10 trở lên.

Bài báo dùng 14 benchmark trong Table 1 và các bảng thực nghiệm. Cách chia 10 + 4 dưới đây là lựa chọn của bạn cho thí nghiệm riêng, không phải cách chia của tác giả. Dataset khách hàng RFM ở phần case study là một dataset riêng, không nằm trong 14 benchmark này; script chưa tải RFM vì bài không chỉ rõ DOI/tệp.

## Chạy

Từ thư mục dự án:

```powershell
python -m pip install -r code/requirements.txt
python code/download_datasets.py
```

Hoặc từ thư mục `code`:

```powershell
python -m pip install -r requirements.txt
python download_datasets.py
```

Chỉ cần thư viện `xlrd==2.0.2` để đọc Breast Tissue `.xls`. Các thao tác tải, đọc CSV/ARFF và ghi metadata dùng thư viện chuẩn Python.

## Chia nhóm

| STT Table 1 | Dataset | Nhóm | Số mẫu | Đặc trưng trong CSV | K trong bài | Số lớp thực |
|---:|---|---|---:|---:|---:|---:|
| 1 | Iris | su_dung | 150 | 4 | 3 | 3 |
| 2 | Flame | su_dung | 240 | 2 | 2 | 2 |
| 3 | Jain | su_dung | 373 | 2 | 2 | 2 |
| 4 | Wine | su_dung | 178 | 13 | 3 | 3 |
| 5 | Glass | su_dung | 214 | 9 | 7 | 6 |
| 6 | Ecoli | su_dung | 336 | 7 | 8 | 8 |
| 7 | Compound | su_dung | 399 | 2 | 6 | 6 |
| 8 | Seed | su_dung | 210 | 7 | 3 | 3 |
| 9 | Breast Tissue | su_dung | 106 | 9 | 6 | 6 |
| 10 | Aggregation | su_dung | 788 | 2 | 7 | 7 |
| 11 | Pima | khong_su_dung | 768 | 8 | 2 | 2 |
| 12 | Room Occupancy | khong_su_dung | 20560 | 5 | 2 | 2 |
| 13 | Rice | khong_su_dung | 3810 | 7 | 2 | 2 |
| 14 | Wifi | khong_su_dung | 2000 | 7 | 4 | 4 |

`khong_su_dung` nghĩa là chưa dùng trong nhóm thí nghiệm chính; bốn bộ vẫn được tải và chuẩn bị để đánh giá riêng. Đây là phân chia theo toàn bộ dataset, không phải chia các dòng thành tập train/test.

## Cấu trúc đầu ra

```text
code/
  download_datasets.py
  requirements.txt
  README.md
  datasets/
    manifest.json
    summary.csv
    su_dung/
      iris/
        data.csv
        metadata.json
        raw/
          source.zip
          download.json
          iris.data
      ... (10 dataset)
    khong_su_dung/
      pima/
      room_occupancy/
      rice/
      wifi/
```

Mỗi dataset có:

- `raw/`: dữ liệu gốc và bản ghi nguồn, thời gian tải, SHA-256. Các tệp trong ZIP cần cho parser cũng được lưu riêng; các tệp mô tả còn lại vẫn có trong ZIP gốc.
- `data.csv`: các đặc trưng số, sau đó là `label` và `label_original`.
- `metadata.json`: danh sách features, ánh xạ nhãn, số mẫu/lớp, `paper_k`, số đặc trưng trong bài và thực tế, checksum và các giả định.
- `sample_info.csv` khi có ID/ngày giờ/split cần giữ để truy vết. Thứ tự dòng tương ứng trực tiếp với `data.csv`, chỉ số `row_index` bắt đầu từ 0.

Nhãn `label` là số nguyên bắt đầu từ 0, ánh xạ xác định theo thứ tự nhãn. `label_original` giữ nhãn gốc. Khi chạy phân cụm, chỉ dùng `feature_columns` trong metadata làm X; cả hai cột nhãn chỉ để đánh giá, không đưa vào X.

Ví dụ đọc một bộ bằng thư viện chuẩn:

```python
import csv
import json
from pathlib import Path

folder = Path('code/datasets/su_dung/iris')
meta = json.loads((folder / 'metadata.json').read_text(encoding='utf-8'))
with (folder / 'data.csv').open(encoding='utf-8', newline='') as f:
    rows = list(csv.DictReader(f))
X = [[float(row[name]) for name in meta['feature_columns']] for row in rows]
y = [int(row['label']) for row in rows]
k_for_paper = meta['paper_k']
```

Script không chuẩn hóa MinMax, không xóa outlier, không thay giá trị 0/âm, không shuffle, không impute và không tạo dữ liệu giả. MinMax sẽ được thực hiện ở bước mô hình sau này.

## Các lựa chọn cần ghi nhớ

1. **Iris:** mặc định lấy `iris.data`. UCI còn có `bezdekIris.data`; bài báo không xác định biến thể. Có thể chọn `--iris-variant bezdekIris.data`. ZIP gốc giữ cả hai.
2. **Glass:** giữ `paper_k=7` theo bài, đồng thời ghi 6 lớp thực trong dữ liệu. Không tạo thêm lớp 4 hoặc đổi nhãn để giả lập 7 lớp.
3. **Room Occupancy:** ghép `datatraining.txt`, `datatest.txt`, `datatest2.txt` theo thứ tự đó để có 20.560 mẫu. CSV dùng 5 cảm biến Temperature, Humidity, Light, CO2, HumidityRatio. ID, ngày giờ và target không phải features. Bài ghi F=7 nhưng chưa giải thích cách mã hóa; script ghi `matches_paper_features=false`, không tạo thêm features giả. Các split gốc và ngày giờ được giữ trong `sample_info.csv`.
4. **Pima:** đường dẫn UCI cũ trả 404 nên dùng bản sao công khai từ `jbrownlee/Datasets`, ghi `source_type=mirror`. Các giá trị 0 giữ nguyên.
5. **Breast Tissue:** dùng sheet `Data`, bỏ Case ID khỏi X, giữ đủ sáu lớp gốc, không gộp thành bốn lớp.
6. Bài không cung cấp hash dữ liệu tác giả dùng. Khớp N/F/K và nguồn công khai chưa chứng minh tệp giống hệt phiên bản tác giả.

## Tuỳ chọn

```powershell
# Chỉ liệt kê, không tải/ghi tệp
python code/download_datasets.py --list

# Chỉ tải 10 bộ dùng chính
python code/download_datasets.py --group su_dung

# Chỉ tải bốn bộ đánh giá riêng
python code/download_datasets.py --group khong_su_dung

# Tải lại từ nguồn
python code/download_datasets.py --force

# Tạo lại CSV từ dữ liệu đã tải, không dùng mạng
python code/download_datasets.py --offline

# Thư mục đầu ra khác
python code/download_datasets.py --output D:/du_lieu/DP_GA_PFCM
```

Mặc định, chạy lại sẽ dùng raw cache đã kiểm tra SHA-256. Nếu cache bị sửa, script dừng bộ đó và yêu cầu `--force`; không dùng dữ liệu sai một cách im lặng. Các bộ lỗi được ghi trong manifest, các bộ khác vẫn tiếp tục. Exit code: 0 thành công; 1 có dataset lỗi; 2 tham số CLI hoặc thư viện thiếu. `--force` và `--offline` không dùng chung.

Đường dẫn mặc định luôn là `datasets` cạnh script, bất kể bạn chạy từ thư mục nào. Thư mục chỉ tải một nhóm vẫn giữ danh sách phân nhóm đủ 14 bộ trong manifest; dùng trường `status` để biết bộ đã có dữ liệu.

## Nguồn

- Bài báo: DOI [10.1016/j.jestch.2023.101525](https://doi.org/10.1016/j.jestch.2023.101525), Table 1.
- Các bộ thật: [UCI Machine Learning Repository](https://archive.ics.uci.edu/). URL cụ thể có trong script và metadata của từng bộ.
- Flame, Jain, Compound, Aggregation: [SIPU / University of Eastern Finland](https://cs.joensuu.fi/sipu/datasets/).
- Pima mirror: [jbrownlee/Datasets](https://github.com/jbrownlee/Datasets).
- [UCI Room Occupancy](https://archive.ics.uci.edu/dataset/357/occupancy+detection) định danh ID, date, sensor và target.

Kiểm tra thực tế: đã tải đủ 14/14, kiểm tra số mẫu, số đặc trưng số, số lớp, giá trị hữu hạn và hash nguồn. Tất cả số mẫu khớp Table 1; Room Occupancy và Glass giữ các chênh lệch đã nêu, không sửa để ép khớp bài.
