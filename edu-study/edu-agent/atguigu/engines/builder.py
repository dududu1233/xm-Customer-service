# === 文件：atguigu/engines/builder.py ===
# 角色：引擎层(engines/)的"总装配工厂"
# 功能：build_dialogue_engine() 加载 flow_config 的 yml 流程 → 实例化所有子组件(轮次规划器/任务处理器/知识处理器/闲聊/澄清) → 注入 DialogueEngine。相当于把"大脑"的各个器官拼成完整大脑
# 入口：被 services/dialogue_service.py(或 app 的 lifespan) 调用，拿到引擎实例
# 出口：几乎 import 了所有 handler/provider，是全项目依赖关系最密集的"总装配图"；想看清各模块怎么串起来，看这里最直观
from pathlib import Path

from atguigu.chitchat.handler import ChitChatHandler
from atguigu.chitchat.responder import ChitChatResponder
from atguigu.clarify.responder import ClarifyResponder
from atguigu.engines.dialogue_engine import DialogueEngine
from atguigu.knowledge.handler import KnowledgeHandler
from atguigu.knowledge.intents import KNOWLEDGE_INTENTS
from atguigu.knowledge.provider.knowledge import ApiOrderProvider, ApiCourseProvider, RagDefaultProvider, \
    FaqDefaultProvider
from atguigu.knowledge.provider.register import KnowledgeRegister
from atguigu.knowledge.resonder import KnowledgeResponder
from atguigu.plan.planner import TurnPlanner
from atguigu.plan.validator import TurnPlanValidator
from atguigu.task.action.builder import build_action_runner
from atguigu.task.commands.processor import CommandProcessor
from atguigu.task.flows.executor import FlowExecutor
from atguigu.task.flows.loader import FlowLoader
from atguigu.task.handler import TaskHandler

PROJECT_ROOT_DIR = Path(__file__).resolve().parents[2]

FLOW_CONFIG_DIR = PROJECT_ROOT_DIR / "flow_config"


def build_dialogue_engine():
    # 1. 加载流程
    flow_list = FlowLoader().load_multi_yaml(
        [FLOW_CONFIG_DIR / yaml for yaml in ("system_flows.yml", "user_flows.yml")])

    return DialogueEngine(
        turn_planner=TurnPlanner(),
        turn_plan_validator=TurnPlanValidator(),
        clarify_responder=ClarifyResponder(),
        task_handler=TaskHandler(
            flow_list=flow_list,
            command_processor=CommandProcessor(),
            flow_executor=FlowExecutor(),
            action_runner=build_action_runner()
        ),
        knowledge_handler=KnowledgeHandler(
            knowledge_intents=KNOWLEDGE_INTENTS,
            knowledge_register=KnowledgeRegister(
                providers=[
                    ApiOrderProvider(),
                    ApiCourseProvider(),
                    RagDefaultProvider(),
                    FaqDefaultProvider()
                ]
            ),
            knowledge_responder=KnowledgeResponder()
        ),
        chitchat_handler=ChitChatHandler(
            chatchat_responder=ChitChatResponder()
        )
    )
