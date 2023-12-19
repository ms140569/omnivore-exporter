#!/usr/bin/env python3

# Simple Evernote enex -> omnivore csv exporter. Save stdout.
# https://docs.omnivore.app/using/importing.html#importing-csv-files

import xml.etree.ElementTree as ET
import csv
import sys
from dataclasses import dataclass, field
from typing import List, Dict
import dateutil.parser as dp
import argparse
import requests
import urllib3

args = None
empty_url_cnt: int = 0
double_record_cnt: int = 0

@dataclass
class Record:
    title: str = ""
    created: str = ""
    updated: str = ""
    tags: List[str] = field(default_factory=lambda: [])
    url: str = ""

records: Dict[str, Record] = dict()

def transform(input_file: str):
    tree = ET.parse(input_file)
    root = tree.getroot()

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
        save_record(rec)

def save_record(rec: Record):
    global empty_url_cnt
    global double_record_cnt
    global records

    if len(rec.url) == 0:
        print(f"Empty record found: {rec.tags}", file=sys.stderr)
        empty_url_cnt += 1
        return
    
    if rec.url in records:
        print(f"Duplicate found: {rec.url}", file=sys.stderr)
        double_record_cnt += 1

        if len(rec.tags) > len(records.get(rec.url).tags):
            records[rec.url] = rec
            print(f"Overriding duplicate: {rec.url}, {rec.tags}", file=sys.stderr)
            return

        print(f"Dropping duplicate: {rec.url}, {rec.tags}", file=sys.stderr)

    records[rec.url] = rec 

def print_records():
    print(f"url,state,labels,saved_at,published_at")

    def toTimestamp(stamp: str):
        return int(dp.parse(stamp).timestamp()*1e3)

    for rec in records.values():
        clean_tags = str(rec.tags).replace('\'', '').replace(' ', '')

        # url,state,labels,saved_at,published_at
        print(f"\"{rec.url}\",SUCCEEDED,\"{clean_tags}\",{toTimestamp(rec.created)},{toTimestamp(rec.updated)}")

def verify_records():
    for rec in records.values():
        try:
            result = requests.head(rec.url, timeout=8.0)
        except Exception as e:
            print(f"Exception happend: {e}")

        print(f"Requesting: {rec.url} response={result}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("-c", "--check",
                        help="checks the url rather than writing the output", action="store_true")

    global args
    local_args = parser.parse_args()
    args = local_args
    
    if len(args.filename) < 1:
        print("Please give ENEX XML-file as first argument")
        sys.exit(1)

    transform(args.filename)

    if args.check:
        print(f"Extracted {len(records)} urls. Checking.", file=sys.stderr)
        verify_records()
    else:
        print_records()

    if empty_url_cnt > 0:
        print(f"Number of empty record found: {empty_url_cnt}", file=sys.stderr)
    
    if double_record_cnt > 0:
        print(f"Number of duplicate records found: {double_record_cnt}", file=sys.stderr)

if __name__ == '__main__':
    sys.exit(main())
