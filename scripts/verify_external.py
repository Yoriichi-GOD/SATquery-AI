"""Recompute export hashes and, when scorable, metrics. No models or dashboard needed."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from paired_lab.external_data.runner import verify


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('run',type=Path)
    args=parser.parse_args();print(json.dumps(verify(args.run),indent=2))


if __name__=='__main__':main()
