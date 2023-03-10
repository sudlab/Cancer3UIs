'''
csvs2parquet.py - 
====================================================

:Author:
:Tags: Python

Purpose
-------

This script takes a tsv (or csv) file, or files, and converts it into 
a parquet file or collection of parquet files with the same schema.

Like cgat combine_tables --cat, columns are added to the table. By default
the filename is used, but a pattern can also be specified, using capture
groups. 

Data will be written out as a partitioned dataset, particianed on cat 
columns. 

The dataset will be written to the current directory unless another directory
is specified with output-prefix

Usage
-----

.. Example use case

Example::

   python csvs2parquet.py *.tsv.gz --regex-filename='(.+).tsv.gz' --output-prefix=outdir.dir/

Type::

   python csvs2parquet.py --help

for command line help.

Command line options
--------------------

'''

#pass in utrons bed on st_in
#also give bam file as the arg


import sys
import cgatcore.experiment as E
from cgatcore import iotools
import dask.dataframe as dd
import re

def main(argv=None):
    """script main.
    parses command line options in sys.argv, unless *argv* is given.
    """

    if argv is None:
        argv = sys.argv

    # setup command line parser
    parser = E.OptionParser(version="%prog version: $Id$",
                            usage=globals()["__doc__"])
    parser.add_option("--regex-filename", dest="regex_filename",
                      help="pattern to apply to filename to build key columns"
                           "each capture group will become a column")
    parser.add_option("-k", "--key-columns", dest = "key_columns",
                      default="track",
                      help="names to use for colums which record the file of"
                           "origin")
    parser.add_option("-p", dest="partition", action="store_true",
                      help="parition dataset. By default partioning will be by the"
                           "cat columns")
    parser.add_option("--partition-on", dest="partition_on",
                     help="Columns to partition output parquet files on."
                          "by default the columsn in key-colums")
    parser.add_option("-P", "--output-prefix", dest="output_prefix",
                      default=".")
    parser.add_option("-s", "--sep", dest="sep",
                      default="\t",
                      help=r"Column seperater. Default = \t")
    parser.add_option("--no-header", dest="header", action="store_false",
                      help="files have no header")
    parser.add_option("--col-names", dest="col_names", 
                      help="Comma seperated list of names to use for columns")
    parser.add_option("-i", "--index", dest="index",
                      help="Set index to this column. Will be recorded in the"
                           "specail pandas index column")
    options, args = E.start(parser, unknowns=True)
    
    n = 0
    
    if options.partition and options.partition_on is None:
        options.partition_on = options.key_columns

    for infile in args:
        
        if options.regex_filename:
            keys = re.match(options.regex_filename, infile).groups()
        else:
            keys = [infile]
            
        if options.col_names is not None and options.header:
            ddf = dd.read_csv(infile, sep=options.sep, header=0, names=options.col_names.split(","))
        elif options.col_names is not None and options.header is False:
            ddf = dd.read_csv(infile, sep=options.sep, header=None, names=options.col_names.split(","))
        else:
            ddf = dd.read_csv(infile, sep=options.sep)
            
        if options.index:
            ddf = ddf.set_index(options.index)
            
        keys = dict(zip([options.key_columns], keys))

        ddf_with_keys = ddf.assign(**keys)
        ddf_with_keys.to_parquet(options.output_prefix,
                                 append=True if n> 0 else False,
                                 partition_on=options.partition_on,
                                 write_index=False,
                                 write_metadata_file=True,
                                 compute=True)
        n += 1
        
        
    

if __name__ == "__main__":
    sys.exit(main(sys.argv))
