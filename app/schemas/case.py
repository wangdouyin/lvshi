"""
案件相关的 Pydantic 模型
"""
from typing import Optional
from pydantic import BaseModel, Field


class CaseCreateRequest(BaseModel):
    """创建案件请求"""
    title: str = Field(..., description="标题", min_length=1, max_length=200)
    introduction: Optional[str] = Field(None, description="简介")
    

class CaseUpdateRequest(BaseModel):
    """更新案件请求"""
    title: Optional[str] = Field(None, description="标题", min_length=1, max_length=200)
    introduction: Optional[str] = Field(None, description="简介")
    progress: Optional[int] = Field(None, description="进度 1进行中 2完成", ge=1, le=2)
    type: Optional[int] = Field(None, description="状态 -1删除 0正常 1归档", ge=-1, le=1)


class CaseResponse(BaseModel):
    """案件响应"""
    case_id: int
    title: Optional[str]
    introduction: Optional[str]
    timestamp: Optional[int]
    complete_timestamp: Optional[int]
    lawyer_last_timestamp: Optional[int]
    update_timestamp: Optional[int]
    progress: int
    type: int
    
    class Config:
        from_attributes = True
