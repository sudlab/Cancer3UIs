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
