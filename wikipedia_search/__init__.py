"""Initialize Flask app."""
from flask import Flask
from typing import Optional

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
    
    # Initialize search index
    from wikipedia_search.search import init_app
    init_app(app)
    
    # Register blueprints
    from wikipedia_search.api import routes as api_routes
    from wikipedia_search.views import routes as view_routes
    app.register_blueprint(api_routes.api_bp)
    app.register_blueprint(view_routes.views_bp)
    
    return app