"""
This is used to manage the submission of final papers. Authors enter the site via
an authenticated URL with a paper ID from hotcrp. When a paper is submitted, it
receives an upload of a zip file with at least one tex file. We start a docker instance
in a separate task to compile the output.
"""

from flask import json, Flask, request, render_template, current_app
import os
import sys
from search.search_lib import search

# Make sure we aren't running on an old python.
assert sys.version_info >= (3, 7)

config = {'db_path': 'search/xapian.db'}

app = Flask(__name__, static_folder='static/', static_url_path='/')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/view/<int:id>')
def view_funder(id):
    result = search(config.get('db_path'),
                    offset=0,
                    textq='id:' + str(id),
                    locationq=None)
    if len(result.get('results')) > 0:
        result = {'item': result.get('results')[0]}
    else:
        result = {'error': 'no such item'}
    print(result)
    return render_template('index.html', **result)

@app.route('/search', methods=['GET'])
def get_results():
    args = request.args.to_dict()
    if 'textq' not in args and 'locationq' not in args:
        return json.jsonify({'error': 'missing queries'})
    return json.jsonify(search(config.get('db_path'),
                               offset=args.get('offset', 0),
                               textq=args.get('textq'),
                               locationq=args.get('locationq')))
    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
