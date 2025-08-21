#!/usr/bin/env python3
"""
数据库数据验证脚本

验证测试数据是否成功存储到Supabase数据库
"""

import sys
from pathlib import Path

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.supabase_connector import SupabaseConnector

def main():
    """验证数据库中的数据"""
    print("🔍 验证数据库中的测试数据...")
    
    try:
        # 创建连接器
        connector = SupabaseConnector()
        print("✅ 数据库连接成功")
        
        # 查询工具数据
        tools_result = connector.client.table('mcp_tools').select('*').execute()
        tools_count = len(tools_result.data)
        print(f"📊 MCP工具表记录数: {tools_count}")
        
        if tools_count > 0:
            latest_tool = tools_result.data[-1]
            print(f"📦 最新工具: {latest_tool.get('name', 'N/A')}")
            print(f"👤 作者: {latest_tool.get('author', 'N/A')}")
            print(f"📂 类别: {latest_tool.get('category', 'N/A')}")
        
        # 查询测试报告
        reports_result = connector.client.table('test_reports').select('*').execute()
        reports_count = len(reports_result.data)
        print(f"📊 测试报告表记录数: {reports_count}")
        
        if reports_count > 0:
            latest_report = reports_result.data[-1]
            print(f"🆔 最新报告ID: {latest_report.get('test_run_id', 'N/A')}")
            print(f"✅ 测试成功数: {latest_report.get('tools_successful', 0)}/{latest_report.get('tools_tested', 0)}")
            print(f"⏱️ 执行时间: {latest_report.get('execution_time_seconds', 0):.2f}秒")
        
        # 查询测试执行详情
        executions_result = connector.client.table('test_executions').select('*').execute()
        executions_count = len(executions_result.data)
        print(f"📊 测试执行表记录数: {executions_count}")
        
        # 查询质量指标
        quality_result = connector.client.table('quality_metrics').select('*').execute()
        quality_count = len(quality_result.data)
        print(f"📊 质量指标表记录数: {quality_count}")
        
        if quality_count > 0:
            latest_quality = quality_result.data[-1]
            print(f"🎯 整体质量评分: {latest_quality.get('overall_quality_score', 0)}")
            print(f"📈 成功率: {latest_quality.get('success_rate', 0)}")
        
        print("\n🎉 数据库验证完成！")
        print(f"📈 总数据条目: {tools_count + reports_count + executions_count + quality_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
