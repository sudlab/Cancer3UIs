'''
extract_sf.py
====================================================

:Author: Ian Sudbery
:Release: $0.1$
:Date: |today|
:Tags: Python

Purpose
-------

Retrieve SF files loaded into the database eariler with P.concatenateAndLoad

Usage
-----

   python extract_sf.py [OPTIONS] DATABASE_FILE_OR_URL

Example::

    python extract_sf.py csvdb --output-filename-pattern=outdir/%s.sf

Type::

   python extract_sf.py --help

for command line help.

Command line options
--------------------

'''

import sys, os
from cgatcore import experiment as E
import cgatcore.iotools as IOTools
import itertools
from cgatcore import database as Database



def main(argv=None):
    """script main.
    parses command line options in sys.argv, unless *argv* is given.
    """

    if argv is None:
        argv = sys.argv

    # setup command line parser
    parser = E.OptionParser(version="%prog version: $1.0$",
                            usage=globals()["__doc__"])
    parser.add_option("-t", "--table", dest="table",
                      default="salmon_quant",
                      help="Database table with the expression data in")
    
    # add common options (-h/--help, ...) and parse command line
    # add_output_options will add a output-file-pattern option
    (options, args) = E.start(parser, argv=argv, add_output_options=True)

    outdir =  os.path.dirname(options.output_filename_pattern)
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    
    statement = '''SELECT track,
                          Name,
                          Length,
                          EffectiveLength,
                          TPM,
                          NumReads
                    FROM %s''' % options.table
    
    dbh = Database.connect(args[0])
    query = dbh.execute(statement)
    headers = [x[0] for x in query.description]
    outfiles = IOTools.FilePool(options.output_filename_pattern,
                                header="\t".join(headers[1:]) + "\n")

    current_file = None    
    for row in query:
        if row[0] != current_file:
            current_file = row[0]
            E.debug(current_file)
            
        outfiles.write(row[0], "\t".join(map(str, row[1:])) + "\n")
        
    outfiles.close()
    

    # write footer and output benchmark information.
    E.stop()

if __name__ == "__main__":
    sys.exit(main(sys.argv))

