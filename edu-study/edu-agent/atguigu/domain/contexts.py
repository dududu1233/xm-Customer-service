# === 文件：atguigu/domain/contexts.py ===
# 角色：domain 层纯数据模型，定义业务流程与系统流程的上下文对象。
# 功能：提供 TaskContext（业务槽位上下文）及一组 SystemContext 子类（任务开始/中断/恢复/取消/收集信息等），带 to_dict/from_dict 序列化，并提供 flow_id→类的映射表。
# 入口：被 task/commands/processor、task/flows/executor 等修改或读取流程状态的地方使用。
# 出口：不 import 任何 atguigu 内部模块（仅标准库 dataclasses/typing）。
"""
上下文对象的类型（抽象）
业务流程上下文

系统流程上下文:继承思想+字典的映射

"""
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(slots=True)
class TaskContext:
    """
    业务流程上下文：
    flow_id:业务流程ID:确认业务流是哪一个的唯一标识：比如order_status_query
    step_id: 业务流程的步骤ID.确认业务流程的步骤。已经走了哪些不，该走哪一步
    slots: 业务流程缺少的槽位信息
    """

    flow_id: str
    step_id: str
    slots: dict[str, Any] = field(default_factory=dict)  # 槽位的信息

    def to_dict(self) -> dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "step_id": self.step_id,
            "slots": self.slots
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskContext":
        return cls(
            flow_id=data['flow_id'],
            step_id=data['step_id'],
            slots=data['slots']
        )


@dataclass(slots=True)
class SystemContext:
    """
    系统流程上下文的基类
    flow_id: 系统流程ID: system_task_started
    step_id: 系统流程的步骤ID:start
    flow_id/step_id一定要是这两个名字【在流程推进器的时候，解释原因】
    """

    flow_id: str
    step_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)  # type: ignore

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "SystemContext":
        flow_id = data['flow_id']
        clz = SYSTEM_CONTEXT_TO_CLASS[flow_id]
        return clz(**data)


@dataclass(slots=True)
class SystemTaskStartedContext(SystemContext):
    started_flow_id: str  # 开启的业务流程的流程ID
    started_flow_name: str  # 开启的业务流程的流程名字(根据业务流程ID获取)


@dataclass(slots=True)
class SystemTaskInterruptedContext(SystemContext):
    interrupted_flow_id: str
    interrupted_flow_name: str
    started_flow_id: str
    started_flow_name: str


@dataclass(slots=True)
class SystemTaskResumedContext(SystemContext):
    resumed_flow_id: str
    resumed_flow_name: str


@dataclass(slots=True)
class SystemTaskResumeFailedContext(SystemContext):
    """没有找到可恢复的业务流程时使用。"""


@dataclass(slots=True)
class SystemTaskCanceledContext(SystemContext):
    canceled_flow_id: str
    canceled_flow_name: str


@dataclass(slots=True)
class SystemCollectInformationContext(SystemContext):
    response: dict[str, Any]  # 要告诉用户业务流程槽位缺少什么
    slot_name: str  # 缺少槽位名字【槽位信息：槽位名字 槽位值】 TODO 主要是为了判断


SYSTEM_CONTEXT_TO_CLASS: dict[str, type[SystemContext]] = {
    "system_task_started": SystemTaskStartedContext,
    "system_task_interrupted": SystemTaskInterruptedContext,
    "system_task_resumed": SystemTaskResumedContext,
    "system_task_canceled": SystemTaskCanceledContext,
    "system_collect_information": SystemCollectInformationContext,
    "system_task_resume_failed": SystemTaskResumeFailedContext
}
