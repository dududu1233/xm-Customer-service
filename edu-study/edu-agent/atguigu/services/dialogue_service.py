# ===== 本文件需要的"零件"都从别的层 import 进来 =====
# UserMessage: 用户在对话框里发来的消息（接口层转好的内部对象）
# ProcessedResult: 引擎处理完后，要回给用户的"结果"（含多条机器人消息）
# ChatHistoryMessage: 给"历史记录"接口用的单条消息结构
from atguigu.domain.messages import UserMessage, ProcessedResult, ChatHistoryMessage

# 引擎：真正动脑子改状态的那一位（厨师长）
from atguigu.engines.dialogue_engine import DialogueEngine
# 仓储：负责把状态读写进数据库（档案柜管理员）
from atguigu.repository.dialogue_repository import DialogueRepository
# 历史消息构造器：把领域里的消息，包装成历史记录接口要的格式
from atguigu.chat_history.builder import ChatHistoryBuilder
from atguigu.infrastructure.http_client import CURRENT_USER_ID


class DialogueStateService:
    """
    服务层 = 餐厅里的「大堂经理」。
    它本身不碰数据库、也不写业务规则，只做一件事：
    把"取状态 → 交给引擎改状态 → 存回状态"这三步串起来（编排 / 总调度）。
    引擎和仓储都是外部通过"依赖注入"塞进来的（见 __init__），
    所以 service 自己不用关心它们是怎么造出来的。
    """

    def __init__(self,
                 engine: DialogueEngine,
                 repository: DialogueRepository):
        # 引擎和仓储不是在这里 new 出来的，而是从外面"注入"进来的
        # （具体在哪注入？看 api/dependencies.py 里那串 Depends 调用链）
        # 这种写法叫"依赖注入"，好处是 service 不关心它们怎么造出来的
        self._engine = engine          # 保存"厨师长"引用
        self._repository = repository  # 保存"档案柜管理员"引用

    async def process_message(self, user_message: UserMessage) -> ProcessedResult:
        """
        职责：处理对话消息的核心入口(service)
        Args:
            user_message:

        Returns:

        """
        # 0. 把当前用户ID写入上下文变量，使后续所有发往 edu-data 的 HTTP 请求
        #    自动带上 X-User-Id 头（agent 自身不直连库，统一走中台）
        user_id_token = CURRENT_USER_ID.set(user_message.sender_id)

        # 1. 从数据库中读取当前用户的对话状态  I/O
        # （补充）"取卡"：按用户 ID 把"对话状态卡"从数据库翻出来；第一次来则拿一张空卡
        dialogue_state = await self._repository.load_state(user_message.sender_id)

        # 2. 引擎层使用（修改对话状态中的内容）计算
        # （补充）"改卡"：把"用户消息 + 当前状态卡"交给引擎，引擎照 flow_config 在卡上写写画画；
        # ⚠️ 这一步改的是内存里的 dialogue_state 对象，还没有落库
        processed_result = await  self._engine.handle_message(user_message, dialogue_state)

        # 3. 修改后的对话状态内容保存到数据库中 I/O
        # （补充）"存卡"：把改好的状态卡序列化成 JSON 存回数据库，下次才能接着聊（对话才连贯）
        await self._repository.save_state(user_message.sender_id, dialogue_state)

        # 4. 清理上下文变量，避免影响后续请求
        CURRENT_USER_ID.reset(user_id_token)

        return processed_result

    async def get_chat_history(self, sender_id: str) -> list[ChatHistoryMessage]:
        """
        职责： 查询该用户所有会话下的聊天内容（当前session下的历史对话）
        Args:
            sender_id:

        Returns:

        """
        # （补充）先取卡：把该用户的整张"状态卡"从数据库捞出来
        state = await self._repository.load_state(sender_id)

        final_chat_history_messages = []

        # （补充）按层级遍历：状态卡(state) → 会话(session) → 轮次(turn)
        # 每个 turn 里装着 1 条用户消息 + N 条机器人回复，逐条包装成历史格式
        for session in state.sessions:

            for turn in session.turns:
                user_message = turn.user_message

                user_chat_history_message = ChatHistoryBuilder.build_chat_history(session.session_id, "user",
                                                                                  user_message.text,
                                                                                  user_message.object)

                final_chat_history_messages.append(user_chat_history_message)

                for bot_message in turn.bot_messages:
                    bot_chat_history_message = ChatHistoryBuilder.build_chat_history(session.session_id, "bot",
                                                                                     bot_message.text,
                                                                                     bot_message.object)

                    final_chat_history_messages.append(bot_chat_history_message)

        return final_chat_history_messages
