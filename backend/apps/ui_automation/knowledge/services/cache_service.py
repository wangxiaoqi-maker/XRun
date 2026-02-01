"""
简单内存缓存服务

用于缓存不频繁变化的数据（如统计信息），减少数据库查询
"""
import time
from typing import Any, Optional, Dict, Callable
from functools import wraps
import asyncio
from loguru import logger


class CacheEntry:
    """缓存条目"""
    __slots__ = ['value', 'expire_at']
    
    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.expire_at = time.time() + ttl
    
    @property
    def is_expired(self) -> bool:
        return time.time() > self.expire_at


class SimpleCache:
    """
    简单内存缓存
    
    特点：
    - 基于 TTL 过期
    - 线程安全（使用 asyncio.Lock）
    - 支持手动失效
    """
    
    _instance: Optional['SimpleCache'] = None
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls) -> 'SimpleCache':
        """获取单例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            if entry.is_expired:
                del self._cache[key]
                return None
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: int = 60) -> None:
        """设置缓存值"""
        async with self._lock:
            self._cache[key] = CacheEntry(value, ttl)
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        根据模式失效缓存
        
        Args:
            pattern: 前缀模式（如 "stats:" 会删除所有以 stats: 开头的键）
        
        Returns:
            删除的数量
        """
        async with self._lock:
            keys_to_delete = [k for k in self._cache if k.startswith(pattern)]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)
    
    async def clear(self) -> None:
        """清空所有缓存"""
        async with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        now = time.time()
        valid_count = sum(1 for e in self._cache.values() if not e.is_expired)
        return {
            "total_keys": len(self._cache),
            "valid_keys": valid_count,
            "expired_keys": len(self._cache) - valid_count
        }


# ========== 缓存键常量 ==========
class CacheKeys:
    """缓存键定义"""
    STATS = "stats:global"
    APPS_LIST = "apps:list:{platform}:{offset}:{limit}"
    PAGES_UNIQUE = "pages:unique:{offset}:{limit}:{app_name}"


# ========== 装饰器 ==========
def cached(key_template: str, ttl: int = 60):
    """
    缓存装饰器
    
    Args:
        key_template: 缓存键模板，支持 {参数名} 占位符
        ttl: 过期时间（秒）
    
    Usage:
        @cached("stats:global", ttl=30)
        async def get_stats():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = SimpleCache.get_instance()
            
            # 构建缓存键
            cache_key = key_template
            if kwargs:
                cache_key = key_template.format(**{k: v or 'none' for k, v in kwargs.items()})
            
            # 尝试获取缓存
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"[Cache HIT] {cache_key}")
                return cached_value
            
            # 执行原函数
            logger.debug(f"[Cache MISS] {cache_key}")
            result = await func(*args, **kwargs)
            
            # 存入缓存
            await cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


def get_cache() -> SimpleCache:
    """获取缓存实例"""
    return SimpleCache.get_instance()


async def invalidate_stats_cache():
    """失效统计缓存（数据变化时调用）"""
    cache = get_cache()
    count = await cache.invalidate_pattern("stats:")
    if count > 0:
        logger.debug(f"[Cache] Invalidated {count} stats cache entries")


async def invalidate_pages_cache():
    """失效页面缓存"""
    cache = get_cache()
    count = await cache.invalidate_pattern("pages:")
    if count > 0:
        logger.debug(f"[Cache] Invalidated {count} pages cache entries")


async def invalidate_apps_cache():
    """失效应用缓存"""
    cache = get_cache()
    count = await cache.invalidate_pattern("apps:")
    if count > 0:
        logger.debug(f"[Cache] Invalidated {count} apps cache entries")
