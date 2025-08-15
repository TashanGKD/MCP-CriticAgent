# Batch MCP 测试框架 - MVP 方案

## 项目概述

基于 `test_crossplatform_mcp.py` 构建的动态 MCP 工具部署、测试生成和大模型交互的最小可行产品。该系统支持根据 URL 动态部署 MCP 工具，自动生成测试用例，并与大模型协作进行验证。

## 核心功能

### 1. 动态 MCP 部署系统
- **数据驱动部署**: 基于 `data/mcp.csv` 中的映射关系动态部署 MCP 工具
- **跨平台兼容**: 支持 Windows/Linux/macOS 环境
- **智能包管理**: 使用 `npx -y @**/**` 自动安装和部署
- **进程管理**: 自动管理 MCP 服务器生命周期

### 2. 自动化测试生成
- **智能测试用例**: 大模型根据 MCP 工具功能自动生成测试用例
- **参数自适应**: 基于工具配置自动适配参数格式
- **测试策略**: 支持单一工具和批量工具测试

### 3. 大模型协作验证
- **ReActAgent**: 使用 AgentScope 的 ReActAgent 进行智能交互
- **真实 MCP 调用**: 验证端到端的 MCP 协议通信
- **结果分析**: 自动分析测试结果并生成报告

## 技术架构

### 核心组件

```
batch_mcp/
├── src/                          # 源代码目录
│   ├── core/                     # 核心模块
│   │   ├── mcp_deployer.py      # MCP 动态部署器
│   │   ├── test_generator.py    # 测试用例生成器
│   │   ├── mcp_communicator.py  # MCP 通信器 (基于现有代码)
│   │   └── platform_detector.py # 平台检测器
│   ├── agents/                   # 智能代理模块
│   │   ├── test_agent.py        # 测试生成代理
│   │   └── validation_agent.py  # 验证执行代理
│   └── utils/                    # 工具函数
│       ├── csv_parser.py        # CSV 数据解析
│       ├── config_loader.py     # 配置加载器
│       └── report_generator.py  # 报告生成器
├── config/                       # 配置文件
│   ├── mcp_mapping.json         # MCP 工具映射配置
│   └── agent_prompts.json       # 代理提示词配置
├── data/                         # 数据目录
│   ├── mcp.csv                  # MCP 工具数据 (现有)
│   └── test_results/            # 测试结果存储
├── test/                         # 测试目录 (现有)
├── .env                         # 环境变量配置
├── pyproject.toml               # UV 项目配置
└── project.md                   # 项目说明文档
```

### 数据流程

1. **URL 输入** → CSV 映射查找 → MCP 包名解析
2. **动态部署** → `npx -y @package/name` → MCP 服务器启动
3. **测试生成** → 大模型分析工具功能 → 生成测试用例
4. **执行验证** → ReActAgent 调用 MCP → 结果验证
5. **报告生成** → 结果分析 → 测试报告输出

## 环境配置

### 环境变量 (.env)
```bash
# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# 项目配置
PROJECT_NAME=Batch_MCP_Testing
LOG_LEVEL=INFO
MAX_CONCURRENT_TESTS=3

# 可选 API Keys (根据 MCP 工具需求)
TAVILY_API_KEY=your_tavily_key_here
FIRECRAWL_API_KEY=your_firecrawl_key_here
GEMINI_API_KEY=your_gemini_key_here
```

### UV 项目配置 (pyproject.toml)
```toml
[project]
name = "batch-mcp-testing"
version = "1.0.0"
description = "动态 MCP 工具部署和测试框架"
authors = [{name = "AI Assistant"}]
readme = "README.md"
requires-python = ">=3.12"

dependencies = [
    "agentscope>=0.0.5",
    "python-dotenv>=1.0.0",
    "pandas>=2.2.0",
    "requests>=2.31.0",
    "asyncio>=3.4.3",
    "pydantic>=2.5.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.6.0"
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.6.0"
]
```

## 核心实现方案

### 1. MCP 动态部署器 (src/core/mcp_deployer.py)

```python
class DynamicMCPDeployer:
    """动态 MCP 工具部署器"""
    
    def __init__(self, csv_data_path: str):
        self.csv_data = self.load_mcp_data(csv_data_path)
        self.active_processes = {}
    
    def deploy_by_url(self, url: str) -> MCPServerInfo:
        """根据 URL 部署 MCP 工具"""
        # 1. 从 CSV 中查找匹配的 URL
        # 2. 解析部署命令 (npx -y @package/name)
        # 3. 启动 MCP 服务器进程
        # 4. 初始化 MCP 协议通信
        # 5. 返回服务器信息
    
    def deploy_by_package(self, package_name: str) -> MCPServerInfo:
        """根据包名直接部署 MCP 工具"""
        # 直接使用包名进行部署
    
    def cleanup(self, server_id: str):
        """清理指定的 MCP 服务器"""
```

### 2. 测试生成代理 (src/agents/test_agent.py)

```python
class TestGeneratorAgent:
    """测试用例生成代理"""
    
    def __init__(self, model_config: dict):
        self.agent = ReActAgent(
            name="test_generator",
            model_config_name="test_gen_model",
            sys_prompt=self.load_test_gen_prompt()
        )
    
    def generate_test_cases(self, mcp_info: MCPServerInfo) -> List[TestCase]:
        """为指定 MCP 工具生成测试用例"""
        # 1. 分析 MCP 工具功能和参数
        # 2. 生成多样化的测试场景
        # 3. 返回结构化的测试用例
    
    def generate_batch_tests(self, tool_urls: List[str]) -> BatchTestPlan:
        """生成批量测试计划"""
```

### 3. 验证执行代理 (src/agents/validation_agent.py)

```python
class ValidationAgent:
    """MCP 验证执行代理"""
    
    def __init__(self, model_config: dict, mcp_tools: dict):
        self.agent = ReActAgent(
            name="validation_agent",
            model_config_name="validation_model",
            service_toolkit=self.build_toolkit(mcp_tools)
        )
    
    def execute_test_case(self, test_case: TestCase) -> TestResult:
        """执行单个测试用例"""
        # 1. 调用相应的 MCP 工具
        # 2. 验证返回结果
        # 3. 生成测试报告
    
    def run_batch_validation(self, test_plan: BatchTestPlan) -> BatchTestResult:
        """执行批量验证"""
```

## 使用流程

### 命令行接口

```bash
# 安装环境
uv sync

# 单一 URL 测试
uv run python -m src.main --url "https://lobehub.com/mcp/upstash-context7"

# 批量测试
uv run python -m src.main --batch --input-file data/target_urls.txt

# 指定包名直接测试
uv run python -m src.main --package "@upstash/context7-mcp"

# 生成测试报告
uv run python -m src.main --report --result-dir data/test_results/
```

### Python API 接口

```python
from src.core.mcp_deployer import DynamicMCPDeployer
from src.agents.test_agent import TestGeneratorAgent
from src.agents.validation_agent import ValidationAgent

# 初始化系统
deployer = DynamicMCPDeployer("data/mcp.csv")
test_agent = TestGeneratorAgent(model_config)
validation_agent = ValidationAgent(model_config, {})

# 部署并测试
mcp_info = deployer.deploy_by_url(target_url)
test_cases = test_agent.generate_test_cases(mcp_info)
results = validation_agent.execute_test_case(test_cases[0])
```

## 质量保证

### 测试策略
- **单元测试**: 每个核心模块都有对应的单元测试
- **集成测试**: 端到端的 MCP 部署和验证测试
- **回归测试**: 确保已验证的 MCP 工具持续可用

### 错误处理
- **部署失败**: 自动重试机制和降级策略
- **通信超时**: 配置化的超时设置和恢复机制
- **测试失败**: 详细的错误日志和故障诊断

### 性能优化
- **并行部署**: 支持多个 MCP 工具并行部署
- **资源管理**: 自动清理不活跃的 MCP 服务器
- **缓存机制**: 缓存已部署的工具信息

## 扩展计划

### 短期优化
1. **Web UI**: 提供可视化的测试界面
2. **监控面板**: 实时监控 MCP 服务器状态
3. **测试数据库**: 持久化测试结果和统计信息

### 长期规划
1. **云端部署**: 支持容器化和云端部署
2. **API 网关**: 提供统一的 MCP 服务接口
3. **智能推荐**: 基于使用情况推荐 MCP 工具

## 成功指标

- **部署成功率**: >90% 的 MCP 工具能够成功部署
- **测试覆盖率**: >80% 的工具功能被测试覆盖
- **执行效率**: 单个工具测试时间 <5 分钟
- **稳定性**: 连续运行 24 小时无重大故障

---

*此 MVP 方案基于现有的 `test_crossplatform_mcp.py` 代码，继承其稳定的 MCP 通信机制和跨平台兼容性，同时扩展了动态部署、智能测试生成和大模型协作功能。*
