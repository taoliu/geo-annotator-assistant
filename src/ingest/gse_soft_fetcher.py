#!/usr/bin/env python3

import argparse as ap
import ftplib
from turtle import delay
import requests

import os
import time

def get_remote_path(geo_id):
    url = ""
    try:
        assert geo_id[:3] == "GSE"
        assert geo_id[3:].isdigit()
        dir_name_n = int(geo_id[3:]) // 1000
        if dir_name_n == 0:
            dir_name = "GSEnnn"
        else:
            dir_name = f"GSE{dir_name_n}" + "nnn"
        url = f"/geo/series/{dir_name}/{geo_id}/soft/{geo_id}_family.soft.gz"
    except AssertionError:
        pass

    return url


def get_local_path(geo_id, local_dir):
    file_path = ""
    try:
        assert geo_id[:3] == "GSE"
        assert geo_id[3:].isdigit()
        dir_name_n = int(geo_id[3:]) // 1000
        if dir_name_n == 0:
            dir_name = "GSEnnn"
        else:
            dir_name = f"GSE{dir_name_n}" + "nnn"
        file_path = f"{local_dir}/{dir_name}/{geo_id}_family.soft.gz"
    except AssertionError:
        pass

    return file_path


def download_file_via_ftp(remote_file_path,
                          local_file_path,
                          ftp_server="ftp.ncbi.nih.gov",
                          skip_existing_files=True):
    try:
        # Connect to the FTP server
        ftp = ftplib.FTP(ftp_server)
        ftp.login('anonymous', 'anonymous@example.com')
        
        remote_dirname = os.path.dirname(remote_file_path)
        remote_filename = os.path.basename(remote_file_path)

        if os.path.exists(local_file_path) and skip_existing_files:
            print(f"{local_file_path} exists, and is skipped for downloading again.")
        else:
            ftp.cwd(remote_dirname)
            # Download the file
            with open(local_file_path, 'wb') as local_file:
                ftp.retrbinary(f'RETR {remote_filename}', local_file.write)
        # Close the connection
        ftp.quit()
        print('Successfully downloaded')
    except Exception as e:
        print(f'Error: {e}')

def download_file_via_https(remote_file_path,
                            local_file_path,
                            base_url="https://ftp.ncbi.nih.gov",
                            skip_existing_files=True):
    try:
        remote_filename = os.path.basename(remote_file_path)

        if os.path.exists(local_file_path) and skip_existing_files:
            print(f"{local_file_path} exists, and is skipped for downloading again.")
        else:
            # Construct the full URL
            full_url = base_url + remote_file_path
            # Download the file
            response = requests.get(full_url, stream=True)

            # Skip if 404
            if response.status_code == 404:
                print("File not found (404). Skipping...")
            else:
                response.raise_for_status()  # Check for other HTTP errors
                with open(local_file_path, 'wb') as local_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # Filter out keep-alive chunks
                            local_file.write(chunk)

        print('Successfully downloaded')
    except Exception as e:
        print(f'Error: {e}')


def main():
    # Description and usage examples for the command-line argument parser
    description = "%(prog)s -- Download SOFT format files for GEO GSE datasets."

    epilog = """
Example:

%(prog)s -i GSE224707 -o GSE224707.soft.gz

In the 'collection1/' directory, there will be
'GSE224707_family.soft.gz' and 'GSE160365_family.soft.gz'.
"""

    # Set up the argument parser with description and epilog
    argparser = ap.ArgumentParser(description=description,
                                  epilog=epilog,
                                  formatter_class=ap.RawDescriptionHelpFormatter)
    argparser.add_argument("-i",
                           dest="id",
                           type=str,
                           required=True,
                           help="The GEO GSE id. E.g., GSE224707. REQUIRED")
    argparser.add_argument("-o",
                           dest="ofile",
                           type=str,
                           required=True,
                           help="The directory of the output SOFT file. E.g. GSE224707.soft.gz. REQUIRED.")
    argparser.add_argument("-O",
                           dest="overwritten",
                           action="store_true",
                           help="Whether to overwrite existing file. Default: False (do not overwrite).")

    # Parse the arguments
    args = argparser.parse_args()

    gse_id = args.id

    output_file_path = args.ofile

    remote_path = get_remote_path(gse_id)
    download_file_via_https(remote_path, output_file_path, skip_existing_files=(not args.overwritten))


# Run the main function if this script is executed
if __name__ == '__main__':
    main()
