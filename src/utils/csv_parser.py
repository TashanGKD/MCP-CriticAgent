#!/usr/bin/env python3
"""
CSV数据解析器

从data/mcp.csv解析MCP工具信息，提供结构化的数据访问接口

作者: AI Assistant
日期: 2025-08-15
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import re
from dataclasses import dataclass
from rich.console import Console

console = Console()

@dataclass
class MCPToolInfo:
    """MCP工具信息数据类"""
    name: str
    url: str
    author: str
    github_url: str
    description: str
    category: str
    package_name: Optional[str] = None
    requires_api_key: bool = False
    install_command: Optional[str] = None
    run_command: Optional[str] = None
    api_requirements: List[str] = None
    
    def __post_init__(self):
        if self.api_requirements is None:
            self.api_requirements = []

class MCPDataParser:
    """MCP数据解析器"""
    
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.df = None
        self.tools_cache = {}
        
    def load_data(self) -> bool:
        """加载CSV数据"""
        try:
            if not self.csv_path.exists():
                console.print(f"[red]❌ CSV文件不存在: {self.csv_path}[/red]")
                return False
            
            console.print(f"[blue]📊 加载MCP数据: {self.csv_path}[/blue]")
            self.df = pd.read_csv(self.csv_path)
            console.print(f"[green]✅ 成功加载 {len(self.df)} 条MCP工具记录[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ 加载CSV数据失败: {e}[/red]")
            return False
    
    def extract_package_name(self, mcp_config: str) -> Optional[str]:
        """从MCP配置中提取包名（优先使用run_command）"""
        if not mcp_config or pd.isna(mcp_config):
            return None
            
        try:
            # 尝试解析JSON配置
            config_data = json.loads(mcp_config)
            
            # 优先检查run_command（这是实际执行命令）
            run_cmd = config_data.get('run_command', '')
            if 'npx -y' in run_cmd:
                match = re.search(r'npx -y ([^\s]+)', run_cmd)
                if match:
                    return match.group(1)
            
            # 检查cline_config中的args
            cline_config = config_data.get('cline_config', {})
            if isinstance(cline_config, dict):
                args = cline_config.get('args', [])
                if isinstance(args, list) and len(args) >= 2 and args[0] == '-y':
                    return args[1]
            
            # 最后检查install_command（可能是安装器而非实际包）
            install_cmd = config_data.get('install_command', '')
            if 'npx -y' in install_cmd and '@smithery/cli' not in install_cmd:
                # 避免Smithery安装器被误认为是包名
                match = re.search(r'npx -y ([^\s]+)', install_cmd)
                if match:
                    return match.group(1)
                    
        except (json.JSONDecodeError, KeyError, AttributeError):
            pass
        
        return None
    
    def parse_tool(self, row) -> Optional[MCPToolInfo]:
        """解析单个工具信息"""
        try:
            # 基础信息
            name = str(row.get('name', '')).strip()
            if not name or name == 'nan':
                return None
                
            url = str(row.get('url', '')).strip()
            author = str(row.get('author', '')).strip()
            github_url = str(row.get('github_url', '')).strip()
            description = str(row.get('description', '')).strip()
            category = str(row.get('type', '其他')).strip()
            
            # 解析包名
            mcp_config = str(row.get('extracted_mcp_config', ''))
            package_name = self.extract_package_name(mcp_config)
            
            # 解析API密钥需求
            requires_api_key = False
            api_requirements = []
            
            api_req_str = str(row.get('extracted_api_requirements', ''))
            if api_req_str and api_req_str != 'nan':
                try:
                    api_data = json.loads(api_req_str)
                    if isinstance(api_data, dict):
                        required_keys = api_data.get('required_keys', [])
                        if required_keys:
                            requires_api_key = True
                            api_requirements = required_keys
                except (json.JSONDecodeError, KeyError):
                    pass
            
            # 提取安装和运行命令
            install_command = None
            run_command = None
            
            if mcp_config and mcp_config != 'nan':
                try:
                    config_data = json.loads(mcp_config)
                    install_command = config_data.get('install_command')
                    run_command = config_data.get('run_command')
                except (json.JSONDecodeError, KeyError):
                    pass
            
            return MCPToolInfo(
                name=name,
                url=url,
                author=author,
                github_url=github_url,
                description=description,
                category=category,
                package_name=package_name,
                requires_api_key=requires_api_key,
                install_command=install_command,
                run_command=run_command,
                api_requirements=api_requirements
            )
            
        except Exception as e:
            console.print(f"[yellow]⚠️ 解析工具信息失败: {e}[/yellow]")
            return None
    
    def get_all_tools(self) -> List[MCPToolInfo]:
        """获取所有有效的MCP工具"""
        if self.df is None:
            if not self.load_data():
                return []
        
        tools = []
        for _, row in self.df.iterrows():
            tool = self.parse_tool(row)
            if tool and tool.package_name:  # 只返回有包名的工具
                tools.append(tool)
        
        console.print(f"[green]📦 解析出 {len(tools)} 个可部署的MCP工具[/green]")
        return tools
    
    def find_tool_by_url(self, url: str) -> Optional[MCPToolInfo]:
        """根据URL查找工具"""
        if self.df is None:
            if not self.load_data():
                return None
        
        # 直接匹配URL
        matches = self.df[self.df['url'] == url]
        if not matches.empty:
            return self.parse_tool(matches.iloc[0])
        
        # 模糊匹配URL中的关键部分
        url_parts = url.split('/')
        if len(url_parts) > 0:
            key_part = url_parts[-1]  # 取URL最后一部分
            matches = self.df[self.df['url'].str.contains(key_part, na=False)]
            if not matches.empty:
                return self.parse_tool(matches.iloc[0])
        
        return None
    
    def find_tool_by_package(self, package_name: str) -> Optional[MCPToolInfo]:
        """根据包名查找工具"""
        tools = self.get_all_tools()
        for tool in tools:
            if tool.package_name == package_name:
                return tool
        return None
    
    def get_tools_by_category(self, category: str) -> List[MCPToolInfo]:
        """根据类别获取工具"""
        tools = self.get_all_tools()
        return [tool for tool in tools if category.lower() in tool.category.lower()]
    
    def search_tools(self, query: str) -> List[MCPToolInfo]:
        """搜索工具"""
        tools = self.get_all_tools()
        query_lower = query.lower()
        
        results = []
        for tool in tools:
            if (query_lower in tool.name.lower() or 
                query_lower in tool.description.lower() or 
                query_lower in tool.author.lower()):
                results.append(tool)
        
        return results

# 全局解析器实例
_parser_instance = None

def get_mcp_parser() -> MCPDataParser:
    """获取全局MCP解析器实例"""
    global _parser_instance
    if _parser_instance is None:
        csv_path = Path(__file__).parent.parent.parent / "data" / "mcp.csv"
        _parser_instance = MCPDataParser(str(csv_path))
    return _parser_instance
