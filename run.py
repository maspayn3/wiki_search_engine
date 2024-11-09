"""Run the Flask application."""
import click
from wikipedia_search import create_app

@click.command()
@click.option('--port', default=5000, help='Part to run server on')
@click.option('--host', default='0.0.0.0', help='Host to run server on')
@click.option('--index-path', default=None, help='Path to index file')
def run_server(port, host, index_path):
    app = create_app('development')
    if index_path:
        app.config['INDEX_PATH'] = index_path
    app.run(host=host, port=port, debug=True)

if __name__ == '__main__':
    run_server()