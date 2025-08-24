#!/usr/bin/env python3
"""
手动更新数据库综合评分脚本
测试新的综合评分功能并手动更新数据库记录
"""
import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def main():
    """手动更新Context7的综合评分数据"""
    print("🚀 手动更新Context7的综合评分数据...")
    
    try:
        client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
        
        # Context7的数据
        context7_url = "https://github.com/upstash/context7"
        github_score = 89  # 从刚才的测试中获得
        success_rate = 100.0  # 基于历史2次测试记录
        test_count = 2
        
        # 计算综合评分 (1:2权重)
        total_score = int((success_rate * 1 + github_score * 2) / 3)
        
        print(f"📊 Context7综合评分计算:")
        print(f"  • GitHub评分: {github_score}/100")
        print(f"  • 测试成功率: {success_rate}%")
        print(f"  • 综合评分: ({success_rate} × 1 + {github_score} × 2) / 3 = {total_score}")
        
        # 检查记录是否存在
        existing = client.table('mcp_repository_evaluations').select('*').eq('github_url', context7_url).execute()
        
        if existing.data:
            print("✅ 找到现有记录，准备更新...")
            # 更新现有记录
            update_data = {
                'success_rate': success_rate,
                'total_score': total_score,
                'test_count': test_count,
                'last_calculated_at': datetime.now().isoformat()
            }
            
            result = client.table('mcp_repository_evaluations').update(update_data).eq('github_url', context7_url).execute()
            print(f"✅ 成功更新Context7记录: {context7_url}")
        else:
            # 插入新记录
            print("💾 创建新的评估记录...")
            insert_data = {
                'github_url': context7_url,
                'final_score': github_score,
                'sustainability_score': 84,  # 从测试中获得
                'popularity_score': 94,      # 从测试中获得
                'success_rate': success_rate,
                'total_score': total_score,
                'test_count': test_count,
                'last_evaluated_at': datetime.now().isoformat(),
                'last_calculated_at': datetime.now().isoformat()
            }
            
            result = client.table('mcp_repository_evaluations').insert(insert_data).execute()
            print(f"✅ 成功插入Context7记录: {context7_url}")
            
        # 验证更新结果
        print("\n🔍 验证更新结果:")
        updated_record = client.table('mcp_repository_evaluations').select('*').eq('github_url', context7_url).execute()
        if updated_record.data:
            record = updated_record.data[0]
            print(f"  • 仓库: {record['github_url']}")
            print(f"  • GitHub评分: {record['final_score']}")
            print(f"  • 测试成功率: {record.get('success_rate', 'N/A')}%")
            print(f"  • 综合评分: {record.get('total_score', 'N/A')}")
            print(f"  • 测试数量: {record.get('test_count', 'N/A')}")
            print(f"  • 更新时间: {record.get('last_calculated_at', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
