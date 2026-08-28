# === 文件：atguigu/task/action/builtin/listener.py ===
# 角色：内置 action，作为流程"暂停等待用户输入"的哨兵。
# 功能：ActionListener(name=action_listen) 的 run 返回空 ActionResult，表示流程在此停下等待用户下一轮输入。
# 入口：被 action/builder 注册到 runner；由 flows/executor 在找不到当前任务时返回。
# 出口：atguigu.domain.state、atguigu.task.action.base。
from typing import Any

from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult


class ActionListener(Action):
    name = "action_listen"

    async def run(self, action_kwargs: dict[str, Any], state: DialogueState) -> ActionResult:
        return ActionResult()
