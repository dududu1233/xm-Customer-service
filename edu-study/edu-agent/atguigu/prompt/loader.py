# === 文件：atguigu/prompt/loader.py ===
# 角色：prompt 层，负责加载 jinja2 提示词模板文件。
# 功能：load_prompt_template_content 按模板名读取 prompt/jinja2/<name>.jinja2 文本返回。
# 入口：被各 responder（chitchat/knowledge/clarify）、plan/planner、task action response 等加载提示词时调用。
# 出口：不 import 任何 atguigu 内部模块（仅 pathlib）。
from pathlib import  Path

# 获取 import 模版
def load_prompt_template_content(template_file_stem: str) -> str:
    prompt_template_file_path =Path(__file__).resolve().parents[0]/ "jinja2"/f"{template_file_stem}.jinja2"

    return  prompt_template_file_path.read_text(encoding="utf-8")
