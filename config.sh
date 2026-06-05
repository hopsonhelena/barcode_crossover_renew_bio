# Edit this file to configure to your data.
#
# To run on new data:
# 	1. Put your unaligned BAM files in READS_DIR (or change READS_DIR to reflect your directory name)
# 	2. Put your reference FASTA files in references/ (or update REFERENCE_GENOMES)
#	3. Run: ./align.sh

## Input ##
# Directory containing input unaligned bam files
READS_DIR="${WORK_DIR}/data/unaligned_bams"

# Space-separated list of reference genome FASTA files to align against.
REFERENCE_GENOMES="${WORK_DIR}/ref_genomes/homo_sapiens.fa ${WORK_DIR}/ref_genomes/oryza_sativa.fa ${WORK_DIR}/ref_genomes/lambda.fa ${WORK_DIR}/ref_genomes/D5405.fa"

# Barcode reference  
PRIMARY_REF="D5405"

# Space-separated list of sample labels used for plotting. Update with new samples as needed. 
SAMPLE_LABELS="bc_zymo_3a_26-124-0051.subsampled_100000=Before bc_zymo_1b_26-124-0070.subsampled_100000=After"

## Output ##
# Output directory for all results
RESULTS_DIR="${WORK_DIR}/results"


## Performance ##
# Number of CPU threads for dorado and samtools
THREADS=4

# Quality filter for mapping
MAPQ_FILTER=10

## Plot Settings ##
# Output format for plots: png, pdf, svg
PLOT_FORMAT="png"

# Figure DPI 
PLOT_DPI=150
