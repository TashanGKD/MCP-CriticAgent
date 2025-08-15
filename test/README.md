# MCP工具测试框架

## 概述
这是一个跨平台的Model Context Protocol (MCP) 工具测试框架，支持Windows、Linux、macOS环境下的MCP工具验证和集成测试。

## 文件结构

### 核心文件
- `test_crossplatform_mcp.py` - **跨平台通用MCP测试框架** (推荐使用)
- `test_single_mcp_tool.py` - **单工具快速测试脚本**
- `mcp_tools_config.py` - **MCP工具配置文件**
- `universal_mcp_test_report.md` - **测试报告模板**

### 配置文件
- `mcp_test_summary.py` - 测试结果跟踪工具

## 快速开始

### 1. 环境准备
```bash
# 安装Python依赖
uv add agentscope python-dotenv

# 安装Node.js (用于MCP服务器)
# Windows: 从 https://nodejs.org 下载安装
# Linux: sudo apt install nodejs npm
# macOS: brew install node

# 配置环境变量
cp .env.example .env
# 编辑.env文件，填入你的OpenAI API配置
```

### 2. 单工具测试
```bash
# 测试Context7工具
python test_single_mcp_tool.py context7

# 测试YouTube工具  
python test_single_mcp_tool.py youtube

# 详细输出模式
python test_single_mcp_tool.py svelte --verbose
```

### 3. 全量测试
```bash
# 测试所有工具
python test_crossplatform_mcp.py --all

# 查看平台信息
python test_crossplatform_mcp.py --info

# 测试指定工具
python test_crossplatform_mcp.py --tool context7
```

## 支持的MCP工具

| 工具名 | 包名 | 功能 | 状态 |
|--------|------|------|------|
| context7 | @upstash/context7-mcp | 库文档查询 | ✅ 已验证 |
| youtube | @limecooler/yt-info-mcp | 视频信息获取 | ✅ 已验证 |
| think | minimal-think-mcp | 思考分析 | ✅ 已验证 |
| svelte | mcp-svelte-docs | Svelte文档 | ✅ 已验证 |
| 12306 | 12306-mcp | 火车票查询 | ✅ 已验证 |
| openalex | openalex-mcp | 学术检索 | ⚠️ 需要API密钥 |

## 技术特性

### 跨平台兼容
- ✅ Windows (PowerShell/CMD)
- ✅ Linux (Bash/Zsh)  
- ✅ macOS (Bash/Zsh)

### 核心功能
- 🔄 自动MCP服务器部署
- 🔧 动态工具函数创建
- 📡 异步MCP协议通信
- 🛡️ 完善的错误处理
- 📊 详细的测试报告

### 技术栈
- **AgentScope**: AI智能体框架
- **MCP**: Model Context Protocol (JSON-RPC 2.0)
- **Node.js**: MCP服务器运行环境
- **Python**: 测试框架实现语言

### `test_agentscope_basic.py`

**基础功能验证脚本** - 验证 AgentScope 基本功能是否正常。

#### 功能特性：
- ✅ 依赖导入检查
- ✅ 环境配置验证
- ✅ ServiceToolkit 功能测试
- ✅ AgentScope 初始化验证
- ✅ 智能体创建测试
- ✅ 简单对话功能验证

#### 使用方法：
```bash
uv run python tests/tools/test_agentscope_basic.py
```

### `test_agentscope_react_verification.py` 

**已验证的ReActAgent工具调用验证** - 使用 ReActAgent 验证真实的工具调用。

#### 主要特性：
1. **真实工具调用验证**
   - 使用 ReActAgent（支持 service_toolkit）
   - 工具调用追踪和统计
   - 唯一验证标识符生成
   - 推理过程可视化（verbose=True）

2. **完整的验证机制**
   - 工具调用计数器
   - 响应内容验证
   - 唯一标识符匹配
   - 调用统计分析

3. **测试场景覆盖**
   - 时间戳获取测试
   - 引用生成测试  
   - 数学计算测试
   - 系统状态测试

#### 使用方法：
```bash
uv run python tests/tools/test_agentscope_react_verification.py
```

#### 验证结果示例：
```
✅ 测试 1 通过: 时间戳获取
📊 工具调用统计:
   总调用次数: 1
   成功调用: 1  
   调用工具: get_current_timestamp
   验证标识: 发现唯一标识符 CALL_123abc_1692123456
```

## 快速开始

### 1. 环境准备

确保已配置 `.env` 文件：

```bash
# API 配置
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-flash

# AgentScope 配置
MODEL_TYPE=openai_chat
MODEL_NAME=qwen-flash
CONFIG_NAME=qwen-flash

# MCP 配置
CONTEXT7_API_KEY=demo_token
MCP_TIMEOUT=30

# 项目配置
AGENTSCOPE_PROJECT_NAME=MCP_Test
PROJECT_DEBUG=false
```

### 2. 安装依赖

```bash
uv sync
# 或
uv add agentscope[service] python-dotenv
```

### 3. 运行测试

```bash
# 基础功能测试（推荐先运行）
uv run python tests/tools/test_agentscope_basic.py

# ReActAgent 工具调用验证
uv run python tests/tools/test_agentscope_react_verification.py

# 真实MCP服务器集成测试
## 快速开始

```bash
# 基础功能验证
uv run python tests/tools/test_agentscope_basic.py

# 工具调用验证（推荐）  
uv run python tests/tools/test_agentscope_react_verification.py

# 基于CSV的简化MCP工具验证（最新）
uv run python tests/tools/test_simplified_mcp_verification.py
```

## 测试特性

### 核心验证机制

| 验证项目 | test_basic | test_react | test_simplified |
|---------|------------|------------|-----------------|
| 基础功能 | ✅ | ✅ | ✅ |
| 工具调用追踪 | ❌ | ✅ | ✅ |
| 唯一标识验证 | ❌ | ✅ | ✅ |
| CSV数据集成 | ❌ | ❌ | ✅ |
| 多场景测试 | ❌ | ✅ | ✅ |

### 简化版MCP验证特性

| 测试场景 | 模拟工具 | 验证要点 |
|---------|----------|----------|
| YouTube信息 | youtube_video_info | 媒体信息获取 |
| 思考分析 | minimal_think_analysis | 复杂问题分析 |
| 文档搜索 | svelte_docs_search | 技术文档查询 |
| 学术搜索 | academic_paper_search | 学术资源获取 |
| 出行查询 | train_ticket_query | 实用信息服务 |
| 知识搜索 | context7_search | 综合信息检索 |

### 验证成功标准

1. **工具调用成功率**: ≥75% 的测试场景通过
2. **唯一标识检测**: 每次工具调用生成并在响应中找到唯一token
3. **调用统计准确**: 正确记录工具调用次数和类型
4. **响应完整性**: 工具返回预期的数据结构和内容

## 已修复的问题

1. **编码问题**: 移除所有 Unicode 特殊字符，确保在 Windows GBK 环境下正常运行
2. **导入错误**: 移除不存在的 `MemoryType` 导入
3. **参数兼容性**: 根据 AgentScope 0.1.6 版本调整 DialogAgent 参数
4. **工具调用验证**: 发现并解决了 DialogAgent 不支持 service_toolkit 的问题
5. **脚本冗余**: 删除了无效的测试脚本，保留最核心和有效的验证方案

## 关键发现

### AgentScope 智能体类型差异

| 智能体类型 | 支持 service_toolkit | 工具调用能力 | 适用场景 |
|------------|---------------------|-------------|----------|
| `DialogAgent` | ❌ 不支持 | 无法真实调用工具 | 简单对话场景 |
| `ReActAgent` | ✅ 支持 | 支持真实工具调用 | 需要工具集成的复杂任务 |

### 真实工具调用验证机制

1. **工具调用追踪器**: 记录每次工具调用的详细信息
2. **唯一标识符验证**: 每次工具调用生成唯一token进行验证
3. **实时调用统计**: 追踪工具调用次数和类型
4. **响应内容验证**: 确认响应包含工具生成的真实数据

## 开发注意事项

### AgentScope 版本兼容性

当前测试基于 AgentScope 0.1.6 版本：

- ⚠️ `DialogAgent` 不支持 `service_toolkit` 参数 - 无法进行真实工具调用
- ✅ `ReActAgent` 支持 `service_toolkit` 参数 - 这是正确的工具集成方式
- `MemoryType` 枚举不存在，使用默认内存管理
- ServiceToolkit 需要与 ReActAgent 配合使用

### 环境要求

- Python >= 3.12
- AgentScope >= 0.1.6
- 有效的通义千问 API 密钥
- Windows/Linux/macOS 兼容

### 故障排除

1. **编码错误**: 设置 `$env:PYTHONIOENCODING="utf-8"`
2. **API 限流**: 检查 API 密钥配额和调用频率
3. **网络问题**: 确保能访问 DashScope API 服务
4. **依赖冲突**: 使用 `uv sync` 重新同步依赖

## 贡献指南

1. 遵循现有的代码风格和结构
2. 添加新功能时确保包含相应的测试用例
3. 更新文档以反映任何新的功能或变更
4. 确保所有测试通过后再提交代码

## 许可证

本项目遵循 MIT 许可证。
MCP_TIMEOUT=30
MCP_EVAL_MAX_WORKERS=3
MCP_EVAL_LOG_LEVEL=INFO
```

### 4. 运行测试

#### 基础 MCP 测试
```bash
uv run python tests/tools/test_agentscope_context7_basic.py
```

这个脚本演示了：
- ✅ AgentScope 环境初始化
- ✅ MCP 服务器连接 (Context7)
- ✅ 智能体创建和配置
- ✅ 基本的文档查询功能
- ✅ 工具使用和响应处理

#### 交互式 MCP 测试
```bash
uv run python tests/tools/test_agentscope_mcp_interactive.py
```

这个脚本提供了：
- 🎯 交互式命令行界面
- 🔧 多种 MCP 服务器支持
- 📊 会话统计和监控
- 🛠️ 工具使用分析
- 💬 多轮对话管理

#### 简化功能测试
```bash
uv run python tests/tools/test_simple.py
```

这个脚本验证：
- 📦 核心模块导入
- ⚙️ 基础配置检查
- 🤖 智能体创建
- 🛠️ 工具集成

## 🔧 核心功能

### AgentScope 集成

本项目使用 AgentScope 框架实现多智能体系统：

```python
import agentscope
from agentscope.agents import DialogAgent
from agentscope.service import ServiceToolkit

# 初始化 AgentScope
agentscope.init(
    model_configs=[model_config],
    project="MCP_Test"
)

# 创建智能体
agent = DialogAgent(
    name="mcp_assistant",
    model_config_name="qwen-flash",
    sys_prompt="你是一个智能技术助手...",
    service_toolkit=toolkit
)
```

### MCP 服务器连接

支持多种 MCP 连接方式：

```python
# HTTP SSE 协议 (远程)
mcp_configs = {
    "mcpServers": {
        "context7": {
            "url": "https://context7.dev/mcp/sse",
            "headers": {
                "Authorization": "Bearer your_token"
            }
        }
    }
}

# STDIO 协议 (本地)
local_configs = {
    "mcpServers": {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"]
        }
    }
}

# 添加到服务工具包
toolkit = ServiceToolkit()
toolkit.add_mcp_servers(server_configs=mcp_configs)
```

### 智能工具调用

智能体可以自动选择和使用可用的工具：

```python
# 用户查询
user_msg = Msg("user", "请搜索关于 AgentScope 的文档", role="user")

# 智能体自动调用 MCP 工具并回复
response = agent(user_msg)
print(response.content)
```

## 📋 测试场景

### 基础测试场景

1. **文档搜索**: "请帮我搜索关于 AgentScope 多智能体框架的基本信息"
2. **技术查询**: "如何在 AgentScope 中使用 MCP 协议?"
3. **功能介绍**: "AgentScope 支持哪些类型的智能体?"

### 交互式测试功能

- `/help` - 显示帮助信息
- `/stats` - 查看会话统计
- `/tools` - 显示可用工具
- `/exit` - 退出会话

## 🛠️ 故障排除

### 常见问题

1. **导入错误**
   ```bash
   # 确保安装了完整的 AgentScope
   uv add "agentscope[service]"
   ```

2. **API 密钥错误**
   ```bash
   # 检查 .env 文件配置
   cat .env
   ```

3. **ServiceToolkit 属性错误**
   ```python
   # ❌ 错误的属性访问
   len(toolkit.tools)  # AttributeError
   
   # ✅ 正确的属性访问
   len(toolkit.service_funcs)  # 服务函数数量
   len(toolkit.json_schemas)   # JSON Schema 数量
   list(toolkit.service_funcs.keys())  # 工具名称列表
   toolkit.tools_instruction  # 工具使用说明
   ```

4. **MCP 连接失败**
   - 检查网络连接
   - 验证 MCP 服务器地址
   - 确认认证信息

### 调试模式

启用调试模式获取详细信息：

```bash
# 在 .env 中设置
PROJECT_DEBUG=true
MCP_EVAL_LOG_LEVEL=DEBUG
```

## 📚 参考资源

- [AgentScope 官方文档](https://doc.agentscope.io/)
- [AgentScope MCP 集成指南](https://doc.agentscope.io/zh_CN/build_tutorial/MCP.html)
- [Model Context Protocol 规范](https://modelcontextprotocol.io/)
- [Context7 MCP 服务](https://context7.dev/)

## 🎯 下一步计划

- [ ] 集成更多 MCP 服务器
- [ ] 添加性能监控
- [ ] 实现错误恢复机制
- [ ] 扩展工具库功能
- [ ] 添加单元测试覆盖

## 📄 许可证

MIT License - 详见 LICENSE 文件。
