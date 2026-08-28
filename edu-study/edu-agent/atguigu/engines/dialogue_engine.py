import time

from atguigu.chitchat.handler import ChitChatHandler
from atguigu.clarify.responder import ClarifyResponder
from atguigu.domain.messages import ProcessedResult, BotMessage, UserMessage, MessageType, FocusedObject
from atguigu.domain.state import DialogueState
from atguigu.knowledge.handler import KnowledgeHandler
from atguigu.plan.planner import TurnPlanner
from atguigu.plan.turn_plan import TurnPlan, ClarifyReason
from atguigu.plan.validator import TurnPlanValidator
from atguigu.task.commands.command import Command, SetSlotsCommand
from atguigu.task.flows.flows import FlowList
from atguigu.task.flows.steps import CollectionFlowStep
from atguigu.task.handler import TaskHandler

# （补充）上面这一堆 import 都是引擎要指挥的"专家团队"，每人负责一类对话能力：
#   - ChitChatHandler / ClarifyResponder：闲聊、澄清追问
#   - KnowledgeHandler + KNOWLEDGE_INTENTS：知识问答（订单/商品/FAQ/RAG 由各类 provider 提供）
#   - TurnPlanner / TurnPlanValidator：用 LLM 分析"这条消息该走哪条轨道"
#   - TaskHandler + FlowList：任务型流程（查订单/物流/退款…），规则写在你见过的 flow_config/*.yml
#   - Command / SetSlotsCommand / CollectionFlowStep：流程里的"指令"和"收集(槽位)步骤"
# 这些对象最终在 engines/builder.py 的 build_dialogue_engine() 里被组装好、注入进来。


class DialogueEngine:
    # （补充）DialogueEngine = 整个对话系统的"导演 / 大脑"。
    # 它自己不写业务规则，而是把消息分派给上面的各位"专家"去处理。
    # service 层每次收到用户消息，都会调用它的 handle_message。

    def __init__(self,
                 turn_planner: TurnPlanner,
                 turn_plan_validator: TurnPlanValidator,
                 clarify_responder: ClarifyResponder,
                 task_handler: TaskHandler,
                 knowledge_handler: KnowledgeHandler,
                 chitchat_handler: ChitChatHandler
                 ):
        # （补充）注意：上面 6 个"专家"都不是在这里 new 出来的，
        # 而是从 engines/builder.py 的 build_dialogue_engine() 注入进来的。
        # 这样引擎只管"怎么分派"，不管"这些专家怎么造"，也方便测试时替换某个 handler。
        self.turn_planner = turn_planner
        self.turn_plan_validator = turn_plan_validator
        self.clarify_responder = clarify_responder
        self.task_handler = task_handler
        self.knowledge_handler = knowledge_handler
        self.chitchat_handler = chitchat_handler

    async def handle_message(self,
                             user_message: UserMessage,
                             dialogue_state: DialogueState) -> ProcessedResult:
        """
        职责：处理消息的核心入口
        Args:
            user_message:
            dialogue_state:

        Returns:

        """

        # （补充）这是 service.process_message 第②步调用的"大脑入口"。
        # 一句话概括它干的事：把一条用户消息，变成一组机器人回复(bot_messages)，
        # 并在这个过程中把对话状态(dialogue_state)一点点推进。
        # 注意：它只改"内存里的 dialogue_state 对象"，真正落库是 service 第③步 save_state 的事。

        # 1. 准备session
        self._prepare_session(dialogue_state)

        # 2. 开启turn
        self._start_turn(user_message, dialogue_state)

        # 3. 消息分流（文本消息 or 对象消息）
        # 3.1 文本消息类型
        if user_message.type is MessageType.TEXT:
            bot_messages = await self._handle_text_message(dialogue_state)

        # 3.2 对象消息类型
        else:
            # a) 将点击的卡片存储到对话状态中
            dialogue_state.focused_object = user_message.object

            # b) 真正处理对象消息
            bot_messages = await self._handle_object_message(user_message.object, dialogue_state,
                                                             self.task_handler.flow_list)

        # 4. 提交
        dialogue_state.pending_turn.bot_messages = bot_messages
        dialogue_state.commit_pending_turn()

        # 5. 返回机器人回复的消息
        return ProcessedResult(message_id=user_message.message_id, messages=bot_messages)

    def _prepare_session(self,
                         state: DialogueState):
        """
        职责：创建session对象
        Args:
            dialogue_state:

        Returns:

        """

        # （补充）session = "一次完整对话"。用户可能中途走了又回来，
        # 用一个 session 把这一轮会话的历史圈在一起。超过 1 小时没动静就当过期，开新的。

        # 1. 获取当前session
        current_session = state.current_session()

        # 2. 当前session没有
        if current_session is None:
            # a) 创建session
            state.start_session()
        # 3. 当前session有
        else:
            # 3.1 判断session是否过期了（简单规则）
            now = time.time()
            # 过期了
            if now - current_session.activated_at > 60 * 60:
                # a) 关闭过期的session
                state.close_current_session()

                # b) 重置运行时该过期session的对话状态
                state.reset_runtime_state_for_new_session()

                # c) 创建新session出来
                state.start_session()
            # 没过期
            else:
                current_session.activated_at = now

    def _start_turn(self,
                    user_message: UserMessage,
                    state: DialogueState):
        # （补充）turn = "一轮交互"（用户说一句 + 机器人回一句）。
        # 这里在状态里开一个 pending_turn（待提交轮次），先把用户这句话记进去，
        # 等下面处理完、机器人回复也填好，再在 handle_message 第④步统一 commit。

        state.begin_turn(user_message)

    async def _handle_text_message(self, dialogue_state: DialogueState) -> list[BotMessage]:
        """
        职责：处理文本消息类型（llm进行路由分析，规划轨道）
        Args:
            dialogue_state:
        Returns:
        """
        # （补充）文本消息是"自然语言"，引擎事先不知道用户想干嘛，
        # 所以先交给 TurnPlanner（背后是 LLM）做"路由分析"：
        #   这条消息到底是 任务(task) / 知识(knowledge) / 闲聊(chitchat) 哪条轨道？
        # 规划出 TurnPlan 后，再用 Validator 校验；校验不过就反问澄清，
        # 校验过了就按轨道分派给对应的 handler（下面的 if/elif/else）。

        # 1. 利用轮次规划器进行路由分析
        turn_plan: TurnPlan = await self.turn_planner.predict(dialogue_state,
                                                              flow_list=self.task_handler.flow_list,
                                                              knowledge_intents=self.knowledge_handler.knowledge_intents)

        # 2. 利用轮次结果校验器校验轮次规划后的结果
        validated = self.turn_plan_validator.valid(turn_plan,
                                                   dialogue_state,
                                                   flow_list=self.task_handler.flow_list,
                                                   knowledge_intents=self.knowledge_handler.knowledge_intents
                                                   )
        #  3. 校验失败
        if not validated.valid:
            return await self.clarify_responder.respond(validated.reason, dialogue_state)

        # 4. 校验成功(到底是哪一条轨道，进入到该轨道内部去执行对应的轨道内逻辑【xxxHandler】)
        if turn_plan.task is not None:
            return await self.task_handler.handle(turn_plan.task.commands, dialogue_state)
        elif turn_plan.knowledge is not None:
            return await self.knowledge_handler.handle(turn_plan.knowledge.intents, dialogue_state)
        else:
            return await self.chitchat_handler.handle(turn_plan.chitchat.chat, dialogue_state)

    async def _handle_object_message(self,
                                     object: FocusedObject,
                                     dialogue_state: DialogueState,
                                     flow_list: FlowList) -> list[BotMessage]:
        """
        职责：处理对象类型，本质构建SetSlotsCommand对象
        Args:
            dialogue_state:

        Returns:

        """
        # （补充）对象消息 = 用户在前端"点了张卡片"（订单卡/商品卡）。
        # 点卡片的本质是"替自己填槽位"：比如点了订单卡，就等于告诉系统 order_number=xxx。
        # 下面就是把这个点击翻译成一条 SetSlotsCommand，再交给 task_handler 去推进流程。

        # 1. 尝试构建SetSlotsCommand对象
        command = self._try_build_set_slots_command(object, dialogue_state, flow_list)

        # 2. 判断command  # 情况3：流程继续推进下一步
        if command:
            return await self.task_handler.handle(commands=[command], dialogue_state=dialogue_state)

        if dialogue_state.active_task is not None:  # 情况2: 流程继续执行，但是不去推进下一步，而是在执行当前这一步
            return await self.task_handler.handle(commands=[], dialogue_state=dialogue_state)

        # 情况1:澄清
        return await self.clarify_responder.respond(reason=ClarifyReason.OBJECT_REQUIRES_INTENT,
                                                    dialogue_state=dialogue_state)

    def _try_build_set_slots_command(self,
                                     object: FocusedObject,
                                     dialogue_state: DialogueState,
                                     flow_list: FlowList) -> Command | None:
        """
        职责：两种卡片类型的槽位（订单类型的槽位 商品信息的槽位）
        Args:
            dialogue_state:
            flow_list:

        Returns:

        """
        # （补充）把"点击的卡片"翻译成"填槽位指令"。
        #   - 订单卡 → slots={"order_number": 卡片id}
        #   - 商品卡 → slots={"product_id": 卡片id}
        # 但填之前要先确认"当前流程这一步正好缺这个槽位"（见下方 _is_can_set_slots_command），
        # 否则点了也没用，返回 None。
        if object.type == "order":
            if self._is_can_set_slots_command(slot_name="order_number", state=dialogue_state, flow_list=flow_list):
                return SetSlotsCommand(command="set_slots", slots={"order_number": object.id})
            return None
        elif object.type == "product":
            if self._is_can_set_slots_command(slot_name="product_id", state=dialogue_state, flow_list=flow_list):
                return SetSlotsCommand(command="set_slots", slots={"product_id": object.id})
            return None
        else:
            return None

    def _is_can_set_slots_command(self,
                                  slot_name: str,
                                  state: DialogueState,
                                  flow_list: FlowList) -> bool:
        """
        职责：处理点击卡片的三种情况
        情况1：没有业务流程，返回False
        情况2：有业务流程，但是收集步骤的时候，并不缺少卡片信息，返回False
        情况3：有业务流程，刚好收集该步骤的时候，点击卡片信息，返回True
        Args:
            slot_name:
            state:
            flow_list:

        Returns:

        """
        # （补充）判断"现在点这张卡合不合适"。三种情况：
        #   情况1：根本没在走任何业务流程 → 返回 False（点卡没意义）
        #   情况2：在走流程，但当前这一步不需要这张卡的槽位 → 返回 False
        #   情况3：在走流程，且当前收集步骤正好缺这个槽位 → 返回 True（填进去）
        # 关键两步：先拿到 active_task 对应的 flow，再定位到当前 step，
        # 看 step 是不是 CollectionFlowStep 且 slot_name 对得上。

        # 1. 获取当前业务流程上下文
        task_context = state.active_task

        # 2. 判读当前业务流程上下文,不存在
        if task_context is None:
            return False

        # 3.判读当前业务流程上下文,存在
        flow = flow_list.get_flow_by_id(task_context.flow_id)
        if flow is None:  # 防御性代码
            return False

        # 4. 判断流程步骤是否存在
        step_id = task_context.step_id
        step = flow.get_step_by_id(step_id)
        if step is None:  # 防御性代码
            return False

        # 5. 获取当前步骤类型
        if not isinstance(step, CollectionFlowStep):
            return False

        return step.slot_name == slot_name
