# 🚀 5分钟快速开始指南

## 📝 您需要做什么

这是一个 **Python CLI 工具**，用于自动化测试 MCP (Model Context Protocol) 工具。只需5步即可开始测试！

## 1️⃣ 环境检查 (1分钟)

```bash
# 检查环境要求
python --version    # 需要 Python 3.12+
node --version      # 需要 Node.js 18+
npx --version       # 需要 npx (用于部署MCP工具)
```

## 2️⃣ 安装项目 (2分钟)

```bash
# 克隆项目
git clone <repository-url>
cd mcp_agent

# 安装依赖 (推荐使用 uv)
uv sync

# 或使用传统方式
pip install -e .
```

## 3️⃣ 环境配置 (1分钟) - 可选

如需 AI 智能测试功能，创建 `.env` 文件：

```bash
# OpenAI API (可选，用于AI智能测试)
OPENAI_API_KEY=your_api_key_here

# 或使用 DashScope (阿里云，推荐中文用户)
DASHSCOPE_API_KEY=your_dashscope_key
```

## 4️⃣ 立即开始测试 (1分钟)

```bash
# 基础测试 - 测试经典的Context7工具
uv run python -m src.main test-url "https://github.com/upstash/context7"

# 启用AI智能测试 (需要API Key)
uv run python -m src.main test-url "https://github.com/upstash/context7" --smart

# 查看所有可用工具 (5000+工具数据库)
uv run python -m src.main list-tools --limit 10
```

## 5️⃣ 查看结果

测试完成后：
- **控制台输出**: 实时显示测试进度和结果
- **报告文件**: 保存在 `data/test_results/` 目录
- **JSON格式**: 机器可读的详细数据
- **HTML格式**: 人类友好的可视化报告

## 🎯 常用命令

```bash
# 直接测试npm包
uv run python -m src.main test-package "@upstash/context7-mcp"

# 搜索工具
uv run python -m src.main list-tools --search "github"

# 环境检查
uv run python -m src.main init-env

# 批量测试
uv run python -m src.main batch-test --input data/test.csv
```

## ❓ 常见问题

**Q: 测试失败怎么办？**  
A: 检查 Node.js 是否安装，运行 `uv run python -m src.main init-env` 诊断

**Q: 没有 API Key 可以使用吗？**  
A: 可以！基础测试功能无需 API Key，AI 智能测试功能才需要

**Q: 支持哪些 MCP 工具？**  
A: 支持 5000+ 工具，使用 `list-tools` 命令查看

## 🎉 完成！

你现在可以：
- 测试任何 GitHub 上的 MCP 工具
- 使用 AI 自动生成测试用例  
- 生成详细的测试报告
- 批量测试多个工具

**需要帮助？** 查看 [完整文档](README.md) 或 [工作流程](workflow.md)

然后验证配置：
```bash
uv run python src/tools/setup_validator.py
```

## ✅ 完成！

如果看到"🎉 所有验证都通过!"，就可以运行：
```bash
uv run python src/main.py
```

## 🆘 需要帮助？

- 详细步骤：查看 `docs/SUPABASE_CHECKLIST.md`
- 完整文档：查看 `docs/SUPABASE_SETUP.md`
- 有问题时查看终端错误信息
