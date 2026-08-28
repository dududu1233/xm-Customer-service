"""
定义FastAPI实例
"""
# 【后端总入口】这个文件是整个后端服务的"门面"：启动、关闭、挂路由都在这里完成
# 类比：餐厅的"店面招牌 + 开门/打烊流程"
# uvicorn 真正启动的就是这里创建的 app（见 main.py: uvicorn.run(app="api.app:app")）
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from atguigu.api.chat_router import router
from atguigu.infrastructure.db_client import init_db_engine, dispose_engine
from atguigu.infrastructure.http_client import init_http_client, disposed_http_client


async def lifespan(_: FastAPI):
    """
    fastapi生命周期的回调函数
    Returns:

    """

    # 1. 初始化各种资源
    # （补充）这里只是"建好连接池/客户端"，并不会立刻真的连数据库，真正的连接要等到第一次查询
    print("应用启动的时候，来执行到回调函数")
    init_db_engine()
    init_http_client()

    # 2. 真正执行路由请求（/api/）
    # （补充）yield 之后，应用进入"正常对外服务"状态，开始接收请求
    yield

    # 3. 释放各种资源
    # （补充）关闭阶段：释放资源，避免连接泄漏
    print("应用关闭的时候，来执行到回调函数")
    await dispose_engine()
    await disposed_http_client()


app = FastAPI(description="智能客服项目的FASTAPI实例", lifespan=lifespan)

# 注册路由
# （补充）把 chat_router 里定义的所有路由（/、/test、/api/chat、/api/chat/history）挂到 app 上
# 挂上之后，这些地址才能被外界访问到
app.include_router(router)

# CORS 兜底：允许任意来源访问，避免"双击打开 index.html（file:// 协议）"时浏览器拦截跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 托管前端调试页：访问 http://127.0.0.1:18082/static/index.html
# （与 API 同源，正常浏览器访问时不存在跨域问题）
STATIC_DIR = Path(__file__).resolve().parents[2] / "static"
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
