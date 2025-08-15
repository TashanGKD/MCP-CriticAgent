#!/usr/bin/env python3
"""
测试智能代理是否能真正调用大模型生成测试用例
"""

import sys
import asyncio
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

@dataclass
class MockToolInfo:
    """模拟工具信息"""
    name: str = "Context7 MCP"
    author: str = "upstash"
    description: str = "用于Context7的MCP服务器，提供最新、版本特定的库文档和代码示例"
    category: str = "开发工具"
    package_name: str = "@upstash/context7-mcp"
    requires_api_key: bool = False
    api_requirements: List[str] = None
    
    def __post_init__(self):
        if self.api_requirements is None:
            self.api_requirements = []

async def test_real_llm_generation():
    """测试真实的大模型调用生成测试用例"""
    print("🤖 测试智能代理大模型调用...")
    
    try:
        # 导入代理
        from src.agents.test_agent import get_test_generator
        from src.agents.validation_agent import get_validation_agent
        
        # 获取代理实例
        test_generator = get_test_generator()
        validation_agent = get_validation_agent()
        
        print(f"✅ 代理初始化状态:")
        print(f"  测试生成代理: {'✅' if test_generator.agent else '❌'}")
        print(f"  验证代理: {'✅' if validation_agent.agent else '❌'}")
        
        if not test_generator.agent:
            print("❌ 测试生成代理未正确初始化")
            return False
            
        # 准备测试数据
        tool_info = MockToolInfo()
        available_tools = [
            {"name": "resolve-library-id", "description": "解析包名到库ID"},
            {"name": "get-library-docs", "description": "获取库文档"}
        ]
        
        print("\n🎯 开始调用大模型生成测试用例...")
        print(f"工具信息: {tool_info.name}")
        print(f"可用工具: {[t['name'] for t in available_tools]}")
        
        # 这里会实际调用大模型
        test_cases = test_generator.generate_test_cases(tool_info, available_tools)
        
        print(f"\n📊 生成结果:")
        print(f"  生成的测试用例数量: {len(test_cases)}")
        
        if test_cases:
            print("\n📝 生成的测试用例详情:")
            for i, case in enumerate(test_cases, 1):
                print(f"  {i}. {case.name}")
                print(f"     描述: {case.description}")
                print(f"     工具: {case.tool_name}")
                print(f"     参数: {case.parameters}")
                print(f"     期望: {case.expected_type}")
                print(f"     优先级: {case.priority}")
                print()
            
            print("✅ 大模型成功生成了测试用例！")
            return True
        else:
            print("⚠️ 大模型没有生成任何测试用例")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"详细错误:\n{traceback.format_exc()}")
        return False

def main():
    """主函数"""
    print("🚀 开始测试智能代理的大模型调用能力...\n")
    
    result = asyncio.run(test_real_llm_generation())
    
    print("\n" + "="*50)
    if result:
        print("🎉 测试成功！智能代理能够正常调用大模型生成测试用例")
        print("💡 这证明智能测试功能已经正常工作")
    else:
        print("❌ 测试失败！智能代理无法正常生成测试用例")
        print("💡 需要检查模型配置或网络连接")
    
    return 0 if result else 1

if __name__ == "__main__":
    exit(main())
