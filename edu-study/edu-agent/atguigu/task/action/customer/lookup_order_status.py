# === 文件：atguigu/task/action/customer/lookup_order_status.py ===
# 角色：自定义 action，查询订单状态信息。
# 功能：ActionLookupOrderStatus 通过 shared.fetch_order 调 edu-data，把订单状态/摘要写入 updated_slots；含 _build_order_summary 拼装摘要文本，_status_to_zh 映射订单状态码为中文。
# 入口：被 action/builder 自动发现注册；由 executor 触发。
# 出口：atguigu.domain.state、atguigu.infrastructure.http_client、atguigu.task.action.base、atguigu.task.action.customer.shared。
from typing import Any

from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.customer.shared import fetch_order


class ActionLookupOrderStatus(Action):
    name = "action_lookup_order_status"

    async def run(self, action_kwargs: dict[str, Any], state: DialogueState) -> ActionResult:
        """
        职责：调用 fetch_order 获取订单信息，并把可读状态/摘要写入 slots
        Args:
            action_kwargs:
            state:

        Returns:

        """

        # 1. 拿槽位中的订单号（用户填的）
        order_number = (state.active_task.slots.get("order_number") or "").strip()

        # 2. 调 edu-data：先列表匹配 orderNo/orderId，再拿详情+明细
        payload = await fetch_order(order_number) if order_number else None

        # 3. 封装到 slots
        if not payload:
            return ActionResult(updated_slots={
                "order_status": "未找到订单",
                "order_summary": f"没有找到与「{order_number}」相关的订单，请确认订单号是否正确。",
            })

        status_zh = _status_to_zh(payload.get("orderStatusCode"))
        return ActionResult(updated_slots={
            "order_status": status_zh,
            "order_summary": _build_order_summary(payload),
        })


# edu-data 订单状态码 → 中文
_STATUS_ZH = {
    "pending": "待付款",
    "paid": "已支付",
    "completed": "已完成",
    "cancelled": "已取消",
    "partial_refunded": "部分退款",
    "refunded": "已退款",
}


def _status_to_zh(code: str | None) -> str:
    return _STATUS_ZH.get(code or "", code or "未知")


def _build_order_summary(payload: dict[str, Any]) -> str:
    """
    拼装订单摘要：订单号 + 金额 + 课程名
    """
    parts: list[str] = []
    if payload.get("orderNo"):
        parts.append(f"订单号 {payload['orderNo']}")
    if payload.get("payableAmount") is not None:
        parts.append(f"实付 ¥{payload['payableAmount']}")
    items = payload.get("items") or []
    if items:
        titles = [str(it.get("itemName") or "").strip()
                  for it in items[:2] if it.get("itemName")]
        if titles:
            parts.append("课程：" + "、".join(titles))
    if payload.get("paymentSummary", {}).get("paidAt"):
        parts.append(f"支付时间 {payload['paymentSummary']['paidAt']}")
    return "。".join(parts) + "。" if parts else ""
