"""
统一响应格式
"""
from typing import Any, Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    """
    统一响应格式
    {
        "code": 0,
        "message": "success",
        "data": ...
    }
    """
    code: int = 0
    message: str = "success"
    data: Optional[T] = None


def success(data: Any = None, message: str = "success") -> dict:
    """
    返回成功响应
    
    :param data: 响应数据，可以是对象、数组或 None
    :param message: 成功消息
    :return: 统一格式的响应字典
    """
    return {
        "code": 0,
        "message": message,
        "data": data
    }



def error(code: int = -1, message: str = "error", data: Any = None) -> dict:
    """
    返回错误响应
    
    :param code: 错误码，非0表示错误
    :param message: 错误消息
    :param data: 附加数据（可选）
    :return: 统一格式的响应字典
    """
    return {
        "code": code,
        "message": message,
        "data": data
    }
