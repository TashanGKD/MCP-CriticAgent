-- Add comprehensive scoring columns to mcp_test_results
-- 
-- 遵循Linus的"好品味"原则：
-- - 统一数据结构，一个表存储所有评分信息
-- - 消除分表查询的特殊情况
--
-- 作者: AI Assistant (Linus式设计)
-- 日期: 2025-08-24

-- 在 mcp_test_results 表中添加GitHub仓库评估相关字段
ALTER TABLE mcp_test_results 
ADD COLUMN IF NOT EXISTS github_evaluation_score INTEGER DEFAULT NULL;

ALTER TABLE mcp_test_results 
ADD COLUMN IF NOT EXISTS sustainability_score INTEGER DEFAULT NULL;

ALTER TABLE mcp_test_results 
ADD COLUMN IF NOT EXISTS popularity_score INTEGER DEFAULT NULL;

-- 添加综合评分字段 (测试成功率1 + GitHub评分2 的加权平均)
ALTER TABLE mcp_test_results 
ADD COLUMN IF NOT EXISTS comprehensive_score INTEGER DEFAULT NULL;

-- 添加计算方法字段
ALTER TABLE mcp_test_results 
ADD COLUMN IF NOT EXISTS calculation_method VARCHAR(50) DEFAULT NULL;

-- 添加评估详细信息 (JSONB格式)
ALTER TABLE mcp_test_results 
ADD COLUMN IF NOT EXISTS evaluation_details JSONB DEFAULT NULL;

-- 添加计算时间戳
ALTER TABLE mcp_test_results 
ADD COLUMN IF NOT EXISTS evaluation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NULL;

-- 添加约束检查 (使用DO块处理IF NOT EXISTS逻辑)
DO $$ 
BEGIN
    -- 添加GitHub评估分数约束
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'check_github_evaluation_score' 
        AND table_name = 'mcp_test_results'
    ) THEN
        ALTER TABLE mcp_test_results 
        ADD CONSTRAINT check_github_evaluation_score 
        CHECK (github_evaluation_score IS NULL OR (github_evaluation_score >= 0 AND github_evaluation_score <= 100));
    END IF;
    
    -- 添加综合评分约束
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'check_comprehensive_score' 
        AND table_name = 'mcp_test_results'
    ) THEN
        ALTER TABLE mcp_test_results 
        ADD CONSTRAINT check_comprehensive_score 
        CHECK (comprehensive_score IS NULL OR (comprehensive_score >= 0 AND comprehensive_score <= 100));
    END IF;
END $$;

-- 创建索引以支持评分查询
CREATE INDEX IF NOT EXISTS idx_mcp_test_github_score ON mcp_test_results (github_evaluation_score) WHERE github_evaluation_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_mcp_test_comprehensive_score ON mcp_test_results (comprehensive_score) WHERE comprehensive_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_mcp_test_tool_github ON mcp_test_results (tool_identifier) WHERE github_evaluation_score IS NOT NULL;

-- JSONB索引支持评估详情查询
CREATE INDEX IF NOT EXISTS idx_mcp_evaluation_details ON mcp_test_results USING GIN (evaluation_details) WHERE evaluation_details IS NOT NULL;

-- 注释说明
COMMENT ON COLUMN mcp_test_results.github_evaluation_score IS 'GitHub仓库评估分数 (0-100)，基于可持续性和受欢迎程度';
COMMENT ON COLUMN mcp_test_results.sustainability_score IS '仓库可持续性评分 (0-100)';
COMMENT ON COLUMN mcp_test_results.popularity_score IS '仓库受欢迎程度评分 (0-100)';
-- 注释说明
COMMENT ON COLUMN mcp_test_results.github_evaluation_score IS 'GitHub仓库评估分数 (0-100)，基于可持续性和受欢迎程度';
COMMENT ON COLUMN mcp_test_results.sustainability_score IS '仓库可持续性评分 (0-100)';
COMMENT ON COLUMN mcp_test_results.popularity_score IS '仓库受欢迎度评分 (0-100)';
COMMENT ON COLUMN mcp_test_results.comprehensive_score IS '综合评分: (测试成功率*1 + GitHub评分*2)/3';
COMMENT ON COLUMN mcp_test_results.calculation_method IS '综合评分计算方法: weighted_average 或 success_rate_only';
COMMENT ON COLUMN mcp_test_results.evaluation_details IS '评估详细信息，包含各项指标的详细分析';
COMMENT ON COLUMN mcp_test_results.evaluation_timestamp IS '评估计算的时间戳';
