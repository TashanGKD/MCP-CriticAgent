#!/usr/bin/env python3
"""
数据库迁移和初始化工具

用于初始化Supabase数据库和运行数据迁移

作者: AI Assistant
日期: 2025-08-16
版本: 1.0.0
"""

import os
import asyncio
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich import print as rprint

# 加载 .env 文件
def load_env_file():
    """加载 .env 文件"""
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# 在导入之前加载环境变量
load_env_file()

# 尝试导入Supabase客户端
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    rprint("[red]❌ Supabase库未安装，请运行: uv add supabase[/red]")

app = typer.Typer(name="db-migrate", help="数据库迁移工具")
console = Console()

def get_supabase_client() -> Optional[Client]:
    """获取Supabase客户端"""
    if not SUPABASE_AVAILABLE:
        return None
    
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not service_key:
        rprint("[red]❌ 请在.env文件中配置SUPABASE_URL和SUPABASE_SERVICE_ROLE_KEY[/red]")
        return None
    
    return create_client(url, service_key)

@app.command("init")
def init_database():
    """初始化数据库结构"""
    rprint("[bold blue]🚀 初始化数据库结构...[/bold blue]")
    
    client = get_supabase_client()
    if not client:
        return
    
    # 读取SQL初始化脚本
    sql_file = Path(__file__).parent.parent.parent / "database" / "supabase_init.sql"
    
    if not sql_file.exists():
        rprint(f"[red]❌ 找不到SQL初始化文件: {sql_file}[/red]")
        raise typer.Exit(1)
    
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句（简单处理）
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        rprint(f"[blue]📋 准备执行 {len(statements)} 条SQL语句...[/blue]")
        
        # 执行SQL语句
        for i, statement in enumerate(statements, 1):
            try:
                if statement.upper().startswith(('CREATE', 'ALTER', 'INSERT')):
                    # 对于DDL语句，使用rpc调用
                    result = client.rpc('exec_sql', {'sql': statement}).execute()
                    rprint(f"[green]✅ ({i}/{len(statements)}) 执行成功[/green]")
                else:
                    rprint(f"[yellow]⏭️ ({i}/{len(statements)}) 跳过注释或空语句[/yellow]")
            except Exception as e:
                rprint(f"[yellow]⚠️ ({i}/{len(statements)}) 语句执行警告: {str(e)[:100]}...[/yellow]")
                # 继续执行其他语句
                continue
        
        rprint("[bold green]🎉 数据库初始化完成！[/bold green]")
        
    except Exception as e:
        rprint(f"[red]❌ 数据库初始化失败: {e}[/red]")
        raise typer.Exit(1)

@app.command("test")
def test_connection():
    """测试数据库连接"""
    rprint("[bold blue]🔍 测试数据库连接...[/bold blue]")
    
    client = get_supabase_client()
    if not client:
        return
    
    try:
        # 测试基本查询
        result = client.table('mcp_tools').select('count').limit(1).execute()
        rprint("[green]✅ 数据库连接成功![/green]")
        
        # 测试表是否存在
        tables_to_check = [
            'mcp_tools', 'test_reports', 'deployments', 
            'test_executions', 'available_tools', 
            'quality_metrics', 'performance_metrics'
        ]
        
        for table in tables_to_check:
            try:
                result = client.table(table).select('count').limit(1).execute()
                rprint(f"[green]✅ 表 {table} 存在[/green]")
            except Exception as e:
                rprint(f"[red]❌ 表 {table} 不存在或有问题: {e}[/red]")
        
    except Exception as e:
        rprint(f"[red]❌ 数据库连接失败: {e}[/red]")
        raise typer.Exit(1)

@app.command("seed")
def seed_data():
    """填充示例数据"""
    rprint("[bold blue]🌱 填充示例数据...[/bold blue]")
    
    client = get_supabase_client()
    if not client:
        return
    
    try:
        # 插入示例MCP工具数据
        sample_tools = [
            {
                'name': 'Context7 MCP',
                'author': 'upstash',
                'github_url': 'https://github.com/upstash/context7',
                'package_name': '@upstash/context7-mcp',
                'category': '开发工具',
                'description': '用于Context7的MCP服务器，提供最新、版本特定的库文档和代码示例',
                'language': 'Node.js',
                'requires_api_key': False,
                'stars': 150
            },
            {
                'name': 'GitHub MCP',
                'author': 'modelcontextprotocol',
                'github_url': 'https://github.com/modelcontextprotocol/servers',
                'package_name': 'github-mcp-server',
                'category': '开发工具',
                'description': 'GitHub集成的MCP服务器',
                'language': 'Python',
                'requires_api_key': True,
                'api_requirements': ['GITHUB_TOKEN'],
                'stars': 200
            }
        ]
        
        for tool_data in sample_tools:
            try:
                # 检查是否已存在
                existing = client.table('mcp_tools').select('tool_id').eq('github_url', tool_data['github_url']).execute()
                
                if not existing.data:
                    result = client.table('mcp_tools').insert(tool_data).execute()
                    rprint(f"[green]✅ 插入工具: {tool_data['name']}[/green]")
                else:
                    rprint(f"[yellow]⏭️ 工具已存在: {tool_data['name']}[/yellow]")
            except Exception as e:
                rprint(f"[red]❌ 插入工具失败 {tool_data['name']}: {e}[/red]")
        
        rprint("[bold green]🎉 示例数据填充完成！[/bold green]")
        
    except Exception as e:
        rprint(f"[red]❌ 示例数据填充失败: {e}[/red]")
        raise typer.Exit(1)

@app.command("clean")
def clean_data(
    confirm: bool = typer.Option(False, "--confirm", help="确认删除所有数据")
):
    """清理测试数据"""
    if not confirm:
        rprint("[yellow]⚠️ 此操作将删除所有测试数据！[/yellow]")
        rprint("[yellow]请使用 --confirm 参数确认删除[/yellow]")
        return
    
    rprint("[bold red]🧹 清理测试数据...[/bold red]")
    
    client = get_supabase_client()
    if not client:
        return
    
    try:
        # 按依赖顺序删除数据
        tables_to_clean = [
            'performance_metrics',
            'quality_metrics', 
            'available_tools',
            'test_executions',
            'deployments',
            'test_reports'
        ]
        
        for table in tables_to_clean:
            try:
                result = client.table(table).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
                rprint(f"[green]✅ 清理表 {table}[/green]")
            except Exception as e:
                rprint(f"[yellow]⚠️ 清理表 {table} 失败: {e}[/yellow]")
        
        rprint("[bold green]🎉 测试数据清理完成！[/bold green]")
        
    except Exception as e:
        rprint(f"[red]❌ 数据清理失败: {e}[/red]")
        raise typer.Exit(1)

@app.command("status")
def show_status():
    """显示数据库状态"""
    rprint("[bold blue]📊 数据库状态概览...[/bold blue]")
    
    client = get_supabase_client()
    if not client:
        return
    
    try:
        # 统计各表记录数
        tables_to_check = {
            'mcp_tools': 'MCP工具',
            'test_reports': '测试报告',
            'deployments': '部署记录',
            'test_executions': '测试执行',
            'available_tools': '可用工具',
            'quality_metrics': '质量指标',
            'performance_metrics': '性能指标'
        }
        
        console.print("\n[bold]📋 数据库表统计:[/bold]")
        
        for table, description in tables_to_check.items():
            try:
                result = client.table(table).select('*', count='exact').execute()
                count = result.count
                console.print(f"  • {description} ({table}): [cyan]{count}[/cyan] 条记录")
            except Exception as e:
                console.print(f"  • {description} ({table}): [red]查询失败[/red]")
        
        # 显示最近的测试报告
        try:
            recent_reports = client.table('test_reports_overview').select('*').order('created_at', desc=True).limit(5).execute()
            
            if recent_reports.data:
                console.print("\n[bold]🕒 最近的测试报告:[/bold]")
                for report in recent_reports.data:
                    status_color = "green" if report['overall_status'] == 'success' else "red"
                    console.print(f"  • [{status_color}]{report['overall_status']}[/{status_color}] {report['tool_name']} - {report['created_at'][:19]}")
        except Exception as e:
            console.print(f"\n[red]❌ 无法获取最近报告: {e}[/red]")
        
    except Exception as e:
        rprint(f"[red]❌ 获取数据库状态失败: {e}[/red]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
