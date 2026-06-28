import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.prompts import ChatPromptTemplate
from core.config import settings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import FewShotChatMessagePromptTemplate

llm = ChatOpenAI(
    model_name=settings.DEEPSEEK_MODEL_NAME,
    temperature=settings.TEMPERATURE,
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_API_BASE,
)

examples = [
    {"input": "2 🐦 2", "output": "4"},
    {"input": "2 🐦 3", "output": "5"},
]

base_prompt = ChatPromptTemplate.from_messages(
    [
        ("human", "{input}"),
        ("ai", "{output}"),
    ]
)

few_shot_prompt = FewShotChatMessagePromptTemplate(
    examples=examples,
    example_prompt=base_prompt,
)

final_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个专业智能助手"),
        few_shot_prompt,
        ("human", "{input}"),
    ]
)

chain = final_prompt | llm
print(final_prompt.invoke(input="5 🐦 41"))
print(chain.invoke(input="5 🐦 41"))