"""Simple file-based cache for API responses."""
import json
import time
from pathlib import Path
from typing import Optional, Any


class SimpleCache:
    """Simple file-based cache with TTL."""

    def __init__(self, cache_dir: Optional[Path] = None, ttl: int = 300):
        """Initialize cache.

        Args:
            cache_dir: Directory for cache files (default: ~/.cache/render-dashboard)
            ttl: Time to live in seconds (default: 300 = 5 minutes)
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "render-dashboard"

        self.cache_dir = cache_dir
        self.ttl = ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a key."""
        # Simple key sanitization
        safe_key = key.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r") as f:
                data = json.load(f)

            # Check if expired
            if time.time() - data["timestamp"] > self.ttl:
                # Expired, delete cache file
                cache_path.unlink()
                return None

            return data["value"]

        except (json.JSONDecodeError, KeyError, IOError):
            # Corrupted cache file, delete it
            if cache_path.exists():
                cache_path.unlink()
            return None

    def set(self, key: str, value: Any) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
        """
        cache_path = self._get_cache_path(key)

        data = {
            "timestamp": time.time(),
            "value": value
        }

        try:
            with open(cache_path, "w") as f:
                json.dump(data, f)
        except (IOError, TypeError):
            # Failed to cache, ignore
            pass

    def clear(self, key: Optional[str] = None) -> None:
        """Clear cache.

        Args:
            key: If provided, clear specific key. Otherwise clear all cache.
        """
        if key:
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                cache_path.unlink()
        else:
            # Clear all cache files
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
