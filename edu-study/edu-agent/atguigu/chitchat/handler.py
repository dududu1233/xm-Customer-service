# === 文件：atguigu/chitchat/handler.py ===
# 角色：闲聊轨道的编排处理者，衔接受话意图与具体回复生成。
# 功能：ChitChatHandler 接收用户闲聊文本与状态，委托 ChitChatResponder 生成机器人消息并返回。
# 入口：被 engines 层（对话引擎）在命中 chitchat 轨道时调用。
# 出口：atguigu.chitchat.responder、atguigu.domain.messages、atguigu.domain.state。
from atguigu.chitchat.responder import ChitChatResponder
from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState


class ChitChatHandler:

    def __init__(self, chatchat_responder: ChitChatResponder):
        self._chatchat_responder = chatchat_responder

    async def handle(self,
                     chat: str,
                     state: DialogueState) -> list[BotMessage]:
        bot_messages = await self._chatchat_responder.response(chat, state)

        return bot_messages
