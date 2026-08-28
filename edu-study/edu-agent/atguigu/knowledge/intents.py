# === 文件：atguigu/knowledge/intents.py ===
# 角色：knowledge 层的配置数据，定义系统支持的知识意图及其绑定的 provider。
# 功能：定义 KnowledgeIntent 数据类与 KNOWLEDGE_INTENTS 字典（课程/订单/退款/报名/平台规则等意图 → provider_id + 所需对象类型）。
# 入口：被 knowledge/handler、plan/planner、plan/validator 引用。
# 出口：不 import 任何 atguigu 内部模块（仅标准库）。
from dataclasses import dataclass


@dataclass(slots=True)
class KnowledgeIntent:
    id: str
    description: str
    provider_ids: list[str]
    requires_object_type: str | None = None


# 系统支持的所有知识意图（教育领域）
KNOWLEDGE_INTENTS: dict[str, KnowledgeIntent] = {
    "course_info": KnowledgeIntent(
        id="course_info", description="课程信息咨询",
        provider_ids=["api.course"], requires_object_type="course",
    ),
    "order_info": KnowledgeIntent(
        id="order_info", description="订单信息咨询",
        provider_ids=["api.order"], requires_object_type="order",
    ),
    "refund_policy": KnowledgeIntent(
        id="refund_policy", description="退款政策咨询",
        provider_ids=["faq.default", "rag.default"],
    ),
    "enrollment_policy": KnowledgeIntent(
        id="enrollment_policy", description="报名政策咨询",
        provider_ids=["faq.default", "rag.default"],
    ),
    "platform_rule": KnowledgeIntent(
        id="platform_rule", description="平台规则咨询",
        provider_ids=["rag.default"],
    ),
    "general_edu_info": KnowledgeIntent(
        id="general_edu_info", description="教育通用信息咨询",
        provider_ids=["faq.default", "rag.default"],
    ),
}
