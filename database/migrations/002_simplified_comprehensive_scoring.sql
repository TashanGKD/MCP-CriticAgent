-- Simplified migration for Supabase SQL Editor
-- 综合评分数据库迁移 - 简化版
-- 执行前请确认已连接到正确的数据库

-- 第1步: 添加基础列
ALTER TABLE mcp_test_results 
ADD COLUMN IF NOT EXISTS comprehensive_score INTEGER DEFAULT NULL;

ALTER TABLE mcp_test_results 
ADD COLUMN IF NOT EXISTS calculation_method VARCHAR(50) DEFAULT NULL;

-- 第2步: 添加评估详情列 (如果需要)
ALTER TABLE mcp_test_results 
ADD COLUMN IF NOT EXISTS evaluation_details JSONB DEFAULT NULL;

-- 第3步: 添加索引优化查询性能
CREATE INDEX IF NOT EXISTS idx_mcp_comprehensive_score 
ON mcp_test_results (comprehensive_score) 
WHERE comprehensive_score IS NOT NULL;

-- 第4步: 添加列注释
COMMENT ON COLUMN mcp_test_results.comprehensive_score IS '综合评分: (测试成功率*1 + GitHub评分*2)/3';
COMMENT ON COLUMN mcp_test_results.calculation_method IS '计算方法: weighted_average 或 success_rate_only';
COMMENT ON COLUMN mcp_test_results.evaluation_details IS '评估详细信息JSON格式';

-- 验证列是否创建成功
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'mcp_test_results' 
AND column_name IN ('comprehensive_score', 'calculation_method', 'evaluation_details')
ORDER BY column_name;
