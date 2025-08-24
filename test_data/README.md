# MCP测试框架

这是一个用于测试Model Context Protocol (MCP)工具的自动化框架。

## 主要功能

- 🚀 自动化MCP工具部署 (npx/uvx)
- 🧪 智能测试用例生成
- 📊 详细的测试报告
- 🗄️ 数据库结果存储
- 🔍 GitHub仓库评估

## 快速开始

```bash
# 安装依赖
uv sync

# 测试单个工具
uv run python -m src.main test-url "https://github.com/example/mcp-tool"

# 批量测试
uv run python -m src.main batch-test --input data/test.csv
```

## 支持的文件格式

- CSV: 员工数据、销售记录
- Excel: 多工作表财务数据  
- JSON: 配置文件、API响应
- PDF: 报告文档
- PowerPoint: 演示文稿

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

MIT License
