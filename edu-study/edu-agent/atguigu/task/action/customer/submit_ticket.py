# === 文件：atguigu/task/action/customer/submit_ticket.py ===
# 角色：自定义 action，提交问题工单。
# 功能：ActionSubmitTicket 通过 shared.fetch_order 拿 orderId + items[0].orderItemId，再调 /me/student-profile 拿 studentId，最后 POST /service-tickets 真实提交。
# 入口：被 action/builder 自动发现注册；由 executor 在 ticket_submit flow 中触发。
# 出口：atguigu.domain.messages、atguigu.domain.state、atguigu.infrastructure.http_client、atguigu.task.action.base、atguigu.task.action.customer.shared。
import asyncio
from typing import Any

from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.infrastructure import http_client
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.customer.shared import fetch_order
from atguigu.config.settings import settings


# 用户口语 → ticketType 枚举
_KEYWORD_TO_TICKET_TYPE = [
    (("退费", "退款", "退课"), "refund"),
    (("投诉", "不满", "差评", "建议"), "complaint"),
    (("咨询", "使用", "课程", "教材", "题库", "上课", "学习", "答疑", "工具"), "after_sales"),
]


def _to_ticket_type(text: str) -> str:
    text = (text or "").strip()
    for keywords, code in _KEYWORD_TO_TICKET_TYPE:
        for kw in keywords:
            if kw in text:
                return code
    return "after_sales"


def _to_title(text: str) -> str:
    text = (text or "").strip()
    return text[:30] + ("…" if len(text) > 30 else "")


class ActionSubmitTicket(Action):
    name = "action_submit_ticket"

    async def run(self, action_kwargs: dict[str, Any], state: DialogueState) -> ActionResult:
        """
        职责：把订单号 + 工单类型 + 问题描述提交为正式工单
        Args:
            action_kwargs:
            state:

        Returns:

        """
        slots = state.active_task.slots or {}
        order_number = (slots.get("order_number") or "").strip()
        ticket_type_input = (slots.get("ticket_type") or "").strip()
        ticket_content = (slots.get("ticket_description") or "").strip()

        if not ticket_content:
            return ActionResult(messages=[
                BotMessage(text="请先描述一下你遇到的问题。")
            ])

        # 1. 拿订单（orderId + items[0].orderItemId）
        order = await fetch_order(order_number)
        if not order:
            return ActionResult(messages=[
                BotMessage(text=f"没有找到订单「{order_number}」，无法提交工单，请确认订单号。")
            ])

        items = order.get("items") or []
        if not items:
            return ActionResult(messages=[
                BotMessage(text=f"订单「{order.get('orderNo') or order_number}」没有关联课程，无法提交工单。")
            ])
        order_item_id = items[0].get("orderItemId")

        # 2. 拿 studentId
        try:
            r = await http_client.http_client.get(
                f"{settings.commerce_api_base_url.rstrip('/')}/api/v1/me/student-profile"
            )
            sp = r.json().get("data") or {}
            student_id = sp.get("studentId") or sp.get("id")
        except Exception as e:
            return ActionResult(messages=[
                BotMessage(text=f"获取学员档案失败：{e}")
            ])

        if not student_id:
            return ActionResult(messages=[
                BotMessage(text="未找到你的学员档案，无法提交工单。")
            ])

        # 3. 构造请求体
        body = {
            "ticketType": _to_ticket_type(ticket_type_input),
            "priorityLevel": "medium",
            "ticketSource": "user_app",
            "title": _to_title(ticket_content),
            "ticketContent": ticket_content,
            "studentId": student_id,
            "orderItemId": order_item_id,
        }

        # 4. 提交
        try:
            r = await http_client.http_client.post(
                f"{settings.commerce_api_base_url.rstrip('/')}/api/v1/service-tickets",
                json=body,
            )
            resp = r.json()
        except Exception as e:
            return ActionResult(messages=[
                BotMessage(text=f"提交工单时网络异常：{e}")
            ])

        if resp.get("code") != 0:
            err = resp.get("message") or "未知错误"
            return ActionResult(messages=[
                BotMessage(text=f"工单提交失败：{err}")
            ])

        data = resp.get("data") or {}
        ticket_no = data.get("ticketNo") or data.get("ticketId") or "—"
        return ActionResult(messages=[
            BotMessage(
                text=(
                    f"已为你提交工单（工单号 {ticket_no}）。"
                    f"问题类型：{ticket_type_input or 'after_sales'}。"
                    f"我们会在 1 个工作日内回复，请留意消息通知。"
                )
            )
        ])
