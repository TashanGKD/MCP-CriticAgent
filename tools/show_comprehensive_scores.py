#!/usr/bin/env python3
"""
展示MCP工具综合评分报告
综合评分 = (测试成功率 * 1 + GitHub评估分数 * 2) / 3

遵循Linus的"好品味"原则：简洁、实用、高效
"""

import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.evaluator import calculate_comprehensive_score_from_tests

def main():
    # 加载环境变量
    load_dotenv()
    
    console = Console()
    
    # 检查环境变量
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        console.print("[red]❌ 缺少Supabase数据库配置[/red]")
        console.print("[yellow]请设置 SUPABASE_URL 和 SUPABASE_SERVICE_ROLE_KEY 环境变量[/yellow]")
        return
    
    console.print(Panel.fit("[bold blue]MCP工具综合评分报告[/bold blue]", border_style="blue"))
    
    # 从数据库动态获取所有有评分的工具
    try:
        from supabase import create_client
        client = create_client(supabase_url, supabase_key)
        
        # 查询所有有评分的不同工具
        result = client.table('mcp_test_results')\
            .select('tool_identifier, tool_name, final_score')\
            .not_.is_('final_score', 'null')\
            .execute()
        
        if not result.data:
            console.print("[red]❌ 数据库中没有找到测试数据[/red]")
            return
        
        # 去重获取唯一工具
        tools = {}
        for record in result.data:
            identifier = record['tool_identifier']
            if identifier not in tools:
                tools[identifier] = record['tool_name']
        
        test_urls = list(tools.keys())
        console.print(f"[green]✅ 找到 {len(test_urls)} 个有评分的MCP工具[/green]\n")
        
    except Exception as e:
        console.print(f"[red]❌ 数据库连接失败: {e}[/red]")
        return
    
    # 创建表格
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    table.add_column("工具名称", style="cyan", no_wrap=True, width=25)
    table.add_column("测试成功率", justify="center", style="green", width=12)
    table.add_column("GitHub评分", justify="center", style="blue", width=12)
    table.add_column("综合评分", justify="center", style="bold yellow", width=12)
    table.add_column("可持续性", justify="center", style="dim", width=12)
    table.add_column("受欢迎度", justify="center", style="dim", width=12)
    table.add_column("测试记录", justify="center", style="dim", width=12)
    
    total_tools = 0
    successful_tools = 0
    
    for github_url in test_urls:
        console.print(f"[dim]正在分析: {github_url}[/dim]")
        
        result = calculate_comprehensive_score_from_tests(github_url)
        
        if result and result.get('test_count', 0) > 0:
            total_tools += 1
            
            # 使用数据库中的工具名称
            tool_name = tools.get(github_url, github_url.split('/')[-1].replace('-mcp', '').replace('-', ' ').title())
            if len(tool_name) > 22:
                tool_name = tool_name[:19] + "..."
            
            success_rate = result.get('success_rate', 0)
            github_score = result.get('github_evaluation_score', 0)
            comprehensive_score = result.get('comprehensive_score', 0)
            sustainability_score = result.get('sustainability_score', 0)
            popularity_score = result.get('popularity_score', 0)
            test_count = result.get('test_count', 0)
            successful_tests = result.get('successful_tests', 0)
            
            # 判断工具质量
            if comprehensive_score >= 80:
                successful_tools += 1
                score_color = "bold green"
            elif comprehensive_score >= 60:
                score_color = "yellow"
            else:
                score_color = "red"
            
            # 格式化显示
            success_rate_str = f"{success_rate}%" if success_rate is not None else "N/A"
            github_score_str = str(github_score) if github_score is not None else "N/A"
            comprehensive_score_str = f"[{score_color}]{comprehensive_score}[/{score_color}]"
            sustainability_str = str(sustainability_score) if sustainability_score is not None else "N/A"
            popularity_str = str(popularity_score) if popularity_score is not None else "N/A"
            test_record_str = f"{successful_tests}/{test_count}"
            
            table.add_row(
                tool_name,
                success_rate_str,
                github_score_str,
                comprehensive_score_str,
                sustainability_str,
                popularity_str,
                test_record_str
            )
        else:
            tool_name = tools.get(github_url, github_url.split('/')[-1].replace('-mcp', '').replace('-', ' ').title())
            if len(tool_name) > 22:
                tool_name = tool_name[:19] + "..."
            table.add_row(
                tool_name,
                "[dim]无数据[/dim]",
                "[dim]无数据[/dim]",
                "[dim red]无数据[/dim red]",
                "[dim]无数据[/dim]",
                "[dim]无数据[/dim]",
                "[dim]0/0[/dim]"
            )
    
    console.print(table)
    
    # 总结信息
    console.print(f"\n[bold]📊 总结[/bold]")
    console.print(f"分析工具数: {len(test_urls)}")
    console.print(f"有测试数据: {total_tools}")
    console.print(f"高质量工具(≥80分): {successful_tools}")
    
    if total_tools > 0:
        success_ratio = (successful_tools / total_tools) * 100
        console.print(f"质量达标率: {success_ratio:.1f}%")
    
    # 显示计算公式
    console.print(f"\n[dim]📐 综合评分公式: (测试成功率×1 + GitHub评估分数×2) ÷ 3[/dim]")
    console.print(f"[dim]🎯 评分标准: ≥80分优秀, 60-79分良好, <60分需改进[/dim]")

if __name__ == "__main__":
    main()
