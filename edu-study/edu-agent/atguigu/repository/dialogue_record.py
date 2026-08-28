# === 文件：atguigu/repository/dialogue_record.py ===
# 角色：repository 层的 ORM 模型，描述对话状态在库中的存储结构。
# 功能：DialogueRecord(Base) 定义 dialogue_states 表（sender_id 主键 + state_json 文本列），用于持久化对话状态。
# 入口：被 repository/dialogue_repository（读写时引用该模型）使用。
# 出口：atguigu.repository.base。
from sqlalchemy.orm import Mapped,mapped_column
from  atguigu.repository.base import  Base
from sqlalchemy import  TEXT

class DialogueRecord(Base):
    __tablename__ = "dialogue_states"

    sender_id:Mapped[str]=mapped_column(primary_key=True)
    # Mapped:可以在ide中进行类型提示和自动补全，类型推断：自动推断数据库对应列的类型
    state_json:Mapped[str]=mapped_column(TEXT,nullable=False,default="{}")



