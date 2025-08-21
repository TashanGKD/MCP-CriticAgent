#!/usr/bin/env python3
"""
智能测试生成代理

基于AgentScope实现的智能测试用例生成器
根据MCP工具的功能和参数自动生成测试用例

作者: AI Assistant
日期: 2025-08-15
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

try:
    import agentscope
    from agentscope.agents import ReActAgent
    from agentscope.message import Msg
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ AgentScope导入失败: {e}")
    print("请确保已安装 agentscope 和 python-dotenv")

from src.utils.csv_parser import MCPToolInfo

@dataclass
class TestCase:
    """测试用例数据结构"""
    name: str
    description: str
    tool_name: str
    parameters: Dict[str, Any]
    expected_type: str  # success, error, specific_content
    expected_result: Optional[str] = None
    priority: str = "normal"  # high, normal, low

class TestGeneratorAgent:
    """智能测试用例生成代理"""
    
    def __init__(self, model_config: Optional[Dict] = None):
        self.model_config = model_config or self._load_default_config()
        self.agent = None
        self._initialize_agent()
    
    def _load_default_config(self) -> Dict:
        """加载默认模型配置"""
        # 加载环境变量
        env_path = Path(__file__).parent.parent.parent / ".env"
        load_dotenv(env_path)
        
        return {
            "config_name": "test_generator_config",
            "model_type": "openai_chat",
            "model_name": os.getenv("OPENAI_MODEL", "qwen-plus"),
            "api_key": os.getenv("OPENAI_API_KEY"),
            "client_args": {
                "base_url": os.getenv("OPENAI_BASE_URL"),
                "timeout": 60  # 增加到60秒超时
            },
            "generate_args": {
                "temperature": 0.7,
                "max_tokens": 1000  # 减少token数量加快响应
            }
        }
    
    def _initialize_agent(self):
        """初始化AgentScope代理"""
        try:
            # 初始化AgentScope
            agentscope.init(
                model_configs=[self.model_config],
                project="MCP_Test_Generator",
                save_dir="./logs",
                save_log=True,
                save_api_invoke=True
            )
            
            # 创建测试生成代理 - 使用UserAgent替代ReActAgent
            sys_prompt = self._get_test_generator_prompt()
            
            try:
                from agentscope.agents import DialogAgent
                self.agent = DialogAgent(
                    name="mcp_test_generator",
                    model_config_name=self.model_config["config_name"],
                    sys_prompt=sys_prompt
                )
            except TypeError:
                # 处理AgentScope版本兼容性问题，移除不支持的参数
                from agentscope.agents import DialogAgent
                self.agent = DialogAgent(
                    name="mcp_test_generator",
                    sys_prompt=sys_prompt
                )
            
            print("✅ 测试生成代理初始化成功")
            
        except Exception as e:
            print(f"❌ 代理初始化失败: {e}")
            self.agent = None  # 标记为不可用
    
    def _get_test_generator_prompt(self) -> str:
        """获取测试生成代理的系统提示词"""
        return '''你是一个专业的MCP(Model Context Protocol)工具测试用例生成专家。

你的任务是根据MCP工具的信息生成实用、现实的测试用例，重点验证工具的核心功能是否正常工作。

## 工具信息输入格式:
- 工具名称: [name]
- 作者: [author] 
- 描述: [description]
- 类别: [category]
- 包名: [package_name]
- 可用工具列表: [available_tools]
- API密钥需求: [requires_api_key]

## 测试用例生成原则（最多4个测试用例）:
1. **基础功能测试** - 验证主要工具能否正常响应（使用常见、有效的参数）
2. **实际使用场景测试** - 测试工具在真实环境下的表现
3. **容错能力测试** - 测试工具对不完美输入的处理（但不必期望严格的错误返回）
4. **边界情况测试**（可选） - 测试工具在特殊情况下是否仍能工作

## 重要测试设计原则:
- **宽松的成功标准**: 只要工具响应了且返回结构化数据，通常认为成功
- **实际的参数选择**: 使用真实存在、常用的参数值（如popular libraries, common queries）
- **合理的期望**: 工具返回相关信息即可，不必完全匹配期望格式
- **避免过度严格**: 错误处理测试应该宽松，工具返回任何信息都比崩溃好

## 具体建议:
- 对于搜索类工具：使用热门、真实存在的搜索词
- 对于文档获取工具：使用知名库/项目ID
- 对于API工具：使用简单、不需要复杂配置的调用
- 错误测试：重点验证工具不会崩溃，而非期望特定错误格式

## 输出格式要求:
请以JSON格式输出测试用例列表，每个测试用例包含:
```json
{
  "test_cases": [
    {
      "name": "测试用例名称",
      "description": "详细描述，说明测试目标",
      "tool_name": "要调用的工具名称",
      "parameters": {"param1": "realistic_value", "param2": "common_value"},
      "expected_type": "success|error|any_response",
      "expected_result": "宽松的期望描述，重点是工具能响应",
      "priority": "high|normal|low"
    }
  ]
}
```

## expected_type说明:
- "success": 期望工具返回有用信息（最常用）
- "any_response": 只要工具响应且不崩溃即可（用于容错测试）
- "error": 仅在明确应该失败的情况使用（如恶意输入）

现在请为给定的MCP工具生成实用、容易通过的测试用例。'''
    
    def generate_test_cases(self, tool_info: MCPToolInfo, available_tools: List[Dict[str, Any]]) -> List[TestCase]:
        """为指定MCP工具生成测试用例"""
        try:
            if self.agent is None:
                print("⚠️ 智能代理不可用，使用备选测试用例")
                return self._generate_fallback_test_cases(tool_info, available_tools)
            
            # 构建工具信息提示
            tool_info_text = f"""
请为以下MCP工具生成测试用例:

工具名称: {tool_info.name}
作者: {tool_info.author}
描述: {tool_info.description}
类别: {tool_info.category}
包名: {tool_info.package_name}
API密钥需求: {"是" if tool_info.requires_api_key else "否"}
API密钥列表: {tool_info.api_requirements if tool_info.requires_api_key else "无"}

可用工具列表:
{json.dumps(available_tools, indent=2, ensure_ascii=False)}

请生成3-5个最重要的测试用例来验证这个MCP工具的核心功能（严格不要超过5个）。优先选择最具代表性的测试场景。
"""
            
            print(f"🤖 正在为 {tool_info.name} 生成真实测试用例...")
            print("📡 调用大模型API...")
            
            # 调用代理生成测试用例 - 使用真实的大模型API
            user_msg = Msg("user", tool_info_text, role="user")
            response = self.agent(user_msg)
            
            print(f"🎯 大模型响应: {response.content[:200]}...")
            
            # 解析响应并生成测试用例
            test_cases = self._parse_test_cases_response(response.content, tool_info, available_tools)
            
            if test_cases:
                print(f"✅ 成功生成 {len(test_cases)} 个真实测试用例")
                return test_cases
            else:
                print("⚠️ 大模型响应解析失败，使用备选测试用例")
                return self._generate_fallback_test_cases(tool_info, available_tools)
            
        except Exception as e:
            print(f"❌ 生成测试用例失败: {e}")
            print("🔄 回退到基于工具信息的智能推断测试用例")
            # 返回基于真实工具信息的推断测试用例（非模拟）
            return self._generate_fallback_test_cases(tool_info, available_tools)
    
    def _parse_test_cases_response(self, response: str, tool_info: MCPToolInfo, available_tools: List[Dict[str, Any]]) -> List[TestCase]:
        """解析代理响应并转换为测试用例"""
        test_cases = []
        
        try:
            # 尝试从响应中提取JSON
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析整个响应
                json_str = response
            
            # 解析JSON
            data = json.loads(json_str)
            
            if isinstance(data, dict) and "test_cases" in data:
                for tc_data in data["test_cases"]:
                    test_case = TestCase(
                        name=tc_data.get("name", "未命名测试"),
                        description=tc_data.get("description", ""),
                        tool_name=tc_data.get("tool_name", ""),
                        parameters=tc_data.get("parameters", {}),
                        expected_type=tc_data.get("expected_type", "success"),
                        expected_result=tc_data.get("expected_result"),
                        priority=tc_data.get("priority", "normal")
                    )
                    test_cases.append(test_case)
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ 解析代理响应失败: {e}")
            # 返回基础测试用例
            return self._generate_fallback_test_cases(tool_info, available_tools)
        
        return test_cases
    
    def _generate_fallback_test_cases(self, tool_info: MCPToolInfo, available_tools: List[Dict[str, Any]]) -> List[TestCase]:
        """生成备选的基础测试用例"""
        test_cases = []
        
        # 基础连通性测试
        test_cases.append(TestCase(
            name="基础连通性测试",
            description="验证MCP工具是否正常响应",
            tool_name="tools/list",
            parameters={},
            expected_type="success",
            priority="high"
        ))
        
        # 为每个可用工具生成基础测试（限制为2个工具以提高速度）
        for tool in available_tools[:2]:  # 限制为前2个工具
            tool_name = tool.get("name", "unknown")
            test_cases.append(TestCase(
                name=f"{tool_name}基础调用测试",
                description=f"测试{tool_name}工具的基础功能",
                tool_name=tool_name,
                parameters=self._generate_basic_parameters(tool),
                expected_type="success",
                priority="normal"
            ))
        
        # API密钥测试
        if tool_info.requires_api_key:
            test_cases.append(TestCase(
                name="API密钥配置检查",
                description="验证所需的API密钥是否正确配置",
                tool_name="config_check",
                parameters={"api_keys": tool_info.api_requirements},
                expected_type="success",
                priority="high"
            ))
        
        return test_cases
    
    def _generate_basic_parameters(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """为工具生成基础参数"""
        # 根据工具描述推断参数
        tool_name = tool.get("name", "").lower()
        
        if "search" in tool_name:
            return {"query": "test"}
        elif "get" in tool_name:
            return {"id": "test"}
        elif "create" in tool_name:
            return {"name": "test"}
        else:
            return {}

# 全局测试生成器实例
_test_generator_instance = None

def get_test_generator() -> TestGeneratorAgent:
    """获取全局测试生成器实例"""
    global _test_generator_instance
    if _test_generator_instance is None:
        _test_generator_instance = TestGeneratorAgent()
    return _test_generator_instance
