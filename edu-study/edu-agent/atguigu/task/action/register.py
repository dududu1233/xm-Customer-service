# === 文件：atguigu/task/action/register.py ===
# 角色：task action 的注册中心。
# 功能：ActionRegister 以 action 名为键保存 Action 实例，提供 registry_action/get_action。
# 入口：被 action/builder 与 action/runner 使用。
# 出口：atguigu.task.action.base。
"""
提供注册能力：将五个子Action管理起来
"""
from atguigu.task.action.base import Action


class ActionRegister:

    def __init__(self):
        self.actions: dict[str, Action] = {}

    def registry_action(self, action: Action):
        self.actions[action.name] = action

    def get_action(self, action_name: str) -> Action:
        return self.actions[action_name]
