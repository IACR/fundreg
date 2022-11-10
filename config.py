class Config(object):
    DEBUG = True
    DEVELOPMENT = True
    DB_PATH='search/xapian.db'
    prefix = '/awful'

class ProductionConfig(Config):
    DEBUG = True
    DEVELOPMENT = True
    # Where you mount the app in mod_wsgi.
    SCRIPT_NAME = '/funding'
    DB_PATH='/home/mccurley/git/fundreg/search/xapian.db'

