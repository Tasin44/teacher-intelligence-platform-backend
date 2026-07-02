"""
Shared utilities:
 - cache key builders + invalidation helpers (per-teacher namespacing)
 - a binary-search helper used for O(log n) title-prefix lookups on
   pre-sorted, cached assignment title indexes (DSA requirement)
"""
from django.core.cache import cache

CACHE_TTL_DASHBOARD = 120       # seconds
CACHE_TTL_LISTS = 60
CACHE_VERSION_PREFIX = "tver"   # per-teacher cache version, used to bulk-invalidate


def teacher_cache_version(teacher_id: int) -> int:
    key = f"{CACHE_VERSION_PREFIX}:{teacher_id}"
    version = cache.get(key)
    if version is None:
        version = 1
        cache.set(key, version, timeout=None)
    return version

def bump_teacher_cache_version(teacher_id: int) -> None:
    """Call this on any write that affects a teacher's dashboard/list caches.
    Cheap O(1) invalidation instead of deleting many individual keys."""
    key = f"{CACHE_VERSION_PREFIX}:{teacher_id}"
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 2, timeout=None)


def scoped_cache_key(teacher_id: int, name: str) -> str:
    return f"{name}:t{teacher_id}:v{teacher_cache_version(teacher_id)}"


def binary_search_title_prefix(sorted_titles: list, prefix: str) -> int:
    """
    Returns the left-most index in `sorted_titles` (sorted ascending,
    case-insensitive) whose title starts with `prefix`, or -1 if none.
    O(log n) instead of O(n) linear scan -- used when searching assignments
    by title across large datasets pulled from cache.
    """
    prefix = prefix.lower()
    lo, hi = 0, len(sorted_titles)
    while lo < hi:
        mid = (lo + hi) // 2
        if sorted_titles[mid].lower() < prefix:
            lo = mid + 1
        else:
            hi = mid
    if lo < len(sorted_titles) and sorted_titles[lo].lower().startswith(prefix):
        return lo
    return -1
