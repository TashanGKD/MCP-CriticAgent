# GitHub Actions + Vercel 双模式架构实现指南

## 🎯 架构概述

你的新架构支持两种测试模式：

### 1. Vercel 快速测试模式
- **前端** → **Vercel API** → **基础MCP测试**
- 响应时间：< 30秒
- 功能：基础连接、工具列表、部署验证

### 2. GitHub Actions AI增强模式  
- **前端** → **Vercel API** → **GitHub Actions** → **AI增强测试** → **结果存储** → **前端轮询**
- 响应时间：5-10分钟
- 功能：AI分析、详细报告、性能基准

## 🛠️ 需要的配置更新

### 1. GitHub Repository Settings
在 `https://github.com/gqy22/batch_mcp/settings/secrets/actions` 中添加：

```
# GitHub API Token (用于触发和查询workflow)
HUB_TOKEN=ghp_your_github_personal_access_token

# 原有的API密钥 (仅用于GitHub Actions)
OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
DASHSCOPE_API_KEY=sk-your-dashscope-key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen-plus
```

### 2. Vercel Environment Variables
在 Vercel Dashboard 中配置：

```
# GitHub集成 (仅用于触发Actions)
HUB_TOKEN=ghp_your_github_personal_access_token
GITHUB_REPOSITORY=gqy22/batch_mcp
```

### 3. GitHub Pages (用于存储测试结果)
在仓库设置中启用 GitHub Pages：
- Source: GitHub Actions
- 用于存储API结果文件

## 📁 新增文件

### 1. Workflow 文件
- `.github/workflows/mcp-api-service.yml` - 支持API调用的workflow

### 2. API 端点
- `api/trigger-github-test.py` - 触发GitHub Actions
- `api/github-test-status.py` - 查询测试状态

### 3. 前端组件
- `frontend/components/IntegratedTestForm.tsx` - 双模式测试表单
- `frontend/app/home-integrated.tsx` - 集成主页面

## 🔄 工作流程

### GitHub Actions 测试流程：
1. **前端提交** → 选择GitHub模式，输入URL
2. **API触发** → `/api/trigger-github-test` 调用GitHub API
3. **Actions运行** → 在GitHub服务器执行完整测试
4. **结果存储** → 测试结果保存到GitHub Pages
5. **状态轮询** → 前端定期查询 `/api/github-test-status`
6. **显示结果** → 解析并展示AI增强的测试报告

### Vercel 快速测试流程：
1. **前端提交** → 选择Vercel模式
2. **直接调用** → `/api/test-mcp` 执行基础测试
3. **即时返回** → 快速显示基础测试结果

## ✅ 优势

### 对用户的好处：
- **选择权**：可根据需求选择快速或详细测试
- **可视化**：统一的Web界面，无需命令行
- **实时反馈**：进度显示和状态更新
- **AI增强**：智能分析和建议

### 对开发的好处：
- **资源优化**：AI功能在GitHub免费运行
- **成本控制**：Vercel只处理轻量级API
- **扩展性**：可以独立优化两种模式
- **可靠性**：双重备份，一个模式故障不影响另一个

## 🚀 部署步骤

1. **更新配置**：按上述说明配置环境变量
2. **推送代码**：提交所有新文件
3. **验证Workflow**：确保`.github/workflows/mcp-api-service.yml`有效
4. **测试集成**：先测试Vercel模式，再测试GitHub模式
5. **监控日志**：检查两种模式的执行情况

## 🎉 完成状态

你现在拥有一个完整的双模式MCP测试平台：
- ✅ 保留原有CLI功能
- ✅ 新增现代Web界面  
- ✅ 支持快速和深度两种测试
- ✅ AI增强分析能力
- ✅ 云端部署就绪

这个架构既满足了快速验证的需求，又保留了深度分析的能力，是一个很好的解决方案！
