# -*- coding: utf-8 -*-
"""
2/19/2019

@author: Ben.Olson

In order to prepare attachments for asset listings on django...

Consolidate photos and pdfs into new folders.
Their links are read in from a csv file.
Some are on the local file system and others require download over https.

New csv should be output as well, indicating the new file locations of asset attachments,
which will make it easier to link the attachments after csv import to django db.
"""

import csv
import sys
import re
import os
import hashlib
from shutil import copy
from urllib.parse import unquote


filename = sys.argv[1]

# TODO: test
def hash_fname(filepath):
    try:
        filename, file_extension = os.path.splitext(filepath)
    
        BLOCKSIZE = 65536
    
        hasher = hashlib.md5()
        
        with open(filepath, 'rb') as afile:
            buf = afile.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(BLOCKSIZE)
        
        newfilename = hasher.hexdigest() + file_extension
        return newfilename

    except:
        print("\nERROR: Fully-qualified file path needed.\nIf you already tried, try again and surround the path with quotes.\n")
        return None
    
def copy_file(f, dest, should_hash_fname):
    #f = "%r"%f
    f = unquote(f)
    
    if should_hash_fname:
        new_fname = hash_fname(f)
        dest = os.path.join(dest, new_fname)
    
    copy(f, dest)
    

debug_count = 0


os.mkdir("assets")
os.mkdir("invoices")

with open(filename, newline='') as csvfile:
    dialect = csv.Sniffer().sniff(csvfile.read(1024))
    csvfile.seek(0)
    reader = csv.reader(csvfile, dialect)
    
    
    search_str = '(https|file):/{2,3}([^ }]+)'
    for row in reader:
        #print("*****************")
        #print(row[0], " ", row[1], " ", row[29], " ", row[40])
        
        id = row[0]
        descr = row[1]
        photos = row[29]
        invoices = row[40]
        
# TODO: consolidate these operatiosn for photos and invoices into one method

        # make a list for photos
        photos = photos.split(',')
        for photo in photos:
            match = re.search(search_str, photo)
            if match:
                protocol = match.group(1)
                url = match.group(2)
                
                if protocol == "file":
                    copy_file(url, "assets", False)
                elif protocol == "https":
                    # TODO: fetch from internet and save to destination instead of doing...
                    #copy_file(url, "assets", True)
                    pass
        
        invoices = invoices.split(',')
        for invoice in invoices:
            match = re.search(search_str, invoice)
            if match:
                protocol = match.group(1)
                url = match.group(2)

                if protocol == "file":
                        print(url)
                        copy_file(url, "invoices", True)
                elif protocol == "https":
                    pass