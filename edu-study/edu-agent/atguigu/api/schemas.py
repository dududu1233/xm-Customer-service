"""
定义接口数据模型：和前端进行交互
继承BaseModel:在运行期间完成类型的校验和类型的转换
"""
# 【接口数据模型 / 前后端契约】
# 这些类定义了"前端发来的数据"和"返回给前端的数据"长什么样。
# FastAPI 会据此自动做：校验（字段/类型对不对）+ 转换（JSON <-> Python 对象）
# 通俗说：这是前后端之间"单据的格式标准"
from typing import Any

from pydantic import BaseModel

from atguigu.domain.messages import ChatHistoryMessage


class ChatObject(BaseModel):
    # （补充）用户点击了某个卡片（商品 / 订单）时，带过来的卡片信息
    id: str  # 商品编号 or  订单编号
    title: str  # 商品标题 or  订单标题
    type: str  # 点击的商品卡片 type:"product" 点击的是订单卡片 type:"order"
    attributes: dict[str, Any]  # 商品or订单的额外信息


class ChatBotMessage(BaseModel):
    # （补充）机器人要回复给用户的单条消息
    text: str  # 机器人回复的内容（当下用的属性）
    object: ChatObject | None = None  # 后续扩展集成的属性


class ChatRequest(BaseModel):
    """
    聊天请求接口数据模型
    """
    # （补充）必填 sender_id；text 与 object 二选一（也可都有）
    sender_id: str
    text: str | None = None
    object: ChatObject | None = None


class ChatResponse(BaseModel):
    """
    聊天响应接口数据模型
    """
    message_id: str
    messages: list[ChatBotMessage]


class ChatHistoryResponse(BaseModel):
    # （补充）查历史记录的响应：返回某个用户的所有历史消息
    sender_id: str
    messages: list[ChatHistoryMessage]
