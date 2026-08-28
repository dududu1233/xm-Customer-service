# === 文件：atguigu/task/action/customer/recommend_similar_products.py ===
# 角色：自定义 action，处理相似商品推荐需求。
# 功能：ActionRecommendSimilarProducts 调用 shared.fetch_product 获取商品标题，返回"暂未接入推荐系统"的占位话术 BotMessage。
# 入口：被 action/builder 自动发现注册；由 executor 触发。
# 出口：atguigu.domain.messages、atguigu.domain.state、atguigu.task.action.base、atguigu.task.action.customer.shared。
from typing import Any

from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.customer.shared import fetch_product


class ActionRecommendSimilarProducts(Action):
    name = "action_recommend_similar_products"

    async def run(self, action_kwargs: dict[str, Any], state: DialogueState) -> ActionResult:
        """
        职责： 调用获取相似商品推荐的接口 并且返回行动的结果对象
        Args:
            action_kwargs:
            state:

        Returns:

        """
        product_id = state.active_task.slots.get("product_id")
        label = product_id or "这件商品"

        payload = await fetch_product(product_id)
        if payload:
            label = str(payload.get("title") or "").strip() or label

        text = (
            f"我已经收到你对\"{label}\"的相似商品推荐需求。"
            "不过当前版本还没有接入正式的推荐系统，稍后可以继续补上这部分能力。"
        )
        return ActionResult(messages=[BotMessage(text=text)])


