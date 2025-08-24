#!/usr/bin/env python3
"""
本地并行压力测试脚本
验证工作流在本地是否正常工作
"""

import subprocess
import json
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

def test_single_tool(tool_info):
    """测试单个MCP工具 - 强制执行完整智能测试"""
    package = tool_info['package']
    name = tool_info['name']
    quality = tool_info.get('quality', 'N/A')
    stars = tool_info.get('stars', 0)
    
    print(f"🧪 开始完整智能测试: {name} ({package}) - {quality}")
    
    start_time = time.time()
    
    try:
        # 检查必要的环境变量配置
        has_ai_config = bool(os.getenv('OPENAI_API_KEY') or os.getenv('DASHSCOPE_API_KEY'))
        has_db_config = bool(os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
        
        if not has_ai_config:
            print(f"  ❌ 未配置AI API密钥，跳过测试")
            return {
                'package': package,
                'name': name,
                'quality': quality,
                'stars': stars,
                'status': 'skipped',
                'duration': 0.0,
                'has_ai': False,
                'has_db': has_db_config,
                'output': '',
                'error': 'Missing AI configuration'
            }
            
        if not has_db_config:
            print(f"  ❌ 未配置数据库，跳过测试")
            return {
                'package': package,
                'name': name,
                'quality': quality,
                'stars': stars,
                'status': 'skipped',
                'duration': 0.0,
                'has_ai': has_ai_config,
                'has_db': False,
                'output': '',
                'error': 'Missing database configuration'
            }
        
        print(f"  ✅ AI和数据库配置完整，执行完整智能测试")
        
        # 构建完整智能测试命令（强制启用所有功能）
        cmd = [
            'uv', 'run', 'python', '-m', 'src.main',
            'test-package', package,
            '--timeout', '120',
            '--verbose'
            # 不添加 --no-smart 和 --no-db-export，使用默认启用
        ]
        
        # 执行完整智能测试
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=150,
            cwd=os.getcwd()
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ 完整智能测试成功: {name} ({duration:.1f}s)")
            return {
                'package': package,
                'name': name,
                'quality': quality,
                'stars': stars,
                'status': 'success',
                'duration': round(duration, 1),
                'has_ai': True,
                'has_db': True,
                'output': result.stdout[-1000:] if result.stdout else '',
                'error': ''
            }
        else:
            print(f"❌ 完整智能测试失败: {name} ({duration:.1f}s)")
            return {
                'package': package,
                'name': name,
                'quality': quality,
                'stars': stars,
                'status': 'failed',
                'duration': round(duration, 1),
                'has_ai': True,
                'has_db': True,
                'output': result.stdout[-1000:] if result.stdout else '',
                'error': result.stderr[-1000:] if result.stderr else ''
            }
            
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"⏰ 测试超时: {name} ({duration:.1f}s)")
        return {
            'package': package,
            'name': name,
            'status': 'timeout',
            'duration': round(duration, 1),
            'output': '',
            'error': 'Test timeout'
        }
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"💥 测试异常: {name} - {str(e)}")
        return {
            'package': package,
            'name': name,
            'status': 'error',
            'duration': round(duration, 1),
            'output': '',
            'error': str(e)
        }

def main():
    """主函数"""
    print("🚀 开始本地并行压力测试...")
    
    # 1. 生成测试目标
    print("\n📋 生成测试目标...")
    
    try:
        # 选择5个工具进行快速测试
        env = os.environ.copy()
        env['TEST_COUNT'] = '5'
        
        result = subprocess.run(
            ['uv', 'run', 'python', 'scripts/simple_tool_selector.py'],
            capture_output=True,
            text=True,
            env=env
        )
        
        if result.returncode != 0:
            print(f"❌ 工具选择失败: {result.stderr}")
            return
            
        # 解析输出
        output_lines = result.stdout.strip().split('\n')
        targets_line = None
        total_line = None
        
        for line in output_lines:
            if line.startswith('targets='):
                targets_line = line
            elif line.startswith('total='):
                total_line = line
                
        if not targets_line or not total_line:
            print(f"❌ 无法解析工具选择结果")
            return
            
        targets_json = targets_line.split('=', 1)[1]
        total = int(total_line.split('=', 1)[1])
        
        targets = json.loads(targets_json)
        
        print(f"✅ 成功选择了 {total} 个测试目标")
        
    except Exception as e:
        print(f"❌ 生成测试目标失败: {e}")
        return
    
    # 2. 并行执行测试
    print("\n🔥 开始并行测试...")
    
    results = []
    max_workers = 3  # 限制并行数，避免系统负载过高
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(test_single_tool, target): target for target in targets}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                
                # 实时显示结果
                status_icon = {
                    'success': '✅',
                    'failed': '❌',
                    'timeout': '⏰',
                    'error': '💥'
                }.get(result['status'], '❓')
                
                print(f"{status_icon} {result['name']} - {result['status']} ({result['duration']}s)")
                
            except Exception as e:
                print(f"💥 任务执行异常: {e}")
    
    # 3. 汇总结果
    print("\n📊 测试结果汇总:")
    
    total_tests = len(results)
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = sum(1 for r in results if r['status'] == 'failed')
    timeout_count = sum(1 for r in results if r['status'] == 'timeout')
    error_count = sum(1 for r in results if r['status'] == 'error')
    
    total_duration = sum(r['duration'] for r in results)
    avg_duration = total_duration / total_tests if total_tests > 0 else 0
    
    success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
    
    print(f"🎯 总数: {total_tests}")
    print(f"✅ 成功: {success_count} ({success_rate:.1f}%)")
    print(f"❌ 失败: {failed_count}")
    print(f"⏰ 超时: {timeout_count}")
    print(f"💥 异常: {error_count}")
    print(f"📈 总耗时: {total_duration:.1f}s")
    print(f"⏱️ 平均耗时: {avg_duration:.1f}s")
    
    # 4. 生成详细报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total': total_tests,
            'success': success_count,
            'failed': failed_count,
            'timeout': timeout_count,
            'error': error_count,
            'success_rate': round(success_rate, 1),
            'total_duration': round(total_duration, 1),
            'avg_duration': round(avg_duration, 1)
        },
        'results': results
    }
    
    # 保存报告
    os.makedirs('logs', exist_ok=True)
    report_file = f"logs/parallel_stress_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 详细报告已保存: {report_file}")
    
    if success_count > 0:
        print(f"\n✅ 成功的工具:")
        for result in results:
            if result['status'] == 'success':
                print(f"  - {result['name']} ({result['package']})")
    
    if failed_count + timeout_count + error_count > 0:
        print(f"\n❌ 失败的工具:")
        for result in results:
            if result['status'] != 'success':
                print(f"  - {result['name']} ({result['package']}) - {result['status']}")
    
    print(f"\n🎉 并行压力测试完成！")

if __name__ == "__main__":
    main()
