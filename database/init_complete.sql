-- =================================================
-- MCP测试框架 - Supabase数据库完整初始化脚本
-- 
-- 说明：在Supabase Dashboard -> SQL Editor 中执行
-- 功能：创建所有表、索引、RLS策略
-- 版本：1.0
-- =================================================

-- 1. 创建MCP工具信息表
CREATE TABLE IF NOT EXISTS mcp_tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    author TEXT,
    github_url TEXT,
    package_name TEXT,
    category TEXT,
    description TEXT,
    version TEXT,
    requires_api_key BOOLEAN DEFAULT FALSE,
    api_requirements JSONB,
    language TEXT,
    license TEXT,
    stars INTEGER,
    last_updated TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 创建测试报告主表
CREATE TABLE IF NOT EXISTS test_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_run_id TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    total_tools INTEGER NOT NULL,
    tools_tested INTEGER NOT NULL,
    tools_successful INTEGER NOT NULL,
    overall_status TEXT NOT NULL,
    execution_time_seconds NUMERIC,
    python_version TEXT,
    platform TEXT,
    test_environment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 创建测试执行详情表
CREATE TABLE IF NOT EXISTS test_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES test_reports(id) ON DELETE CASCADE,
    tool_id UUID REFERENCES mcp_tools(id),
    status TEXT NOT NULL,
    execution_time_seconds NUMERIC,
    memory_usage_mb NUMERIC,
    test_data JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 创建质量指标表
CREATE TABLE IF NOT EXISTS quality_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES test_reports(id) ON DELETE CASCADE,
    success_rate NUMERIC,
    performance_score NUMERIC,
    reliability_score NUMERIC,
    overall_quality_score NUMERIC,
    metrics_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. 创建性能分析表
CREATE TABLE IF NOT EXISTS performance_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES test_reports(id) ON DELETE CASCADE,
    avg_execution_time NUMERIC,
    max_execution_time NUMERIC,
    min_execution_time NUMERIC,
    total_execution_time NUMERIC,
    avg_memory_usage NUMERIC,
    max_memory_usage NUMERIC,
    performance_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. 创建部署信息表
CREATE TABLE IF NOT EXISTS deployment_info (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES test_reports(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    environment TEXT,
    deployment_time TIMESTAMP WITH TIME ZONE,
    deployment_duration_seconds NUMERIC,
    deployment_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. 创建测试元数据表
CREATE TABLE IF NOT EXISTS test_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES test_reports(id) ON DELETE CASCADE,
    test_framework_version TEXT,
    config_hash TEXT,
    git_commit TEXT,
    test_tags JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =================================================
-- 创建索引提升查询性能
-- =================================================
CREATE INDEX IF NOT EXISTS idx_test_reports_timestamp ON test_reports(timestamp);
CREATE INDEX IF NOT EXISTS idx_test_reports_status ON test_reports(overall_status);
CREATE INDEX IF NOT EXISTS idx_test_executions_report_id ON test_executions(report_id);
CREATE INDEX IF NOT EXISTS idx_test_executions_tool_id ON test_executions(tool_id);
CREATE INDEX IF NOT EXISTS idx_test_executions_status ON test_executions(status);
CREATE INDEX IF NOT EXISTS idx_mcp_tools_name ON mcp_tools(name);
CREATE INDEX IF NOT EXISTS idx_mcp_tools_category ON mcp_tools(category);

-- =================================================
-- 启用行级安全(RLS)
-- =================================================
ALTER TABLE mcp_tools ENABLE ROW LEVEL SECURITY;
ALTER TABLE test_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE test_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE quality_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE deployment_info ENABLE ROW LEVEL SECURITY;
ALTER TABLE test_metadata ENABLE ROW LEVEL SECURITY;

-- =================================================
-- 创建RLS策略 - 允许service_role完全访问
-- =================================================
CREATE POLICY "service_role_access" ON mcp_tools FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_access" ON test_reports FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_access" ON test_executions FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_access" ON quality_metrics FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_access" ON performance_analysis FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_access" ON deployment_info FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_access" ON test_metadata FOR ALL USING (auth.role() = 'service_role');

-- =================================================
-- 插入测试数据验证表结构
-- =================================================
INSERT INTO mcp_tools (name, author, description, category, language) 
VALUES ('test-tool', 'system', 'Database initialization test tool', 'testing', 'python')
ON CONFLICT DO NOTHING;

-- =================================================
-- 完成！
-- 执行以下查询验证安装：
-- 
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;
-- SELECT schemaname, tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
-- SELECT * FROM mcp_tools LIMIT 1;
-- =================================================
