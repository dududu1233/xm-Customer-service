import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert  # 注意mysql包
# （补充）上面这行是 MySQL 专属的"插入或更新"语法（UPSERT）；换数据库就得改这里
# （补充）下面两个 import：DialogueState=要读写的"记忆卡"类型；DialogueRecord=数据库表对应的 ORM 类（见 dialogue_record.py）

from atguigu.domain.state import DialogueState
from atguigu.repository.dialogue_record import DialogueRecord


class DialogueRepository:
    # （补充）"档案柜管理员"：只负责把 DialogueState 在"内存对象"和"MySQL 文本"之间来回搬运，不含任何业务规则

    def __init__(self, session: AsyncSession):
        self._session = session

    async def load_state(self, sender_id: str) -> DialogueState:
        # （补充）读库入口：service.process_message 第①步会调用它，按用户ID把"记忆卡"从 MySQL 捞回内存
        """
        职责：根据用户ID ,读取完整的对话状态
        Args:
            sender_id:

        Returns:

        """

        # 1. 定义SQL语句
        stmt = select(DialogueRecord).where(DialogueRecord.sender_id == sender_id)

        # 2. 执行SQL语句
        cursor_result = await self._session.execute(stmt)

        # 3. 获取结果对象
        dialogue_record = cursor_result.scalar_one_or_none()
        # 3.1 用户不存在
        if dialogue_record is None:
            # （补充）第一次来的用户：发一张空白"记忆卡"，后续对话再往里填
            return DialogueState(sender_id=sender_id)

        # 3.2 用户已经存在
        dialogue_record_dict = json.loads(dialogue_record.state_json)
        # （补充）state_json 是之前存进去的文本，这里 json.loads 还原成 dict，再用 from_dict 变回 DialogueState 对象

        return DialogueState.from_dict(dialogue_record_dict)

    async def save_state(self,
                         sender_id: str,
                         dialogue_state: DialogueState):
        # （补充）写库入口：service.process_message 第③步调用它，把引擎改完的"记忆卡"落回 MySQL
        """
        职责：将引擎层修改后的对话状态保存到数据库中、
        如果用户之前不存在，调用save_state方法，像数据库中插入一条记录。
        如果用户之前存在， 调用save_state方法， 修改当前用户的state_json字段

        传统思路：插入记录之前，先根据sender_id查询，如果不存在在，保存 如果存在，修改
        SQL语句层面做：Insert or Update(唯一值：主键索引、唯一索引)
        MySQL:有插入和修改对应的升级SQL语句。

         INSERT INTO dialogue_states (sender_id, state_json) VALUES (%s, %s) AS new ON DUPLICATE KEY UPDATE state_json = new.state_json


        Args:
            sender_id:
            dialogue_state:

        Returns:

        """
        # 1.转换对话状态
        dialogue_state_dict = dialogue_state.to_dict()
        # （补充）先调 domain/state.py 的 to_dict()，把内存里的"记忆卡"变成普通 dict

        dialogue_state_str = json.dumps(dialogue_state_dict, ensure_ascii=False)
        # （补充）再把 dict 变成 JSON 文本字符串（ensure_ascii=False 让中文不乱码）

        # 2. 定义SQL语句
        # 2.1 定义INSERT的SQL语句
        insert_stmt = insert(DialogueRecord).values(sender_id=sender_id, state_json=dialogue_state_str)
        # （补充）insert(...) 是 SQLAlchemy 表达式写法（不是字符串SQL），描述"要往表里插这一行"

        # 2.2 定义UPDATE的SQL语句
        update_stmt = insert_stmt.on_duplicate_key_update(state_json=insert_stmt.inserted.state_json)
        # （补充）on_duplicate_key_update = 主键(sender_id)已存在就改新值，即"插入或更新" UPSERT

        # 3. 执行SQL语句
        await self._session.execute(update_stmt)
        # （补充）真正把 SQL 发给 MySQL 执行（执行了但还没"落盘"，要等 commit）

        # 4. 手动提交
        await self._session.commit()
        # （补充）commit 才让数据真正写入数据库；不 commit，前面 execute 的结果会被回滚丢掉
