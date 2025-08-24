#!/usr/bin/env python3
"""
Debug 脚本 - 调试解析过程
"""

import sys
from pathlib import Path
import pandas as pd

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.csv_parser import MCPDataParser

def debug_parsing():
    """调试解析过程"""
    print("🔍 开始调试 mcp.csv 解析过程...")
    
    # 直接创建解析器
    csv_path = "data/mcp.csv"
    parser = MCPDataParser(csv_path)
    
    # 加载数据
    success = parser.load_data()
    if not success:
        print("❌ 数据加载失败")
        return False
        
    print(f"✅ 数据加载成功，共 {len(parser.df)} 条记录")
    
    # 调试第一行数据
    first_row = parser.df.iloc[0]
    print("\n🔍 第一行原始数据:")
    print(f"name: {first_row.get('name')}")
    print(f"extracted_mcp_config存在: {'extracted_mcp_config' in first_row}")
    
    # 调用normalize_field_names
    print("\n🔍 调用normalize_field_names:")
    normalized = parser.normalize_field_names(dict(first_row))
    print(f"install_command: {normalized.get('install_command')}")
    print(f"run_command: {normalized.get('run_command')}")
    print(f"deployment_method: {normalized.get('deployment_method')}")
    
    # 调用parse_tool
    print("\n🔍 调用parse_tool:")
    tool = parser.parse_tool(first_row)
    if tool:
        print(f"✅ 成功解析工具: {tool.name}")
        print(f"  - install_command: {tool.install_command}")
        print(f"  - run_command: {tool.run_command}")
        print(f"  - package_name: {tool.package_name}")
    else:
        print("❌ 解析工具失败")
    
    return True

if __name__ == "__main__":
    debug_parsing()
