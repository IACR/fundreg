# Crossref funder registry search

The purpose of this repository is to provide a search index on the
Crossref funders registry. This is designed to allow quick lookup of
funders by their name, or alternate names. It is built using the
xapian search library. This was built as a support piece for a
forthcoming `LaTeX` package that provides an API for authors to
specify their metadata directly in the `LaTeX` source of their
publications.

Crossref provides an alternative way to search funders, but it does not appear
to use stemming or phrase search. Thus for example, their search for
[mathematics](https://api.crossref.org/funders?query=mathematics) does
not retrieve the American Mathematical Society because it matches only
on mathematics and not the stems of the word. 

We regard the funders registry as primary, but we also augment it by
the ROR registry to cover the case where a professor receives support
for a temporary visit to conduct research. For this reason we have
defined a common entity called `Funder` in `search/model.py` and
we parse data from both sources into this format. If a ROR entity is
found that matches a Funder Registry entity because it has an external
preferred ID for `FundRef`, then we merge it into the existing Funder
Registry entity.  The `Funder` entity has a name, country, and
references to related entities.  It includes child and parent
relationships as well as "related" entities.

There are two parts to this:
1. the search library that supports downloading the crossref and ROR data
   to build the search index.
2. a web app written in python/Flask that shows how to use the library. It
   provides a web interface for the user to enter terms for the name of their
   funding agency and (optionally) their country. It returns the relevant
   LaTeX code for entering it.

To run the app on your desktop, install the required packages, build the index
using
```
cd search
python3 create_index.py
```
There are options on `create_index.py` to fetch the RDF or rebuild the JSON.
Then change to the root directory and type `python3 app.py`. When you run it as
a wsgi app you may have to change the prefix where it is mounted on your server.

## Data sources

The two data sources are Funder Registry (FundReg) and ROR. FundReg
data is available through several sources, but they vary in what they
provide. We use the RDF distribution, which is a single file that
includes relationships to other entities. The latest version is stored
as `data/registry.rdf`.

The information about how to fetch ROR data is at
https://ror.readme.io/docs/data-dump Their data is versioned and
available as a large JSON file. We store
the latest version in `search/data/` and provide a symbolic link to
the latest version as `search/data/ror.json`. 

## Parsing data

The RDF file is parsed using
a python SAX parser in `search/rdf_parser.py`. The output is a
`FunderList` object. This data set is fairly small (approximately 32000
documents).

The ror data in `search/data/ror.json` is is a rather large JSON file
with an array at the top level, so we parse it using the python `naya`
package that provides a streaming parser. We provide the `FunderList`
object to this parser and merge the ROR objects into the list.

## The data model

The `Funder` object is defined in `search/model.py using the
`pydantic` python package to facilitate easy validation, but it could
have been built with any technology that supports serialization
(validation is just a good practice). The JSON schema for the Funder
object is given by:

```
{
  "title": [
    "Funder entity that sponsors Research"
  ],
  "description": "Funder may come from Funder's Registry or ROR.  This picks up\nsource, source_id, and global_id() from GlobalEntity.",
  "type": "object",
  "properties": {
    "source": {
      "title": "Original source of data",
      "description": "We prefer fundref, but this is not complete",
      "allOf": [
        {
          "$ref": "#/definitions/DataSource"
        }
      ]
    },
    "source_id": {
      "title": "Unique ID within the data source",
      "description": "See global_id() for a global ID. This is the ROR suffix for ROR entities, and the Funding Registry ID for FundReg entities.",
      "type": "string"
    },
    "name": {
      "title": "The main name of the organization",
      "description": "Other names are in altnames",
      "minLength": 2,
      "type": "string"
    },
    "country": {
      "title": "Country of affiliation",
      "description": "May be any string",
      "type": "string"
    },
    "country_code": {
      "title": "ISO 3-letter country code.",
      "description": "Optional",
      "type": "string"
    },
    "funder_type": {
      "title": "The type of funding agency",
      "description": "May be from ROR.",
      "allOf": [
        {
          "$ref": "#/definitions/FunderType"
        }
      ]
    },
    "preferred_fundref": {
      "title": "ROR may stipulate a preferred FundRef value",
      "description": "We use this to merge ROR records",
      "type": "string"
    },
    "altnames": {
      "title": "List of alternative names",
      "description": "May be in a language other than English",
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "children": {
      "title": "Child entities",
      "description": "From FundReg and ROR.",
      "type": "array",
      "items": {
        "$ref": "#/definitions/Relationship"
      }
    },
    "parents": {
      "title": "Parent entities",
      "description": "From FundReg and ROR.",
      "type": "array",
      "items": {
        "$ref": "#/definitions/Relationship"
      }
    },
    "related": {
      "title": "Related entities",
      "description": "From FundReg and ROR.",
      "type": "array",
      "items": {
        "$ref": "#/definitions/Relationship"
      }
    }
  },
  "required": [
    "source",
    "source_id",
    "name",
    "country",
    "funder_type",
    "altnames",
    "children",
    "parents",
    "related"
  ],
  "additionalProperties": false,
  "definitions": {
    "DataSource": {
      "title": "DataSource",
      "description": "We index two types of organizations.",
      "enum": [
        "fundreg",
        "ror",
        "merged"
      ],
      "type": "string"
    },
    "FunderType": {
      "title": "FunderType",
      "description": "These are from ROR, and we map FundReg to these.",
      "enum": [
        "Education",
        "Healthcare",
        "Company",
        "Archive",
        "Nonprofit",
        "Government",
        "Facility",
        "Institute",
        "Other"
      ],
      "type": "string"
    },
    "Relationship": {
      "title": "Relationship",
      "description": "This picks up source, source_id, and global_id() from GlobalEntity.",
      "type": "object",
      "properties": {
        "source": {
          "title": "Original source of data",
          "description": "We prefer fundref, but this is not complete",
          "allOf": [
            {
              "$ref": "#/definitions/DataSource"
            }
          ]
        },
        "source_id": {
          "title": "Unique ID within the data source",
          "description": "See global_id() for a global ID. This is the ROR suffix for ROR entities, and the Funding Registry ID for FundReg entities.",
          "type": "string"
        },
        "name": {
          "title": "Name of entity.",
          "description": "May not be the same as other names.",
          "type": "string"
        }
      },
      "required": [
        "source",
        "source_id",
        "name"
      ]
    }
  }
}
```
