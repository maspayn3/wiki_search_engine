"""Initialize Flask app."""
from flask import Flask
from typing import Optional
import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db():
    """Get database connection."""
    from flask import current_app
    
    db_path = current_app.config['DATABASE_PATH']
    print(db_path)
    conn = sqlite3.connect(db_path)
    
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def create_app(config_name: str = 'default') -> Flask:
    """Create and configure Flask app.
    
    Args:
        config_name: Configuration to use (default, development, testing)
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    from wikipedia_search.config import config
    app.config.from_object(config[config_name])
    
    import database
    database.init_db(app)

    # Initialize search index
    from wikipedia_search.search import init_app
    init_app(app)
    
    # Register blueprints
    from wikipedia_search.api import routes as api_routes
    from wikipedia_search.views import routes as view_routes
    app.register_blueprint(api_routes.api_bp)
    app.register_blueprint(view_routes.views_bp)

    return app

# Make database connection available at package level
__all__ = ['create_app', 'get_db']