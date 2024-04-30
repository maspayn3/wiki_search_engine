import sqlite3

def get_db():
    """Opens database connection."""
    db = sqlite3.connect('./var/wiki.sqlite3')
    return db