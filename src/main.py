#!/usr/bin/env python3
"""
MCP 测试框架 - 主入口 (简洁版)

遵循 Linus 的"好品味"原则：
- CLI入口只负责参数解析和委托
- 每个命令<20行
- 无业务逻辑，无深度嵌套

作者: AI Assistant (Linus重构版) 
日期: 2025-08-18
版本: 2.0.0 (简洁版)
"""

import sys
from pathlib import Path
import typer
from rich import print as rprint

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.cli_handlers import get_cli_handler
from src.core.tester import TestConfig

app = typer.Typer(
    name="batch-mcp",
    help="动态 MCP 工具部署和测试框架 - 简洁版",
    add_completion=False,
    rich_markup_mode="rich"
)

handler = get_cli_handler()

@app.command("test-url")
def test_single_url(
    url: str = typer.Argument(..., help="要测试的 MCP 工具 URL"),
    timeout: int = typer.Option(600, "--timeout", "-t", help="测试超时时间（秒）"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出模式"),
    save_report: bool = typer.Option(True, "--save-report/--no-save-report", help="保存测试报告"),
    cleanup: bool = typer.Option(True, "--cleanup/--no-cleanup", help="自动清理"),
    smart: bool = typer.Option(False, "--smart/--no-smart", help="启用AI智能测试")
):
    """测试单个 MCP 工具 URL"""
    rprint(f"[bold green]🎯 开始测试 MCP 工具:[/bold green] {url}")
    
    config = TestConfig(timeout, verbose, smart, cleanup, save_report)
    success = handler.test_url(url, config)
    
    if success:
        rprint(f"\n[bold green]🎉 {url} 测试完成！[/bold green]")
    else:
        raise typer.Exit(1)

@app.command("test-package")
def test_package(
    package: str = typer.Argument(..., help="要测试的 MCP 包名"),
    timeout: int = typer.Option(600, "--timeout", "-t", help="测试超时时间（秒）"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出模式"),
    cleanup: bool = typer.Option(True, "--cleanup", help="自动清理"),
    smart: bool = typer.Option(False, "--smart", help="启用AI智能测试")
):
    """直接测试指定的 MCP 包"""
    rprint(f"[bold green]📦 开始测试 MCP 包:[/bold green] {package}")
    
    config = TestConfig(timeout, verbose, smart, cleanup, False)
    success = handler.test_package(package, config)
    
    if success:
        rprint(f"\n[bold green]🎉 {package} 测试完成！[/bold green]")
    else:
        raise typer.Exit(1)

@app.command("list-tools")
def list_available_tools(
    category: str = typer.Option(None, "--category", "-c", help="按类别筛选"),
    search: str = typer.Option(None, "--search", "-s", help="搜索工具"),
    limit: int = typer.Option(20, "--limit", "-l", help="显示数量限制"),
    show_package: bool = typer.Option(False, "--show-package", help="显示包名")
):
    """列出可用的 MCP 工具"""
    rprint("[bold green]📋 加载 MCP 工具列表...[/bold green]")
    handler.list_tools(category, search, limit, show_package)

@app.command("init-env")
def init_environment():
    """初始化测试环境"""
    rprint("[bold green]🔧 初始化测试环境...[/bold green]")
    # 简化的环境检查
    try:
        from src.utils.csv_parser import get_mcp_parser
        from src.core.simple_mcp_deployer import get_simple_mcp_deployer
        
        parser = get_mcp_parser()
        tools = parser.get_all_tools()
        rprint(f"[green]✅ 找到 {len(tools)} 个可用工具[/green]")
        
        deployer = get_simple_mcp_deployer()
        rprint("[green]✅ 部署器已就绪[/green]")
        rprint("[green]✅ 环境检查完成[/green]")
        
    except Exception as e:
        rprint(f"[red]❌ 环境检查失败: {e}[/red]")
        raise typer.Exit(1)

@app.callback()
def main(version: bool = typer.Option(False, "--version", help="显示版本信息")):
    """MCP 测试框架 - 简洁版"""
    if version:
        rprint("[bold green]Batch MCP Testing Framework v2.0.0 (简洁版)[/bold green]")
        raise typer.Exit()

if __name__ == "__main__":
    app()
