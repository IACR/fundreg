# Crossref funder registry search

The purpose of this repository is to provide a search index on the
Crossref funders registry. This is designed to allow quick lookup of
funders by their name, country, or alternate names. It is built using
the xapian search library.

Crossref provides an alternative way to search funders, but it does not appear
to use stemming or phrase search. Thus for example, their search for
[mathematics](https://api.crossref.org/funders?query=mathematics) does
not retrieve the American Mathematical Society because it matches only
on mathematics and not the stems of the word. 

There are two parts to this:
1. the search library that supports downloading the crossref data and building
   the search index.
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

## How this is built

The search index is built from parsing the RDF download, converting to JSON, and
using that to create the index.  The data set is quite small (approximately
32000 documents).

The search index holds documents that have the form:
```
{
  "id": "100000083",
  "doi": "10.13039/100000083",
  "name": "Directorate for Computer and Information Science and Engineering",
  "alt-names": [
    "Directorate for Computer & Information Science & Engineering",
    "Computer and Information Science and Engineering",
    "NSF Directorate for Computer and Information Science and Engineering",
    "NSF Computer and Information Science and Engineering",
    "NSF Computer & Information Science and Engineering Directorate",
    "NSF Directorate for Computer & Information Science & Engineering",
    "Computer and Information Science and Engineering Directorate National Science Foundation",
    "NSF's Directorate for Computer and Information Science and Engineering",
    "Computer & Information Science & Engineering",
    "CISE",
    "CISE/OAD",
    "CISE NSF"
  ],
  "narrower": {
    "100007523": "Division of Advanced Cyberinfrastructure",
    "100000143": "Division of Computing and Communication Foundations",
    "100000144": "Division of Computer and Network Systems",
    "100000145": "Division of Information and Intelligent Systems",
    "100000105": "Office of Advanced Cyberinfrastructure"
  },
  "broader": {
    "100000001": "National Science Foundation"
  },
  "location": "United States of America"
}
```
The `narrower` and `broader` categories allow the user to navigate to more specific or less
specific funding agencies.

