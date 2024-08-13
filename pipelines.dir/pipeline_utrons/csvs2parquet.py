'''
csvs2parquet.py - 
====================================================

:Author:
:Tags: Python

Purpose
-------

This script takes a tsv (or csv) file, or files, and converts it into 
a parquet file or collection of parquet files with the same schema.

Like cgat combine_tables --cat, columns can be added to the table to denote
origin. By default the filename is used, but a pattern can also be specified,
using capture groups. 

Data can also  be written out as a partitioned dataset, particianed on cat 
columns by default, or on other columsn. 

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


import sys
import os
import cgatcore.experiment as E
from cgatcore import iotools
import dask.dataframe as dd
import re
import pyarrow as pa
import numpy as np

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
                      default=True,
                      help="files have no header")
    parser.add_option("--col-names", dest="col_names", 
                      help="Comma seperated list of names to use for columns")
    parser.add_option("--dtypes", dest="dtypes",
                      help="If dtype guessing fails, use this to explicitly set them"
                      " by providing a comma seperated list of column=dtype pairs")
    options, args = E.start(parser, unknowns=True)
    
    n = 0
    
    E.debug("options.col_names is %s" % options.col_names)
    E.debug("options.header is %s" % options.header)
    
    if options.partition and options.partition_on is None:
        options.partition_on = options.key_columns

    if options.dtypes is not None:
        dtypes = {entry.split("=")[0]: entry.split("=")[1] for entry in options.dtypes.split(",")}
    else:
        dtypes = None
    
    if options.key_columns:
        options.key_columns = options.key_columns.split(",")
        track_col = options.key_columns[0]
    elif options.regex_filename:
        options.key_columns = ["track"]
        track_col = "track"
    else:
        track_col = False

    if options.regex_filename:
        regex = re.compile(options.regex_filename)

        if not regex.groups == len(options.key_columns):
            E.error("Different number of groups in key_columns to capture"
                    "groups in regex\n"
                    "Key Columns = %s\n"
                    "Regex = %s" % (",".join(options.key_columns),
                                    options.regex_filename))
            sys.exit(1)

    if options.col_names is not None and options.header is True:
        E.debug("Replacing header")
        ddf = dd.read_csv(args, sep=options.sep, 
                          header=0, 
                          names=options.col_names.split(","), 
                          dtype=dtypes, assume_missing=True,
                          comment="#",
                          include_path_column=track_col)
    elif options.col_names is not None and options.header is False:
        E.debug("File contains no header, using provided headers")
        ddf = dd.read_csv(args, 
                          sep=options.sep, 
                          header=None, 
                          names=options.col_names.split(","), 
                          dtype=dtypes,
                          assume_missing=True,
                          comment="#",
                          include_path_column=track_col)
    else:
        E.debug("Using first line as header")
        ddf = dd.read_csv(args, sep=options.sep, dtype=dtypes, assume_missing=True,
                          comment="#",
                          include_path_column=track_col)
    
    if options.regex_filename:
        key_cols = ddf[track_col].str.extract(options.regex_filename, expand=True)
        key_cols.columns = options.key_columns
        ddf = dd.concat([ddf.drop(track_col, axis=1), key_cols],
                        axis=1)
                        
    ddf.to_parquet(options.output_prefix,
                   partition_on=options.partition_on,
                   engine="pyarrow",
                   write_index=False,
                   write_metadata_file=True,
                   compute=True)
    E.stop()
    
        
        
    

if __name__ == "__main__":
    sys.exit(main(sys.argv))
