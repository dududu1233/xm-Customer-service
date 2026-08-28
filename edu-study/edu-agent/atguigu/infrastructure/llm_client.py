# === 文件：atguigu/infrastructure/llm_client.py ===
# 角色：基础设施层 —— 封装"大模型(LLM)调用"这一外部能力
# 功能：用 LangChain 的 init_chat_model 创建一个全局 LLM 客户端 `llm_client`（模型名/key/base_url 都来自 settings，兼容 openai 协议）；这是整个客服"能理解、会回答"的能力来源
# 入口：被各业务 handler（task/knowledge/chitchat 等）import 使用
# 出口：依赖 config/settings 的配置；文件末尾的 main_test / __main__ 是作者本地调试片段，与线上运行无关
"""
通过LangChain定义LLM客户端
模块之间的组件导入的标准写法：
1.导入sdk自带的
2.导入第三方的
3.导入自己定义
"""
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser

from atguigu.config.settings import settings

llm_client: BaseChatModel = init_chat_model(
    model_provider="openai",
    model=settings.llm_model,
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url
)


async def main_test():
    pass


if __name__ == '__main__':
    """
    流式调用：stream：同步的流式    astream:异步流式
    非流式调用：invoke:同步非流式   ainvoke:异步非流式
    Runnable组件提供的：抽象接口：定义常用的三组方法 batch  abatch
    :return:
    """
    # ai_message: AIMessage = llm_client.invoke("请你给我讲一个笑话，确保要幽默")
    chain = llm_client | StrOutputParser()  # | LCEL表达式：

    content = chain.invoke("我今天心情不好，请你安慰我一下")   # 输出=llm_client.invoke(原始输入)  最终输出=StrOutputParser.invoke(上一个组件输出)
    print(content)
