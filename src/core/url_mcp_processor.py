#!/usr/bin/env python3
"""
URL-MCP 智能对接处理器

完善的URL与MCP工具自动部署、测试和报告生成系统

作者: AI Assistant
日期: 2025-08-15
"""

import os
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

try:
    from rich.console import Console
    from rich.table import Table
    from rich import print as rprint
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    print("❌ Rich未安装，使用基础输出")
    def rprint(text): print(text)
    Console = None

from src.utils.csv_parser import get_mcp_parser, MCPToolInfo
from src.core.simple_mcp_deployer import get_simple_mcp_deployer

@dataclass
class TestReport:
    """测试报告数据结构"""
    session_id: str
    url: str
    tool_info: MCPToolInfo
    start_time: datetime
    end_time: Optional[datetime] = None
    deployment_success: bool = False
    deployment_time: float = 0.0
    communication_success: bool = False
    available_tools_count: int = 0
    test_results: List[Dict[str, Any]] = None
    error_messages: List[str] = None
    performance_metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.test_results is None:
            self.test_results = []
        if self.error_messages is None:
            self.error_messages = []
        if self.performance_metrics is None:
            self.performance_metrics = {}

class URLMCPProcessor:
    """URL-MCP智能处理器"""
    
    def __init__(self):
        self.console = Console() if Console else None
        self.parser = get_mcp_parser()
        self.deployer = get_simple_mcp_deployer()
        self.reports_dir = Path("data/test_results/reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_url(
        self, 
        url: str, 
        enable_smart_test: bool = False,
        timeout: int = 30,
        generate_report: bool = True
    ) -> TestReport:
        """完整的URL处理流程"""
        
        session_id = str(uuid.uuid4())[:8]
        start_time = datetime.now()
        
        # 初始化报告
        report = TestReport(
            session_id=session_id,
            url=url,
            tool_info=None,
            start_time=start_time
        )
        
        try:
            rprint(f"[bold green]🎯 开始处理URL:[/bold green] {url}")
            rprint(f"[blue]📝 会话ID: {session_id}[/blue]")
            
            # 第一步：URL解析和工具匹配
            tool_info = await self._resolve_url_to_tool(url)
            if not tool_info:
                report.error_messages.append("无法从URL解析到MCP工具")
                return report
            
            report.tool_info = tool_info
            
            # 第二步：工具部署
            deployment_start = time.time()
            server_info = await self._deploy_tool(tool_info, timeout)
            deployment_time = time.time() - deployment_start
            
            report.deployment_time = deployment_time
            
            if not server_info:
                report.error_messages.append("MCP工具部署失败")
                return report
            
            report.deployment_success = True
            report.available_tools_count = len(server_info.available_tools)
            
            # 第三步：通信验证
            comm_success = await self._verify_communication(server_info)
            report.communication_success = comm_success
            
            # 第四步：功能测试
            if enable_smart_test:
                test_results = await self._run_smart_tests(tool_info, server_info)
            else:
                test_results = await self._run_basic_tests(server_info)
            
            report.test_results = test_results
            
            # 第五步：性能分析
            performance = await self._analyze_performance(server_info, deployment_time)
            report.performance_metrics = performance
            
            # 清理资源
            try:
                self.deployer.cleanup_server(server_info.server_id)
            except Exception as e:
                report.error_messages.append(f"清理失败: {str(e)}")
            
        except Exception as e:
            report.error_messages.append(f"处理异常: {str(e)}")
            rprint(f"[red]❌ 处理失败: {e}[/red]")
        
        finally:
            report.end_time = datetime.now()
            
            # 生成报告
            if generate_report:
                await self._generate_reports(report)
        
        return report
    
    async def _resolve_url_to_tool(self, url: str) -> Optional[MCPToolInfo]:
        """将URL解析为MCP工具信息"""
        try:
            rprint("[blue]🔍 解析URL到MCP工具...[/blue]")
            
            # 1. 直接URL匹配
            tool_info = self.parser.find_tool_by_url(url)
            if tool_info and tool_info.package_name:
                rprint(f"[green]✅ 通过URL直接匹配: {tool_info.name}[/green]")
                return tool_info
            
            # 如果URL匹配但缺少包名，先尝试构造
            if tool_info and not tool_info.package_name and "github.com" in url:
                constructed_package = self._construct_package_from_github_url(url)
                if constructed_package:
                    tool_info.package_name = constructed_package
                    rprint(f"[green]✅ URL匹配并补充包名: {tool_info.name} -> {constructed_package}[/green]")
                    return tool_info
            
            # 2. 从URL提取包名
            package_name = self._extract_package_from_url(url)
            if package_name:
                tool_info = self.parser.find_tool_by_package(package_name)
                if tool_info:
                    rprint(f"[green]✅ 通过包名匹配: {tool_info.name}[/green]")
                    return tool_info
            
            # 3. 智能搜索
            search_terms = self._extract_search_terms_from_url(url)
            for term in search_terms:
                tools = self.parser.search_tools(term)
                if tools:
                    tool_info = tools[0]  # 取第一个匹配的
                    rprint(f"[green]✅ 通过搜索词'{term}'匹配: {tool_info.name}[/green]")
                    return tool_info
            
            # 4. 如果是GitHub URL，尝试构造包名
            if "github.com" in url:
                constructed_package = self._construct_package_from_github_url(url)
                if constructed_package:
                    # 创建伪工具信息用于测试
                    tool_info = MCPToolInfo(
                        name=f"GitHub Tool: {constructed_package}",
                        url=url,
                        author="Unknown",
                        github_url=url,
                        description=f"从GitHub URL {url} 构造的MCP工具",
                        category="GitHub Repository",
                        package_name=constructed_package,
                        requires_api_key=False,
                        api_requirements=[]
                    )
                    rprint(f"[yellow]⚡ 从GitHub URL构造: {constructed_package}[/yellow]")
                    return tool_info
            
            rprint(f"[red]❌ 无法从URL解析MCP工具: {url}[/red]")
            return None
            
        except Exception as e:
            rprint(f"[red]❌ URL解析异常: {e}[/red]")
            return None
    
    def _extract_package_from_url(self, url: str) -> Optional[str]:
        """从URL提取NPM包名"""
        # 常见的NPM包URL模式
        patterns = [
            r"npmjs\.com/package/([^/]+(?:/[^/]+)?)",
            r"npm\.im/([^/]+(?:/[^/]+)?)",
            r"@([^/]+/[^/]+)",
        ]
        
        import re
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    # 兼容旧测试脚本的方法名，统一对外暴露
    def _extract_package_name(self, url: str) -> Optional[str]:
        """从任意URL中推断可用于 npx 的包名/来源规范。
        优先顺序:
        1) 直接包含的 npm 包名（npmjs 链接或 @scope/name 形式）
        2) GitHub URL -> 返回 npx 可用的 github:owner/repo 规范
        3) 无法推断则返回 None
        """
        # 直接提取 npm 包名
        pkg = self._extract_package_from_url(url)
        if pkg:
            return pkg

        # GitHub URL 回退
        if "github.com" in url:
            return self._construct_package_from_github_url(url)

        return None
    
    def _extract_search_terms_from_url(self, url: str) -> List[str]:
        """从URL提取搜索关键词"""
        terms = []
        
        # 从路径中提取词汇
        import re
        path_parts = re.findall(r'/([^/]+)', url)
        for part in path_parts:
            if len(part) > 2 and part not in ['www', 'com', 'org', 'net']:
                terms.append(part.replace('-', ' ').replace('_', ' '))
        
        return terms
    
    def _construct_package_from_github_url(self, url: str) -> Optional[str]:
        """从GitHub URL构造可能的包名"""
        import re
        
        # 提取 github.com/username/repo 模式
        match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
        if match:
            username, repo = match.groups()
            
            # 清理repo名称
            repo = repo.rstrip('.git')
            
            # 优先返回 npx 可直接执行的 GitHub 源规范
            # 参考: npx -y github:owner/repo
            github_spec = f"github:{username}/{repo}"
            return github_spec
        
        return None
    
    async def _deploy_tool(self, tool_info: MCPToolInfo, timeout: int):
        """部署MCP工具"""
        try:
            # 优先使用run_command，其次使用package_name
            if tool_info.run_command:
                display_name = tool_info.run_command
                rprint(f"[blue]🚀 部署MCP工具: {display_name}[/blue]")
                server_info = self.deployer.deploy_package(
                    package_name=tool_info.package_name, 
                    timeout=timeout,
                    run_command=tool_info.run_command
                )
            else:
                display_name = tool_info.package_name
                rprint(f"[blue]🚀 部署MCP工具: {display_name}[/blue]")
                
                if not tool_info.package_name:
                    raise ValueError("缺少包名信息")
                
                server_info = self.deployer.deploy_package(tool_info.package_name, timeout)
            
            if server_info:
                rprint(f"[green]✅ {display_name} 部署成功！[/green]")
                rprint(f"[green]🔧 可用工具: {[tool['name'] for tool in server_info.available_tools]}[/green]")
                rprint(f"[green]✅ 部署成功，工具数: {len(server_info.available_tools)}[/green]")
            
            return server_info
            
        except Exception as e:
            rprint(f"[red]❌ 部署失败: {e}[/red]")
            return None
    
    async def _verify_communication(self, server_info) -> bool:
        """验证MCP通信"""
        try:
            rprint("[blue]📡 验证MCP通信...[/blue]")
            
            tools_request = {
                "jsonrpc": "2.0",
                "id": 999,
                "method": "tools/list",
                "params": {}
            }
            
            result = server_info.communicator.send_request(tools_request, timeout=10)
            
            if result['success']:
                rprint("[green]✅ MCP通信正常[/green]")
                return True
            else:
                rprint(f"[yellow]⚠️ MCP通信异常: {result.get('error')}[/yellow]")
                return False
                
        except Exception as e:
            rprint(f"[red]❌ 通信验证失败: {e}[/red]")
            return False
    
    async def _run_basic_tests(self, server_info) -> List[Dict[str, Any]]:
        """运行基础测试"""
        tests = []
        
        try:
            rprint("[blue]🧪 执行基础功能测试...[/blue]")
            
            # 工具列表测试
            test_start = time.time()
            tools_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            
            result = server_info.communicator.send_request(tools_request)
            test_time = time.time() - test_start
            
            tests.append({
                "name": "工具列表测试",
                "success": result['success'],
                "response_time": test_time,
                "details": result
            })
            
            # 对每个可用工具进行简单测试
            for i, tool in enumerate(server_info.available_tools[:3], 1):
                test_start = time.time()
                tool_name = tool.get('name', 'unknown')
                
                try:
                    # 尝试调用工具（使用空参数）
                    tool_request = {
                        "jsonrpc": "2.0",
                        "id": i + 1,
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": {}
                        }
                    }
                    
                    result = server_info.communicator.send_request(tool_request, timeout=5)
                    test_time = time.time() - test_start
                    
                    tests.append({
                        "name": f"工具调用测试: {tool_name}",
                        "success": result.get('success', False),
                        "response_time": test_time,
                        "details": result
                    })
                    
                except Exception as e:
                    tests.append({
                        "name": f"工具调用测试: {tool_name}",
                        "success": False,
                        "response_time": time.time() - test_start,
                        "error": str(e)
                    })
            
            passed = sum(1 for t in tests if t.get('success', False))
            rprint(f"[green]📊 基础测试完成: {passed}/{len(tests)} 通过[/green]")
            
        except Exception as e:
            rprint(f"[red]❌ 基础测试失败: {e}[/red]")
        
        return tests
    
    async def _run_smart_tests(self, tool_info: MCPToolInfo, server_info) -> List[Dict[str, Any]]:
        """运行智能测试（暂时回退到基础测试）"""
        try:
            rprint("[blue]🤖 尝试智能测试...[/blue]")
            
            # 尝试导入智能代理
            try:
                from src.agents.test_agent import get_test_generator
                from src.agents.validation_agent import get_validation_agent
                
                # 智能测试逻辑（简化版）
                rprint("[yellow]⚠️ 智能测试功能开发中，使用增强基础测试[/yellow]")
                return await self._run_basic_tests(server_info)
                
            except Exception as agent_error:
                rprint(f"[yellow]⚠️ 智能代理不可用: {agent_error}[/yellow]")
                rprint("[blue]🔄 回退到基础测试模式[/blue]")
                return await self._run_basic_tests(server_info)
                
        except Exception as e:
            rprint(f"[red]❌ 智能测试失败: {e}[/red]")
            return await self._run_basic_tests(server_info)
    
    async def _analyze_performance(self, server_info, deployment_time: float) -> Dict[str, float]:
        """性能分析"""
        metrics = {
            "deployment_time": deployment_time,
            "tools_count": len(server_info.available_tools),
            "startup_time": time.time() - server_info.start_time
        }
        
        # 简单的响应时间测试
        try:
            start = time.time()
            tools_request = {
                "jsonrpc": "2.0",
                "id": 999,
                "method": "tools/list",
                "params": {}
            }
            server_info.communicator.send_request(tools_request, timeout=5)
            metrics["avg_response_time"] = time.time() - start
        except:
            metrics["avg_response_time"] = -1
        
        return metrics
    
    async def _generate_reports(self, report: TestReport):
        """生成多格式测试报告"""
        try:
            rprint("[blue]📊 生成测试报告...[/blue]")
            
            # 1. JSON报告
            await self._generate_json_report(report)
            
            # 2. HTML报告
            await self._generate_html_report(report)
            
            # 3. 控制台摘要
            self._print_console_summary(report)
            
        except Exception as e:
            rprint(f"[red]❌ 报告生成失败: {e}[/red]")
    
    async def _generate_json_report(self, report: TestReport):
        """生成JSON格式报告"""
        try:
            timestamp = report.start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"mcp_test_{timestamp}_{report.session_id}.json"
            filepath = self.reports_dir / filename
            
            # 转换为可序列化的格式
            report_data = asdict(report)
            report_data['start_time'] = report.start_time.isoformat()
            report_data['end_time'] = report.end_time.isoformat() if report.end_time else None
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            rprint(f"[green]✅ JSON报告: {filepath}[/green]")
            
        except Exception as e:
            rprint(f"[red]❌ JSON报告生成失败: {e}[/red]")
    
    async def _generate_html_report(self, report: TestReport):
        """生成HTML格式报告"""
        try:
            timestamp = report.start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"mcp_test_{timestamp}_{report.session_id}.html"
            filepath = self.reports_dir / filename
            
            html_content = self._create_html_template(report)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            rprint(f"[green]✅ HTML报告: {filepath}[/green]")
            
        except Exception as e:
            rprint(f"[red]❌ HTML报告生成失败: {e}[/red]")
    
    def _create_html_template(self, report: TestReport) -> str:
        """创建HTML报告模板"""
        duration = (report.end_time - report.start_time).total_seconds() if report.end_time else 0
        
        success_count = sum(1 for test in report.test_results if test.get('success', False))
        total_tests = len(report.test_results)
        success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP测试报告 - {report.session_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background: #2563eb; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .status-success {{ color: #16a34a; font-weight: bold; }}
        .status-failed {{ color: #dc2626; font-weight: bold; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .metric {{ background: #f8fafc; padding: 15px; border-radius: 6px; border-left: 4px solid #3b82f6; }}
        .test-results {{ margin-top: 20px; }}
        .test-item {{ background: #f9fafb; margin: 10px 0; padding: 15px; border-radius: 6px; border-left: 4px solid #10b981; }}
        .test-failed {{ border-left-color: #ef4444; }}
        .timestamp {{ color: #6b7280; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>MCP工具测试报告</h1>
            <p>会话ID: {report.session_id}</p>
            <p class="timestamp">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <h2>基本信息</h2>
        <div class="metrics">
            <div class="metric">
                <strong>测试URL</strong><br>
                <code>{report.url}</code>
            </div>
            <div class="metric">
                <strong>工具名称</strong><br>
                {report.tool_info.name if report.tool_info else '未知'}
            </div>
            <div class="metric">
                <strong>包名</strong><br>
                <code>{report.tool_info.package_name if report.tool_info else '未知'}</code>
            </div>
            <div class="metric">
                <strong>测试时长</strong><br>
                {duration:.2f} 秒
            </div>
        </div>
        
        <h2>测试状态</h2>
        <div class="metrics">
            <div class="metric">
                <strong>部署状态</strong><br>
                <span class="{'status-success' if report.deployment_success else 'status-failed'}">
                    {'✅ 成功' if report.deployment_success else '❌ 失败'}
                </span>
            </div>
            <div class="metric">
                <strong>通信状态</strong><br>
                <span class="{'status-success' if report.communication_success else 'status-failed'}">
                    {'✅ 正常' if report.communication_success else '❌ 异常'}
                </span>
            </div>
            <div class="metric">
                <strong>可用工具数</strong><br>
                {report.available_tools_count} 个
            </div>
            <div class="metric">
                <strong>测试成功率</strong><br>
                {success_count}/{total_tests} ({success_rate:.1f}%)
            </div>
        </div>
        
        <h2>性能指标</h2>
        <div class="metrics">
            <div class="metric">
                <strong>部署时间</strong><br>
                {report.deployment_time:.2f} 秒
            </div>
            <div class="metric">
                <strong>平均响应时间</strong><br>
                {report.performance_metrics.get('avg_response_time', -1):.3f} 秒
            </div>
            <div class="metric">
                <strong>启动时间</strong><br>
                {report.performance_metrics.get('startup_time', -1):.2f} 秒
            </div>
        </div>
        
        <h2>测试结果详情</h2>
        <div class="test-results">
"""
        
        for test in report.test_results:
            success_class = "" if test.get('success', False) else "test-failed"
            status_icon = "✅" if test.get('success', False) else "❌"
            
            html += f"""
            <div class="test-item {success_class}">
                <strong>{status_icon} {test.get('name', '未命名测试')}</strong><br>
                <span class="timestamp">响应时间: {test.get('response_time', 0):.3f}s</span>
                {f"<br><span style='color: #dc2626;'>错误: {test.get('error', '')}</span>" if test.get('error') else ""}
            </div>
"""
        
        if report.error_messages:
            html += """
        <h2>错误信息</h2>
        <div style="background: #fef2f2; padding: 15px; border-radius: 6px; border-left: 4px solid #ef4444;">
"""
            for error in report.error_messages:
                html += f"<p style='color: #dc2626;'>❌ {error}</p>"
            
            html += "</div>"
        
        html += """
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _print_console_summary(self, report: TestReport):
        """打印控制台摘要"""
        if not self.console:
            return
        
        try:
            duration = (report.end_time - report.start_time).total_seconds() if report.end_time else 0
            success_count = sum(1 for test in report.test_results if test.get('success', False))
            total_tests = len(report.test_results)
            success_rate = (success_count/total_tests*100) if total_tests > 0 else 0
            
            # 创建摘要面板
            summary_text = f"""
🎯 URL: {report.url}
📦 工具: {report.tool_info.name if report.tool_info else '未知'}
⏱️ 耗时: {duration:.2f}秒
🚀 部署: {'✅ 成功' if report.deployment_success else '❌ 失败'}
📡 通信: {'✅ 正常' if report.communication_success else '❌ 异常'}
🛠️ 工具数: {report.available_tools_count}
🧪 测试: {success_count}/{total_tests} 通过 ({success_rate:.1f}%)
"""
            
            panel = Panel(
                summary_text.strip(),
                title=f"📊 测试摘要 [{report.session_id}]",
                border_style="green" if report.deployment_success and report.communication_success else "red"
            )
            
            self.console.print(panel)
            
        except Exception as e:
            rprint(f"[yellow]⚠️ 控制台摘要生成失败: {e}[/yellow]")

# 全局处理器实例
_url_processor_instance = None

def get_url_mcp_processor() -> URLMCPProcessor:
    """获取全局URL-MCP处理器实例"""
    global _url_processor_instance
    if _url_processor_instance is None:
        _url_processor_instance = URLMCPProcessor()
    return _url_processor_instance
