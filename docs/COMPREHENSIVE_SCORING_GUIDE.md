# MCP工具综合评分系统使用指南

## 概述

综合评分系统将**测试成功率**和**GitHub仓库评估**按**1:2**权重进行综合评价，为MCP工具提供客观的质量评估。

```
综合评分 = (测试成功率 × 1 + GitHub评估分数 × 2) ÷ 3
```

## 数据库配置

### 1. 执行数据库迁移

在Supabase SQL编辑器中执行以下文件：

```sql
-- 文件: database/migrations/002_simplified_comprehensive_scoring.sql
```

### 2. 验证表结构

确认`mcp_test_results`表包含以下新列：
- `comprehensive_score` (INTEGER) - 综合评分 (0-100)
- `calculation_method` (VARCHAR) - 计算方法
- `evaluation_details` (JSONB) - 详细评估信息

## 使用方法

### 1. 测试单个工具（自动计算综合评分）

```bash
uv run python src/main.py test-url https://github.com/upstash/context7 --evaluate
```

### 2. 查看综合评分报告

```bash
uv run python show_comprehensive_scores.py
```

### 3. 导出综合评分数据

```bash
uv run python export_comprehensive_scores.py
```

## 评分标准

| 分数范围 | 质量等级 | 说明 |
|---------|---------|------|
| 80-100  | 优秀    | 高质量，推荐使用 |
| 60-79   | 良好    | 质量较好，可以使用 |
| 0-59    | 需改进  | 存在问题，需要改进 |

## 计算逻辑

### GitHub评估分数 (权重: 2)
- **可持续性** (84%)：代码更新频率、Issue响应速度等
- **受欢迎程度** (16%)：Stars、Forks等社区指标

### 测试成功率 (权重: 1)
- **部署成功**: 工具能否正常启动
- **通信成功**: MCP协议通信是否正常
- **功能测试**: AI智能测试的通过率

### 计算方法
- `weighted_average`: 同时有测试数据和GitHub评估
- `success_rate_only`: 仅有测试数据
- `evaluator_only`: 仅有GitHub评估

## 示例结果

```
Context7 MCP工具评估结果:
├─ 测试成功率: 75.0% (3/4 测试通过)
├─ GitHub评估: 89分
│  ├─ 可持续性: 84分 (活跃开发)
│  └─ 受欢迎程度: 94分 (27K stars)
└─ 综合评分: 84分 (优秀)
   计算: (75×1 + 89×2) ÷ 3 = 84
```

## 数据表结构

最新的`mcp_test_results`表包含：

```sql
-- 基础测试字段
test_success BOOLEAN
deployment_success BOOLEAN  
communication_success BOOLEAN

-- GitHub评估字段
final_score INTEGER           -- GitHub总评分
sustainability_score INTEGER  -- 可持续性评分
popularity_score INTEGER      -- 受欢迎程度评分

-- 综合评分字段 (新增)
comprehensive_score INTEGER   -- 综合评分
calculation_method VARCHAR    -- 计算方法
evaluation_details JSONB      -- 详细信息
```

## API接口

### 计算综合评分

```python
from src.core.evaluator import calculate_comprehensive_score_from_tests

result = calculate_comprehensive_score_from_tests(
    github_url="https://github.com/upstash/context7"
)

print(f"综合评分: {result['comprehensive_score']}")
print(f"计算说明: {result['message']}")
```

## 注意事项

1. **数据库迁移**: 首次使用需要在Supabase执行迁移脚本
2. **环境变量**: 确保设置了`SUPABASE_URL`和`SUPABASE_SERVICE_ROLE_KEY`
3. **权限要求**: 需要数据库写入权限
4. **兼容性**: 系统在数据库列不存在时仍能正常运行，只是无法存储综合评分

## 故障排除

**Q: 提示"column does not exist"错误?**
A: 请先在Supabase执行数据库迁移脚本。

**Q: 综合评分计算失败?**
A: 检查GitHub URL是否正确，确保数据库中有对应的测试记录。

**Q: 测试成功率为0%?**
A: 可能是工具部署失败或测试用例不适合，检查错误日志。
