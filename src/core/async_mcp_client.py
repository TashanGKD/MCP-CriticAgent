#!/usr/bin/env python3
"""
异步 MCP 客户端封装

为 ValidationAgent 提供 awaitable 的 list_tools/call_tool 接口，
基于 SimpleMCPCommunicator.send_request 实现。

作者: AI Assistant
日期: 2025-08-15
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Dict, Optional


class AsyncMCPClient:
    """将同步的 SimpleMCPCommunicator 封装为异步接口。

    约定返回格式：
    - list_tools() -> {"success": bool, "tools": list, "error"?: str, "raw"?: Any}
    - call_tool(name, arguments) -> {"success": bool, "result": Any, "error"?: str, "raw"?: Any}
    """

    def __init__(self, communicator) -> None:
        self._comm = communicator

    async def _send(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> Dict[str, Any]:
        """在线程池中调用同步 send_request，返回原始结构。"""
        loop = asyncio.get_running_loop()
        request = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000) % 10_000_000,
            "method": method,
        }
        if params is not None:
            request["params"] = params

        def _call():
            return self._comm.send_request(request, timeout=timeout)

        return await loop.run_in_executor(None, _call)

    async def list_tools(self, timeout: float = 30.0) -> Dict[str, Any]:
        """获取工具列表并规范化结构。"""
        try:
            res = await self._send("tools/list", None, timeout=timeout)
            if not res.get("success"):
                return {"success": False, "tools": [], "error": res.get("error", "unknown error")}

            data = res.get("data")
            tools = []
            if isinstance(data, dict):
                # 期望 JSON-RPC {result: {tools: [...]}}
                tools = data.get("result", {}).get("tools", []) if "result" in data else []
            return {"success": True, "tools": tools, "raw": data}
        except Exception as e:
            return {"success": False, "tools": [], "error": str(e)}

    async def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None, timeout: float = 60.0) -> Dict[str, Any]:
        """调用指定工具并规范化结构。"""
        try:
            params = {"name": name, "arguments": arguments or {}}
            res = await self._send("tools/call", params, timeout=timeout)
            if not res.get("success"):
                return {"success": False, "error": res.get("error", "unknown error")}

            data = res.get("data")
            result = None
            error = None

            if isinstance(data, dict):
                if "error" in data:
                    # JSON-RPC 错误
                    try:
                        error = data["error"].get("message") if isinstance(data["error"], dict) else str(data["error"])
                    except Exception:
                        error = str(data["error"])  # 保底
                elif "result" in data:
                    result = data["result"]
            else:
                # 非标准响应，直接返回原始
                result = data

            if error is not None:
                return {"success": False, "error": error, "raw": data}
            return {"success": True, "result": result, "raw": data}
        except Exception as e:
            return {"success": False, "error": str(e)}
