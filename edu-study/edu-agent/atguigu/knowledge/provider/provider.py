# === 文件：atguigu/knowledge/provider/provider.py ===
# 角色：知识提供者的抽象基类与返回结构定义。
# 功能：定义 KnowledgeChunk（检索片段）与抽象类 Provider（含 provider_id 与异步 retrival 接口）。
# 入口：被 knowledge/provider/knowledge.py 的各类 provider 继承，被 register.py 引用类型。
# 出口：atguigu.domain.state。
from abc import ABC, abstractmethod
from dataclasses import dataclass

from atguigu.domain.state import DialogueState


@dataclass(slots=True)
class KnowledgeChunk:
    content: str


class Provider(ABC):
    provider_id: str

    @abstractmethod
    async def retrival(self, state: DialogueState) -> list[KnowledgeChunk]:
        pass
