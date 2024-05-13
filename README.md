# Cancer 3UIs paper code repository

This repository contains code used within the Cancer 3UIs paper (Ref when out). 

## Contents:
- Bioinformatic pipelines used in our analysis can be found in /pipelines.dir
- Scripts used to generate figures can be found within /scripts.dir
    - Here we have subsetted per figure
        - Fig1 - Characterizing our assembly
        - Fig2 - Splicing analysis and 3UI proportion of transcriptome analysis
        - Fig3 - CLIP-seq / Ago-CLIP enrichment analysis
        - Fig4 - HCT116 siUPF1 RNAseq analysis
        - Fig5 - HCT116 CHIR99021 treatment RNAseq analysis
        - Supplementary Figures
            - Further subsetted as above


## File/Data Structure

This repository is placed in the same directory as the folders containing each individual tisssue pipeline run, and the merged "all-TCGA" run. As follows:

```bash
└── TCGA_GTEx/
    ├── fastqc/
    ├── mapping/
    ├── clinical/
    └── utrons/
        ├── Cancer3UIs/
        │   ├── pipelines.dir/
        │   ├── scripts.dir/
        │   └── README.md <-- YOU ARE HERE!!!
        ├── colon_utrons/
        ├── lung_utrons/
        ├── etc...
        └── all_TCGA/
            └── quant/
                ├── colon/
                │   └── parquet/
                │       ├── rMATS_ri/
                │       │   └── Data compressed in .parquet format
                │       ├── utrons_expression/
                │       ├── pso/
                │       ├── rmats_junction_counts/
                │       ├── featurecounts/
                │       └── etc...
                ├── lung/
                └── etc...
```


## Run on your machine / cluster

Clone the project

```bash
  git clone https://github.com/sudlab/Cancer3UIs.git
```

Go to the project directory

```bash
  cd /path/to/where/you/cloned/it/Cancer3UIs
```

Install our conda environment

```bash
  conda create --name new_utrons_env --file new_utrons_env_spec_list.txt
```

Activate the conda environment

```bash
  source activate /path/to/where/you/cloned/it/Cancer3UIs/new_utrons_env
```

## The pipelines

`pipelines.dir` contains the code for the three pipelines neccessary to build the input datasets for the figure producing scripts. They are:

`pipeline_assemble` - pipeline assemble processes BAM files from TCGA to produce a GTF transcriptome annotation. This was run once per cancer type to produce a cancer type specific GTF. 

`pipeline_annotate` - This pipeline takes a set of GTF annotations, merges and filters them, and then creates a 3UI centric annotation - 3UI containing transcripts are called by reference to a filtered reference transcriptome. The 3UI calling script produces a series of Bed files:

 - `.all.bed.gz` - this file has one line per 3UI containing transcript. It is a bed12 annotating the positions of all 3UIs in a transcript.
 - `.indevidual.bed.gz` - this file has one line per 3UI. It is a bed6 annotating the positions of all 3UIs. Contains duplicate rows where the same 3UI appears in multiple transcripts. 
 - `.no_cds.bed.gz` - this file has one line per 3UI. It is a bed6 annotating the positions of 3UIs where neither the 5' or 3' splice site is used in the coding region of a known transcript.
 - `.novel.bed.gz` - this file has one line per 3UI. It is a bed6 annotating the positions of 3UIs that are novel compared to the reference sequence. 
 - `.partnered.bed.gz` - this file has one line per 3UI. It is a bed6 annotating the positions of 3UIs from transcripts that are identical to a reference coding transcript except for this 3UI.
     
All the bed files have corresponding `_ids` files, that list the ids of the transcripts in that category. Various aspects of the transcripts are then recorded including:
 - For novel transcripts, which is the closest known transcript structure
 - What is the distance between the stop codon and the 5' splice site of the 3UI
 - What is the 4bp splice-site sequence for each 3UI
     
The script also does comparisons of each of the input GTFs to the merge GTF so as to record which transcripts was present in which initial sample (as the names will have changed. 

`pipeline_requant` - this pipeline uses a selection of tools to perform quantitiation of BAM files using the merged GTF file that came from `pipeline_annotate`. The outputs from this pipeline are:

 - Transcript expression levels are measured using `salmon`. 
 - The fraction expression for each transcript in each sample is calculated by dviding the transcript TPM by the gene TPM after filtering for "annomous transcripts" that were identified by assembling simulated reads. 
 - Exon and junction counts are determined using featureCounts. 
 - Percent Spliced Out (PSO) is calculated using a custom script.  
 - rMATs is applied, with a custom event set that contains annotation for all 3UIs to compare cancer with non-cancer samples. The compatible and non-compatible counts as the indevidual sample percent spliced in (PSI)s for each sample are extracted from each sample. 
    
Output data is formatted as `parquet` database files. This pipeline was applied to each cancer type seperately. In general, we named input files `CANCERTYPE[-NO]-ID` where ID is a alphanumeric code going from `a1` to `zz9`. Samples are not connected to the original TCGA IDs to prevent deanonymisatoin.  

## Running a pipeline

All pipelines were built using the CGAT-core workflow system, which is install as part of our environment. see www.github.com/cgat-developers/cgat-core for details on how to configure for your cluster/HPC. 

Each pipeline requires a configuration file. A template for the configuration can be found at `pipelines.dir/pipeline_utrons/pipeline.yml`. You will need to point the configuration to your input filtered geneset and list of artefactual transcripts at the least. This must be placed in the same directory as you wish to run the pipeline in. Input data is then place in the appropriate input location. `.bam` or `.remote` in`input_assemble.dir` for the assembly pipeline; `.gtf.gz` files in `input_genesets.dur` for the annotation pipeline. `.bam` or `.remote` in `input_quantitation.dir` for the requant pipeline. 

pipelines are then run with:
```
python PATH/TO/PIPELINE.py make full
```

You can add `-p X` to the end to control how many tasks are launched simultaneously on your cluster. The log will appear in `pipeline.log` in the same directory. Run times are ~4 days per cancer type for assemble and requant, running 100 simulatenous tasks. `annotate` runs much quicker. 

