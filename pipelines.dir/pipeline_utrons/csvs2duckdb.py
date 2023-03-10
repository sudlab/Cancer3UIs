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
import pandas as dd
import re
import duckdb

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
                      default = "track",
                      help="names to use for colums which record the file of"
                           "origin")
    parser.add_option("-p", dest="partition", action="store_true",
                      help="parition dataset. By default partioning will be by the"
                           "cat columns")
    parser.add_option("--partition-on", dest="partition_on",
                     help="Columns to partition output parquet files on."
                          "by default the columsn in key-colums")
    parser.add_option("--database-path", dest="database_path",
                      default="csvdb.duck",
                      help="path to database file")
    parser.add_option("-s", "--sep", dest="sep",
                      default="\t",
                      help=r"Column seperater. Default = \t")
    parser.add_option("--no-header", dest="header", action="store_false",
                      help="files have no header")
    parser.add_option("--col-names", dest="col_names", 
                      help="Comma seperated list of names to use for columns")
    parser.add_option("-t", "--tablename", dest="tablename",
                      help="name of table to import into")
    options, args = E.start(parser, unknowns=True)
    
    n = 0
    
    con = duckdb.connect(options.database_path)
    con.execute("DROP TABLE IF EXISTS %s" % options.tablename)
    con.close()
    
    for infile in args:
        
        E.debug("importing file %s" % infile)
        # forcing opening and closing for each file forces clearing of the cache
        # and prevents run away memory usage
        con = duckdb.connect(options.database_path)
        
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
            
        keys = dict(zip([options.key_columns], keys))

        ddf_with_keys = ddf.assign(**keys)
        
        if n==0:
            con.execute("CREATE TABLE %s AS SELECT * from ddf_with_keys" % options.tablename)
        else:
            con.execute("INSERT INTO %s SELECT * from ddf_with_keys" % options.tablename)
        con.unregister("ddf_with_keys")
        

            
        n += 1
        
        con.close()        
    E.stop()
    
        
            
        
        
        
        
        
        
    

if __name__ == "__main__":
    sys.exit(main(sys.argv))
