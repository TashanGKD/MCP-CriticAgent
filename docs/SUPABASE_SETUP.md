# Supabase数据库设置指南

本文档说明如何为MCP测试框架设置Supabase数据库。

## 前提条件

1. 需要一个Supabase账户
2. 创建一个新的Supabase项目

## 设置步骤

### 1. 创建Supabase项目

1. 访问 [Supabase Dashboard](https://app.supabase.com)
2. 注册或登录账户
3. 点击 "New project" 按钮
4. 填写项目信息：
   - **Organization**: 选择您的组织（通常是您的用户名）
   - **Project name**: 建议使用 `mcp-testing` 或 `mcp-agent-db`
   - **Database Password**: 设置一个强密码（至少8位，包含数字和字母）
   - **Region**: 选择离您最近的区域（如 `ap-northeast-1` 为亚太东京）
5. 点击 "Create new project"
6. 等待2-3分钟项目创建完成

### 2. 获取API密钥

在项目仪表板中：

1. 项目创建完成后，进入项目主页
2. 在左侧菜单中找到 **Settings** 
3. 点击 **API** 子菜单
4. 在 "Project API keys" 部分，您会看到：
   - **Project URL**: 形如 `https://abcdefghijk.supabase.co`
   - **anon public**: 以 `eyJ` 开头的长字符串（公开密钥）
   - **service_role**: 以 `eyJ` 开头的长字符串（服务密钥，⚠️ 请保密）

**重要提示**: 
- `anon public` 密钥可以在前端使用
- `service_role` 密钥拥有完全访问权限，只能在服务器端使用
- 绝不要将 `service_role` 密钥暴露在公开代码中

### 3. 配置环境变量

1. 在项目根目录找到 `.env.template` 文件
2. 复制一份并重命名为 `.env`：
   ```bash
   copy .env.template .env
   ```
3. 编辑 `.env` 文件，将您从Supabase获取的信息填入：

```bash
# Supabase配置（必填）
SUPABASE_URL=https://你的项目ID.supabase.co
SUPABASE_KEY=你的anon_public密钥
SUPABASE_SERVICE_ROLE_KEY=你的service_role密钥

# 其他配置保持默认即可（可选）
ENVIRONMENT=development
LOG_LEVEL=INFO
```

**配置示例**：
```bash
# 真实配置示例（密钥已脱敏）
SUPABASE_URL=https://abcdefghijk.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6...
```

### 4. 初始化数据库结构

**重要**: Supabase项目初始为空数据库，需要创建我们的表结构。

运行以下命令初始化：

```bash
# 1. 首先测试连接（确保配置正确）
uv run python src/tools/db_migrate.py test

# 2. 初始化数据库结构（创建所有表）
uv run python src/tools/db_migrate.py init

# 3. 填充示例数据（可选，用于测试）
uv run python src/tools/db_migrate.py seed
```

**预期输出示例**：
```
🔍 测试数据库连接...
✅ 数据库连接成功!
✅ 表 mcp_tools 存在
✅ 表 test_reports 存在
...

🚀 初始化数据库结构...
📋 准备执行 45 条SQL语句...
✅ (1/45) 执行成功
✅ (2/45) 执行成功
...
🎉 数据库初始化完成！
```

**如果遇到错误**：
- 检查网络连接
- 确认密钥配置正确
- 查看终端详细错误信息

### 5. 验证设置

```bash
# 查看数据库状态
uv run python src/tools/db_migrate.py status
```

## 数据库结构

数据库包含以下主要表：

### 核心表

1. **mcp_tools** - MCP工具信息
2. **test_reports** - 测试报告主表
3. **deployments** - 部署记录
4. **test_executions** - 测试执行详情
5. **available_tools** - 可用工具列表
6. **quality_metrics** - 质量指标
7. **performance_metrics** - 性能指标

### 视图

1. **test_reports_overview** - 测试报告概览
2. **mcp_tools_stats** - 工具统计
3. **performance_trends** - 性能趋势

## 权限配置

数据库使用Row Level Security (RLS)：

- **认证用户**: 可读取所有数据
- **服务角色**: 可读写所有数据
- **匿名用户**: 无权限

## 数据保留

- 默认保留90天的测试数据
- 可通过环境变量 `DATA_RETENTION_DAYS` 调整
- 可使用清理命令：`uv run python src/tools/db_migrate.py clean --confirm`

## 故障排除

### 常见问题

1. **连接失败**
   - 检查网络连接
   - 验证URL和密钥正确性
   - 确认项目状态正常

2. **权限错误**
   - 确认使用了正确的service_role密钥
   - 检查RLS策略

3. **表不存在**
   - 运行 `db_migrate.py init` 创建表结构

### 调试命令

```bash
# 详细连接测试
uv run python -c "
from src.core.supabase_connector import get_supabase_connector
connector = get_supabase_connector()
print('连接状态:', connector.test_connection() if connector else 'Failed')
"

# 检查环境变量
uv run python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('URL:', os.getenv('SUPABASE_URL'))
print('KEY长度:', len(os.getenv('SUPABASE_KEY', '')))
print('SERVICE_KEY长度:', len(os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')))
"
```

### 5. 验证配置

运行验证脚本确保一切配置正确：

```bash
# 运行完整验证
uv run python src/tools/setup_validator.py
```

**预期输出**：
```
🚀 Supabase 配置验证开始...

🔍 检查环境变量配置...
  ✅ SUPABASE_URL: https://xxx...
  ✅ SUPABASE_SERVICE_ROLE_KEY: eyJhbGci...

🔗 测试Supabase连接...
  ✅ 连接成功! 数据库可访问

🗄️ 检查数据库表结构...
  ✅ 表 mcp_tools 存在
  ✅ 表 test_reports 存在
  ✅ 表 test_executions 存在
  ...
  🎉 所有表都已正确创建!

📊 验证结果汇总:
  ✅ 通过 环境变量配置
  ✅ 通过 Supabase连接
  ✅ 通过 数据库表结构

🎉 所有验证都通过! 系统已准备就绪
💡 现在可以运行: uv run python src/main.py
```

**如果验证失败**：
1. 检查网络连接
2. 确认.env文件配置
3. 重新获取API密钥
4. 查看详细错误信息


## 安全注意事项

1. **绝不** 将service_role密钥提交到版本控制
2. 在生产环境中定期轮换密钥
3. 限制service_role密钥的使用范围
4. 定期审查RLS策略

## 高级配置

### 备份策略

Supabase自动提供：
- 实时备份
- 时间点恢复
- 数据导出功能

### 扩展功能

可启用的PostgreSQL扩展：
- `uuid-ossp`: UUID生成
- `pg_stat_statements`: 性能监控
- `pg_cron`: 定时任务（付费计划）

### 监控

在Supabase Dashboard中可以监控：
- 数据库使用情况
- API调用统计
- 性能指标
- 错误日志
