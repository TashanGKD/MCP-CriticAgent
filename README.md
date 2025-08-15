# 🧪 Batch MCP Testing Platform

现代化的 MCP (Model Context Protocol) 工具测试平台，支持动态部署、自动化测试和可视化报告生成。

## 🌟 全新 Web 版本

项目已重构为 **Next.js + Python** 混合架构，提供现代化的 Web 界面和 Vercel 一键部署支持。

### ✨ 主要特性

- 🌐 **现代化 Web 界面**: 响应式设计，支持移动端
- ⚡ **实时测试进度**: 可视化测试状态和进度
- 🚀 **一键部署**: Vercel 平台无缝部署
- 📊 **可视化报告**: 交互式测试结果展示
- 🔄 **保留所有功能**: 100% 兼容原有 CLI 功能

## 🚀 核心功能

- **🎯 URL 驱动测试**: 输入 GitHub URL → 自动解析包名 → 部署测试 → 生成报告
- **🤖 AI 智能测试**: 集成大语言模型，自动生成针对性测试用例和智能分析
- **📦 自动化部署**: 基于 npm/npx 的跨平台 MCP 工具部署
- **🔧 协议兼容**: 支持 MCP STDIO 协议，自动处理参数兼容性
- **🌐 跨平台支持**: Windows/Linux/macOS 原生兼容
- **📊 详细报告**: JSON/HTML 双格式测试报告，包含 AI 分析结果
- **🗄️ 智能数据库**: 5000+ MCP 工具的预建数据库和智能搜索

## 📋 系统要求

### Web 版本 (推荐)
- **浏览器**: 现代浏览器 (Chrome, Firefox, Safari, Edge)
- **部署**: Vercel 账号 (免费)

### 本地开发
- **Python**: 3.12+
- **Node.js**: 18.0+ 
- **UV**: 现代 Python 包管理器

## 🚀 快速开始

### 方式一: Web 版本 (推荐)

1. **在线访问**: [https://batch-mcp.vercel.app](https://batch-mcp.vercel.app)
2. **输入 GitHub URL**: 例如 `https://github.com/upstash/context7`
3. **开始测试**: 点击测试按钮，实时查看进度
4. **查看结果**: 可视化测试报告和详细数据

### 方式二: 一键部署到你的 Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-username/batch_mcp)

### 方式三: 本地开发

## ⚡ 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd batch_mcp

# 安装依赖 (推荐使用 uv)
uv sync

# 或使用传统方式
pip install -e .
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# 基础配置
OPENAI_API_KEY=your_api_key_here      # 用于 AI 智能测试功能
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# 或使用 DashScope (阿里云通义千问)
DASHSCOPE_API_KEY=your_dashscope_key  # 推荐用于中文环境
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1
DASHSCOPE_MODEL=qwen-plus
```

### 3. 基础使用

```bash
# 🎯 测试单个 GitHub MCP 项目 (启用 AI 智能测试)
uv run python -m src.main test-url "https://github.com/upstash/context7" --smart --timeout 600

# � 使用基础测试模式
uv run python -m src.main test-url "https://github.com/upstash/context7" --timeout 600

# �📦 直接测试 MCP 包
uv run python -m src.main test-package "@upstash/context7-mcp" --timeout 600

# 📝 批量测试 (使用 data/test.csv)
uv run python -m src.main batch-test --file data/test.csv --limit 5

# 🔍 列出数据库中的 MCP 工具
uv run python -m src.main list-tools --limit 10
```

## 🤖 AI 智能测试

当使用 `--smart` 参数时，系统将：

1. **🧠 智能分析**: AI 分析 MCP 工具的功能和参数
2. **📋 生成测试用例**: 自动生成 3-5 个针对性测试用例
3. **🔍 执行验证**: 运行测试并收集结果
4. **📊 智能分析**: AI 分析测试结果并提供改进建议

```bash
# 启用 AI 智能测试
uv run python -m src.main test-url "https://github.com/example/mcp-tool" --smart

# 查看 AI 分析报告
# 报告将包含详细的测试分析和改进建议
```

## 🏗️ 项目架构

```
batch_mcp/
├── src/                          # 源代码
│   ├── core/                     # 核心模块
│   │   ├── simple_mcp_deployer.py    # MCP 部署器 
│   │   ├── async_mcp_client.py       # 异步 MCP 客户端
│   │   └── url_mcp_processor.py      # URL 处理器
│   ├── agents/                   # AI 智能代理
│   │   ├── test_agent.py            # 测试用例生成代理
│   │   └── validation_agent.py      # 测试结果验证代理
│   ├── utils/                    # 工具模块
│   │   └── csv_parser.py            # CSV 数据解析
│   └── main.py                   # 主入口
├── data/                         # 数据文件
│   ├── mcp.csv                      # MCP 工具数据库 (5000+ 条)
│   └── test_results/                # 测试结果
├── test/                         # 测试脚本
├── .github/workflows/            # GitHub Actions (支持 AI 智能测试)
├── .env                          # 环境配置
├── pyproject.toml               # 项目配置
└── README.md                    # 项目文档
```

## 🛠️ 核心功能

### URL 到测试的完整流程

1. **URL 解析**: GitHub URL → 智能匹配数据库中的 MCP 工具
2. **包名映射**: 从 CSV 数据提取正确的 NPM 包名和运行命令
3. **自动部署**: `npx` 部署 MCP 工具，支持参数回退
4. **协议通信**: JSON-RPC over STDIO 协议通信
5. **功能测试**: 初始化、工具列表、基础调用测试
6. **报告生成**: 详细的 JSON/HTML 测试报告

### 支持的测试场景

- ✅ **协议兼容性**: 自动检测并适配不同的启动参数
- ✅ **工具发现**: 验证 MCP 工具的可用性和功能列表
- ✅ **基础调用**: 测试工具的基本调用能力
- ✅ **错误处理**: 详细的错误诊断和恢复建议

## 📈 使用示例

### 成功案例

```bash
# Context7 文档工具
uv run python -m src.main test-url "https://github.com/upstash/context7"

# Svelte 文档工具  
uv run python -m src.main test-url "https://github.com/spences10/mcp-svelte-docs"
```

### 报告示例

测试完成后会在 `data/test_results/reports/` 目录生成：

- `mcp_test_YYYYMMDD_HHMMSS_<session_id>.json`: JSON 格式详细报告
- `mcp_test_YYYYMMDD_HHMMSS_<session_id>.html`: HTML 格式可视化报告

## 🔧 高级配置

### 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥 (智能测试) | 否 |
| `OPENAI_BASE_URL` | OpenAI API 基础 URL | 否 |
| `OPENAI_MODEL` | 使用的模型名称 | 否 |

### 命令行选项

```bash
# 超时设置
--timeout 30

# 智能测试 (需要 OpenAI API)
--smart

# 批量限制
--limit 10

# 详细输出
--verbose
```

## 🚀 GitHub Actions 集成

项目提供 GitHub Actions 工作流，支持：

- 输入 GitHub URL 触发测试
- 自动生成和上传测试报告
- 跨平台 (Ubuntu/Windows) 并行测试

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 📜 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP 协议标准
- [AgentScope](https://github.com/modelscope/agentscope) - 智能代理框架  
- [UV](https://github.com/astral-sh/uv) - 现代 Python 包管理
