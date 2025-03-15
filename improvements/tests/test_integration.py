import pytest
import requests
import time
import json
from unittest import mock
from prometheus_client.parser import text_string_to_metric_families

# The base URL for the API. In a real test environment, this might point to a test server
BASE_URL = "http://localhost:5000"

@pytest.fixture
def api_client():
    """Fixture to provide a session for making requests to the API."""
    session = requests.Session()
    yield session
    session.close()

class TestAPIEndpoints:
    """Test the API endpoints for the Rick and Morty API wrapper."""
    
    def test_get_characters(self, api_client):
        """Test that the /characters endpoint returns a successful response."""
        response = api_client.get(f"{BASE_URL}/characters")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) > 0
        assert "name" in data["results"][0]
        
    def test_get_character_by_id(self, api_client):
        """Test that the /character/{id} endpoint returns the correct character."""
        character_id = 1  # Rick Sanchez
        response = api_client.get(f"{BASE_URL}/character/{character_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == character_id
        assert data["name"] == "Rick Sanchez"
        
    def test_get_locations(self, api_client):
        """Test that the /locations endpoint returns a successful response."""
        response = api_client.get(f"{BASE_URL}/locations")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) > 0
        
    def test_get_episodes(self, api_client):
        """Test that the /episodes endpoint returns a successful response."""
        response = api_client.get(f"{BASE_URL}/episodes")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) > 0
        
    def test_filter_characters(self, api_client):
        """Test filtering characters by query parameters."""
        response = api_client.get(f"{BASE_URL}/characters", params={"status": "Alive", "species": "Human"})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        # All returned characters should match the filter criteria
        for character in data["results"]:
            assert character["status"] == "Alive"
            assert character["species"] == "Human"
            
    def test_api_error_handling(self, api_client):
        """Test that the API properly handles errors for invalid requests."""
        # Test with an invalid character ID
        response = api_client.get(f"{BASE_URL}/character/99999")
        assert response.status_code == 404
        
        # Test with invalid endpoint
        response = api_client.get(f"{BASE_URL}/invalid_endpoint")
        assert response.status_code == 404


class TestCachingBehavior:
    """Test the caching mechanism of the API."""
    
    def test_cache_hit(self, api_client):
        """Test that repeated requests hit the cache."""
        # First request - should be a cache miss
        first_response = api_client.get(f"{BASE_URL}/character/1")
        assert first_response.status_code == 200
        assert "X-Cache" in first_response.headers
        assert first_response.headers["X-Cache"] == "MISS"
        
        # Second request to the same endpoint - should be a cache hit
        second_response = api_client.get(f"{BASE_URL}/character/1")
        assert second_response.status_code == 200
        assert "X-Cache" in second_response.headers
        assert second_response.headers["X-Cache"] == "HIT"
        
        # Response body should be the same
        assert first_response.json() == second_response.json()
    
    def test_cache_ttl(self, api_client):
        """Test that the cache expires after the TTL."""
        # This test assumes a short TTL (e.g., 5 seconds) for testing purposes
        # In a real application, you might mock time or use a test configuration with shorter TTL
        
        # First request - should be a cache miss
        first_response = api_client.get(f"{BASE_URL}/character/2", params={"cache_ttl": 1})
        assert first_response.headers["X-Cache"] == "MISS"
        
        # Immediate second request - should be a cache hit
        second_response = api_client.get(f"{BASE_URL}/character/2", params={"cache_ttl": 1})
        assert second_response.headers["X-Cache"] == "HIT"
        
        # Wait for the cache to expire
        time.sleep(1.5)
        
        # Third request after TTL expired - should be a cache miss again
        third_response = api_client.get(f"{BASE_URL}/character/2", params={"cache_ttl": 1})
        assert third_response.headers["X-Cache"] == "MISS"
    
    def test_different_query_params_different_cache(self, api_client):
        """Test that different query parameters result in different cache entries."""
        # Request with one set of query parameters
        first_response = api_client.get(f"{BASE_URL}/characters", params={"status": "Alive"})
        assert first_response.headers["X-Cache"] == "MISS"
        
        # Request with different query parameters should be a cache miss
        second_response = api_client.get(f"{BASE_URL}/characters", params={"status": "Dead"})
        assert second_response.headers["X-Cache"] == "MISS"
        
        # Repeat of first request should be a cache hit
        third_response = api_client.get(f"{BASE_URL}/characters", params={"status": "Alive"})
        assert third_response.headers["X-Cache"] == "HIT"


class TestRateLimiting:
    """Test the rate limiting functionality of the API."""
    
    def test_rate_limit_headers(self, api_client):
        """Test that rate limit headers are included in responses."""
        response = api_client.get(f"{BASE_URL}/character/1")
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        # Verify values make sense
        assert int(response.headers["X-RateLimit-Limit"]) > 0
        assert int(response.headers["X-RateLimit-Remaining"]) >= 0
        assert int(response.headers["X-RateLimit-Reset"]) > 0
    
    def test_rate_limit_exceeded(self, api_client):
        """Test that exceeding the rate limit returns 429 Too Many Requests."""
        # Set a very low rate limit for testing
        rate_limit = 3
        
        # Make requests until rate limit is reached
        for i in range(rate_limit):
            response = api_client.get(f"{BASE_URL}/character/{i+1}", 
                                      params={"rate_limit": rate_limit, "rate_limit_period": 60})
            assert response.status_code == 200
            remaining = int(response.headers["X-RateLimit-Remaining"])
            assert remaining == rate_limit - (i + 1)
        
        # One more request should trigger rate limit
        response = api_client.get(f"{BASE_URL}/character/1", 
                                  params={"rate_limit": rate_limit, "rate_limit_period": 60})
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        
        # Response body should explain the rate limit
        error_data = response.json()
        assert "error" in error_data
        assert "rate limit" in error_data["error"].lower()
    
    def test_rate_limit_reset(self, api_client):
        """Test that rate limit resets after the defined period."""
        # Set a very low rate limit and short period for testing
        rate_limit = 2
        period = 2  # 2 seconds
        
        # Make requests until rate limit is reached
        for i in range(rate_limit):
            response = api_client.get(f"{BASE_URL}/character/{i+1}", 
                                     params={"rate_limit": rate_limit, "rate_limit_period": period})
            assert response.status_code == 200
        
        # Next request should be rate limited
        response = api_client.get(f"{BASE_URL}/character/1", 
                                 params={"rate_limit": rate_limit, "rate_limit_period": period})
        assert response.status_code == 429
        
        # Wait for the rate limit period to pass
        time.sleep(period + 0.5)
        
        # We should be able to make requests again
        response = api_client.get(f"{BASE_URL}/character/1", 
                                 params={"rate_limit": rate_limit, "rate_limit_period": period})
        assert response.status_code == 200


class TestPrometheusMetrics:
    """Test the Prometheus metrics."""
    
    def test_metrics_endpoint(self, api_client):
        """Test that the /metrics endpoint returns proper Prometheus metrics."""
        response = api_client.get(f"{BASE_URL}/metrics")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/plain; version=0.0.4"
        
        # Basic validation of metrics content
        metrics_text = response.text
        assert "rick_morty_api_requests_total" in metrics_text
        assert "rick_morty_api_request_duration_seconds" in metrics_text
        assert "rick_morty_api_cache_hits_total" in metrics_text
        assert "rick_morty_api_cache_misses_total" in metrics_text
        assert "rick_morty_api_rate_limit_exceeded_total" in metrics_text
    
    @pytest.mark.parametrize("endpoint", [
        "/characters",
        "/character/1",
        "/locations",
        "/episodes"
    ])
    def test_request_metrics_incremented(self, api_client, endpoint):
        """Test that request metrics are incremented after API calls."""
        # Get initial metrics
        initial_metrics = api_client.get(f"{BASE_URL}/metrics").text
        
        # Make a request to the specified endpoint
        api_client.get(f"{BASE_URL}{endpoint}")
        
        # Get updated metrics
        updated_metrics = api_client.get(f"{BASE_URL}/metrics").text
        
        # Parse metrics to check counters
        initial_counters = {
            family.name: {sample.labels['endpoint']: sample.value 
                         for sample in family.samples if 'endpoint' in sample.labels}
            for family in text_string_to_metric_families(initial_metrics)
            if family.name == 'rick_morty_api_requests_total'
        }
        
        updated_counters = {
            family.name: {sample.labels['endpoint']: sample.value 
                         for sample in family.samples if 'endpoint' in sample.labels}
            for family in text_string_to_metric_families(updated_metrics)
            if family.name == 'rick_morty_api_requests_total'
        }
        
        # Check that the counter for this endpoint has incremented
        assert endpoint in updated_counters['rick_morty_api_requests_total']
        if endpoint in initial_counters.get('rick_morty_api_requests_total', {}):
            assert (updated_counters['rick_morty_api_requests_total'][endpoint] > 
                   initial_counters['rick_morty_api_requests_total'][endpoint])
        else:
            assert updated_counters['rick_morty_api_requests_total'][endpoint] > 0
    
    def test_cache_metrics(self, api_client):
        """Test that cache hit/miss metrics are updated correctly."""
        # Get initial metrics
        initial_metrics = api_client.get(f"{BASE_URL}/metrics").text
        
        # Make a request that should miss cache
        api_client.get(f"{BASE_URL}/character/1")
        
        # Make the same request again to hit cache
        api_client.get(f"{BASE_URL}/character/1")
        
        # Get updated metrics
        updated_metrics = api_client.get(f"{BASE_URL}/metrics").text
        
        # Parse metrics to check counters
        initial_cache = {
            family.name: sum(sample.value for sample in family.samples)
            for family in text_string_to_metric_families(initial_metrics)
            if family.name in ['rick_morty_api_cache_hits_total', 'rick_morty_api_cache_misses_total']
        }
        
        updated_cache = {
            family.name: sum(sample.value for sample in family.samples)
            for family in text_string_to_metric_families(updated_metrics)
            if family.name in ['rick_morty_api_cache_hits_total', 'rick_morty_api_cache_misses_total']
        }
        
        # Check cache hit/miss metrics have incremented appropriately
        if 'rick_morty_api_cache_misses_total' in initial_cache:
            assert (updated_cache['rick_morty_api_cache_misses_total'] > 
                   initial_cache['rick_morty_api_cache_misses_total'])
        else:
            assert updated_cache['rick_morty_api_cache_misses_total'] > 0
            
        if 'rick_morty_api_cache_hits_total' in initial_cache:
            assert (updated_cache['rick_morty_api_cache_hits_total'] > 
                   initial_cache['rick_morty_api_cache_hits_total'])
        else:
            assert updated_cache['rick_morty_api_cache_hits_total'] > 0
    
    def test_rate_limit_metrics(self, api_client):
        """Test that rate limit metrics are updated when rate limit is exceeded."""
        # Get initial metrics
        initial_metrics = api_client.get(f"{BASE_URL}/metrics").text
        
        # Set a very low rate limit and exhaust it
        rate_limit = 2
        for i in range(rate_limit):
            api_client.get(f"{BASE_URL}/character/{i+1}", 
                          params={"rate_limit": rate_limit, "rate_limit_period": 60})
        
        # This request should exceed rate limit
        api_client.get(f"{BASE_URL}/character/1", 
                      params={"rate_limit": rate_limit, "rate_limit_period": 60})
        
        # Get updated metrics
        updated_metrics = api_client.get(f"{BASE_URL}/metrics").text
        
        # Parse metrics to check rate limit counter
        initial_rate_limits = {
            family.name: sum(sample.value for sample in family.samples)
            for family

