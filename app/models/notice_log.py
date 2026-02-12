"""
提醒通知记录表
"""
from sqlalchemy import Column, Integer, String, Text

from app.core.database import Base


class NoticeLog(Base):
    """
    提醒通知记录表
    """
    __tablename__ = "notice_log"

    notice_log_id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    account_id = Column(Integer, nullable=False, comment="账号表主键")
    notice_type = Column(Integer, nullable=True, comment="消息类型")
    title = Column(String(200), nullable=True, comment="消息标题")
    content = Column(Text, nullable=True, comment="消息内容")
