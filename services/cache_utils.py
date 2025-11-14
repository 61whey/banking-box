"""
Cache utilities for FastAPI-Cache
"""
from typing import Any, Optional
from fastapi import Request, Response
from redis import asyncio as aioredis


def client_key_builder(
    func,
    namespace: str = "",
    *,
    request: Request = None,
    response: Response = None,
    args: tuple = (),
    kwargs: dict = None,
) -> str:
    """
    Custom key builder for caching that includes the client_id.

    This ensures each user gets their own cached data for external accounts.

    Key format: namespace:function_name:client_id
    Example: banking-box:get_external_accounts:CLIENT123
    """
    kwargs = kwargs or {}
    
    # Extract client_id from kwargs (passed from get_current_client dependency)
    current_client = kwargs.get("current_client", {})
    client_id = current_client.get("client_id", "unknown")
    
    # Build cache key
    cache_key = f"{namespace}:{func.__name__}:client:{client_id}"
    
    return cache_key


def client_page_key_builder(
    func,
    namespace: str = "",
    *,
    request: Request = None,
    response: Response = None,
    args: tuple = (),
    kwargs: dict = None,
) -> str:
    """
    Custom key builder for caching that includes the client_id and page number.
    
    This ensures each user gets their own cached data for paginated endpoints,
    with different cache entries for each page.

    Key format: namespace:function_name:client:{client_id}:page:{page}
    Example: banking-box:get_external_payment_history:client:CLIENT123:page:1
    """
    kwargs = kwargs or {}
    
    # Extract client_id from kwargs (passed from get_current_client dependency)
    current_client = kwargs.get("current_client", {})
    client_id = current_client.get("client_id", "unknown")
    
    # Extract page number from kwargs
    page = kwargs.get("page", 1)
    
    # Build cache key
    cache_key = f"{namespace}:{func.__name__}:client:{client_id}:page:{page}"
    
    return cache_key


async def invalidate_client_cache(redis_client: aioredis.Redis, client_id: str, namespace: str = "banking-box"):
    """
    Invalidate all cached data for a specific client.

    Args:
        redis_client: Async Redis client instance
        client_id: Client's person_id
        namespace: Cache namespace (default: banking-box)

    Usage:
        await invalidate_client_cache(redis_client, "CLIENT123")
    """
    pattern = f"{namespace}:*:client:{client_id}"

    # Find all keys matching the pattern
    keys = []
    async for key in redis_client.scan_iter(match=pattern):
        keys.append(key)

    # Delete all matching keys
    if keys:
        await redis_client.delete(*keys)
        return len(keys)

    return 0


async def invalidate_all_cache(redis_client: aioredis.Redis, namespace: str = "banking-box"):
    """
    Invalidate all cached data in the namespace.

    Args:
        redis_client: Async Redis client instance
        namespace: Cache namespace (default: banking-box)

    Usage:
        await invalidate_all_cache(redis_client)
    """
    pattern = f"{namespace}:*"

    # Find all keys matching the pattern
    keys = []
    async for key in redis_client.scan_iter(match=pattern):
        keys.append(key)

    # Delete all matching keys
    if keys:
        await redis_client.delete(*keys)
        return len(keys)

    return 0
