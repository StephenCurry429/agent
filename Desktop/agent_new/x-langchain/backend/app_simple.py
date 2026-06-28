#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版后端服务 - 支持真实 OpenAI 模型
"""

import sys
import os

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'src'))

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import sqlite3
import tempfile

# 加载环境变量
load_dotenv()

app = FastAPI(title="X-LangChain API", description="LangChain 智能助手 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    model_name: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    model: str

# 初始化 OpenAI 客户端
model_name = os.getenv("MODEL_NAME", "mock")
api_key = os.getenv("OPENAI_API_KEY")

client = None
if model_name == "openai" and api_key:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        print(f"✅ OpenAI 客户端初始化成功")
    except Exception as e:
        print(f"❌ OpenAI 客户端初始化失败: {e}")
        client = None

@app.get("/")
async def root():
    return {"message": "X-LangChain API 服务已启动"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": model_name}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    message = request.message
    
    # 使用真实 OpenAI 模型
    if client:
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的助手，请用中文回答问题。"},
                    {"role": "user", "content": message}
                ],
                temperature=float(os.getenv("TEMPERATURE", 0.7))
            )
            return {"response": response.choices[0].message.content, "model": "openai-gpt-3.5-turbo"}
        except Exception as e:
            print(f"OpenAI 请求失败，降级到模拟模式: {e}")
            response = generate_mock_response(message)
            return {"response": response, "model": "mock"}
    
    response = generate_mock_response(message)
    return {"response": response, "model": "mock"}

def generate_mock_response(message):
    """生成模拟响应"""
    msg_lower = message.lower()
    
    # 代码相关请求（放在计算之前，因为代码可能包含运算符）
    if "代码" in message or "python" in msg_lower or "javascript" in msg_lower or "编程" in message or "function" in msg_lower or "def" in msg_lower:
        if "斐波那契" in message or "fibonacci" in msg_lower:
            fib_code = '''好的！这是一个计算斐波那契数列第 n 项的 Python 函数：

```python
def fibonacci(n):
    """
    计算斐波那契数列的第 n 项
    
    参数:
        n (int): 要计算的项数，从 0 开始计数
        
    返回:
        int: 斐波那契数列的第 n 项
        
    示例:
        >>> fibonacci(0)
        0
        >>> fibonacci(5)
        5
        >>> fibonacci(10)
        55
    """
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b

# 测试
if __name__ == "__main__":
    print(f"斐波那契数列第 10 项: {fibonacci(10)}")
```

这个函数使用迭代方式实现，时间复杂度 O(n)，空间复杂度 O(1)。'''
            return fib_code
        
        elif ("+" in message or "-" in message or "*" in message or "/" in message) and ("代码" in message or "python" in msg_lower or "编程" in message):
            add_code = '''好的！这是一个简单的 Python 计算代码：

```python
# 计算 1 + 2
result = 1 + 2
print(f"计算结果: {result}")

# 或者封装成函数
def add(a, b):
    """加法函数"""
    return a + b

print(f"1 + 2 = {add(1, 2)}")
```'''
            return add_code
        
        else:
            return "当然可以帮您编写代码！\n\n以下是一个 Python 示例：\n```python\ndef greet(name):\n    print('Hello, ' + name + '!')\n\ngreet('World')\n```\n\n请问您需要编写什么类型的代码？可以告诉我具体需求。"
    
    elif "天气" in message:
        return "根据最新数据，今天天气晴朗，气温25-32°C，适合户外活动。建议做好防晒措施，多喝水保持身体水分。"
    
    elif "计算" in message or ("+" in message and "代码" not in message):
        # 纯计算请求（不包含代码相关关键词）
        return "我可以帮您进行各种数学计算。您可以直接输入数学表达式，例如：2 + 3 * 4，我会为您计算结果。"
    
    elif "SQL" in message or "数据库" in message or "查询" in message:
        # 检测常见的SQL查询场景
        if "users" in message.lower() or "用户" in message:
            if "最新" in message or "最近" in message:
                sql_code = '''好的！根据您的需求，这是查询最近一周注册用户的 SQL 语句：

```sql
-- 查询最近一周注册的用户
SELECT id, name, email, created_at
FROM users
WHERE created_at >= NOW() - INTERVAL 7 DAY
ORDER BY created_at DESC;
```

**说明：**
- `NOW() - INTERVAL 7 DAY` 获取7天前的时间
- `ORDER BY created_at DESC` 按注册时间倒序排列
- 返回字段：用户ID、姓名、邮箱、注册时间'''
                return sql_code
            
            elif "数量" in message or "count" in message.lower():
                sql_code = '''好的！这是统计用户数量的 SQL 语句：

```sql
-- 统计用户总数
SELECT COUNT(*) as total_users
FROM users;

-- 按注册日期分组统计
SELECT DATE(created_at) as register_date, COUNT(*) as count
FROM users
GROUP BY DATE(created_at)
ORDER BY register_date DESC;
```'''
                return sql_code
        
        elif "orders" in message.lower() or "订单" in message:
            sql_code = '''好的！这是订单相关的 SQL 查询示例：

```sql
-- 查询订单详情（关联用户表）
SELECT 
    o.id as order_id,
    u.name as user_name,
    o.total_amount,
    o.status,
    o.created_at
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.created_at >= '2024-01-01'
ORDER BY o.created_at DESC;

-- 统计订单总金额
SELECT SUM(total_amount) as total_revenue
FROM orders
WHERE status = 'completed';
```'''
            return sql_code
        
        elif "join" in message.lower() or "关联" in message:
            sql_code = '''好的！这是一个表关联查询的示例：

```sql
-- 关联查询示例
SELECT 
    u.name as user_name,
    COUNT(o.id) as order_count,
    SUM(o.total_amount) as total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2024-01-01'
GROUP BY u.id, u.name
HAVING COUNT(o.id) > 5
ORDER BY order_count DESC;
```

**说明：**
- `LEFT JOIN` 保留左表（users）的所有记录
- `GROUP BY` 按用户分组
- `HAVING` 过滤订单数大于5的用户'''
            return sql_code
        
        else:
            sql_code = '''当然可以！我可以帮您编写 SQL 查询语句。

**请提供以下信息：**
1. 表名（如：users, orders）
2. 需要查询的字段（如：id, name, created_at）
3. 查询条件（如：创建时间 > '2024-01-01'）
4. 是否需要关联其他表

**SQL 查询示例：**
```sql
SELECT users.name, COUNT(orders.id) as order_count
FROM users
LEFT JOIN orders ON users.id = orders.user_id
WHERE users.created_at > '2024-01-01'
GROUP BY users.id
HAVING COUNT(orders.id) > 5
ORDER BY order_count DESC;
```

请问您需要查询什么数据？'''
            return sql_code
    
    elif "文章" in message or "写作" in message:
        return "好的，我可以帮您撰写文章。请告诉我您需要写哪方面的内容，比如主题、字数要求、目标读者等信息，我会为您创作一篇高质量的文章。"
    
    elif "总结" in message or "摘要" in message:
        return "请把需要总结的内容发给我，我会帮您提炼核心要点，用简洁明了的语言进行总结。"
    
    elif "翻译" in message:
        return "请告诉我需要翻译的内容和目标语言，我会为您提供准确的翻译。支持中英互译及多种语言。"
    
    elif "建议" in message or "推荐" in message:
        return "当然可以！请告诉我您需要哪方面的建议，比如旅行、学习、工作等，我会根据您的情况提供实用的建议。"
    
    elif "你是谁" in message or "介绍" in message:
        return "我是 X-LangChain 智能助手，是一个基于 LangChain 框架构建的AI助手。我可以帮助您处理各种任务，包括编写代码、撰写文章、数据分析、知识问答等。"
    
    else:
        return f"收到您的消息：{message[:50]}...\n\n这是一个模拟响应。在实际应用中，我会调用真实的AI模型为您提供更准确、更专业的回答。如果您有任何问题，欢迎随时问我！"

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    message = request.message
    
    # 使用真实 OpenAI 流式响应
    if client:
        try:
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的助手，请用中文回答问题。"},
                    {"role": "user", "content": message}
                ],
                stream=True,
                temperature=float(os.getenv("TEMPERATURE", 0.7))
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield {"token": chunk.choices[0].delta.content, "done": False}
            yield {"token": "", "done": True}
            return
        except Exception as e:
            print(f"OpenAI 请求失败，降级到模拟模式: {e}")
            # 降级到模拟响应
            response = generate_mock_response(message)
            for i in range(0, len(response), 5):
                chunk = response[i:i+5]
                yield {"token": chunk, "done": False}
            yield {"token": "", "done": True}
            return
    
    # 本地模拟流式响应
    response = generate_mock_response(message)
    for i in range(0, len(response), 5):
        chunk = response[i:i+5]
        yield {"token": chunk, "done": False}
    
    yield {"token": "", "done": True}

# SQL 文件上传和查询功能
@app.post("/upload-sql")
async def upload_sql_file(file: UploadFile = File(...)):
    """
    上传 SQL 文件并执行查询
    
    参数:
        file: SQL 文件 (.sql 或 .db)
    
    返回:
        查询结果或错误信息
    """
    try:
        # 检查文件类型
        filename = file.filename.lower()
        if not (filename.endswith('.sql') or filename.endswith('.db')):
            raise HTTPException(status_code=400, detail="仅支持 .sql 或 .db 文件")
        
        # 读取文件内容
        contents = await file.read()
        
        if filename.endswith('.db'):
            # SQLite 数据库文件
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
                temp_db.write(contents)
                temp_db_path = temp_db.name
            
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            
            # 获取所有表名
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [t[0] for t in cursor.fetchall()]
            
            result = "已成功加载数据库文件！\n\n"
            result += "📋 数据库中的表：\n"
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table});")
                columns = [col[1] for col in cursor.fetchall()]
                result += f"- **{table}**: {', '.join(columns)}\n"
            
            conn.close()
            os.unlink(temp_db_path)
            
            return {"response": result, "model": "sql-file", "tables": tables}
        
        else:
            # SQL 脚本文件
            sql_content = contents.decode('utf-8', errors='ignore')
            
            # 创建临时数据库
            conn = sqlite3.connect(':memory:')
            cursor = conn.cursor()
            
            # 执行 SQL 脚本
            try:
                cursor.executescript(sql_content)
                conn.commit()
                
                # 获取所有表名
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [t[0] for t in cursor.fetchall()]
                
                result = "已成功执行 SQL 文件！\n\n"
                result += "📋 创建的表：\n"
                for table in tables:
                    cursor.execute(f"PRAGMA table_info({table});")
                    columns = [col[1] for col in cursor.fetchall()]
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    row_count = cursor.fetchone()[0]
                    result += f"- **{table}**: {', '.join(columns)} ({row_count} 条记录)\n"
                
                conn.close()
                return {"response": result, "model": "sql-file", "tables": tables}
            
            except Exception as e:
                conn.close()
                raise HTTPException(status_code=400, detail=f"SQL 执行错误: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")

@app.post("/query-sql")
async def query_sql(request: dict):
    """
    执行 SQL 查询
    
    参数:
        sql: SQL 查询语句
        file_contents: 可选，SQL 文件内容（用于创建临时表）
    
    返回:
        查询结果
    """
    try:
        sql = request.get('sql', '')
        file_contents = request.get('file_contents', '')
        
        if not sql.strip():
            raise HTTPException(status_code=400, detail="请提供 SQL 查询语句")
        
        # 创建内存数据库
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        # 如果提供了文件内容，先执行
        if file_contents:
            try:
                cursor.executescript(file_contents)
                conn.commit()
            except Exception as e:
                conn.close()
                raise HTTPException(status_code=400, detail=f"SQL 文件执行错误: {str(e)}")
        
        # 执行查询
        cursor.execute(sql)
        
        # 获取列名
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # 获取数据
        rows = cursor.fetchall()
        row_count = len(rows)
        
        conn.close()
        
        # 格式化结果
        result = f"✅ 查询成功！共 {row_count} 条记录\n\n"
        
        if row_count > 0:
            # 添加表头
            result += "| " + " | ".join(columns) + " |\n"
            result += "| " + " | ".join(["---"] * len(columns)) + " |\n"
            
            # 添加数据行（最多显示100条）
            for row in rows[:100]:
                formatted_row = []
                for val in row:
                    if val is None:
                        formatted_row.append("NULL")
                    else:
                        formatted_row.append(str(val))
                result += "| " + " | ".join(formatted_row) + " |\n"
            
            if row_count > 100:
                result += f"\n... 还有 {row_count - 100} 条记录未显示\n"
        
        return {"response": result, "model": "sql-query"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL 查询错误: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
