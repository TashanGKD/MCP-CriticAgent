#!/usr/bin/env python3
"""
Supabase 设置验证器

用途：验证 Supabase 配置和数据库连接是否正确配置
运行：uv run python src/tools/setup_validator.py
"""

import os
import sys
from pathlib import Path

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent.parent))

# 加载 .env 文件
def load_env_file():
    """加载 .env 文件"""
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print(f"✅ 已加载 .env 文件: {env_path}")
    else:
        print(f"⚠️ 未找到 .env 文件: {env_path}")

# 在导入之前加载环境变量
load_env_file()

def validate_environment():
    """验证环境变量配置"""
    print("🔍 检查环境变量配置...")
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # 安全显示（只显示前10个字符）
            safe_value = value[:10] + "..." if len(value) > 10 else value
            print(f"  ✅ {var}: {safe_value}")
    
    if missing_vars:
        print(f"  ❌ 缺失环境变量: {', '.join(missing_vars)}")
        print(f"  💡 请检查 .env 文件是否配置正确")
        return False
    
    return True

def validate_supabase_connection():
    """验证Supabase连接"""
    print("\n🔗 测试Supabase连接...")
    
    try:
        from core.supabase_connector import SupabaseConnector
        
        connector = SupabaseConnector()
        
        # 测试连接
        response = connector.client.table('mcp_tools').select('count').execute()
        print(f"  ✅ 连接成功! 数据库可访问")
        return True
        
    except ImportError as e:
        print(f"  ❌ 导入错误: {e}")
        print(f"  💡 请确保已安装 supabase 依赖: uv add supabase")
        return False
    except Exception as e:
        print(f"  ❌ 连接失败: {e}")
        print(f"  💡 请检查 URL 和密钥是否正确")
        return False

def validate_database_schema():
    """验证数据库表结构"""
    print("\n🗄️ 检查数据库表结构...")
    
    try:
        from core.supabase_connector import SupabaseConnector
        
        connector = SupabaseConnector()
        
        expected_tables = [
            'mcp_tools',
            'test_reports', 
            'test_executions',
            'quality_metrics',
            'performance_analysis',
            'deployment_info',
            'test_metadata'
        ]
        
        existing_tables = []
        missing_tables = []
        
        for table in expected_tables:
            try:
                response = connector.client.table(table).select('count').limit(1).execute()
                existing_tables.append(table)
                print(f"  ✅ 表 {table} 存在")
            except Exception:
                missing_tables.append(table)
                print(f"  ❌ 表 {table} 不存在")
        
        if missing_tables:
            print(f"\n  💡 需要初始化数据库: uv run python src/tools/db_migrate.py init")
            return False
        
        print(f"\n  🎉 所有表都已正确创建!")
        return True
        
    except Exception as e:
        print(f"  ❌ 检查失败: {e}")
        return False

def main():
    """主验证流程"""
    print("🚀 Supabase 配置验证开始...\n")
    
    steps = [
        ("环境变量配置", validate_environment),
        ("Supabase连接", validate_supabase_connection),  
        ("数据库表结构", validate_database_schema)
    ]
    
    results = []
    for step_name, step_func in steps:
        try:
            result = step_func()
            results.append((step_name, result))
        except Exception as e:
            print(f"❌ {step_name} 验证失败: {e}")
            results.append((step_name, False))
    
    # 汇总结果
    print("\n" + "="*50)
    print("📊 验证结果汇总:")
    
    all_passed = True
    for step_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {status} {step_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 所有验证都通过! 系统已准备就绪")
        print("💡 现在可以运行: uv run python src/main.py")
    else:
        print("⚠️  部分验证失败，请按照提示修复问题")
        print("📖 详细设置指南: docs/SUPABASE_SETUP.md")

if __name__ == "__main__":
    main()
