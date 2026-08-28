# === 文件：atguigu/task/action/base.py ===
# 角色：task action 的抽象基类与返回结构。
# 功能：定义 ActionResult（消息 + 更新槽位）与抽象类 Action（含 name 与异步 run 接口），供具体 action 继承。
# 入口：被所有具体 action（builtin/customer）继承，被 runner/register/builder 引用。
# 出口：atguigu.domain.messages、atguigu.domain.state。
from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass, field

from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState



@dataclass(slots=True)
class ActionResult:
    messages:list[BotMessage]=field(default_factory=list)
    updated_slots:dict[str,Any]=field(default_factory=dict)





class Action(ABC):

    name: str

    @abstractmethod
    async def  run(self,action_kwargs:dict[str,Any],state:DialogueState)->ActionResult:
        pass



# 1.子类进行 占位 实现
# 2. “开闭原则”：对扩展开放，对修改关闭。 当每次有新动作(新改动时) 不用改全部
# 3. “依赖倒置” + “多态” ： 多个类 -> 一个类来进行调用



