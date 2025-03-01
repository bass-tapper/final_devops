import requests
import logging
from flask import Flask, jsonify, request, make_response
import os
from werkzeug.exceptions import HTTPException
from functools import wraps
import time

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Constants
API_BASE_URL = "https://rickandmortyapi.com/api/character"
CACHE_TIMEOUT = 300  # 5 minutes cache
character_cache = {"data": None, "timestamp": 0}
character_detail_cache = {}

# Rate limiting setup
requests_limit = {}

def rate_limit(limit=10, per=60):
    """Rate limiting decorator to prevent abuse"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            client_ip = request.remote_addr
            
            # Check if IP has made requests
            if client_ip not in requests_limit:
                requests_limit[client_ip] = {"count": 0, "start": time.time()}
            
            # Reset counter if time period has passed
            if time.time() - requests_limit[client_ip]["start"] > per:
                requests_limit[client_ip] = {"count": 0, "start": time.time()}
            
            # Increment request count
            requests_limit[client_ip]["count"] += 1
            
            # Check if limit exceeded
            if requests_limit[client_ip]["count"] > limit:
                return make_response(jsonify({"error": "Rate limit exceeded"}), 429)
            
            return f(*args, **kwargs)
        return wrapped
    return decorator

def fetch_characters(filtered=True):
    """
    Fetches characters from Rick & Morty API.
    If filtered=True, returns characters matching these criteria:
    - Species: Human
    - Status: Alive
    - Origin: Earth (C-137)
    """
    # Check cache first
    current_time = time.time()
    if character_cache["data"] is not None and current_time - character_cache["timestamp"] < CACHE_TIMEOUT:
        logger.info("Returning characters from cache")
        return character_cache["data"]
    
    logger.info("Fetching characters from Rick & Morty API")
    url = API_BASE_URL
    characters = []
    
    try:
        while url:
            logger.info(f"Fetching data from: {url}")
            response = requests.get(url)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            data = response.json()
            
            # Process results
            for character in data.get('results', []):
                # Apply filters if requested
                if filtered:
                    if (character.get('species') == 'Human' and 
                        character.get('status') == 'Alive' and 
                        character.get('origin', {}).get('name') == 'Earth (C-137)'):
                        
                        # Extract required fields
                        characters.append({
                            'id': character.get('id'),
                            'name': character.get('name'),
                            'status': character.get('status'),
                            'species': character.get('species'),
                            'location': character.get('location', {}).get('name'),
                            'origin': character.get('origin', {}).get('name'),
                            'image_url': character.get('image')
                        })
                else:
                    # Include all characters but with consistent schema
                    characters.append({
                        'id': character.get('id'),
                        'name': character.get('name'),
                        'status': character.get('status'),
                        'species': character.get('species'),
                        'location': character.get('location', {}).get('name'),
                        'origin': character.get('origin', {}).get('name'),
                        'image_url': character.get('image')
                    })
            
            # Get URL for next page, if any
            url = data.get('info', {}).get('next')
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {str(e)}")
        return None
    
    # Update cache
    character_cache["data"] = characters
    character_cache["timestamp"] = current_time
    
    return characters

def fetch_character_by_id(character_id):
    """Fetch a specific character by ID from the Rick & Morty API"""
    # Check cache first
    if character_id in character_detail_cache and time.time() - character_detail_cache[character_id]["timestamp"] < CACHE_TIMEOUT:
        logger.info(f"Returning character {character_id} from cache")
        return character_detail_cache[character_id]["data"]
    
    try:
        url = f"{API_BASE_URL}/{character_id}"
        logger.info(f"Fetching character data from: {url}")
        
        response = requests.get(url)
        response.raise_for_status()
        
        character = response.json()
        
        # Format character data
        character_data = {
            'id': character.get('id'),
            'name': character.get('name'),
            'status': character.get('status'),
            'species': character.get('species'),
            'type': character.get('type'),
            'gender': character.get('gender'),
            'origin': character.get('origin', {}).get('name'),
            'location': character.get('location', {}).get('name'),
            'image_url': character.get('image'),
            'episode': character.get('episode', []),
            'url': character.get('url'),
            'created': character.get('created')
        }
        
        # Update cache
        character_detail_cache[character_id] = {
            "data": character_data,
            "timestamp": time.time()
        }
        
        return character_data
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return None
        logger.error(f"HTTP error: {str(e)}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {str(e)}")
        raise

# API Routes
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

@app.route('/characters', methods=['GET'])
@rate_limit()
def get_characters():
    """
    Get all characters endpoint
    Optional query parameter 'filtered=true/false' 
    to apply Human/Alive/Earth C-137 filter
    """
    filtered = request.args.get('filtered', 'true').lower() == 'true'
    characters = fetch_characters(filtered=filtered)
    
    if characters is None:
        return jsonify({'error': 'Failed to fetch characters from API'}), 503
    
    return jsonify({
        'count': len(characters),
        'characters': characters
    })

@app.route('/characters/<int:character_id>', methods=['GET'])
@rate_limit()
def get_character(character_id):
    """Get a specific character by ID"""
    character = fetch_character_by_id(character_id)
    
    if character is None:
        return jsonify({'error': 'Character not found'}), 404
    
    return jsonify(character)

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    logger.error(f"Server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(HTTPException)
def handle_http_exception(error):
    """Handle HTTP exceptions"""
    response = jsonify({'error': error.description})
    response.status_code = error.code
    return response

@app.errorhandler(Exception)
def handle_exception(error):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(error)}")
    return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == "__main__":
    # For production, use a proper WSGI server like gunicorn
    # This is for development only
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
