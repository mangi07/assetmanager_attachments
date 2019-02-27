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

TODO: may be better with class-based preprocessing on file urls - separate out the file operations from csv data
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
new_filename = filename + "_new"

os.mkdir("assets")
os.mkdir("invoices")
copied_files = {} # key: old path, value: new path (dest)
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
    """Returns a filepath: directory + filename"""
    global file_counter
    name, ext = os.path.splitext(file)
    dest = os.path.join(folder, str(file_counter)+ext)
    file_counter = file_counter + 1
    return dest
    
    
def copy_file(f, dest, should_hash_fname):
    """Returns a filepath: directory + filename"""
    f = unquote(f)
    
    if should_hash_fname:
        new_fname = hash_fname(f)
        dest = os.path.join(dest, new_fname)
        #print("dest of hashed file:" + dest) # debug
    else:
        dest = get_dest_path(dest, f)
    
    #copy(f, dest) # debug: remove to actually copy files
    
    return dest


def move_files(from_list, folder, should_hash_fname):
    new_paths = []
    dest = ""
    from_list = from_list.split(',')
    search_str = '(https|file):/{2,3}([^ }]+)'
    
    for file_link in from_list:
        if file_link in copied_files:
            # Find old path that matches new path so this *.csv entry knows and records where the file was moved.
            # This is needed so that the photo's new path will be known in the updated *.csv entry
            dest = copied_files[file_link]
            new_paths.append(dest)
            continue
        
        match = re.search(search_str, file_link)
        if match:
            protocol = match.group(1)
            
            if protocol == "file":
                url = match.group(2)
                #print(url)
                dest = copy_file(url, folder, should_hash_fname)
                
            elif protocol == "https":
                url = match.group(0)
                #a = urlparse(url)
                #print(url)
                #print("waiting for http request to complete")
                r = requests.get(url, allow_redirects=True)
                
                dest = get_dest_path(folder, url)
                #open(dest, 'wb').write(r.content) # debug: uncomment when done debugging
                
            copied_files[file_link] = dest
        
        elif re.search('C:/.+', file_link):
            dest = copy_file(file_link, folder, should_hash_fname)
            
            copied_files[file_link] = dest

        #print(dest) # debug
        new_paths.append(dest)
            
    return new_paths


with open(filename, newline='') as csvfile:
    dialect = csv.Sniffer().sniff(csvfile.read(1024))
    csvfile.seek(0)
    reader = csv.reader(csvfile, dialect)
    
    for row in reader:
        id = row[0]
        descr = row[1]
        photos = row[29]
        invoices = row[40]
        
        new_photo_paths = move_files(photos, "assets", False)
        new_invoice_paths = move_files(invoices, "invoices", True)
        
        print("photo links: " + str(new_photo_paths))
        print("invoice links: " + str(new_invoice_paths))
        
        row[29] = new_photo_paths
        row[40] = new_invoice_paths
        
        #print("*******************") # debug
        #print(row) # debug
        