#!/usr/bin/env python3
"""
简化的数据库保存测试
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.supabase_connector import SupabaseConnector

def test_direct_db_save():
    """直接测试数据库保存功能"""
    print("🧪 直接测试数据库保存...")
    
    try:
        # 创建连接器
        connector = SupabaseConnector()
        print("✅ 数据库连接成功")
        
        # 插入一个测试工具
        tool_data = {
            'name': 'Direct Test Tool',
            'author': 'Test System',
            'github_url': 'https://github.com/test/direct-test',
            'package_name': 'direct-test-tool',
            'category': 'testing',
            'description': 'A tool to test direct database insertion',
            'version': '1.0.0',
            'requires_api_key': False,
            'language': 'Python',
            'license': 'MIT',
            'stars': 50
        }
        
        result = connector.client.table('mcp_tools').insert(tool_data).execute()
        tool_id = result.data[0]['id']
        print(f"✅ 工具插入成功，ID: {tool_id}")
        
        # 插入一个测试报告
        report_data = {
            'test_run_id': 'direct-test-123',
            'timestamp': datetime.now().isoformat(),
            'total_tools': 1,
            'tools_tested': 1,
            'tools_successful': 1,
            'overall_status': 'SUCCESS',
            'execution_time_seconds': 2.5,
            'python_version': '3.12.0',
            'platform': 'Windows',
            'test_environment': 'direct-test'
        }
        
        result = connector.client.table('test_reports').insert(report_data).execute()
        report_id = result.data[0]['id']
        print(f"✅ 报告插入成功，ID: {report_id}")
        
        # 插入一个测试执行记录
        execution_data = {
            'report_id': report_id,
            'tool_id': tool_id,
            'status': 'SUCCESS',
            'execution_time_seconds': 1.5,
            'memory_usage_mb': 30.0,
            'test_data': {'test_type': 'basic', 'result': 'passed'}
        }
        
        result = connector.client.table('test_executions').insert(execution_data).execute()
        execution_id = result.data[0]['id']
        print(f"✅ 执行记录插入成功，ID: {execution_id}")
        
        # 验证数据
        tools_count = len(connector.client.table('mcp_tools').select('*').execute().data)
        reports_count = len(connector.client.table('test_reports').select('*').execute().data)
        executions_count = len(connector.client.table('test_executions').select('*').execute().data)
        
        print(f"📊 数据验证:")
        print(f"  🛠️ 工具数: {tools_count}")
        print(f"  📄 报告数: {reports_count}")
        print(f"  ⚡ 执行记录数: {executions_count}")
        
        print("🎉 直接数据库测试成功！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_direct_db_save()
    sys.exit(0 if success else 1)
