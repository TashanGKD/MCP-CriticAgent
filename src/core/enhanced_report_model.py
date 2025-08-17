#!/usr/bin/env python3
"""
增强的MCP测试报告数据模型

为Supabase存储优化的测试报告数据结构，支持更好的查询和分析

作者: AI Assistant
日期: 2025-08-16
版本: 2.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import uuid
import json

class TestStatus(Enum):
    """测试状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"

class DeploymentStatus(Enum):
    """部署状态枚举"""
    PENDING = "pending"
    DEPLOYING = "deploying"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class TestMetadata:
    """测试元数据"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    test_environment: str = "local"
    trigger_source: str = "manual"  # manual, github_actions, api
    operator: Optional[str] = None
    tags: List[str] = field(default_factory=list)

@dataclass
class ToolInfo:
    """MCP工具信息（标准化）"""
    name: str
    author: str
    github_url: str
    package_name: Optional[str] = None
    category: str = "Unknown"
    description: str = ""
    version: Optional[str] = None
    requires_api_key: bool = False
    api_requirements: List[str] = field(default_factory=list)
    language: str = "Unknown"  # Node.js, Python, etc.
    license: Optional[str] = None
    stars: Optional[int] = None
    last_updated: Optional[datetime] = None

@dataclass
class DeploymentInfo:
    """部署信息"""
    status: DeploymentStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    package_manager: str = "npm"  # npm, pip, uv
    deployment_method: str = "local"  # local, docker, cloud
    process_id: Optional[int] = None
    server_id: Optional[str] = None
    port: Optional[int] = None
    error_details: Optional[str] = None
    resource_usage: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AvailableTool:
    """可用工具详情"""
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    category: str = "general"
    required_permissions: List[str] = field(default_factory=list)

@dataclass
class TestExecution:
    """单个测试执行记录"""
    test_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    test_name: str = ""
    test_type: str = "basic"  # basic, communication, functionality, performance
    status: TestStatus = TestStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    assertion_results: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)

@dataclass
class QualityMetrics:
    """质量指标"""
    overall_score: float = 0.0  # 0-100
    deployment_reliability: float = 0.0
    communication_stability: float = 0.0
    functionality_coverage: float = 0.0
    performance_rating: float = 0.0
    documentation_quality: float = 0.0
    api_design_quality: float = 0.0

@dataclass
class PerformanceAnalysis:
    """性能分析"""
    deployment_time_seconds: float = 0.0
    startup_time_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    response_time_avg_ms: float = 0.0
    response_time_p95_ms: float = 0.0
    throughput_ops_per_second: float = 0.0
    stability_score: float = 0.0

@dataclass
class EnhancedMCPTestReport:
    """增强的MCP测试报告（面向数据库存储）"""
    # 基础标识
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # 测试元数据
    metadata: TestMetadata = field(default_factory=TestMetadata)
    
    # 工具信息
    tool_info: ToolInfo = None
    
    # 部署信息
    deployment: DeploymentInfo = None
    
    # 可用工具列表
    available_tools: List[AvailableTool] = field(default_factory=list)
    
    # 测试执行记录
    test_executions: List[TestExecution] = field(default_factory=list)
    
    # 质量指标
    quality_metrics: QualityMetrics = field(default_factory=QualityMetrics)
    
    # 性能分析
    performance: PerformanceAnalysis = field(default_factory=PerformanceAnalysis)
    
    # 总体状态
    overall_status: TestStatus = TestStatus.PENDING
    total_duration_seconds: float = 0.0
    
    # 错误和警告
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # 环境信息
    environment: Dict[str, str] = field(default_factory=dict)
    
    # 附加数据
    raw_logs: Optional[str] = None
    screenshots: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（用于JSON序列化）"""
        def convert_value(value):
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, Enum):
                return value.value
            elif hasattr(value, '__dict__'):
                return {k: convert_value(v) for k, v in value.__dict__.items()}
            elif isinstance(value, list):
                return [convert_value(item) for item in value]
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            else:
                return value
        
        return convert_value(self.__dict__)
    
    def calculate_quality_score(self) -> float:
        """计算综合质量分数"""
        metrics = self.quality_metrics
        weights = {
            'deployment_reliability': 0.25,
            'communication_stability': 0.25,
            'functionality_coverage': 0.20,
            'performance_rating': 0.15,
            'documentation_quality': 0.10,
            'api_design_quality': 0.05
        }
        
        total_score = 0.0
        for metric, weight in weights.items():
            total_score += getattr(metrics, metric, 0.0) * weight
        
        self.quality_metrics.overall_score = total_score
        return total_score
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """获取摘要统计"""
        return {
            'total_tests': len(self.test_executions),
            'passed_tests': sum(1 for test in self.test_executions if test.status == TestStatus.SUCCESS),
            'failed_tests': sum(1 for test in self.test_executions if test.status == TestStatus.FAILED),
            'success_rate': self._calculate_success_rate(),
            'avg_response_time': self.performance.response_time_avg_ms,
            'deployment_success': self.deployment.status == DeploymentStatus.SUCCESS if self.deployment else False,
            'available_tools_count': len(self.available_tools),
            'quality_score': self.quality_metrics.overall_score
        }
    
    def _calculate_success_rate(self) -> float:
        """计算成功率"""
        if not self.test_executions:
            return 0.0
        
        passed = sum(1 for test in self.test_executions if test.status == TestStatus.SUCCESS)
        return (passed / len(self.test_executions)) * 100

# 数据库表结构映射
class DatabaseSchema:
    """数据库表结构定义"""
    
    # 主表：测试报告
    test_reports = {
        'report_id': 'UUID PRIMARY KEY',
        'created_at': 'TIMESTAMP WITH TIME ZONE',
        'updated_at': 'TIMESTAMP WITH TIME ZONE',
        'session_id': 'UUID',
        'test_environment': 'VARCHAR(50)',
        'trigger_source': 'VARCHAR(50)',
        'operator': 'VARCHAR(100)',
        'overall_status': 'VARCHAR(20)',
        'total_duration_seconds': 'FLOAT',
        'quality_score': 'FLOAT',
        'metadata_json': 'JSONB',
        'environment_json': 'JSONB'
    }
    
    # 工具信息表
    mcp_tools = {
        'tool_id': 'UUID PRIMARY KEY',
        'name': 'VARCHAR(200)',
        'author': 'VARCHAR(100)',
        'github_url': 'TEXT',
        'package_name': 'VARCHAR(200)',
        'category': 'VARCHAR(100)',
        'description': 'TEXT',
        'version': 'VARCHAR(50)',
        'requires_api_key': 'BOOLEAN',
        'api_requirements': 'TEXT[]',
        'language': 'VARCHAR(50)',
        'license': 'VARCHAR(50)',
        'stars': 'INTEGER',
        'last_updated': 'TIMESTAMP WITH TIME ZONE',
        'created_at': 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()',
        'updated_at': 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()'
    }
    
    # 部署记录表
    deployments = {
        'deployment_id': 'UUID PRIMARY KEY',
        'report_id': 'UUID REFERENCES test_reports(report_id)',
        'tool_id': 'UUID REFERENCES mcp_tools(tool_id)',
        'status': 'VARCHAR(20)',
        'start_time': 'TIMESTAMP WITH TIME ZONE',
        'end_time': 'TIMESTAMP WITH TIME ZONE',
        'duration_seconds': 'FLOAT',
        'package_manager': 'VARCHAR(20)',
        'deployment_method': 'VARCHAR(50)',
        'process_id': 'INTEGER',
        'server_id': 'VARCHAR(100)',
        'port': 'INTEGER',
        'error_details': 'TEXT',
        'resource_usage_json': 'JSONB'
    }
    
    # 测试执行表
    test_executions = {
        'execution_id': 'UUID PRIMARY KEY', 
        'report_id': 'UUID REFERENCES test_reports(report_id)',
        'test_id': 'VARCHAR(50)',
        'test_name': 'VARCHAR(200)',
        'test_type': 'VARCHAR(50)',
        'status': 'VARCHAR(20)',
        'start_time': 'TIMESTAMP WITH TIME ZONE',
        'end_time': 'TIMESTAMP WITH TIME ZONE',
        'duration_seconds': 'FLOAT',
        'input_data_json': 'JSONB',
        'output_data_json': 'JSONB',
        'error_message': 'TEXT',
        'assertion_results_json': 'JSONB',
        'performance_metrics_json': 'JSONB'
    }
    
    # 可用工具表
    available_tools = {
        'available_tool_id': 'UUID PRIMARY KEY',
        'report_id': 'UUID REFERENCES test_reports(report_id)',
        'tool_name': 'VARCHAR(200)',
        'description': 'TEXT',
        'input_schema_json': 'JSONB',
        'output_schema_json': 'JSONB',
        'category': 'VARCHAR(100)',
        'required_permissions': 'TEXT[]'
    }
    
    # 质量指标表
    quality_metrics = {
        'metric_id': 'UUID PRIMARY KEY',
        'report_id': 'UUID REFERENCES test_reports(report_id)',
        'overall_score': 'FLOAT',
        'deployment_reliability': 'FLOAT',
        'communication_stability': 'FLOAT', 
        'functionality_coverage': 'FLOAT',
        'performance_rating': 'FLOAT',
        'documentation_quality': 'FLOAT',
        'api_design_quality': 'FLOAT',
        'calculated_at': 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()'
    }
    
    # 性能分析表
    performance_metrics = {
        'performance_id': 'UUID PRIMARY KEY',
        'report_id': 'UUID REFERENCES test_reports(report_id)',
        'deployment_time_seconds': 'FLOAT',
        'startup_time_seconds': 'FLOAT',
        'memory_usage_mb': 'FLOAT',
        'cpu_usage_percent': 'FLOAT',
        'response_time_avg_ms': 'FLOAT',
        'response_time_p95_ms': 'FLOAT',
        'throughput_ops_per_second': 'FLOAT',
        'stability_score': 'FLOAT',
        'measured_at': 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()'
    }
