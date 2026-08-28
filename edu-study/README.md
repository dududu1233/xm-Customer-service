# 教育智能客服系统

基于「大模型 + 任务流程编排」的教育领域智能客服系统。系统由两个服务组成：**edu-data**（业务数据底座）与 **edu-agent**（AI 对话大脑）。AI 通过调用业务底座的 HTTP 接口，完成课程咨询、订单查询、学习进度查询、退款申请、工单提交等完整业务闭环。

---

## 一、项目结构

```
edu-study/
├── edu-data/                 # ① 业务数据底座（纯后端，提供教育业务 API）
│   ├── app/
│   │   ├── main.py           #    启动入口（FastAPI + 13 个业务路由）
│   │   ├── routers/          #    业务接口：orders/payments/tickets/courses/enrollments…
│   │   ├── database.py       #    数据库连接（pymysql）
│   │   └── config.py         #    配置（读 .env）
│   ├── .env                  #    数据库连接配置
│   └── pyproject.toml
│
├── edu-agent/                # ② AI 对话大脑（LLM + 任务流程编排）
│   ├── atguigu/              #    核心包（分层架构）
│   │   ├── main.py           #      启动入口
│   │   ├── api/              #      对外接口层（/api/chat、/api/chat/history）
│   │   ├── services/         #      服务层（对话状态管理）
│   │   ├── engines/          #      引擎层（对话引擎、总装配）
│   │   ├── plan/             #      规划层（LLM 路由分析）
│   │   ├── task/             #      任务流程层（flows + action）
│   │   ├── knowledge/        #      知识层（意图 + provider）
│   │   ├── infrastructure/   #      基础设施（LLM 客户端、HTTP 客户端）
│   │   └── domain/           #      领域模型（对话状态）
│   ├── flow_config/          #    流程配置（YAML，新增业务流程只改这里）
│   │   ├── user_flows.yml    #      业务流程定义
│   │   └── system_flows.yml  #      系统流程定义
│   ├── static/               #    前端调试页
│   │   └── index.html
│   └── .env                  #    LLM 配置 + 底座地址 + 状态库
│
├── pyproject.toml            # 统一依赖配置
└── .venv/                    # 共享虚拟环境（两个服务共用）
```

### 核心分层（edu-agent / atguigu）

```
api 层（收 HTTP 请求）
  └─ services 层（对话状态管理，收消息→处理→存状态）
       └─ engines 层（对话引擎，消息分派）
            ├─ plan 层（LLM 路由分析：task / knowledge / chitchat）
            │     ├─ task      → task 层（flow + action 编排）
            │     ├─ knowledge → knowledge 层（意图 + provider 查数据）
            │     └─ chitchat  → chitchat 层（闲聊）
            └─ infrastructure（LLM 客户端 / HTTP 客户端）
```

---

## 二、技术栈

| 组件 | 说明 |
|---|---|
| 语言 | Python 3.12 |
| Web 框架 | FastAPI + Uvicorn |
| 大模型 | 通义千问（DashScope，OpenAI 兼容协议）|
| LLM 编排 | LangChain（PromptTemplate / JsonOutputParser / init_chat_model）|
| 数据库 | MySQL（业务库 `edu` + 对话状态库 `edu_agent`）|
| 数据访问 | edu-data 用 pymysql，edu-agent 用 asyncmy |
| 配置 | python-dotenv + pydantic-settings |

---

## 三、环境准备

### 1. 依赖安装

两个服务共用 `edu-study/.venv`。在 `edu-study/` 目录下执行：

```bash
uv sync
# 或
./.venv/Scripts/python.exe -m pip install -r <依赖>
```

依赖统一声明在 `edu-study/pyproject.toml`（agent 层 + data 层已合并）。

### 2. 数据库初始化

确保 MySQL 已启动（默认 127.0.0.1:3306，root / 123321）：

- **业务库 `edu`**：edu-data 首次启动前需初始化建表并导入样本数据（见 `edu-data` 目录下的 `init_db.py` 与 `generate/` 数据生成脚本）。
- **对话状态库 `edu_agent`**：存对话状态，表结构如下（已手动建好）：

```sql
CREATE DATABASE IF NOT EXISTS edu_agent CHARACTER SET utf8mb4;
USE edu_agent;
CREATE TABLE IF NOT EXISTS dialogue_states (
    sender_id VARCHAR(128) NOT NULL,
    state_json TEXT NOT NULL,
    PRIMARY KEY (sender_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 3. 配置

- `edu-data/.env`：数据库连接（DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME）
- `edu-agent/.env`：LLM 配置 + 底座地址 + 状态库连接

---

## 四、启动说明

**顺序很重要：先启动 edu-data（底座），再启动 edu-agent（大脑）。**

### 第 1 步：启动 edu-data（业务底座，端口 8000）

```bash
cd edu-study/edu-data
../.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
```

看到 `Uvicorn running on http://0.0.0.0:8000` 即成功。**窗口保持打开。**

### 第 2 步：启动 edu-agent（AI 大脑，端口 18082）

```bash
cd edu-study/edu-agent
../.venv/Scripts/python.exe atguigu/main.py
```

看到 `Uvicorn running on http://0.0.0.0:18082` 即成功。**窗口保持打开。**

### 第 3 步：打开前端调试页

浏览器访问：

```
http://127.0.0.1:18082/static/index.html
```

> 说明：edu-agent 已通过 FastAPI `StaticFiles` 托管 `static/` 目录，并配置 CORS，页面与接口同源，无跨域问题。

---

## 五、核心接口

### edu-agent（对话大脑）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 健康检查，返回 `{"success":"ok"}` |
| POST | `/api/chat` | 对话主接口，body：`{"sender_id":"281","text":"你好"}` |
| GET | `/api/chat/history?sender_id=281` | 获取会话历史 |

### edu-data（业务底座，均需请求头 `X-User-Id`）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/orders` | 订单列表 |
| GET | `/api/v1/orders/{id}` | 订单详情 |
| GET | `/api/v1/orders/{id}/items` | 订单明细（新增，供退款/工单取 orderItemId）|
| GET | `/api/v1/me/cohorts` | 我的班次 |
| GET | `/api/v1/me/cohorts/{id}/progress` | 学习进度 |
| GET | `/api/v1/series?keyword=` | 课程搜索 |
| GET | `/api/v1/series/{id}/cohorts` | 课程班次 |
| POST | `/api/v1/order-items/{id}/refund-requests` | 提交退款申请 |
| POST | `/api/v1/service-tickets` | 提交工单 |

---

## 六、业务能力清单

| 能力 | 实现方式 | 对应流程 / 意图 |
|---|---|---|
| 课程咨询 | knowledge 轨道 → `course_info` → `ApiCourseProvider` 调课程接口 | `course_info` |
| 订单查询 | task 轨道 → `order_status_query` → `action_lookup_order_status` | `order_status_query` |
| 学习进度查询 | task 轨道 → `study_progress_query` → `action_lookup_study_progress` | `study_progress_query` |
| 退款申请 | task 轨道 → `refund_request` → `action_submit_refund`（真实提交）| `refund_request` |
| 工单提交 | task 轨道 → `ticket_submit` → `action_submit_ticket`（真实提交）| `ticket_submit` |
| 闲聊 / 澄清 | chitchat / clarify 轨道 | — |

### 扩展新业务流程（不改核心代码）

1. 在 `flow_config/user_flows.yml` 新增 flow（声明 steps 与 slots）
2. 在 `atguigu/task/action/customer/` 下新增 action 类（自动发现注册）
3. 如需查新数据，在 `atguigu/knowledge/provider/knowledge.py` 加 provider

---

## 七、验收演示脚本

以下对话序列可完整演示业务闭环（用户 ID `281`，拥有订单 `ORD0000033548`）：

```
1. 你好
2. 查一下我的订单 ORD0000033548 的状态
3. 查一下通用编程入门班的学习进度
4. 我要申请退款          → 订单号 ORD0000033548 → 课程太难，跟不上
5. 我要提交工单          → 订单号 ORD0000033548 → 技术问题 → 视频播放卡顿
```

---

## 八、常见问题

| 问题 | 原因 | 解决 |
|---|---|---|
| 启动报 `ModuleNotFoundError: tzdata` | Windows 缺时区数据 | 安装 `tzdata` |
| 对话返回 403 | DashScope 免费额度耗尽 | 换模型（`.env` 的 `llm_model`）或充值 |
| agent 查不到订单 | 订单不属于该用户 | 确认 `sender_id` 与 `X-User-Id` 对应用户 |
| 端口被占用 | 服务已在运行 | `netstat -ano \| findstr :8000` 查 PID 后结束 |
