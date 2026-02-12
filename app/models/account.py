"""
账号表
"""
from sqlalchemy import Column, Integer, String

from app.core.database import Base


class Account(Base):
    """
    账号表
    type: 1-客户 2-律师 3-参与者 0-主任
    close: 0-正常 1-关闭
    """
    __tablename__ = "account"

    account_id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(50), nullable=True, comment="姓名")
    mobile = Column(String(20), nullable=True, comment="手机号")
    openid = Column(String(100), nullable=True, comment="公众号openid")
    sign_up_timestamp = Column(Integer, nullable=True, comment="注册时间")
    close = Column(Integer, default=0, comment="关闭状态 0正常 1关闭")
    type = Column(Integer, default=1, comment="类型 1客户 2律师 3参与者 0主任")
