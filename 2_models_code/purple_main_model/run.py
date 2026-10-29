"""PURPLE | Run the main model alone; use run_compare_all.py for comparisons."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from result_portal import run_stage
if __name__=="__main__":
    raise SystemExit(run_stage("main"))
