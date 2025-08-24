# 🧪 Batch MCP Testing Framework

自动化的 MCP (Model Context Protocol) 工具测试框架，支持动态部署、智能测试和详细报告生成。

## ✨ 主要特性

- **🎯 URL 驱动测试**: 输入 GitHub URL → 自动解析包名 → 部署测试 → 生成报告
- **🤖 AI 智能测试**: 集成大语言模型，自动生成针对性测试用例和智能分析
- **🏆 LobeHub 评分集成**: 完整展示工具的质量等级、评分、Stars/Forks 数据
- **📦 海量工具数据库**: 预建 5000+ MCP 工具数据库，从 mcp.csv 数据源自动加载
- **📊 详细报告**: JSON/HTML 双格式测试报告，包含 AI 分析结果和 LobeHub 评分
- **🔧 协议兼容**: 支持 MCP STDIO 协议，自动处理参数兼容性
- **🌐 跨平台支持**: Windows/Linux/macOS 原生兼容
- **🗃️ 数据库集成**: 自动导出测试结果到 Supabase，支持标准化查询和数据分析

## 📋 系统要求

- **Python**: 3.12+
- **Node.js**: 18.0+ (用于部署MCP工具)
- **UV**: 现代 Python 包管理器

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd mcp_agent

# 安装依赖 (推荐使用 uv)
uv sync

# 或使用传统方式
pip install -e .
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# AI模型配置 (用于智能测试功能)
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# 或使用 DashScope (阿里云通义千问)
DASHSCOPE_API_KEY=your_dashscope_key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1
DASHSCOPE_MODEL=qwen-plus

# Supabase数据库配置 (用于测试结果存储，可选)
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_key
```

### 3. 基础使用

```bash
# 🎯 测试单个 GitHub MCP 项目 (默认启用 AI 智能测试、数据库导出和代码质量评估)
uv run python -m src.main test-url "https://github.com/upstash/context7"

# 🔧 禁用特定功能
uv run python -m src.main test-url "https://github.com/upstash/context7" --no-smart --no-db-export --no-evaluate

# 📦 直接测试 MCP 包 (默认启用全部高级功能)
uv run python -m src.main test-package "@upstash/context7-mcp"

# ⚡ 快速测试模式 (禁用评估，提升测试速度)
uv run python -m src.main test-package "@upstash/context7-mcp" --no-evaluate

# 🔍 列出数据库中的 MCP 工具
uv run python -m src.main list-tools --limit 10

# 🔍 搜索特定工具
uv run python -m src.main list-tools --search "github"
```

### 🎛️ 默认参数说明

从 v2.1.0 开始，以下功能默认启用：

- **`--smart`**: AI 智能测试，生成真实测试用例
- **`--db-export`**: 导出结果到 Supabase 数据库  
- **`--evaluate`**: 代码质量评估 (GitHub 仓库分析)

使用 `--no-smart`、`--no-db-export`、`--no-evaluate` 可禁用对应功能。

## 🏆 LobeHub 评分系统集成

框架完整集成了 LobeHub 的 MCP 工具评分数据，提供工具质量评估：

### 评分数据内容

- **🎖️ 质量等级**: 优质/良好/欠佳 三级分类
- **💯 数值评分**: 0-100 分的具体评分
- **⭐ GitHub Stats**: Stars 和 Forks 数量统计
- **🔗 LobeHub URL**: 工具的 LobeHub 页面链接

### 在报告中的展示

测试报告中会自动展示 LobeHub 评分信息：

```html
<h2>LobeHub 评分</h2>
<div class="stats">
  <div class="stat"><div>质量等级</div><div>优质</div></div>
  <div class="stat"><div>评分</div><div>2.0</div></div>
  <div class="stat"><div>Stars</div><div>19800</div></div>
  <div class="stat"><div>Forks</div><div>1000</div></div>
</div>
<p>📱 <a href="https://lobehub.com/mcp/upstash-context7">LobeHub 页面</a></p>
```

### 数据覆盖率统计

- 总工具数: **5,157** 个
- 有 LobeHub 评级: **604** 个 (11.7%)
- 有数值评分: **587** 个 (11.4%)
- 有 GitHub Stars: **2,819** 个 (54.7%)

## 🤖 AI 智能测试

启用 `--smart` 参数后，框架将使用 AI 代理执行高级测试：

1. **🧠 智能分析**: AI 分析 MCP 工具的功能和参数
2. **📋 生成测试用例**: 自动生成 3-5 个针对性测试用例  
3. **🔍 执行验证**: 运行测试并收集结果
4. **📊 智能分析**: AI 分析测试结果并提供改进建议

```bash
# 启用 AI 智能测试
uv run python -m src.main test-url "https://github.com/example/mcp-tool" --smart
```

## 📊 代码质量评估

启用 `--evaluate` 参数后，框架将对 MCP 工具进行全面的代码质量分析：

### 评估维度

1. **🔄 可持续性评分 (Sustainability Score)**:
   - **活跃度**: 最近提交频率和时间间隔
   - **稳定性**: 代码提交的规律性和间隔标准差
   - **响应性**: Issue 解决速度和维护质量
   - **项目健康度**: 开放 Issue 比例和积压情况

2. **📈 流行度评分 (Popularity Score)**:
   - **GitHub Stars**: 社区认可度 
   - **Fork 数量**: 开发者参与度和二次开发活跃程度

3. **🏆 综合评分 (Final Score)**:
   - 基于可持续性和流行度的加权综合评分 (0-100)

### 数据库字段

评估结果将保存到数据库的以下字段：

- `final_score`: 最终综合评分 (0-100)
- `sustainability_score`: 可持续性评分 (0-100)  
- `popularity_score`: 流行度评分 (0-100)
- `sustainability_details`: 可持续性详细分析 (JSONB)
- `popularity_details`: 流行度详细分析 (JSONB)

```bash
# 执行完整评估 (默认启用)
uv run python -m src.main test-package "@upstash/context7-mcp"

# 快速测试 (禁用评估)
uv run python -m src.main test-package "@upstash/context7-mcp" --no-evaluate
```

## 🏗️ 项目架构

```
mcp_agent/
├── src/                          # 源代码
│   ├── main.py                   # CLI 入口点
│   ├── core/                     # 核心模块
│   │   ├── simple_mcp_deployer.py    # MCP 部署器
│   │   ├── async_mcp_client.py       # 异步 MCP 客户端
│   │   └── url_mcp_processor.py      # URL 处理器
│   ├── agents/                   # AI 智能代理
│   │   ├── test_agent.py         # 测试生成代理
│   │   └── validation_agent.py   # 验证执行代理
│   └── utils/                    # 工具函数
│       ├── csv_parser.py         # CSV 数据解析
│       └── config_loader.py      # 配置加载
├── data/                         # 数据目录
│   ├── mcp.csv                   # 5000+ MCP 工具数据库
│   └── test_results/             # 测试结果和报告
├── docs/                         # 文档
│   ├── README.md                 # 项目说明
│   ├── QUICKSTART.md             # 快速开始
│   └── workflow.md               # 架构和流程
├── test/                         # 测试模块
├── .env                          # 环境变量配置
└── pyproject.toml                # UV 项目配置
```

## 🛠️ 核心工作流程

### URL 到测试的完整流程

1. **URL 解析**: GitHub URL → 智能匹配数据库中的 MCP 工具
2. **包名映射**: 从 CSV 数据提取正确的 NPM 包名和运行命令
3. **自动部署**: `npx` 部署 MCP 工具，支持参数回退
4. **协议通信**: JSON-RPC over STDIO 协议通信
5. **功能测试**: 初始化、工具列表、基础/智能调用测试
6. **报告生成**: 详细的 JSON/HTML 测试报告

### 支持的测试场景

- ✅ **协议兼容性**: 自动检测并适配不同的启动参数
- ✅ **工具发现**: 验证 MCP 工具的可用性和功能列表
- ✅ **基础调用**: 测试工具的基本调用能力
- ✅ **AI智能测试**: 自动生成和执行复杂测试用例
- ✅ **错误处理**: 详细的错误诊断和恢复建议

## 📈 使用示例

```bash
# Context7 文档工具
uv run python -m src.main test-url "https://github.com/upstash/context7"

# Svelte 文档工具  
uv run python -m src.main test-url "https://github.com/spences10/mcp-svelte-docs"
```

## 📊 测试报告

测试完成后，报告将保存在 `data/test_results/` 目录下：

- **JSON 格式**: 机器可读的详细测试数据
- **HTML 格式**: 人类友好的可视化报告

## 🗄️ 数据库集成

### 功能概述

框架支持将测试结果自动导出到 Supabase 数据库，实现：

- **📊 历史追踪**: 追踪 MCP 工具的测试历史和性能变化
- **📈 成功率分析**: 统计部署、通信、测试的成功率
- **🔍 数据查询**: 支持复杂查询和数据分析
- **🔗 第三方集成**: 其他程序可通过标准 API 获取测试数据

### 使用方法

```bash
# 测试并导出到数据库
uv run python -m src.main test-url "https://github.com/upstash/context7" --db-export

# 批量导入现有测试结果
python import_test_results.py

# 验证数据库数据
python verify_import.py
```

### 数据库结构

采用 Linus 式单表设计，一次测试一行记录：

```sql
CREATE TABLE mcp_test_results (
    test_id UUID PRIMARY KEY,
    test_timestamp TIMESTAMP WITH TIME ZONE,
    tool_identifier TEXT NOT NULL,
    tool_name TEXT,
    tool_author TEXT,
    test_success BOOLEAN NOT NULL,
    deployment_success BOOLEAN NOT NULL,
    communication_success BOOLEAN NOT NULL,
    available_tools_count INTEGER,
    test_duration_seconds FLOAT,
    error_messages TEXT[],
    test_details JSONB,
    environment_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE
);
```

### 数据访问 API

其他程序可按照 `docs/SUPABASE_API_SPEC.md` 规范访问测试数据：

```python
from supabase import create_client

client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# 获取最新测试结果
recent_tests = client.from_('mcp_test_results').select('*').order('test_timestamp', desc=True).limit(10).execute()

# 获取成功率统计
success_stats = client.from_('mcp_test_results').select('test_success').execute()
```  
- **控制台输出**: 实时测试进度和结果摘要

## 🔧 开发和贡献

```bash
# 开发模式安装
uv sync --dev

# 运行测试
uv run pytest

# 代码格式化
uv run black src/

# 环境检查
uv run python -m src.main init-env
```

## 🚀 GitHub Actions 工作流

### 单工具测试工作流
- **文件**: `.github/workflows/simple-mcp-test.yml`
- **触发**: 手动触发，输入GitHub URL
- **功能**: 测试单个MCP工具，生成详细报告，支持GitHub Pages发布
- **默认启用**: AI智能测试、数据库导出、代码质量评估

### 压力测试工作流
- **文件**: `.github/workflows/mcp-stress-test.yml`  
- **触发**: 手动触发或每周日自动执行
- **功能**: 批量测试多个MCP工具，生成压测报告
- **默认启用**: AI智能测试、数据库导出、代码质量评估
- **配置参数**:
  - `test_limit`: 测试工具数量限制（默认50）
  - `deployment_method`: 部署方式过滤（npx/pip/all）
  - `timeout_per_tool`: 单工具超时时间（默认300s）
  - `smart_mode`: 启用AI智能测试（默认true）
  - `category_filter`: 按类别过滤工具（可选）

**压测特性**:
- 📊 按LobeHub评分排序（优质工具优先测试）
- 🔄 最多3个工具并发测试，每个工具执行完整评估
- 📈 实时进度显示和成功率统计
- 📄 详细结果报告和GitHub Pages发布
- ⏰ 支持定时自动压测
- 🗄️ 自动保存测试结果到Supabase数据库

## 📝 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

**在 MCP 生态系统中建设可靠的测试基础设施** 🔧
