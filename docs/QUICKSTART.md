# 🚀 MCP测试框架 - 快速入门指南

## 📋 5分钟快速开始

### 第一步：安装和配置

```bash
# 1. 克隆项目
git clone <repository-url>
cd mcp_agent

# 2. 安装依赖
uv sync

# 3. 环境检查
uv run python -m src.main init-env
```

### 第二步：基础测试

```bash
# 测试一个简单的 MCP 工具
uv run python -m src.main test-url "https://github.com/upstash/context7"
```

期望输出：
```
🎯 开始测试 MCP 工具: https://github.com/upstash/context7
✅ 找到工具: Context7 MCP - 最新代码文档适用于任何提示
📦 开始部署 MCP 工具...
✅ MCP 工具部署成功
🔄 开始测试 MCP 工具功能...
📊 生成测试报告...
✅ JSON 报告已保存: data/test_results/mcp_test_*.json
✅ HTML 报告已保存: data/test_results/mcp_test_*.html
🎉 https://github.com/upstash/context7 测试完成！
```

### 第三步：查看测试报告

测试完成后，打开 `data/test_results/` 目录中的 HTML 文件查看详细报告。

---

## 🤖 AI智能测试 (推荐)

### 配置 AI 模型

创建 `.env` 文件：

```bash
# 使用 OpenAI
OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# 或使用阿里云通义千问
DASHSCOPE_API_KEY=sk-your-dashscope-key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen-plus
```

### 启用智能测试

```bash
# AI 智能测试
uv run python -m src.main test-url "https://github.com/upstash/context7" --smart
```

智能测试会：
- 🧠 自动分析工具功能
- 📋 生成针对性测试用例
- 🔍 执行高级验证
- 📊 提供智能分析报告

---

## 🗄️ 数据库集成 (可选)

### 配置数据库

在 `.env` 文件中添加：

```bash
# Supabase配置
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_key
```

### 启用数据库导出

```bash
# 测试并导出到数据库
uv run python -m src.main test-url "https://github.com/upstash/context7" --smart --db-export
```

### 验证数据导入

```bash
# 检查数据库连接
python simple_db_test.py

# 查看导入的数据
python verify_import.py
```

---

## 📋 常用命令速查

### 基础测试
```bash
# 测试 GitHub URL
uv run python -m src.main test-url "https://github.com/username/repo"

# 测试 NPM 包
uv run python -m src.main test-package "@username/package-name"

# 列出可用工具
uv run python -m src.main list-tools --limit 10
```

### 高级功能
```bash
# AI智能测试
uv run python -m src.main test-url "URL" --smart

# 数据库导出
uv run python -m src.main test-url "URL" --db-export

# 详细输出
uv run python -m src.main test-url "URL" --verbose

# 自定义超时
uv run python -m src.main test-url "URL" --timeout 300
```

### 数据管理
```bash
# 批量导入测试结果
python import_test_results.py

# 验证数据库
python verify_import.py

# 快速连接检查
python quick_table_check.py
```

---

## 🔧 故障排除

### 常见问题

**1. Node.js 版本过低**
```bash
# 检查 Node.js 版本
node --version  # 需要 >= 18.0.0

# 更新 Node.js
# Windows: 下载最新版本安装包
# macOS: brew install node
# Linux: 使用包管理器更新
```

**2. UV 未安装**
```bash
# 安装 UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**3. 测试失败**
```bash
# 检查环境
uv run python -m src.main init-env

# 详细调试
uv run python -m src.main test-url "URL" --verbose
```

**4. 数据库连接失败**
```bash
# 检查配置
cat .env | grep SUPABASE

# 测试连接
python simple_db_test.py
```

### 获取帮助

```bash
# 查看帮助
uv run python -m src.main --help

# 查看命令帮助
uv run python -m src.main test-url --help
```

---

*"Talk is cheap. Show me the code."* - 开始您的第一个测试吧！ 🚀
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
