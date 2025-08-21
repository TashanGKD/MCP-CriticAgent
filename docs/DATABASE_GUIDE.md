# MCP Agent 数据库完整使用手册

## 📋 概述

MCP Agent 使用 Supabase PostgreSQL 数据库存储所有 MCP 工具的测试结果。本文档详细说明数据库结构、字段含义、查询方法和集成方式，供其他程序调用使用。

**数据库设计哲学**: 遵循 Linus 的"好品味"原则 - 单表设计，消除所有特殊情况，一次测试一行记录。

---

## 🗄️ 数据库连接配置

### 基本信息
```bash
数据库类型: PostgreSQL (Supabase托管)
数据库URL: https://vmikqjfxbdvfpakvwoab.supabase.co
表名: mcp_test_results
```

### 连接方式

#### Python (推荐)
```python
from supabase import create_client

# 连接配置
SUPABASE_URL = "https://your-project.supabase.co"  # 替换为实际项目URL
SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key"  # 完整权限

# 创建客户端
client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
```

#### 其他语言
```javascript
// JavaScript
import { createClient } from '@supabase/supabase-js'
const client = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
```

```sql
-- 直接SQL连接
-- 使用PostgreSQL标准连接字符串
postgresql://postgres:[密码]@db.vmikqjfxbdvfpakvwoab.supabase.co:5432/postgres
```

---

## 📊 数据表结构详解

### `mcp_test_results` 表完整字段说明

| 字段名 | 数据类型 | 约束 | 说明 | 示例值 |
|--------|----------|------|------|--------|
| **主键和时间戳** |
| `test_id` | UUID | PRIMARY KEY | 测试记录唯一标识符，自动生成 | `550e8400-e29b-41d4-a716-446655440000` |
| `test_timestamp` | TIMESTAMPTZ | NOT NULL | 测试执行时间戳（带时区） | `2025-08-21T19:24:37.123456+00:00` |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | 记录创建时间 | `2025-08-21T19:24:37.123456+00:00` |
| **工具标识信息** |
| `tool_identifier` | TEXT | NOT NULL | 工具标识符（URL或包名） | `https://github.com/upstash/context7` |
| `tool_name` | TEXT | | 工具显示名称 | `Context7 MCP - 最新代码文档适用于任何提示` |
| `tool_author` | TEXT | | 工具作者/组织 | `upstash` |
| `tool_category` | TEXT | | 工具分类 | `开发工具, 推荐` |
| **测试状态（布尔值）** |
| `test_success` | BOOLEAN | NOT NULL | 整体测试是否成功 | `true` |
| `deployment_success` | BOOLEAN | NOT NULL | 工具部署是否成功 | `true` |
| `communication_success` | BOOLEAN | NOT NULL | MCP协议通信是否成功 | `true` |
| **性能指标** |
| `available_tools_count` | INTEGER | DEFAULT 0 | 可用工具数量 | `2` |
| `test_duration_seconds` | FLOAT | NOT NULL | 测试总耗时（秒） | `1.234` |
| **错误信息** |
| `error_messages` | TEXT[] | | 错误消息数组 | `["工具调用失败: Invalid arguments"]` |
| **详细信息（JSONB）** |
| `test_details` | JSONB | DEFAULT '{}' | 详细测试结果和配置信息 | 见下方详细说明 |
| `environment_info` | JSONB | DEFAULT '{}' | 环境信息（系统、版本等） | 见下方详细说明 |

### JSONB 字段详细结构

#### `test_details` 字段内容
```json
{
  "test_results": [
    {
      "test_name": "MCP协议通信测试",
      "success": true,
      "duration": 0.123,
      "error_message": null
    },
    {
      "test_name": "工具调用测试: resolve-library-id",
      "success": true, 
      "duration": 0.456,
      "error_message": null
    }
  ],
  "total_tests": 2,
  "passed_tests": 2,
  "test_config": {
    "timeout": 600,
    "verbose": false,
    "smart_test": false,
    "cleanup": true
  }
}
```

#### `environment_info` 字段内容
```json
{
  "platform": "Linux",
  "python_version": "3.12.11",
  "node_version": "24.3.0",
  "process_pid": 3338700,
  "test_framework_version": "2.0.0",
  "deployment_method": "npx",
  "mcp_protocol_version": "2024-11-05"
}
```

---

## 🔍 常用查询示例

### 基本查询

#### 1. 获取最新测试结果
```python
# 获取最近10条测试记录
recent_tests = client.table('mcp_test_results')\
    .select('*')\
    .order('test_timestamp', desc=True)\
    .limit(10)\
    .execute()

for test in recent_tests.data:
    print(f"{test['test_timestamp']}: {test['tool_name']} - {'✅' if test['test_success'] else '❌'}")
```

#### 2. 按工具查询
```python
# 查询特定工具的测试历史
tool_history = client.table('mcp_test_results')\
    .select('*')\
    .eq('tool_identifier', 'https://github.com/upstash/context7')\
    .order('test_timestamp', desc=True)\
    .execute()
```

#### 3. 成功率统计
```python
# 计算整体成功率
all_tests = client.table('mcp_test_results').select('test_success').execute()
total = len(all_tests.data)
success_count = sum(1 for test in all_tests.data if test['test_success'])
success_rate = (success_count / total * 100) if total > 0 else 0
print(f"成功率: {success_count}/{total} ({success_rate:.1f}%)")
```

### 高级查询

#### 4. 按时间范围查询
```python
from datetime import datetime, timedelta

# 查询最近24小时的测试
yesterday = datetime.now() - timedelta(days=1)
recent_tests = client.table('mcp_test_results')\
    .select('*')\
    .gte('test_timestamp', yesterday.isoformat())\
    .execute()
```

#### 5. 按作者统计
```python
# 统计各作者的工具测试情况
author_stats = client.table('mcp_test_results')\
    .select('tool_author, test_success')\
    .execute()

# 处理统计结果
author_summary = {}
for test in author_stats.data:
    author = test['tool_author'] or 'Unknown'
    if author not in author_summary:
        author_summary[author] = {'total': 0, 'success': 0}
    author_summary[author]['total'] += 1
    if test['test_success']:
        author_summary[author]['success'] += 1

# 打印结果
for author, stats in author_summary.items():
    rate = stats['success'] / stats['total'] * 100
    print(f"{author}: {stats['success']}/{stats['total']} ({rate:.1f}%)")
```

#### 6. JSONB 查询示例
```python
# 查询包含特定测试结果的记录
failed_tool_calls = client.table('mcp_test_results')\
    .select('tool_name, test_details')\
    .contains('test_details', {'test_results': [{'test_name': '工具调用测试'}]})\
    .execute()

# 查询特定环境的测试
linux_tests = client.table('mcp_test_results')\
    .select('*')\
    .contains('environment_info', {'platform': 'Linux'})\
    .execute()
```

### 性能分析查询

#### 7. 性能统计
```python
# 查询平均测试时间
performance = client.table('mcp_test_results')\
    .select('tool_name, test_duration_seconds')\
    .order('test_duration_seconds', desc=True)\
    .limit(20)\
    .execute()

print("最耗时的工具:")
for test in performance.data:
    print(f"{test['tool_name']}: {test['test_duration_seconds']:.2f}秒")
```

#### 8. 工具可用性统计
```python
# 统计工具数量分布
tool_counts = client.table('mcp_test_results')\
    .select('tool_name, available_tools_count')\
    .execute()

# 按工具数量分组
count_distribution = {}
for test in tool_counts.data:
    count = test['available_tools_count']
    if count not in count_distribution:
        count_distribution[count] = 0
    count_distribution[count] += 1

print("工具数量分布:")
for count, frequency in sorted(count_distribution.items()):
    print(f"{count}个工具: {frequency}次测试")
```

---

## 📈 数据分析和报表

### 趋势分析
```python
# 按日统计测试数量和成功率
from collections import defaultdict
import json

daily_stats = defaultdict(lambda: {'total': 0, 'success': 0})

all_tests = client.table('mcp_test_results')\
    .select('test_timestamp, test_success')\
    .order('test_timestamp', desc=True)\
    .execute()

for test in all_tests.data:
    date = test['test_timestamp'][:10]  # 提取日期部分
    daily_stats[date]['total'] += 1
    if test['test_success']:
        daily_stats[date]['success'] += 1

# 输出每日统计
print("每日测试统计:")
for date, stats in sorted(daily_stats.items(), reverse=True):
    rate = stats['success'] / stats['total'] * 100
    print(f"{date}: {stats['success']}/{stats['total']} ({rate:.1f}%)")
```

### 故障分析
```python
# 查询失败的测试及原因
failed_tests = client.table('mcp_test_results')\
    .select('tool_name, tool_identifier, error_messages, test_details')\
    .eq('test_success', False)\
    .order('test_timestamp', desc=True)\
    .execute()

print("失败测试分析:")
for test in failed_tests.data:
    print(f"工具: {test['tool_name']}")
    print(f"URL: {test['tool_identifier']}")
    if test['error_messages']:
        print(f"错误: {test['error_messages']}")
    print("---")
```

---

## 🔧 集成开发指南

### REST API 访问
```python
import requests

# 使用Supabase REST API
url = "https://vmikqjfxbdvfpakvwoab.supabase.co/rest/v1/mcp_test_results"
headers = {
    'apikey': 'your-service-role-key',
    'Authorization': 'Bearer your-service-role-key',
    'Content-Type': 'application/json'
}

# GET请求示例
response = requests.get(f"{url}?limit=10&order=test_timestamp.desc", headers=headers)
data = response.json()
```

### 批量数据导出
```python
def export_all_test_data():
    """导出所有测试数据为JSON文件"""
    all_data = client.table('mcp_test_results').select('*').execute()
    
    with open('mcp_test_export.json', 'w', encoding='utf-8') as f:
        json.dump(all_data.data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"已导出 {len(all_data.data)} 条记录")
    return all_data.data

# 使用示例
exported_data = export_all_test_data()
```

### 实时监控
```python
def monitor_new_tests():
    """监控新的测试结果"""
    last_check = datetime.now()
    
    while True:
        new_tests = client.table('mcp_test_results')\
            .select('*')\
            .gte('test_timestamp', last_check.isoformat())\
            .order('test_timestamp', desc=True)\
            .execute()
        
        for test in new_tests.data:
            status = "✅ 成功" if test['test_success'] else "❌ 失败"
            print(f"新测试: {test['tool_name']} - {status}")
        
        last_check = datetime.now()
        time.sleep(60)  # 每分钟检查一次
```

---

## 📋 数据完整性和维护

### 数据验证
```python
def validate_data_integrity():
    """验证数据完整性"""
    # 检查必填字段
    incomplete = client.table('mcp_test_results')\
        .select('test_id, tool_identifier, test_success')\
        .is_('tool_identifier', 'null')\
        .execute()
    
    if incomplete.data:
        print(f"发现 {len(incomplete.data)} 条不完整记录")
    
    # 检查时间戳一致性
    time_issues = client.table('mcp_test_results')\
        .select('test_id, test_timestamp, created_at')\
        .execute()
    
    for record in time_issues.data:
        test_time = datetime.fromisoformat(record['test_timestamp'].replace('Z', '+00:00'))
        created_time = datetime.fromisoformat(record['created_at'].replace('Z', '+00:00'))
        diff = abs((test_time - created_time).total_seconds())
        if diff > 60:  # 超过1分钟差异
            print(f"时间戳异常: {record['test_id']} - 差异 {diff}秒")
```

### 定期清理
```python
def cleanup_old_data(days_to_keep=90):
    """清理旧数据（保留最近90天）"""
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    old_records = client.table('mcp_test_results')\
        .delete()\
        .lt('test_timestamp', cutoff_date.isoformat())\
        .execute()
    
    print(f"已清理 {len(old_records.data)} 条旧记录")
```

---

## 🚀 最佳实践

### 查询优化
1. **使用索引**: 主要查询字段已建立索引，包括 `test_timestamp`、`tool_identifier`、`test_success`
2. **分页查询**: 大量数据查询时使用 `limit()` 和 `offset()`
3. **选择性查询**: 使用 `select()` 只获取需要的字段
4. **JSONB查询**: 合理使用 `contains()`、`@>`等操作符

### 错误处理
```python
def safe_query(query_func, *args, **kwargs):
    """安全的查询包装器"""
    try:
        result = query_func(*args, **kwargs)
        return result
    except Exception as e:
        print(f"查询失败: {e}")
        return None

# 使用示例
result = safe_query(
    lambda: client.table('mcp_test_results').select('*').limit(10).execute()
)
```

### 性能监控
```python
import time

def timed_query(query_func, *args, **kwargs):
    """计时查询"""
    start_time = time.time()
    result = query_func(*args, **kwargs)
    duration = time.time() - start_time
    print(f"查询耗时: {duration:.3f}秒")
    return result
```

---

## 📞 技术支持

### 联系方式
- **项目仓库**: https://github.com/gqy20/mcp_agent
- **文档版本**: v1.0.0
- **最后更新**: 2025-08-21

### 常见问题
1. **连接超时**: 检查网络连接和API密钥
2. **权限问题**: 确保使用service_role_key而非anon_key
3. **JSONB查询**: 参考PostgreSQL JSONB操作符文档
4. **性能优化**: 合理使用索引和分页

---

**注意**: 此文档基于 MCP Agent v2.0.0 (Linus重构版)，遵循"好品味"设计原则，提供简洁而完整的数据访问方案。
