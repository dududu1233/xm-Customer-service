# === 文件：atguigu/repository/base.py ===
# 角色：持久化层(repository/)的 ORM 基类定义
# 功能：定义 SQLAlchemy 声明式基类 `Base(DeclarativeBase)`，所有 ORM 模型都继承它
# 入口：被各 ORM 模型文件 import 继承
# 出口：当前状态持久化(dialogue_repository)实际用手写 SQL 而非 ORM 模型，此 Base 是预留地基，所以文件很薄——属正常，不是漏写
from sqlalchemy.orm import  DeclarativeBase

class Base(DeclarativeBase):
    pass