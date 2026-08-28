# === 文件：atguigu/knowledge/provider/knowledge.py ===
# 角色：knowledge 层对外部中台 API / 知识库的封装（具体 provider 实现）。
# 功能：实现 ApiOrderProvider、ApiCourseProvider（调 edu-data 订单/课程接口）、RagDefaultProvider、FaqDefaultProvider（占位返回），各自通过 retrival 返回知识片段。
# 入口：在 engines/builder 中实例化并注册到 KnowledgeRegister，运行时由 KnowledgeHandler 经 register 取出调用。
# 出口：atguigu.domain.state、atguigu.knowledge.provider.provider、atguigu.config.settings、atguigu.infrastructure（http_client）。
import asyncio
import json
from typing import Any

from atguigu.domain.state import DialogueState
from atguigu.knowledge.provider.provider import Provider, KnowledgeChunk
from atguigu.config.settings import settings
from atguigu.infrastructure import http_client


class ApiOrderProvider(Provider):
    provider_id = "api.order"

    async def retrival(self, state: DialogueState) -> list[KnowledgeChunk]:
        """
        调用 edu-data 订单查询接口，将查询到的数据封装到知识检索结果对象的content中

        Args:
            state:

        Returns:

        """
        focused_object = state.focused_object
        order_id = focused_object.id

        order_payload, items_payload = await asyncio.gather(
            self._fetch_order(order_id),
            self._fetch_order_items(order_id),
        )

        return [
            KnowledgeChunk(
                content="订单与明细信息：\n"
                        + json.dumps(
                    {
                        "order_id": order_id,
                        "order": order_payload,
                        "items": items_payload,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        ]

    async def _fetch_order(self, order_id) -> dict[str, Any]:
        url = f"{settings.commerce_api_base_url}/api/v1/orders/{order_id}"
        response = await http_client.http_client.get(url)
        return response.json()["data"]

    async def _fetch_order_items(self, order_id) -> list[dict[str, Any]]:
        url = f"{settings.commerce_api_base_url}/api/v1/orders/{order_id}/items"
        response = await http_client.http_client.get(url)
        data = response.json().get("data", {})
        return data.get("items", [])


class ApiCourseProvider(Provider):
    provider_id = "api.course"

    async def retrival(self, state: DialogueState) -> list[KnowledgeChunk]:
        """
        调用 edu-data 课程查询接口，将查询到的数据封装到知识检索结果对象的content中

        Args:
            state:

        Returns:

        """

        series_id = state.focused_object.id
        data: dict[str, Any] = await self._get_course_info_by_id(series_id)
        cohorts: list[dict[str, Any]] = await self._get_course_cohorts(series_id)
        text = json.dumps(
            {"course": data, "cohorts": cohorts},
            ensure_ascii=False,
            indent=2,
        )
        return [KnowledgeChunk(content=f"课程信息:\n{text}")]

    async def _get_course_info_by_id(self, series_id: str) -> dict[str, Any]:
        url = f"{settings.commerce_api_base_url}/api/v1/series/{series_id}"
        response = await http_client.http_client.get(url)
        return response.json()["data"]

    async def _get_course_cohorts(self, series_id: str) -> list[dict[str, Any]]:
        url = f"{settings.commerce_api_base_url}/api/v1/series/{series_id}/cohorts"
        response = await http_client.http_client.get(url)
        return response.json().get("data", [])


class RagDefaultProvider(Provider):
    provider_id = "rag.default"

    async def retrival(self, state: DialogueState) -> list[KnowledgeChunk]:
        """
        调用知识库（TODO) 自行接入

        Args:
            state:

        Returns:


        """
        return [KnowledgeChunk(content="未检索到相关信息")]


class FaqDefaultProvider(Provider):
    provider_id = "faq.default"

    async def retrival(self, state: DialogueState) -> list[KnowledgeChunk]:
        """
        调用常见问题集文档（TODO) 自行接入【语义检索：向量化】

        Args:
            state:

        Returns:


        """
        return [KnowledgeChunk(content="未检索到相关问题")]
