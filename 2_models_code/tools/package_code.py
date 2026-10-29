"""Package code, prepared datasets and actual results; exclude local runtime/raw cache."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1]
output=ROOT.parent/"output"/"code"/"DP_GA_PFCM_code.zip"
output.parent.mkdir(parents=True,exist_ok=True)
paths=[p for p in ROOT.rglob("*") if p.is_file() and not
       any(part in (".venv","__pycache__","raw") for part in p.relative_to(ROOT).parts)
       and p.suffix not in (".pyc",".pyo")]
with ZipFile(output,"w",compression=ZIP_DEFLATED,compresslevel=6) as z:
    for path in sorted(paths):
        z.write(path,"code/"+path.relative_to(ROOT).as_posix())
with ZipFile(output) as z:
    assert z.testzip() is None
    for name in ("code/ASSUMPTIONS.md","code/run_compare_all.py",
                 "code/purple_main_model/dp_ga_pfcm.py","code/datasets/su_dung/iris/data.csv",
                 "code/FILE_GROUPS.html"):
        assert name in z.namelist(),name
print(f"Packaged {len(paths)} files; {output.stat().st_size/1024/1024:.2f} MiB: {output}")
