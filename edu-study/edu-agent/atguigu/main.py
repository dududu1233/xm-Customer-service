# === 文件：atguigu/main.py ===
# 角色：程序总入口（"点火器"），不属于任何业务层
# 功能：读取 settings 里的 host/port，用 uvicorn 把 FastAPI 应用(api.app:app)拉起来，开始监听 HTTP 请求
# 入口：你手动 `python atguigu/main.py` 运行它，整个服务才启动
# 出口：把请求交给 api/app.py 里的 FastAPI 实例；自身不做任何业务处理（只负责"拉起服务器"）
"""
启动uvicorn web服务
"""
import  uvicorn

from atguigu.config.settings import  settings

if __name__ == '__main__':

    uvicorn.run(app="atguigu.api.app:app",host=settings.app_host,port=settings.app_port)

