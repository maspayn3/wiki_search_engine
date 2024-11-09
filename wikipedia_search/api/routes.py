"""API routes for the search engine."""
import flask
from flask import Blueprint, jsonify, request
from wikipedia_search.search import search_index, search_engine

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.route('/hello')
def hello():
    """Test endpoint."""
    return flask.jsonify({
        "message": "Hello from API!",
        "status": "success"
    })

@api_bp.route('/test-search/', methods=['GET'])
def test_search():
    """Test search endpoint."""
    return flask.jsonify({
        "query": "test",
        "hits": [
            {"doc_id": "1", "score": 0.9},
            {"doc_id": "2", "score": 0.7}
        ]
    })

@api_bp.route('/word/<string:word>/', methods=['GET'])
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

@api_bp.route('/hits/', methods=['GET'])
def get_hits():
    """Search endpoint using vector space model with cosine similarity."""
    try:
        query = request.args.get('q')
        if not query:
            return flask.jsonify({"error": "No query provided"}), 400
        
        # set optional parameters
        k = request.args.get('k', default=10, type=int)
        strict = request.args.get('strict', default=False, type=bool)

        # use search engine to search query
        search_results = search_engine.search(query, k=k, strict_match=strict)
        print(search_results)

        results_formmated =[
            {
                "doc_id": doc_id,
                "score": float(score)
            }
            for doc_id, score in search_results
        ]

        return jsonify({
            "query": query,
            "num_results": len(results_formmated),
            "results": results_formmated,
            "strict_match": strict
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "query": query
        }), 500



@api_bp.route('/stats')
def get_stats():
    """Get basic statistics about the index."""
    index = search_index.inverted_index
    return jsonify({
        "total_words": len(index),
        "sample_words": list(index.keys())[:5],  # First 5 words
        "stopwords_count": len(search_index.stopwords),
    })