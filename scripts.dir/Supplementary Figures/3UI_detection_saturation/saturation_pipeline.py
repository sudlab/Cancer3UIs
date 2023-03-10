"""
This pipeline will deal with merging our gtfs and then identifying 3UIs.

In order to run this pipeline the saturation dir structure must first have been randomly assigned
by running 'build_file_structure.py' in the directory. This requires all the gtfs to be used in 
the saturation to be within (or soft linked to within) a file called "all_files.dir" in the cwd.
"""

# Generic pipeline imports

from ruffus import *
from ruffus.combinatorics import product
import sys
import os
import re
import pandas as pd
import shutil
import sqlite3
import subprocess
import glob
from cgatcore import experiment as E
import cgat.Sra as Sra
from cgatcore import pipeline as P
import cgatpipelines.tasks.rnaseq as RnaSeq
import tempfile
import cgatcore.iotools as iotools 

# load options from the config file
PARAMS = P.get_parameters(
    ["%s/pipeline.yml" % os.path.splitext(__file__)[0],
     "../pipeline.yml",
     "pipeline.yml"])


# Pipeline

###############################
### Merge - STRGs to MSTRGs ###
###############################

@collate("saturation/*/*/*.gtf.gz",
       regex("saturation/(.+)/(.+)/.+.gtf.gz"),
       r"saturation/\1/\2/merged/\1.\2.merged.gtf.gz")
def merge_gtfs(infiles, outfile):
    infiles = ["<(zcat %s)" % infile for infile in infiles]
    infiles = " ".join(infiles)
    reference = os.path.join(PARAMS["annotations_dir"], PARAMS["annotations_interface_geneset_all_gtf"])

    job_threads = PARAMS["stringtie_merge_threads"]
    job_memory = PARAMS["stringtie_merge_memory"]

    statement = '''stringtie --merge
                             -G <(zcat %(reference)s)
                             -p %(stringtie_merge_threads)s
                             %(stringtie_merge_options)s
                             %(infiles)s
                            2> %(outfile)s.log
                   | cgat gtf2gtf --method=sort
                           --sort-order=gene+transcript
                            -S %(outfile)s -L %(outfile)s.log'''

    P.run(statement) 

##########################################
### Produce class file from merged gtf ###
##########################################

@transform(merge_gtfs,
           suffix(".gtf.gz"),
           ".class.gz")
def classifyTranscripts(infile, outfile):
    to_cluster = True

    reference = os.path.join(PARAMS["annotations_dir"], PARAMS["annotations_interface_geneset_all_gtf"])

    counter = PARAMS['gtf2table_classifier']

    job_memory = "16G"

    statement = '''
    zcat %(infile)s
    | cgat gtf2table
           --counter=%(counter)s
           --reporter=transcripts
           --gff-file=%(reference)s
           --log=%(outfile)s.log
    | gzip
    > %(outfile)s
    '''
    P.run(statement)

############################################################
### filter class by APRIS L1 and L2 protein coding genes ###
############################################################

@transform(classifyTranscripts,
           suffix(".class.gz"),
           ".filtered.class.gz")
def filterAggClasses(infile, outfile):    
    classes_to_remove = ["intergenic",
                         "complete",
                         "flank3",
                         "flank5",
                         "fragment",
                         "intronic",
                         "utr3", 
                         "utr5"]
    
    outf = iotools.open_file(outfile, "w")
    
    for line in iotools.open_file(infile):
        fields = line.split("\t")
        if fields[0].startswith("MSTR") and fields[6] in classes_to_remove:
            continue
        outf.write(line)
        
    outf.close()
    
###########################################
### filter merged gtf by filtered.class ###
###########################################

@follows(filterAggClasses)
@transform(merge_gtfs,
           regex("(.+)/(.+).gtf.gz"),
           add_inputs(r"\1/\2.filtered.class.gz"),
           r"\1/\2.filtered.gtf.gz")
def filterGTFs(infiles, outfile):
    gtf_file, class_file = infiles
    statement = '''cgat gtf2gtf --method=filter
                                --filter-method=transcript
                                --map-tsv-file=<(zcat %(class_file)s | cut -f1)
                                -I %(gtf_file)s
                                -S %(outfile)s
                                -L %(outfile)s.log'''
    P.run(statement)
 
################################################################
### run find_utrons.py to detect the various classes of 3UIs ###
################################################################
    
@subdivide(filterGTFs,
           regex("(.+)/(.+).filtered.gtf.gz"),
           add_inputs(PARAMS["annotations_filtered_reference_gtf"],
                      r"\1/\2.filtered.class.gz"),
           [r"\1/utron_beds.dir/\2.all_utrons.bed.gz",
            r"\1/utron_beds.dir/\2.indevidual_utrons.bed.gz",
            r"\1/utron_beds.dir/\2.partnered_utrons.bed.gz",
            r"\1/utron_beds.dir/\2.novel_utrons.bed.gz",
            r"\1/utron_beds.dir/\2.no_cds_utrons.bed.gz"])
def find_utrons(infiles, outfiles):

    infile, reference, classfile = infiles
    job_memory="48G"

    all_out, all_bed6_out, part_out, novel_out, no_cds_out = outfiles

    track = P.snip(all_out, ".all_utrons.bed.gz")
    current_file = __file__ 
    full_utron_path = "/shared/sudlab1/General/projects/stem_utrons/pipelines/pipeline_utrons/pipeline_utrons/find_utrons.py"
    statement = '''cgat gtf2gtf -I %(infile)s
                             --method=sort
                             --sort-order=gene+transcript
                              -L %(track)s.log
                 | python %(full_utron_path)s 
                             --reffile=%(reference)s
                             --class-file=%(classfile)s
                             --outfile %(all_out)s
                             --indivfile %(all_bed6_out)s
                             --partfile=%(part_out)s
                             --novel-file=%(novel_out)s
                             --not-cds-outfile=%(no_cds_out)s
                              -L %(track)s.log'''

    P.run(statement)

#############################################################################
### create a summary table with number of 3UIs for each class in each sim ###
#############################################################################

@follows(mkdir("saturation/output"))
@collate(find_utrons,
       regex("saturation/(.+)/.+/merged/utron_beds.dir/.+.all_utrons.bed.gz"),
       r"saturation/output/\1.summary.tsv")
def summarize_per_simulation(infiles, outfile):
    
    output_df = pd.DataFrame(columns=['n', 'events'])
    for infile in infiles:
        #for each file, split its name to get the "nX" value, then strip the n and force to be an int
        n = int(re.split("/", infile)[2][1:])
        #query the OS to give us the number of unique events detected. $1 = chr, $2$3 = pos, $6 = strand
        value = os.popen("zcat " + infile + " | awk {'print $1$2$3$6'} | uniq -u | wc -l").read().strip()
        #add these to the output dataframe
        new_row = {"n":n, "events":value}
        output_df = output_df.append(new_row, ignore_index=True)
    output_df.to_csv(outfile, sep="\t", index=False)

#####################################################
### create a summary table for total pipeline run ###
#####################################################

@follows(mkdir("saturation/output/all"))
@merge(summarize_per_simulation, "saturation/output/all/all.summary.tsv")
def summarize_experiment(infiles, outfile):

    output_df = pd.DataFrame(columns=['n', 'events', "rep"])
    for infile in infiles:
        #for each infile, split by / to get the file name, then split by . to get the rep number
        rep_n = int(re.split("\.", (re.split("/", infile)[2]))[0][4:])
        df = pd.read_csv(infile, sep="\t")
        df["rep"] = rep_n
        output_df = output_df.append(df, ignore_index=True)
    output_df.to_csv(outfile, sep="\t", index=False)

@follows(merge_gtfs, classifyTranscripts, filterAggClasses, filterGTFs, find_utrons, summarize_per_simulation, summarize_experiment)
def full():
    pass


def main(argv=None):
    if argv is None:
        argv = sys.argv
    P.main(argv)


if __name__ == "__main__":
    sys.exit(P.main(sys.argv))