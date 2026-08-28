# === 文件：atguigu/task/flows/links.py ===
# 角色：task 流程步骤之间"边"的数据模型。
# 功能：定义 FlowStepLink 基类及 FlowStepStaticLink（顺序）/FlowStepConditionLink（条件）/FlowStepFallbackLink（兜底边），携带目标步骤 ID。
# 入口：被 flows/steps、flows/executor 使用。
# 出口：不 import 任何 atguigu 内部模块（仅标准库）。
"""
边数据模型
顺序边： next: ask_order_number
条件边 ：  - if: "条件1" then "clarification_rejected"    - if: "条件2" then "no_relevant_answer"
默认兜底边: - else: ask_rephrase
基类思想
"""

from dataclasses import  dataclass

@dataclass(slots=True)
class   FlowStepLink:
    """
    三种边的基类
    """
    target:str        # 下一个节点的节点ID(顺序边的next内容、条件边的then内容、兜底边的else内容)


@dataclass(slots=True)
class  FlowStepStaticLink(FlowStepLink):
    pass


@dataclass(slots=True)
class FlowStepConditionLink(FlowStepLink):
    condition:str        # 条件



@dataclass(slots=True)
class FlowStepFallbackLink(FlowStepLink):
    pass













