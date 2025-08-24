-- LobeHub评分字段迁移脚本
-- 
-- 遵循Linus"好品味"原则：简洁添加，无破坏性更改
-- 
-- 作者: AI Assistant (Linus式设计)
-- 日期: 2025-08-24
-- 版本: 1.1.0

-- 添加LobeHub评分相关列
ALTER TABLE mcp_test_results 
ADD COLUMN IF NOT EXISTS lobehub_url TEXT,               -- LobeHub页面URL
ADD COLUMN IF NOT EXISTS lobehub_evaluate TEXT,          -- LobeHub评分等级 (优质/良好/欠佳)
ADD COLUMN IF NOT EXISTS lobehub_score DECIMAL(4,2),     -- LobeHub具体评分数字
ADD COLUMN IF NOT EXISTS lobehub_star_count INTEGER,      -- GitHub星标数量
ADD COLUMN IF NOT EXISTS lobehub_fork_count INTEGER;      -- GitHub分支数量

-- 添加约束检查 (确保数据完整性)
ALTER TABLE mcp_test_results 
ADD CONSTRAINT check_lobehub_score CHECK (lobehub_score >= 0 AND lobehub_score <= 100),
ADD CONSTRAINT check_star_count CHECK (lobehub_star_count >= 0),
ADD CONSTRAINT check_fork_count CHECK (lobehub_fork_count >= 0);

-- 创建索引 (支持按评分查询)
CREATE INDEX IF NOT EXISTS idx_mcp_lobehub_url ON mcp_test_results (lobehub_url);
CREATE INDEX IF NOT EXISTS idx_mcp_lobehub_evaluate ON mcp_test_results (lobehub_evaluate);
CREATE INDEX IF NOT EXISTS idx_mcp_lobehub_score ON mcp_test_results (lobehub_score);
CREATE INDEX IF NOT EXISTS idx_mcp_star_count ON mcp_test_results (lobehub_star_count);

-- 添加注释说明
COMMENT ON COLUMN mcp_test_results.lobehub_url IS 'LobeHub工具页面URL';
COMMENT ON COLUMN mcp_test_results.lobehub_evaluate IS 'LobeHub评分等级：优质/良好/欠佳/NULL';
COMMENT ON COLUMN mcp_test_results.lobehub_score IS 'LobeHub具体评分数字(0-100)';
COMMENT ON COLUMN mcp_test_results.lobehub_star_count IS 'GitHub仓库星标数量';
COMMENT ON COLUMN mcp_test_results.lobehub_fork_count IS 'GitHub仓库分支数量';

-- 完成日志
DO $$
BEGIN
  RAISE NOTICE '✅ LobeHub评分字段添加完成 - 支持工具质量分析';
END $$;
