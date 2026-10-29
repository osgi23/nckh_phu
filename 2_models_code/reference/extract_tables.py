"""Extract literal Tables 6-8,11-13. Preserve suspicious values, never fix silently."""
import csv
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parent/"tmp"/"pdfs"/"paper-extracted.txt"
NAMES={"Iris":"iris","Flame":"flame","Jain":"jain","Wine":"wine","Glass":"glass",
"Ecoli":"ecoli","Seed":"seed","Aggregation":"aggregation","Compound":"compound",
"Breast Tissue":"breast_tissue","Pima":"pima","Room Occupancy":"room_occupancy","Rice":"rice","Wifi":"wifi"}
STAGE1=["K-means","FCM","PFCM","DP-FCM","DP-PFCM"]
STAGE2=["DP-PFCM","DP-GA-PFCM","DP-PSO-PFCM","DP-SCA-PFCM","DP-FBI-PFCM","GA-IFWCOM","SCA-FPCOM"]
rows=[]
text=SOURCE.read_text(encoding="utf-8")
for table,metric in [(6,"accuracy_purity"),(7,"ari"),(8,"nmi"),(11,"accuracy_purity"),(12,"ari"),(13,"nmi")]:
    stage=1 if table<=8 else 2
    methods=STAGE1 if stage==1 else STAGE2
    start=re.search(r"Table "+str(table)+r"\s*\n(?:First|Second)-stage",text)
    if start is None:
        raise ValueError(f"Table {table} not found")
    chunk=text[start.end():].split("Sum of Rank",1)[0]
    for name,slug in NAMES.items():
        match=re.search(r"^"+re.escape(name)+r"\s+([^\n]+)",chunk,re.MULTILINE)
        if match is None:
            raise ValueError(f"Table {table}: {name} missing")
        line=match[1]
        if stage==1:
            tokens=re.findall(r"[0-9]+(?:\.[0-9]+)?",line)
            if len(tokens)!=10:
                raise ValueError(f"Malformed row {table}/{name}: {line!r}")
            pairs=zip(tokens[:5],tokens[5:])
        else:
            pairs=re.findall(r"([0-9]+(?:\.[0-9]+)?)\s*\(([0-9]+)\)",line)
            if len(pairs)!=7:
                raise ValueError(f"Malformed row {table}/{name}: {line!r}")
        for method,(mean,rank) in zip(methods,pairs):
            note="Published mean only; no raw repeat runs."
            if table==11 and slug=="glass" and method=="DP-PFCM":
                note+=" Suspicious 0.066 retained literally; Table 6 reports 0.566."
            rows.append({"stage":stage,"table":table,"dataset":slug,"method":method,
                         "metric":metric,"mean":mean,"rank_reported":rank,"note":note})
output=ROOT/"reference"/"paper_metrics.csv"
with output.open("w",encoding="utf-8-sig",newline="") as stream:
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
assert len(rows)==14*(5+7)*3
print(f"Extracted {len(rows)} literal mean/rank cells.")
