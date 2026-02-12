"""
用户相关的 Pydantic 模型（用于请求/响应验证）
"""
from typing import Optional
from pydantic import BaseModel, Field, validator
import re


class UserCreateRequest(BaseModel):
    """创建用户请求"""
    name: str = Field(..., description="姓名", min_length=1, max_length=50)
    mobile: str = Field(..., description="手机号", min_length=11, max_length=11)
    type: int = Field(1, description="类型 1客户 2律师 3参与者 0主任", ge=0, le=3)
    
    @validator('mobile')
    def validate_mobile(cls, v):
        """验证手机号格式"""
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError('手机号格式错误')
        return v


class UserUpdateRequest(BaseModel):
    """更新用户请求"""
    name: Optional[str] = Field(None, description="姓名", min_length=1, max_length=50)
    mobile: Optional[str] = Field(None, description="手机号", min_length=11, max_length=11)
    type: Optional[int] = Field(None, description="类型", ge=0, le=3)
    close: Optional[int] = Field(None, description="关闭状态 0正常 1关闭", ge=0, le=1)
    
    @validator('mobile')
    def validate_mobile(cls, v):
        """验证手机号格式"""
        if v and not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError('手机号格式错误')
        return v


class UserResponse(BaseModel):
    """用户响应"""
    account_id: int
    name: Optional[str]
    mobile: Optional[str]
    type: int
    close: int
    sign_up_timestamp: Optional[int]
    
    class Config:
        from_attributes = True  # 允许从 ORM 模型创建
