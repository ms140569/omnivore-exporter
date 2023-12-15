#!/usr/bin/env python3

# Simple Evernote enex -> omnivore csv exporter. Save stdout.
# https://docs.omnivore.app/using/importing.html#importing-csv-files

import xml.etree.ElementTree as ET
import csv
import sys
from dataclasses import dataclass, field
from typing import List
import dateutil.parser as dp

@dataclass
class Record:
    title: str = ""
    created: str = ""
    updated: str = ""
    tags: List[str] = field(default_factory=lambda: [])
    url: str = ""

def transform(input_file: str):
    tree = ET.parse(input_file)
    root = tree.getroot()

    print(f"url,state,labels,saved_at,published_at")

    for elem in root:
        rec = Record()
        tags = []

        for s in elem:
            if s.tag == 'title':
                rec.title = s.text

            if s.tag == 'created':
                rec.created = s.text

            if s.tag == 'updated':
                rec.updated = s.text

            if s.tag == 'tag':
                tags.append(s.text)

            if s.tag == 'note-attributes':
                for i in s:
                    if i.tag == 'source-url':
                        rec.url = i.text
        
        rec.tags = tags
        render(rec)

def render(rec: Record):
    clean_tags = str(rec.tags).replace('\'', '').replace(' ', '')

    def toTimestamp(stamp: str):
        return int(dp.parse(stamp).timestamp()*1e3)

    # url,state,labels,saved_at,published_at
    print(f"{rec.url},SUCCEEDED,\"{clean_tags}\",{toTimestamp(rec.created)},{toTimestamp(rec.updated)}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Please give ENEX XML-file as first argument")
        sys.exit(1)

    transform(sys.argv[1])
