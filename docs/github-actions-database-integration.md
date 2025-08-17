# GitHub Actions数据库集成配置指南

## 概述
为了在GitHub Actions工作流中启用数据库存储功能，您需要配置Supabase secrets。

## 必需的Secrets配置

在您的GitHub仓库中，前往 `Settings` > `Secrets and variables` > `Actions`，添加以下secrets：

### Supabase数据库配置（必需）
- **`SUPABASE_URL`**: 您的Supabase项目URL（例如：`https://your-project.supabase.co`）
- **`SUPABASE_SERVICE_ROLE_KEY`**: 您的Supabase service_role密钥（**注意：必须是service_role密钥，不是anon密钥**）

### AI智能测试配置（可选，但推荐）
- **`OPENAI_API_KEY`**: OpenAI API密钥
- **`OPENAI_BASE_URL`**: OpenAI API基础URL（可选）
- **`OPENAI_MODEL`**: 使用的OpenAI模型（可选，默认为gpt-4）

或者

- **`DASHSCOPE_API_KEY`**: 阿里云DashScope API密钥
- **`DASHSCOPE_BASE_URL`**: DashScope API基础URL（可选）
- **`DASHSCOPE_MODEL`**: 使用的模型（可选，默认为qwen-plus）

## 数据库表结构

当配置完成后，GitHub Actions工作流将自动把测试结果保存到以下7个Supabase表中：

### 1. 🧪 test_reports (测试报告主表)
- **用途**: 存储每次测试运行的概要信息
- **关键字段**: test_run_id, timestamp, total_tools, tools_tested, tools_successful, overall_status
- **数据示例**: 测试ID、测试时间、成功率、总体状态

### 2. 🛠️ mcp_tools (MCP工具信息表)
- **用途**: 存储MCP工具的元数据信息
- **关键字段**: name, author, github_url, package_name, category, description
- **数据示例**: 工具名称、作者、GitHub链接、包名、分类

### 3. ⚡ test_executions (测试执行详情表)
- **用途**: 存储每个测试用例的执行详情
- **关键字段**: report_id, tool_id, status, execution_time_seconds, test_data
- **数据示例**: 执行状态、运行时间、测试数据、错误信息

### 4. 📈 quality_metrics (质量指标表)
- **用途**: 存储测试质量评估指标
- **关键字段**: report_id, success_rate, performance_score, reliability_score, overall_quality_score
- **数据示例**: 成功率、性能评分、可靠性评分、综合质量分数

### 5. 🚀 performance_analysis (性能分析表)
- **用途**: 存储性能相关的分析数据
- **关键字段**: report_id, avg_execution_time, max_execution_time, avg_memory_usage
- **数据示例**: 平均执行时间、最大执行时间、内存使用情况

### 6. 🚀 deployment_info (部署信息表)
- **用途**: 存储MCP工具的部署状态和信息
- **关键字段**: report_id, status, environment, deployment_time, deployment_duration_seconds
- **数据示例**: 部署状态、环境信息、部署时间、部署耗时

### 7. 📋 test_metadata (测试元数据表)
- **用途**: 存储测试相关的元数据信息
- **关键字段**: report_id, test_framework_version, git_commit, test_tags
- **数据示例**: 框架版本、Git提交信息、测试标签

## 工作流增强功能

### 数据库验证步骤
新增的 `Database Storage Verification` 步骤将：
- 验证数据库连接是否正常
- 统计各表中的最新记录数量
- 生成数据库统计报告（db_stats.json）

### 增强的摘要报告
GitHub Actions的摘要将包含：
- 数据库存储状态（已启用/未启用）
- 各表的数据存储统计
- 数据库验证结果

### 构建产物
除了原有的测试报告文件外，还将包含：
- `db_stats.json`: 数据库存储统计信息
- 所有测试报告文件（JSON、HTML格式）

## 使用方法

1. 在Supabase中创建项目并执行 `database/init_complete.sql` 初始化脚本
2. 在GitHub仓库中配置必要的Secrets
3. 触发GitHub Actions工作流
4. 查看Actions摘要中的数据库存储统计
5. 从构建产物中下载详细的数据库统计文件

## 数据查询示例

配置完成后，您可以在Supabase Dashboard中查询数据：

```sql
-- 查看最近的测试报告
SELECT test_run_id, timestamp, overall_status, tools_tested, tools_successful
FROM test_reports
ORDER BY timestamp DESC
LIMIT 10;

-- 统计测试成功率趋势
SELECT DATE(timestamp) as test_date, 
       AVG(tools_successful::float / tools_tested * 100) as avg_success_rate
FROM test_reports
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY DATE(timestamp)
ORDER BY test_date;
```

## 故障排除

如果数据库存储失败：
1. 检查Supabase URL和Key是否正确配置
2. 确认Supabase项目中的表结构是否正确创建
3. 检查GitHub Actions日志中的详细错误信息
4. 验证Row Level Security (RLS)策略是否正确配置
