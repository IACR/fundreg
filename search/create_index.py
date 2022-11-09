#!/usr/bin/env python

"""
Main driver for the index build. Note that running this will not
overwrite an existing index specified in args.dbpath. If you are
replacing an existing database, then write it to a temporary location
and then move the directory to the production directory.

"""

import argparse
import json
from parser import parse_rdf
from pathlib import Path
import os
import requests
import sys
import xapian
from xml.etree import ElementTree as ET
# no longer used
# from habanero import Crossref
from search_lib import index_funder

assert sys.version_info >= (3,0)

def create_index(dbpath, items, verbose=False):
    db = xapian.WritableDatabase(dbpath, xapian.DB_CREATE_OR_OPEN)

    # Set up a TermGenerator that we'll use in indexing.
    termgenerator = xapian.TermGenerator()
    termgenerator.set_database(db)
    # use Porter's 2002 stemmer
    termgenerator.set_stemmer(xapian.Stem("english")) 
    termgenerator.set_flags(termgenerator.FLAG_SPELLING);
    count = 0
    for item in items.values():
        narrower = {}
        for key in item.get('narrower'):
            narrower[key] = items.get(key).get('name')
        item['narrower'] = narrower
        broader = {}
        for key in item.get('broader'):
            broader[key] = items.get(key).get('name')
        item['broader'] = broader
        index_funder(item, db, termgenerator)
        count += 1
        if count % 5000 == 0:
            print(f'{count} funders')
            db.commit()
    db.commit()
    print(f'Indexed {count} documents')

def fetch_rdf():
    print('fetching data/registry.rdf file...')
    url = 'https://gitlab.com/crossref/open_funder_registry/-/raw/master/registry.rdf?inline=false'
    response = requests.get(url)
    rdf_file = Path('data/registry.rdf')
    rdf_file.write_text(response.text, encoding='UTF-8')
    print('updated registry.rdf file')

if __name__ == '__main__':
    arguments = argparse.ArgumentParser()
    arguments.add_argument('--verbose',
                           action='store_true',
                           help='Whether to print debug info')
    arguments.add_argument('--fetch',
                           action='store_true',
                           help='Whether to fetch a fresh copy with the crossref API')
    arguments.add_argument('--rebuild_json',
                           action='store_true',
                           help='Whether to rebuild the json file from RDF')
    arguments.add_argument('--dbpath',
                           default='xapian.db',
                           help='Path to writable database directory.')
    args = arguments.parse_args()
    funders = {}
    outdated = []
    funders_file = Path('data/funders.json2')
    if os.path.isfile(args.dbpath) or os.path.isdir(args.dbpath):
        print('CANNOT OVERWRITE dbpath')
        sys.exit(2)
    if args.fetch:
        fetch_rdf()
    if args.fetch or args.rebuild_json:
        country_map = json.loads(open('data/country_map.json', 'r').read())
        funders = parse_rdf(country_map)
        funders_file.write_text(json.dumps(funders, indent=2), encoding='UTF-8')
    else:
        funders = json.loads(funders_file.read_text(encoding='UTF-8'))
    create_index(args.dbpath, funders.get('items'), args.verbose)

