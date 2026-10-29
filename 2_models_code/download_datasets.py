#!/usr/bin/env python3
"""Download the 14 Table-1 datasets for DP-GA-PFCM reproduction.

Python >= 3.10. Only Breast Tissue XLS parsing requires xlrd:
    python -m pip install -r requirements.txt
    python download_datasets.py

Grouping is the user's experimental choice, NOT a split made by the paper:
first 10 datasets -> su_dung; last 4 -> khong_su_dung (external evaluation).
Feature values, zeros, negative values and outliers are preserved. No scaling,
imputation, shuffle, synthetic data, or labels-as-features are performed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request
import zipfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class DatasetSpec:
    order: int
    name: str
    slug: str
    n: int
    paper_features: int
    paper_k: int
    numeric_features: int
    observed_classes: int
    url: str
    homepage: str
    source_type: str = "primary"

    @property
    def group(self) -> str:
        return "su_dung" if self.order <= 10 else "khong_su_dung"


def uci(dataset_id: int, filename: str) -> str:
    return f"https://archive.ics.uci.edu/static/public/{dataset_id}/{filename}.zip"


SIPU = "https://cs.joensuu.fi/sipu/datasets/"
SPECS = (
    DatasetSpec(1, "Iris", "iris", 150, 4, 3, 4, 3, uci(53, "iris"), "https://archive.ics.uci.edu/dataset/53/iris"),
    DatasetSpec(2, "Flame", "flame", 240, 2, 2, 2, 2, SIPU + "flame.txt", SIPU),
    DatasetSpec(3, "Jain", "jain", 373, 2, 2, 2, 2, SIPU + "jain.txt", SIPU),
    DatasetSpec(4, "Wine", "wine", 178, 13, 3, 13, 3, uci(109, "wine"), "https://archive.ics.uci.edu/dataset/109/wine"),
    DatasetSpec(5, "Glass", "glass", 214, 9, 7, 9, 6, uci(42, "glass+identification"), "https://archive.ics.uci.edu/dataset/42/glass+identification"),
    DatasetSpec(6, "Ecoli", "ecoli", 336, 7, 8, 7, 8, uci(39, "ecoli"), "https://archive.ics.uci.edu/dataset/39/ecoli"),
    DatasetSpec(7, "Compound", "compound", 399, 2, 6, 2, 6, SIPU + "Compound.txt", SIPU),
    DatasetSpec(8, "Seed", "seed", 210, 7, 3, 7, 3, uci(236, "seeds"), "https://archive.ics.uci.edu/dataset/236/seeds"),
    DatasetSpec(9, "Breast Tissue", "breast_tissue", 106, 9, 6, 9, 6, uci(192, "breast+tissue"), "https://archive.ics.uci.edu/dataset/192/breast+tissue"),
    DatasetSpec(10, "Aggregation", "aggregation", 788, 2, 7, 2, 7, SIPU + "Aggregation.txt", SIPU),
    DatasetSpec(11, "Pima", "pima", 768, 8, 2, 8, 2, "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv", "https://github.com/jbrownlee/Datasets", "mirror"),
    DatasetSpec(12, "Room Occupancy", "room_occupancy", 20560, 7, 2, 5, 2, uci(357, "occupancy+detection"), "https://archive.ics.uci.edu/dataset/357/occupancy+detection"),
    DatasetSpec(13, "Rice", "rice", 3810, 7, 2, 7, 2, uci(545, "rice+cammeo+and+osmancik"), "https://archive.ics.uci.edu/dataset/545/rice+cammeo+and+osmancik"),
    DatasetSpec(14, "Wifi", "wifi", 2000, 7, 4, 7, 4, uci(422, "wireless+indoor+localization"), "https://archive.ics.uci.edu/dataset/422/wireless+indoor+localization"),
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".part")
    temporary.write_bytes(data)
    temporary.replace(path)


def save_json(path: Path, value: object) -> None:
    atomic_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def validate_payload(spec: DatasetSpec, data: bytes) -> None:
    if not data or data.lstrip().lower().startswith((b"<!doctype html", b"<html")):
        raise ValueError("Empty response or HTML instead of dataset")
    if spec.url.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            bad = archive.testzip()
            if bad:
                raise ValueError(f"Corrupt ZIP member: {bad}")
            if sum(member.file_size for member in archive.infolist()) > 50_000_000:
                raise ValueError("Unexpectedly large ZIP contents")


def fetch(spec: DatasetSpec, folder: Path, args: argparse.Namespace) -> tuple[bytes, dict]:
    filename = "source.zip" if spec.url.endswith(".zip") else "source.txt"
    path = folder / "raw" / filename
    record_path = folder / "raw" / "download.json"
    if path.exists() and not args.force:
        if not record_path.exists():
            raise ValueError(f"Cached source has no provenance record: {path}; rerun with --force")
        record = json.loads(record_path.read_text(encoding="utf-8"))
        data = path.read_bytes()
        if digest(data) != record.get("sha256") or record.get("requested_url") != spec.url:
            raise ValueError(f"Cached source hash/URL mismatch: {path}; rerun with --force")
        validate_payload(spec, data)
        return data, record
    if args.offline:
        raise FileNotFoundError(f"No cached source for {spec.name}; run online once first")
    last_error: Exception | None = None
    for attempt in range(args.retries):
        try:
            request = urllib.request.Request(spec.url, headers={"User-Agent": "DP-GA-PFCM-dataset-downloader/1.0"})
            with urllib.request.urlopen(request, timeout=args.timeout) as response:
                data = response.read(25_000_001)
                final_url = response.url
            if len(data) > 25_000_000:
                raise ValueError("Unexpected source size above 25 MB")
            validate_payload(spec, data)
            record = {
                "requested_url": spec.url, "resolved_url": final_url,
                "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
                "sha256": digest(data), "bytes": len(data), "source_type": spec.source_type,
            }
            atomic_bytes(path, data)
            save_json(record_path, record)
            return data, record
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            last_error = exc
            if isinstance(exc, urllib.error.HTTPError) and exc.code in (400, 401, 403, 404):
                break
            if attempt + 1 < args.retries:
                time.sleep(min(2 ** attempt, 4))
    raise RuntimeError(f"Download failed for {spec.name}: {last_error}")


def text(data: bytes) -> str:
    return data.decode("utf-8-sig").replace("\r\r\n", "\n")


def split_rows(data: bytes, comma: bool = False) -> list[list[str]]:
    lines = [line.strip() for line in text(data).splitlines() if line.strip()]
    return list(csv.reader(lines)) if comma else [line.split() for line in lines]


def read_member(archive: zipfile.ZipFile, member: str, folder: Path) -> bytes:
    # Only explicitly named members are read; never use extractall on remote ZIPs.
    data = archive.read(member)
    atomic_bytes(folder / "raw" / Path(member).name, data)
    return data


def parse(spec: DatasetSpec, data: bytes, folder: Path, iris_variant: str) -> tuple[list[str], list[list[float]], list[str], list[dict], list[str]]:
    auxiliary: list[dict] = []
    notes: list[str] = []
    members: list[str] = []
    slug = spec.slug
    archive = zipfile.ZipFile(io.BytesIO(data)) if spec.url.endswith(".zip") else None
    def member(name: str) -> bytes:
        if archive is None:
            raise ValueError("Expected ZIP archive")
        members.append(name)
        return read_member(archive, name, folder)
    try:
        if slug in ("flame", "jain", "compound", "aggregation"):
            rows = split_rows(data)
            features = ["x1", "x2"]
            raw_x, y = [r[:-1] for r in rows], [r[-1] for r in rows]
        elif slug == "iris":
            rows = split_rows(member(iris_variant), comma=True)
            features = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
            raw_x, y = [r[:-1] for r in rows], [r[-1] for r in rows]
            notes.append(f"Chosen Iris variant: {iris_variant}; the paper does not identify the variant. Both variants remain in source.zip.")
        elif slug == "wine":
            rows = split_rows(member("wine.data"), comma=True)
            features = ["alcohol", "malic_acid", "ash", "alcalinity_of_ash", "magnesium", "total_phenols", "flavanoids", "nonflavanoid_phenols", "proanthocyanins", "color_intensity", "hue", "od280_od315", "proline"]
            raw_x, y = [r[1:] for r in rows], [r[0] for r in rows]
        elif slug == "glass":
            rows = split_rows(member("glass.data"), comma=True)
            features = ["refractive_index", "Na", "Mg", "Al", "Si", "K", "Ca", "Ba", "Fe"]
            raw_x, y = [r[1:-1] for r in rows], [r[-1] for r in rows]
            auxiliary = [{"source_id": r[0]} for r in rows]
            notes.append("Table 1 sets k=7, but the source contains 6 observed classes (class 4 is absent). paper_k=7 and observed_classes=6 are kept separately.")
        elif slug == "ecoli":
            rows = split_rows(member("ecoli.data"))
            features = ["mcg", "gvh", "lip", "chg", "aac", "alm1", "alm2"]
            raw_x, y = [r[1:-1] for r in rows], [r[-1] for r in rows]
            auxiliary = [{"sequence_name": r[0]} for r in rows]
        elif slug == "seed":
            rows = split_rows(member("seeds_dataset.txt"))
            features = ["area", "perimeter", "compactness", "kernel_length", "kernel_width", "asymmetry", "groove_length"]
            raw_x, y = [r[:-1] for r in rows], [r[-1] for r in rows]
        elif slug == "breast_tissue":
            try:
                import xlrd
            except ImportError as exc:
                raise RuntimeError("Breast Tissue requires xlrd. Run: python -m pip install xlrd==2.0.2") from exc
            book = xlrd.open_workbook(file_contents=member("BreastTissue.xls"))
            sheet = book.sheet_by_name("Data")
            rows = [sheet.row_values(i) for i in range(1, sheet.nrows)]
            features = ["I0", "PA500", "HFS", "DA", "Area", "A_DA", "Max_IP", "DR", "P"]
            raw_x, y = [r[2:] for r in rows], [str(r[1]).strip() for r in rows]
            auxiliary = [{"case_id": int(r[0])} for r in rows]
            notes.append("Original six classes are preserved; fad/mas/gla are not merged into four classes.")
        elif slug == "pima":
            rows = split_rows(data, comma=True)
            features = ["pregnancies", "glucose", "blood_pressure", "skin_thickness", "insulin", "bmi", "diabetes_pedigree", "age"]
            raw_x, y = [r[:-1] for r in rows], [r[-1] for r in rows]
            notes.append("Uses a jbrownlee/Datasets mirror because the old UCI Pima URL returns 404. Zero values are preserved; no imputation or filtering is applied.")
        elif slug == "room_occupancy":
            features = ["Temperature", "Humidity", "Light", "CO2", "HumidityRatio"]
            raw_x, y = [], []
            for filename in ("datatraining.txt", "datatest.txt", "datatest2.txt"):
                reader = csv.reader(io.StringIO(text(member(filename))))
                header = next(reader)
                if header != ["date", *features, "Occupancy"]:
                    raise ValueError(f"Unexpected occupancy header: {header}")
                for row in reader:
                    if not row:
                        continue
                    if len(row) != 8:
                        raise ValueError(f"Expected ID,date,5 sensors,target in {filename}: {row}")
                    raw_x.append(row[2:7]); y.append(row[7])
                    auxiliary.append({"source_split": filename, "source_id": row[0], "date": row[1]})
            notes.append("All three original files are concatenated in training,test,test2 order to obtain 20560 rows. Original split/ID/date are saved in sample_info.csv.")
            notes.append("Table 1 reports F=7. This CSV uses only the 5 numeric sensor features; ID, date and target are excluded from X. The paper's exact seven-feature encoding is unknown.")
        elif slug == "rice":
            arff = text(member("Rice_Cammeo_Osmancik.arff"))
            attributes = []
            data_lines = []
            in_data = False
            for line in arff.splitlines():
                line = line.strip()
                if not line or line.startswith("%"):
                    continue
                if line.lower().startswith("@attribute"):
                    match = re.match(r"@attribute\s+(\S+)\s+", line, re.I)
                    if match is None:
                        raise ValueError("Unsupported ARFF attribute")
                    attributes.append(match.group(1).strip("\"'"))
                elif line.lower() == "@data":
                    in_data = True
                elif in_data:
                    data_lines.append(line)
            rows = list(csv.reader(data_lines, skipinitialspace=True))
            if len(attributes) != 8 or attributes[-1].lower() != "class":
                raise ValueError(f"Unexpected Rice schema: {attributes}")
            features = attributes[:-1]
            raw_x, y = [r[:-1] for r in rows], [r[-1] for r in rows]
        elif slug == "wifi":
            rows = split_rows(member("wifi_localization.txt"))
            features = [f"rssi_{i}" for i in range(1, 8)]
            raw_x, y = [r[:-1] for r in rows], [r[-1] for r in rows]
        else:
            raise ValueError(f"Unknown parser: {slug}")
        if any(len(row) != len(features) for row in raw_x):
            raise ValueError("Inconsistent feature width")
        x = [[float(value) for value in row] for row in raw_x]
        y = [str(value).strip() for value in y]
        if len(x) != spec.n or len(features) != spec.numeric_features or len(x) != len(y):
            raise ValueError(f"Shape mismatch: actual={len(x)}x{len(features)}, expected={spec.n}x{spec.numeric_features}")
        if not all(math.isfinite(v) for row in x for v in row) or any(not label for label in y):
            raise ValueError("Missing/nonfinite feature values or empty labels")
        if len(set(y)) != spec.observed_classes:
            raise ValueError(f"Class count mismatch: {len(set(y))} != {spec.observed_classes}")
        if auxiliary and len(auxiliary) != len(x):
            raise ValueError("Auxiliary metadata row count mismatch")
        return features, x, y, auxiliary, notes + ["Parsed member: " + name for name in members]
    finally:
        if archive is not None:
            archive.close()


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    atomic_bytes(path, stream.getvalue().encode("utf-8"))


def label_order(label: str) -> tuple[int, object]:
    try:
        return 0, int(label)
    except ValueError:
        return 1, label


def process(spec: DatasetSpec, root: Path, args: argparse.Namespace) -> dict:
    folder = root / spec.group / spec.slug
    data, source_record = fetch(spec, folder, args)
    features, x, labels, auxiliary, notes = parse(spec, data, folder, args.iris_variant)
    classes = sorted(set(labels), key=label_order)
    label_mapping = {value: i for i, value in enumerate(classes)}
    csv_path = folder / "data.csv"
    write_csv(csv_path, [*features, "label", "label_original"],
              [row + [label_mapping[label], label] for row, label in zip(x, labels)])
    if auxiliary:
        auxiliary_columns = list(auxiliary[0])
        write_csv(folder / "sample_info.csv", ["row_index", *auxiliary_columns],
                  [[i, *[row[key] for key in auxiliary_columns]] for i, row in enumerate(auxiliary)])
    record = {
        "status": "ok", "name": spec.name, "slug": spec.slug, "table1_order": spec.order,
        "group": spec.group, "grouping_reason": "User requested first 10 for main experiments and last 4 for separate evaluation; the paper uses all 14.",
        "n_samples": len(x), "n_features": len(features), "feature_columns": features,
        "label_column": "label", "original_label_column": "label_original",
        "label_mapping": label_mapping, "class_counts": dict(Counter(labels)),
        "observed_classes": len(classes), "paper_k": spec.paper_k,
        "paper_n": spec.n, "paper_features": spec.paper_features,
        "matches_paper_n": len(x) == spec.n, "matches_paper_features": len(features) == spec.paper_features,
        "matches_paper_k": len(classes) == spec.paper_k,
        "source_homepage": spec.homepage, "source": source_record,
        "data_path": csv_path.relative_to(root).as_posix(),
        "data_sha256": digest(csv_path.read_bytes()), "notes": notes,
        "preprocessing": "Numeric parsing only; no scaling, imputation, row deletion or shuffle. Labels/ID/date are not X features.",
    }
    save_json(folder / "metadata.json", record)
    return record


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "datasets")
    parser.add_argument("--group", choices=("all", "su_dung", "khong_su_dung"), default="all")
    parser.add_argument("--iris-variant", choices=("iris.data", "bezdekIris.data"), default="iris.data")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=45)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--force", action="store_true", help="Redownload sources and regenerate outputs")
    parser.add_argument("--offline", action="store_true", help="Only use previously verified cached sources")
    parser.add_argument("--list", action="store_true", help="List datasets without writing files or downloading")
    args = parser.parse_args(argv)
    if args.workers < 1 or args.retries < 1 or args.timeout <= 0:
        parser.error("workers/retries must be >=1 and timeout must be >0")
    if args.force and args.offline:
        parser.error("--force and --offline cannot be combined")
    specs = [spec for spec in SPECS if args.group == "all" or spec.group == args.group]
    if args.list:
        for spec in specs:
            print(f"{spec.order:2}. {spec.name:15} {spec.group:15} paper N/F/K={spec.n}/{spec.paper_features}/{spec.paper_k}")
        return 0
    if any(spec.slug == "breast_tissue" for spec in specs):
        try:
            import xlrd  # noqa: F401
        except ImportError:
            print("Missing xlrd. Install with: python -m pip install xlrd==2.0.2", file=sys.stderr)
            return 2
    root = args.output.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    results = {}
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        results = {record["slug"]: record for record in previous.get("datasets", [])}
    failed = 0
    with ThreadPoolExecutor(max_workers=min(args.workers, len(specs))) as executor:
        futures = {executor.submit(process, spec, root, args): spec for spec in specs}
        for future in as_completed(futures):
            spec = futures[future]
            try:
                record = future.result()
                print(f"[OK] {spec.name:15} {record['n_samples']:5} x {record['n_features']:2} | {spec.group}")
                for note in record["notes"]:
                    if not note.startswith("Parsed member:"):
                        print(f"     NOTE: {note}")
            except Exception as exc:
                failed += 1
                record = {"status": "failed", "slug": spec.slug, "name": spec.name,
                          "table1_order": spec.order, "group": spec.group, "error": str(exc)}
                print(f"[FAILED] {spec.name}: {exc}", file=sys.stderr)
            results[spec.slug] = record
    ordered = sorted(results.values(), key=lambda r: r["table1_order"])
    save_json(manifest_path, {
        "paper_doi": "10.1016/j.jestch.2023.101525", "expected_datasets": 14,
        "grouping": {"su_dung": [s.slug for s in SPECS[:10]], "khong_su_dung": [s.slug for s in SPECS[10:]]},
        "grouping_is_from_user_not_paper": True,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(), "datasets": ordered,
    })
    write_csv(root / "summary.csv",
              ["name", "group", "status", "n_samples", "n_features", "observed_classes", "paper_k", "paper_features", "matches_paper_features", "data_path"],
              [[r.get(key, "") for key in ("name", "group", "status", "n_samples", "n_features", "observed_classes", "paper_k", "paper_features", "matches_paper_features", "data_path")] for r in ordered])
    print(f"\nCompleted: {len(specs)-failed}/{len(specs)} selected datasets. Manifest: {manifest_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
