# === 文件：atguigu/task/commands/command.py ===
# 角色：task 命令的数据模型，表示对流程状态的指令。
# 功能：定义 Command 基类及 StartFlowCommand/SetSlotsCommand/ResumedFlowCommand/CancelFlowCommand，含 from_dict 按 command 类型反序列化。
# 入口：被 plan/turn_plan（构造命令）、task/commands/processor、task/handler、plan/validator 引用。
# 出口：不 import 任何 atguigu 内部模块（仅标准库）。
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Command:
    command: str


    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Command":
        command_type = data['command']
        clz=COMMAND_TO_CLASS[command_type]
        return clz(**data)

@dataclass(slots=True)
class StartFlowCommand(Command):
    """
    开启新的业务流程命令
    """
    flow: str  # 业务流程ID


@dataclass(slots=True)
class SetSlotsCommand(Command):
    slots: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ResumedFlowCommand(Command):
    flow: str | None = None


@dataclass(slots=True)
class CancelFlowCommand(Command):
    flow:str | None=None


COMMAND_TO_CLASS: dict[str, type[Command]] = {
    "start_flow": StartFlowCommand,
    "resume_flow": ResumedFlowCommand,
    "cancel_flow": CancelFlowCommand,
    "set_slots": SetSlotsCommand
}
