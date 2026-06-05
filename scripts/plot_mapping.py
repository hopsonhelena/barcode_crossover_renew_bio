#!/usr/bin/env python3
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

# Generate summary tables and plots  
 
parser = argparse.ArgumentParser()
parser.add_argument("--results-dir", required=True, type=Path)
parser.add_argument("--outdir",      required=True, type=Path)
parser.add_argument("--format", dest="fmt", default="png", choices=["png", "pdf", "svg"])
parser.add_argument("--dpi",    type=int, default=150)
parser.add_argument("--sample-labels", default="")
args = parser.parse_args()
 
SAMPLE_LABELS = dict(pair.split("=") for pair in args.sample_labels.split() if "=" in pair)
 
args.outdir.mkdir(parents=True, exist_ok=True)
 
df_all = pd.read_csv(args.results_dir / "mapping_rates_all_reads.csv")
df_rescue = pd.read_csv(args.results_dir / "mapping_rates_unmapped_D5405.csv")

df_all["sample"] = df_all["sample"].map(lambda s: SAMPLE_LABELS.get(s, s))
df_rescue["sample"] = df_rescue["sample"].map(
    lambda s: SAMPLE_LABELS.get(s.replace("_D5405_unmapped", ""), s)
)

TABLE_BBOX = [0.01, 0.08, 0.98, 0.80]
HEADER_COLOR = "#2c6e49"
 
 
# Table 1: Cross-species alignment rate
sample_order = df_all["sample"].drop_duplicates().tolist()
if "Before" in sample_order and "After" in sample_order:
    sample_order = ["Before", "After"] + [x for x in sample_order if x not in {"Before", "After"}]

ref_order = list(df_all["reference"].drop_duplicates())

t1_n = df_all.pivot(index="sample", columns="reference", values="mapped_reads").reindex(index=sample_order, columns=ref_order)
t1_p = df_all.pivot(index="sample", columns="reference", values="percent_mapped").reindex(index=sample_order, columns=ref_order)

t1_n = t1_n.applymap(lambda x: f"{int(x):,}" if pd.notna(x) else "")
t1_p = t1_p.applymap(lambda x: f"{x:.2f}%" if pd.notna(x) else "")

t1_parts = []
for ref in ref_order:
    t1_parts.append(t1_n[[ref]].rename(columns={ref: f"{ref} (n)"}))
    t1_parts.append(t1_p[[ref]].rename(columns={ref: f"{ref} (%)"}))

t1 = pd.concat(t1_parts, axis=1).reset_index().rename(columns={"sample": "Sample"})

fig, ax = plt.subplots(figsize=(max(12, len(t1.columns) * 1.5), 2.8))
ax.axis("off")

tbl = ax.table(
    cellText=t1.values,
    colLabels=t1.columns,
    cellLoc="center",
    colLoc="center",
    loc="center",
    bbox=TABLE_BBOX,
)

tbl.auto_set_font_size(False)
tbl.set_fontsize(10)
tbl.scale(1, 1.25)

for j in range(len(t1.columns)):
    tbl[(0, j)].set_facecolor(HEADER_COLOR)
    tbl[(0, j)].set_text_props(color="white", fontweight="bold")

ax.set_title("Table 1: Alignment Rate by Reference", fontsize=14, fontweight="bold", pad=8)
fig.tight_layout()
fig.savefig(args.outdir / f"table1_all_reads.{args.fmt}", dpi=args.dpi, bbox_inches="tight", pad_inches=0.1)
plt.close(fig)
 
# Table 2: Rescue alignment
sample_order = df_rescue["sample"].drop_duplicates().tolist()
if "Before" in sample_order and "After" in sample_order:
    sample_order = ["Before", "After"] + [x for x in sample_order if x not in {"Before", "After"}]

ref_order = list(df_rescue["reference"].drop_duplicates())

t2_total = (
    df_rescue[["sample", "total_reads"]]
    .drop_duplicates()
    .rename(columns={"sample": "Sample", "total_reads": "Total D5405\nunmapped (n)"})
)
t2_total["Total D5405\nunmapped (n)"] = t2_total["Total D5405\nunmapped (n)"].map(lambda x: f"{int(x):,}")
t2_total = t2_total.set_index("Sample").reindex(sample_order).reset_index()

t2_n = df_rescue.pivot(index="sample", columns="reference", values="mapped_reads").reindex(index=sample_order, columns=ref_order)
t2_p = df_rescue.pivot(index="sample", columns="reference", values="percent_mapped").reindex(index=sample_order, columns=ref_order)

t2_n = t2_n.applymap(lambda x: f"{int(x):,}" if pd.notna(x) else "")
t2_p = t2_p.applymap(lambda x: f"{x:.2f}%" if pd.notna(x) else "")

t2_parts = []
for ref in ref_order:
    t2_parts.append(t2_n[[ref]].rename(columns={ref: f"{ref} (n)"}))
    t2_parts.append(t2_p[[ref]].rename(columns={ref: f"{ref} (%)"}))

t2 = pd.concat(t2_parts, axis=1).reset_index().rename(columns={"sample": "Sample"})
t2 = t2_total.merge(t2, on="Sample", how="left")

fig, ax = plt.subplots(figsize=(max(12, len(t2.columns) * 1.5), 2.8))
ax.axis("off")

tbl = ax.table(
    cellText=t2.values,
    colLabels=t2.columns,
    cellLoc="center",
    colLoc="center",
    loc="center",
    bbox=TABLE_BBOX,
)

tbl.auto_set_font_size(False)
tbl.set_fontsize(10)
tbl.scale(1, 1.25)

for j in range(len(t2.columns)):
    tbl[(0, j)].set_facecolor(HEADER_COLOR)
    tbl[(0, j)].set_text_props(color="white", fontweight="bold")

ax.set_title("Table 2: Alignment of D5405 Unmapped Reads", fontsize=14, fontweight="bold", pad=8)
fig.tight_layout()
fig.savefig(args.outdir / f"table2_unmapped_d5405.{args.fmt}", dpi=args.dpi, bbox_inches="tight", pad_inches=0.1)
plt.close(fig) 
 
# Plot: Rescue mapping rate by reference
pivot = df_rescue.pivot(index="reference", columns="sample", values="percent_mapped")
fig, ax = plt.subplots(figsize=(max(7, len(pivot) * 2), 5))

colors = plt.get_cmap("Set2").colors
pivot.plot(
    kind="bar",
    ax=ax,
    color=colors[: len(pivot.columns)],
    edgecolor="white",
    width=0.7,
)

ax.set_xlabel("Reference")
ax.set_ylabel("% D5405-Unmapped Reads Mapped")
ax.set_title("Alignment of D5405-Unmapped Reads")
ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right")
ax.legend(title="Sample", bbox_to_anchor=(1.01, 1), loc="upper left")
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f%%"))
ax.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig(args.outdir / f"plot_rescue.{args.fmt}", dpi=args.dpi, bbox_inches="tight", pad_inches=0.1)
plt.close(fig)
