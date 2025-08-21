# MCP工具测试 - 快速使用指南

## 🚀 快速开始

### 环境检查
```bash
# 检查平台信息
python test_crossplatform_mcp.py --info
```

### 单个工具测试
```bash
# 快速测试单个工具
python test_single_mcp_tool.py context7
python test_single_mcp_tool.py youtube
python test_single_mcp_tool.py svelte

# 详细输出模式
python test_single_mcp_tool.py think --verbose
```

### 全量测试
```bash
# 测试所有工具
python test_crossplatform_mcp.py --all

# 测试指定工具
python test_crossplatform_mcp.py --tool context7
```

## 📁 文件说明

### 核心测试框架
- `test_crossplatform_mcp.py` - **主要测试框架** (跨平台兼容)
- `test_single_mcp_tool.py` - **快速单工具测试**

### 配置文件
- `mcp_tools_config.py` - MCP工具配置
- `universal_mcp_test_report.md` - 最新测试报告

### 辅助工具
- `mcp_test_summary.py` - 测试结果追踪

## ✅ 已验证的工具

| 工具 | 状态 | 功能 |
|------|------|------|
| context7 | ✅ | 库文档查询 |
| youtube | ✅ | 视频信息获取 |
| think | ✅ | 思考分析 |
| svelte | ✅ | Svelte文档 |
| 12306 | ✅ | 火车票查询 |
| openalex | ⚠️ | 学术检索 (需API密钥) |

## 🔧 环境要求

- **Python 3.12+** (推荐使用UV环境管理)
- **Node.js 18+** (用于MCP服务器)
- **OpenAI API** (配置在.env文件中)

## 📋 测试检查清单

### 准备工作
- [ ] 检查Node.js安装: `node --version`
- [ ] 检查npx可用: `npx --version` 
- [ ] 配置.env文件: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`

### 验证步骤
- [ ] 平台信息检查: `python test_crossplatform_mcp.py --info`
- [ ] 单工具测试: `python test_single_mcp_tool.py context7`
- [ ] 全量测试: `python test_crossplatform_mcp.py --all`

## 🎯 成功标志

看到以下输出表示测试成功：
```
🎉 [工具名]验证成功！
✅ 验证要点:
   - 成功部署了真实的[工具名]
   - AgentScope通过MCP协议调用了真实工具
   - 验证了端到端的[工具名]集成
   - 获取了有效的[类别]结果
   - 跨平台兼容性: Windows/Linux/macOS
```

## 🐛 常见问题

### Node.js问题
```
❌ Node.js/npx不可用，请先安装Node.js
```
**解决**: 从 https://nodejs.org 安装最新LTS版本

### 环境变量问题  
```
❌ 缺少环境变量: OPENAI_API_KEY
```
**解决**: 正确配置.env文件

### 网络问题
```
❌ MCP服务器启动失败
```
**解决**: 检查网络连接，确保能访问npm registry

---

**更新日期**: 2025年8月14日  
**框架版本**: v2.0.0  
**兼容平台**: Windows/Linux/macOS
