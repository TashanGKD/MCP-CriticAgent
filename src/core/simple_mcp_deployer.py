#!/usr/bin/env python3
"""
简化版MCP部署器

移除有问题的依赖，专注核心MCP部署功能

作者: AI Assistant
日期: 2025-08-15
"""

import os
import sys
import json
import time
import uuid
import subprocess
import threading
import queue
import platform
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# 简化的通信器类（基于原CrossPlatformMCPCommunicator）
class SimpleMCPCommunicator:
    """简化的MCP通信器"""
    
    def __init__(self, process):
        self.process = process
        self.lock = threading.Lock()
        self.response_queue = queue.Queue()
        self.reader_thread = None
        self.stderr_thread = None
        self.platform = platform.system().lower()
        # 流式缓冲区（二进制）
        self._buffer = bytearray()
        self.start_reader_thread()
        self.start_stderr_thread()
    
    def start_reader_thread(self):
        """启动读取线程"""
        def reader():
            try:
                stdout = self.process.stdout  # binary
                while self.process.poll() is None:
                    try:
                        chunk = stdout.read(1)
                        if not chunk:
                            time.sleep(0.01)
                            continue
                        self._buffer.extend(chunk)
                        # 解析可能到达的完整帧（Content-Length 格式）
                        while True:
                            msg = self._try_extract_message()
                            if msg is None:
                                break
                            self.response_queue.put(msg)
                            preview = (msg[:100] + "...") if len(msg) > 100 else msg
                            print(f"📨 收到MCP响应: {preview}")
                    except Exception as read_e:
                        print(f"读取异常: {read_e}")
                        time.sleep(0.02)
            except Exception as e:
                print(f"读取线程异常: {e}")
        
        self.reader_thread = threading.Thread(target=reader, daemon=True)
        self.reader_thread.start()
        print(f"🔄 MCP通信读取线程已启动 (平台: {self.platform})")

    def start_stderr_thread(self):
        """读取并打印 stderr，辅助诊断"""
        def err_reader():
            try:
                stderr = self.process.stderr
                while self.process.poll() is None:
                    try:
                        line = stderr.readline()
                        if line:
                            try:
                                text = line.decode(errors="ignore").rstrip()
                            except Exception:
                                text = str(line)
                            if text:
                                # 限制单行长度，避免刷屏
                                print(f"⚙️ MCP STDERR: {text[:300]}")
                        else:
                            time.sleep(0.02)
                    except Exception:
                        time.sleep(0.05)
            except Exception:
                pass

        self.stderr_thread = threading.Thread(target=err_reader, daemon=True)
        self.stderr_thread.start()
    
    def _try_extract_message(self) -> Optional[str]:
        """从缓冲区解析一条换行符分隔的消息，返回解码后的 JSON 文本；无完整行返回 None"""
        try:
            buffer_str = self._buffer.decode('utf-8', errors='ignore')
            
            # 查找第一个换行符
            newline_pos = buffer_str.find('\n')
            if newline_pos == -1:
                return None
            
            # 提取消息内容（去除回车符）
            message_line = buffer_str[:newline_pos].rstrip('\r')
            
            # 更新缓冲区（移除已处理的消息）
            remaining = buffer_str[newline_pos + 1:]
            self._buffer = bytearray(remaining.encode('utf-8'))
            
            # 返回非空行
            if message_line.strip():
                return message_line
            else:
                # 跳过空行，继续尝试解析下一行
                return self._try_extract_message() if remaining else None
            
        except Exception as e:
            print(f"⚠️ 解析换行符消息时出错: {e}")
            return None

    def _write_json_frame(self, payload: Dict[str, Any]):
        """发送JSON消息（MCP STDIO 协议：JSON + 换行符）"""
        json_str = json.dumps(payload, ensure_ascii=False)
        # MCP STDIO 协议使用简单的换行符分隔
        message = json_str + "\n"
        self.process.stdin.write(message.encode("utf-8"))
        self.process.stdin.flush()

    def send_notification(self, payload: Dict[str, Any]) -> None:
        """发送 JSON-RPC 通知（换行符分隔）"""
        with self.lock:
            self._write_json_frame(payload)

    def send_request(self, request: Dict[str, Any], timeout: float = 20.0) -> Dict[str, Any]:
        """发送同步MCP请求"""
        with self.lock:
            try:
                if self.process.poll() is not None:
                    return {'success': False, 'error': f'MCP进程已终止: {self.process.returncode}'}
                
                # 清空队列
                while not self.response_queue.empty():
                    try:
                        self.response_queue.get_nowait()
                    except queue.Empty:
                        break
                
                # 发送请求（换行符分隔）
                print(f"📤 发送MCP请求: {request.get('method', 'unknown')}")
                self._write_json_frame(request)
                
                # 等待响应
                try:
                    response_text = self.response_queue.get(timeout=timeout)
                    print(f"📥 收到完整响应: {response_text[:200]}...")
                    try:
                        response_data = json.loads(response_text)
                        return {'success': True, 'data': response_data, 'raw': response_text}
                    except json.JSONDecodeError:
                        return {'success': True, 'data': response_text, 'raw': response_text}
                except queue.Empty:
                    print(f"⏰ 请求超时 ({timeout}s)")
                    return {'success': False, 'error': '请求超时'}
                
            except Exception as e:
                return {'success': False, 'error': f'通信异常: {str(e)}'}

def detect_simple_platform() -> Dict[str, Any]:
    """简化的平台检测"""
    platform_info = {
        'system': platform.system(),
        'architecture': platform.architecture()[0],
        'python_version': platform.python_version(),
        'node_available': False,
        'npx_path': None
    }
    
    # 检查Node.js和npx
    try:
        npx_path = shutil.which("npx")
        if npx_path:
            platform_info['node_available'] = True
            platform_info['npx_path'] = npx_path
            
            # 检查Node.js版本
            result = subprocess.run([npx_path, "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                platform_info['npx_version'] = result.stdout.strip()
    except Exception as e:
        print(f"⚠️ Node.js环境检测失败: {e}")
    
    return platform_info

@dataclass
class SimpleMCPServerInfo:
    """简化的MCP服务器信息"""
    package_name: str
    process: subprocess.Popen
    communicator: SimpleMCPCommunicator
    server_id: str
    available_tools: List[Dict[str, Any]]
    status: str = "running"
    start_time: float = 0.0

class SimpleMCPDeployer:
    """简化的MCP工具部署器"""
    
    def __init__(self):
        self.active_servers = {}  # server_id -> SimpleMCPServerInfo
        self.platform_info = detect_simple_platform()
        print(f"🖥️ 平台信息: {self.platform_info['system']} ({self.platform_info['architecture']})")
        
    def _try_start_process(self, cmd, creation_flags, display_name, run_command, package_name):
        """尝试启动进程，带--stdio回退机制"""
        try:
            # 构建进程参数（跨平台兼容）
            popen_kwargs = {
                'stdin': subprocess.PIPE,
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'cwd': str(Path.cwd()),
                'text': False,
                'bufsize': 0
            }
            
            # Windows特定的creation flags
            if self.platform_info['system'] == 'Windows':
                popen_kwargs['creationflags'] = creation_flags
            
            # 首次尝试
            process = subprocess.Popen(cmd, **popen_kwargs)
            
            # 等待一小段时间检查是否立即失败
            time.sleep(2)
            
            if process.poll() is not None:
                # 进程已退出，检查错误
                stdout, stderr = process.communicate()
                error_msg = stderr.decode() if stderr else ""
                
                # 如果是参数错误且有备用方案，则重试
                error_indicators = [
                    "unknown option '--stdio'",
                    "too many arguments",
                    "Expected 0 arguments but got",
                    "unexpected argument"
                ]
                
                if any(indicator in error_msg for indicator in error_indicators) and not run_command:
                    print(f"⚠️ {display_name} 不支持额外参数，尝试纯净启动...")
                    
                    # 重新构建命令（仅包含包名）
                    npx_path = self.platform_info['npx_path']
                    fallback_cmd = [npx_path, "-y", package_name]
                    print(f"📝 回退命令: {' '.join(fallback_cmd)}")
                    
                    process = subprocess.Popen(fallback_cmd, **popen_kwargs)
                    time.sleep(2)
                else:
                    raise Exception(f"MCP服务器启动失败: {error_msg}")
            
            return process
            
        except Exception as e:
            print(f"❌ 启动进程失败: {e}")
            return None
        
    def deploy_package(self, package_name: str, timeout: int = 30, run_command: str = None) -> Optional[SimpleMCPServerInfo]:
        """部署MCP包
        
        Args:
            package_name: 包名（仅在run_command为空时使用）
            timeout: 超时时间
            run_command: 完整的运行命令（优先使用，来自CSV数据）
        """
        if not package_name and not run_command:
            print("❌ 包名和运行命令都不能为空")
            return None
            
        display_name = run_command.split()[-1] if run_command else package_name
        server_id = f"mcp_{uuid.uuid4().hex[:8]}"
        print(f"🚀 开始部署: {display_name}")
        print(f"🆔 服务器ID: {server_id}")
        
        try:
            # 检查Node.js环境
            if not self.platform_info['node_available']:
                raise Exception("Node.js/npx不可用，请先安装Node.js")
            
            npx_path = self.platform_info['npx_path']
            print(f"✅ 找到npx: {npx_path}")
            
            # 构建启动命令 - 优先使用run_command
            if run_command:
                # 解析完整的run_command
                cmd_parts = run_command.split()
                if cmd_parts[0] == "npx":
                    cmd = [npx_path] + cmd_parts[1:]
                else:
                    cmd = [npx_path, "-y"] + cmd_parts
            else:
                # 默认不添加 --stdio，因为很多MCP工具不支持这个参数
                cmd = [npx_path, "-y", package_name]
            
            print(f"📝 执行命令: {' '.join(cmd)}")
            
            # 启动MCP服务器进程
            creation_flags = 0
            if self.platform_info['system'] == 'Windows':
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            process = self._try_start_process(cmd, creation_flags, display_name, run_command, package_name)
            if not process:
                return None
                
            print(f"📦 MCP进程启动: PID={process.pid}")
            print(f"⏳ 等待 {display_name} 启动...")
            
            # 创建通信器
            communicator = SimpleMCPCommunicator(process)
            time.sleep(1)
            
            # 初始化MCP协议
            print("🔗 初始化MCP协议...")
            available_tools = self._initialize_mcp_protocol(communicator, package_name, timeout)
            
            # 创建服务器信息
            server_info = SimpleMCPServerInfo(
                package_name=package_name,
                process=process,
                communicator=communicator,
                server_id=server_id,
                available_tools=available_tools,
                status="running",
                start_time=time.time()
            )
            
            # 保存到活动服务器列表
            self.active_servers[server_id] = server_info
            
            print(f"✅ {package_name} 部署成功！")
            print(f"🔧 可用工具: {[tool.get('name') for tool in available_tools]}")
            
            return server_info
            
        except Exception as e:
            print(f"❌ 部署 {package_name} 失败: {e}")
            if 'process' in locals():
                try:
                    process.terminate()
                except:
                    pass
            return None
    
    def _initialize_mcp_protocol(self, communicator: SimpleMCPCommunicator, 
                               package_name: str, timeout: int) -> List[Dict[str, Any]]:
        """初始化MCP协议并获取工具列表"""
        
        # 1. Initialize请求 (移除可选字段以增强兼容性)
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "simple-mcp-client", 
                    "version": "1.0.0"
                }
            }
        }
        
        init_result = communicator.send_request(init_request, timeout=timeout)
        if not init_result['success']:
            # 尝试更简化的初始化
            print(f"⚠️ 标准初始化失败: {init_result['error']}")
            print("🔄 尝试简化初始化...")
            
            simple_init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05"
                }
            }
            
            init_result = communicator.send_request(simple_init_request, timeout=timeout)
            if not init_result['success']:
                raise Exception(f"MCP初始化失败: {init_result['error']}")
        
        print("✅ MCP协议初始化成功")
        # 2. Initialized通知 (MCP协议要求此通知不能有params字段)
        init_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        communicator.send_notification(init_notification)
        print("✅ 发送initialized通知完成")

        # 3. 获取工具列表 (某些MCP工具不需要params字段)
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        tools_result = communicator.send_request(tools_request, timeout=timeout)
        if tools_result['success'] and 'data' in tools_result:
            tools_data = tools_result['data']
            if isinstance(tools_data, dict) and "result" in tools_data:
                tools = tools_data["result"].get("tools", [])
                return tools

        raise Exception("获取工具列表失败")
    
    def cleanup_server(self, server_id: str) -> bool:
        """清理指定的服务器"""
        if server_id not in self.active_servers:
            return False
            
        server_info = self.active_servers[server_id]
        print(f"🧹 清理服务器: {server_info.package_name} (ID: {server_id})")
        
        try:
            server_info.process.terminate()
            server_info.process.wait(timeout=5)
            print(f"✅ 服务器 {server_id} 已停止")
        except Exception as e:
            print(f"⚠️ 清理异常: {e}")
        
        # 从活动列表中移除
        del self.active_servers[server_id]
        return True
    
    def cleanup_all(self):
        """清理所有服务器"""
        print("🧹 清理所有MCP服务器...")
        
        server_ids = list(self.active_servers.keys())
        for server_id in server_ids:
            self.cleanup_server(server_id)
        
        print("✅ 所有服务器已清理完成")

# 全局部署器实例
_simple_deployer_instance = None

def get_simple_mcp_deployer() -> SimpleMCPDeployer:
    """获取全局简化MCP部署器实例"""
    global _simple_deployer_instance
    if _simple_deployer_instance is None:
        _simple_deployer_instance = SimpleMCPDeployer()
    return _simple_deployer_instance
