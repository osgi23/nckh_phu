"""ORANGE | Run Stage 2 comparisons. Missing A6/A7 are explicitly reported."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from result_portal import run_stage
if __name__=="__main__":
    raise SystemExit(run_stage("comparisons"))
