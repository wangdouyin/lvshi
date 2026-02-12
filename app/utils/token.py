"""
Token 管理工具
基于 Redis 实现 Token 的生成、验证、删除
"""
import uuid
import json
from typing import Optional, Any

from app.core.redis import redis_client
from app.core.config import TOKEN_EXPIRE_SECONDS






class TokenManager:
    """
    Token 管理器
    
    使用方法:
        # 生成 token
        token = TokenManager.generate(account_id=1, account_type=2)
        
        # 验证 token
        data = TokenManager.verify(token)
        if data:
            account_id = data.get("account_id")
        
        # 删除 token
        TokenManager.delete(token)
        
        # 刷新 token 过期时间
        TokenManager.refresh(token)
    """
    
    # Token 前缀
    TOKEN_PREFIX = "token:"
    # 用户 Token 映射前缀（用于踢出旧登录）
    USER_TOKEN_PREFIX = "user_token:"
    
    @classmethod
    def _get_token_key(cls, token: str) -> str:
        """获取 Token 在 Redis 中的 key"""
        return f"{cls.TOKEN_PREFIX}{token}"
    
    @classmethod
    def _get_user_token_key(cls, account_id: int) -> str:
        """获取用户 Token 映射的 key"""
        return f"{cls.USER_TOKEN_PREFIX}{account_id}"
    
    @classmethod
    def generate(
        cls,
        account_id: int,
        account_type: int = 1,
        extra_data: Optional[dict] = None,
        expire_seconds: int = None,
        single_login: bool = False
    ) -> str:
        """
        生成 Token
        
        :param account_id: 账号ID
        :param account_type: 账号类型 (0主任 1客户 2律师 3参与者)
        :param extra_data: 额外数据
        :param expire_seconds: 过期时间（秒），默认使用配置
        :param single_login: 是否单点登录（踢出旧登录）
        :return: token 字符串
        """
        if expire_seconds is None:
            expire_seconds = TOKEN_EXPIRE_SECONDS
        
        # 单点登录：删除该用户的旧 token
        if single_login:
            cls.delete_by_account(account_id)
        
        # 生成新 token
        token = uuid.uuid4().hex
        
        # 存储数据
        data = {
            "account_id": account_id,
            "account_type": account_type,
            **(extra_data or {})
        }
        
        token_key = cls._get_token_key(token)
        user_token_key = cls._get_user_token_key(account_id)
        
        # 存储 token -> 用户数据
        redis_client.setex(token_key, expire_seconds, json.dumps(data))
        
        # 存储 用户ID -> token（用于单点登录）
        redis_client.setex(user_token_key, expire_seconds, token)
        
        return token
    
    @classmethod
    def verify(cls, token: str) -> Optional[dict]:
        """
        验证 Token
        
        :param token: token 字符串
        :return: 用户数据字典，无效则返回 None
        """
        if not token:
            return None
        
        token_key = cls._get_token_key(token)
        data = redis_client.get(token_key)
        
        if data:
            return json.loads(data)
        return None
    
    @classmethod
    def delete(cls, token: str) -> bool:
        """
        删除 Token
        
        :param token: token 字符串
        :return: 是否删除成功
        """
        if not token:
            return False
        
        # 先获取用户数据，以便删除用户 token 映射
        data = cls.verify(token)
        if data:
            account_id = data.get("account_id")
            if account_id:
                user_token_key = cls._get_user_token_key(account_id)
                redis_client.delete(user_token_key)
        
        token_key = cls._get_token_key(token)
        return redis_client.delete(token_key) > 0
    
    @classmethod
    def delete_by_account(cls, account_id: int) -> bool:
        """
        根据账号ID删除 Token（用于踢出登录）
        
        :param account_id: 账号ID
        :return: 是否删除成功
        """
        user_token_key = cls._get_user_token_key(account_id)
        old_token = redis_client.get(user_token_key)
        
        if old_token:
            token_key = cls._get_token_key(old_token)
            redis_client.delete(token_key)
            redis_client.delete(user_token_key)
            return True
        return False
    
    @classmethod
    def refresh(cls, token: str, expire_seconds: int = None) -> bool:
        """
        刷新 Token 过期时间
        
        :param token: token 字符串
        :param expire_seconds: 新的过期时间（秒）
        :return: 是否刷新成功
        """
        if not token:
            return False
        
        if expire_seconds is None:
            expire_seconds = TOKEN_EXPIRE_SECONDS
        
        token_key = cls._get_token_key(token)
        
        # 检查 token 是否存在
        if not redis_client.exists(token_key):
            return False
        
        # 刷新过期时间
        redis_client.expire(token_key, expire_seconds)
        
        # 同时刷新用户 token 映射的过期时间
        data = cls.verify(token)
        if data:
            account_id = data.get("account_id")
            if account_id:
                user_token_key = cls._get_user_token_key(account_id)
                redis_client.expire(user_token_key, expire_seconds)
        
        return True
    
    @classmethod
    def get_account_id(cls, token: str) -> Optional[int]:
        """
        从 Token 获取账号ID
        
        :param token: token 字符串
        :return: 账号ID，无效则返回 None
        """
        data = cls.verify(token)
        if data:
            return data.get("account_id")
        return None
    
    @classmethod
    def get_account_type(cls, token: str) -> Optional[int]:
        """
        从 Token 获取账号类型
        
        :param token: token 字符串
        :return: 账号类型，无效则返回 None
        """
        data = cls.verify(token)
        if data:
            return data.get("account_type")
        return None
