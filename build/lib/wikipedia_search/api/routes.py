"""API routes for the search engine."""
import flask
from flask import Blueprint, jsonify
from wikipedia_search.search import index_loader

bp = Blueprint('api', __name__, url_prefix='/api/v1')

@bp.route('/hello')
def hello():
    """Test endpoint."""
    return flask.jsonify({
        "message": "Hello from API!",
        "status": "success"
    })

@bp.route('/test-search')
def test_search():
    """Test search endpoint."""
    return flask.jsonify({
        "query": "test",
        "hits": [
            {"doc_id": "1", "score": 0.9},
            {"doc_id": "2", "score": 0.7}
        ]
    })

@bp.route('/word/<string:word>')
def get_word(word: str):
    """Get index entry for a specific word."""

    if word in index_loader.search_index.inverted_index:
        return jsonify({
            "word": word,
            "data": index_loader.search_index.inverted_index[word]
        })
    
    return flask.jsonify({
        "error": f"Word '{word}' not found in index"
    }), 404


@bp.route('/stats')
def get_stats():
    """Get basic statistics about the index."""
    index = index_loader.search_index.inverted_index
    return jsonify({
        "total_words": len(index),
        "sample_words": list(index.keys())[:5],  # First 5 words
        "stopwords_count": len(index_loader.search_index.stopwords),
    })