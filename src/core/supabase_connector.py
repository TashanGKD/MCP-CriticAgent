#!/usr/bin/env python3
"""
Supabase数据库连接器

用于将MCP测试结果存储到Supabase数据库的连接器类

作者: AI Assistant
日期: 2025-08-16
版本: 1.0.0
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import asdict
import asyncio
from pathlib import Path

from .enhanced_report_model import (
    EnhancedMCPTestReport,
    TestStatus,
    ToolInfo,
    QualityMetrics,
    PerformanceAnalysis
)

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

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    print("⚠️ Supabase库未安装，数据库功能不可用")
    SUPABASE_AVAILABLE = False
    Client = None

from src.core.enhanced_report_model import (
    EnhancedMCPTestReport, 
    ToolInfo, 
    DeploymentInfo, 
    TestExecution,
    AvailableTool,
    QualityMetrics,
    PerformanceAnalysis,
    TestStatus,
    DeploymentStatus
)

class SupabaseConnector:
    """Supabase数据库连接器"""
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        初始化Supabase连接器
        
        Args:
            url: Supabase项目URL，如果为None则从环境变量获取
            key: Supabase API密钥，如果为None则从环境变量获取
        """
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase库未安装，请运行: uv add supabase")
        
        self.url = url or os.getenv('SUPABASE_URL')
        self.key = key or os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.url or not self.key:
            raise ValueError("请在环境变量中设置SUPABASE_URL和SUPABASE_SERVICE_ROLE_KEY")
        
        self.client = create_client(self.url, self.key)
        self.logger = logging.getLogger(__name__)
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            # 尝试查询一个简单的表
            result = self.client.table('mcp_tools').select('count').limit(1).execute()
            return True
        except Exception as e:
            self.logger.error(f"数据库连接测试失败: {e}")
            return False
    
    def insert_or_update_tool(self, tool_info: ToolInfo) -> str:
        """
        插入或更新MCP工具信息
        
        Args:
            tool_info: 工具信息对象
            
        Returns:
            str: 工具ID
        """
        tool_data = {
            'name': tool_info.name,
            'author': tool_info.author,
            'github_url': tool_info.github_url,
            'package_name': tool_info.package_name,
            'category': tool_info.category,
            'description': tool_info.description,
            'version': tool_info.version,
            'requires_api_key': tool_info.requires_api_key,
            'api_requirements': tool_info.api_requirements,
            'language': tool_info.language,
            'license': tool_info.license,
            'stars': tool_info.stars,
            'last_updated': tool_info.last_updated.isoformat() if tool_info.last_updated else None
        }
        
        # 首先尝试根据github_url或package_name查找现有工具
        existing_tool = None
        if tool_info.github_url:
            result = self.client.table('mcp_tools').select('id').eq('github_url', tool_info.github_url).execute()
            if result.data:
                existing_tool = result.data[0]
        
        if not existing_tool and tool_info.package_name:
            result = self.client.table('mcp_tools').select('id').eq('package_name', tool_info.package_name).execute()
            if result.data:
                existing_tool = result.data[0]
        
        if existing_tool:
            # 更新现有工具
            tool_id = existing_tool['id']
            self.client.table('mcp_tools').update(tool_data).eq('id', tool_id).execute()
            self.logger.info(f"更新工具信息: {tool_info.name} (ID: {tool_id})")
        else:
            # 插入新工具
            result = self.client.table('mcp_tools').insert(tool_data).execute()
            tool_id = result.data[0]['id']
            self.logger.info(f"插入新工具: {tool_info.name} (ID: {tool_id})")
        
        return tool_id
    
    def save_test_report(self, report: EnhancedMCPTestReport) -> str:
        """
        保存完整的测试报告
        
        Args:
            report: 增强的测试报告对象
            
        Returns:
            str: 报告ID
        """
        try:
            # 1. 插入或更新工具信息
            tool_id = None
            if report.tool_info:
                tool_id = self.insert_or_update_tool(report.tool_info)
            
            # 2. 插入测试报告主记录
            report_data = {
                'test_run_id': report.metadata.session_id,
                'timestamp': report.created_at.isoformat(),
                'total_tools': len(report.available_tools),
                'tools_tested': len(report.test_executions),
                'tools_successful': len([e for e in report.test_executions if e.status == TestStatus.SUCCESS]),
                'overall_status': report.overall_status.value,
                'execution_time_seconds': report.total_duration_seconds,
                'python_version': report.environment.get('python_version', 'unknown'),
                'platform': report.environment.get('platform', 'unknown'),
                'test_environment': report.metadata.test_environment
            }
            
            result = self.client.table('test_reports').insert(report_data).execute()
            report_uuid = result.data[0]['id']
            self.logger.info(f"插入测试报告: {report.metadata.session_id}, UUID: {report_uuid}")
            
            # 3. 插入部署信息
            if report.deployment:
                deployment_data = {
                    'report_id': report_uuid,
                    'status': report.deployment.status.value,
                    'environment': report.deployment.deployment_method,
                    'deployment_time': report.deployment.start_time.isoformat(),
                    'deployment_duration_seconds': report.deployment.duration_seconds,
                    'deployment_data': {
                        'package_manager': report.deployment.package_manager,
                        'process_id': report.deployment.process_id,
                        'server_id': report.deployment.server_id,
                        'port': report.deployment.port,
                        'error_details': report.deployment.error_details,
                        'resource_usage': report.deployment.resource_usage
                    }
                }
                
                self.client.table('deployment_info').insert(deployment_data).execute()
                self.logger.info(f"插入部署信息: {report.metadata.session_id}")
            
            # 4. 插入测试执行记录
            if report.test_executions:
                executions_data = []
                for execution in report.test_executions:
                    execution_data = {
                        'report_id': report_uuid,
                        'tool_id': tool_id,
                        'status': execution.status.value,
                        'execution_time_seconds': execution.duration_seconds,
                        'memory_usage_mb': execution.performance_metrics.get('memory_mb', 0) if execution.performance_metrics else 0,
                        'test_data': {
                            'test_name': execution.test_name,
                            'test_type': execution.test_type,
                            'input_data': execution.input_data,
                            'output_data': execution.output_data,
                            'assertion_results': execution.assertion_results,
                            'performance_metrics': execution.performance_metrics
                        },
                        'error_message': execution.error_message
                    }
                    executions_data.append(execution_data)
                
                self.client.table('test_executions').insert(executions_data).execute()
                self.logger.info(f"插入{len(executions_data)}条测试执行记录")
            
            # 5. 插入质量指标
            if report.quality_metrics:
                successful_tests = len([e for e in report.test_executions if e.status == TestStatus.SUCCESS])
                total_tests = len(report.test_executions)
                quality_data = {
                    'report_id': report_uuid,
                    'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0,
                    'performance_score': report.quality_metrics.performance_rating,
                    'reliability_score': report.quality_metrics.deployment_reliability,
                    'overall_quality_score': report.quality_metrics.overall_score,
                    'metrics_data': {
                        'deployment_reliability': report.quality_metrics.deployment_reliability,
                        'communication_stability': report.quality_metrics.communication_stability,
                        'functionality_coverage': report.quality_metrics.functionality_coverage,
                        'documentation_quality': report.quality_metrics.documentation_quality,
                        'api_design_quality': report.quality_metrics.api_design_quality
                    }
                }
                
                self.client.table('quality_metrics').insert(quality_data).execute()
                self.logger.info(f"插入质量指标: {report.metadata.session_id}")
            
            # 6. 插入性能分析
            if report.performance:
                performance_data = {
                    'report_id': report_uuid,
                    'avg_execution_time': report.total_duration_seconds,
                    'max_execution_time': report.total_duration_seconds,
                    'min_execution_time': report.total_duration_seconds,
                    'total_execution_time': report.total_duration_seconds,
                    'avg_memory_usage': report.performance.memory_usage_mb,
                    'max_memory_usage': report.performance.memory_usage_mb,
                    'performance_data': {
                        'deployment_time_seconds': report.performance.deployment_time_seconds,
                        'startup_time_seconds': report.performance.startup_time_seconds,
                        'cpu_usage_percent': report.performance.cpu_usage_percent
                    }
                }
                
                self.client.table('performance_analysis').insert(performance_data).execute()
                self.logger.info(f"插入性能分析: {report.metadata.session_id}")
            
            # 7. 插入测试元数据
            if report.metadata:
                metadata_data = {
                    'report_id': report_uuid,
                    'test_framework_version': getattr(report.metadata, 'test_framework_version', '1.0.0'),
                    'config_hash': getattr(report.metadata, 'config_hash', None),
                    'git_commit': getattr(report.metadata, 'git_commit', None),
                    'test_tags': report.metadata.tags,
                    'metadata': {
                        'session_id': report.metadata.session_id,
                        'test_environment': report.metadata.test_environment,
                        'trigger_source': report.metadata.trigger_source,
                        'operator': report.metadata.operator
                    }
                }
                
                self.client.table('test_metadata').insert(metadata_data).execute()
                self.logger.info(f"插入测试元数据: {report.metadata.session_id}")
            
            return str(report_uuid)
            
        except Exception as e:
            self.logger.error(f"保存测试报告失败: {e}")
            raise
    
    def get_test_reports(self, 
                        limit: int = 50, 
                        tool_id: Optional[str] = None,
                        status: Optional[str] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        查询测试报告
        
        Args:
            limit: 返回记录数限制
            tool_id: 工具ID过滤
            status: 状态过滤
            start_date: 开始日期过滤
            end_date: 结束日期过滤
            
        Returns:
            List[Dict]: 测试报告列表
        """
        query = self.client.table('test_reports_overview').select('*')
        
        if tool_id:
            query = query.eq('tool_id', tool_id)
        
        if status:
            query = query.eq('overall_status', status)
        
        if start_date:
            query = query.gte('created_at', start_date.isoformat())
        
        if end_date:
            query = query.lte('created_at', end_date.isoformat())
        
        result = query.order('created_at', desc=True).limit(limit).execute()
        return result.data
    
    def get_tool_statistics(self) -> List[Dict[str, Any]]:
        """获取工具统计信息"""
        result = self.client.table('mcp_tools_stats').select('*').order('total_tests', desc=True).execute()
        return result.data
    
    def get_performance_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取性能趋势数据"""
        result = self.client.table('performance_trends').select('*').limit(days).execute()
        return result.data
    
    def delete_test_report(self, report_id: str) -> bool:
        """
        删除测试报告（级联删除相关数据）
        
        Args:
            report_id: 报告ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            self.client.table('test_reports').delete().eq('report_id', report_id).execute()
            self.logger.info(f"删除测试报告: {report_id}")
            return True
        except Exception as e:
            self.logger.error(f"删除测试报告失败: {e}")
            return False

def get_supabase_connector() -> Optional[SupabaseConnector]:
    """获取Supabase连接器实例"""
    try:
        connector = SupabaseConnector()
        if connector.test_connection():
            return connector
        else:
            print("⚠️ Supabase连接测试失败")
            return None
    except Exception as e:
        print(f"⚠️ 创建Supabase连接器失败: {e}")
        return None

# 导出主要类和函数
__all__ = ['SupabaseConnector', 'get_supabase_connector']
