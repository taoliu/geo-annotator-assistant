#!/usr/bin/env python3

from glob import glob
import os
import json
import argparse as ap

from .gse_soft_parser import extract_sample_level_data
from .utils import gse_dict_to_prompt

def main():
    # configure args
    description = "%(prog)s -- Extract information of each sample in a GEO series from the given SOFT file. Then store the extracted context in prompt for each GSM in a jsonl file."
    epilog = """
Example:

%(prog)s -i test.soft.gz -o test_content.jsonl
"""

    argparser = ap.ArgumentParser(description=description,
                                  epilog=epilog,
                                  formatter_class=ap.RawDescriptionHelpFormatter)
    argparser.add_argument("-i",
                           dest="ifile",
                           type=str,
                           required=True,
                           help="The input SOFT file, or gzipped SOFT file. REQUIRED.")
    argparser.add_argument("-o",
                           dest="ofile",
                           type=str,
                           required=True,
                           help="The filename of the output jsonl file. REQUIRED.")
    args = argparser.parse_args()

    input_file_path = args.ifile
    output_file_path = args.ofile

    with open(output_file_path, "wt") as f:
        gse_dict = extract_sample_level_data(input_file_path)
        if gse_dict is None:
            print(f"No sample data extracted from {input_file_path}.")
        else:
            data_to_write = gse_dict_to_prompt(gse_dict)

            # Write each dictionary entry on its own line
            for entry in data_to_write:
                f.write(json.dumps(entry) + '\n')

if __name__ == '__main__':
    main()