#!/usr/bin/env python3
"""
LobeHub 数据库迁移脚本
执行数据库迁移以添加 LobeHub 评分字段
"""
import os
from supabase import create_client, Client

def main():
    """执行数据库迁移"""
    print("🚀 开始执行 LobeHub 评分字段迁移...")
    
    try:
        # 直接从系统环境变量读取
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        print(f"🔍 检查环境变量: URL={'已设置' if url else '未设置'}, KEY={'已设置' if key else '未设置'}")
        
        if not url or not key:
            print("❌ 缺少 SUPABASE_URL 或 SUPABASE_SERVICE_ROLE_KEY 环境变量")
            return
            
        supabase: Client = create_client(url, key)
        print("✅ 数据库连接成功")
        
        # 读取迁移脚本
        with open('database/migrations/add_lobehub_ratings.sql', 'r', encoding='utf-8') as f:
            migration_content = f.read()
        
        # 分解SQL语句（按分号分割）
        statements = [stmt.strip() for stmt in migration_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        
        print(f"📋 准备执行 {len(statements)} 个数据库语句")
        
        for i, statement in enumerate(statements, 1):
            print(f"[{i}/{len(statements)}] 执行: {statement[:50]}...")
            
            # 使用 RPC 执行 SQL
            result = supabase.rpc('eval', {'query': statement}).execute()
            print(f"✅ 语句 {i} 执行成功")
        
        print("🎉 LobeHub 评分字段迁移完成！")
        
        # 验证迁移结果
        verify_migration(supabase)
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()

def verify_migration(supabase: Client):
    """验证迁移是否成功"""
    print("\n🔍 验证迁移结果...")
    
    try:
        # 查询表结构
        query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'mcp_test_results'
        AND column_name LIKE 'lobehub_%'
        ORDER BY column_name;
        """
        
        result = supabase.rpc('eval', {'query': query}).execute()
        
        if result.data:
            print("✅ 发现 LobeHub 评分字段:")
            for row in result.data:
                nullable = "可空" if row['is_nullable'] == 'YES' else "非空"
                print(f"  - {row['column_name']}: {row['data_type']} ({nullable})")
        else:
            print("❌ 没有找到 LobeHub 评分字段")
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")

if __name__ == "__main__":
    main()
