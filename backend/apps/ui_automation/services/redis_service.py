"""
Redis 服务 - 解决多进程数据共享问题

核心功能：
1. 执行状态共享（替代内存 execution_cache）
2. Pub/Sub 实时消息推送
3. 设备状态同步
4. 分布式锁
"""
import json
import asyncio
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
import redis.asyncio as redis
from contextlib import asynccontextmanager
from loguru import logger


class RedisService:
    """
    Redis 服务单例
    
    支持两种模式：
    1. Redis 可用时：使用 Redis 存储
    2. Redis 不可用时：降级为内存存储（开发模式）
    """
    
    _instance: Optional['RedisService'] = None
    
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._fallback_cache: Dict[str, Any] = {}  # 降级用内存缓存
        self._use_fallback = False
        self._subscribers: Dict[str, List[Callable]] = {}
        
    @classmethod
    def get_instance(cls) -> 'RedisService':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def connect(
        self, 
        host: str = "localhost", 
        port: int = 6379, 
        db: int = 0,
        password: Optional[str] = None
    ):
        """
        连接 Redis
        
        如果连接失败，自动降级为内存模式
        """
        try:
            self._redis = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # 测试连接
            await self._redis.ping()
            self._use_fallback = False
            logger.info(f"✅ Redis 连接成功: {host}:{port}")
        except Exception as e:
            logger.warning(f"⚠️ Redis 连接失败，降级为内存模式: {e}")
            self._use_fallback = True
            self._redis = None
    
    async def disconnect(self):
        """断开连接"""
        if self._pubsub:
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()
    
    @property
    def is_connected(self) -> bool:
        return self._redis is not None and not self._use_fallback
    
    # ==================== 执行状态管理 ====================
    
    async def set_execution_status(
        self, 
        execution_id: str, 
        status: str,
        logs: Optional[List[str]] = None,
        finished: bool = False,
        error_message: Optional[str] = None,
        ttl: int = 3600  # 1小时过期
    ):
        """
        设置执行状态
        
        同时发布状态变更事件
        """
        data = {
            "status": status,
            "logs": logs or [],
            "finished": finished,
            "error_message": error_message,
            "updated_at": datetime.now().isoformat()
        }
        
        key = f"execution:{execution_id}"
        
        if self._use_fallback:
            self._fallback_cache[key] = data
        else:
            await self._redis.setex(key, ttl, json.dumps(data))
            # 发布状态变更事件
            await self._redis.publish(
                f"execution:{execution_id}:events",
                json.dumps({"type": "status_update", "data": data})
            )
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict]:
        """获取执行状态"""
        key = f"execution:{execution_id}"
        
        if self._use_fallback:
            return self._fallback_cache.get(key)
        
        data = await self._redis.get(key)
        return json.loads(data) if data else None
    
    async def append_execution_log(
        self, 
        execution_id: str, 
        log_entry: str,
        ttl: int = 3600
    ):
        """
        追加执行日志
        
        使用 Redis List 实现高效追加
        """
        key = f"execution:{execution_id}:logs"
        event_channel = f"execution:{execution_id}:events"
        
        if self._use_fallback:
            status_key = f"execution:{execution_id}"
            if status_key not in self._fallback_cache:
                self._fallback_cache[status_key] = {"logs": [], "status": "pending"}
            self._fallback_cache[status_key]["logs"].append(log_entry)
        else:
            await self._redis.rpush(key, log_entry)
            await self._redis.expire(key, ttl)
            # 发布日志事件
            await self._redis.publish(
                event_channel,
                json.dumps({"type": "log", "data": log_entry})
            )
    
    async def get_execution_logs(self, execution_id: str) -> List[str]:
        """获取所有执行日志"""
        key = f"execution:{execution_id}:logs"
        
        if self._use_fallback:
            status_key = f"execution:{execution_id}"
            cache = self._fallback_cache.get(status_key, {})
            return cache.get("logs", [])
        
        return await self._redis.lrange(key, 0, -1)
    
    # ==================== Pub/Sub 实时推送 ====================
    
    async def subscribe_execution(
        self, 
        execution_id: str,
        callback: Callable[[Dict], Any]
    ):
        """
        订阅执行事件
        
        用于 WebSocket 实时推送
        """
        channel = f"execution:{execution_id}:events"
        
        if self._use_fallback:
            # 降级模式：使用本地回调
            if channel not in self._subscribers:
                self._subscribers[channel] = []
            self._subscribers[channel].append(callback)
            return
        
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(channel)
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    await callback(data)
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
    
    @asynccontextmanager
    async def execution_subscriber(self, execution_id: str):
        """
        执行事件订阅器（上下文管理器）
        
        Usage:
            async with redis_service.execution_subscriber(exec_id) as subscriber:
                async for event in subscriber:
                    await websocket.send_json(event)
        """
        channel = f"execution:{execution_id}:events"
        
        if self._use_fallback:
            # 降级模式：轮询
            yield self._fallback_poll_generator(execution_id)
            return
        
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(channel)
        
        async def event_generator():
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        yield json.loads(message["data"])
            except asyncio.CancelledError:
                pass
        
        try:
            yield event_generator()
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
    
    async def _fallback_poll_generator(self, execution_id: str):
        """降级模式的轮询生成器"""
        last_log_count = 0
        key = f"execution:{execution_id}"
        
        while True:
            cache = self._fallback_cache.get(key, {})
            logs = cache.get("logs", [])
            
            # 发送新日志
            if len(logs) > last_log_count:
                for log in logs[last_log_count:]:
                    yield {"type": "log", "data": log}
                last_log_count = len(logs)
            
            # 发送状态
            yield {"type": "status_update", "data": cache}
            
            if cache.get("finished"):
                yield {"type": "finished"}
                break
            
            await asyncio.sleep(0.3)
    
    # ==================== 设备状态管理 ====================
    
    async def set_device_status(
        self, 
        device_id: str, 
        status: Dict[str, Any],
        ttl: int = 300  # 5分钟过期
    ):
        """设置设备状态"""
        key = f"device:{device_id}"
        
        if self._use_fallback:
            self._fallback_cache[key] = status
        else:
            await self._redis.setex(key, ttl, json.dumps(status))
    
    async def get_device_status(self, device_id: str) -> Optional[Dict]:
        """获取设备状态"""
        key = f"device:{device_id}"
        
        if self._use_fallback:
            return self._fallback_cache.get(key)
        
        data = await self._redis.get(key)
        return json.loads(data) if data else None
    
    async def get_all_devices(self) -> List[Dict]:
        """获取所有设备状态"""
        if self._use_fallback:
            return [
                v for k, v in self._fallback_cache.items() 
                if k.startswith("device:")
            ]
        
        keys = await self._redis.keys("device:*")
        devices = []
        for key in keys:
            data = await self._redis.get(key)
            if data:
                devices.append(json.loads(data))
        return devices
    
    # ==================== 分布式锁 ====================
    
    @asynccontextmanager
    async def lock(
        self, 
        name: str, 
        timeout: int = 10,
        blocking_timeout: int = 5
    ):
        """
        分布式锁
        
        防止多实例重复执行同一任务
        
        Usage:
            async with redis_service.lock(f"execution:{exec_id}"):
                # 执行任务
        """
        lock_key = f"lock:{name}"
        lock_value = datetime.now().isoformat()
        acquired = False
        
        if self._use_fallback:
            # 降级模式：直接执行（单进程无需锁）
            yield
            return
        
        try:
            # 尝试获取锁
            acquired = await self._redis.set(
                lock_key, 
                lock_value, 
                nx=True, 
                ex=timeout
            )
            
            if not acquired:
                # 等待锁释放
                for _ in range(blocking_timeout * 10):
                    await asyncio.sleep(0.1)
                    acquired = await self._redis.set(
                        lock_key, 
                        lock_value, 
                        nx=True, 
                        ex=timeout
                    )
                    if acquired:
                        break
            
            if not acquired:
                raise TimeoutError(f"获取锁 {name} 超时")
            
            yield
            
        finally:
            if acquired:
                await self._redis.delete(lock_key)
    
    # ==================== 通用方法 ====================
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """通用设置"""
        if self._use_fallback:
            self._fallback_cache[key] = value
        else:
            if ttl:
                await self._redis.setex(key, ttl, json.dumps(value))
            else:
                await self._redis.set(key, json.dumps(value))
    
    async def get(self, key: str) -> Optional[Any]:
        """通用获取"""
        if self._use_fallback:
            return self._fallback_cache.get(key)
        
        data = await self._redis.get(key)
        return json.loads(data) if data else None
    
    async def delete(self, key: str):
        """删除键"""
        if self._use_fallback:
            self._fallback_cache.pop(key, None)
        else:
            await self._redis.delete(key)
    
    async def clear_execution(self, execution_id: str):
        """清理执行相关的所有数据"""
        keys = [
            f"execution:{execution_id}",
            f"execution:{execution_id}:logs"
        ]
        
        if self._use_fallback:
            for key in keys:
                self._fallback_cache.pop(key, None)
        else:
            await self._redis.delete(*keys)


# 全局实例
redis_service = RedisService.get_instance()


async def init_redis(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None
):
    """
    初始化 Redis 连接
    
    在 FastAPI 启动时调用
    """
    await redis_service.connect(host, port, db, password)


async def close_redis():
    """
    关闭 Redis 连接
    
    在 FastAPI 关闭时调用
    """
    await redis_service.disconnect()
