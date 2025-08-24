#!/usr/bin/env python3
"""
MCP 测试核心逻辑 - 简洁版

遵循 Linus 的"好品味"原则：
- 消除所有特殊情况
- 每个函数只做一件事
- 无3层以上缩进

作者: AI Assistant (Linus重构版)
日期: 2025-08-18
版本: 2.0.0 (简洁版)
"""

import time
import asyncio
from typing import Tuple, List, Optional
from dataclasses import dataclass

from src.core.report_generator import TestResult
from src.utils.csv_parser import MCPToolInfo


@dataclass
class TestConfig:
    """测试配置 - 统一数据结构"""
    timeout: int = 600
    verbose: bool = False
    smart_test: bool = False
    cleanup: bool = True
    save_report: bool = True
    db_export: bool = False
    evaluate: bool = True


class MCPTester:
    """MCP测试器 - 核心测试逻辑"""
    
    def __init__(self):
        self.parser = None
        self.deployer = None
        
    def _get_services(self):
        """延迟加载服务 - 避免循环导入"""
        if not self.parser:
            from src.utils.csv_parser import get_mcp_parser
            from src.core.simple_mcp_deployer import get_simple_mcp_deployer
            self.parser = get_mcp_parser()
            self.deployer = get_simple_mcp_deployer()
        return self.parser, self.deployer
    
    def find_tool_by_url(self, url: str) -> Optional[MCPToolInfo]:
        """根据URL查找工具信息"""
        parser, _ = self._get_services()
        return parser.find_tool_by_url(url)
    
    def deploy_tool(self, package_name: str, timeout: int):
        """部署MCP工具"""
        _, deployer = self._get_services()
        return deployer.deploy_package(package_name, timeout)
    
    def cleanup_server(self, server_id: str):
        """清理服务器"""
        _, deployer = self._get_services()
        return deployer.cleanup_server(server_id)
    
    def run_basic_test(self, server_info, timeout: int = 10) -> Tuple[bool, List[TestResult]]:
        """基础连通性测试 - 简化版"""
        test_results = []
        
        # 1. MCP协议通信测试
        comm_result = self._test_mcp_communication(server_info, timeout)
        test_results.append(comm_result)
        
        if not comm_result.success:
            return False, test_results
        
        # 2. 工具调用测试（如果有工具）
        if server_info.available_tools:
            tool_result = self._test_first_tool(server_info, timeout)
            test_results.append(tool_result)
        
        return True, test_results
    
    def _test_mcp_communication(self, server_info, timeout: int) -> TestResult:
        """MCP协议通信测试 - 单一职责"""
        start_time = time.time()
        
        request = {
            "jsonrpc": "2.0",
            "id": 999,
            "method": "tools/list",
            "params": {}
        }
        
        result = server_info.communicator.send_request(request, timeout=timeout)
        duration = time.time() - start_time
        
        return TestResult(
            test_name="MCP协议通信测试",
            success=result['success'],
            duration=duration,
            error_message=result.get('error') if not result['success'] else None
        )
    
    def _test_first_tool(self, server_info, timeout: int) -> TestResult:
        """测试第一个可用工具 - 智能参数生成"""
        first_tool = server_info.available_tools[0]
        tool_name = first_tool.get('name', 'unknown')
        
        start_time = time.time()
        
        # 生成基本测试参数
        arguments = self._generate_test_arguments(first_tool)
        
        request = {
            "jsonrpc": "2.0",
            "id": 1000,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        result = server_info.communicator.send_request(request, timeout=timeout)
        duration = time.time() - start_time
        
        return TestResult(
            test_name=f"工具调用测试: {tool_name}",
            success=result['success'],
            duration=duration,
            error_message=result.get('error') if not result['success'] else None
        )
    
    def _generate_test_arguments(self, tool_info: dict) -> dict:
        """为工具生成基本测试参数 - Linus式简单逻辑"""
        tool_name = tool_info.get('name', '')
        input_schema = tool_info.get('inputSchema', {})
        properties = input_schema.get('properties', {})
        required = input_schema.get('required', [])
        
        arguments = {}
        
        # 特殊工具的精确参数
        if tool_name == 'resolve-library-id':
            arguments = {"libraryName": "react"}
        elif tool_name == 'get-library-docs':
            arguments = {"context7CompatibleLibraryID": "/facebook/react"}
        elif 'library' in tool_name.lower():
            arguments = {"library": "react"}
        elif 'query' in tool_name.lower():
            arguments = {"query": "test"}
        elif 'search' in tool_name.lower():
            arguments = {"query": "example"}
        elif 'file' in tool_name.lower():
            arguments = {"path": "/tmp/test.txt"}
        else:
            # 根据schema和required字段生成参数
            for prop_name in required:
                prop_info = properties.get(prop_name, {})
                prop_type = prop_info.get('type', 'string')
                
                if prop_type == 'string':
                    # 基于属性名称的启发式
                    if 'name' in prop_name.lower():
                        arguments[prop_name] = "test"
                    elif 'id' in prop_name.lower():
                        arguments[prop_name] = "/test/example"
                    elif 'query' in prop_name.lower():
                        arguments[prop_name] = "example query"
                    elif 'path' in prop_name.lower():
                        arguments[prop_name] = "/tmp/test"
                    else:
                        arguments[prop_name] = "test_value"
                elif prop_type == 'number' or prop_type == 'integer':
                    arguments[prop_name] = 1000 if 'token' in prop_name.lower() else 1
                elif prop_type == 'boolean':
                    arguments[prop_name] = True
                elif prop_type == 'array':
                    arguments[prop_name] = []
                elif prop_type == 'object':
                    arguments[prop_name] = {}
        
        return arguments
    
    async def run_smart_test(self, tool_info: MCPToolInfo, server_info, verbose: bool) -> Tuple[bool, List[TestResult]]:
        """智能测试 - 简化版"""
        try:
            # 动态导入，避免强依赖
            from src.agents.test_agent import get_test_generator
            from src.agents.validation_agent import get_validation_agent
            from src.core.async_mcp_client import AsyncMCPClient
            
            test_generator = get_test_generator()
            validation_agent = get_validation_agent()
            
            # 生成测试用例
            test_cases = test_generator.generate_test_cases(tool_info, server_info.available_tools)
            
            if not test_cases:
                return self.run_basic_test(server_info)
            
            # 执行智能验证
            mcp_client = AsyncMCPClient(server_info.communicator)
            ai_results = await validation_agent.execute_test_suite(test_cases, mcp_client)
            
            # 转换结果格式
            test_results = []
            for r in ai_results:
                test_results.append(TestResult(
                    test_name=r.test_case.name,
                    success=(r.status.value == "pass"),
                    duration=r.execution_time,
                    error_message=r.error_message
                ))
            
            passed = sum(1 for r in ai_results if r.status.value == "pass")
            success_rate = passed / len(ai_results) if ai_results else 0
            
            return (success_rate >= 0.7), test_results
            
        except ImportError:
            # 智能测试不可用，回退到基础测试
            return self.run_basic_test(server_info)


# 全局测试器实例
_tester = MCPTester()

def get_mcp_tester() -> MCPTester:
    """获取全局测试器实例"""
    return _tester
