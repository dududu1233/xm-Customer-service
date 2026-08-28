# === 文件：atguigu/infrastructure/http_client.py ===
# 角色：infrastructure 层对外部 HTTP 能力的封装。
# 功能：维护全局异步 httpx 客户端，提供 init_http_client / disposed_http_client 的初始化与释放；含调试用 main_test。
# 入口：被 knowledge provider、task action（customer/shared、lookup_order_status）等需要调用中台 API 的模块使用（通过 `from atguigu.infrastructure import http_client` 引用其 http_client 全局变量）。
# 出口：不 import 任何 atguigu 内部模块（依赖 httpx）。
"""

定义HTTP客户端(异步)

"""
import asyncio
import contextvars

from httpx import AsyncClient

# 当前请求对应的 edu-data 用户ID（即聊天 sender_id）。
# 用 contextvar 承载，每次对话请求在 service 层 set 一次，
# 所有向下游 edu-data 发的 HTTP 请求都会自动带上 X-User-Id 头，
# action / knowledge provider 里无需任何改动。
CURRENT_USER_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_user_id", default=None
)


async def _inject_user_header(request):
    """httpx 请求钩子：自动注入 X-User-Id 头。"""
    uid = CURRENT_USER_ID.get()
    if uid:
        request.headers["X-User-Id"] = str(uid)


http_client: AsyncClient | None = None


def init_http_client():
    """
    初始化http_client 资源
    """
    global http_client
    # event_hooks 在每个请求发出前注入 X-User-Id（来自 CURRENT_USER_ID）
    http_client = AsyncClient(
        timeout=120,
        trust_env=False,
        event_hooks={"request": [_inject_user_header]},
    )


async def disposed_http_client():
    """
    释放http_client资源
    :return:
    """
    await http_client.aclose()


async def main_test():
    init_http_client()

    response = await http_client.get(url="http://192.168.200.155:18081/orders/A20260408002")

    print(response.json())
    data= response.json()['data']
    print(data)


if __name__ == '__main__':
    asyncio.run(main_test())
