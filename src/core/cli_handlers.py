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
from src.utils.csv_parser import MCPToolInfo, get_mcp_parser
from src.core.evaluator import evaluate_full_repository_with_comprehensive_score

class CLIHandler:
    """CLI命令处理器 - 统一处理模式"""
    
    def __init__(self):
        self.tester = get_mcp_tester()

    def evaluate_tools(self, db_export: bool):
        """评估所有工具 - 包含综合评分"""
        try:
            parser = get_mcp_parser()
            tools = parser.get_all_tools()
            if not tools:
                rprint("[red]❌ 没有找到可评估的工具。[/red]")
                return

            # 创建Supabase客户端供评估使用
            supabase_client = None
            if db_export:
                try:
                    import os
                    from supabase import create_client
                    supabase_url = os.getenv('SUPABASE_URL')
                    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
                    if supabase_url and supabase_key:
                        supabase_client = create_client(supabase_url, supabase_key)
                except:
                    pass

            for tool in tools:
                if not tool.github_url:
                    continue

                rprint(f"[blue]🔍 正在评估: {tool.name}[/blue]")
                evaluation_result = evaluate_full_repository_with_comprehensive_score(tool.github_url, supabase_client)

                if evaluation_result["status"] == "success":
                    final_score = evaluation_result['final_score']
                    comprehensive_score = evaluation_result.get('final_comprehensive_score', final_score)
                    rprint(f"[green]✅ 评估完成: {tool.name} - GitHub评分: {final_score}/100, 综合评分: {comprehensive_score}/100[/green]")
                    if db_export:
                        self._export_evaluation_to_database(tool.github_url, evaluation_result)
                else:
                    rprint(f"[red]❌ 评估失败: {tool.name} - {evaluation_result['message']}[/red]")

        except Exception as e:
            rprint(f"[red]❌ 评估过程发生错误: {e}[/red]")

    def _export_evaluation_to_database(self, github_url: str, evaluation_result: dict):
        """导出评估结果到数据库 - 包含综合评分"""
        try:
            import os
            from supabase import create_client
            from datetime import datetime

            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

            if not supabase_url or not supabase_key:
                rprint("[yellow]⚠️ 数据库配置未设置，跳过数据库导出[/yellow]")
                return

            client = create_client(supabase_url, supabase_key)

            # 获取综合评分数据
            test_success_info = evaluation_result.get('test_success_rate', {})
            comprehensive_info = evaluation_result.get('comprehensive_scoring', {})

            record = {
                'github_url': github_url,
                'final_score': evaluation_result['final_score'],
                'sustainability_score': evaluation_result['sustainability']['total_score'],
                'popularity_score': evaluation_result['popularity']['total_score'],
                'sustainability_details': evaluation_result['sustainability']['details'],
                'popularity_details': evaluation_result['popularity']['details'],
                'last_evaluated_at': datetime.now().isoformat(),
                # 新增字段
                'success_rate': test_success_info.get('success_rate'),
                'test_count': test_success_info.get('test_count', 0),
                'total_score': comprehensive_info.get('total_score'),
                'last_calculated_at': datetime.now().isoformat(),
            }

            client.table('mcp_repository_evaluations').upsert(record).execute()
            rprint(f"[green]✅ 成功导出评估结果到数据库: {github_url}[/green]")

        except Exception as e:
            rprint(f"[yellow]⚠️ 数据库导出异常: {e}[/yellow]")
    
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
            
            # 3.5. 评估工具
            evaluation_result = None
            if config.evaluate:
                rprint("[blue]🔍 正在评估工具...[/blue]")
                # 创建Supabase客户端供评估使用
                supabase_client = None
                if config.db_export:
                    try:
                        import os
                        from supabase import create_client
                        supabase_url = os.getenv('SUPABASE_URL')
                        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
                        if supabase_url and supabase_key:
                            supabase_client = create_client(supabase_url, supabase_key)
                    except:
                        pass
                
                evaluation_result = evaluate_full_repository_with_comprehensive_score(tool_info.github_url, supabase_client)
                if evaluation_result and evaluation_result.get("status") == "success":
                    self._display_evaluation_result(evaluation_result)

            # 4. 生成报告
            report_files = {}
            if config.save_report:
                report_files = self._save_report(url, tool_info, server_info, success, test_results, server_info.start_time, evaluation_result)
            
            # 4.5. 数据库导出 (可选)
            if config.db_export:
                self._export_to_database(report_files.get('json'), evaluation_result=evaluation_result)
            
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
            # 查找工具信息
            parser, _ = self.tester._get_services()
            tool_info = parser.find_tool_by_package(package)

            # 直接部署包
            server_info = self.tester.deploy_tool(package, config.timeout)
            if not server_info:
                rprint("[red]❌ MCP工具部署失败[/red]")
                return False
            
            self._display_deployment_success(server_info, package)
            
            # 执行测试 - 统一逻辑，支持smart模式
            success, test_results = self._run_tests(tool_info, server_info, config)
            
            # 评估工具
            evaluation_result = None
            if config.evaluate and tool_info and tool_info.github_url:
                rprint("[blue]🔍 正在评估工具...[/blue]")
                # 创建Supabase客户端供评估使用
                supabase_client = None
                if config.db_export:
                    try:
                        import os
                        from supabase import create_client
                        supabase_url = os.getenv('SUPABASE_URL')
                        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
                        if supabase_url and supabase_key:
                            supabase_client = create_client(supabase_url, supabase_key)
                    except:
                        pass
                
                evaluation_result = evaluate_full_repository_with_comprehensive_score(tool_info.github_url, supabase_client)
                if evaluation_result and evaluation_result.get("status") == "success":
                    self._display_evaluation_result(evaluation_result)

            # 生成报告（如果需要）
            report_files = {}
            if config.save_report:
                report_files = self._save_report(package, tool_info, server_info, success, test_results, server_info.start_time, evaluation_result)
            
            # 数据库导出 (如果需要)
            if config.db_export:
                self._export_to_database(report_files.get('json'), evaluation_result=evaluation_result)
            
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
    
    def _save_report(self, url: str, tool_info: MCPToolInfo, server_info, success: bool, test_results, start_time, evaluation_result: Optional[dict] = None):
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
                evaluation_result=evaluation_result,
                formats=['json', 'html']
            )
            
            for format_name, file_path in report_files.items():
                rprint(f"[green]✅ {format_name.upper()} 报告已保存: {file_path}[/green]")
            
            return report_files
                
        except Exception as e:
            rprint(f"[red]❌ 报告生成失败: {e}[/red]")
            return {}
    
    def _export_to_database(self, json_report_path: str, evaluation_result: Optional[dict] = None):
        """导出到数据库 - MVP版本"""
        if not json_report_path:
            rprint("[yellow]⚠️ 没有JSON报告，跳过数据库导出[/yellow]")
            return
        
        try:
            rprint("[blue]🗄️ 导出结果到数据库...[/blue]")
            
            import os
            from supabase import create_client
            import json
            from datetime import datetime
            
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            if not supabase_url or not supabase_key:
                rprint("[yellow]⚠️ 数据库配置未设置 (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)，跳过数据库导出[/yellow]")
                return
            
            client = create_client(supabase_url, supabase_key)
            
            with open(json_report_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            deployment_ok = json_data.get('deployment_success', False)
            communication_ok = json_data.get('communication_success', False)
            test_results = json_data.get('test_results', [])
            
            if test_results:
                passed_tests = sum(1 for test in test_results if test.get('success', False))
                success_rate = (passed_tests / len(test_results)) * 100
                tests_successful = success_rate >= 50.0
            else:
                tests_successful = False
                
            overall_success = deployment_ok and communication_ok and tests_successful
            
            # 获取工具信息（如果存在）
            tool_info = json_data.get('tool_info', {})
            
            record = {
                'test_timestamp': datetime.now().isoformat(),
                'tool_identifier': tool_info.get('github_url', '') if tool_info else json_data.get('test_url', ''),
                'tool_name': tool_info.get('name', 'Unknown') if tool_info else json_data.get('tool_name', 'Unknown'),
                'tool_author': tool_info.get('author', '') if tool_info else '',
                'tool_category': tool_info.get('category', '') if tool_info else '',
                'test_success': overall_success,
                'deployment_success': json_data.get('deployment_success', False),
                'communication_success': json_data.get('communication_success', False),
                'available_tools_count': json_data.get('available_tools_count', 0),
                'test_duration_seconds': json_data.get('test_duration_seconds', 0),
                'error_messages': json_data.get('error_messages', []),
                'test_details': json_data.get('test_results', []),
                'environment_info': {'platform': json_data.get('platform_info', 'Unknown')}
            }
            
            # 添加LobeHub评分信息（如果工具信息中有）
            if tool_info:
                record.update({
                    'lobehub_url': tool_info.get('lobehub_url'),
                    'lobehub_evaluate': tool_info.get('lobehub_evaluate'),
                    'lobehub_score': tool_info.get('lobehub_score'),
                    'lobehub_star_count': tool_info.get('lobehub_star_count'),
                    'lobehub_fork_count': tool_info.get('lobehub_fork_count'),
                })

            if evaluation_result and evaluation_result.get("status") == "success":
                record['final_score'] = evaluation_result['final_score']
                record['sustainability_score'] = evaluation_result['sustainability']['total_score']
                record['popularity_score'] = evaluation_result['popularity']['total_score']
                record['sustainability_details'] = evaluation_result['sustainability']['details']
                record['popularity_details'] = evaluation_result['popularity']['details']
                record['evaluation_timestamp'] = datetime.now().isoformat()
                
                # 计算并添加综合评分 - 形成闭环 (兼容模式)
                try:
                    from src.core.evaluator import calculate_comprehensive_score_from_tests
                    github_url = tool_info.get('github_url', '') if tool_info else json_data.get('test_url', '')
                    
                    if github_url:
                        # 先插入基础记录
                        response = client.table('mcp_test_results').insert(record).execute()
                        
                        if response.data:
                            record_id = response.data[0]['test_id']
                            rprint("[green]✅ 基础记录已保存到数据库[/green]")
                            
                            # 计算综合评分
                            comp_result = calculate_comprehensive_score_from_tests(github_url, client)
                            if comp_result and comp_result.get('comprehensive_score') is not None:
                                try:
                                    # 尝试更新记录，如果列不存在会失败但不影响主流程
                                    update_data = {
                                        'comprehensive_score': comp_result['comprehensive_score'],
                                        'calculation_method': comp_result['calculation_method']
                                    }
                                    
                                    client.table('mcp_test_results')\
                                        .update(update_data)\
                                        .eq('test_id', record_id)\
                                        .execute()
                                    
                                    rprint(f"[green]✅ 综合评分已更新: {comp_result['comprehensive_score']} ({comp_result['calculation_method']})[/green]")
                                    
                                except Exception as update_error:
                                    # 列不存在，但不影响核心功能
                                    rprint(f"[yellow]⚠️ 综合评分列不存在，请先运行数据库迁移: {update_error}[/yellow]")
                                    rprint(f"[dim]💡 综合评分计算完成: {comp_result['comprehensive_score']}, 但无法存储到数据库[/dim]")
                            else:
                                rprint("[dim]⚠️ 无法计算综合评分[/dim]")
                            
                            return  # 成功，提前返回
                        
                except Exception as e:
                    rprint(f"[yellow]⚠️ 综合评分处理失败: {e}[/yellow]")
                    # 继续执行普通插入逻辑

            rprint(f"[dim]Dumping to database: {record}[/dim]")
            response = client.table('mcp_test_results').insert(record).execute()
            
            if response.data:
                rprint("[green]✅ 数据库导出成功 - 记录已保存到 mcp_test_results 表[/green]")
            else:
                rprint(f"[red]❌ 数据库导出失败: {response.error.message if response.error else '未知错误'}[/red]")
                
        except Exception as e:
            rprint(f"[red]❌ 数据库导出异常: {e}[/red]")
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

    def _display_evaluation_result(self, evaluation_result: dict):
        """显示评估结果 - 包含综合评分"""
        from rich.table import Table
        from rich.console import Console

        console = Console()
        table = Table(title="MCP 工具评估结果")

        table.add_column("类别", style="cyan", width=20)
        table.add_column("指标", style="magenta", width=25)
        table.add_column("分数", style="green", width=10)
        table.add_column("原因", style="white", width=50)

        sustainability = evaluation_result.get('sustainability', {})
        popularity = evaluation_result.get('popularity', {})
        test_success_info = evaluation_result.get('test_success_rate', {})
        comprehensive_info = evaluation_result.get('comprehensive_scoring', {})

        # 显示综合评分
        final_comprehensive_score = evaluation_result.get('final_comprehensive_score', evaluation_result.get('final_score'))
        table.add_row("[bold red]综合评分[/bold red]", "", f"[bold red]{final_comprehensive_score}[/bold red]", "GitHub评估 + 测试成功率综合")
        
        # 显示GitHub评估分数
        table.add_row("GitHub评分", "", f"[bold]{evaluation_result.get('final_score')}[/bold]", "仓库可持续性和受欢迎程度")
        
        # 显示测试成功率
        if test_success_info.get('success_rate') is not None:
            success_rate = test_success_info['success_rate']
            test_count = test_success_info.get('test_count', 0)
            table.add_row("测试成功率", "", f"[bold]{success_rate}%[/bold]", f"基于 {test_count} 次测试记录")
        else:
            table.add_row("测试成功率", "", "[dim]暂无数据[/dim]", "无测试记录")

        table.add_section()
        table.add_row("[bold]可持续性[/bold]", "", f"[bold]{sustainability.get('total_score')}[/bold]", "")
        for metric, data in sustainability.get('details', {}).items():
            table.add_row("", metric, str(data.get('score')), data.get('reason'))
        
        table.add_section()
        table.add_row("[bold]受欢迎程度[/bold]", "", f"[bold]{popularity.get('total_score')}[/bold]", "")
        for metric, data in popularity.get('details', {}).items():
            table.add_row("", metric, str(data.get('score')), data.get('reason'))

        console.print(table)
    
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
