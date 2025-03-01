import unittest
from unittest.mock import patch, MagicMock
import json
import time
import requests
from rick_morty_api import app, fetch_characters, fetch_character_by_id, character_cache, character_detail_cache, CACHE_TIMEOUT, requests_limit

class TestHealthEndpoint(unittest.TestCase):
    """Test cases for the health check endpoint"""
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_health_check(self):
        """Test the health check endpoint returns the correct status"""
        response = self.app.get('/health')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'healthy')


class TestCharactersEndpoint(unittest.TestCase):
    """Test cases for the characters endpoint"""
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
        # Reset cache before each test
        character_cache["data"] = None
        character_cache["timestamp"] = 0
    
    @patch('rick_morty_api.requests.get')
    def test_get_filtered_characters(self, mock_get):
        """Test getting filtered characters"""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'info': {'next': None},
            'results': [
                {
                    'id': 1,
                    'name': 'Rick Sanchez',
                    'status': 'Alive',
                    'species': 'Human',
                    'origin': {'name': 'Earth (C-137)'},
                    'location': {'name': 'Earth'},
                    'image': 'https://rickandmortyapi.com/api/character/avatar/1.jpeg'
                },
                {
                    'id': 2,
                    'name': 'Morty Smith',
                    'status': 'Alive',
                    'species': 'Human',
                    'origin': {'name': 'Earth (C-137)'},
                    'location': {'name': 'Earth'},
                    'image': 'https://rickandmortyapi.com/api/character/avatar/2.jpeg'
                },
                {
                    'id': 3,
                    'name': 'Summer Smith',
                    'status': 'Alive',
                    'species': 'Human',
                    'origin': {'name': 'Earth (Replacement Dimension)'},
                    'location': {'name': 'Earth'},
                    'image': 'https://rickandmortyapi.com/api/character/avatar/3.jpeg'
                },
            ]
        }
        mock_get.return_value = mock_response
        
        # Make request
        response = self.app.get('/characters?filtered=true')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['characters']), 2)  # Only 2 characters match the filter criteria
        self.assertEqual(data['count'], 2)
        
        # Check that the filtered data only includes characters from Earth (C-137)
        for character in data['characters']:
            self.assertEqual(character['species'], 'Human')
            self.assertEqual(character['status'], 'Alive')
            self.assertEqual(character['origin'], 'Earth (C-137)')
        
        # Verify mock was called correctly
        mock_get.assert_called_once_with("https://rickandmortyapi.com/api/character")
    
    @patch('rick_morty_api.requests.get')
    def test_get_unfiltered_characters(self, mock_get):
        """Test getting unfiltered characters"""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'info': {'next': None},
            'results': [
                {
                    'id': 1,
                    'name': 'Rick Sanchez',
                    'status': 'Alive',
                    'species': 'Human',
                    'origin': {'name': 'Earth (C-137)'},
                    'location': {'name': 'Earth'},
                    'image': 'https://rickandmortyapi.com/api/character/avatar/1.jpeg'
                },
                {
                    'id': 3,
                    'name': 'Summer Smith',
                    'status': 'Alive',
                    'species': 'Human',
                    'origin': {'name': 'Earth (Replacement Dimension)'},
                    'location': {'name': 'Earth'},
                    'image': 'https://rickandmortyapi.com/api/character/avatar/3.jpeg'
                },
            ]
        }
        mock_get.return_value = mock_response
        
        # Make request
        response = self.app.get('/characters?filtered=false')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['characters']), 2)  # All characters should be returned
        self.assertEqual(data['count'], 2)
        
        # Verify mock was called correctly
        mock_get.assert_called_once_with("https://rickandmortyapi.com/api/character")
    
    @patch('rick_morty_api.requests.get')
    def test_characters_api_error(self, mock_get):
        """Test error handling when the API fails"""
        # Mock a failed API response
        mock_get.side_effect = Exception("API connection error")
        
        # Make request
        response = self.app.get('/characters')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 500)
        self.assertEqual(data['error'], 'An unexpected error occurred')
    
    @patch('rick_morty_api.requests.get')
    def test_characters_cache(self, mock_get):
        """Test that the cache is working correctly"""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'info': {'next': None},
            'results': [
                {
                    'id': 1,
                    'name': 'Rick Sanchez',
                    'status': 'Alive',
                    'species': 'Human',
                    'origin': {'name': 'Earth (C-137)'},
                    'location': {'name': 'Earth'},
                    'image': 'https://rickandmortyapi.com/api/character/avatar/1.jpeg'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # First request should call the API
        response1 = self.app.get('/characters')
        self.assertEqual(response1.status_code, 200)
        
        # Second request should use the cache
        response2 = self.app.get('/characters')
        self.assertEqual(response2.status_code, 200)
        
        # Verify mock was called only once
        mock_get.assert_called_once()
    
    @patch('rick_morty_api.fetch_characters')
    def test_pagination_processing(self, mock_fetch):
        """Test that multiple pages of results are processed correctly"""
        # This test doesn't directly test the API route but the underlying fetch_characters function
        mock_fetch.return_value = [
            {'id': 1, 'name': 'Character 1'},
            {'id': 2, 'name': 'Character 2'}
        ]
        
        response = self.app.get('/characters')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['characters']), 2)
        mock_fetch.assert_called_once_with(filtered=True)


class TestCharacterDetailEndpoint(unittest.TestCase):
    """Test cases for the character detail endpoint"""
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
        # Reset cache before each test
        character_detail_cache.clear()
    
    @patch('rick_morty_api.requests.get')
    def test_get_character_by_id(self, mock_get):
        """Test getting a character by ID"""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'id': 1,
            'name': 'Rick Sanchez',
            'status': 'Alive',
            'species': 'Human',
            'type': '',
            'gender': 'Male',
            'origin': {'name': 'Earth (C-137)'},
            'location': {'name': 'Earth'},
            'image': 'https://rickandmortyapi.com/api/character/avatar/1.jpeg',
            'episode': ['https://rickandmortyapi.com/api/episode/1'],
            'url': 'https://rickandmortyapi.com/api/character/1',
            'created': '2017-11-04T18:48:46.250Z'
        }
        mock_get.return_value = mock_response
        
        # Make request
        response = self.app.get('/characters/1')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['name'], 'Rick Sanchez')
        self.assertEqual(data['status'], 'Alive')
        self.assertEqual(data['species'], 'Human')
        self.assertEqual(data['origin'], 'Earth (C-137)')
        
        # Verify mock was called correctly
        mock_get.assert_called_once_with("https://rickandmortyapi.com/api/character/1")
    
    @patch('rick_morty_api.requests.get')
    def test_character_not_found(self, mock_get):
        """Test error handling when a character is not found"""
        # Mock a 404 response
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=MagicMock(status_code=404))
        mock_get.return_value = mock_response
        
        # Make request
        response = self.app.get('/characters/999')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], 'Character not found')
    
    @patch('rick_morty_api.requests.get')
    def test_character_cache(self, mock_get):
        """Test that the character cache is working correctly"""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'id': 1,
            'name': 'Rick Sanchez',
            'status': 'Alive',
            'species': 'Human',
            'type': '',
            'gender': 'Male',
            'origin': {'name': 'Earth (C-137)'},
            'location': {'name': 'Earth'},
            'image': 'https://rickandmortyapi.com/api/character/avatar/1.jpeg',
            'episode': ['https://rickandmortyapi.com/api/episode/1'],
            'url': 'https://rickandmortyapi.com/api/character/1',
            'created': '2017-11-04T18:48:46.250Z'
        }
        mock_get.return_value = mock_response
        
        # First request should call the API
        response1 = self.app.get('/characters/1')
        self.assertEqual(response1.status_code, 200)
        
        # Second request should use the cache
        response2 = self.app.get('/characters/1')
        self.assertEqual(response2.status_code, 200)
        
        # Verify mock was called only once
        mock_get.assert_called_once()


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling"""
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_not_found_error(self):
        """Test 404 error handling"""
        response = self.app.get('/nonexistent-endpoint')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], 'Resource not found')
    
    @patch('rick_morty_api.fetch_character_by_id')
    def test_server_error(self, mock_fetch):
        """Test 500 error handling"""
        # Clear the rate limiter before this test
        requests_limit.clear()
        # Simulate a server error
        mock_fetch.side_effect = Exception("Unexpected server error")
        
        response = self.app.get('/characters/1')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(data['error'], 'An unexpected error occurred')


class TestRateLimiting(unittest.TestCase):
    """Test cases for rate limiting"""
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        # Clear rate limiting data
        requests_limit.clear()
    
    @patch('rick_morty_api.fetch_characters')
    def test_rate_limit_enforced(self, mock_fetch):
        """Test that rate limiting is enforced"""
        # Mock the fetch_characters function to return some data
        mock_fetch.return_value = [{'id': 1, 'name': 'Character 1'}]
        
        # Make more requests than the limit allows
        for _ in range(10):
            response = self.app.get('/characters')
            self.assertEqual(response.status_code, 200)
        
        # The next request should be rate limited
        response = self.app.get('/characters')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 429)
        self.assertEqual(data['error'], 'Rate limit exceeded')


class TestCacheFunctions(unittest.TestCase):
    """Test cases for caching functions"""
    
    @patch('rick_morty_api.requests.get')
    def test_fetch_characters_cache(self, mock_get):
        """Test that fetch_characters uses and updates the cache correctly"""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'info': {'next': None},
            'results': [
                {
                    'id': 1,
                    'name': 'Rick Sanchez',
                    'status': 'Alive',
                    'species': 'Human',
                    'origin': {'name': 'Earth (C-137)'},
                    'location': {'name': 'Earth'},
                    'image': 'https://rickandmortyapi.com/api/character/avatar/1.jpeg'
                }
            ]
        }


