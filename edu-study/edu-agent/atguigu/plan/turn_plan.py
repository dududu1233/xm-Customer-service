# === 文件：atguigu/plan/turn_plan.py ===
# 角色：plan 层的数据模型，定义单轮计划与各轨道结构及校验原因枚举。
# 功能：定义 TaskTurnPlan/KnowledgeTurnPlan/ChitChatTurnPlan/TurnPlan（含 activated_tracks）、ClarifyReason 枚举、TurnPlanValidatedResult。
# 入口：被 plan/planner、plan/validator、clarify/responder、engines 等使用。
# 出口：atguigu.task.commands.command。
from dataclasses import dataclass
from enum import Enum
from typing import Any

from atguigu.task.commands.command import Command


@dataclass(slots=True)
class TaskTurnPlan:
    commands: list[Command]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskTurnPlan":
        return cls(
            commands=[Command.from_dict(command_dict) for command_dict in data['commands']]
        )


@dataclass(slots=True)
class KnowledgeTurnPlan:
    intents: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnowledgeTurnPlan":
        return cls(
            intents=data['intents']
        )


@dataclass(slots=True)
class ChitChatTurnPlan:
    chat: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChitChatTurnPlan":
        return cls(
            chat=data.get('chat')
        )


@dataclass(slots=True)
class TurnPlan:
    task: TaskTurnPlan | None = None
    knowledge: KnowledgeTurnPlan | None = None
    chitchat: ChitChatTurnPlan | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TurnPlan":
        return cls(
            task=TaskTurnPlan.from_dict(data['task']) if data.get('task') is not None else None,
            knowledge=KnowledgeTurnPlan.from_dict(data['knowledge']) if data.get('knowledge') is not None else None,
            chitchat=ChitChatTurnPlan.from_dict(data['chitchat']) if data.get('chitchat') is not None else None
        )


    # 激活 的 各个 轨道
    def  activated_tracks(self):
        activated_tracks:list[str]=[]

        if self.task is not None:
            activated_tracks.append("task")
        if self.knowledge is not None:
            activated_tracks.append("knowledge")
        if self.chitchat is not None:
            activated_tracks.append("chitchat")

        return  activated_tracks


# 原因
class ClarifyReason(Enum):
    MISSING_TRACK = "missing_track" # 错过 track轨迹
    MULTIPLE_TRACKS = "multiple_tracks" # multiple 多数 tracks
    MISSING_TASK_COMMANDS = "missing_task_commands"
    MISSING_KNOWLEDGE_INTENT = "missing_knowledge_intent"
    MISSING_FOCUSED_OBJECT = "missing_focused_object"
    OBJECT_REQUIRES_INTENT = "object_requires_intent"
    INVALID_TASK_COMMANDS = "invalid_task_commands" # invalid: 无效的
    MULTIPLE_TASK_FLOWS = "multiple_task_flows" # multiple : 多数的
    UNKNOWN_TASK_FLOW = "unknown_task_flow"



@dataclass(slots=True)
class TurnPlanValidatedResult:
    valid: bool
    reason: ClarifyReason | None=None

