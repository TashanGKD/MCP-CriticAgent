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
        'npx_path': None,
        'uv_available': False,
        'uvx_path': None
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
    
    # 检查uv和uvx
    try:
        uvx_path = shutil.which("uvx")
        if uvx_path:
            platform_info['uv_available'] = True
            platform_info['uvx_path'] = uvx_path
            
            # 检查uvx版本
            result = subprocess.run([uvx_path, "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                platform_info['uvx_version'] = result.stdout.strip()
    except Exception as e:
        print(f"⚠️ UV环境检测失败: {e}")
    
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
    
    def detect_simple_platform(self, github_url: str) -> tuple[str, str]:
        """根据GitHub URL检测简单平台类型（运行时）
        
        Args:
            github_url: GitHub仓库URL
            
        Returns:
            (runtime_type, runtime_command): 运行时类型和对应的命令路径
        """
        # 检查URL中是否包含uvx的指示信息
        uvx_indicators = [
            '/uv-',         # 包含uv-前缀
            'uvx://',       # uvx协议
            'uv-mcp',       # uv-mcp字样
            '-uv-',         # 中间包含-uv-
            'uv_mcp',       # uv_mcp字样（下划线）
        ]
        
        if any(indicator in github_url for indicator in uvx_indicators):
            return "uvx", self._get_uvx_command()
        
        # 默认使用npx
        return "npx", self._get_npx_command()
    
    def _get_npx_command(self) -> str:
        """获取npx命令路径"""
        if self.platform_info['node_available'] and self.platform_info['npx_path']:
            return self.platform_info['npx_path']
        return "npx"
    
    def _get_uvx_command(self) -> str:
        """获取uvx命令路径"""
        if self.platform_info['uv_available'] and self.platform_info['uvx_path']:
            return self.platform_info['uvx_path']  
        return "uvx"
        
    def _get_runtime_info(self, run_command: str = None, package_name: str = None) -> Dict[str, Any]:
        """获取运行时信息（npx或uvx）
        
        Args:
            run_command: 完整的运行命令，如 "uvx excel-mcp-server stdio"
            package_name: 包名（当没有run_command时使用）
            
        Returns:
            包含runtime_type, runtime_path, display_name等的字典
        """
        runtime_info = {
            'runtime_type': 'npx',  # 默认使用npx
            'runtime_path': None,
            'display_name': package_name or 'unknown',
            'available': False
        }
        
        # 从run_command推断运行时类型
        if run_command:
            cmd_parts = run_command.split()
            if cmd_parts and cmd_parts[0] in ['uvx', 'npx']:
                runtime_info['runtime_type'] = cmd_parts[0]
                runtime_info['display_name'] = cmd_parts[-1] if len(cmd_parts) > 1 else cmd_parts[0]
            else:
                # 如果不是以uvx或npx开头，假设是包名，默认使用npx
                runtime_info['display_name'] = run_command.split()[-1]
        
        # 检查对应的运行时是否可用
        if runtime_info['runtime_type'] == 'uvx':
            if self.platform_info['uv_available']:
                runtime_info['runtime_path'] = self.platform_info['uvx_path']
                runtime_info['available'] = True
            else:
                print(f"⚠️ uvx不可用，fallback到npx")
                runtime_info['runtime_type'] = 'npx'
        
        if runtime_info['runtime_type'] == 'npx':
            if self.platform_info['node_available']:
                runtime_info['runtime_path'] = self.platform_info['npx_path']
                runtime_info['available'] = True
        
        return runtime_info

    def _build_runtime_command(self, runtime_info: Dict[str, Any], run_command: str = None, package_name: str = None) -> List[str]:
        """构建运行时命令
        
        Args:
            runtime_info: 运行时信息
            run_command: 完整的运行命令
            package_name: 包名
            
        Returns:
            命令列表
        """
        runtime_path = runtime_info['runtime_path']
        runtime_type = runtime_info['runtime_type']
        
        if run_command:
            # 处理占位符
            processed_command = run_command.replace('[transport]', 'stdio')
            
            # 解析完整的run_command
            cmd_parts = processed_command.split()
            if cmd_parts[0] in ['npx', 'uvx']:
                # 替换第一个词为实际的运行时路径
                if runtime_type == 'npx':
                    return [runtime_path] + cmd_parts[1:]
                else:  # uvx
                    return [runtime_path] + cmd_parts[1:]
            else:
                # 不是标准格式，添加运行时前缀
                if runtime_type == 'npx':
                    return [runtime_path, "-y"] + cmd_parts
                else:  # uvx
                    return [runtime_path] + cmd_parts
        else:
            # 使用包名构建命令
            if runtime_type == 'npx':
                return [runtime_path, "-y", package_name]
            else:  # uvx
                return [runtime_path, package_name]

    def _try_start_process(self, cmd, creation_flags, display_name, run_command, package_name, runtime_info):
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
                    runtime_type = runtime_info['runtime_type']
                    runtime_path = runtime_info['runtime_path']
                    if runtime_type == 'npx':
                        fallback_cmd = [runtime_path, "-y", package_name]
                    else:  # uvx
                        fallback_cmd = [runtime_path, package_name]
                    print(f"📝 回退命令: {' '.join(fallback_cmd)}")
                    
                    process = subprocess.Popen(fallback_cmd, **popen_kwargs)
                    time.sleep(2)
                else:
                    raise Exception(f"MCP服务器启动失败: {error_msg}")
            
            return process
            
        except Exception as e:
            print(f"❌ 启动进程失败: {e}")
            return None
        
    def deploy_package(self, package_name: str, timeout: int = 30, run_command: str = None, github_url: str = None) -> Optional[SimpleMCPServerInfo]:
        """部署MCP包
        
        Args:
            package_name: 包名（仅在run_command为空时使用）
            timeout: 超时时间
            run_command: 完整的运行命令（优先使用，来自CSV数据）
            github_url: GitHub URL（用于智能运行时检测）
        """
        if not package_name and not run_command:
            print("❌ 包名和运行命令都不能为空")
            return None
            
        # 如果提供了GitHub URL，尝试智能检测运行时
        if github_url and not run_command:
            runtime_type, runtime_cmd = self.detect_simple_platform(github_url)
            print(f"🔍 根据GitHub URL检测到运行时: {runtime_type}")
            
            # 构建基于GitHub URL的运行命令
            if runtime_type == "uvx" and "/uv-" in github_url:
                # 从GitHub URL中提取包名或使用--from参数
                if package_name:
                    run_command = f"uvx {package_name}"
                else:
                    run_command = f"uvx --from git+{github_url} mcp-server"
            elif runtime_type == "npx":
                run_command = f"npx -y {package_name}" if package_name else None

        # 获取运行时信息
        runtime_info = self._get_runtime_info(run_command, package_name)
        display_name = runtime_info['display_name']
        runtime_type = runtime_info['runtime_type']
        
        server_id = f"mcp_{uuid.uuid4().hex[:8]}"
        print(f"🚀 开始部署: {display_name}")
        print(f"🆔 服务器ID: {server_id}")
        print(f"🔧 运行时: {runtime_type}")
        
        try:
            # 检查运行时环境
            if not runtime_info['available']:
                if runtime_type == 'uvx':
                    raise Exception("uvx不可用，请先安装uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
                else:
                    raise Exception("npx不可用，请先安装Node.js")
            
            runtime_path = runtime_info['runtime_path']
            print(f"✅ 找到{runtime_type}: {runtime_path}")
            
            # 构建启动命令
            cmd = self._build_runtime_command(runtime_info, run_command, package_name)
            print(f"📝 执行命令: {' '.join(cmd)}")
            
            # 启动MCP服务器进程
            creation_flags = 0
            if self.platform_info['system'] == 'Windows':
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            process = self._try_start_process(cmd, creation_flags, display_name, run_command, package_name, runtime_info)
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
