"""API routes for the search engine."""
import flask
from flask import Blueprint, jsonify
from wikipedia_search.search import search_index

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.route('/hello')
def hello():
    """Test endpoint."""
    return flask.jsonify({
        "message": "Hello from API!",
        "status": "success"
    })

@api_bp.route('/test-search')
def test_search():
    """Test search endpoint."""
    return flask.jsonify({
        "query": "test",
        "hits": [
            {"doc_id": "1", "score": 0.9},
            {"doc_id": "2", "score": 0.7}
        ]
    })

@api_bp.route('/word/<string:word>')
def get_word(word: str):
    """Get index entry for a specific word."""
    
    if word in search_index.inverted_index:
        return jsonify({
            "word": word,
            "data": search_index.inverted_index[word]
        })
    
    return flask.jsonify({
        "error": f"Word '{word}' not found in index"
    }), 404


@api_bp.route('/stats')
def get_stats():
    """Get basic statistics about the index."""
    index = search_index.inverted_index
    return jsonify({
        "total_words": len(index),
        "sample_words": list(index.keys())[:5],  # First 5 words
        "stopwords_count": len(search_index.stopwords),
    })