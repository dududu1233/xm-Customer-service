"""
定义路由
"""
# 【接口层 / HTTP 入口】定义所有对外暴露的路由（URL 地址）
# 这一层只做"翻译"：把前端发来的 JSON 转成内部对象、把内部结果转回 JSON
# 不包含任何业务逻辑，真正的活都交给 services / engines 去干
import uuid
from dataclasses import dataclass
from fastapi import APIRouter

from atguigu.api.schemas import ChatResponse, ChatRequest, ChatBotMessage, ChatObject, ChatHistoryResponse
from atguigu.domain.messages import UserMessage, ProcessedResult, MessageType, FocusedObject
from atguigu.api.dependencies import DialogueStateServiceDep

router = APIRouter()


@router.get("/")
def hello_endpoint():
    """
    接口响应层：FASTAPI自动会将接口返回的对象序列化为json格式字符串:序列化
    接口请求处理层： FASTAPI自动的将前端发送的json格式字符串反序列化成数据模型对象【数据模型出来】：反序列化

    Returns:

    """
    # （补充）探活接口（health check）：用来快速确认"后端是不是活着"
    # 浏览器直接访问 http://localhost:18082/ 就能看到 {"success":"ok"}
    # 不碰数据库、不碰业务，最安全的冒烟测试
    return {"success": "ok"}


@dataclass(slots=True)
class User:
    """仅用于下方 /test 演示接口的返回结构示例，和真实业务无关"""
    name: str
    age: int
    address: str


@router.get("/test", response_model=User)
def test_endpoint():
    """
    response_model:
    作用1：校验器作用
    作用2：过滤器作用
    作用3：生成丰富的接口文档信息（作用）
    Returns:

    """
    # （补充）返回里多了个 card_no 字段，因为 User 里没定义它，会被自动过滤掉
    return {
        "name": "zs",
        "age": "18",
        "address": "sz",
        "card_no": "xxxxxxxabcdddddddd"   # 这个字段在 User 里没有，会被 response_model 过滤掉
    }


@router.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest,
                        service: DialogueStateServiceDep):
    # （补充）核心对话接口：用户发一句话进来，返回客服的回复
    # 一次请求生命周期：前端 JSON ──(1)──> 内部 UserMessage ──(2)──> service 处理 ──(3)──> 前端 JSON
    # 1.将接口数据模型转成领域数据模型
    user_message = _build_user_message(chat_request)

    # 2.调用service处理领域数据模型---返回的还是领域数据模型
    # （补充）service 会去读状态、调引擎、存状态
    processed_result = await service.process_message(user_message)

    # 3. 将处理后的领域数据 模型转成接口数据模型
    chat_response = _build_chat_response(processed_result)

    return chat_response


def _build_user_message(chat_request: ChatRequest) -> UserMessage:
    """
    职责：接口数据模型转成领域数据模型
    Args:
        chat_request:

    Returns:

    """
    # （补充）如果带了 object（点了商品/订单卡片），就标记为 OBJECT 类型，否则是普通 TEXT 文本
    return UserMessage(
        sender_id=chat_request.sender_id,                 # 谁发的（用户唯一标识）
        message_id=str(uuid.uuid4().hex),                # 给这条消息生成一个唯一 ID
        type=MessageType.OBJECT if chat_request.object is not None else MessageType.TEXT,
        text=chat_request.text,                          # 用户实际输入的文字
        object=FocusedObject(
            id=chat_request.object.id,
            type=chat_request.object.type,
            title=chat_request.object.title,
            attributes=chat_request.object.attributes,
        ) if chat_request.object is not None else None   # 没点卡片就为 None
    )


def _build_chat_response(processed_result: ProcessedResult) -> ChatResponse:
    """
     职责：处理后的领域数据模型转成接口数据模型
    Args:
        processed_result:

    Returns:

    """
    # （补充）把内部每条机器人消息，逐个转成接口用的 ChatBotMessage
    return ChatResponse(
        message_id=processed_result.message_id,
        messages=[
            ChatBotMessage(
                text=bot_message.text,
                object=ChatObject(
                    id=bot_message.object.id,
                    type=bot_message.object.type,
                    title=bot_message.object.title,
                    attributes=bot_message.object.attributes
                ) if bot_message.object is not None else None
            )
            for bot_message in processed_result.messages
        ]
    )


@router.get("/api/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history_endpoint(sender_id: str,
                                    service: DialogueStateServiceDep):
    # （补充）查历史记录接口：根据 sender_id 拉取这个用户的历史对话
    # 例如 /api/chat/history?sender_id=user123
    chat_history_messages = await service.get_chat_history(sender_id)

    return ChatHistoryResponse(sender_id=sender_id, messages=chat_history_messages)
