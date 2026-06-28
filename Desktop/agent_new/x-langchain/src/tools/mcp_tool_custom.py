# from __future__ import annotations

# from typing import Any, Dict, Mapping

# import json

# import requests
# from langchain.tools import tool


# MCP_BASE_URL = "http://localhost:8000"
# MCP_PATH = "/mcp"
# _JSONRPC_VERSION = "2.0"
# _TIMEOUT_S = 30

# _SESSION_ID: str | None = None
# _REQUEST_ID: int = 1
# _INITIALIZED: bool = False


# def _mcp_url() -> str:
#     return f"{MCP_BASE_URL}{MCP_PATH}"


# def _get_or_handshake_session_id() -> str:
#     """
#     获取 MCP 会话 ID（优先用缓存，否则通过 StreamableHTTP 握手获取）。

#     说明：
#     - StreamableHTTP 模式下，服务端通常在 **首次 POST 响应头** 返回 `mcp-session-id`
#     - 旧的 `GET + Accept: text/event-stream` 方式在部分服务端会直接返回 400
#     """
#     global _SESSION_ID

#     if _SESSION_ID:
#         return _SESSION_ID

#     try:
#         # 发送最小化 initialize 以触发服务端分配 session id
#         init_payload: Dict[str, Any] = {
#             "jsonrpc": _JSONRPC_VERSION,
#             "method": "initialize",
#             "params": {
#                 "protocolVersion": "2024-11-05",
#                 "capabilities": {
#                     "roots": {"listChanged": True},
#                     "sampling": {},
#                 },
#                 "clientInfo": {
#                     "name": "x-langchain-mcp-client",
#                     "version": "1.0.0",
#                 },
#             },
#             "id": _next_request_id(),
#         }

#         response: requests.Response = requests.post(
#             _mcp_url(),
#             json=init_payload,
#             headers={
#                 "Content-Type": "application/json",
#                 # StreamableHTTP 建议同时接受 JSON 与 SSE（服务端可能用 SSE 推送）
#                 "Accept": "application/json, text/event-stream",
#             },
#             timeout=_TIMEOUT_S,
#         )
#         response.raise_for_status()

#         session_id = response.headers.get("mcp-session-id")
#         if not session_id:
#             raise RuntimeError("无法从 MCP 服务器获取会话 ID（缺少 mcp-session-id 响应头）")

#         # 记录 session id，并完成 initialize 的解析（失败也不阻断拿 session）
#         _SESSION_ID = session_id
#         try:
#             data = response.json()
#             if data.get("error"):
#                 raise RuntimeError(f"MCP initialize 错误: {data['error']}")
#         except ValueError:
#             # 兼容服务端以 SSE/空 body 等形式返回（只要 session id 在 header 即可）
#             pass

#         return session_id
#     except requests.RequestException as exc:
#         raise RuntimeError(f"连接 MCP 服务器失败：{exc}") from exc


# def _next_request_id() -> int:
#     global _REQUEST_ID
#     current = _REQUEST_ID
#     _REQUEST_ID += 1
#     return current


# def _build_jsonrpc_payload(method: str, params: Mapping[str, Any] | None) -> Dict[str, Any]:
#     if not method:
#         raise ValueError("method 不能为空")
#     return {
#         "jsonrpc": _JSONRPC_VERSION,
#         "method": method,
#         "params": dict(params or {}),
#         "id": _next_request_id(),
#     }


# def _post_jsonrpc(payload: Mapping[str, Any], session_id: str) -> Dict[str, Any]:
#     response: requests.Response = requests.post(
#         _mcp_url(),
#         json=dict(payload),
#         headers={
#             "Content-Type": "application/json",
#             "Accept": "application/json",
#             "mcp-session-id": session_id,
#         },
#         timeout=_TIMEOUT_S,
#     )
#     response.raise_for_status()
#     data: Dict[str, Any] = response.json()

#     if data.get("error"):
#         raise RuntimeError(f"MCP 服务器错误: {data['error']}")

#     return data.get("result", data)


# def _jsonrpc_call(method: str, params: Mapping[str, Any] | None = None) -> Dict[str, Any]:
#     """
#     向 MCP 服务器发送 JSON-RPC 请求。
#     """

#     # 获取 MCP 会话 ID
#     session_id = _get_or_handshake_session_id()
#     # 构建 JSON-RPC 请求
#     payload = _build_jsonrpc_payload(method, params)
#     # 发送 JSON-RPC 请求
#     return _post_jsonrpc(payload, session_id)


# def _ensure_initialized() -> None:
#     """
#     确保 MCP 会话已完成 initialize 流程。
#     """
#     global _INITIALIZED

#     if _INITIALIZED:
#         return

#     # 初始化会话
#     init_params: Dict[str, Any] = {
#         "protocolVersion": "2024-11-05",
#         "capabilities": {
#             "roots": {"listChanged": True},
#             "sampling": {},
#         },
#         "clientInfo": {
#             "name": "x-langchain-mcp-client",
#             "version": "1.0.0",
#         },
#     }
#     _jsonrpc_call("initialize", init_params)
#     _INITIALIZED = True


# def _mcp_call(method: str, params: Mapping[str, Any]) -> str:
#     """
#     调用 MCP 服务器的核心逻辑。

#     Args:
#         method: MCP JSON-RPC 方法名，例如 'tools/list'、'tools/call'
#         params: 传给 MCP 的参数字典

#     Returns:
#         MCP 返回的结果（JSON 字符串）
#     """
#     try:
#         _ensure_initialized()
#         result = _jsonrpc_call(method, params)
#         return json.dumps(result, ensure_ascii=False)
#     except Exception as exc:  # noqa: BLE001
#         return f"MCP 调用异常：{exc}"


# @tool
# def default_custom_mcp_call_tool(method: str, params: Dict[str, Any]) -> str:
#     """
#     通用 MCP 调用工具（遵循 JSON-RPC 协议）。

#     流程：
#     1. 获取 MCP 会话 ID
#     2. 构建 JSON-RPC 请求
#     3. 发送 JSON-RPC 请求
#     4. 返回 MCP 返回结果

#     Args:
#         method: MCP JSON-RPC 方法名，例如:
#             - "tools/list": 列出所有工具，params 应为 {}。
#             - "tools/call": 调用指定工具，params 形式为
#               {"name": "<tool_name>", "arguments": {...}}。
#             - "prompts/list": 列出所有 prompts，params 应为 {}。
#             - "prompts/get": 获取指定 prompt，params 形式为
#               {"name": "<prompt_name>", "arguments": {...}}。
#         params: MCP 参数（JSON 对象），结构需符合对应 method 的协议。

#     Returns:
#         MCP 返回结果的 JSON 字符串表示
#     """
#     return _mcp_call(method, params)

