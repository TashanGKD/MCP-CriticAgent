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
from dataclasses import dataclass, field
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
    deployment_method: str
    category: str = ""
    package_name: Optional[str] = None
    requires_api_key: bool = False
    install_command: Optional[str] = None
    run_command: Optional[str] = None
    api_requirements: List[str] = field(default_factory=list)
    final_score: Optional[int] = None
    sustainability_score: Optional[int] = None
    popularity_score: Optional[int] = None
    
    # LobeHub评分信息
    lobehub_url: Optional[str] = None
    lobehub_evaluate: Optional[str] = None      # 优质/良好/欠佳
    lobehub_score: Optional[float] = None       # 具体评分数字
    lobehub_star_count: Optional[int] = None    # GitHub星标数
    lobehub_fork_count: Optional[int] = None    # GitHub分支数

class MCPDataParser:
    """MCP数据解析器"""
    
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.df = None
        self.tools_cache = {}
    
    def normalize_field_names(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        将mcp.csv的字段名标准化为期望的字段名
        这样可以统一处理两种CSV格式，消除特殊情况
        """
        import json
        
        # mcp.csv -> expected field mapping
        field_mapping = {
            'extracted_deployment_methods': 'deployment_method', 
            'extracted_requires_api_key': 'requires_api_key',
            'extracted_use_cases': 'use_cases'
        }
        
        normalized = {}
        for key, value in row.items():
            # Use mapping if exists, otherwise keep original key
            normalized_key = field_mapping.get(key, key)
            normalized[normalized_key] = value
            
        # Extract install_command and run_command from extracted_mcp_config
        if 'extracted_mcp_config' in row and pd.notna(row['extracted_mcp_config']):
            try:
                config_str = str(row['extracted_mcp_config']).strip()
                if config_str:
                    config = json.loads(config_str)
                    if 'install_command' in config:
                        normalized['install_command'] = config['install_command']
                    if 'run_command' in config:
                        normalized['run_command'] = config['run_command']
            except (json.JSONDecodeError, Exception) as e:
                console.print(f"[yellow]⚠️ 解析mcp_config失败: {e}[/yellow]")
        
        # Handle special cases for deployment_method 
        if 'deployment_method' in normalized and pd.notna(normalized['deployment_method']):
            # Extract the first deployment method if multiple exist
            deploy_val = str(normalized['deployment_method'])
            if 'npm' in deploy_val.lower() or 'npx' in deploy_val.lower():
                normalized['deployment_method'] = 'npx'
            elif 'pip' in deploy_val.lower():
                normalized['deployment_method'] = 'pip'
            else:
                normalized['deployment_method'] = 'npx'  # default
        else:
            normalized['deployment_method'] = 'npx'  # default for missing values
            
        # Handle API key requirements
        if 'requires_api_key' in normalized:
            api_key_val = str(normalized['requires_api_key']).lower()
            normalized['requires_api_key'] = api_key_val in ['true', '1', 'yes', 'required']
        else:
            normalized['requires_api_key'] = False
            
        return normalized
        
    def load_data(self) -> bool:
        """加载CSV数据"""
        try:
            if not self.csv_path.exists():
                console.print(f"[red]❌ CSV文件不存在: {self.csv_path}[/red]")
                return False
            
            console.print(f"[blue]📊 加载MCP数据: {self.csv_path}[/blue]")
            # 直接使用pandas读取CSV，更加稳定可靠
            self.df = pd.read_csv(self.csv_path, encoding='utf-8')
            console.print(f"[green]✅ 成功加载 {len(self.df)} 条MCP工具记录[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ 加载CSV数据失败: {e}[/red]")
            return False
    
    def extract_package_name(self, install_command: str, run_command: str, deployment_method: str) -> Optional[str]:
        """从命令中提取包名"""
        if deployment_method not in ['npm', 'npx']:
            return None

        command = run_command if pd.notna(run_command) and run_command else install_command
        if pd.isna(command) or not command:
            return None

        # Regex to find package names, including scoped packages
        match = re.search(r'(?:npx -y |@)[^\s@/]+(?:/[^\s@]+)?', command)
        if match:
            return match.group(0).replace('npx -y ', '').strip()
        
        # Fallback for simple npm install commands
        match = re.search(r'npm install -g ([^\s]+)', command)
        if match:
            return match.group(1).strip()

        return None

    def parse_tool(self, row) -> Optional[MCPToolInfo]:
        """解析单个工具信息"""
        try:
            # 标准化字段名
            normalized_row = self.normalize_field_names(dict(row))
            
            name = str(normalized_row.get('name', '')).strip()
            if not name or pd.isna(name):
                return None

            install_command = str(normalized_row.get('install_command', '')).strip()
            package_name = self.extract_package_name(
                install_command, 
                normalized_row.get('run_command'),
                normalized_row.get('deployment_method')
            )

            return MCPToolInfo(
                name=name,
                url=str(normalized_row.get('url', '')).strip(),
                author=str(normalized_row.get('author', '')).strip(),
                github_url=str(normalized_row.get('github_url', '')).strip(),
                description=str(normalized_row.get('description', '')).strip(),
                deployment_method=str(normalized_row.get('deployment_method', '')).strip(),
                package_name=package_name,
                requires_api_key=bool(normalized_row.get('requires_api_key')),
                install_command=install_command,
                run_command=str(normalized_row.get('run_command', '')).strip(),
                final_score=pd.to_numeric(normalized_row.get('final_score'), errors='coerce'),
                sustainability_score=pd.to_numeric(normalized_row.get('sustainability_score'), errors='coerce'),
                popularity_score=pd.to_numeric(normalized_row.get('popularity_score'), errors='coerce'),
                
                # LobeHub评分信息 
                lobehub_url=str(normalized_row.get('url', '')).strip() if pd.notna(normalized_row.get('url')) else None,
                lobehub_evaluate=str(normalized_row.get('evaluate', '')).strip() if pd.notna(normalized_row.get('evaluate')) else None,
                lobehub_score=pd.to_numeric(normalized_row.get('Unnamed: 5'), errors='coerce') if pd.notna(normalized_row.get('Unnamed: 5')) else None,
                lobehub_star_count=int(pd.to_numeric(normalized_row.get('star_count'), errors='coerce')) if pd.notna(pd.to_numeric(normalized_row.get('star_count'), errors='coerce')) else 0,
                lobehub_fork_count=int(pd.to_numeric(normalized_row.get('fork_count'), errors='coerce')) if pd.notna(pd.to_numeric(normalized_row.get('fork_count'), errors='coerce')) else 0,
            )
            
        except Exception as e:
            console.print(f"[yellow]⚠️ 解析工具信息失败: {e} for row {row}[/yellow]")
            return None
    
    def get_all_tools(self) -> List[MCPToolInfo]:
        """获取所有有效的MCP工具"""
        if self.df is None:
            if not self.load_data():
                return []
        
        tools = []
        for _, row in self.df.iterrows():
            tool = self.parse_tool(row)
            if tool:
                tools.append(tool)
        
        console.print(f"[green]📦 解析出 {len(tools)} 个可部署的MCP工具[/green]")
        return tools
    
    def find_tool_by_url(self, url: str) -> Optional[MCPToolInfo]:
        """根据URL查找工具"""
        if self.df is None:
            if not self.load_data():
                return None
        
        matches = self.df[self.df['github_url'] == url]
        if not matches.empty:
            return self.parse_tool(matches.iloc[0])
        
        return None
    
    def find_tool_by_package(self, package_name: str) -> Optional[MCPToolInfo]:
        """根据包名查找工具 - 支持模糊匹配"""
        tools = self.get_all_tools()
        
        # 1. 精确匹配
        for tool in tools:
            if tool.package_name == package_name:
                return tool
        
        # 2. 包含匹配 (去掉版本号)
        clean_package = package_name.split('@')[0]  # 移除版本号
        for tool in tools:
            if tool.package_name and clean_package in tool.package_name:
                return tool
        
        # 3. 通过install_command匹配
        for tool in tools:
            if tool.install_command and clean_package in tool.install_command:
                return tool
                
        # 4. 通过run_command匹配
        for tool in tools:
            if tool.run_command and clean_package in tool.run_command:
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
