#!/usr/bin/env bash

# Barcode crossover analysis workflow for multiplexed ONT sequencing runs.
# Usage:
#   ./align.sh
#
# Optional arguments:
#   -i  Input BAM directory
#   -o  Output directory
#   -t  Number of threads
#   -h  Show help

set -euo pipefail

# use location of script (with option for slurm)
WORK_DIR="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
source "${WORK_DIR}/config.sh"

# Argument parsing
while getopts "i:o:t:h" opt; do
  case $opt in
    i) READS_DIR="$OPTARG" ;;
    o) RESULTS_DIR="$OPTARG" ;;
    t) THREADS="$OPTARG" ;;
    h) grep '^#' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) echo "Unknown option: -$OPTARG" >&2; exit 1 ;;
  esac
done

# Log file setup
mkdir -p "${RESULTS_DIR}/logs"
LOGFILE="${RESULTS_DIR}/logs/renew_tech_challenge_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOGFILE") 2>&1

# Check for dorado installation and print version
command -v dorado >/dev/null 2>&1 || {
    echo "ERROR: dorado not found in PATH"
    exit 1
}

echo "Using $(dorado --version)"


# Create output directories
mkdir -p "${RESULTS_DIR}/alignments_all" "${RESULTS_DIR}/alignments_${PRIMARY_REF}_unmapped" "${RESULTS_DIR}/flagstat" "${RESULTS_DIR}/plots"

# List input files
echo "=== Process input files  ==="
bam_files=("${READS_DIR}"/*.bam)
REFS_ARRAY=($REFERENCE_GENOMES)
echo "input: ${#bam_files[@]} BAM(s), ${#REFS_ARRAY[@]} reference(s): ${REFS_ARRAY[*]}"

# Step 1: Align each BAM to each reference
echo "=== Step 1: Aligning with dorado ==="

for ref in "${REFS_ARRAY[@]}"; do
  ref_name=$(basename "$ref" | sed 's/\.[^.]*$//')
 
  for input_bam in "${bam_files[@]}"; do
    sample=$(basename "$input_bam" .bam)
    out_bam="${RESULTS_DIR}/alignments_all/${sample}_vs_${ref_name}.bam"
    flagstat_out="${RESULTS_DIR}/flagstat/${sample}_vs_${ref_name}.flagstat"

    if [[ ! -f "$out_bam" ]]; then
      echo "Aligning ${sample} to ${ref_name}" 
      TMP_DIR="${RESULTS_DIR}/alignments_all/.tmp_${sample}_vs_${ref_name}"
      rm -rf "$TMP_DIR" && mkdir -p "$TMP_DIR"
      
      # Align 
      dorado aligner --threads "$THREADS" \
          --output-dir "$TMP_DIR" \
          "$ref" \
          "$input_bam" \
          2>>"$LOGFILE"
  
      # Sort and index
      TMP_BAM=$(find "$TMP_DIR" -name "*.bam" | head -1) 
      samtools sort -@ "$THREADS" -o "$out_bam" "$TMP_BAM" 2>>"$LOGFILE"
      samtools index "$out_bam" 2>>"$LOGFILE"
      rm -rf "$TMP_DIR"
    fi

    # Flagstat alignment summary
    if [[ ! -f "$flagstat_out" ]]; then
      samtools flagstat <(samtools view -q "$MAPQ_FILTER" -b "$out_bam") > "$flagstat_out"
    fi
  done
done


# Step 2: Extract unmapped reads from D5405 and align to other references
echo "=== Step 2: Extracting unmapped reads from ${PRIMARY_REF} alignment ==="

for input_bam in "${bam_files[@]}"; do
  sample=$(basename "$input_bam" .bam)
  d5405_bam="${RESULTS_DIR}/alignments_all/${sample}_vs_${PRIMARY_REF}.bam"
  unmapped_bam="${RESULTS_DIR}/alignments_${PRIMARY_REF}_unmapped/${sample}_unmapped_${PRIMARY_REF}.bam"

  # Extract unmapped reads  
  if [[ ! -f "$unmapped_bam" ]]; then
    echo "Extracting unmapped reads: ${sample}"
    samtools view -@ "$THREADS" -f 4 -F 256 -F 2048 -b "$d5405_bam" \
      -o "$unmapped_bam" 2>>"$LOGFILE"
    samtools index "$unmapped_bam" 2>>"$LOGFILE"
  fi

  # Align unmapped reads to other reference genomes
  for ref in "${REFS_ARRAY[@]}"; do
    ref_name=$(basename "$ref" | sed 's/\.[^.]*$//')
    [[ "$ref_name" == "$PRIMARY_REF" ]] && continue
 
    rescue_bam="${RESULTS_DIR}/alignments_${PRIMARY_REF}_unmapped/${sample}_${PRIMARY_REF}_unmapped_vs_${ref_name}.bam"
    rescue_flagstat="${RESULTS_DIR}/flagstat/${sample}_${PRIMARY_REF}_unmapped_vs_${ref_name}.flagstat"
 
    if [[ ! -f "$rescue_bam" ]]; then
      echo "Aligning: ${sample} to ${PRIMARY_REF} unmapped reads vs ${ref_name}"
      TMP_DIR="${RESULTS_DIR}/alignments_${PRIMARY_REF}_unmapped/.tmp_${sample}_${PRIMARY_REF}_unmapped_vs_${ref_name}"
      rm -rf "$TMP_DIR" && mkdir -p "$TMP_DIR"

      # Align with dorado 
      dorado aligner \
        --threads "$THREADS" \
        --output-dir "$TMP_DIR" \
        "$ref" \
        "$unmapped_bam" \
        2>>"$LOGFILE"

      # Sort and index
      TMP_BAM=$(find "$TMP_DIR" -name "*.bam" | head -1)
      samtools sort -@ "$THREADS" -o "$rescue_bam" "$TMP_BAM" 2>>"$LOGFILE"
      samtools index "$rescue_bam" 2>>"$LOGFILE"
      rm -rf "$TMP_DIR"
    fi

    # Flagstat alignment summary
    if [[ ! -f "$rescue_flagstat" ]]; then
      samtools flagstat <(samtools view -q "$MAPQ_FILTER" -b "$rescue_bam") > "$rescue_flagstat"
    fi
  done
done

# Step 3: Quantify percent mapped
echo "=== Step 3: Quantifying alignment rates ==="

python3 "${WORK_DIR}/scripts/quantify_mapping.py" \
  --flagstat-dir "${RESULTS_DIR}/flagstat" \
  --output-dir   "${RESULTS_DIR}/flagstat" 

# Step 4: Output plots and summary tables
echo "=== Step 4: Generating plots ==="

python3 "${WORK_DIR}/scripts/plot_mapping.py" \
  --results-dir "${RESULTS_DIR}/flagstat" \
  --outdir      "${RESULTS_DIR}/plots" \
  --format      "${PLOT_FORMAT}" \
  --dpi         "${PLOT_DPI}" \
  --sample-labels "${SAMPLE_LABELS}"
 
echo "Done. Results in ${RESULTS_DIR}/"
