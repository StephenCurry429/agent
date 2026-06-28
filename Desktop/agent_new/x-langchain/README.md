# x-langchain

> LangChain 学习与实践项目 - 构建生产级 LLM 应用的最佳实践指南

`x-langchain` 是一个完整的 LangChain 学习与实践项目，旨在帮助开发者系统学习和掌握 LangChain 框架的核心概念与应用方法。本项目通过实际案例展示如何使用 LangChain 构建大语言模型应用，包括模型集成、工具调用、上下文管理等关键功能，为 LangChain 初学者和进阶开发者提供实践参考。

**核心价值**：开箱即用的多模型支持、插件化工具系统、完整的 TextToSQL 解决方案、前后端分离架构

**适用场景**：智能客服、数据查询助手、企业知识库问答、LLM 应用原型开发

---

## 什么是 LangChain？

- **官方定义**："LangChain is a framework for developing applications powered by large language models"
- **Gartner 描述**："LLM application development frameworks like LangChain"

简单来说，`LangChain` 是一个帮助开发者快速构建基于大语言模型（LLM）应用的开发框架。

---

## 核心特性

- **多模型兼容** - 支持 DeepSeek、豆包、阿里云通义千问、OpenAI 兼容接口等主流 LLM 后端
- **记忆系统** - 双层记忆架构：
  - **语义记忆**：ChromaDB + 本地嵌入模型（BAAI/bge-small-zh-v1.5），支持跨会话语义检索召回
  - **生成式记忆**：Memory Stream 架构，含重要性评分（LLM 自动打分）、时效衰减、反思提炼、分层规划
- **RAG 检索引擎** - 6 种检索策略：BM25 关键词、语义向量、MMR 多样性、RRF 混合融合、全融合（语义+MMR+BM25）、Cross-Encoder 精排序；支持查询扩展
- **上下文压缩** - 4 层上下文注入：语义记忆 + 生成式记忆 + 历史摘要 + 最近 N 条消息，自动裁剪超长上下文
- **工具调用（Function Calling）** - 通过声明式接口集成外部 API 与业务系统
- **TextToSQL 功能** - 支持自然语言到 SQL 的转换，包括问题重写、Schema 解析、SQL 生成、验证和执行
- **MCP 协议支持** - 集成 Model Context Protocol，支持 MCP 工具调用
- **上下文管理** - 内置对话历史管理，支持连续对话
- **安全合规** - API 密钥管理（从环境变量加载，避免硬编码）、输入/输出内容过滤
- **可观测性** - 集成结构化日志系统，便于监控和调试
- **插件化架构** - 基于装饰器的工具自动注册，支持热插拔
- **前后端分离** - 提供完整的 Web 前端界面和 RESTful API 服务

---

## 技术栈

| 类别 | 技术 |
|------|------|
| **核心框架** | LangChain, LangGraph |
| **模型集成** | langchain-openai, langchain-community, dashscope |
| **配置管理** | pydantic-settings, python-dotenv |
| **工具库** | duckduckgo-search, sqlalchemy, pymysql |
| **MCP 协议** | langchain-mcp-adapters |
| **日志系统** | loguru |
| **向量数据库** | ChromaDB |
| **嵌入模型** | sentence-transformers (BAAI/bge-small-zh-v1.5) |
| **重排序** | CrossEncoder (BAAI/bge-reranker-base) |
| **分词** | jieba |
| **后端服务** | FastAPI, Uvicorn |
| **前端技术** | HTML5, CSS3, JavaScript (ES6+) |
| **包管理** | uv / pip |
| **部署** | Docker |

---

## 项目结构

```
x-langchain/
├── src/                                # 源代码目录
│   ├── main.py                         # 项目主入口，CLI 交互接口
│   ├── core/                           # 核心模块
│   │   ├── config.py                   # 配置类，环境变量加载
│   │   ├── logger.py                   # 日志系统
│   │   ├── semantic_memory.py          # 语义会话记忆（ChromaDB 向量存储）
│   │   └── context_compressor.py       # 上下文压缩器（4 层注入）
│   ├── constants/                      # 常量模块
│   │   ├── develop.py                  # 开发相关常量
│   │   └── streaming_modes.py          # 流式传输模式
│   ├── models/                         # 模型管理模块
│   │   └── providers.py                # 模型提供者与统一模型创建入口
│   ├── agents/                         # Agent 模块
│   │   ├── agent.py                    # LangGraph Agent 定义
│   │   ├── agent_factory.py            # Agent 工厂
│   │   ├── generative_agent.py         # 生成式 Agent（Memory Stream + 反思 + 规划）
│   │   └── fallback_agent.py           # 降级 Agent
│   ├── rag/                            # RAG 检索引擎模块
│   │   ├── vector_store.py             # 向量存储 + 6 种检索策略
│   │   └── rag_tool.py                 # RAG 工具封装
│   ├── tools/                          # 工具模块
│   │   ├── registry.py                 # 工具注册表
│   │   ├── web_tool.py                 # 网络搜索（DuckDuckGo）
│   │   ├── weather_tool.py             # 天气查询（高德地图 API）
│   │   ├── calendar_tool.py            # 日历查询
│   │   ├── exchange_rate_tool.py       # 汇率查询
│   │   ├── current_time_tool.py        # 当前时间查询
│   │   ├── code_sandbox_tool.py        # 代码沙箱
│   │   ├── mcp_tool_custom.py          # MCP 工具封装
│   │   ├── qiuchi_mcp/                 # 秋池 MCP 工具包
│   │   └── text_to_sql/                # TextToSQL 工具链
│   │       ├── question_rewrite_tool.py
│   │       ├── get_schema_tool.py
│   │       ├── generate_sql_tool.py
│   │       ├── validate_sql_tool.py
│   │       ├── execute_sql_tool.py
│   │       └── convert_to_natural_language_tool.py
│   └── clients/                        # 客户端模块
│       └── db/                         # 数据库客户端
│           └── client.py
├── backend/                            # 后端 API 服务
│   └── app.py                          # FastAPI 服务入口
├── frontend/                           # 前端界面
│   ├── index.html                      # 单文件前端（HTML + CSS + JS）
│   └── SilkChatBubble.jsx             # Silk 设计系统聊天组件
├── data/                               # 运行时数据
│   ├── semantic_memory/                # 语义记忆向量库
│   ├── generative_memory/              # 生成式记忆数据
│   ├── chat_history/                   # 对话历史快照
│   └── rag/                            # RAG 知识库文档
├── tests/                              # 测试模块
├── docs/                               # 文档目录
├── examples/                           # 示例代码
├── .env.example                        # 环境变量配置示例
├── pyproject.toml                      # 项目元数据和依赖
├── Dockerfile                          # Docker 构建文件
└── README.md                           # 项目文档
```

---

## 系统架构

### 分层架构图

```mermaid
graph TB
    subgraph 用户层
        CLI[命令行接口<br/>main.py]
        WEB[Web 前端<br/>frontend/]
    end

    subgraph API层
        API[FastAPI 服务<br/>backend/app.py]
    end

    subgraph 应用层
        AF[Agent 工厂<br/>agent_factory.py]
        AG[Agent 实例]
        GA[生成式 Agent<br/>generative_agent.py]
    end

    subgraph 模型层
        MF[模型提供者<br/>providers.py]
        DS[DeepSeek]
        DB[豆包]
        TY[通义千问]
        MK[Mock 模型]
        OAI[OpenAI 兼容]
    end

    subgraph 记忆与检索层
        SM[语义记忆<br/>ChromaDB]
        GM[生成式记忆<br/>Memory Stream]
        RG[RAG 引擎<br/>vector_store.py]
        CC[上下文压缩<br/>context_compressor.py]
    end

    subgraph 工具层
        subgraph 本地工具
            WT[天气工具]
            CT[日历工具]
            WS[网络搜索]
            ER[汇率查询]
            CD[代码沙箱]
            TI[当前时间]
        end
        subgraph MCP 工具
            WMCP[天气 MCP]
            QMCP[秋池 MCP]
        end
        subgraph TextToSQL
            QR[问题重写]
            GS[获取 Schema]
            SG[生成 SQL]
            VS[验证 SQL]
            ES[执行 SQL]
            CN[结果转换]
        end
    end

    subgraph 基础设施层
        CFG[配置管理<br/>config.py]
        LOG[日志系统<br/>logger.py]
        DBC[数据库客户端<br/>db/client.py]
    end

    CLI --> AF
    WEB --> API --> AF
    AF --> AG
    AF --> MF
    AF --> CC
    MF --> DS & DB & TY & MK & OAI
    AG --> WT & CT & WS & ER & CD & TI & WMCP & QMCP
    AG --> QR --> GS --> SG --> VS --> ES --> CN
    GA --> SM & GM
    CC --> SM & GM
    RG --> SM

    CFG -.-> AF & MF
    LOG -.-> AF & MF & AG & GA
    DBC -.-> ES & GS
```

---

## 快速开始

### 环境要求

| 环境 | 要求 |
|------|------|
| **Windows** | Python 3.11+, 推荐使用 PowerShell 或 Git Bash |
| **Linux/macOS** | Python 3.11+, 任意 Shell |

> 推荐使用 [`uv`](https://github.com/astral-sh/uv) 作为包管理器，亦可兼容 `pip`

### 项目克隆

```bash
git clone https://gitee.com/chain-engine/x-langchain.git
cd x-langchain
```

### 依赖安装

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -e .

# 安装后端依赖（FastAPI）
pip install fastapi uvicorn

# 安装可选依赖（记忆系统 + RAG 检索）
pip install chromadb sentence-transformers jieba
```

### 配置文件创建

```bash
# 复制配置模板
cp .env.example .env
```

编辑 `.env` 文件，配置必要的 API 密钥：

```env
# ====================================
# 模型 API 配置（至少配置一组）
# ====================================

# OpenAI 兼容接口（支持本地代理如 mimo/ollama）
# OPENAI_API_KEY=your-api-key
# OPENAI_BASE_URL=http://localhost:8317/v1

# DeepSeek API
# DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# DEEPSEEK_API_BASE=https://api.deepseek.com/v1
# DEEPSEEK_MODEL_NAME=deepseek-chat

# 豆包 API
# DOUBAO_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# DOUBAO_API_BASE=https://ark.cn-beijing.volces.com/api/v3
# DOUBAO_MODEL_NAME=ep-xxxxxxxxxxxxxx

# 阿里云通义千问 API
# ALIYUN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# ALIYUN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
# ALIYUN_MODEL_NAME=qwen-plus

# ====================================
# 外部服务 API 配置
# ====================================

# 高德地图 API 配置（天气查询工具需要）
# AMAP_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# LangSmith 可观测性配置
# LANGSMITH_API_KEY=lsv2_pt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx_xxxxxxxxxxxxx

# ====================================
# 数据库配置（TextToSQL 功能需要）
# ====================================

# DB_HOST=localhost
# DB_PORT=3306
# DB_USER=root
# DB_PASSWORD=your_password
# DB_NAME=your_database

# 或者使用完整数据库 URL（优先级高于分项配置）
# DB_URL=mysql+pymysql://user:password@localhost:3306/db_name

# ====================================
# 通用配置
# ====================================

MODEL_NAME=deepseek     # 默认模型：deepseek / doubao / tongyi / mock
TEMPERATURE=0.0         # LLM 温度参数 (0.0-2.0)
DEBUG=False             # 调试模式
STRUCTURED=False        # 结构化输出模式

# TextToSQL 专用模型（默认使用 MODEL_NAME）
# TEXT_TO_SQL_MODEL_NAME=deepseek

# TextToSQL 安全限制
TEXT_TO_SQL_MAX_ROWS=100
TEXT_TO_SQL_QUERY_TIMEOUT=30

# ====================================
# MCP 服务器配置（可选）
# ====================================

# 天气 MCP 服务器
# WEATHER_MCP_BASE_URL=http://localhost:8000
# WEATHER_MCP_PATH=/mcp
# WEATHER_MCP_MODE=http

# 秋池 MCP 服务器
# QIUCHI_MCP_BASE_URL=http://localhost:8000
# QIUCHI_MCP_PATH=/mcp
# QIUCHI_MCP_MODE=http

# MCP 工具默认关闭，配置好 MCP 服务后设为 True
MCP_ENABLED=False
```

### 启动方式

#### 方式一：命令行交互模式

```bash
# 使用默认模型（DeepSeek）
uv run src/main.py

# 或使用已安装的命令行入口
uv run x-langchain

# 通过环境变量指定模型
MODEL_NAME=deepseek uv run src/main.py
MODEL_NAME=doubao uv run src/main.py
MODEL_NAME=tongyi uv run src/main.py
```

#### 方式二：后端 API 服务

```bash
# 启动后端服务（端口 8000）
python backend/app.py
```

#### 方式三：前端界面

```bash
# 启动前端静态文件服务（端口 8080）
cd frontend
python -m http.server 8080
```

#### 方式四：Docker 启动

```bash
# 构建镜像
docker build -t x-langchain:latest .

# 运行容器（挂载配置和日志目录）
docker run -it --rm \
  -v $(pwd)/.env:/app/.env:ro \
  -v $(pwd)/logs:/app/logs \
  x-langchain:latest

# Windows PowerShell
docker run -it --rm `
  -v ${PWD}/.env:/app/.env:ro `
  -v ${PWD}/logs:/app/logs `
  x-langchain:latest
```

### 常用命令

```bash
# 运行测试
uv run python -m pytest

# 运行特定测试模块
uv run python -m pytest tests/test_providers.py -v

# 代码格式化（如果安装了 ruff）
uv run ruff format .

# 类型检查（如果安装了 pyright）
uv run pyright
```

---

## 使用方法

### 交互式对话模式

启动程序后，进入交互式对话模式：

```bash
$ uv run src/main.py

==================================================
欢迎使用智能助手！输入 'exit'、'quit' 或 '退出' 结束对话
==================================================

你: 上海天气怎么样？

2026-03-05 10:00:00,123 - INFO - 查询结果:
上海今天多云，气温 18°C，东风 3级，湿度 65%，空气质量良好。

你: 帮我查询数据库中的用户数量

2026-03-05 10:01:00,456 - INFO - 查询结果:
根据数据库查询，当前系统中有 150 个用户。

你: exit

感谢使用，再见！
```

### Web 前端界面

1. 启动后端服务：`python backend/app.py`
2. 启动前端服务：`cd frontend && python -m http.server 8080`
3. 在浏览器中访问：`http://localhost:8080`

前端功能特性：
- 现代化深色/浅色双主题 UI 设计
- 实时流式聊天响应 + Token 逐字渲染
- 思考链五阶段可视化（拆解→推理→工具调用→校验→总结）+ 实时状态指示
- 对话历史保存（本地存储 + JSON 导出 + 侧边栏浏览）
- 搜索资源/搜索摘要智能折叠卡片
- 对话导出（Markdown / Word）
- 话题新会话（重置记忆上下文）
- 响应式设计，支持移动端

### API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 前端页面 |
| `/health` | GET | 健康检查 |
| `/chat` | POST | 非流式聊天 |
| `/chat/stream` | POST | 流式聊天（思考链 + 搜索源 + token） |
| `/config/model` | GET / POST | 查看/修改模型配置 |
| `/skills` | GET | 工具列表 |
| `/logs` | GET | 日志查询 |
| `/export/docx` | POST | 导出 Word 文档 |
| `/rag/upload` | POST | RAG 文档上传 |
| `/rag/documents` | GET | RAG 文档列表 |
| `/rag/search` | GET | RAG 语义检索 |
| **DELETE** `/rag/documents/{filename}` | DELETE | 删除 RAG 文档 |

**请求示例**：

```bash
# 健康检查
curl http://localhost:8000/health

# 非流式聊天
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'

# 流式聊天
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "介绍一下你自己"}'

# RAG 文档上传
curl -X POST http://localhost:8000/rag/upload \
  -F "file=@document.pdf"

# RAG 语义检索
curl "http://localhost:8000/rag/search?q=查询关键词&k=4"

# 文档列表
curl http://localhost:8000/rag/documents
```

### 模型选择

通过环境变量 `MODEL_NAME` 指定模型：

| 模型 | 环境变量 | 说明 |
|------|---------|------|
| DeepSeek | `MODEL_NAME=deepseek` | 默认模型，性价比高 |
| 豆包 | `MODEL_NAME=doubao` | 字节跳动出品 |
| 通义千问 | `MODEL_NAME=tongyi` | 阿里云出品 |
| OpenAI 兼容 | `MODEL_NAME=openai` | 兼容 OpenAI 接口的第三方代理（mimo/ollama 等） |
| Mock | `MODEL_NAME=mock` | 本地模拟模型，无需 API Key |

```bash
# 使用 DeepSeek（默认）
uv run src/main.py

# 使用豆包
MODEL_NAME=doubao uv run src/main.py

# 使用通义千问
MODEL_NAME=tongyi uv run src/main.py

# 使用 OpenAI 兼容接口（需配置 OPENAI_API_KEY + OPENAI_BASE_URL）
MODEL_NAME=openai uv run src/main.py

# 使用 Mock 模型（无需 API Key）
MODEL_NAME=mock python backend/app.py
```

---

## 记忆系统与 RAG 检索

### 双层记忆架构

x-langchain 实现了双层记忆系统，为 Agent 提供跨会话、跨时间的智能记忆能力：

**1. 语义记忆 (Semantic Memory)**
- 基于 ChromaDB 向量数据库 + `BAAI/bge-small-zh-v1.5` 本地嵌入模型
- 每轮对话自动存入向量库，新问题时语义检索相关历史
- 支持中文关键词 BM25 后备检索，混合评分排序
- 4 层上下文注入：语义记忆 → 生成式记忆 → 历史摘要 → 最近消息

**2. 生成式记忆 (Generative Memory)**
- 基于 Stanford "Generative Agents" 论文的 Memory Stream 架构
- 每条记忆经 LLM 自动重要性评分（1-10 分）
- 检索得分 = `0.3 × 时效衰减 + 0.4 × 重要性 + 0.3 × 关键词相关性`
- 内置反思（Reflection）和分层规划（Planning）机制

### RAG 检索引擎

x-langchain 内置了一套完整的 RAG 检索引擎，核心技术特点：

**多角度查询扩展**
- 自动去除疑问词/语气词，提取核心查询
- 按标点拆分为多个子问题，从不同角度检索
- 最多生成 3 个查询变体，多路结果 RRF 融合，提高召回率

**多维度检索策略**

| 检索策略 | 算法 | 说明 |
|----------|------|------|
| `semantic` | 语义向量 | 纯 cosine 相似度检索，理解语义含义 |
| `bm25` | BM25 关键词 | 词频 + IDF 逆文档频率，精确匹配专有名词/术语 |
| `mmr` | MMR 最大边际相关性 | 语义相似度 + 结果去重（λ=0.6），保证多样性 |
| `hybrid` | **[推荐]** RRF 倒数秩融合 | 双路融合：语义（权重 0.6）+ BM25（权重 0.4），兼顾语义与关键词 |
| `all` | 三路 RRF 融合 | 全维度融合：语义（0.4）+ MMR（0.2）+ BM25（0.4），最高召回率 |
| `cross_encoder` | Cross-Encoder 精排 | BAAI/bge-reranker-base 对候选结果逐对打分重排，大幅提升精度 |

**文档管理（增/删/查）**

| 操作 | 方法 | 说明 |
|------|------|------|
| 上传文档 | `add_document(path)` | 支持 TXT/PDF/DOCX/MD，自动分块（chunk=800, overlap=100）并向量化 |
| 删除文档 | `delete_document(filename)` | 从向量库中删除该文档的所有分块，同时删除源文件 |
| 文档列表 | `list_documents()` | 列出所有已索引的文档及文件大小 |
| 清空 | `clear()` | 清空全部向量库和源文件 |

**Embedding 模型自动回退链**
1. `text-embedding-3-small` @ OpenAI 兼容接口
2. `text-embedding-ada-002` @ OpenAI 兼容接口
3. `text-embedding-3-small` @ DeepSeek 接口
4. `BAAI/bge-small-zh-v1.5` 本地模型（HuggingFace）
5. `all-MiniLM-L6-v2` 本地备选

> 所有外部 API 不可用时自动降级为纯 BM25 关键词检索，保证基本可用性

```python
# 使用示例
from rag.vector_store import get_rag_store
store = get_rag_store()

# 上传文档
store.add_document("docs/article.pdf")

# 多策略融合检索（推荐 hybrid）
results = store.fused_search(
    query="关键词",
    strategy="hybrid",         # 可选: semantic / bm25 / mmr / hybrid / all
    expand_query=True,         # 启用多角度查询扩展
    cross_encode_rerank=True,  # 启用 Cross-Encoder 精排
)

# 删除文档
store.delete_document("article.pdf")

# 查看已索引文档
store.list_documents()
```

---

## 插件化工具系统

x-langchain 提供插件化的工具管理系统，开发者可轻松添加新工具，无需修改核心代码。

### 核心特性

- **自动注册** - 使用 `@register_tool` 装饰器自动注册工具
- **工具发现** - 自动扫描 `tools/` 目录，发现新工具
- **类别管理** - 按类别组织工具，便于管理和过滤
- **向后兼容** - 完全兼容现有工具代码

### 快速开始

创建新工具只需三步：

```python
# 1. 在 tools/ 目录下创建新文件
# tools/my_tool.py

# 2. 使用装饰器注册工具
from tools.registry import register_tool

@register_tool(name="my_tool", category="custom", description="我的工具")
class MyTool:
    def __init__(self):
        self.name = "my_tool"
        self.description = "我的自定义工具"

    def run(self, param: str) -> str:
        return f"处理参数: {param}"

# 3. 完成！工具会在模块导入时自动注册
```

### 工具查询

```python
from tools import ToolRegistry

# 检查工具是否存在
if ToolRegistry.contains("my_tool"):
    tool = ToolRegistry.get("my_tool")

# 获取所有工具
all_tools = ToolRegistry.get_all()

# 按类别获取工具
custom_tools = ToolRegistry.get_all(category="custom")

# 获取统计信息
stats = ToolRegistry.get_stats()
print(f"总工具数: {stats['total_tools']}")
```

> 详细文档请参考 [插件开发指南](docs/插件开发指南.md)

---

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

---

## 参考资料

- [LangChain 官方文档](https://python.langchain.com/docs/get_started/introduction)
- [LangChain 中文文档](https://langchain-doc.cn/v1/python/langchain/overview.html)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Python 官方文档](https://docs.python.org/3/)
- [uv 包管理器](https://github.com/astral-sh/uv)
- [DeepSeek 官方文档](https://platform.deepseek.com/docs/api)
- [豆包官方文档](https://www.doubao.com/)
- [阿里云通义千问](https://help.aliyun.com/product/1081203.html)

---

## 联系方式

| 项目 | 信息 |
|------|------|
| **作者** | John Young（夜雨诗来） |
| **邮箱** | john.young@foxmail.com |
| **Gitee** | https://gitee.com/yeyushilai |
| **GitHub** | https://github.com/yeyushilai |
| **项目地址** | https://gitee.com/chain-engine/x-langchain |
| **GitHub** | https://github.com/StephenCurry429/langchain |