"""Redis client with connection pooling and error handling."""

import json
import logging
from datetime import timedelta
from typing import Any, Optional

import redis
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from app.config import get_settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client with connection pooling and robust error handling."""

    def __init__(self):
        """Initialize Redis client with connection pool."""
        settings = get_settings()

        self._pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            db=settings.redis_db,
            max_connections=settings.redis_max_connections,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )

        self._client: Optional[redis.Redis] = None
        self._ttl = settings.redis_ttl

    @property
    def client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.Redis(connection_pool=self._pool)
        return self._client

    def get(self, key: str) -> Optional[dict]:
        """Get value from Redis.

        Args:
            key: Redis key

        Returns:
            Dictionary value or None if not found
        """
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error getting key '{key}': {e}")
            return None

    def set(
        self,
        key: str,
        value: dict,
        ex: Optional[int] = None
    ) -> bool:
        """Set value in Redis with optional expiration.

        Args:
            key: Redis key
            value: Dictionary value to store
            ex: Expiration time in seconds (defaults to settings.redis_ttl)

        Returns:
            True if successful, False otherwise
        """
        try:
            ttl = ex if ex is not None else self._ttl
            self.client.setex(
                key,
                timedelta(seconds=ttl),
                json.dumps(value)
            )
            return True
        except (RedisError, TypeError) as e:
            logger.error(f"Error setting key '{key}': {e}")
            return False

    def update(self, key: str, updates: dict) -> bool:
        """Update existing key with partial data.

        Args:
            key: Redis key
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            current = self.get(key)
            if current is None:
                logger.warning(f"Key '{key}' not found for update")
                return False

            current.update(updates)
            return self.set(key, current)
        except Exception as e:
            logger.error(f"Error updating key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from Redis.

        Args:
            key: Redis key

        Returns:
            True if key was deleted, False otherwise
        """
        try:
            return bool(self.client.delete(key))
        except RedisError as e:
            logger.error(f"Error deleting key '{key}': {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in Redis.

        Args:
            key: Redis key

        Returns:
            True if key exists, False otherwise
        """
        try:
            return bool(self.client.exists(key))
        except RedisError as e:
            logger.error(f"Error checking key '{key}': {e}")
            return False

    def ping(self) -> bool:
        """Check Redis connection health.

        Returns:
            True if Redis is responsive, False otherwise
        """
        try:
            return self.client.ping()
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    def get_queue_depth(self, queue_name: str) -> int:
        """Get the number of items in a Redis list queue.

        Args:
            queue_name: Name of the queue

        Returns:
            Number of items in queue
        """
        try:
            return self.client.llen(queue_name)
        except RedisError as e:
            logger.error(f"Error getting queue depth for '{queue_name}': {e}")
            return 0

    def close(self):
        """Close Redis connection pool."""
        if self._client:
            self._client.close()
        if self._pool:
            self._pool.disconnect()


# Global Redis client instance
_redis_client: Optional[RedisClient] = None


def get_redis() -> RedisClient:
    """Get or create global Redis client instance.

    Returns:
        RedisClient: Global Redis client
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client
