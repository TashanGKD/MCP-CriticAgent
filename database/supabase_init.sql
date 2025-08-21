-- MCP测试结果数据库 - 简洁版 (Linus重构)
-- 
-- 遵循"好品味"原则：
-- - 一次测试 = 一行记录 
-- - 无需复杂JOIN查询
-- - 核心信息在列中，详细信息在JSONB中
--
-- 作者: AI Assistant (Linus式设计)
-- 日期: 2025-08-21

-- 启用UUID和时间戳扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 简洁的单表设计 - 消除所有特殊情况
CREATE TABLE mcp_test_results (
    -- 主键和时间戳
    test_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 工具标识 (核心信息)
    tool_identifier TEXT NOT NULL,  -- URL或package name
    tool_name TEXT,
    tool_author TEXT, 
    tool_category TEXT,
    
    -- 测试状态 (布尔值，无条件分支)
    test_success BOOLEAN NOT NULL,
    deployment_success BOOLEAN NOT NULL,
    communication_success BOOLEAN NOT NULL,
    
    -- 性能指标 (核心数据)
    available_tools_count INTEGER DEFAULT 0,
    test_duration_seconds FLOAT NOT NULL,
    
    -- 错误信息
    error_messages TEXT[],
    
    -- 详细信息 (JSONB - 灵活存储)
    test_details JSONB DEFAULT '{}',    -- 详细测试结果
    environment_info JSONB DEFAULT '{}', -- 环境信息
    
    -- 审计信息
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 约束检查 (简单验证)
    CHECK (test_duration_seconds >= 0.0),
    CHECK (available_tools_count >= 0)
);

-- 简洁的索引设计 (只建必要的)
CREATE INDEX idx_mcp_test_timestamp ON mcp_test_results (test_timestamp);
CREATE INDEX idx_mcp_test_tool ON mcp_test_results (tool_identifier);
CREATE INDEX idx_mcp_test_success ON mcp_test_results (test_success);

-- JSONB 索引 (支持详细信息查询)
CREATE INDEX idx_mcp_test_details ON mcp_test_results USING GIN (test_details);
CREATE INDEX idx_mcp_environment ON mcp_test_results USING GIN (environment_info);

-- 自动更新时间戳函数
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.created_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 注释说明
COMMENT ON TABLE mcp_test_results IS 'MCP工具测试结果 - 单表设计，一次测试一行记录';
COMMENT ON COLUMN mcp_test_results.tool_identifier IS '工具标识：URL或package name';
COMMENT ON COLUMN mcp_test_results.test_details IS '详细测试结果：测试用例、性能指标等';
COMMENT ON COLUMN mcp_test_results.environment_info IS '环境信息：平台、版本、进程ID等';
