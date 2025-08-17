#!/usr/bin/env python3
"""
Batch MCP Testing Framework - 主入口文件

基于 test_crossplatform_mcp.py 构建的动态 MCP 工具部署和测试框架
支持根据 URL 动态部署 MCP 工具，自动生成测试用例，并与大模型协作进行验证

作者: AI Assistant
日期: 2025-08-15
版本: 1.0.0
"""

import sys
import time
import asyncio
import platform
from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入核心模块
from src.utils.csv_parser import get_mcp_parser, MCPToolInfo
from src.core.simple_mcp_deployer import get_simple_mcp_deployer
from src.core.url_mcp_processor import get_url_mcp_processor
from src.core.enhanced_report_generator import generate_test_report

# 兼容性导入：保持原有TestResult接口
try:
    from src.core.report_generator import TestResult
except ImportError:
    # 如果原始TestResult不可用，创建一个简单的替代
    class TestResult:
        def __init__(self, test_name: str, success: bool, duration: float, 
                     error_message: str = None, output: str = None):
            self.test_name = test_name
            self.success = success  
            self.duration = duration
            self.error_message = error_message
            self.output = output

# 智能代理模块（可选导入）
try:
    from src.agents.test_agent import get_test_generator
    from src.agents.validation_agent import get_validation_agent
    AGENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ AgentScope 模块不可用: {e}")
    AGENTS_AVAILABLE = False

app = typer.Typer(
    name="batch-mcp",
    help="动态 MCP 工具部署和测试框架",
    add_completion=False,
    rich_markup_mode="rich"
)
console = Console()

@app.command("test-url")
def test_single_url(
    url: str = typer.Argument(..., help="要测试的 MCP 工具 URL"),
    timeout: int = typer.Option(600, "--timeout", "-t", help="测试超时时间（秒，默认10分钟）"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出模式"),
    save_report: bool = typer.Option(True, "--save-report/--no-save-report", help="保存测试报告"),
    cleanup: bool = typer.Option(True, "--cleanup/--no-cleanup", help="测试完成后自动清理"),
    smart: bool = typer.Option(False, "--smart/--no-smart", help="启用AI智能测试（需要AgentScope）")
):
    """测试单个 MCP 工具 URL"""
    rprint(f"[bold green]🎯 开始测试 MCP 工具:[/bold green] {url}")
    
    try:
        # 获取解析器和部署器
        parser = get_mcp_parser()
        deployer = get_simple_mcp_deployer()
        
        # 从URL查找工具信息
        rprint("[blue]🔍 在数据库中查找对应的MCP工具...[/blue]")
        tool_info = parser.find_tool_by_url(url)
        
        if not tool_info:
            rprint(f"[red]❌ 在数据库中未找到URL对应的MCP工具: {url}[/red]")
            rprint("[yellow]💡 提示: 可以使用 'batch-mcp list-tools --search <关键词>' 搜索可用工具[/yellow]")
            raise typer.Exit(1)
        
        # 显示找到的工具信息
        rprint(f"[green]✅ 找到工具: {tool_info.name}[/green]")
        rprint(f"[blue]👤 作者: {tool_info.author}[/blue]")
        rprint(f"[blue]📦 包名: {tool_info.package_name}[/blue]")
        rprint(f"[blue]📂 类别: {tool_info.category}[/blue]")
        rprint(f"[blue]📝 描述: {tool_info.description[:100]}...[/blue]")
        
        if not tool_info.package_name:
            rprint("[red]❌ 该工具缺少包名信息，无法部署[/red]")
            raise typer.Exit(1)
        
        # 检查API密钥需求
        if tool_info.requires_api_key:
            rprint(f"[yellow]🔑 该工具需要API密钥: {', '.join(tool_info.api_requirements)}[/yellow]")
            rprint("[yellow]⚠️ 请确保已在.env文件中配置相应的API密钥[/yellow]")
        
        # 部署MCP工具
        rprint("[blue]🚀 正在部署MCP工具...[/blue]")
        server_info = deployer.deploy_package(tool_info.package_name, timeout)
        
        if not server_info:
            rprint("[red]❌ MCP工具部署失败[/red]")
            raise typer.Exit(1)
        
        # 显示部署结果
        rprint(f"[green]✅ 部署成功！服务器ID: {server_info.server_id}[/green]")
        
        # 显示可用工具
        if server_info.available_tools:
            rprint(f"[green]🛠️ 可用工具 ({len(server_info.available_tools)} 个):[/green]")
            for i, tool in enumerate(server_info.available_tools, 1):
                tool_name = tool.get('name', 'unknown')
                tool_desc = tool.get('description', '无描述')
                rprint(f"  {i}. [cyan]{tool_name}[/cyan] - {tool_desc[:60]}...")
        
        # 执行基础测试
        rprint("[yellow]🧪 执行基础连通性测试...[/yellow]")
        
        # 检查是否启用智能测试
        if smart and AGENTS_AVAILABLE:
            rprint("[blue]🤖 启用AI智能测试模式...[/blue]")
            success, test_results = asyncio.run(_run_smart_test(tool_info, server_info, verbose))
        else:
            if smart and not AGENTS_AVAILABLE:
                rprint("[yellow]⚠️ AgentScope不可用，使用基础测试模式[/yellow]")
            
            # 基础测试
            success, test_results = _run_basic_test(server_info, timeout)
        
        if not success:
            rprint("[red]❌ 测试失败[/red]")
        
        # 显示测试摘要
        rprint("\n[bold green]📊 测试摘要:[/bold green]")
        rprint(f"  • URL: [cyan]{url}[/cyan]")
        rprint(f"  • 工具名称: [cyan]{tool_info.name}[/cyan]")
        rprint(f"  • 包名: [cyan]{tool_info.package_name}[/cyan]")
        rprint(f"  • 部署状态: [green]✅ 成功[/green]")
        rprint(f"  • 进程PID: [blue]{server_info.process.pid}[/blue]")
        rprint(f"  • 可用工具数: [blue]{len(server_info.available_tools)}[/blue]")
        rprint(f"  • 通信状态: {'[green]✅ 正常[/green]' if success else '[red]❌ 异常[/red]'}")
        rprint(f"  • 运行时间: [blue]{time.time() - server_info.start_time:.2f}秒[/blue]")
        
        if tool_info.requires_api_key:
            rprint(f"  • API密钥: [yellow]🔑 需要 ({', '.join(tool_info.api_requirements)})[/yellow]")
        else:
            rprint(f"  • API密钥: [green]🆓 无需[/green]")
        
        # 生成测试报告
        if save_report:
            try:
                rprint("[blue]📊 生成测试报告...[/blue]")
                
                # 生成报告
                report_files = generate_test_report(
                    url=url,
                    tool_info=tool_info,
                    server_info=server_info,
                    test_success=success,
                    duration=time.time() - server_info.start_time,
                    test_results=test_results,
                    formats=['json', 'html', 'database']
                )

                if not report_files:
                    rprint("[yellow]⚠️ 报告生成函数返回空结果，未生成任何文件[/yellow]")
                    rprint(f"[dim]期望目录: {(Path('data')/ 'test_results').resolve()}[/dim]")
                else:
                    for format_name, file_path in report_files.items():
                        rprint(f"[green]✅ {format_name.upper()} 报告已保存: {file_path}[/green]")
            except Exception as report_error:
                rprint(f"[red]❌ 报告生成失败: {report_error}[/red]")
                import traceback
                rprint(f"[yellow]⚠️ 详细错误: {traceback.format_exc()}[/yellow]")
        else:
            rprint("[dim]（已跳过报告生成：save_report=False）[/dim]")

        
    except Exception as e:
        rprint(f"[red]❌ 测试过程发生错误: {e}[/red]")
        success = False
        
    finally:
        # 清理资源
        if cleanup:
            try:
                if 'server_info' in locals() and server_info:
                    rprint("[yellow]🧹 清理测试环境...[/yellow]")
                    deployer.cleanup_server(server_info.server_id)
                    rprint("[green]✅ 清理完成[/green]")
            except Exception as e:
                rprint(f"[yellow]⚠️ 清理异常: {e}[/yellow]")
    
    if not success:
        raise typer.Exit(1)
    
    rprint(f"\n[bold green]🎉 {url} 测试完成！[/bold green]")
    return True

@app.command("smart-test-url")
def smart_test_url(
    url: str = typer.Argument(..., help="要测试的 MCP 工具 URL"),
    timeout: int = typer.Option(600, "--timeout", "-t", help="测试超时时间（秒，默认10分钟）"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出模式"),
    enable_smart: bool = typer.Option(True, "--smart", help="启用AI智能测试"),
    generate_report: bool = typer.Option(True, "--report", help="生成详细测试报告")
):
    """智能URL测试 - 使用增强的URL-MCP处理器"""
    
    try:
        # 使用新的URL-MCP处理器
        processor = get_url_mcp_processor()
        
        rprint(f"[bold green]🚀 启动智能URL测试:[/bold green] {url}")
        
        # 执行完整的处理流程
        report = asyncio.run(processor.process_url(
            url=url,
            enable_smart_test=enable_smart and AGENTS_AVAILABLE,
            timeout=timeout,
            generate_report=generate_report
        ))
        
        # 判断测试是否成功
        if report.deployment_success and report.communication_success:
            success_rate = 0
            if report.test_results:
                passed = sum(1 for test in report.test_results if test.get('success', False))
                success_rate = passed / len(report.test_results)
            
            if success_rate >= 0.7:  # 70%以上成功率
                rprint(f"\n[bold green]🎉 智能URL测试成功完成！[/bold green]")
                return True
            else:
                rprint(f"\n[yellow]⚠️ 测试完成但成功率较低 ({success_rate:.1%})[/yellow]")
        else:
            rprint(f"\n[red]❌ 智能URL测试失败[/red]")
            if report.error_messages:
                for error in report.error_messages:
                    rprint(f"[red]  • {error}[/red]")
            
            raise typer.Exit(1)
            
    except Exception as e:
        rprint(f"[red]❌ 智能URL测试过程发生错误: {e}[/red]")
        if verbose:
            import traceback
            rprint(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)
@app.command("test-package")
def test_package(
    package: str = typer.Argument(..., help="要测试的 MCP 包名 (如: @upstash/context7-mcp)"),
    timeout: int = typer.Option(600, "--timeout", "-t", help="测试超时时间（秒，默认10分钟）"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出模式"),
    cleanup: bool = typer.Option(True, "--cleanup", help="测试完成后自动清理"),
    smart: bool = typer.Option(False, "--smart", help="启用AI智能测试（需要AgentScope）")
):
    """直接测试指定的 MCP 包"""
    rprint(f"[bold green]📦 开始测试 MCP 包:[/bold green] {package}")
    
    try:
        # 获取部署器
        deployer = get_simple_mcp_deployer()
        
        # 部署MCP工具
        rprint("[blue]🚀 正在部署MCP工具...[/blue]")
        server_info = deployer.deploy_package(package, timeout)
        
        if not server_info:
            rprint("[red]❌ MCP工具部署失败[/red]")
            raise typer.Exit(1)
        
        # 显示部署结果
        rprint(f"[green]✅ 部署成功！服务器ID: {server_info.server_id}[/green]")
        rprint(f"[blue]� 包名: {server_info.package_name}[/blue]")
        rprint(f"[blue]� 工具数量: {len(server_info.available_tools)}[/blue]")
        
        # 显示可用工具
        if server_info.available_tools:
            rprint(f"[green]🛠️ 可用工具 ({len(server_info.available_tools)} 个):[/green]")
            for i, tool in enumerate(server_info.available_tools, 1):
                tool_name = tool.get('name', 'unknown')
                tool_desc = tool.get('description', '无描述')
                rprint(f"  {i}. [cyan]{tool_name}[/cyan] - {tool_desc[:60]}...")
        
        # 执行基础测试（简单的工具列表验证）
        rprint("[yellow]🧪 执行基础连通性测试...[/yellow]")
        
        # 检查是否启用智能测试
        if smart and AGENTS_AVAILABLE:
            rprint("[blue]🤖 启用AI智能测试模式...[/blue]")
            # 为包测试创建工具信息
            pseudo_tool_info = MCPToolInfo(
                name=package.split('/')[-1],
                author="Unknown",
                description=f"MCP package: {package}",
                category="Package Test",
                package_name=package,
                requires_api_key=False,
                api_requirements=[]
            )
            success, _ = asyncio.run(_run_smart_test(pseudo_tool_info, server_info, verbose))
        else:
            if smart and not AGENTS_AVAILABLE:
                rprint("[yellow]⚠️ AgentScope不可用，使用基础测试模式[/yellow]")
            
            # 基础测试
            success, _ = _run_basic_test(server_info, timeout)
        
        if not success:
            rprint("[red]❌ 测试失败[/red]")
            raise Exception("测试执行失败")
        
        # 显示测试摘要
        rprint("\n[bold green]📊 测试摘要:[/bold green]")
        rprint(f"  • 包名: [cyan]{package}[/cyan]")
        rprint(f"  • 部署状态: [green]✅ 成功[/green]")
        rprint(f"  • 进程PID: [blue]{server_info.process.pid}[/blue]") 
        rprint(f"  • 可用工具数: [blue]{len(server_info.available_tools)}[/blue]")
        rprint(f"  • 通信状态: [green]✅ 正常[/green]")
        rprint(f"  • 运行时间: [blue]{time.time() - server_info.start_time:.2f}秒[/blue]")
        
        success = True
        
    except Exception as e:
        rprint(f"[red]❌ 测试过程发生错误: {e}[/red]")
        success = False
        
    finally:
        # 清理资源
        if cleanup:
            try:
                if 'server_info' in locals() and server_info:
                    rprint("[yellow]🧹 清理测试环境...[/yellow]")
                    deployer.cleanup_server(server_info.server_id)
                    rprint("[green]✅ 清理完成[/green]")
            except Exception as e:
                rprint(f"[yellow]⚠️ 清理异常: {e}[/yellow]")
    
    if not success:
        raise typer.Exit(1)
    
    rprint(f"\n[bold green]🎉 {package} 测试完成！[/bold green]")
    return True

@app.command("batch-test")
def batch_test(
    input_file: Path = typer.Option(..., "--input", "-i", help="包含 URL 列表的输入文件"),
    output_dir: Path = typer.Option("data/test_results", "--output", "-o", help="输出目录"),
    max_concurrent: int = typer.Option(3, "--concurrent", "-c", help="最大并发测试数"),
    timeout: int = typer.Option(600, "--timeout", "-t", help="每个测试的超时时间（秒，默认10分钟）")
):
    """批量测试多个 MCP 工具"""
    rprint(f"[bold green]🚀 开始批量测试:[/bold green] {input_file}")
    if not input_file.exists():
        rprint(f"[red]❌ 输入文件不存在:[/red] {input_file}")
        raise typer.Exit(1)

    # 读取 CSV（支持中文表头与 UTF-8 BOM）
    import csv
    urls: List[str] = []
    try:
        with open(input_file, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            # 常见列名候选
            url_keys = [
                "GitHub链接", "github_url", "url", "链接", "URL", "Github链接",
            ]
            for row in reader:
                # 逐列尝试提取 URL
                u = None
                for k in url_keys:
                    if k in row and row[k]:
                        u = row[k].strip()
                        break
                if u and u.startswith("http"):
                    urls.append(u)
    except Exception as e:
        rprint(f"[red]❌ CSV读取失败: {e}[/red]")
        raise typer.Exit(1)

    if not urls:
        rprint("[yellow]⚠️ 未在CSV中解析到任何URL[/yellow]")
        raise typer.Exit(1)

    # 顺序执行（MVP：先不开并发，减少环境压力）
    processor = get_url_mcp_processor()
    output_dir.mkdir(parents=True, exist_ok=True)

    total = len(urls)
    ok = 0
    for idx, url in enumerate(urls, 1):
        rprint(f"\n[bold blue]{idx}/{total} ▶ 测试:[/bold blue] {url}")
        try:
            report = asyncio.run(processor.process_url(
                url=url,
                enable_smart_test=False,
                timeout=timeout,
                generate_report=True,
            ))
            if report.deployment_success and report.communication_success:
                ok += 1
        except Exception as e:
            rprint(f"[yellow]⚠️ 测试异常: {e}")
            continue

    rprint(f"\n[bold green]📊 批量测试完成: {ok}/{total} 成功[/bold green]")
    return ok == total

@app.command("list-tools")
def list_available_tools(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="按类别筛选工具"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="搜索工具名称或描述"),
    limit: int = typer.Option(20, "--limit", "-l", help="显示数量限制"),
    show_package: bool = typer.Option(False, "--show-package", help="显示包名信息")
):
    """列出可用的 MCP 工具"""
    rprint("[bold green]📋 加载 MCP 工具列表...[/bold green]")
    
    try:
        parser = get_mcp_parser()
        
        # 获取工具列表
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
        
        # 限制显示数量
        if len(tools) > limit:
            tools = tools[:limit]
            rprint(f"[yellow]📋 显示前 {limit} 个工具（总共 {len(parser.get_all_tools())} 个）[/yellow]")
        
        # 创建表格
        table = Table(title="MCP 工具列表")
        table.add_column("名称", style="cyan", width=25)
        table.add_column("作者", style="magenta", width=15)
        table.add_column("类别", style="green", width=12)
        if show_package:
            table.add_column("包名", style="yellow", width=30)
        table.add_column("描述", style="white", width=40)
        table.add_column("API", style="red", width=5)
        
        # 添加工具信息
        for tool in tools:
            api_status = "🔑" if tool.requires_api_key else "🆓"
            
            # 截断过长的内容
            name = tool.name[:23] + "..." if len(tool.name) > 25 else tool.name
            desc = tool.description[:38] + "..." if len(tool.description) > 40 else tool.description
            
            row_data = [
                name,
                tool.author,
                tool.category.split('\n')[0],  # 只取第一行类别
            ]
            
            if show_package:
                package = tool.package_name or "N/A"
                row_data.append(package[:28] + "..." if len(package) > 30 else package)
            
            row_data.extend([desc, api_status])
            table.add_row(*row_data)
        
        console.print(table)
        
        # 显示使用提示
        rprint("\n[bold yellow]💡 使用说明:[/bold yellow]")
        rprint("  • 测试工具: [cyan]batch-mcp test-package <包名>[/cyan]")
        rprint("  • 搜索工具: [cyan]batch-mcp list-tools --search <关键词>[/cyan]")
        rprint("  • 按类别筛选: [cyan]batch-mcp list-tools --category <类别>[/cyan]")
        rprint("  • 显示包名: [cyan]batch-mcp list-tools --show-package[/cyan]")
        
        # 显示统计信息
        api_count = sum(1 for tool in tools if tool.requires_api_key)
        rprint(f"\n[dim]📊 统计: {len(tools)} 个工具，{api_count} 个需要API密钥[/dim]")
        
    except Exception as e:
        rprint(f"[red]❌ 加载工具列表失败: {e}[/red]")
        raise typer.Exit(1)

@app.command("init-env")
def init_environment():
    """初始化测试环境"""
    rprint("[bold green]🔧 初始化测试环境...[/bold green]")
    
    try:
        # 1. 检查环境文件
        env_file = project_root / ".env"
        if not env_file.exists():
            rprint("[red]❌ 未找到 .env 文件[/red]")
            rprint("[yellow]💡 请确保项目根目录下有 .env 配置文件[/yellow]")
            raise typer.Exit(1)
        
        rprint("[green]✅ 找到 .env 配置文件[/green]")
        
        # 2. 检查平台环境
        from src.core.simple_mcp_deployer import detect_simple_platform
        platform_info = detect_simple_platform()
        
        rprint(f"[blue]🖥️ 平台信息:[/blue]")
        rprint(f"  • 操作系统: {platform_info['system']} ({platform_info['architecture']})")
        rprint(f"  • Python版本: {platform_info['python_version']}")
        
        # 3. 检查Node.js环境
        if platform_info['node_available']:
            rprint("[green]✅ Node.js/NPX 环境可用[/green]")
            rprint(f"  • NPX路径: {platform_info['npx_path']}")
            if 'npx_version' in platform_info:
                rprint(f"  • NPX版本: {platform_info['npx_version']}")
        else:
            rprint("[red]❌ Node.js/NPX 环境不可用[/red]")
            rprint("[yellow]⚠️ 请安装 Node.js 以使用 MCP 工具部署功能[/yellow]")
            rprint("[blue]💡 下载地址: https://nodejs.org/[/blue]")
        
        # 4. 检查数据文件
        csv_file = project_root / "data" / "mcp.csv"
        if csv_file.exists():
            rprint("[green]✅ 找到 MCP 工具数据文件[/green]")
            
            # 快速测试CSV解析
            try:
                parser = get_mcp_parser()
                tools = parser.get_all_tools()
                rprint(f"  • 可用工具数: {len(tools)}")
                
                api_free_count = sum(1 for t in tools if not t.requires_api_key)
                rprint(f"  • 免API密钥工具: {api_free_count}")
                rprint(f"  • 需API密钥工具: {len(tools) - api_free_count}")
                
            except Exception as e:
                rprint(f"[yellow]⚠️ CSV数据解析异常: {e}[/yellow]")
        else:
            rprint("[red]❌ 未找到 MCP 工具数据文件[/red]")
            rprint(f"[yellow]⚠️ 预期位置: {csv_file}[/yellow]")
        
        # 5. 检查依赖包
        rprint("[blue]📦 检查Python依赖...[/blue]")
        required_packages = ['typer', 'rich', 'pandas', 'pydantic']
        
        for package in required_packages:
            try:
                __import__(package)
                rprint(f"  • {package}: [green]✅ 已安装[/green]")
            except ImportError:
                rprint(f"  • {package}: [red]❌ 未安装[/red]")
        
        # 6. 环境总结
        rprint("\n[bold blue]📋 环境检查总结:[/bold blue]")
        
        if platform_info['node_available'] and csv_file.exists():
            rprint("[green]✅ 环境配置完整，可以正常使用所有功能[/green]")
            rprint("\n[bold yellow]🚀 推荐操作:[/bold yellow]")
            rprint("  • 查看工具列表: [cyan]uv run python -m src.main list-tools --limit 10[/cyan]")
            rprint("  • 测试简单工具: [cyan]uv run python -m src.main test-package <包名>[/cyan]")
            rprint("  • 搜索工具: [cyan]uv run python -m src.main list-tools --search <关键词>[/cyan]")
        else:
            rprint("[yellow]⚠️ 环境存在问题，部分功能可能无法正常使用[/yellow]")
            if not platform_info['node_available']:
                rprint("[red]  × 需要安装 Node.js[/red]")
            if not csv_file.exists():
                rprint("[red]  × 缺少 MCP 工具数据文件[/red]")
        
        rprint("[green]✅ 环境检查完成[/green]")
        
    except Exception as e:
        rprint(f"[red]❌ 环境检查失败: {e}[/red]")
        raise typer.Exit(1)

@app.command("generate-report")
def generate_report(
    result_dir: Path = typer.Option("data/test_results", "--dir", "-d", help="测试结果目录"),
    output_format: str = typer.Option("html", "--format", "-f", help="报告格式 (html/json/csv)")
):
    """生成测试报告"""
    rprint(f"[bold green]📊 生成测试报告:[/bold green] {result_dir}")
    
    if not result_dir.exists():
        rprint(f"[red]❌ 结果目录不存在:[/red] {result_dir}")
        raise typer.Exit(1)
    
    # TODO: 实现报告生成逻辑
    rprint("[yellow]⚠️ 功能正在开发中...[/yellow]")

def _run_basic_test(server_info, timeout: int = 10) -> tuple[bool, List[TestResult]]:
    """执行基础连通性测试并尝试调用工具"""
    test_results = []
    overall_success = True
    
    try:
        # 1. 基础通信测试
        rprint("[blue]🧪 执行基础连通性测试...[/blue]")
        start_time = time.time()
        
        tools_request = {
            "jsonrpc": "2.0",
            "id": 999,
            "method": "tools/list",
            "params": {}
        }
        
        test_result = server_info.communicator.send_request(tools_request, timeout=timeout)
        communication_duration = time.time() - start_time
        
        if not test_result['success']:
            error_msg = test_result.get('error', '未知错误')
            rprint(f"[yellow]⚠️ MCP通信测试异常: {error_msg}[/yellow]")
            test_results.append(TestResult(
                test_name="MCP协议通信测试",
                success=False,
                duration=communication_duration,
                error_message=error_msg
            ))
            overall_success = False
            return overall_success, test_results
        
        rprint("[green]✅ MCP通信测试成功！[/green]")
        rprint(f"[green]📡 协议状态: 正常通信[/green]")
        
        test_results.append(TestResult(
            test_name="MCP协议通信测试",
            success=True,
            duration=communication_duration,
            output="成功获取工具列表"
        ))
        
        # 2. 尝试调用第一个可用工具（如果有的话）
        available_tools = server_info.available_tools
        if available_tools and len(available_tools) > 0:
            first_tool = available_tools[0]
            tool_name = first_tool.get('name')
            
            rprint(f"[blue]🧪 尝试调用工具: {tool_name}[/blue]")
            
            tool_start_time = time.time()
            
            # 构建简单的工具调用请求
            tool_call_request = {
                "jsonrpc": "2.0",
                "id": 1000,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": {}  # 大多数工具支持空参数
                }
            }
            
            tool_result = server_info.communicator.send_request(tool_call_request, timeout=timeout)
            tool_duration = time.time() - tool_start_time
            
            if tool_result['success']:
                rprint(f"[green]✅ 工具调用成功: {tool_name}[/green]")
                # 显示结果的一部分
                output_summary = "工具调用成功"
                if 'data' in tool_result:
                    result_data = tool_result['data']
                    if isinstance(result_data, dict) and 'result' in result_data:
                        result_content = str(result_data['result'])[:200]
                        rprint(f"[dim]📄 工具输出: {result_content}...[/dim]")
                        output_summary = f"输出: {result_content[:100]}..."
                
                test_results.append(TestResult(
                    test_name=f"工具调用测试: {tool_name}",
                    success=True,
                    duration=tool_duration,
                    output=output_summary
                ))
            else:
                error_msg = tool_result.get('error', '调用失败')
                rprint(f"[yellow]⚠️ 工具调用测试: {error_msg}[/yellow]")
                rprint("[dim]💡 这可能是正常的，某些工具需要特定参数[/dim]")
                
                test_results.append(TestResult(
                    test_name=f"工具调用测试: {tool_name}",
                    success=False,
                    duration=tool_duration,
                    error_message=error_msg
                ))
                # 工具调用失败不影响整体成功状态，因为可能需要特定参数
        else:
            rprint("[yellow]⚠️ 没有可用工具进行测试[/yellow]")
            test_results.append(TestResult(
                test_name="工具可用性检查",
                success=False,
                duration=0.0,
                error_message="没有可用工具"
            ))
            
        rprint(f"[green]⏱️ 运行时间: {time.time() - server_info.start_time:.2f}秒[/green]")
        return overall_success, test_results
        
    except Exception as e:
        rprint(f"[red]❌ 基础测试失败: {e}[/red]")
        test_results.append(TestResult(
            test_name="基础测试异常",
            success=False,
            duration=0.0,
            error_message=str(e)
        ))
        return False, test_results

async def _run_smart_test(tool_info: MCPToolInfo, server_info, verbose: bool = False) -> tuple[bool, list[TestResult]]:
    """执行AI智能测试"""
    try:
        # 获取智能代理
        test_generator = get_test_generator()
        validation_agent = get_validation_agent()

        rprint("[blue]🎯 生成智能测试用例...[/blue]")

        # 生成测试用例
        test_cases = test_generator.generate_test_cases(tool_info, server_info.available_tools)

        if not test_cases:
            rprint("[yellow]⚠️ 未生成任何测试用例，使用基础测试[/yellow]")
            success, base_results = _run_basic_test(server_info)
            return success, base_results

        rprint(f"[green]✅ 生成了 {len(test_cases)} 个测试用例[/green]")

        # 执行智能验证
        rprint("[blue]🚀 执行智能验证测试...[/blue]")

        # 创建异步客户端（基于已有通信器）
        from src.core.async_mcp_client import AsyncMCPClient
        mcp_client = AsyncMCPClient(server_info.communicator)

        ai_results = await validation_agent.execute_test_suite(test_cases, mcp_client)

        # 计算成功率
        passed = sum(1 for result in ai_results if result.status.value == "pass")
        success_rate = passed / len(ai_results) if ai_results else 0

        rprint(f"[green]📊 智能测试完成: {passed}/{len(ai_results)} 通过 ({success_rate:.1%})[/green]")

        # 转换为报告可用的 TestResult 列表
        report_results: list[TestResult] = []
        for r in ai_results:
            report_results.append(TestResult(
                test_name=r.test_case.name,
                success=(r.status.value == "pass"),
                duration=r.execution_time,
                error_message=r.error_message,
                output=(r.analysis or None)
            ))

        return (success_rate >= 0.7), report_results  # 70%以上成功率视为通过

    except Exception as e:
        rprint(f"[red]❌ 智能测试失败: {e}[/red]")
        if verbose:
            import traceback
            rprint(f"[dim]{traceback.format_exc()}[/dim]")

        # 回退到基础测试
        rprint("[yellow]⚠️ 回退到基础测试模式[/yellow]")
        success, results = _run_basic_test(server_info)
        return success, results

@app.callback()
def main(
    version: bool = typer.Option(False, "--version", help="显示版本信息")
):
    """
    Batch MCP Testing Framework
    
    动态 MCP 工具部署和测试框架，支持根据 URL 自动部署 MCP 工具并进行智能测试。
    
    使用方法:
    - 子命令: uv run python -m src test-url <URL>
    - 批量测试: uv run python -m src batch-test --input data/test.csv
    """
    if version:
        rprint("[bold green]Batch MCP Testing Framework v1.0.0[/bold green]")
        rprint("基于 AgentScope 和 Model Context Protocol")
        raise typer.Exit()

if __name__ == "__main__":
    app()

# 支持 python -m src.main 调用
def main():
    app()

if __name__ == "__main__":
    main()
else:
    # 如果作为模块被调用，也要支持执行
    import sys
    if len(sys.argv) > 0 and sys.argv[0].endswith('src.main'):
        main()
