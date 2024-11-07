"""Web routes for the search engine."""
from flask import Blueprint, render_template, request, jsonify
import requests

bp = Blueprint('views', __name__)

@bp.route('/')
def index():
    """Home page with API test form."""
    return render_template('test.html')

@bp.route('/test-api', methods=['GET'])
def test_api():
    """Test page for API endpoints."""
    # Get some test data from our API
    word = request.args.get('word', '')
    if word:
        api_response = requests.get(f'http://localhost:5000/api/v1/word/{word}')
        return jsonify(api_response.json())
    return jsonify({"message": "Enter a word to test"})

@bp.route('/stats')
def show_stats():
    """Show index statistics."""
    try:
        api_response = requests.get('http://localhost:5000/api/v1/stats')
        return render_template('stats.html', stats=api_response.json())
    except requests.RequestException:
        return "Error fetching stats", 500