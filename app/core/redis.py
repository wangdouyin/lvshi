"""
Redis 连接配置
"""
import redis

from app.core.config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB

# 创建 Redis 连接池
pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=REDIS_DB,
    decode_responses=True
)

# Redis 客户端
redis_client = redis.Redis(connection_pool=pool)


def get_redis() -> redis.Redis:
    """获取 Redis 客户端"""
    return redis_client
