#!/usr/bin/env python3
"""
增强的MCP测试报告生成器

支持新的数据结构并集成Supabase数据库存储

作者: AI Assistant
日期: 2025-08-16
版本: 2.0.0
"""

import json
import platform
import psutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import uuid

try:
    from rich.console import Console
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    def rprint(text): print(text)

from src.core.enhanced_report_model import (
    EnhancedMCPTestReport,
    TestMetadata,
    ToolInfo,
    DeploymentInfo,
    AvailableTool,
    TestExecution,
    QualityMetrics,
    PerformanceAnalysis,
    TestStatus,
    DeploymentStatus
)

try:
    from src.core.supabase_connector import SupabaseConnector
    SUPABASE_AVAILABLE = True
    def get_supabase_connector(): 
        return SupabaseConnector()
except ImportError:
    SUPABASE_AVAILABLE = False
    def get_supabase_connector(): return None

class EnhancedReportGenerator:
    """增强的MCP测试报告生成器"""
    
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
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化Supabase连接器（如果可用）
        self.supabase_connector = get_supabase_connector() if SUPABASE_AVAILABLE else None
        if self.supabase_connector:
            rprint("[green]✅ Supabase连接器已初始化[/green]")
        else:
            rprint("[yellow]⚠️ Supabase连接器不可用，仅使用本地文件存储[/yellow]")
    
    def create_enhanced_report(self,
                             url: str,
                             tool_info,
                             server_info,
                             test_success: bool,
                             duration: float,
                             test_results: List[Dict] = None,
                             error_messages: List[str] = None,
                             smart_test_enabled: bool = False,
                             trigger_source: str = "manual") -> EnhancedMCPTestReport:
        """
        创建增强的测试报告
        
        Args:
            url: 测试URL
            tool_info: 工具信息
            server_info: 服务器信息
            test_success: 测试是否成功
            duration: 测试持续时间
            test_results: 测试结果列表
            error_messages: 错误消息列表
            smart_test_enabled: 是否启用智能测试
            trigger_source: 触发源
        
        Returns:
            EnhancedMCPTestReport: 增强的测试报告
        """
        # 创建报告对象
        report = EnhancedMCPTestReport()
        
        # 设置元数据
        report.metadata = TestMetadata(
            test_environment="local",
            trigger_source=trigger_source,
            tags=["smart" if smart_test_enabled else "basic", "mcp-test"]
        )
        
        # 转换工具信息
        if tool_info:
            report.tool_info = ToolInfo(
                name=tool_info.name,
                author=tool_info.author,
                github_url=getattr(tool_info, 'github_url', url),
                package_name=tool_info.package_name,
                category=tool_info.category,
                description=tool_info.description,
                requires_api_key=tool_info.requires_api_key,
                api_requirements=tool_info.api_requirements
            )
        
        # 设置部署信息
        if server_info:
            report.deployment = DeploymentInfo(
                status=DeploymentStatus.SUCCESS if server_info else DeploymentStatus.FAILED,
                start_time=datetime.fromtimestamp(server_info.start_time) if server_info else datetime.now(),
                end_time=datetime.now(),
                duration_seconds=duration,
                process_id=server_info.process.pid if server_info and server_info.process else None,
                server_id=server_info.server_id if server_info else None,
                resource_usage=self._get_resource_usage(server_info)
            )
            
            # 转换可用工具
            if hasattr(server_info, 'available_tools') and server_info.available_tools:
                for tool in server_info.available_tools:
                    available_tool = AvailableTool(
                        name=tool.get('name', 'unknown'),
                        description=tool.get('description', ''),
                        input_schema=tool.get('inputSchema', {}),
                        output_schema=tool.get('outputSchema', {})
                    )
                    report.available_tools.append(available_tool)
        
        # 转换测试执行记录
        if test_results:
            for test_result in test_results:
                execution = TestExecution(
                    test_name=getattr(test_result, 'test_name', 'unknown'),
                    test_type=getattr(test_result, 'test_type', 'basic'),
                    status=TestStatus.SUCCESS if getattr(test_result, 'success', False) else TestStatus.FAILED,
                    start_time=datetime.now(),  # 简化处理
                    end_time=datetime.now(),
                    duration_seconds=getattr(test_result, 'duration', 0.0),
                    error_message=getattr(test_result, 'error_message', None),
                    output_data={'result': getattr(test_result, 'output', '')}
                )
                report.test_executions.append(execution)
        
        # 计算质量指标
        deployment_success = report.deployment and report.deployment.status == DeploymentStatus.SUCCESS
        report.quality_metrics = self._calculate_quality_metrics(
            deployment_success,
            test_success,
            len(report.available_tools),
            report.test_executions
        )
        
        # 性能分析
        report.performance = self._analyze_performance(
            duration,
            server_info,
            report.test_executions
        )
        
        # 设置总体状态
        report.overall_status = TestStatus.SUCCESS if test_success else TestStatus.FAILED
        report.total_duration_seconds = duration
        
        # 设置错误信息
        if error_messages:
            report.errors = error_messages
        
        # 环境信息
        report.environment = {
            'platform': platform.system(),
            'python_version': platform.python_version(),
            'architecture': platform.architecture()[0]
        }
        
        return report
    
    def _get_resource_usage(self, server_info) -> Dict[str, Any]:
        """获取资源使用情况"""
        if not server_info or not server_info.process:
            return {}
        
        try:
            process = psutil.Process(server_info.process.pid)
            return {
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'cpu_percent': process.cpu_percent(),
                'num_threads': process.num_threads(),
                'create_time': process.create_time()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {}
    
    def _calculate_quality_metrics(self,
                                 deployment_success: bool,
                                 communication_success: bool,
                                 available_tools_count: int,
                                 test_executions: List[TestExecution]) -> QualityMetrics:
        """计算质量指标"""
        metrics = QualityMetrics()
        
        # 部署可靠性
        metrics.deployment_reliability = 100.0 if deployment_success else 0.0
        
        # 通信稳定性
        metrics.communication_stability = 100.0 if communication_success else 0.0
        
        # 功能覆盖率
        if test_executions:
            passed_tests = sum(1 for test in test_executions if test.status == TestStatus.SUCCESS)
            metrics.functionality_coverage = (passed_tests / len(test_executions)) * 100.0
        else:
            metrics.functionality_coverage = 0.0
        
        # 性能评级（基于可用工具数量）
        if available_tools_count > 0:
            metrics.performance_rating = min(100.0, available_tools_count * 20.0)
        else:
            metrics.performance_rating = 0.0
        
        # 文档质量（简化评估）
        metrics.documentation_quality = 75.0  # 默认值
        
        # API设计质量（简化评估）
        metrics.api_design_quality = 80.0  # 默认值
        
        # 计算总分
        metrics.overall_score = (
            metrics.deployment_reliability * 0.25 +
            metrics.communication_stability * 0.25 +
            metrics.functionality_coverage * 0.20 +
            metrics.performance_rating * 0.15 +
            metrics.documentation_quality * 0.10 +
            metrics.api_design_quality * 0.05
        )
        
        return metrics
    
    def _analyze_performance(self,
                           total_duration: float,
                           server_info,
                           test_executions: List[TestExecution]) -> PerformanceAnalysis:
        """分析性能指标"""
        performance = PerformanceAnalysis()
        
        performance.deployment_time_seconds = total_duration
        
        if server_info:
            resource_usage = self._get_resource_usage(server_info)
            performance.memory_usage_mb = resource_usage.get('memory_mb', 0.0)
            performance.cpu_usage_percent = resource_usage.get('cpu_percent', 0.0)
        
        if test_executions:
            durations = [test.duration_seconds for test in test_executions if test.duration_seconds > 0]
            if durations:
                performance.response_time_avg_ms = sum(durations) / len(durations) * 1000
                performance.response_time_p95_ms = sorted(durations)[int(len(durations) * 0.95)] * 1000
        
        # 稳定性分数（基于成功率）
        if test_executions:
            success_count = sum(1 for test in test_executions if test.status == TestStatus.SUCCESS)
            performance.stability_score = (success_count / len(test_executions)) * 100.0
        
        return performance
    
    def save_report(self, report: EnhancedMCPTestReport, formats: List[str] = None) -> Dict[str, str]:
        """
        保存报告到多种格式
        
        Args:
            report: 增强的测试报告
            formats: 要保存的格式列表 ['json', 'html', 'database']
        
        Returns:
            Dict[str, str]: 格式到文件路径的映射
        """
        if formats is None:
            formats = ['json', 'html']
        
        saved_files = {}
        
        # 保存到数据库
        if 'database' in formats and self.supabase_connector:
            try:
                report_id = self.supabase_connector.save_test_report(report)
                saved_files['database'] = f"Database record: {report_id}"
                rprint(f"[green]✅ 报告已保存到数据库: {report_id}[/green]")
            except Exception as e:
                rprint(f"[red]❌ 数据库保存失败: {e}[/red]")
        
        # 保存JSON格式
        if 'json' in formats:
            json_path = self._save_json_report(report)
            saved_files['json'] = str(json_path)
        
        # 保存HTML格式
        if 'html' in formats:
            html_path = self._save_html_report(report)
            saved_files['html'] = str(html_path)
        
        return saved_files
    
    def _save_json_report(self, report: EnhancedMCPTestReport) -> Path:
        """保存JSON格式报告"""
        timestamp = report.created_at.strftime('%Y%m%d_%H%M%S')
        json_filename = f"enhanced_mcp_test_{timestamp}.json"
        json_path = self.reports_dir / json_filename
        
        # 转换为可序列化的字典
        report_dict = report.to_dict()
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
        
        return json_path
    
    def _save_html_report(self, report: EnhancedMCPTestReport) -> Path:
        """保存HTML格式报告"""
        timestamp = report.created_at.strftime('%Y%m%d_%H%M%S')
        html_filename = f"enhanced_mcp_test_{timestamp}.html"
        html_path = self.reports_dir / html_filename
        
        # 生成HTML内容
        html_content = self._generate_html_content(report)
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_path
    
    def _generate_html_content(self, report: EnhancedMCPTestReport) -> str:
        """生成HTML报告内容"""
        # 计算统计数据
        stats = report.get_summary_stats()
        
        # 生成可用工具列表
        tools_html = ""
        for tool in report.available_tools:
            tools_html += f"""
            <div class="tool-card">
                <h4>{tool.name}</h4>
                <p>{tool.description}</p>
                <span class="badge">{tool.category}</span>
            </div>
            """
        
        # 生成测试结果表格
        tests_html = ""
        for test in report.test_executions:
            status_class = "success" if test.status == TestStatus.SUCCESS else "failure"
            status_icon = "✅" if test.status == TestStatus.SUCCESS else "❌"
            
            tests_html += f"""
            <tr>
                <td>{test.test_name}</td>
                <td><span class="{status_class}">{status_icon} {test.status.value}</span></td>
                <td>{test.test_type}</td>
                <td>{test.duration_seconds:.3f}s</td>
                <td>{test.error_message or '-'}</td>
            </tr>
            """
        
        # 构建完整HTML
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>增强MCP测试报告 - {report.tool_info.name if report.tool_info else 'Unknown'}</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            margin: 0; 
            padding: 20px; 
            line-height: 1.6; 
            background: #f5f7fa;
        }}
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 12px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
            overflow: hidden;
        }}
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 40px; 
            text-align: center;
        }}
        .header h1 {{ margin: 0; font-size: 2.5em; font-weight: 300; }}
        .header p {{ margin: 15px 0 0 0; font-size: 1.1em; opacity: 0.9; }}
        .section {{ padding: 30px; border-bottom: 1px solid #eee; }}
        .section:last-child {{ border-bottom: none; }}
        .section h2 {{ color: #2d3748; margin-top: 0; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #667eea;
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
            color: #667eea;
        }}
        .stat-label {{ color: #6a737d; font-size: 0.9em; }}
        .success {{ color: #28a745; font-weight: bold; }}
        .failure {{ color: #dc3545; font-weight: bold; }}
        .warning {{ color: #ffc107; font-weight: bold; }}
        .badge {{ 
            background: #e3f2fd; 
            color: #1976d2; 
            padding: 4px 8px; 
            border-radius: 4px; 
            font-size: 0.8em; 
        }}
        .tool-card {{ 
            background: #f8f9fa; 
            padding: 15px; 
            margin: 10px 0; 
            border-radius: 8px; 
            border-left: 4px solid #007bff; 
        }}
        .tool-card h4 {{ margin: 0 0 8px 0; color: #2d3748; }}
        .tool-card p {{ margin: 0 0 8px 0; color: #6a737d; }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0;
        }}
        th, td {{ 
            padding: 12px; 
            text-align: left; 
            border-bottom: 1px solid #ddd; 
        }}
        th {{ 
            background: #f8f9fa; 
            font-weight: 600;
            color: #495057;
        }}
        tr:hover {{ background: #f8f9fa; }}
        .quality-bar {{
            width: 100%;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin: 8px 0;
        }}
        .quality-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745 0%, #20c997 50%, #ffc107 100%);
            transition: width 0.3s ease;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 增强MCP测试报告</h1>
            <p><strong>{report.tool_info.name if report.tool_info else 'Unknown Tool'}</strong></p>
            <p>{report.created_at.strftime('%Y-%m-%d %H:%M:%S')} | 会话ID: {report.metadata.session_id}</p>
        </div>
        
        <div class="section">
            <h2>📊 测试概览</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">总体状态</div>
                    <div class="stat-number {'success' if report.overall_status == TestStatus.SUCCESS else 'failure'}">
                        {'✅' if report.overall_status == TestStatus.SUCCESS else '❌'}
                    </div>
                    <div class="stat-label">{report.overall_status.value}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">质量分数</div>
                    <div class="stat-number">{report.quality_metrics.overall_score:.1f}</div>
                    <div class="quality-bar">
                        <div class="quality-fill" style="width: {report.quality_metrics.overall_score}%"></div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">测试通过率</div>
                    <div class="stat-number">{stats['success_rate']:.1f}%</div>
                    <div class="stat-label">{stats['passed_tests']}/{stats['total_tests']} 通过</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">可用工具</div>
                    <div class="stat-number">{stats['available_tools_count']}</div>
                    <div class="stat-label">个工具可用</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🛠️ 工具信息</h2>
            {f'''
            <p><strong>作者:</strong> {report.tool_info.author}</p>
            <p><strong>包名:</strong> {report.tool_info.package_name or 'N/A'}</p>
            <p><strong>类别:</strong> {report.tool_info.category}</p>
            <p><strong>GitHub:</strong> <a href="{report.tool_info.github_url}" target="_blank">{report.tool_info.github_url}</a></p>
            <p><strong>描述:</strong> {report.tool_info.description}</p>
            <p><strong>API密钥:</strong> {'需要' if report.tool_info.requires_api_key else '不需要'}</p>
            ''' if report.tool_info else '<p>无工具信息</p>'}
        </div>
        
        <div class="section">
            <h2>⚙️ 部署信息</h2>
            {f'''
            <p><strong>状态:</strong> <span class="{'success' if report.deployment.status == DeploymentStatus.SUCCESS else 'failure'}">{report.deployment.status.value}</span></p>
            <p><strong>部署时间:</strong> {report.deployment.duration_seconds:.2f} 秒</p>
            <p><strong>服务器ID:</strong> {report.deployment.server_id or 'N/A'}</p>
            <p><strong>进程ID:</strong> {report.deployment.process_id or 'N/A'}</p>
            ''' if report.deployment else '<p>无部署信息</p>'}
        </div>
        
        <div class="section">
            <h2>🔧 可用工具列表</h2>
            {tools_html if tools_html else '<p>无可用工具</p>'}
        </div>
        
        <div class="section">
            <h2>🧪 测试执行详情</h2>
            {f'''
            <table>
                <thead>
                    <tr>
                        <th>测试名称</th>
                        <th>状态</th>
                        <th>类型</th>
                        <th>耗时</th>
                        <th>错误信息</th>
                    </tr>
                </thead>
                <tbody>
                    {tests_html}
                </tbody>
            </table>
            ''' if tests_html else '<p>无测试执行记录</p>'}
        </div>
        
        <div class="section">
            <h2>📈 性能指标</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">内存使用</div>
                    <div class="stat-number">{report.performance.memory_usage_mb:.1f}</div>
                    <div class="stat-label">MB</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">平均响应时间</div>
                    <div class="stat-number">{report.performance.response_time_avg_ms:.1f}</div>
                    <div class="stat-label">毫秒</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">稳定性分数</div>
                    <div class="stat-number">{report.performance.stability_score:.1f}</div>
                    <div class="stat-label">分</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">总耗时</div>
                    <div class="stat-number">{report.total_duration_seconds:.2f}</div>
                    <div class="stat-label">秒</div>
                </div>
            </div>
        </div>
        
        {f'''
        <div class="section">
            <h2>⚠️ 错误和警告</h2>
            {f'<h3>错误:</h3><ul>{"".join(f"<li>{error}</li>" for error in report.errors)}</ul>' if report.errors else ''}
            {f'<h3>警告:</h3><ul>{"".join(f"<li>{warning}</li>" for warning in report.warnings)}</ul>' if report.warnings else ''}
        </div>
        ''' if report.errors or report.warnings else ''}
    </div>
</body>
</html>"""
        
        return html_content

# 兼容性函数
def generate_test_report(url: str, tool_info, server_info, test_success: bool, 
                        duration: float, test_results: List[Dict] = None, 
                        formats: List[str] = None) -> Dict[str, str]:
    """
    生成测试报告（兼容旧版本API）
    
    Returns:
        Dict[str, str]: 格式到文件路径的映射
    """
    generator = EnhancedReportGenerator()
    
    # 创建增强报告
    enhanced_report = generator.create_enhanced_report(
        url=url,
        tool_info=tool_info,
        server_info=server_info,
        test_success=test_success,
        duration=duration,
        test_results=test_results or []
    )
    
    # 保存报告
    if formats is None:
        formats = ['json', 'html', 'database']
    
    return generator.save_report(enhanced_report, formats)

# 导出主要类和函数
__all__ = ['EnhancedReportGenerator', 'generate_test_report']
