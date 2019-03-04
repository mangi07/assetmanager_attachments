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

TODO: may be better with class-based preprocessing on file urls - separate out the file operations from csv data parsing
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
from PIL import Image


filename = sys.argv[1]
new_filename = "new.csv"

if not os.path.isdir("assets"):
    os.mkdir("assets")
if not os.path.isdir("invoices"):
    os.mkdir("invoices")
if not os.path.isdir("temp"):
    os.mkdir("temp")
copied_files = {} # key: old path, value: new path (dest)
file_counter = 0
debug_counter = 0


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
    return dest
    
    
def copy_file(f, folder, should_hash_fname):
    """Returns a filepath: directory + filename"""
    global file_counter
    f = unquote(f)
    
    if should_hash_fname:
        new_fname = hash_fname(f)
        dest = os.path.join(folder, new_fname)
    else:
        dest = get_dest_path(folder, f)
    
    copy(f, dest)
    if folder.endswith("assets"):
        file_counter = file_counter + 1
    
    return dest


def get_file_type(filepath):
    filename, ext = os.path.splitext(filepath)
    print("In get_file_ext: " + ext)
    ext == ext.lower()
    if ext == ".jpg" or ext == ".jpeg" or ext == ".png" or ext == ".gif" or ext == ".png":
        return "image"
    elif ext == ".pdf":
        return "pdf"
    return "unknown"


# TODO: function here to check for corrupt image and pdf files, then img check in elif https protocol move here
def verify_file(filepath):
    file_type = get_file_type(filepath)
    if file_type == "image":
        try:
            with Image.open(filepath, mode="r") as img:
                img.verify()
            return True
        except:
            print(filepath + " not a valid file")
            return False
    elif file_type == "pdf":
        return True
    return False


def move_files(from_list, folder, should_hash_fname):
    global debug_counter
    new_paths = []
    dest = None
    from_list = from_list.split(',')
    search_str = '(https|file):/{2,3}([^ }]+)'
    
    for file_link in from_list:
        if file_link in copied_files:
            # In this case, the file referred to in this row was already moved during a previous row iteration.
            # Find and and record where the file was copied to for this new *.csv entry.
            dest = copied_files[file_link]
            new_paths.append(dest)
            continue
        match = re.search(search_str, file_link)
        if match:
            protocol = match.group(1)
            if protocol == "file":
                url = match.group(2)
                dest = copy_file(url, folder, should_hash_fname)
            elif protocol == "https":
                url = match.group(0)
                #a = urlparse(url)
                r = requests.get(url, allow_redirects=True)
                debug_counter = debug_counter + 1
                # download the file to a temp dir
                # check file contents are readable as image file (exception thrown if not)
                # if so, simply call function copy_file
                temp_path = get_dest_path("temp", url)
                open(temp_path, 'wb').write(r.content)
                if verify_file(temp_path):
                    dest = copy_file(temp_path, folder, should_hash_fname)
                    os.remove(temp_path)
                else:
                    os.remove(temp_path)
                    raise Exception
            copied_files[file_link] = dest
        # TODO: this regex is not quite right with the number of slashes
        elif re.search('C:[/\\\\].+', file_link):
            dest = copy_file(file_link, folder, should_hash_fname)
            copied_files[file_link] = dest
        if dest is not None:
            new_paths.append(dest)
    return new_paths


with open(filename, 'r', newline='') as csvfile:
    dialect = csv.Sniffer().sniff(csvfile.read(1024))
    csvfile.seek(0)
    reader = csv.reader(csvfile, dialect)
    
    for row in reader:
        id = row[0]
        descr = row[1]
        photos = row[29]
        invoices = row[40]

        # catch runtime errors such as file not found
        # and append the row causing error to a separate csv to be dealt with later
        # because we want the script to make one pass through the original asset listing without stopping
        try:
            new_photo_paths = move_files(photos, "assets", False)
            if len(new_photo_paths) > 0:
                row[29] = new_photo_paths

            new_invoice_paths = move_files(invoices, "invoices", True)
            if len(new_invoice_paths) > 0:
                row[40] = new_invoice_paths

            # TODO: get files from "OTHER LINKS" column
        except:
            with open("errors.csv", 'a', newline='') as ef:
                writer = csv.writer(ef)
                writer.writerow(row)
                continue
        # TODO: convert cells of this nature -- '['']' OR '['','']' etc. -- to this: ''

        with open(new_filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

        # debug
        #print("*******************")
        #print(row)
        #print("photo links: " + str(new_photo_paths))
        #print("invoice links: " + str(new_invoice_paths))

# debug
print("\n\nNumber of http(s) requests: " + str(debug_counter))