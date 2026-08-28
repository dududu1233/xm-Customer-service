# === 文件：atguigu/chitchat/responder.py ===
# 角色：闲聊轨道的实际执行者，调用 LLM 生成闲聊回复。
# 功能：ChitChatResponder 加载 chitchat_respond 提示词，结合最近历史，用 LLM 生成一句 BotMessage 文本。
# 入口：被 ChitChatHandler 调用。
# 出口：atguigu.infrastructure.llm_client、atguigu.chat_history.builder、atguigu.domain.messages、atguigu.domain.state、atguigu.prompt.loader。
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from atguigu.infrastructure.llm_client import llm_client
from atguigu.chat_history.builder import ChatHistoryBuilder
from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.prompt.loader import load_prompt_template_content


class ChitChatResponder:

    async def response(self, chat: str, state: DialogueState) -> list[BotMessage]:
        # 1. 加载提示词内容
        prompt_template_str = load_prompt_template_content("chitchat_respond")

        # 2. 定义提示词模版对象
        prompt_template = PromptTemplate.from_template(template=prompt_template_str, template_format="jinja2")

        # 3. 定义chain
        chain = prompt_template | llm_client | StrOutputParser()

        # 4. 调用链chain
        result = await  chain.ainvoke({
            "user_message": chat,
            "history": ChatHistoryBuilder.build(state.current_session().turns[-10:])
        })

        return [BotMessage(text=result)]
