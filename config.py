class Config(object):
    DEBUG = True
    DEVELOPMENT = True
    DB_PATH='search/xapian.db' # may need to be absolute path.

class ProductionConfig(Config):
    DEBUG = False
    DEVELOPMENT = False
    # Where you mount the app in mod_wsgi.
    SCRIPT_NAME = '/funding'
    DB_PATH='search/xapian.db' # may need to be absolute path.

