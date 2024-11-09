"""WSGI entry point."""
from wikipedia_search import create_app

application = create_app('development')
app = application