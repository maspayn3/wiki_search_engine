import sqlite3

def get_db():
    """Opens database connection."""
    db = sqlite3.connect('./var/wiki.sqlite3')

    if not db:
        print("Error connnecting to database")
        exit(1)
    return db