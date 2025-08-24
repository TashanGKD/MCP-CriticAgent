#!/usr/bin/env python3
"""
执行综合评分字段迁移脚本
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

def main():
    """执行数据库迁移"""
    print("🚀 开始执行综合评分字段迁移...")
    
    try:
        # 从环境变量读取配置
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        print(f"🔍 检查环境变量: URL={'已设置' if url else '未设置'}, KEY={'已设置' if key else '未设置'}")
        
        if not url or not key:
            print("❌ 缺少 SUPABASE_URL 或 SUPABASE_SERVICE_ROLE_KEY 环境变量")
            return False
        
        supabase: Client = create_client(url, key)
        print("✅ 数据库连接成功")
        
        # 读取迁移脚本
        with open('database/migrations/002_add_comprehensive_scoring.sql', 'r', encoding='utf-8') as f:
            migration_content = f.read()
        
        # 分解SQL语句（按分号分割）
        statements = [stmt.strip() for stmt in migration_content.split(';') 
                     if stmt.strip() and not stmt.strip().startswith('--')]
        
        print(f"📋 准备执行 {len(statements)} 个数据库语句")
        
        for i, statement in enumerate(statements, 1):
            print(f"[{i}/{len(statements)}] 执行: {statement[:50]}...")
            try:
                # 使用 RPC 执行 SQL  
                result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                print(f"✅ 语句 {i} 执行成功")
            except Exception as stmt_error:
                print(f"⚠️ 语句 {i} 执行警告: {stmt_error}")
                # 继续执行下一条语句，因为可能是字段已存在等非致命错误
        
        print("🎉 综合评分字段迁移完成！")
        
        # 验证迁移结果
        verify_migration(supabase)
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_migration(supabase: Client):
    """验证迁移是否成功"""
    print("\n🔍 验证迁移结果...")
    
    try:
        # 查询表结构
        query = """
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'mcp_repository_evaluations'
        ORDER BY ordinal_position;
        """
        
        result = supabase.rpc('exec_sql', {'sql': query}).execute()
        
        if result.data:
            print("📋 mcp_repository_evaluations 表结构:")
            for row in result.data:
                nullable = "可空" if row['is_nullable'] == 'YES' else "非空"
                print(f"  - {row['column_name']}: {row['data_type']} ({nullable})")
            
            # 检查新字段是否存在
            column_names = [row['column_name'] for row in result.data]
            new_fields = ['success_rate', 'total_score', 'test_count', 'last_calculated_at']
            
            missing_fields = [field for field in new_fields if field not in column_names]
            if missing_fields:
                print(f"⚠️ 缺少字段: {missing_fields}")
                return False
            else:
                print("✅ 所有新字段已成功添加")
                return True
        else:
            print("❌ 无法查询表结构")
            return False
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
