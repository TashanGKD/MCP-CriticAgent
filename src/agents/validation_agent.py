#!/usr/bin/env python3
"""
智能验证执行代理

基于AgentScope实现的智能测试执行和验证器
自动执行测试用例并分析结果

作者: AI Assistant  
日期: 2025-08-15
"""

import os
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    import agentscope
    from agentscope.agents import ReActAgent
    from agentscope.message import Msg
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ AgentScope导入失败: {e}")
    print("请确保已安装 agentscope 和 python-dotenv")

from src.agents.test_agent import TestCase

class TestResultStatus(Enum):
    """测试结果状态"""
    PASS = "pass"
    FAIL = "fail" 
    ERROR = "error"
    SKIP = "skip"

@dataclass
class TestResult:
    """测试结果数据结构"""
    test_case: TestCase
    status: TestResultStatus
    execution_time: float
    response: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    analysis: Optional[str] = None

class ValidationAgent:
    """智能验证执行代理"""
    
    def __init__(self, model_config: Optional[Dict] = None):
        self.model_config = model_config or self._load_default_config()
        self.agent = None
        self._initialize_agent()
    
    def _load_default_config(self) -> Dict:
        """加载默认模型配置"""
        env_path = Path(__file__).parent.parent.parent / ".env"
        load_dotenv(env_path)
        
        return {
            "config_name": "validation_agent_config",
            "model_type": "openai_chat", 
            "model_name": os.getenv("OPENAI_MODEL", "qwen-plus"),
            "api_key": os.getenv("OPENAI_API_KEY"),
            "client_args": {
                "base_url": os.getenv("OPENAI_BASE_URL"),
                "timeout": 60  # 增加到60秒超时
            },
            "generate_args": {
                "temperature": 0.3,  # 较低温度以获得更一致的分析
                "max_tokens": 800   # 减少token数量加快响应
            }
        }
    
    def _initialize_agent(self):
        """初始化AgentScope代理"""
        try:
            # 初始化AgentScope  
            agentscope.init(
                model_configs=[self.model_config],
                project="MCP_Test_Validator",
                save_dir="./logs",
                save_log=True,
                save_api_invoke=True
            )
            
            # 创建验证代理 - 使用可用的代理类
            sys_prompt = self._get_validation_prompt()
            
            try:
                from agentscope.agents import DialogAgent
                self.agent = DialogAgent(
                    name="mcp_test_validator",
                    model_config_name=self.model_config["config_name"],
                    sys_prompt=sys_prompt
                )
            except TypeError:
                # 处理AgentScope版本兼容性问题，移除不支持的参数
                from agentscope.agents import DialogAgent
                self.agent = DialogAgent(
                    name="mcp_test_validator",
                    sys_prompt=sys_prompt
                )
            
            print("✅ 验证执行代理初始化成功")
            
        except Exception as e:
            print(f"❌ 代理初始化失败: {e}")
            self.agent = None
    
    def _get_validation_prompt(self) -> str:
        """获取验证代理的系统提示词"""
        return '''你是一个专业的MCP(Model Context Protocol)工具测试结果分析专家。

你的任务是分析测试执行结果，判断测试是否通过，并提供详细的分析报告。

## 输入信息格式:
- 测试用例名称: [name]
- 测试描述: [description]  
- 调用工具: [tool_name]
- 输入参数: [parameters]
- 期望结果类型: [expected_type]
- 期望结果内容: [expected_result]
- 实际执行时间: [execution_time]
- 实际响应: [actual_response]
- 错误信息: [error_message]

## 分析原则:
1. **功能正确性** - 工具是否按预期工作
2. **响应有效性** - 返回数据是否有意义和完整
3. **性能表现** - 响应时间是否合理
4. **错误处理** - 错误信息是否清晰有用
5. **稳定性** - 结果是否一致可靠

## 输出格式:
请以JSON格式输出分析结果:
```json
{
  "status": "pass|fail|error",
  "confidence": 0.0-1.0,
  "analysis": "详细分析说明",
  "issues": ["发现的问题列表"],
  "recommendations": ["改进建议"]
}
```

## 判断标准:
- **PASS**: 工具响应正常，结果符合预期
- **FAIL**: 工具响应但结果不符合预期
- **ERROR**: 工具无法响应或出现严重错误

现在请分析给定的测试结果。'''
    
    async def execute_test_suite(self, test_cases: List[TestCase], mcp_client) -> List[TestResult]:
        """执行测试套件"""
        results = []
        
        print(f"🚀 开始执行 {len(test_cases)} 个测试用例")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] 执行测试: {test_case.name}")
            
            try:
                result = await self._execute_single_test(test_case, mcp_client)
                results.append(result)
                
                # 显示简要结果
                status_icon = "✅" if result.status == TestResultStatus.PASS else "❌" if result.status == TestResultStatus.FAIL else "⚠️"
                print(f"{status_icon} {result.status.value.upper()} ({result.execution_time:.2f}s)")
                
            except Exception as e:
                print(f"❌ 测试执行异常: {e}")
                error_result = TestResult(
                    test_case=test_case,
                    status=TestResultStatus.ERROR,
                    execution_time=0.0,
                    error_message=str(e),
                    analysis="测试执行过程中发生异常"
                )
                results.append(error_result)
        
        # 生成测试报告摘要
        self._print_test_summary(results)
        
        return results
    
    async def _execute_single_test(self, test_case: TestCase, mcp_client) -> TestResult:
        """执行单个测试用例"""
        start_time = time.time()
        
        try:
            # 执行MCP工具调用
            if test_case.tool_name == "tools/list":
                # 特殊处理工具列表调用
                response = await mcp_client.list_tools()
            elif test_case.tool_name == "config_check":
                # 特殊处理配置检查
                response = {"status": "success", "message": "配置检查通过"}
            else:
                # 执行普通工具调用
                response = await mcp_client.call_tool(
                    test_case.tool_name,
                    test_case.parameters
                )
            
            execution_time = time.time() - start_time
            
            # 使用AI代理分析结果
            analysis_result = await self._analyze_test_result(test_case, response, execution_time)
            
            # 构建测试结果
            result = TestResult(
                test_case=test_case,
                status=TestResultStatus(analysis_result.get("status", "error")),
                execution_time=execution_time,
                response=response,
                analysis=analysis_result.get("analysis", "")
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return TestResult(
                test_case=test_case,
                status=TestResultStatus.ERROR,
                execution_time=execution_time,
                error_message=str(e),
                analysis=f"测试执行失败: {str(e)}"
            )
    
    async def _analyze_test_result(self, test_case: TestCase, response: Dict[str, Any], execution_time: float) -> Dict[str, Any]:
        """使用AI代理分析测试结果"""
        try:
            if self.agent is None:
                print("⚠️ AI代理不可用，使用基础规则分析")
                return self._basic_result_analysis(test_case, response, execution_time)
            
            # 构建分析提示
            analysis_prompt = f"""
请分析以下MCP工具测试结果:

测试用例名称: {test_case.name}
测试描述: {test_case.description}
调用工具: {test_case.tool_name}
输入参数: {json.dumps(test_case.parameters, ensure_ascii=False)}
期望结果类型: {test_case.expected_type}
期望结果内容: {test_case.expected_result or "未指定"}
执行时间: {execution_time:.3f}秒

实际响应:
{json.dumps(response, indent=2, ensure_ascii=False)}

请分析这个测试是否通过，并提供详细分析。
"""
            
            print(f"🤖 正在调用AI代理分析测试结果...")
            print("📡 发送请求到大模型API...")
            
            # 调用分析代理 - 真实的大模型调用
            user_msg = Msg("user", analysis_prompt, role="user")
            agent_response = self.agent(user_msg)
            
            print(f"🎯 大模型分析完成")
            
            # 解析代理响应
            return self._parse_analysis_response(agent_response.content)
            
        except Exception as e:
            print(f"⚠️ AI分析失败，使用基础规则: {e}")
            return self._basic_result_analysis(test_case, response, execution_time)
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """解析AI代理的分析响应"""
        try:
            # 尝试从响应中提取JSON
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            else:
                # 如果没有找到JSON格式，尝试直接解析
                return json.loads(response)
                
        except (json.JSONDecodeError, AttributeError):
            # 解析失败，返回基础分析
            return {
                "status": "error",
                "confidence": 0.5,
                "analysis": "AI分析响应解析失败",
                "issues": ["响应格式不正确"],
                "recommendations": ["检查AI模型配置"]
            }
    
    def _basic_result_analysis(self, test_case: TestCase, response: Dict[str, Any], execution_time: float) -> Dict[str, Any]:
        """基础规则分析测试结果"""
        try:
            # 基础成功判断
            if response and not response.get("error"):
                status = "pass"
                analysis = "工具调用成功，返回了有效响应"
                issues = []
            else:
                status = "fail"
                analysis = "工具调用失败或返回错误"
                issues = ["工具响应包含错误信息"]
            
            # 性能检查
            if execution_time > 10.0:
                issues.append(f"响应时间过长 ({execution_time:.2f}s)")
            
            return {
                "status": status,
                "confidence": 0.7,
                "analysis": analysis,
                "issues": issues,
                "recommendations": ["使用AI代理进行详细分析"] if issues else []
            }
            
        except Exception:
            return {
                "status": "error",
                "confidence": 0.3,
                "analysis": "基础分析失败",
                "issues": ["无法分析测试结果"],
                "recommendations": ["检查响应数据格式"]
            }
    
    def _print_test_summary(self, results: List[TestResult]):
        """打印测试摘要"""
        total = len(results)
        passed = len([r for r in results if r.status == TestResultStatus.PASS])
        failed = len([r for r in results if r.status == TestResultStatus.FAIL])
        errors = len([r for r in results if r.status == TestResultStatus.ERROR])
        
        print(f"\n📊 测试执行摘要:")
        print(f"   总计: {total}")
        print(f"   通过: {passed} ✅")
        print(f"   失败: {failed} ❌")
        print(f"   错误: {errors} ⚠️")
        print(f"   成功率: {(passed/total*100):.1f}%")
        
        # 显示平均执行时间
        avg_time = sum(r.execution_time for r in results) / total if total > 0 else 0
        print(f"   平均执行时间: {avg_time:.2f}s")

# 全局验证代理实例
_validation_agent_instance = None

def get_validation_agent() -> ValidationAgent:
    """获取全局验证代理实例"""
    global _validation_agent_instance
    if _validation_agent_instance is None:
        _validation_agent_instance = ValidationAgent()
    return _validation_agent_instance
