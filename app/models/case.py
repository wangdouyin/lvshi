"""
案件表
"""
from sqlalchemy import Column, Integer, String, Text

from app.core.database import Base


class Case(Base):
    """
    案件表
    progress: 1-进行中 2-完成
    type: -1-删除 0-正常 1-归档
    """
    __tablename__ = "case"

    case_id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    title = Column(String(200), nullable=True, comment="标题")
    introduction = Column(Text, nullable=True, comment="简介")
    timestamp = Column(Integer, nullable=True, comment="创建时间")
    complete_timestamp = Column(Integer, nullable=True, comment="完成时间")
    lawyer_last_timestamp = Column(Integer, nullable=True, comment="律师最后回复时间")
    update_timestamp = Column(Integer, nullable=True, comment="消息更新时间")
    progress = Column(Integer, default=1, comment="进度 1进行中 2完成")
    type = Column(Integer, default=0, comment="状态 -1删除 0正常 1归档")
