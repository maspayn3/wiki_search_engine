"""API routes for the search engine."""
import flask
from flask import Blueprint, jsonify, request
from wikipedia_search.search import search_index, search_engine
from database import get_db
from typing import List, Tuple

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

def enhance_search_results(results: List[Tuple[int, float]]) -> List[dict]:
    """
    Enhance search results with document information from database.
    
    Args:
        results: List of (doc_id, score) tuples from search engine
        
    Returns:
        List of dictionaries containing enhanced result information
    """
    enhanced_results = []
    try:
        with get_db() as conn:
            for doc_id, score in results:
                # Get document metadata
                cur = conn.execute(
                    """
                    SELECT title, summary, url
                    FROM documents 
                    WHERE doc_id = ?
                    """, 
                    (doc_id,)
                )
                doc = cur.fetchone()
                if doc:
                    enhanced_results.append({
                        "doc_id": doc_id,
                        "score": float(score),
                        "title": doc['title'],
                        "summary": doc['summary'] or "No summary available",
                        "url": doc['url']
                    })

    except Exception as e:
        print(f"Error enhancing results: {str(e)}")
        # Re-raise to be handled by the route
        raise
        
    return enhanced_results

@api_bp.route('/hello')
def hello():
    """Test endpoint."""
    return flask.jsonify({
        "message": "Hello from API!",
        "status": "success"
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
        strict = request.args.get('strict', default=True, type=bool)

        # use search engine to search query
        search_results = search_engine.search(query, k=k, strict_match=strict)
        # print(search_results)

        enhanced_results = enhance_search_results(search_results)

        return jsonify({
            "query": query,
            "num_results": len(enhanced_results),
            "results": enhanced_results,
            "strict_match": strict,
            "search_time" : search_engine.metrics.most_recent_search_time
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "query": query
        }), 500



@api_bp.route('/stats')
def get_stats():
    """Get basic statistics about the index."""
    return jsonify(search_engine.metrics.get_stats())