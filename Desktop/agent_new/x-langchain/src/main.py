# -*- coding: utf-8 -*-
"""
项目主入口

作为脚本执行，提供交互式对话功能。
"""

import sys
import time
import os
import warnings
from typing import Any, Dict

# 抑制 Pydantic 的非序列化默认值警告
warnings.filterwarnings(
    "ignore",
    message=".*is not JSON serializable.*",
    category=UserWarning,
)

from core import settings
from core import logger
from agents import agent_factory
from constants import STREAM_MODE_MESSAGES


def search(agent: Any, query: str) -> Dict[str, str]:
    """
    查询指定内容（打字机效果流式输出）

    Args:
        agent: Agent 实例
        query: 查询内容

    Returns:
        查询结果字典，包含 output 字段
    """
    # 构建用户输入
    user_input: str = query

    # 调用 Agent（使用打字机效果流式输出）
    logger.info("查询结果:")

    full_text: str = ""

    for chunk in agent.stream(
        input={"messages": [{"role": "user", "content": user_input}]},
        config={"run_name": "AI Assistant"},
        stream_mode=STREAM_MODE_MESSAGES,
    ):
        # 处理元组格式 (AIMessageChunk, metadata)
        if isinstance(chunk, tuple) and len(chunk) == 2:
            message_chunk, metadata = chunk
            if hasattr(message_chunk, "content") and message_chunk.content:
                # 逐字输出，每个字符间隔 0.02 秒
                for char in message_chunk.content:
                    sys.stdout.write(char)
                    sys.stdout.flush()
                    full_text += char
                    time.sleep(0.02)

    # 换行
    print()

    # 返回最终结果
    return {"output": full_text}


def interactive_chat(agent: Any) -> None:
    """
    交互式对话模式

    Args:
        agent: Agent 实例
    """
    print("\n" + "=" * 50)
    print("欢迎使用智能助手！输入 'exit'、'quit' 或 '退出' 结束对话")
    print("=" * 50 + "\n")

    while True:
        try:
            # 获取用户输入
            user_input: str = input("你: ").strip()

            # 检查是否退出
            if user_input.lower() in ["exit", "quit", "退出", "离开", "bye", "再见"]:
                print("\n感谢使用，再见！")
                break

            # 跳过空输入
            if not user_input:
                continue

            # 执行查询
            print()
            search(agent, user_input)
            print()

        except KeyboardInterrupt:
            print("\n\n检测到中断信号，正在退出...")
            break
        except EOFError:
            print("\n\n输入结束，正在退出...")
            break
        except Exception as e:
            logger.error(f"处理输入时出错: {e}")
            print("抱歉，处理您的请求时出现了错误，请重试。\n")


def main() -> None:
    """
    主函数，直接执行交互式对话
    """
    try:
        # 从环境变量获取模型名称，默认使用 deepseek
        model_name: str = os.getenv("MODEL_NAME", "deepseek")

        # 验证模型配置
        logger.info(f"正在验证模型配置: {model_name}")
        if not settings.validate_model_config(model_name):
            logger.error(f"{model_name} 模型的配置不完整，请检查 .env 文件中的配置")
            sys.exit(1)

        # 打印配置信息
        logger.info(
            f"配置信息: DEBUG={settings.DEBUG}, STRUCTURED={settings.STRUCTURED}"
        )

        # 创建 Agent
        logger.info(f"正在创建 Agent (使用 {model_name} 模型)...")
        agent: Any = agent_factory.create_agent(model_name)

        # 进入交互式对话模式
        interactive_chat(agent)

    except ImportError as e:
        logger.error(f"缺少依赖模块: {e}")
        logger.info("请运行 'uv sync' 安装依赖")
        if settings.DEBUG:
            import traceback

            logger.debug(traceback.format_exc())
        sys.exit(1)
    except ConnectionError as e:
        logger.error(f"网络连接失败: {e}")
        logger.info("请检查网络连接和 API 端点配置")
        if settings.DEBUG:
            import traceback

            logger.debug(traceback.format_exc())
        sys.exit(1)
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        if settings.DEBUG:
            import traceback

            logger.debug(traceback.format_exc())
        sys.exit(1)
    except Exception as e:
        logger.error(f"错误: {e}")
        if settings.DEBUG:
            import traceback

            logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
