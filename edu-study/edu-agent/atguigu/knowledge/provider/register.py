# === 文件：atguigu/knowledge/provider/register.py ===
# 角色：知识提供者的注册中心。
# 功能：KnowledgeRegister 以 provider_id 为键保存 Provider 实例，提供 get_provider_by_id 查询。
# 入口：被 KnowledgeHandler 调用；在 engines/builder 中初始化。
# 出口：atguigu.knowledge.provider.provider。
from atguigu.knowledge.provider.provider import Provider


class KnowledgeRegister:

    def __init__(self, providers: list[Provider]):
        self._providers: dict[str, Provider] = {provider.provider_id: provider for provider in providers}



    def  get_provider_by_id(self,provider_id:str)->Provider:
        return self._providers[provider_id]
