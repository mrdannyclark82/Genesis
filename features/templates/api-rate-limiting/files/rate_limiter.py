"""API Rate Limiting implementation using Flask-Limiter."""

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
from typing import Optional


class RateLimiter:
    """Rate limiting for API endpoints."""
    
    def __init__(self, app: Optional[Flask] = None, redis_url: str = "redis://localhost:6379"):
        """Initialize rate limiter with optional Flask app."""
        self.redis_client = None
        self.limiter = None
        
        if app:
            self.init_app(app, redis_url)
    
    def init_app(self, app: Flask, redis_url: str = "redis://localhost:6379"):
        """Initialize rate limiter with Flask app."""
        try:
            # Try to connect to Redis
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()  # Test connection
            
            # Initialize Flask-Limiter with Redis storage
            self.limiter = Limiter(
                app,
                key_func=get_remote_address,
                storage_uri=redis_url,
                default_limits=["200 per day", "50 per hour"]
            )
            
        except redis.ConnectionError:
            # Fallback to in-memory storage if Redis is not available
            print("Warning: Redis not available, using in-memory rate limiting")
            self.limiter = Limiter(
                app,
                key_func=get_remote_address,
                default_limits=["200 per day", "50 per hour"]
            )
        
        # Set up error handler
        @app.errorhandler(429)
        def ratelimit_handler(e):
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': str(e.description),
                'retry_after': getattr(e, 'retry_after', None)
            }), 429
    
    def limit(self, rate: str):
        """Decorator for applying rate limits to specific endpoints."""
        if self.limiter:
            return self.limiter.limit(rate)
        else:
            # Return no-op decorator if limiter not initialized
            def decorator(f):
                return f
            return decorator


# Example usage:
"""
from flask import Flask
from rate_limiter import RateLimiter

app = Flask(__name__)
rate_limiter = RateLimiter(app)

@app.route('/api/data')
@rate_limiter.limit("10 per minute")
def get_data():
    return jsonify({'data': 'example'})

@app.route('/api/upload')
@rate_limiter.limit("5 per minute")
def upload_data():
    return jsonify({'status': 'uploaded'})

if __name__ == '__main__':
    app.run(debug=True)
"""