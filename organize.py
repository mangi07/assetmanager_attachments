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
from urllib.parse import urlparse
import requests


filename = sys.argv[1]
os.mkdir("assets")
os.mkdir("invoices")
copied_files = []
file_counter = 0


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
    

def get_dest_path(folder, file):
    global file_counter
    name, ext = os.path.splitext(file)
    dest = os.path.join(folder, str(file_counter)+ext)
    file_counter = file_counter + 1
    return dest
    
    
def copy_file(f, dest, should_hash_fname):
    f = unquote(f)
    
    if should_hash_fname:
        new_fname = hash_fname(f)
        dest = os.path.join(dest, new_fname)
    else:
        dest = get_dest_path(dest, f)
        print(dest)
    
    copy(f, dest)


def move_files(from_list, folder, should_hash_fname):
    from_list = from_list.split(',')
    search_str = '(https|file):/{2,3}([^ }]+)'
    
    for file_link in from_list:
        if file_link in copied_files:
            continue
        
        match = re.search(search_str, file_link)
        if match:
            protocol = match.group(1)
            
            if protocol == "file":
                url = match.group(2)
                print(url)
                copy_file(url, folder, should_hash_fname)
                
            elif protocol == "https":
                url = match.group(0)
                a = urlparse(url)
                print(url)
                r = requests.get(url, allow_redirects=True)
                
                dest = get_dest_path(folder, url)
                open(dest, 'wb').write(r.content)
                
            copied_files.append(file_link)
        
        elif re.search('C:/.+', file_link):
            copy_file(file_link, folder, should_hash_fname)
            
            copied_files.append(file_link)


with open(filename, newline='') as csvfile:
    dialect = csv.Sniffer().sniff(csvfile.read(1024))
    csvfile.seek(0)
    reader = csv.reader(csvfile, dialect)
    
    for row in reader:
        id = row[0]
        descr = row[1]
        photos = row[29]
        invoices = row[40]
        
        move_files(photos, "assets", False)
        move_files(invoices, "invoices", True)
        