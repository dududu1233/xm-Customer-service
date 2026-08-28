"""
管理service.
FASTAPI的依赖注入：Depends
Annotated；注解。可以将类型提示和依赖注入绑定在一起
"""
# 【依赖注入装配中心】把各个组件（引擎 / 仓储 / 服务）按依赖关系"拼装"起来
# FastAPI 的依赖注入（Depends）+ 类型注解（Annotated）机制：
# 路由函数只要声明"我需要 DialogueStateServiceDep"，FastAPI 就自动按下面的链条把它造好并传进来
# 装配链条：session(数据库会话) → repository(仓储) → service(服务) → 交给路由
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from atguigu.engines.dialogue_engine import DialogueEngine
from atguigu.repository.dialogue_repository import DialogueRepository
from atguigu.services.dialogue_service import DialogueStateService
from atguigu.infrastructure.db_client import session_factory  # 有坑  模块下的成员
from atguigu.infrastructure import  db_client                   # 包下面的模块 可以的
from  atguigu.engines.builder import  build_dialogue_engine

# 工厂函数：构造一个对话引擎实例
def get_dialogue_engine():
    return build_dialogue_engine()


# 类型别名：把"DialogueEngine 类型"和"如何造它(Depends)"绑定在一起
# 以后路由只要写 `engine: DialogueEngineDep`，FastAPI 就自动调用 get_dialogue_engine() 注入
DialogueEngineDep = Annotated[DialogueEngine, Depends(get_dialogue_engine)]


# 工厂函数：每次请求提供一个数据库会话(session)
async def get_session():
    async with db_client.session_factory() as session:
        yield session  # 一定要yield出去，一旦return 代码块执行完，session对象又被释放掉了。用完，才来释放


# 类型别名：路由声明 `session: DialogueSessionDep` 即可拿到一个可用的数据库会话
DialogueSessionDep = Annotated[AsyncSession, Depends(get_session)]


# 工厂函数：用上面的 session 造一个仓储（负责读写数据库）
def get_dialogue_repository(session: DialogueSessionDep):
    return DialogueRepository(session)


# 类型别名
DialogueRepositoryDep = Annotated[DialogueRepository, Depends(get_dialogue_repository)]


# 工厂函数：把"引擎"和"仓储"组合成"服务"（编排中枢）
def get_dialogue_service(engine: DialogueEngineDep, repository: DialogueRepositoryDep):
    return DialogueStateService(engine, repository)


# 最终对外暴露的类型别名：路由里写的 `service: DialogueStateServiceDep` 就是它
# FastAPI 会递归地把 engine、repository、session 全部自动造好并注入进来
DialogueStateServiceDep = Annotated[DialogueStateService, Depends(get_dialogue_service)]
