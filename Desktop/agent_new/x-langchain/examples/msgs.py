from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

# 1. 定义系统人设
system_msg = SystemMessage(content="你是一个数学助手。如果用户问计算题，请使用计算器工具。")

# 2. 用户提问
human_msg = HumanMessage(content="123 乘以 456 等于多少？")

# 3. AI 决定调用工具 (模拟)
ai_msg = AIMessage(
    content="", 
    tool_calls=[{"name": "calculator", "args": {"a": 123, "b": 456}, "id": "call_1"}]
)

# 4. 工具返回结果
tool_msg = ToolMessage(content="56088", tool_call_id="call_1")

# 5. AI 基于结果回答
final_ai_msg = AIMessage(content="123 乘以 456 等于 56088。")

# 将所有消息放入列表，构成完整的对话状态
conversation_state = [
    system_msg, 
    human_msg, 
    ai_msg, 
    tool_msg, 
    final_ai_msg
]