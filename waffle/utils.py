from __future__ import annotations

import hashlib
import logging
from typing import Any

from django.conf import settings
from django.core.cache import BaseCache, caches

import waffle
from waffle import defaults

logger = logging.getLogger('waffle')


def get_setting(name: str, default: Any = None) -> Any:
    try:
        return getattr(settings, 'WAFFLE_' + name)
    except AttributeError:
        return getattr(defaults, name, default)


def keyfmt(k: str, v: str | None = None) -> str:
    prefix = get_setting('CACHE_PREFIX') + waffle.__version__
    if v is None:
        key = prefix + k
    else:
        key = prefix + hashlib.md5((k % v).encode('utf-8')).hexdigest()
    return key


def get_cache() -> BaseCache:
    CACHE_NAME = get_setting('CACHE_NAME')
    return caches[CACHE_NAME]


def _get_retries(retries: int | None) -> int:
    if retries is not None:
        return retries
    return get_setting('CACHE_RETRIES')


def cache_get(cache: BaseCache, key: str, retries: int | None = None) -> Any:
    if not get_setting('CACHE_FAILOVER'):
        return cache.get(key)
    max_retries = _get_retries(retries)
    for attempt in range(1 + max_retries):
        try:
            return cache.get(key)
        except Exception:
            logger.warning(
                'Cache get failed for key %s (attempt %d/%d)',
                key, attempt + 1, 1 + max_retries, exc_info=True,
            )
    return None


def cache_set(cache: BaseCache, key: str, value: Any, retries: int | None = None) -> None:
    if not get_setting('CACHE_FAILOVER'):
        cache.set(key, value)
        return
    max_retries = _get_retries(retries)
    for attempt in range(1 + max_retries):
        try:
            cache.set(key, value)
            return
        except Exception:
            logger.warning(
                'Cache set failed for key %s (attempt %d/%d)',
                key, attempt + 1, 1 + max_retries, exc_info=True,
            )


def cache_add(cache: BaseCache, key: str, value: Any, retries: int | None = None) -> None:
    if not get_setting('CACHE_FAILOVER'):
        cache.add(key, value)
        return
    max_retries = _get_retries(retries)
    for attempt in range(1 + max_retries):
        try:
            cache.add(key, value)
            return
        except Exception:
            logger.warning(
                'Cache add failed for key %s (attempt %d/%d)',
                key, attempt + 1, 1 + max_retries, exc_info=True,
            )


def cache_delete(cache: BaseCache, key: str, retries: int | None = None) -> None:
    if not get_setting('CACHE_FAILOVER'):
        cache.delete(key)
        return
    max_retries = _get_retries(retries)
    for attempt in range(1 + max_retries):
        try:
            cache.delete(key)
            return
        except Exception:
            logger.warning(
                'Cache delete failed for key %s (attempt %d/%d)',
                key, attempt + 1, 1 + max_retries, exc_info=True,
            )


def cache_delete_many(cache: BaseCache, keys: list[str], retries: int | None = None) -> None:
    if not get_setting('CACHE_FAILOVER'):
        cache.delete_many(keys)
        return
    max_retries = _get_retries(retries)
    for attempt in range(1 + max_retries):
        try:
            cache.delete_many(keys)
            return
        except Exception:
            logger.warning(
                'Cache delete_many failed for keys %s (attempt %d/%d)',
                keys, attempt + 1, 1 + max_retries, exc_info=True,
            )
