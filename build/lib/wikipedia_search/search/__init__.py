"""Search package initialization. Manages the search index instance."""
from wikipedia_search.search.index_loader import SearchIndex, init_app

# Create global search index instance
search_index = SearchIndex()

# Make these available when importing from search package
__all__ = ['search_index', 'init_app']