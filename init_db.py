"""
数据库初始化脚本
运行: python init_db.py
"""
import pymysql
from app.core.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
from app.core.database import engine, Base
from app.models import Account, Sms, Case, AccountCase, CaseCommunication, NoticeLog


def create_database():
    """创建数据库（如果不存在）"""
    connection = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        charset='utf8mb4'
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            print(f"数据库 '{DB_NAME}' 创建成功（或已存在）")
    finally:
        connection.close()


def create_tables():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)
    print("所有表创建成功：")
    for table in Base.metadata.tables:
        print(f"  - {table}")


if __name__ == "__main__":
    print("开始初始化数据库...")
    print("-" * 40)
    create_database()
    print("-" * 40)
    create_tables()
    print("-" * 40)
    print("数据库初始化完成！")
