# GitHub Actions 前端集成部署指南

## 🔧 **部署方式说明**

您的部署方式是：**通过 GitHub 提交自动触发 Vercel 部署**

### **部署流程**：
1. 代码提交到 GitHub → 2. Vercel 自动检测到更改 → 3. 自动构建和部署

## 🚨 **之前遇到 404 错误的原因**

1. **API 函数入口点问题**：Vercel 需要特定的函数签名
2. **路由配置不完整**：API 路径没有正确映射
3. **环境变量配置**：需要在 Vercel Dashboard 中配置

## ✅ **已修复的问题**

1. **修复了 API 函数入口点**：
   - `trigger-github-workflow.py` - 触发工作流
   - `workflow-status.py` - 查询工作流状态

2. **更新了 vercel.json 配置**：
   - 添加了明确的 API 路由映射
   - 配置了 Python 运行时参数
   - 设置了环境变量引用

3. **环境变量配置**：
   - `GITHUB_TOKEN` - 需要在 Vercel Dashboard 中设置
   - `GITHUB_REPOSITORY` - 已硬编码为 "gqy22/batch_mcp"

## 🎯 **部署步骤**

### **Step 1: 确保 Vercel 环境变量配置**
在 Vercel Dashboard 中设置：
- `GITHUB_TOKEN` = `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`

### **Step 2: 提交代码到 GitHub**
```bash
git add .
git commit -m "fix: 修复 GitHub Actions API 集成和 Vercel 部署配置"
git push origin main
```

### **Step 3: 等待 Vercel 自动部署**
- Vercel 会自动检测到 GitHub 推送
- 大约 1-3 分钟完成部署
- 可以在 Vercel Dashboard 查看部署状态

### **Step 4: 测试 API 端点**
部署完成后，测试这些端点：
- `https://batch-mcp.vercel.app/api/trigger-github-workflow`
- `https://batch-mcp.vercel.app/api/workflow-status`

## 🔍 **验证部署成功的方法**

1. **前端功能测试**：
   - 访问 https://batch-mcp.vercel.app
   - 在页面顶部找到 "GitHub Actions 工作流触发器"
   - 尝试点击"触发工作流"按钮

2. **API 端点测试**：
   ```bash
   # 测试状态查询（不需要POST数据）
   curl https://batch-mcp.vercel.app/api/workflow-status
   
   # 如果返回 JSON 而不是 404，说明 API 正常
   ```

## 🐛 **如果仍然遇到问题**

1. **检查 Vercel 构建日志**：
   - 访问 Vercel Dashboard
   - 查看最新部署的构建日志

2. **检查环境变量**：
   - 确保 `GITHUB_TOKEN` 在 Vercel 中正确设置
   - 检查 Token 权限（需要 workflow 权限）

3. **API 路径检查**：
   - 确保请求的是正确的端点路径
   - 检查前端代码中的 fetch URL

## 📊 **预期的正常行为**

部署成功后：
- ✅ 前端页面正常显示
- ✅ GitHub Actions 触发器界面显示
- ✅ 点击"触发工作流"后返回成功消息
- ✅ 工作流状态可以正常查询和显示

现在您可以进行 Git 提交和推送来触发自动部署！
