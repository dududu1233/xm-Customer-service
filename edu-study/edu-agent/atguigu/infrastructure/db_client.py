# === 文件：atguigu/infrastructure/db_client.py ===
# 角色：基础设施层 —— 数据库连接工厂
# 功能：创建异步 SQLAlchemy 引擎 + session 工厂(async_sessionmaker, expire_on_commit=False)。init_db_engine 建连接池(懒连接，不立刻连库)，dispose_engine 释放
# 入口：app.py 的 lifespan 启动时会调用 init_db_engine 预建连接池
# 出口：产出 session_factory 交给 repository 层开 session 读写 MySQL；表需手动建(无自动 create_all)
"""

数据库的引擎
数据库连接工厂

"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine
from sqlalchemy import text
from atguigu.config.settings import settings

session_engine: AsyncEngine | None = None

session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db_engine():
    global session_engine, session_factory

    session_engine = create_async_engine(url=settings.database_url, echo=True)  # echo=True 可以显示SQL语句
    session_factory = async_sessionmaker(session_engine, expire_on_commit=False)  # expire_on_commit


async def dispose_engine():
    await session_engine.dispose()


async def main_test():
    init_db_engine()

    async with session_factory() as session:
        cursor = await session.execute(text("select 1"))  # CursorResult
        print(cursor.mappings().fetchone())   # (1,)   # 元组：索引取元组中的元素    {'1': 1}: 字典：方便根据列名来获取


    await  dispose_engine()

if __name__ == '__main__':

    asyncio.run(main_test())
