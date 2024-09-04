import imp
import os
import sys
from sgAmmoCsvUpdate import app

sys.path.insert(0, os.path.dirname(__file__))

server = app.server

wsgi = imp.load_source('wsgi', 'sgAmmoCsvUpdate.py')
application = wsgi.application
