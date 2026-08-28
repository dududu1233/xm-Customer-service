# === 文件：atguigu/task/action/customer/submit_refund.py ===
# 角色：自定义 action，提交课程订单退款申请。
# 功能：ActionSubmitRefund 通过 shared.fetch_order 拿 orderId + items[0].orderItemId，再调 edu-data POST /order-items/{id}/refund-requests 真实提交。
# 入口：被 action/builder 自动发现注册；由 executor 在 refund_request flow 中触发。
# 出口：atguigu.domain.messages、atguigu.domain.state、atguigu.infrastructure.http_client、atguigu.task.action.base、atguigu.task.action.customer.shared。
import asyncio
from decimal import Decimal
from typing import Any

from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.infrastructure import http_client
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.customer.shared import fetch_order
from atguigu.config.settings import settings


class ActionSubmitRefund(Action):
    name = "action_submit_refund"

    async def run(self, action_kwargs: dict[str, Any], state: DialogueState) -> ActionResult:
        """
        职责：根据订单号与退款原因，真实提交退款申请
        Args:
            action_kwargs:
            state:

        Returns:

        """
        slots = state.active_task.slots or {}
        order_number = (slots.get("order_number") or "").strip()
        refund_reason = (slots.get("refund_reason") or "").strip() or "用户申请退款"

        # 1. 拿订单详情与明细
        order = await fetch_order(order_number)
        if not order:
            return ActionResult(messages=[
                BotMessage(text=f"没有找到订单「{order_number}」，无法提交退款申请，请确认订单号。")
            ])

        items = order.get("items") or []
        if not items:
            return ActionResult(messages=[
                BotMessage(text=f"订单「{order.get('orderNo') or order_number}」没有可退款的课程明细。")
            ])

        # 默认对第一笔明细做退款（用户一般一单一课）
        item = items[0]
        order_item_id = item.get("orderItemId")
        item_status = item.get("orderItemStatusCode")
        apply_amount = item.get("payableAmount") or 0

        # 状态检查：仅 paid / completed 可退
        if item_status not in {"paid", "completed"}:
            return ActionResult(messages=[
                BotMessage(
                    text=f"订单明细当前状态为「{item_status}」，不允许退款（仅已支付/已完成的课程可退）。"
                )
            ])

        # 2. 构造请求体并提交
        body = {
            "refundType": "personal_reason",  # 默认个人原因（真实场景应由 LLM 分类）
            "refundReason": refund_reason,
            "applyAmount": apply_amount,
            "remark": None,
        }
        try:
            r = await http_client.http_client.post(
                f"{settings.commerce_api_base_url.rstrip('/')}/api/v1/order-items/{order_item_id}/refund-requests",
                json=body,
            )
            resp = r.json()
        except Exception as e:
            return ActionResult(messages=[
                BotMessage(text=f"提交退款申请时网络异常：{e}")
            ])

        if resp.get("code") != 0:
            err = resp.get("message") or "未知错误"
            return ActionResult(messages=[
                BotMessage(text=f"退款申请提交失败：{err}")
            ])

        data = resp.get("data") or {}
        refund_id = data.get("refundRequestId") or "—"
        return ActionResult(messages=[
            BotMessage(
                text=(
                    f"已为订单「{order.get('orderNo') or order_number}」"
                    f"提交退款申请（课程：{item.get('itemName', '—')}，"
                    f"申请金额 ¥{apply_amount}）。"
                    f"退款申请单号 {refund_id}，我们会在 1-3 个工作日内审核。"
                )
            )
        ])
