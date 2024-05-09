import flask
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, World!"


@app.route('/api/v1/')
def get_api():
    """Default api route."""
    context = {
        'hits': '/api/v1/hits/',
        'url': '/api/v1/'
    }

    return flask.jsonify(**context), 200

