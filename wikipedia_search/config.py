"Config settings for wiki search engine."
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    "Base configuration."

    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    
    DATABASE_PATH = os.path.join(BASE_DIR, '..', 'var', 'wiki.sqlite3')
    DATABASE_POOL_SIZE = 10
    DATABASE_TIMEOUT = 30

    INDEX_PATH = os.path.join(BASE_DIR, '../data/')
    STOPWORDS_PATH = os.path.join(BASE_DIR, '../data/stop_words.txt')

    MAX_SEARCH_RESULTS = 10

    DEBUG = False

class DevelopmentConfig(Config):
    """Dev config."""
    DEBUG = True


config = {
    'development': DevelopmentConfig
}