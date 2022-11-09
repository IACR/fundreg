#!/usr/bin/env python

"""
Main driver for the index build. Note that running this will not
overwrite an existing index specified in args.dbpath. If you are
replacing an existing database, then write it to a temporary location
and then move the directory to the production directory.

"""

import argparse
import json
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

    lookup = {}
    for item in items:
        lookup[item.get('id')] = item
    # Set up a TermGenerator that we'll use in indexing.
    termgenerator = xapian.TermGenerator()
    termgenerator.set_database(db)
    # use Porter's 2002 stemmer
    termgenerator.set_stemmer(xapian.Stem("english")) 
    termgenerator.set_flags(termgenerator.FLAG_SPELLING);
    count = 0
    for item in items:
        narrower = {}
        for key in item.get('narrower'):
            narrower[key] = lookup.get(key).get('name')
        item['narrower'] = narrower
        broader = {}
        for key in item.get('broader'):
            broader[key] = lookup.get(key).get('name')
        item['broader'] = broader
        index_funder(item, db, termgenerator)
        count += 1
        if count % 5000 == 0:
            print(f'{count} funders')
            db.commit()
    db.commit()
    print(f'Indexed {count} documents')

def update_from_crossref():
    """This method is deprecated since it did not support narrower."""
    cr = Crossref()
    num_fetched=0
    # We want all of them but we don't know how many there are yet.
    total_records = 100000000
    while num_fetched < total_records:
        page = cr.funders(offset=num_fetched)
        message = page.get('message')
        total_records = int(message.get('total-results'))
        items = message.get('items')
        for item in items:
            del item['tokens']
            funders[item.get('id')] = item
            for repl in item['replaces']:
                print('replaces {}'.format(repl))
                outdated.append(repl)
        num_fetched = len(funders)
        print('{}/{}/{} fetched'.format(len(items), num_fetched, total_records))
    for id in outdated:
        if id in funders:
            del funders[id]
    items = list(funders.values())
    funders_file.write_text(json.dumps({'num': len(items), 'items': items}, indent=2), encoding='UTF-8')

def fetch_rdf():
    print('fetching data/registry.rdf file...')
    url = 'https://gitlab.com/crossref/open_funder_registry/-/raw/master/registry.rdf?inline=false'
    response = requests.get(url)
    rdf_file = Path('data/registry.rdf')
    rdf_file.write_text(response.text, encoding='UTF-8')
    print('updated registry.rdf file')

def update_from_rdf():
    ns = {'skos': 'http://www.w3.org/2004/02/skos/core#',
          'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
          'dct': 'http://purl.org/dc/terms/',
          'skosxl': 'http://www.w3.org/2008/05/skos-xl#',
          'svf': 'http://data.crossref.org/fundingdata/xml/schema/grant/grant-1.2/',
          'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
          'fref': 'http://data.crossref.org/fundingdata/terms',
          'schema': 'https://none.schema.org/'}
    root = ET.parse('data/registry.rdf')
    funders = {}

    # The RDF file appears to have country in two equally obtuse formats:
    # 1. geonames ID.
    # 2. ISO3 codes.
    # Because of this, we have to look up the name from the ISO3 code.
    countries = {}
    country_file = Path('data/countries.json')
    country_list = json.loads(country_file.read_text(encoding='UTF-8'))
    for c in country_list:
        countries[c['iso3'].lower()] = c['name']

    conceptlist = root.find('skos:ConceptScheme', ns)
    for topconcept in conceptlist.findall('skos:hasTopConcept', ns):
        id = topconcept.attrib['{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource'].split('/')[-1]
        funders[id] = {'id': id, 'doi': '10.13039/' + id}
    for concept in root.findall('skos:Concept', ns):
        id = concept.attrib['{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about'].split('/')[-1]
        assert id in funders
        funder = funders[id]
        preferred = concept.find('skosxl:prefLabel', ns)
        if preferred:
            funder['name'] = preferred.find('skosxl:Label', ns).find('skosxl:literalForm', ns).text
        altnames = []
        for altnode in concept.findall('skosxl:altLabel', ns):
            label = altnode.find('skosxl:Label', ns)
            if label:
                lname = label.find('skosxl:literalForm', ns).text
                altnames.append(lname)
        funder['altnames'] = altnames
        narrowlist = []
        for narrownode in concept.findall('skos:narrower', ns):
            narrowlist.append(narrownode.attrib['{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource'].split('/')[-1])
        funder['narrower'] = narrowlist
        broaderlist = []
        for broadernode in concept.findall('skos:broader', ns):
            broaderlist.append(broadernode.attrib['{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource'].split('/')[-1])
        funder['broader'] = broaderlist
        bodyTypeNode = concept.find('svf:fundingBodyType', ns)
        if bodyTypeNode:
            funder['bodyType'] = bodyTypeNode.text
        regionNode = concept.find('svf:region', ns)
        if regionNode:
            funder['region'] = regionNode.text
        countryNode = concept.find('schema:address', ns)
        if countryNode:
            postalAddressNode = countryNode.find('schema:postalAddress', ns)
            if postalAddressNode:
                funder['location'] = postalAddressNode[0].text
                if funder['location'] in countries:
                    funder['location'] = countries.get(funder['location'])

    funders = {'items': list(funders.values())}
    funders['num'] = len(funders['items'])
    json_file = Path('data/funders.json')
    json_file.write_text(json.dumps(funders, indent=2), encoding='UTF-8')
    return funders

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
    funders_file = Path('data/funders.json')
    if os.path.isfile(args.dbpath) or os.path.isdir(args.dbpath):
        print('CANNOT OVERWRITE dbpath')
        sys.exit(2)
    if args.fetch:
        fetch_rdf()
    if args.rebuild_json:
        funders = update_from_rdf()
    else:
        funders = json.loads(funders_file.read_text(encoding='UTF-8'))
    create_index(args.dbpath, funders.get('items'), args.verbose)

