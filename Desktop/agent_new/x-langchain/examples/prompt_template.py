from langchain_core.prompts import PromptTemplate

if __name__ == "__main__":
    prompt_template = PromptTemplate.from_template(
        """
        你是一个专业的SQL查询助手，能够根据用户的自然语言描述生成对应的SQL查询语句。
        请根据用户的描述，生成符合要求的SQL查询语句。
        用户描述：{input}
        """
    )

    print(prompt_template.format(input="查询所有用户的姓名和年龄"))