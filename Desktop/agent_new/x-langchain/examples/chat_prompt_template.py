import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.prompts import ChatPromptTemplate
from core.config import settings
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model_name=settings.DEEPSEEK_MODEL_NAME,
    temperature=settings.TEMPERATURE,
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_API_BASE,
)

prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个专业智能助手"),
        ("user", "{input}"),
    ]
)

print(prompt_template.invoke(input="武汉今天天气怎么样?"))

chain = prompt_template | llm
print(chain.invoke(input="武汉今天天气怎么样?"))
