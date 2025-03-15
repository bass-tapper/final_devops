#!/usr/bin/env python3
"""
Prometheus metrics for the Rick and Morty API.

This module provides Prometheus metrics collection for monitoring the
Rick and Morty API wrapper, including request counts, response times,
cache statistics, and rate limiting information.
"""

import time
from typing import Callable, Any, Dict, Optional
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, Summary

# Request metrics
REQUEST_COUNT = Counter(
    'rickmorty_requests_total',
    'Total count of requests made to the Rick and Morty API',
    ['endpoint', 'method', 'status']
)

REQUEST_LATENCY = Histogram(
    'rickmorty_request_duration_seconds',
    'Time spent processing requests to the Rick and Morty API',
    ['endpoint', 'method'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
)

# Cache metrics
CACHE_HIT_COUNT = Counter(
    'rickmorty_cache_hits_total',
    'Total count of cache hits',
    ['endpoint']
)

CACHE_MISS_COUNT = Counter(
    'rickmorty_cache_misses_total',
    'Total count of cache misses',
    ['endpoint']
)

CACHE_SIZE = Gauge(
    'rickmorty_cache_size',
    'Current size of the cache',
    ['endpoint']
)

# Rate limit metrics
RATE_LIMIT_REMAINING = Gauge(
    'rickmorty_rate_limit_remaining',
    'Remaining requests before rate limit is reached',
)

RATE_LIMIT_RESET = Gauge(
    'rickmorty_rate_limit_reset_seconds',
    'Time in seconds until the rate limit resets',
)

RATE_LIMIT_DELAY = Histogram(
    'rickmorty_rate_limit_delay_seconds',
    'Time spent waiting due to rate limiting',
    buckets=(0.01, 0.1, 0.5, 1, 5, 10, 30, 60, 120)
)

# Error metrics
ERROR_COUNT = Counter(
    'rickmorty_errors_total',
    'Total count of errors encountered',
    ['endpoint', 'error_type']
)

# Summary for response size
RESPONSE_SIZE = Summary(
    'rickmorty_response_size_bytes',
    'Size of responses in bytes',
    ['endpoint']
)


def track_request_latency(endpoint: str, method: str = 'GET') -> Callable:
    """
    Decorator to track request latency for a given endpoint.
    
    Args:
        endpoint (str): The API endpoint being called
        method (str): The HTTP method used (default: 'GET')
        
    Returns:
        Callable: The decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                status = 'success'
                return result
            except Exception as e:
                status = 'error'
                ERROR_COUNT.labels(endpoint=endpoint, error_type=type(e).__name__).inc()
                raise
            finally:
                duration = time.time() - start_time
                REQUEST_COUNT.labels(endpoint=endpoint, method=method, status=status).inc()
                REQUEST_LATENCY.labels(endpoint=endpoint, method=method).observe(duration)
        return wrapper
    return decorator


def track_cache_metrics(endpoint: str, hit: bool, cache_size: int) -> None:
    """
    Update cache-related metrics.
    
    Args:
        endpoint (str): The API endpoint being accessed
        hit (bool): Whether this was a cache hit (True) or miss (False)
        cache_size (int): Current size of the cache
    """
    if hit:
        CACHE_HIT_COUNT.labels(endpoint=endpoint).inc()
    else:
        CACHE_MISS_COUNT.labels(endpoint=endpoint).inc()
    
    CACHE_SIZE.labels(endpoint=endpoint).set(cache_size)


def update_rate_limit_metrics(remaining: int, reset_time: float) -> None:
    """
    Update rate limit metrics based on API response headers.
    
    Args:
        remaining (int): Number of requests remaining before rate limit is reached
        reset_time (float): Unix timestamp when the rate limit will reset
    """
    RATE_LIMIT_REMAINING.set(remaining)
    
    # Calculate time until reset
    current_time = time.time()
    reset_seconds = max(0, reset_time - current_time)
    RATE_LIMIT_RESET.set(reset_seconds)


def record_rate_limit_delay(delay_seconds: float) -> None:
    """
    Record time spent waiting due to rate limiting.
    
    Args:
        delay_seconds (float): The time in seconds spent waiting
    """
    RATE_LIMIT_DELAY.observe(delay_seconds)


def record_response_size(endpoint: str, size_bytes: int) -> None:
    """
    Record the size of a response.
    
    Args:
        endpoint (str): The API endpoint that was called
        size_bytes (int): Size of the response in bytes
    """
    RESPONSE_SIZE.labels(endpoint=endpoint).observe(size_bytes)


def get_metrics_middleware():
    """
    Create a middleware function for Flask to track request metrics.
    
    Returns:
        Callable: A Flask middleware function
    """
    def middleware(app):
        @app.before_request
        def before_request():
            # Store start time in request context
            app.request.start_time = time.time()
            
        @app.after_request
        def after_request(response):
            # Calculate request duration
            duration = time.time() - app.request.start_time
            endpoint = app.request.endpoint or 'unknown'
            method = app.request.method
            
            # Update metrics
            REQUEST_COUNT.labels(
                endpoint=endpoint, 
                method=method, 
                status=response.status_code
            ).inc()
            REQUEST_LATENCY.labels(
                endpoint=endpoint, 
                method=method
            ).observe(duration)
            
            # Record response size if available
            if response.content_length:
                RESPONSE_SIZE.labels(endpoint=endpoint).observe(response.content_length)
                
            return response
    
    return middleware


def init_metrics_endpoint(app) -> None:
    """
    Initialize the metrics endpoint for the Flask application.
    
    This sets up a /metrics endpoint to expose Prometheus metrics.
    
    Args:
        app: The Flask application instance
    """
    from prometheus_client import make_wsgi_app
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    
    # Add metrics endpoint
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
        '/metrics': make_wsgi_app()
    })
    
    # Register metrics middleware
    metrics_middleware = get_metrics_middleware()
    metrics_middleware(app)
    
    print("Prometheus metrics initialized - available at /metrics endpoint")

