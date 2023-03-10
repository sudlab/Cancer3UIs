'''
get_psi.py - 
====================================================

:Author:
:Tags: Python

Purpose
-------

.. Overall purpose and function of the script>

Usage
-----

.. Example use case

Example::

   python cgat_script_template.py

Type::

   python cgat_script_template.py --help

for command line help.

Command line options
--------------------

'''

#pass in utrons bed on st_in
#also give bam file as the arg


import sys
import cgatcore.experiment as E
from cgatcore import iotools
from cgat import Bed
import pysam

def main(argv=None):
    """script main.
    parses command line options in sys.argv, unless *argv* is given.
    """

    if argv is None:
        argv = sys.argv

    # setup command line parser
    parser = E.OptionParser(version="%prog version: $Id$",
                            usage=globals()["__doc__"])

    

    # add common options (-h/--help, ...) and parse command line
    (options, args) = E.start(parser, argv=argv)

    bam = pysam.AlignmentFile(args[0])

    outlines = list()
    
    for junction in Bed.iterator(options.stdin):
        for utron_start, utron_end in junction.toIntervals():
            reads = bam.fetch(junction.contig,
                              utron_start - 1,
                              utron_end + 1)
            retained_reads = 0
            spliced_reads = 0
            incompatible = 0
        
            reads = list(reads)
            total = len(reads)
        
            if len(reads) == 0:
                continue
        
            for read in reads:

                if read.get_tag("NH") > 1:
                    continue
            
                if read.is_unmapped:
                    continue
            
                found = False
            
                try:
                    if 'N' not in read.cigarstring and \
                    read.pos < utron_start and \
                    read.aend > utron_start:
                     found = True
                     retained_reads += 1
                     continue
                except TypeError:
                    E.error(print(read.to_string()))
                    raise 
            
                segments = read.get_blocks()

                for i in range(len(segments) - 1):

                    if segments[i][0] < utron_start and\
                       segments[i][1] > utron_start:
                        found = True
                        retained_reads += 1
                    elif abs(segments[i][1] - utron_start) < 3 and\
                         abs(segments[i+1][0]  - utron_end) < 3:
                        found = True
                        spliced_reads += 1

                if not found and \
                   segments[-1][0] < utron_start and \
                   segments[-1][1] > utron_start:
                    retained_reads += 1
                else:
                    incompatible += 1
                

            if spliced_reads + retained_reads > 0:
                psi = retained_reads/float(spliced_reads + retained_reads)
            else:
                psi = "NA"
            
            options.stdout.write("\t".join(map(str, [junction.contig,
                                                 utron_start,
                                                 utron_end,
                                                 junction.name,
                                                 retained_reads,
                                                 spliced_reads,
                                                 incompatible,
                                                 total,
                                                 psi])) +
                             "\n")
     
    # write footer and output benchmark information.
    E.stop()

if __name__ == "__main__":
    sys.exit(main(sys.argv))
