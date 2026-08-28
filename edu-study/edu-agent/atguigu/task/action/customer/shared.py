# === 文件：atguigu/task/action/customer/shared.py ===
# 角色：自定义 action 共用的 HTTP 工具函数集合。
# 功能：封装 _base_url/_extract_data、fetch_order（订单号→orderId 解析后查 edu-data 订单+明细），统一向 edu-data 发 GET 请求并做异常兜底返回 None。
# 入口：被各 customer action（lookup_order_status 等）调用。
# 出口：atguigu.config.settings、atguigu.infrastructure（http_client）。
"""
封装自定义action统一发请求的工具函数
"""



from atguigu.config.settings import settings
from atguigu.infrastructure import http_client


def _base_url() -> str:
    """
    职责：获取 edu-data 服务的根地址
    Returns:

    """
    return settings.commerce_api_base_url.rstrip("/")


def _extract_data(result: dict | None) -> dict | None:
    """
    职责：从响应结果中获取真实的字典数据
    Args:
        result:

    Returns:

    """
    data = result.get("data") if isinstance(result, dict) else None
    return data if isinstance(data, dict) else None


async def fetch_order(order_id_input: str) -> dict | None:
    """
    职责：根据用户输入（订单号 ORD... 或数字 orderId）获取订单完整数据
    流程：拉取该用户订单列表(最多100条) → 本地匹配 orderNo/orderId → 命中后调详情与明细

    Args:
        order_id_input: 用户输入的订单号或订单ID

    Returns:
        dict: 包含 orderId/orderNo/orderStatusCode/totalAmount/payableAmount/items 等字段，失败返回 None
    """
    try:
        # 1. 拉取当前用户的订单列表（需要 X-User-Id，由 http_client 钩子自动注入）
        r = await http_client.http_client.get(
            f"{_base_url()}/api/v1/orders?pageNo=1&pageSize=100"
        )
        data = _extract_data(r.json()) or {}
    except Exception:
        return None

    items = data.get("list", []) or []
    if not items:
        return None

    # 2. 本地匹配：orderId 等于输入 或 orderNo 包含输入
    target = str(order_id_input).strip()
    matched = None
    for o in items:
        if target and target == str(o.get("orderId", "")):
            matched = o
            break
        if target and target in str(o.get("orderNo", "")):
            matched = o
            break
    if matched is None:
        return None

    order_id = matched["orderId"]

    # 3. 取订单详情与明细
    try:
        r2 = await http_client.http_client.get(f"{_base_url()}/api/v1/orders/{order_id}")
        detail = _extract_data(r2.json()) or {}
    except Exception:
        detail = {}
    try:
        r3 = await http_client.http_client.get(f"{_base_url()}/api/v1/orders/{order_id}/items")
        items_data = _extract_data(r3.json()) or {}
        detail["items"] = items_data.get("items", [])
    except Exception:
        detail["items"] = []
    # 携带订单号（列表里有，详情里没有）
    detail.setdefault("orderNo", matched.get("orderNo"))
    return detail if detail else None


async def fetch_logistics(order_id: str) -> dict | None:
    """
    兼容旧 action（lookup_logistics.py）import。教育场景不使用，保留以避免 ImportError。
    """
    return None


async def fetch_product(product_id: str) -> dict | None:
    """
    兼容旧 action（recommend_similar_products.py）import。教育场景不使用，保留以避免 ImportError。
    """
    return None
