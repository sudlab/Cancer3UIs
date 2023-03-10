#############################################################################################
###                                                                                       ###
### The purpose of this script is to simulate stringtie merge of various sized assemblies ###
###     in doing so we can create a saturation plot to see if we picked everything up     ###
###                                                                                       ###
#############################################################################################

"""
How the script will work:
    - We will create a function to randomly group things together, based on "n"
        - where n is the number of gtfs to merge 
            - input from config.yml
        - we probably don't want to do every increment from 1 to max
    - We can also do this "z" times
        - where z is the number of simulations we do
        - probably 3?
            - input from config.yml
    - The script will create a directory structure where the input files are soft-linked (saves space)
    - This then allows us to use the pipelining software to run everything simulataneously
    - Via the pipeline we will:
        - merge gtfs with stringtie
        - run find_utrons.py on the merged_gtf
        - get summary stats on the output
            - mainly how many 3UIs per category we have detected
        - output this as a final table so we can plot with R

Prereqs:
    - simply soft-link all .gtf files from stringtie into a dir called "all_files.dir" 
"""

from ruffus import *
from ruffus.combinatorics import product
import sys
import os
import shutil
import sqlite3
import subprocess
import glob
from cgatcore import experiment as E
import cgat.Sra as Sra
import cgatcore.iotools as iotools
from cgatcore import pipeline as P
import tempfile
from os import listdir
from os.path import isfile, join
import random

PARAMS = P.get_parameters(
    ["%s/pipeline.yml" % os.path.splitext(__file__)[0],
     "../pipeline.yml",
     "pipeline.yml"])

PARAMS["project_src"]=os.path.dirname(__file__)

n_to_merge = PARAMS["intervals_list"]
num_simulations = PARAMS["num_simulations"]

def pick_random_files(n):
    all_files = [f for f in listdir("all_files.dir") if isfile(join("all_files.dir", f))]
    random_indexes = random.sample(range(0,len(all_files)),n)
    random_files = [all_files[i] for i in random_indexes]
    return random_files

def pick_random_groups(n_merge):
    groups = [pick_random_files(i) for i in n_merge]
    return groups

def pick_n_random_groups(n_sims):
    n_groups = [pick_random_groups(n_to_merge) for i in range(0,n_sims)]
    return n_groups

def create_file_structure():
    groups = pick_n_random_groups(num_simulations)
    intervals = n_to_merge
    n = 1
    for rep in groups:
        repname = "rep_" + str(n)
        if not os.path.exists("saturation/"+repname):
            os.makedirs("saturation/"+repname)
        n2 = 1
        for i in range(0,len(intervals)):
            files = rep[i]
            interval = intervals[i]
            if not os.path.exists("saturation/"+repname+"/n"+str(interval)):
                os.makedirs("saturation/"+repname+"/n"+str(interval))
            for eachfile in files:
                eachfile_path = os.path.realpath("all_files.dir/"+eachfile)
                os.system("ln -s " + eachfile_path + " " + "saturation/"+repname+"/n"+str(interval))
            print("## file structure built for interval " + str(n2) + "/" + str(len(intervals)) + " ##")
            n2+=1
        print("##### file structure built for simulation " + str(n) + "/" + str(len(groups)) + " #####")
        n+=1

create_file_structure()