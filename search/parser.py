from enum import Enum
import json
import sys
from xml.sax import parse
from xml.sax.handler import ContentHandler

class Tag(str, Enum):
    """Tags that we recognize and act on."""
    hasTopConcept = 'skos:hasTopConcept'
    Concept            = 'skos:Concept'
    literalForm        = 'skosxl:literalForm'
    prefLabel          = 'skosxl:prefLabel'
    altLabel           = 'skosxl:altLabel'
    broader            = 'skos:broader'
    narrower           = 'skos:narrower'
    fundingBodyType    = 'svf:fundingBodyType'
    fundingBodySubType = 'svf:fundingBodySubType'
    state              = 'svf:state'
    region             = 'svf:region'
    addressCountry     = 'schema:addressCountry'
    country            = 'svf:country'

class FunderHandler(ContentHandler):
    """Handler for parsing registry.rdf."""
    def __init__(self, data, country_map):
        self.data = data
        self.country_map = country_map
        self.item = None
        # Keep track of current tag for characters()
        self.current_tag = None
        self.in_altLabel = False
        self.in_prefLabel = False
        self.content = ''

    def id_from_uri(self, uri):
        return uri.split('/')[-1]

    def startElement(self, name, attrs):
        self.current_tag = name
        if name == Tag.hasTopConcept:
            exid = self.id_from_uri(attrs.get('rdf:resource'))
            self.data['existing'].append(exid)
        elif name == Tag.Concept:
            docid = self.id_from_uri(attrs.get('rdf:about'))
            self.item = {'id': docid,
                         'doi': '10.13039/' + docid,
                         'altnames': [],
                         'narrower': [],
                         'broader': []
                         }
        elif name == Tag.broader:
            self.item['broader'].append(self.id_from_uri(attrs.get('rdf:resource')))
        elif name == Tag.narrower:
            self.item['narrower'].append(self.id_from_uri(attrs.get('rdf:resource')))
        elif name == Tag.state:
            self.item['state'] = attrs.get('rdf:resource')
        elif name == Tag.prefLabel:
            self.in_prefLabel = True
        elif name == Tag.altLabel:
            self.in_altLabel = True
        elif name == Tag.country:
            self.item['geocountry'] = attrs.get('rdf:resource')

    # This is annoying because if you have <foo>This &ampl; that</foo>
    # then it calls characters() three times inside the foo tag. Because
    # of that we simply accumulate the strings inside a tag as self.content
    # and then collect it at endElement
    def characters(self, content):
        self.content += content

    def endElement(self, name):
        self.content = self.content.strip()
        if name == 'skos:Concept':
            self.data['items'][self.item['id']] = self.item
            self.item = None
        elif name == Tag.prefLabel:
            self.in_prefLabel = False
        elif name == Tag.altLabel:
            self.in_altLabel = False
        if self.current_tag == Tag.literalForm and self.in_altLabel:
            self.item['altnames'].append(self.content)
        elif self.current_tag == Tag.literalForm and self.in_prefLabel:
            self.item['name'] = self.content
        elif self.current_tag == Tag.fundingBodyType:
            self.item['fundingBodyType'] = self.content
        elif self.current_tag == Tag.fundingBodySubType:
            self.item['fundingBodySubType'] = self.content
        elif self.current_tag == Tag.region:
            self.item['region'] = self.content
        elif self.current_tag == Tag.addressCountry:
            self.item['country_code'] = self.content
            self.item['country'] = self.country_map.get(self.content, 'unknown')
        self.current_tag = None
        self.content = '' # reset at end of tag.
            

def parse_rdf(country_map):
    """Parse the registry.rdf file and return a dict.
       args:
          country_map: a dict from iso3 country codes to names
       return:
          a dict with items.
    """
    # existing is merely used to check the hasTopConcept assertions
    # and is deleted after the check.
    data = {
        'existing': [],
        'items': {}
    }
    handler = FunderHandler(data, country_map)
    parse("data/registry.rdf", handler)
    for existing in data['existing']:
        try:
            assert existing in data['items']
        except Exception as e:
            print(str(e))
            # print(json.dumps(data, indent=2))
            sys.exit(32)
    del data['existing']
    return data

if __name__ == '__main__':
    country_map = json.loads(open('data/country_map.json', 'r').read())
    data = parse_rdf(country_map)
    print(json.dumps(data, indent=2))
