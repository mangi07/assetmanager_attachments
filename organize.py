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

filename = sys.argv[1]


with open(filename, newline='') as csvfile:
    dialect = csv.Sniffer().sniff(csvfile.read(1024))
    csvfile.seek(0)
    reader = csv.reader(csvfile, dialect)
    
    
    for row in reader:
        print(row[0], " ", row[1], " ", row[29], " ", row[40])
        
        id = row[0]
        descr = row[1]
        photos = row[29]
        invoices = row[40]
        
        # make a list for photos
        photos = photos.split(',')
        for photo in photos:
            match = re.match(r'(https|file)://([^ }]+)', photo)
            protocol = match.group(1)
            url = match.group(2)
            
        
        
        
    