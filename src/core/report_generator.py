#!/usr/bin/env python3
"""
MCP 测试报告生成器

负责生成和管理 MCP 工具测试的各种报告格式，包括 JSON、HTML、CSV 等。
支持单个测试报告和批量测试汇总报告。

作者: AI Assistant
日期: 2025-08-15
版本: 1.0.0
"""

import json
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
import csv

# 导入工具信息类型
try:
    from src.utils.csv_parser import MCPToolInfo
except ImportError:
    # 简化版本，用于测试
    @dataclass
    class MCPToolInfo:
        name: str
        author: str
        package_name: str
        category: str
        description: str
        requires_api_key: bool
        api_requirements: List[str]

@dataclass
class TestResult:
    """单个测试结果"""
    test_name: str
    success: bool
    duration: float
    error_message: Optional[str] = None
    output: Optional[str] = None

@dataclass
class MCPTestReport:
    """完整的 MCP 测试报告"""
    test_url: str
    test_time: datetime
    tool_info: MCPToolInfo
    deployment_success: bool
    communication_success: bool
    available_tools_count: int
    available_tools: List[Dict[str, Any]]
    test_duration_seconds: float
    platform_info: str
    process_pid: Optional[int]
    server_id: Optional[str]
    test_results: List[TestResult] = None
    error_messages: List[str] = None
    
    def __post_init__(self):
        if self.test_results is None:
            self.test_results = []
        if self.error_messages is None:
            self.error_messages = []

class MCPReportGenerator:
    """MCP 测试报告生成器"""
    
    def __init__(self, output_dir: Union[str, Path] = "data/test_results"):
        """
        初始化报告生成器
        
        Args:
            output_dir: 报告输出目录
        """
        self.output_dir = Path(output_dir)
        self.reports_dir = self.output_dir / "reports"
        self.logs_dir = self.output_dir / "logs"
        self.summaries_dir = self.output_dir / "summaries"
        
        # 确保目录存在
        for dir_path in [self.reports_dir, self.logs_dir, self.summaries_dir]:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                # 使用内置打印，避免额外依赖
                print(f"[WARN] 创建目录失败: {dir_path} -> {e}")
    
    def generate_single_test_report(self, 
                                  url: str,
                                  tool_info: MCPToolInfo,
                                  server_info,
                                  test_success: bool,
                                  duration: float,
                                  test_results: List[TestResult] = None,
                                  error_messages: List[str] = None) -> MCPTestReport:
        """
        生成单个测试的报告对象
        
        Args:
            url: 测试的 URL
            tool_info: 工具信息
            server_info: 服务器信息
            test_success: 测试是否成功
            duration: 测试持续时间
            test_results: 详细测试结果列表
            error_messages: 错误消息列表
            
        Returns:
            MCPTestReport: 测试报告对象
        """
        report = MCPTestReport(
            test_url=url,
            test_time=datetime.now(),
            tool_info=tool_info,
            deployment_success=server_info is not None,
            communication_success=test_success,
            available_tools_count=len(server_info.available_tools) if server_info else 0,
            available_tools=[
                {
                    "name": tool.get("name", "unknown"),
                    "description": tool.get("description", "")[:100] + "..." 
                    if len(tool.get("description", "")) > 100 
                    else tool.get("description", "")
                }
                for tool in (server_info.available_tools if server_info else [])
            ],
            test_duration_seconds=duration,
            platform_info=platform.system(),
            process_pid=server_info.process.pid if server_info else None,
            server_id=server_info.server_id if server_info else None,
            test_results=test_results or [],
            error_messages=error_messages or []
        )
        
        return report
    
    def save_json_report(self, report: MCPTestReport) -> Path:
        """
        保存 JSON 格式报告
        
        Args:
            report: 测试报告对象
            
        Returns:
            Path: 保存的文件路径
        """
        timestamp = report.test_time.strftime('%Y%m%d_%H%M%S')
        json_filename = f"mcp_test_{timestamp}.json"
        json_path = self.reports_dir / json_filename
        
        # 转换为可序列化的字典
        report_dict = {
            "test_url": report.test_url,
            "test_time": report.test_time.isoformat(),
            "tool_info": {
                "name": report.tool_info.name,
                "author": report.tool_info.author,
                "package_name": report.tool_info.package_name,
                "category": report.tool_info.category,
                "description": report.tool_info.description[:200] + "..." 
                if len(report.tool_info.description) > 200 
                else report.tool_info.description,
                "requires_api_key": report.tool_info.requires_api_key,
                "api_requirements": report.tool_info.api_requirements
            },
            "deployment_success": report.deployment_success,
            "communication_success": report.communication_success,
            "available_tools_count": report.available_tools_count,
            "available_tools": report.available_tools,
            "test_duration_seconds": report.test_duration_seconds,
            "platform": report.platform_info,
            "process_pid": report.process_pid,
            "server_id": report.server_id,
            "test_results": [
                {
                    "test_name": test.test_name,
                    "success": test.success,
                    "duration": test.duration,
                    "error_message": test.error_message,
                    "output": test.output
                }
                for test in report.test_results
            ],
            "error_messages": report.error_messages,
            "summary": {
                "overall_success": report.deployment_success and report.communication_success,
                "test_count": len(report.test_results),
                "passed_tests": sum(1 for test in report.test_results if test.success),
                "failed_tests": sum(1 for test in report.test_results if not test.success),
                "success_rate": (sum(1 for test in report.test_results if test.success) / len(report.test_results)) 
                if report.test_results else 0.0
            }
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
        
        return json_path
    
    def save_html_report(self, report: MCPTestReport) -> Path:
        """
        保存 HTML 格式报告
        
        Args:
            report: 测试报告对象
            
        Returns:
            Path: 保存的文件路径
        """
        timestamp = report.test_time.strftime('%Y%m%d_%H%M%S')
        html_filename = f"mcp_test_{timestamp}.html"
        html_path = self.reports_dir / html_filename
        
        # 计算成功率
        success_rate = 0.0
        if report.test_results:
            passed = sum(1 for test in report.test_results if test.success)
            success_rate = passed / len(report.test_results)
        
        # 生成工具卡片
        tools_cards = ""
        for tool in report.available_tools:
            tools_cards += f'''
            <div class="tool-card">
                <strong>{tool["name"]}</strong>
                <br>
                <small>{tool["description"]}</small>
            </div>
            '''
        
        # 生成测试结果表格
        test_results_table = ""
        if report.test_results:
            test_results_table = '''
            <div class="section">
                <h2>🧪 详细测试结果</h2>
                <table>
                    <tr>
                        <th>测试名称</th>
                        <th>结果</th>
                        <th>耗时</th>
                        <th>错误信息</th>
                    </tr>
            '''
            for test in report.test_results:
                status_class = "success" if test.success else "failure"
                status_icon = "✅" if test.success else "❌"
                error_msg = test.error_message or "-"
                
                test_results_table += f'''
                <tr>
                    <td>{test.test_name}</td>
                    <td class="{status_class}">{status_icon}</td>
                    <td>{test.duration:.2f}s</td>
                    <td>{error_msg[:50]}{'...' if len(error_msg) > 50 else ''}</td>
                </tr>
                '''
            
            test_results_table += '''
                </table>
            </div>
            '''
        
        # 生成错误信息部分
        error_section = ""
        if report.error_messages:
            error_section = '''
            <div class="section">
                <h2>⚠️ 错误信息</h2>
                <ul>
            '''
            for error in report.error_messages:
                error_section += f'<li>{error}</li>'
            error_section += '''
                </ul>
            </div>
            '''
        
        html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP 工具测试报告 - {report.tool_info.name}</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            margin: 20px; 
            line-height: 1.6; 
            background-color: #f5f5f5;
        }}
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 10px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 30px; 
            text-align: center;
        }}
        .header h1 {{ margin: 0; font-size: 2.5em; }}
        .header p {{ margin: 10px 0 0 0; font-size: 1.2em; opacity: 0.9; }}
        .section {{ 
            margin: 0; 
            padding: 25px; 
            border-bottom: 1px solid #eee; 
        }}
        .section:last-child {{ border-bottom: none; }}
        .success {{ color: #28a745; font-weight: bold; }} 
        .failure {{ color: #dc3545; font-weight: bold; }}
        .warning {{ color: #ffc107; font-weight: bold; }}
        .tools-list {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 15px; 
            margin-top: 15px;
        }}
        .tool-card {{ 
            padding: 15px; 
            background: #f8f9fa; 
            border-radius: 8px; 
            border-left: 4px solid #007bff; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 15px;
            background: white;
        }} 
        th, td {{ 
            padding: 12px; 
            text-align: left; 
            border-bottom: 1px solid #ddd; 
        }}
        th {{ 
            background-color: #f8f9fa; 
            font-weight: 600;
            color: #495057;
        }}
        tr:hover {{ background-color: #f8f9fa; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #dee2e6;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            margin: 5px 0;
        }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background-color: #e9ecef;
            border-radius: 10px;
            margin: 10px 0;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
            transition: width 0.3s ease;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 MCP 工具测试报告</h1>
            <p><strong>{report.tool_info.name}</strong> - {report.test_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="section">
            <h2>📊 测试概览</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div>部署状态</div>
                    <div class="stat-number {'success' if report.deployment_success else 'failure'}">
                        {'✅' if report.deployment_success else '❌'}
                    </div>
                    <div>{'成功' if report.deployment_success else '失败'}</div>
                </div>
                <div class="stat-card">
                    <div>通信状态</div>
                    <div class="stat-number {'success' if report.communication_success else 'failure'}">
                        {'✅' if report.communication_success else '❌'}
                    </div>
                    <div>{'正常' if report.communication_success else '异常'}</div>
                </div>
                <div class="stat-card">
                    <div>可用工具</div>
                    <div class="stat-number">{report.available_tools_count}</div>
                    <div>个工具</div>
                </div>
                <div class="stat-card">
                    <div>测试时长</div>
                    <div class="stat-number">{report.test_duration_seconds:.1f}</div>
                    <div>秒</div>
                </div>
            </div>
            
            <table style="margin-top: 20px;">
                <tr><th>测试 URL</th><td>{report.test_url}</td></tr>
                <tr><th>工具名称</th><td>{report.tool_info.name}</td></tr>
                <tr><th>作者</th><td>{report.tool_info.author}</td></tr>
                <tr><th>包名</th><td>{report.tool_info.package_name}</td></tr>
                <tr><th>类别</th><td>{report.tool_info.category}</td></tr>
                <tr><th>平台</th><td>{report.platform_info}</td></tr>
                <tr><th>进程 PID</th><td>{report.process_pid or 'N/A'}</td></tr>
                <tr><th>服务器 ID</th><td>{report.server_id or 'N/A'}</td></tr>
            </table>
        </div>
        
        <div class="section">
            <h2>🛠️ 可用工具 ({report.available_tools_count} 个)</h2>
            <div class="tools-list">
                {tools_cards}
            </div>
        </div>
        
        {test_results_table}
        
        <div class="section">
            <h2>📝 工具描述</h2>
            <p>{report.tool_info.description}</p>
            <p><strong>API密钥需求:</strong> 
                {'🔑 需要 (' + ', '.join(report.tool_info.api_requirements) + ')' if report.tool_info.requires_api_key else '🆓 无需'}
            </p>
        </div>
        
        {error_section}
        
        <div class="section">
            <h2>📈 测试统计</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div>总测试数</div>
                    <div class="stat-number">{len(report.test_results)}</div>
                </div>
                <div class="stat-card">
                    <div>通过测试</div>
                    <div class="stat-number success">{sum(1 for test in report.test_results if test.success)}</div>
                </div>
                <div class="stat-card">
                    <div>失败测试</div>
                    <div class="stat-number failure">{sum(1 for test in report.test_results if not test.success)}</div>
                </div>
                <div class="stat-card">
                    <div>成功率</div>
                    <div class="stat-number">{success_rate:.1%}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {success_rate * 100}%"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_path
    
    def save_csv_summary(self, reports: List[MCPTestReport]) -> Path:
        """
        保存 CSV 格式的测试摘要
        
        Args:
            reports: 测试报告列表
            
        Returns:
            Path: 保存的文件路径
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f"mcp_test_summary_{timestamp}.csv"
        csv_path = self.summaries_dir / csv_filename
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入表头
            writer.writerow([
                '测试时间', 'URL', '工具名称', '作者', '包名', '类别',
                '部署成功', '通信成功', '可用工具数', '测试时长(秒)',
                '测试总数', '通过测试', '失败测试', '成功率', '平台'
            ])
            
            # 写入数据
            for report in reports:
                passed_tests = sum(1 for test in report.test_results if test.success)
                total_tests = len(report.test_results)
                success_rate = passed_tests / total_tests if total_tests > 0 else 0.0
                
                writer.writerow([
                    report.test_time.strftime('%Y-%m-%d %H:%M:%S'),
                    report.test_url,
                    report.tool_info.name,
                    report.tool_info.author,
                    report.tool_info.package_name,
                    report.tool_info.category,
                    'Yes' if report.deployment_success else 'No',
                    'Yes' if report.communication_success else 'No',
                    report.available_tools_count,
                    f"{report.test_duration_seconds:.2f}",
                    total_tests,
                    passed_tests,
                    total_tests - passed_tests,
                    f"{success_rate:.1%}",
                    report.platform_info
                ])
        
        return csv_path
    
    def generate_complete_report(self,
                               url: str,
                               tool_info: MCPToolInfo,
                               server_info,
                               test_success: bool,
                               duration: float,
                               test_results: List[TestResult] = None,
                               error_messages: List[str] = None,
                               formats: List[str] = None) -> Dict[str, Path]:
        """
        生成完整的测试报告（多种格式）
        
        Args:
            url: 测试的 URL
            tool_info: 工具信息
            server_info: 服务器信息
            test_success: 测试是否成功
            duration: 测试持续时间
            test_results: 详细测试结果列表
            error_messages: 错误消息列表
            formats: 要生成的格式列表 ['json', 'html', 'csv']
            
        Returns:
            Dict[str, Path]: 格式名到文件路径的映射
        """
        if formats is None:
            formats = ['json', 'html']
        
        # 生成报告对象
        report = self.generate_single_test_report(
            url, tool_info, server_info, test_success, duration,
            test_results, error_messages
        )
        
        # 生成各种格式的报告
        generated_files = {}
        
        if 'json' in formats:
            json_path = self.save_json_report(report)
            generated_files['json'] = json_path
        
        if 'html' in formats:
            html_path = self.save_html_report(report)
            generated_files['html'] = html_path
        
        if 'csv' in formats:
            csv_path = self.save_csv_summary([report])
            generated_files['csv'] = csv_path
        
        return generated_files

# 全局报告生成器实例
_report_generator_instance = None

def get_report_generator(output_dir: Union[str, Path] = "data/test_results") -> MCPReportGenerator:
    """获取全局报告生成器实例"""
    global _report_generator_instance
    if _report_generator_instance is None:
        _report_generator_instance = MCPReportGenerator(output_dir)
    return _report_generator_instance

# 便捷函数
def generate_test_report(url: str,
                        tool_info: MCPToolInfo,
                        server_info,
                        test_success: bool,
                        duration: float,
                        test_results: List[TestResult] = None,
                        error_messages: List[str] = None,
                        formats: List[str] = None) -> Dict[str, Path]:
    """
    便捷函数：生成测试报告
    
    Args:
        url: 测试的 URL
        tool_info: 工具信息
        server_info: 服务器信息
        test_success: 测试是否成功
        duration: 测试持续时间
        test_results: 详细测试结果列表
        error_messages: 错误消息列表
        formats: 要生成的格式列表
        
    Returns:
        Dict[str, Path]: 格式名到文件路径的映射
    """
    generator = get_report_generator()
    return generator.generate_complete_report(
        url, tool_info, server_info, test_success, duration,
        test_results, error_messages, formats
    )
