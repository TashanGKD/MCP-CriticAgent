#!/usr/bin/env python3
"""
简单的MCP工具选择脚本
直接处理CSV文件，选择不需要API key的工具
"""

import pandas as pd
import json
import os
import sys

def main():
    """选择简单可靠、不需要API key的MCP工具"""
    test_count = int(os.getenv('TEST_COUNT', 20))
    
    # 读取CSV文件
    csv_path = 'data/mcp.csv'
    try:
        df = pd.read_csv(csv_path)
        print(f"📦 总工具数: {len(df)}")
    except Exception as e:
        print(f"❌ 读取CSV文件失败: {e}")
        sys.exit(1)
    
    # 筛选条件
    simple_tools = []
    
    # 排除的浏览器相关关键词
    browser_keywords = [
        'playwright', 'browser', 'chrome', 'firefox', 'selenium', 
        'webdriver', 'screenshot', 'automation', 'web', 'puppeteer',
        'cypress', 'headless', 'dom', 'html', 'css', 'javascript'
    ]
    
    for _, row in df.iterrows():
        # 必须有包名
        if pd.isna(row.get('extracted_mcp_config')):
            continue
            
        try:
            # 解析MCP配置获取包名
            mcp_config = row.get('extracted_mcp_config', '{}')
            if isinstance(mcp_config, str) and mcp_config.strip():
                config_data = json.loads(mcp_config)
                run_command = config_data.get('run_command', '')
                
                # 提取包名
                package_name = None
                if 'npx' in run_command and '@' in run_command:
                    # npx -y @upstash/context7-mcp
                    parts = run_command.split()
                    for part in parts:
                        if '@' in part and '/' in part:
                            package_name = part
                            break
                
                if not package_name:
                    continue
                
                # 检查是否为浏览器相关工具
                name = str(row.get('name', 'Unknown')).lower()
                description = str(row.get('description', '')).lower()
                package_lower = package_name.lower()
                
                is_browser_related = any(keyword in name or keyword in description or keyword in package_lower 
                                       for keyword in browser_keywords)
                
                if is_browser_related:
                    continue  # 排除浏览器相关工具
                
                # 检查是否需要API key
                requires_api = row.get('extracted_requires_api_key', False)
                if requires_api in [True, 'True', 'true', 1, '1']:
                    continue
                
                # 基础信息
                name = row.get('name', 'Unknown')
                author = row.get('author', 'Unknown')
                stars = row.get('star_count', 0)
                quality = row.get('evaluate', 'N/A')
                
                # 计算可靠性得分
                reliability_score = 0
                if isinstance(stars, (int, float)) and stars > 0:
                    reliability_score += min(stars, 1000) * 0.001
                
                if quality == '优质':
                    reliability_score += 3
                elif quality == '良好':
                    reliability_score += 2
                elif quality and quality != 'N/A':
                    reliability_score += 1
                
                if 'npx' in run_command:
                    reliability_score += 1
                
                simple_tools.append({
                    'package': package_name,
                    'name': str(name)[:50],  # 限制长度
                    'stars': int(stars) if isinstance(stars, (int, float)) else 0,
                    'author': str(author)[:30],  # 限制长度
                    'quality': str(quality) if quality else 'N/A',
                    'reliability_score': round(reliability_score, 2)
                })
                
        except Exception as e:
            continue
    
    print(f"🔓 筛选出不需要API key的工具: {len(simple_tools)}")
    
    # 按可靠性排序
    simple_tools.sort(key=lambda x: x['reliability_score'], reverse=True)
    
    # 限制数量
    test_tools = simple_tools[:test_count]
    
    print(f"📋 最终测试工具数: {len(test_tools)}")
    
    # 统计质量分布
    quality_dist = {}
    for tool in test_tools:
        quality = tool['quality']
        quality_dist[quality] = quality_dist.get(quality, 0) + 1
    
    print(f"📊 质量分布: {quality_dist}")
    
    # 输出为GitHub Actions格式
    print(f"targets={json.dumps(test_tools)}")
    print(f"total={len(test_tools)}")
    
    # 显示前5个工具
    print("\n🔧 选定的前5个工具:")
    for i, tool in enumerate(test_tools[:5]):
        print(f"{i+1}. {tool['name']} ({tool['package']}) - {tool['quality']} - 得分:{tool['reliability_score']}")
    
    return len(test_tools)

if __name__ == "__main__":
    try:
        count = main()
        sys.exit(0)
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)
