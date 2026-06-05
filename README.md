# Renew Technical Challenge

## Overview

This repository contains a bash/Python workflow to quantify barcode crossover in multiplexed Oxford Nanopore sequencing runs.

Steps:

* Aligns ONT BAM files to multiple reference genomes using Dorado
* Summarizes mapping rates
* Extracts reads that do not map to the expected D5405 reference
* Realigns those reads to the remaining references
* Generates summary tables and figures

## Software Requirements

**Option 1 — pip:**
```bash
pip install -r requirements.txt
```
Install samtools separately:
- macOS: `brew install samtools`
- Linux: `sudo apt install samtools`

**Option 2 — conda (includes samtools):**
```bash
conda env create -f environment.yml
conda activate renew-tech-challenge
```

**Dorado (required for both options):**
Download from https://github.com/nanoporetech/dorado/releases and ensure it is on your PATH.

Versions: Python 3.11, samtools 1.16, and Dorado 1.3.0.


## Configuration

Customization options in `config.sh`:

* Input BAM directory (`READS_DIR`)
* Reference genome FASTA files (`REFERENCE_GENOMES`)
* Expected barcode reference (`PRIMARY_REF`)
* Sample labels used in plots (`SAMPLE_LABELS`)
* Number of CPU threads (`THREADS`)
* Minimum mapping quality (`MAPQ_FILTER`)
* Plot output format and DPI


## To Run

Clone the repository:

```bash
git clone https://github.com/hopsonhelena/barcode_crossover_renew_bio.git
cd barcode_crossover_renew_bio
```

## Input Files

Place unaligned BAM files in:

```text
data/unaligned_bams/
```

Place reference genome FASTA files in:

```text
ref_genomes/
```

Edit `config.sh` to set your input files and references.

Then run:

```bash
chmod +x align.sh
./align.sh
```

## Output

Results are written to:

```text
results/
├── alignments_all/              # Primary alignments of each sample to all reference genomes
├── alignments_D5405_unmapped/   # D5405-unmapped reads and alignments to non-D5405 references
├── flagstat/                    # samtools flagstat outputs and mapping rate summary tables
├── plots/                       # Summary figures and formatted result tables
└── logs/                        # Pipeline execution logs
```

Key output files include:

* `flagstat/mapping_rates_all_reads.csv`
* `flagstat/mapping_rates_unmapped_D5405.csv`
* Summary tables and figures in `plots/`

## Methodology

Reads assigned to the D5405 barcode were aligned independently to each reference genome using Dorado. Reads that failed to align to D5405 were extracted and realigned to the remaining references to identify potential barcode crossover events.

## Results

See `RESULTS.md` for analysis, figures, and interpretation.

