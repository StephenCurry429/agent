# -*- coding: utf-8 -*-
"""
Gradio 多模态对话示例

基于 DeepSeek API 实现的多模态对话界面。

功能特性:
    - 支持文本、图片、音频多模态输入
    - 将本地媒体文件转换为 base64 data URL 格式
    - 使用 SQLite 持久化会话历史
    - 支持麦克风录音输入

使用方式:
    1. 配置 .env 文件中的 API 密钥
    2. 运行: python examples/gradio_multimodal_deepseek.py
    3. 浏览器访问 http://localhost:7860

环境变量:
    DEEPSEEK_API_KEY: DeepSeek API 密钥
    DEEPSEEK_API_BASE: API 基础地址
    DEEPSEEK_MODEL_NAME: 模型名称

注意事项:
    - DeepSeek 官方模型主要为文本模型
    - 若模型不支持图片/音频，仍可作为多模态输入组装的参考
"""

from __future__ import annotations

import base64
import io
import os
import sys
import uuid
from pathlib import Path
from typing import Any

import gradio as gr
from PIL import Image
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage

# 添加项目路径
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
SRC_DIR: Path = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from models.providers import create_chat_model  # noqa: E402


# =============================================================================
# 配置常量
# =============================================================================

# 数据库配置
DATABASE_URL: str = "sqlite:///chat_history.db"
HISTORY_TABLE_NAME: str = "t_session_history"

# 支持的文件类型
SUPPORTED_IMAGE_EXTENSIONS: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".webp")
SUPPORTED_AUDIO_EXTENSIONS: tuple[str, ...] = (".wav", ".mp3")

# 图片配置
IMAGE_DETAIL_LEVEL: str = "low"  # low | high | auto

# 音频配置
DEFAULT_AUDIO_DURATION_SECONDS: int = 30

# UI 配置
CHATBOT_HEIGHT: int = 520
GRADIO_THEME: str = "Soft"


# =============================================================================
# 工具函数
# =============================================================================


def encode_bytes_to_data_url(data: bytes, mime_type: str) -> str:
    """
    将字节数据编码为 base64 data URL 格式。

    Args:
        data: 原始字节数据
        mime_type: MIME 类型，如 "image/png", "audio/wav"

    Returns:
        base64 编码的 data URL 字符串

    Example:
        >>> with open("image.png", "rb") as f:
        ...     data_url = encode_bytes_to_data_url(f.read(), "image/png")
        >>> print(data_url[:50])
        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA...'
    """
    encoded: str = base64.b64encode(data).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def get_mime_type_from_extension(file_path: str | Path) -> str:
    """
    根据文件扩展名获取 MIME 类型。

    Args:
        file_path: 文件路径

    Returns:
        MIME 类型字符串

    Raises:
        ValueError: 不支持的文件类型
    """
    suffix: str = Path(file_path).suffix.lower()

    mime_mapping: dict[str, str] = {
        # 图片类型
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        # 音频类型
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
    }

    if suffix not in mime_mapping:
        raise ValueError(f"不支持的文件类型: {suffix}")

    return mime_mapping[suffix]


# =============================================================================
# 媒体处理函数
# =============================================================================


def process_image_to_content_part(
    image_path: str | Path,
    detail: str = IMAGE_DETAIL_LEVEL,
) -> dict[str, Any]:
    """
    将图片文件转换为 DeepSeek 多模态 content part。

    Args:
        image_path: 图片文件路径
        detail: 图片细节级别，可选值为 "low"、"high" 或 "auto"
            - low: 低分辨率，处理速度更快
            - high: 高分辨率，细节更丰富
            - auto: 根据图片尺寸自动选择

    Returns:
        符合 DeepSeek API 格式的 content part 字典，结构如下:
        {
            "type": "image_url",
            "image_url": {
                "url": "data:image/png;base64,...",
                "detail": "low"
            }
        }

    Raises:
        FileNotFoundError: 图片文件不存在
        PIL.UnidentifiedImageError: 无法识别的图片格式

    Example:
        >>> part = process_image_to_content_part("photo.png", detail="high")
        >>> print(part["type"])
        'image_url'
    """
    path: Path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"图片文件不存在: {path}")

    # 使用 PIL 读取并重新编码，确保格式正确
    with Image.open(path) as img:
        # 确定输出格式
        img_format: str = (img.format or "PNG").upper()
        if img_format not in ("PNG", "JPEG", "WEBP", "GIF"):
            img_format = "PNG"

        # 转换为字节流
        buffer: io.BytesIO = io.BytesIO()
        img.save(buffer, format=img_format)

        # 获取 MIME 类型
        mime_type: str = get_mime_type_from_extension(f".{img_format.lower()}")

    return {
        "type": "image_url",
        "image_url": {
            "url": encode_bytes_to_data_url(buffer.getvalue(), mime_type),
            "detail": detail,
        },
    }


def process_audio_to_content_part(
    audio_path: str | Path,
    duration: int | None = DEFAULT_AUDIO_DURATION_SECONDS,
) -> dict[str, Any]:
    """
    将音频文件转换为 content part。

    注意: DeepSeek 对音频的支持可能有所不同，请根据实际 API 文档调整。

    Args:
        audio_path: 音频文件路径
        duration: 音频时长（秒），用于某些 API 的元数据

    Returns:
        符合多模态 API 格式的 content part 字典，结构如下:
        {
            "type": "audio_url",
            "audio_url": {
                "url": "data:audio/wav;base64,...",
                "duration": 30
            }
        }

    Raises:
        FileNotFoundError: 音频文件不存在
        ValueError: 不支持的音频格式

    Example:
        >>> part = process_audio_to_content_part("recording.wav", duration=10)
        >>> print(part["type"])
        'audio_url'
    """
    path: Path = Path(audio_path)

    if not path.exists():
        raise FileNotFoundError(f"音频文件不存在: {path}")

    # 读取文件并获取 MIME 类型
    raw_data: bytes = path.read_bytes()
    mime_type: str = get_mime_type_from_extension(path)

    payload: dict[str, Any] = {
        "type": "audio_url",
        "audio_url": {
            "url": encode_bytes_to_data_url(raw_data, mime_type),
        },
    }

    if duration is not None:
        payload["audio_url"]["duration"] = duration

    return payload


def process_file_to_content_part(file_path: str | Path) -> dict[str, Any]:
    """
    根据文件类型自动处理为对应的 content part。

    Args:
        file_path: 文件路径

    Returns:
        content part 字典

    Raises:
        ValueError: 不支持的文件类型

    Example:
        >>> part = process_file_to_content_part("photo.jpg")
        >>> print(part["type"])
        'image_url'
    """
    path: Path = Path(file_path)
    suffix: str = path.suffix.lower()

    if suffix in SUPPORTED_IMAGE_EXTENSIONS:
        return process_image_to_content_part(path)

    if suffix in SUPPORTED_AUDIO_EXTENSIONS:
        return process_audio_to_content_part(path)

    # 不支持的文件类型，返回文本提示
    return {
        "type": "text",
        "text": f"（收到文件: {path.name}，当前不支持该文件类型的多模态处理）",
    }


# =============================================================================
# 消息处理函数
# =============================================================================


def build_multimodal_content_parts(
    text: str | None,
    files: list[str] | None,
) -> list[dict[str, Any]]:
    """
    将文本和文件列表组装为多模态 content parts。

    Args:
        text: 用户输入的文本内容
        files: 上传的文件路径列表

    Returns:
        content parts 列表，每个元素都是一个 content part 字典

    Example:
        >>> parts = build_multimodal_content_parts(
        ...     "请描述这张图片",
        ...     ["photo.jpg", "recording.wav"]
        ... )
        >>> print(len(parts))
        3  # 1 text + 1 image + 1 audio
    """
    parts: list[dict[str, Any]] = []

    # 添加文本部分
    if text and text.strip():
        parts.append({
            "type": "text",
            "text": text.strip(),
        })

    # 处理文件
    for file_path in files or []:
        try:
            part = process_file_to_content_part(file_path)
            parts.append(part)
        except (FileNotFoundError, ValueError) as e:
            parts.append({
                "type": "text",
                "text": f"（文件处理失败: {Path(file_path).name}，错误: {e}）",
            })

    return parts


def create_chat_message_history(session_id: str) -> SQLChatMessageHistory:
    """
    创建或获取指定会话的历史记录管理器。

    Args:
        session_id: 会话唯一标识符

    Returns:
        SQLChatMessageHistory 实例

    Note:
        历史记录存储在 SQLite 数据库中，路径由 DATABASE_URL 指定
    """
    return SQLChatMessageHistory(
        session_id=session_id,
        table_name=HISTORY_TABLE_NAME,
        connection_string=DATABASE_URL,
    )


# =============================================================================
# Gradio 回调函数
# =============================================================================


def handle_user_input(
    chat_history: list[dict[str, Any]],
    user_input: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    处理用户输入，将消息添加到聊天历史并清空输入框。

    Args:
        chat_history: 当前聊天历史列表
        user_input: 用户输入，包含 "text" 和 "files" 字段

    Returns:
        元组，包含:
        - 更新后的聊天历史
        - 清空后的输入框状态

    Example:
        >>> history = []
        >>> user_input = {"text": "你好", "files": []}
        >>> new_history, cleared_input = handle_user_input(history, user_input)
    """
    # 添加文本消息
    if user_input.get("text"):
        chat_history.append({
            "role": "user",
            "content": user_input["text"],
        })

    # 添加文件消息
    for file_path in user_input.get("files") or []:
        chat_history.append({
            "role": "user",
            "content": {"path": str(file_path)},
        })

    # 清空输入框
    cleared_input: dict[str, Any] = {
        "text": "",
        "files": [],
    }

    return chat_history, cleared_input


def process_model_response(
    chat_history: list[dict[str, Any]],
    session_id: str,
) -> list[dict[str, Any]]:
    """
    处理模型响应，将 AI 回复添加到聊天历史。

    此函数执行以下步骤:
    1. 从聊天历史中提取最新的用户输入
    2. 将输入转换为多模态 content parts
    3. 调用 LLM 模型获取响应
    4. 将响应保存到会话历史并更新 UI

    Args:
        chat_history: 当前聊天历史列表
        session_id: 会话唯一标识符

    Returns:
        更新后的聊天历史（包含 AI 回复）

    Example:
        >>> history = [{"role": "user", "content": "你好"}]
        >>> new_history = process_model_response(history, "session-123")
        >>> print(new_history[-1]["role"])
        'assistant'
    """
    # 提取最新一轮用户输入
    last_assistant_idx: int = -1
    for i in range(len(chat_history) - 1, -1, -1):
        if chat_history[i]["role"] == "assistant":
            last_assistant_idx = i
            break

    # 获取用户输入片段
    user_messages: list[dict[str, Any]] = (
        chat_history
        if last_assistant_idx == -1
        else chat_history[last_assistant_idx + 1:]
    )

    # 分离文本和文件
    text_parts: list[str] = []
    file_paths: list[str] = []

    for msg in user_messages:
        if msg["role"] != "user":
            continue

        content = msg.get("content")
        if isinstance(content, str):
            text_parts.append(content)
        elif isinstance(content, dict) and "path" in content:
            file_paths.append(str(content["path"]))

    # 构建多模态 content parts
    combined_text: str | None = "\n".join(text_parts).strip() or None
    content_parts: list[dict[str, Any]] = build_multimodal_content_parts(
        text=combined_text,
        files=file_paths,
    )

    # 创建 LLM 实例
    llm = create_chat_model(provider_name="deepseek")

    # 创建用户消息（使用 content_parts 或纯文本）
    # HumanMessage 的 content 可以是 str 或 list
    user_message: HumanMessage = HumanMessage(
        content=content_parts if content_parts else (combined_text or "")  # type: ignore[arg-type]
    )

    # 保存到会话历史
    chat_history_manager: SQLChatMessageHistory = create_chat_message_history(
        session_id
    )
    chat_history_manager.add_message(
        HumanMessage(content=combined_text or "[多模态输入]")
    )

    # 调用模型
    try:
        response = llm.invoke([user_message])
        # 提取响应文本
        raw_content: Any = (
            response.content
            if hasattr(response, "content")
            else str(response)
        )
        ai_response_text: str = (
            raw_content
            if isinstance(raw_content, str)
            else str(raw_content)
        )
    except Exception as e:
        ai_response_text = f"抱歉，处理您的请求时出错: {e}"

    # 保存 AI 响应
    chat_history_manager.add_message(AIMessage(content=ai_response_text))

    # 更新聊天历史
    chat_history.append({
        "role": "assistant",
        "content": ai_response_text,
    })

    return chat_history


# =============================================================================
# UI 构建函数
# =============================================================================


def create_gradio_interface() -> gr.Blocks:
    """
    创建 Gradio 多模态对话界面。

    Returns:
        配置完成的 Gradio Blocks 实例

    界面组件:
        - Chatbot: 聊天消息显示区域
        - MultimodalTextbox: 多模态输入框（支持文本、文件、麦克风）
        - State: 会话 ID 状态管理
    """
    with gr.Blocks(
        title="多模态对话 (DeepSeek)",
        theme=getattr(gr.themes, GRADIO_THEME)(),
    ) as interface:
        # 会话状态
        session_id = gr.State(value=lambda: str(uuid.uuid4()))

        # 标题和说明
        gr.Markdown("""
        ### 多模态对话 (DeepSeek)

        **功能说明:**
        - 支持文本输入
        - 支持上传图片 (PNG, JPG, JPEG, WEBP)
        - 支持上传音频 (WAV, MP3)
        - 支持麦克风录音

        **使用方法:**
        1. 在下方输入框输入文本或上传文件
        2. 点击发送或按 Enter 键
        3. 等待 AI 响应
        """)

        # 聊天显示区域
        chatbot = gr.Chatbot(
            height=CHATBOT_HEIGHT,
            label="对话",
            avatar_images=(None, "🤖"),
        )

        # 多模态输入框
        chat_input = gr.MultimodalTextbox(
            file_types=["image", ".wav", ".mp3"],
            file_count="multiple",
            placeholder="请输入文本，或上传图片/音频...",
            show_label=False,
            sources=["microphone", "upload"],
            submit_btn="发送",
            stop_btn=False,
        )

        # 设置事件处理链
        (
            chat_input.submit(
                fn=handle_user_input,
                inputs=[chatbot, chat_input],
                outputs=[chatbot, chat_input],
            )
            .then(
                fn=process_model_response,
                inputs=[chatbot, session_id],
                outputs=[chatbot],
            )
            .then(
                fn=lambda: gr.MultimodalTextbox(interactive=True),
                inputs=None,
                outputs=[chat_input],
            )
        )

    return interface


# =============================================================================
# 主入口
# =============================================================================


def main() -> None:
    """
    应用程序主入口。

    启动 Gradio 服务器，监听本地请求。

    环境变量要求:
        - DEEPSEEK_API_KEY: DeepSeek API 密钥 (必需)
        - DEEPSEEK_API_BASE: API 基础地址 (可选)
        - DEEPSEEK_MODEL_NAME: 模型名称 (可选)
    """
    # 检查环境变量
    api_key: str | None = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("警告: 未设置 DEEPSEEK_API_KEY 环境变量")
        print("请在 .env 文件中配置 API 密钥")

    # Gradio 6 在启动时会先请求自身的 `/startup-events`。
    # 在某些网络环境下（例如被代理拦截），即使访问的是 localhost 也可能连不上。
    # 强制把本机地址加入 NO_PROXY，可显著提高启动稳定性。
    existing_no_proxy = os.getenv("NO_PROXY", "").strip()
    desired = ["127.0.0.1", "localhost"]
    if existing_no_proxy:
        parts = [p.strip() for p in existing_no_proxy.split(",") if p.strip()]
        for d in desired:
            if d not in parts:
                parts.append(d)
        os.environ["NO_PROXY"] = ",".join(parts)
    else:
        os.environ["NO_PROXY"] = ",".join(desired)

    # 创建并启动界面
    interface = create_gradio_interface()
    interface.launch()


if __name__ == "__main__":
    main()
