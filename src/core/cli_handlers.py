#!/usr/bin/env python3
"""
MCP CLI 命令处理器 - 简洁版

遵循 Linus 的"好品味"原则：
- 每个命令处理器只做一件事
- 消除深度嵌套
- 统一的错误处理模式

作者: AI Assistant (Linus重构版)
日期: 2025-08-18
版本: 2.0.0 (简洁版)
"""

import time
import asyncio
from pathlib import Path
from typing import Optional, List
from rich import print as rprint

from src.core.tester import get_mcp_tester, TestConfig
from src.core.report_generator import generate_test_report
from src.utils.csv_parser import MCPToolInfo


class CLIHandler:
    """CLI命令处理器 - 统一处理模式"""
    
    def __init__(self):
        self.tester = get_mcp_tester()
    
    def test_url(self, url: str, config: TestConfig) -> bool:
        """测试URL - 主要流程"""
        try:
            # 1. 查找工具信息
            tool_info = self._find_tool_info(url)
            if not tool_info:
                return False
            
            # 2. 部署工具
            server_info = self._deploy_tool(tool_info, config)
            if not server_info:
                return False
            
            # 3. 执行测试
            success, test_results = self._run_tests(tool_info, server_info, config)
            
            # 4. 生成报告
            report_files = {}
            if config.save_report:
                report_files = self._save_report(url, tool_info, server_info, success, test_results, server_info.start_time)
            
            # 4.5. 数据库导出 (可选)
            if config.db_export:
                self._export_to_database(report_files.get('json'), report_files)
            
            # 5. 清理资源
            if config.cleanup:
                self._cleanup_server(server_info.server_id)
            
            return success
            
        except Exception as e:
            rprint(f"[red]❌ 测试过程发生错误: {e}[/red]")
            return False
    
    def test_package(self, package: str, config: TestConfig) -> bool:
        """测试包 - 统一流程"""
        try:
            # 直接部署包
            server_info = self.tester.deploy_tool(package, config.timeout)
            if not server_info:
                rprint("[red]❌ MCP工具部署失败[/red]")
                return False
            
            self._display_deployment_success(server_info, package)
            
            # 执行测试 - 统一逻辑，支持smart模式
            success, test_results = self._run_tests(None, server_info, config)
            
            # 生成报告（如果需要）
            report_files = {}
            if config.save_report:
                report_files = self._save_report(package, None, server_info, success, test_results, server_info.start_time)
            
            # 数据库导出 (如果需要)
            if config.db_export:
                self._export_to_database(report_files.get('json'), report_files)
            
            # 清理
            if config.cleanup:
                self._cleanup_server(server_info.server_id)
            
            return success
            
        except Exception as e:
            rprint(f"[red]❌ 测试过程发生错误: {e}[/red]")
            return False
    
    def list_tools(self, category: Optional[str], search: Optional[str], limit: int, show_package: bool):
        """列出工具 - 简化实现"""
        try:
            parser, _ = self.tester._get_services()
            
            # 获取工具列表 - 无特殊情况处理
            if search:
                tools = parser.search_tools(search)
                rprint(f"[blue]🔍 搜索结果 '{search}': 找到 {len(tools)} 个工具[/blue]")
            elif category:
                tools = parser.get_tools_by_category(category)
                rprint(f"[blue]📂 类别 '{category}': 找到 {len(tools)} 个工具[/blue]")
            else:
                tools = parser.get_all_tools()
                rprint(f"[blue]📦 共找到 {len(tools)} 个可部署的 MCP 工具[/blue]")
            
            if not tools:
                rprint("[yellow]⚠️ 未找到匹配的工具[/yellow]")
                return
            
            # 限制并显示
            tools = tools[:limit] if len(tools) > limit else tools
            self._display_tools_table(tools, show_package)
            
        except Exception as e:
            rprint(f"[red]❌ 加载工具列表失败: {e}[/red]")
            raise
    
    def _find_tool_info(self, url: str) -> Optional[MCPToolInfo]:
        """查找工具信息 - 单一职责"""
        rprint("[blue]🔍 在数据库中查找对应的MCP工具...[/blue]")
        tool_info = self.tester.find_tool_by_url(url)
        
        if not tool_info:
            rprint(f"[red]❌ 在数据库中未找到URL对应的MCP工具: {url}[/red]")
            rprint("[yellow]💡 提示: 可以使用 'batch-mcp list-tools --search <关键词>' 搜索可用工具[/yellow]")
            return None
        
        self._display_tool_info(tool_info)
        return tool_info
    
    def _deploy_tool(self, tool_info: MCPToolInfo, config: TestConfig):
        """部署工具 - 单一职责"""
        if not tool_info.package_name:
            rprint("[red]❌ 该工具缺少包名信息，无法部署[/red]")
            return None
        
        if tool_info.requires_api_key:
            rprint(f"[yellow]🔑 该工具需要API密钥: {', '.join(tool_info.api_requirements)}[/yellow]")
            rprint("[yellow]⚠️ 请确保已在.env文件中配置相应的API密钥[/yellow]")
        
        rprint("[blue]🚀 正在部署MCP工具...[/blue]")
        server_info = self.tester.deploy_tool(tool_info.package_name, config.timeout)
        
        if not server_info:
            rprint("[red]❌ MCP工具部署失败[/red]")
            return None
        
        self._display_deployment_success(server_info)
        return server_info
    
    def _run_tests(self, tool_info: Optional[MCPToolInfo], server_info, config: TestConfig):
        """执行测试 - 支持无tool_info场景"""
        rprint("[yellow]🧪 执行基础连通性测试...[/yellow]")
        
        if config.smart_test and tool_info:
            try:
                from src.agents.test_agent import get_test_generator
                rprint("[blue]🤖 启用AI智能测试模式...[/blue]")
                return asyncio.run(self.tester.run_smart_test(tool_info, server_info, config.verbose))
            except ImportError:
                rprint("[yellow]⚠️ AgentScope不可用，使用基础测试模式[/yellow]")
        elif config.smart_test and not tool_info:
            rprint("[yellow]⚠️ 包测试暂不支持AI智能模式，使用基础测试[/yellow]")
        
        return self.tester.run_basic_test(server_info, config.timeout)
    
    def _save_report(self, url: str, tool_info: MCPToolInfo, server_info, success: bool, test_results, start_time):
        """保存报告 - 单一职责"""
        try:
            rprint("[blue]📊 生成测试报告...[/blue]")
            
            report_files = generate_test_report(
                url=url,
                tool_info=tool_info,
                server_info=server_info,
                test_success=success,
                duration=time.time() - start_time,
                test_results=test_results,
                formats=['json', 'html']
            )
            
            for format_name, file_path in report_files.items():
                rprint(f"[green]✅ {format_name.upper()} 报告已保存: {file_path}[/green]")
            
            return report_files
                
        except Exception as e:
            rprint(f"[red]❌ 报告生成失败: {e}[/red]")
            return {}
    
    def _export_to_database(self, json_report_path: str, result: dict = None):
        """导出到数据库 - MVP版本"""
        if not json_report_path:
            rprint("[yellow]⚠️ 没有JSON报告，跳过数据库导出[/yellow]")
            return
        
        try:
            rprint("[blue]🗄️ 导出结果到数据库...[/blue]")
            
            # 使用与database_examples.py相同的方式
            import os
            from supabase import create_client
            import json
            from datetime import datetime
            
            # 获取数据库配置 - 使用环境变量
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            if not supabase_url or not supabase_key:
                rprint("[yellow]⚠️ 数据库配置未设置 (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)，跳过数据库导出[/yellow]")
                return
            
            # 创建Supabase客户端 - 与database_examples.py相同的方式
            client = create_client(supabase_url, supabase_key)
            rprint("[green]✅ Supabase客户端连接成功[/green]")
            
            # 读取JSON报告
            with open(json_report_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 计算整体测试成功状态 - 基于实际JSON结构和成功率标准
            deployment_ok = json_data.get('deployment_success', False)
            communication_ok = json_data.get('communication_success', False)
            test_results = json_data.get('test_results', [])
            
            # 计算测试成功率 - 50%或以上即认为成功
            if test_results:
                passed_tests = sum(1 for test in test_results if test.get('success', False))
                success_rate = (passed_tests / len(test_results)) * 100
                tests_successful = success_rate >= 50.0  # 50%或以上认为成功
            else:
                tests_successful = False
                
            overall_success = deployment_ok and communication_ok and tests_successful
            
            # 转换为数据库记录格式 - 匹配实际数据库表结构
            record = {
                'test_timestamp': datetime.now().isoformat(),
                'tool_identifier': json_data.get('tool_info', {}).get('github_url', '') if json_data.get('tool_info') else json_data.get('test_url', ''),
                'tool_name': json_data.get('tool_info', {}).get('name', 'Unknown') if json_data.get('tool_info') else json_data.get('tool_name', 'Unknown'),
                'tool_author': json_data.get('tool_info', {}).get('author', '') if json_data.get('tool_info') else '',
                'tool_category': json_data.get('tool_info', {}).get('category', '') if json_data.get('tool_info') else '',
                'test_success': overall_success,
                'deployment_success': json_data.get('deployment_success', False),
                'communication_success': json_data.get('communication_success', False),
                'available_tools_count': json_data.get('available_tools_count', 0),
                'test_duration_seconds': json_data.get('test_duration_seconds', 0),
                'error_messages': json_data.get('error_messages', []),
                'test_details': json_data.get('test_results', []),
                'environment_info': {'platform': json_data.get('platform_info', 'Unknown')}
            }
            
            # 插入数据库 - 使用与database_examples.py相同的方式
            response = client.table('mcp_test_results').insert(record).execute()
            
            if response.data:
                rprint("[green]✅ 数据库导出成功 - 记录已保存到 mcp_test_results 表[/green]")
                rprint(f"[dim]   工具: {record['tool_name']}[/dim]")
                rprint(f"[dim]   成功: {'✅' if record['test_success'] else '❌'}[/dim]")
                rprint(f"[dim]   耗时: {record['test_duration_seconds']:.1f}秒[/dim]")
            else:
                rprint("[yellow]⚠️ 数据库导出可能失败，但不影响测试结果[/yellow]")
                
        except Exception as e:
            rprint(f"[yellow]⚠️ 数据库导出异常: {e}[/yellow]")
            rprint("[dim]   检查 SUPABASE_URL 和 SUPABASE_SERVICE_ROLE_KEY 环境变量[/dim]")
    
    def _cleanup_server(self, server_id: str):
        """清理服务器 - 单一职责"""
        try:
            rprint("[yellow]🧹 清理测试环境...[/yellow]")
            self.tester.cleanup_server(server_id)
            rprint("[green]✅ 清理完成[/green]")
        except Exception as e:
            rprint(f"[yellow]⚠️ 清理异常: {e}[/yellow]")
    
    def _display_tool_info(self, tool_info: MCPToolInfo):
        """显示工具信息 - 统一格式"""
        rprint(f"[green]✅ 找到工具: {tool_info.name}[/green]")
        rprint(f"[blue]👤 作者: {tool_info.author}[/blue]")
        rprint(f"[blue]📦 包名: {tool_info.package_name}[/blue]")
        rprint(f"[blue]📂 类别: {tool_info.category}[/blue]")
        rprint(f"[blue]📝 描述: {tool_info.description[:100]}...[/blue]")
    
    def _display_deployment_success(self, server_info, package_name=None):
        """显示部署成功信息 - 统一格式"""
        rprint(f"[green]✅ 部署成功！服务器ID: {server_info.server_id}[/green]")
        
        if package_name:
            rprint(f"[blue]📦 包名: {package_name}[/blue]")
        
        if server_info.available_tools:
            rprint(f"[green]🛠️ 可用工具 ({len(server_info.available_tools)} 个):[/green]")
            for i, tool in enumerate(server_info.available_tools, 1):
                tool_name = tool.get('name', 'unknown')
                tool_desc = tool.get('description', '无描述')
                rprint(f"  {i}. [cyan]{tool_name}[/cyan] - {tool_desc[:60]}...")
    
    def _display_tools_table(self, tools: List[MCPToolInfo], show_package: bool):
        """显示工具表格 - 简化实现"""
        from rich.table import Table
        from rich.console import Console
        
        console = Console()
        table = Table(title="MCP 工具列表")
        
        table.add_column("名称", style="cyan", width=25)
        table.add_column("作者", style="magenta", width=15)
        table.add_column("类别", style="green", width=12)
        
        if show_package:
            table.add_column("包名", style="yellow", width=30)
        
        table.add_column("描述", style="white", width=40)
        table.add_column("API", style="red", width=5)
        
        for tool in tools:
            api_status = "🔑" if tool.requires_api_key else "🆓"
            name = tool.name[:23] + "..." if len(tool.name) > 25 else tool.name
            desc = tool.description[:38] + "..." if len(tool.description) > 40 else tool.description
            
            row_data = [name, tool.author, tool.category.split('\n')[0]]
            
            if show_package:
                package = tool.package_name or "N/A"
                row_data.append(package[:28] + "..." if len(package) > 30 else package)
            
            row_data.extend([desc, api_status])
            table.add_row(*row_data)
        
        console.print(table)


# 全局处理器实例
_handler = CLIHandler()

def get_cli_handler() -> CLIHandler:
    """获取全局CLI处理器实例"""
    return _handler
