# === 文件：atguigu/config/settings.py ===
# 角色：配置层，集中读取项目运行所需的环境变量配置。
# 功能：用 pydantic-settings 从 .env 加载 LLM、中台 API、数据库、服务主机等配置，对外暴露 settings 单例。
# 入口：被 infrastructure（llm_client、db_client、http_client 相关）、knowledge provider、task action 等几乎所有需要配置的项依赖。
# 出口：不 import 任何 atguigu 内部模块（仅依赖 pydantic_settings）。
from pathlib import Path

from pydantic_settings import SettingsConfigDict, BaseSettings

PROJECT_DIR = Path(__file__).resolve().parents[2]

ENV_FILE_PATH = PROJECT_DIR / ".env"

print(ENV_FILE_PATH)


class Settings(BaseSettings):
    llm_model: str
    llm_base_url: str
    llm_api_key: str
    commerce_api_base_url: str
    database_url: str
    app_host: str
    app_port: int  # APP_PORT=18082 自动转换成int类型（能转 转不了就报错）

    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH, env_file_encoding="utf-8")


settings = Settings()  # type:ignore
