-- 评估相关字段迁移脚本
-- 
-- 遵循Linus"好品味"原则：添加评估分析相关字段
-- 
-- 作者: AI Assistant (Linus式设计)
-- 日期: 2025-08-24
-- 版本: 1.2.0

-- 添加评估相关列
ALTER TABLE mcp_test_results 
ADD COLUMN IF NOT EXISTS final_score INTEGER,                    -- 最终综合评分 (0-100)
ADD COLUMN IF NOT EXISTS sustainability_score INTEGER,           -- 可持续性评分 (0-100)  
ADD COLUMN IF NOT EXISTS popularity_score INTEGER,               -- 流行度评分 (0-100)
ADD COLUMN IF NOT EXISTS sustainability_details JSONB,          -- 可持续性详细分析
ADD COLUMN IF NOT EXISTS popularity_details JSONB,              -- 流行度详细分析
ADD COLUMN IF NOT EXISTS evaluation_timestamp TIMESTAMP WITH TIME ZONE; -- 评估时间戳

-- 添加约束检查 (确保分数在合理范围内)
ALTER TABLE mcp_test_results 
ADD CONSTRAINT check_final_score CHECK (final_score >= 0 AND final_score <= 100),
ADD CONSTRAINT check_sustainability_score CHECK (sustainability_score >= 0 AND sustainability_score <= 100),
ADD CONSTRAINT check_popularity_score CHECK (popularity_score >= 0 AND popularity_score <= 100);

-- 创建索引 (支持按评分查询)
CREATE INDEX IF NOT EXISTS idx_mcp_final_score ON mcp_test_results (final_score);
CREATE INDEX IF NOT EXISTS idx_mcp_sustainability_score ON mcp_test_results (sustainability_score);
CREATE INDEX IF NOT EXISTS idx_mcp_popularity_score ON mcp_test_results (popularity_score);
CREATE INDEX IF NOT EXISTS idx_mcp_evaluation_timestamp ON mcp_test_results (evaluation_timestamp);

-- JSONB 索引 (支持详细信息查询)
CREATE INDEX IF NOT EXISTS idx_mcp_sustainability_details ON mcp_test_results USING GIN (sustainability_details);
CREATE INDEX IF NOT EXISTS idx_mcp_popularity_details ON mcp_test_results USING GIN (popularity_details);

-- 添加注释说明
COMMENT ON COLUMN mcp_test_results.final_score IS '最终综合评分(0-100)，基于可持续性和流行度';
COMMENT ON COLUMN mcp_test_results.sustainability_score IS '可持续性评分(0-100)，基于代码质量、维护活跃度等';
COMMENT ON COLUMN mcp_test_results.popularity_score IS '流行度评分(0-100)，基于GitHub星标、下载量等';
COMMENT ON COLUMN mcp_test_results.sustainability_details IS '可持续性详细分析JSON数据';
COMMENT ON COLUMN mcp_test_results.popularity_details IS '流行度详细分析JSON数据';
COMMENT ON COLUMN mcp_test_results.evaluation_timestamp IS '评估执行时间戳';

-- 完成日志
DO $$
BEGIN
  RAISE NOTICE '✅ 评估相关字段添加完成 - 支持综合质量分析';
END $$;
