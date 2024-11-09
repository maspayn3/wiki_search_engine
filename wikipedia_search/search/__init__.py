"""Search package initialization. Manages the search index instance."""
from wikipedia_search.search.index_loader import SearchIndex
from wikipedia_search.search.search_engine import SearchEngine

# Create global search index and engine instances
print("Creating empty search objects...")
search_index = SearchIndex()
search_engine = SearchEngine(search_index)

def init_app(app):
    """Initialize search index with application config."""
    print("Loading index data")
    search_index.load_index(
        app.config['INDEX_PATH'],
        app.config['STOPWORDS_PATH']
    )
    print("Index Loaded!")

# Make these available when importing from search package
__all__ = ['search_index', 'init_app', 'search_engine']