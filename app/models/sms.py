"""
验证码表
"""
from sqlalchemy import Column, Integer, String

from app.core.database import Base


class Sms(Base):
    """
    验证码表
    """
    __tablename__ = "sms"

    sms_id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    mobile = Column(String(20), nullable=True, comment="手机号")
    sms_code = Column(String(10), nullable=True, comment="验证码")
    timestamp = Column(Integer, nullable=True, comment="发送时间")
    type = Column(Integer, nullable=True, comment="类型")
