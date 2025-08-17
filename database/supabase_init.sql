-- MCP测试结果数据库初始化脚本
-- 适用于Supabase PostgreSQL

-- 启用UUID扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 启用PostgreSQL的时间戳自动更新函数
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 1. MCP工具信息表
CREATE TABLE mcp_tools (
    tool_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    author VARCHAR(100) NOT NULL,
    github_url TEXT,
    package_name VARCHAR(200),
    category VARCHAR(100) DEFAULT 'Unknown',
    description TEXT,
    version VARCHAR(50),
    requires_api_key BOOLEAN DEFAULT false,
    api_requirements TEXT[],
    language VARCHAR(50) DEFAULT 'Unknown',
    license VARCHAR(50),
    stars INTEGER,
    last_updated TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 索引和约束
    UNIQUE(github_url),
    UNIQUE(package_name)
);

-- 2. 测试报告主表
CREATE TABLE test_reports (
    report_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id UUID NOT NULL,
    test_environment VARCHAR(50) DEFAULT 'local',
    trigger_source VARCHAR(50) DEFAULT 'manual',
    operator VARCHAR(100),
    overall_status VARCHAR(20) DEFAULT 'pending',
    total_duration_seconds FLOAT DEFAULT 0.0,
    quality_score FLOAT DEFAULT 0.0,
    metadata_json JSONB DEFAULT '{}',
    environment_json JSONB DEFAULT '{}',
    
    -- 外键
    tool_id UUID REFERENCES mcp_tools(tool_id) ON DELETE SET NULL,
    
    -- 检查约束
    CHECK (overall_status IN ('pending', 'running', 'success', 'failed', 'timeout', 'error')),
    CHECK (quality_score >= 0.0 AND quality_score <= 100.0),
    CHECK (total_duration_seconds >= 0.0)
);

-- 3. 部署记录表
CREATE TABLE deployments (
    deployment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES test_reports(report_id) ON DELETE CASCADE,
    tool_id UUID REFERENCES mcp_tools(tool_id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'pending',
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds FLOAT DEFAULT 0.0,
    package_manager VARCHAR(20) DEFAULT 'npm',
    deployment_method VARCHAR(50) DEFAULT 'local',
    process_id INTEGER,
    server_id VARCHAR(100),
    port INTEGER,
    error_details TEXT,
    resource_usage_json JSONB DEFAULT '{}',
    
    -- 检查约束
    CHECK (status IN ('pending', 'deploying', 'success', 'failed', 'timeout')),
    CHECK (duration_seconds >= 0.0),
    CHECK (port IS NULL OR (port > 0 AND port <= 65535))
);

-- 4. 测试执行表
CREATE TABLE test_executions (
    execution_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES test_reports(report_id) ON DELETE CASCADE,
    test_id VARCHAR(50) NOT NULL,
    test_name VARCHAR(200) NOT NULL,
    test_type VARCHAR(50) DEFAULT 'basic',
    status VARCHAR(20) DEFAULT 'pending',
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds FLOAT DEFAULT 0.0,
    input_data_json JSONB DEFAULT '{}',
    output_data_json JSONB DEFAULT '{}',
    error_message TEXT,
    assertion_results_json JSONB DEFAULT '[]',
    performance_metrics_json JSONB DEFAULT '{}',
    
    -- 检查约束
    CHECK (status IN ('pending', 'running', 'success', 'failed', 'timeout', 'error')),
    CHECK (test_type IN ('basic', 'communication', 'functionality', 'performance', 'integration', 'stress')),
    CHECK (duration_seconds >= 0.0)
);

-- 5. 可用工具表
CREATE TABLE available_tools (
    available_tool_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES test_reports(report_id) ON DELETE CASCADE,
    tool_name VARCHAR(200) NOT NULL,
    description TEXT,
    input_schema_json JSONB DEFAULT '{}',
    output_schema_json JSONB DEFAULT '{}',
    category VARCHAR(100) DEFAULT 'general',
    required_permissions TEXT[]
);

-- 6. 质量指标表
CREATE TABLE quality_metrics (
    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES test_reports(report_id) ON DELETE CASCADE,
    overall_score FLOAT DEFAULT 0.0,
    deployment_reliability FLOAT DEFAULT 0.0,
    communication_stability FLOAT DEFAULT 0.0,
    functionality_coverage FLOAT DEFAULT 0.0,
    performance_rating FLOAT DEFAULT 0.0,
    documentation_quality FLOAT DEFAULT 0.0,
    api_design_quality FLOAT DEFAULT 0.0,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 检查约束
    CHECK (overall_score >= 0.0 AND overall_score <= 100.0),
    CHECK (deployment_reliability >= 0.0 AND deployment_reliability <= 100.0),
    CHECK (communication_stability >= 0.0 AND communication_stability <= 100.0),
    CHECK (functionality_coverage >= 0.0 AND functionality_coverage <= 100.0),
    CHECK (performance_rating >= 0.0 AND performance_rating <= 100.0),
    CHECK (documentation_quality >= 0.0 AND documentation_quality <= 100.0),
    CHECK (api_design_quality >= 0.0 AND api_design_quality <= 100.0)
);

-- 7. 性能分析表
CREATE TABLE performance_metrics (
    performance_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES test_reports(report_id) ON DELETE CASCADE,
    deployment_time_seconds FLOAT DEFAULT 0.0,
    startup_time_seconds FLOAT DEFAULT 0.0,
    memory_usage_mb FLOAT DEFAULT 0.0,
    cpu_usage_percent FLOAT DEFAULT 0.0,
    response_time_avg_ms FLOAT DEFAULT 0.0,
    response_time_p95_ms FLOAT DEFAULT 0.0,
    throughput_ops_per_second FLOAT DEFAULT 0.0,
    stability_score FLOAT DEFAULT 0.0,
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 检查约束
    CHECK (deployment_time_seconds >= 0.0),
    CHECK (startup_time_seconds >= 0.0),
    CHECK (memory_usage_mb >= 0.0),
    CHECK (cpu_usage_percent >= 0.0 AND cpu_usage_percent <= 100.0),
    CHECK (response_time_avg_ms >= 0.0),
    CHECK (response_time_p95_ms >= 0.0),
    CHECK (throughput_ops_per_second >= 0.0),
    CHECK (stability_score >= 0.0 AND stability_score <= 100.0)
);

-- 创建索引以优化查询性能
CREATE INDEX idx_test_reports_created_at ON test_reports(created_at DESC);
CREATE INDEX idx_test_reports_tool_id ON test_reports(tool_id);
CREATE INDEX idx_test_reports_status ON test_reports(overall_status);
CREATE INDEX idx_test_reports_session_id ON test_reports(session_id);
CREATE INDEX idx_test_reports_trigger_source ON test_reports(trigger_source);

CREATE INDEX idx_deployments_report_id ON deployments(report_id);
CREATE INDEX idx_deployments_status ON deployments(status);
CREATE INDEX idx_deployments_start_time ON deployments(start_time DESC);

CREATE INDEX idx_test_executions_report_id ON test_executions(report_id);
CREATE INDEX idx_test_executions_status ON test_executions(status);
CREATE INDEX idx_test_executions_test_type ON test_executions(test_type);

CREATE INDEX idx_available_tools_report_id ON available_tools(report_id);
CREATE INDEX idx_available_tools_category ON available_tools(category);

CREATE INDEX idx_quality_metrics_report_id ON quality_metrics(report_id);
CREATE INDEX idx_quality_metrics_overall_score ON quality_metrics(overall_score DESC);

CREATE INDEX idx_performance_metrics_report_id ON performance_metrics(report_id);
CREATE INDEX idx_performance_metrics_measured_at ON performance_metrics(measured_at DESC);

CREATE INDEX idx_mcp_tools_category ON mcp_tools(category);
CREATE INDEX idx_mcp_tools_author ON mcp_tools(author);
CREATE INDEX idx_mcp_tools_language ON mcp_tools(language);
CREATE INDEX idx_mcp_tools_stars ON mcp_tools(stars DESC);

-- 创建更新时间戳触发器
CREATE TRIGGER update_mcp_tools_updated_at
    BEFORE UPDATE ON mcp_tools
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_test_reports_updated_at
    BEFORE UPDATE ON test_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- 创建有用的视图
-- 1. 测试报告概览视图
CREATE VIEW test_reports_overview AS
SELECT 
    tr.report_id,
    tr.created_at,
    tr.session_id,
    tr.overall_status,
    tr.total_duration_seconds,
    tr.quality_score,
    mt.name as tool_name,
    mt.author as tool_author,
    mt.category as tool_category,
    mt.package_name,
    d.status as deployment_status,
    d.duration_seconds as deployment_duration,
    qm.overall_score as quality_overall_score,
    (SELECT COUNT(*) FROM test_executions te WHERE te.report_id = tr.report_id) as total_tests,
    (SELECT COUNT(*) FROM test_executions te WHERE te.report_id = tr.report_id AND te.status = 'success') as passed_tests,
    (SELECT COUNT(*) FROM available_tools at WHERE at.report_id = tr.report_id) as available_tools_count
FROM test_reports tr
LEFT JOIN mcp_tools mt ON tr.tool_id = mt.tool_id
LEFT JOIN deployments d ON tr.report_id = d.report_id
LEFT JOIN quality_metrics qm ON tr.report_id = qm.report_id;

-- 2. 工具统计视图
CREATE VIEW mcp_tools_stats AS
SELECT 
    mt.tool_id,
    mt.name,
    mt.author,
    mt.category,
    mt.package_name,
    mt.language,
    mt.stars,
    COUNT(tr.report_id) as total_tests,
    COUNT(CASE WHEN tr.overall_status = 'success' THEN 1 END) as successful_tests,
    ROUND(AVG(tr.quality_score), 2) as avg_quality_score,
    ROUND(AVG(tr.total_duration_seconds), 2) as avg_test_duration,
    MAX(tr.created_at) as last_tested
FROM mcp_tools mt
LEFT JOIN test_reports tr ON mt.tool_id = tr.tool_id
GROUP BY mt.tool_id, mt.name, mt.author, mt.category, mt.package_name, mt.language, mt.stars;

-- 3. 性能趋势视图
CREATE VIEW performance_trends AS
SELECT 
    DATE_TRUNC('day', tr.created_at) as test_date,
    mt.category as tool_category,
    COUNT(tr.report_id) as tests_count,
    ROUND(AVG(pm.deployment_time_seconds), 2) as avg_deployment_time,
    ROUND(AVG(pm.response_time_avg_ms), 2) as avg_response_time,
    ROUND(AVG(pm.memory_usage_mb), 2) as avg_memory_usage,
    ROUND(AVG(tr.quality_score), 2) as avg_quality_score
FROM test_reports tr
LEFT JOIN mcp_tools mt ON tr.tool_id = mt.tool_id
LEFT JOIN performance_metrics pm ON tr.report_id = pm.report_id
WHERE tr.created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', tr.created_at), mt.category
ORDER BY test_date DESC;

-- 启用行级安全性 (RLS)
ALTER TABLE mcp_tools ENABLE ROW LEVEL SECURITY;
ALTER TABLE test_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE deployments ENABLE ROW LEVEL SECURITY;
ALTER TABLE test_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE available_tools ENABLE ROW LEVEL SECURITY;
ALTER TABLE quality_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_metrics ENABLE ROW LEVEL SECURITY;

-- 创建基础的RLS策略（允许所有认证用户读取）
CREATE POLICY "Allow authenticated read access" ON mcp_tools FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated read access" ON test_reports FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated read access" ON deployments FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated read access" ON test_executions FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated read access" ON available_tools FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated read access" ON quality_metrics FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated read access" ON performance_metrics FOR SELECT TO authenticated USING (true);

-- 创建插入权限策略（允许service role写入）
CREATE POLICY "Allow service role write access" ON mcp_tools FOR ALL TO service_role USING (true);
CREATE POLICY "Allow service role write access" ON test_reports FOR ALL TO service_role USING (true);
CREATE POLICY "Allow service role write access" ON deployments FOR ALL TO service_role USING (true);
CREATE POLICY "Allow service role write access" ON test_executions FOR ALL TO service_role USING (true);
CREATE POLICY "Allow service role write access" ON available_tools FOR ALL TO service_role USING (true);
CREATE POLICY "Allow service role write access" ON quality_metrics FOR ALL TO service_role USING (true);
CREATE POLICY "Allow service role write access" ON performance_metrics FOR ALL TO service_role USING (true);

-- 创建一些有用的函数
-- 1. 计算测试成功率
CREATE OR REPLACE FUNCTION calculate_test_success_rate(report_uuid UUID)
RETURNS FLOAT AS $$
DECLARE
    total_tests INTEGER;
    passed_tests INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_tests 
    FROM test_executions 
    WHERE report_id = report_uuid;
    
    SELECT COUNT(*) INTO passed_tests 
    FROM test_executions 
    WHERE report_id = report_uuid AND status = 'success';
    
    IF total_tests = 0 THEN
        RETURN 0.0;
    END IF;
    
    RETURN (passed_tests::FLOAT / total_tests::FLOAT) * 100.0;
END;
$$ LANGUAGE plpgsql;

-- 2. 获取工具的最新测试状态
CREATE OR REPLACE FUNCTION get_tool_latest_status(tool_uuid UUID)
RETURNS TABLE(
    latest_test_date TIMESTAMP WITH TIME ZONE,
    latest_status VARCHAR(20),
    latest_quality_score FLOAT,
    total_tests_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        tr.created_at,
        tr.overall_status,
        tr.quality_score,
        COUNT(*) OVER()
    FROM test_reports tr
    WHERE tr.tool_id = tool_uuid
    ORDER BY tr.created_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- 插入初始示例数据（可选）
INSERT INTO mcp_tools (name, author, github_url, package_name, category, description, language, requires_api_key) VALUES
('Context7 MCP', 'upstash', 'https://github.com/upstash/context7', '@upstash/context7-mcp', '开发工具', '用于Context7的MCP服务器，提供最新、版本特定的库文档和代码示例', 'Node.js', false),
('GitHub MCP', 'modelcontextprotocol', 'https://github.com/modelcontextprotocol/servers', 'github-mcp-server', '开发工具', 'GitHub集成的MCP服务器', 'Python', true);

-- 创建数据保留策略（可选，保留最近90天的数据）
-- 这个可以根据需要调整
CREATE OR REPLACE FUNCTION cleanup_old_test_data()
RETURNS void AS $$
BEGIN
    DELETE FROM test_reports 
    WHERE created_at < NOW() - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;

-- 注释：设置定期清理任务需要在应用层面实现，或使用pg_cron扩展
