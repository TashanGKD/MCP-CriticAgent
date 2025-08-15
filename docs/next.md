# 下一步行动计划

## 🎉 MVP 已完成！

✅ **核心目标达成**: 输入 GitHub MCP URL → 解析/映射包名 → npx 启动 MCP → 初始化协议 → 连通性/功能测试 → 报告输出

### 🔧 关键问题解决
- ✅ **协议兼容性**: 修复 STDIO 传输协议，从 Content-Length 帧改为标准的换行符分隔格式
- ✅ **URL→包名映射**: 支持 GitHub URL 自动构造 `github:owner/repo` 规范  
- ✅ **报告生成**: 修复除零错误，完善 JSON/HTML 双格式输出
- ✅ **端到端验证**: 成功与真实 MCP 服务器 (@hakan.ucar/hangi-kredi-mcp) 通信

### 📊 当前能力
- 🔍 **工具发现**: CSV 数据库 + URL 智能解析
- 🚀 **自动部署**: 跨平台 npx 包管理，进程控制
- 📡 **协议通信**: MCP STDIO 标准兼容，JSON-RPC 完整实现  
- 🧪 **功能测试**: 初始化、工具列表、基础调用测试
- 📊 **报告生成**: 多格式结果输出，性能指标统计

---

## 🚀 后续增强方向

### 1. 规模化测试 [高优先级]
- [ ] **批量处理**: 并行测试多个 URL，进度条显示，智能重试机制
- [ ] **数据库集成**: 测试结果持久化，历史趋势分析，性能基准对比
- [ ] **CI/CD 集成**: GitHub Actions 定期测试 MCP 生态质量

### 2. 智能测试增强 [中优先级]  
- [ ] **智能参数生成**: 基于工具 schema 自动生成测试参数
- [ ] **语义化测试**: 理解工具功能，生成有意义的测试用例
- [ ] **错误分析**: 智能诊断部署失败原因，提供修复建议

### 3. 用户体验优化 [中优先级]
- [ ] **Web UI**: 可视化测试界面，拖拽式批量测试
- [ ] **交互式测试**: 实时 MCP 工具调试和参数调整  
- [ ] **社区集成**: 测试结果分享，工具评分和推荐

### 4. 生态扩展 [低优先级]
- [ ] **多协议支持**: HTTP/SSE 传输协议扩展
- [ ] **云端部署**: Docker 容器化，Kubernetes 集群支持
- [ ] **API 服务**: RESTful 接口，第三方集成支持

---

## ✅ 已完成的核心功能
- [x] JSON/HTML多格式报告
- [x] 性能指标和成功率分析
- [x] Rich控制台可视化输出
- [x] 自动时间戳和会话跟踪

## 待完成的优化项目 🔧

### 1. AgentScope完善 [高优先级]
- [ ] 修复service_toolkit导入问题
- [ ] 优化智能代理提示词设计
- [ ] 增加更多测试场景识别

### 1.1 智能测试接口修复 [高优先级]
- [ ] 为 SimpleMCPCommunicator 增加异步接口：list_tools()/call_tool()（内部封装 send_request）
- [ ] 修复 main._run_smart_test 的通信器注入（避免以 communicator 构造 communicator）
- [ ] 在 ValidationAgent 增加对基础通信器的适配层（缺少接口时自动回退基础规则）

### 2. 并行化增强 [中优先级]
- [ ] 批量URL测试并行处理
- [ ] 测试用例并发执行优化
- [ ] 资源管理和进程池

### 2.1 启动参数与容错 [中优先级]
- [ ] 为部署器增加 run_command/args 支持（优先使用 CSV 中的 run_command，默认附加 --stdio）
- [ ] 启动失败的诊断与重试（npm cache clean、--prefer-online、超时重试）

### 3. 功能扩展 [中优先级]
- [ ] 支持更多代码仓库平台
- [ ] 配置文件和测试模板系统
- [ ] 历史数据分析和趋势报告

### 3.1 协议与解析 [高优先级] 🆙
- [x] ~~实现 JSON-RPC Content-Length 帧解析与多消息聚合~~ **已实现但格式不兼容**
- [ ] **紧急**: 分析 MCP SDK 期望的 STDIO 协议帧格式（通过抓包或源码分析）
- [ ] 修正我们的 Content-Length 帧编码以匹配 MCP SDK 期望格式
- [ ] 统一工具响应解析与错误归因（初始化/工具列表/工具调用分层报错）

### 4. 用户体验 [低优先级]
- [ ] 交互式CLI界面
- [ ] Web Dashboard
- [ ] 插件系统支持

## 立即行动项 🚀

### 本周目标
1. **修复MCP协议兼容性** - 分析 MCP SDK 期望的 STDIO 帧格式并调整我们的实现
2. **实际工具测试** - 使用修复后的协议验证真实MCP工具
3. **智能测试完善** - 为 SimpleMCPCommunicator 增加异步接口
4. **文档完善** - 更新README和使用指南

### 推荐测试命令
```bash
# 基础功能测试
uv run python -m src.main list-tools --limit 5

# 智能URL测试
uv run python -m src.main smart-test-url "@modelcontextprotocol/server-filesystem" --timeout 20

# 包测试
uv run python -m src.main test-package @modelcontextprotocol/server-filesystem --smart

# 验证脚本
uv run python test/verify_agents.py

# 一键 URL（包含 GitHub）测试（报告会保存到 data/test_results/reports）
uv run python -m src.main https://github.com/upstash/context7 --timeout 25
uv run python -m src.main smart-test-url https://github.com/upstash/context7 --timeout 25
```
1. **错误诊断增强** - MCP部署失败的智能诊断和修复建议
2. **API服务化** - 提供RESTful API接口
3. **持续集成** - 定期自动验证MCP工具可用性

## 技术债务
1. **原版部署器修复** - 解决tools.mcp_tools_config导入问题
2. **测试覆盖** - 添加单元测试和集成测试
3. **文档完善** - API文档和使用指南

## 运行前置（Checklist）
- [ ] uv sync（安装 rich/pandas/typer 等依赖）
- [ ] Windows 安装 Node.js（提供 npx）
- [ ] .env 配置 OPENAI_API_KEY（如需智能测试）
- [ ] data/mcp.csv 存在（用于映射与搜索）

---
*阶段性胜利：核心框架完成，准备进入真实部署验证阶段*
