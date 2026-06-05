#!/usr/bin/env python3
import argparse
import re
from pathlib import Path
import pandas as pd


def parse_flagstat(path):
    lines = path.read_text()
    total  = int(re.search(r"(\d+) \+ \d+ primary\n", lines).group(1))
    mapped = int(re.search(r"(\d+) \+ \d+ primary mapped", lines).group(1))
    pct    = round(mapped / total * 100, 4) if total else 0.0
    return total, mapped, pct
 
 
parser = argparse.ArgumentParser()
parser.add_argument("--flagstat-dir", required=True, type=Path)
parser.add_argument("--output-dir",   required=True, type=Path)
parser.add_argument("--primary-ref", default="D5405")
args = parser.parse_args()
 
files = sorted(args.flagstat_dir.glob("*.flagstat"))
 
all_reads, unmapped_rescue = [], []
 
for fpath in files:
    sample, reference = fpath.stem.split("_vs_", 1) if "_vs_" in fpath.stem else (fpath.stem, "unknown")
    total, mapped, pct = parse_flagstat(fpath)
    row = {"sample": sample, "reference": reference,
           "total_reads": total, "mapped_reads": mapped, "percent_mapped": pct}
    if f"_{args.primary_ref}_unmapped" in sample:
        unmapped_rescue.append(row)
    else:
        all_reads.append(row)
    print(f"  {sample} vs {reference}: {mapped:,}/{total:,} mapped ({pct:.2f}%)")
 
args.output_dir.mkdir(parents=True, exist_ok=True)
 
all_reads_csv    = args.output_dir / "mapping_rates_all_reads.csv"
unmapped_csv = args.output_dir / f"mapping_rates_unmapped_{args.primary_ref}.csv"
 
pd.DataFrame(all_reads).to_csv(all_reads_csv, index=False)
pd.DataFrame(unmapped_rescue).to_csv(unmapped_csv, index=False)
 
print(f"\nWrote {len(all_reads)} rows to: {all_reads_csv}")
print(f"Wrote {len(unmapped_rescue)} rows to: {unmapped_csv}")
