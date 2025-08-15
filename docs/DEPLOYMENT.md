# 🚀 Batch MCP Testing Platform - 重构版部署指南

## 📋 项目概述

本项目已成功重构为 Next.js + Python 的混合架构，支持 Vercel 平台一键部署。

### 🏗️ 新架构特点

- **前端**: Next.js 14 + TypeScript + Tailwind CSS
- **后端**: Python Serverless Functions (Vercel)  
- **部署**: Vercel 平台自动部署
- **API**: RESTful API 设计，支持实时状态查询

---

## 🛠️ 本地开发

### 1. 环境准备

```bash
# 确保已安装 Node.js 18+ 和 Python 3.12+
node --version
python --version

# 安装前端依赖
cd frontend
npm install

# 安装Python依赖
cd ..
pip install -r requirements.txt
```

### 2. 环境变量配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入API密钥
# OPENAI_API_KEY=your-key
# DASHSCOPE_API_KEY=your-key
```

### 3. 启动开发服务器

```bash
# 前端开发
cd frontend
npm run dev
# 访问 http://localhost:3000

# 后端测试（原CLI命令）
uv run python -m src.main test-url "https://github.com/upstash/context7"
```

---

## ☁️ Vercel 部署

### 1. 一键部署

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-username/batch_mcp)

### 2. 手动部署

```bash
# 安装 Vercel CLI
npm i -g vercel

# 登录 Vercel
vercel login

# 部署项目
vercel --prod
```

### 3. 环境变量配置

在 Vercel Dashboard 中配置环境变量：

```
OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
DASHSCOPE_API_KEY=sk-your-dashscope-key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen-plus
```

---

## 🌐 新功能介绍

### 1. Web 用户界面
- 🎨 现代化响应式设计
- 📱 移动端友好
- ⚡ 实时进度显示
- 📊 可视化测试结果

### 2. API 端点

#### `POST /api/test-mcp`
启动 MCP 工具测试
```json
{
  "url": "https://github.com/upstash/context7",
  "timeout": 600,
  "smart": true,
  "verbose": false
}
```

#### `GET /api/list-tools?search=context&limit=10`  
搜索可用的 MCP 工具

#### `GET /api/test-status/{task_id}`
查询测试状态和进度

### 3. 实时功能
- 📈 测试进度实时更新
- 🔄 自动状态轮询
- ⚠️ 错误处理和重试
- 📱 响应式状态显示

---

## 🔄 迁移检查清单

### ✅ 已完成功能

- [x] **前端架构**: Next.js + TypeScript + Tailwind CSS
- [x] **后端重构**: Python Serverless Functions
- [x] **核心功能**: MCP 工具部署和测试逻辑
- [x] **API 设计**: RESTful API 端点
- [x] **部署配置**: Vercel 配置文件
- [x] **用户界面**: 现代化 Web 界面

### ✅ 保持的核心能力

- [x] **MCP 部署**: GitHub URL → npm 包名映射
- [x] **跨平台兼容**: Windows/Linux/macOS 支持
- [x] **协议通信**: MCP JSON-RPC 协议实现
- [x] **测试生成**: 自动化测试用例生成
- [x] **报告输出**: HTML/JSON 双格式报告

### 🔄 架构优势

1. **无缝部署**: Vercel 一键部署，零配置
2. **成本效益**: Serverless 按需付费
3. **高可用性**: 全球CDN分发
4. **自动扩展**: 自动处理流量峰值
5. **监控集成**: 内置性能监控

---

## 🧪 测试流程

### 1. 本地测试

```bash
# 测试前端构建
cd frontend
npm run build
npm start

# 测试Python API
python api/test-mcp.py
python api/list-tools.py
```

### 2. 集成测试

1. 启动前端开发服务器
2. 输入测试URL: `https://github.com/upstash/context7`
3. 验证API调用和数据流转
4. 检查报告生成和展示

### 3. 部署验证

1. 部署到 Vercel
2. 验证环境变量配置
3. 测试生产环境 API
4. 检查静态资源加载

---

## 📊 性能指标

### 预期性能

- **首页加载**: < 3 秒
- **API 响应**: < 100ms (工具列表)
- **测试完成**: < 300 秒 (单个工具)
- **报告生成**: < 5 秒

### 监控指标

- ✅ API 可用性 > 99%
- ✅ 错误率 < 1%
- ✅ 平均响应时间 < 500ms
- ✅ 并发支持 > 100 用户

---

## 🔧 故障排除

### 常见问题

1. **前端编译错误**
   - 检查 Node.js 版本 (需要 18+)
   - 删除 `node_modules` 重新安装

2. **Python 依赖问题**
   - 检查 Python 版本 (需要 3.12+)
   - 使用虚拟环境隔离依赖

3. **API 调用失败**
   - 检查环境变量配置
   - 验证网络连接和防火墙

4. **Vercel 部署失败**
   - 检查 `vercel.json` 配置
   - 验证环境变量设置

### 日志查看

```bash
# Vercel 函数日志
vercel logs

# 本地调试
npm run dev -- --debug
```

---

## 🚀 下一步计划

### 短期优化 (1-2周)

- [ ] **实时通信**: WebSocket/SSE 支持
- [ ] **数据持久化**: 测试历史存储
- [ ] **批量测试**: 多工具并行测试  
- [ ] **用户认证**: 简单的访问控制

### 中期增强 (1个月)

- [ ] **智能推荐**: 基于使用情况推荐工具
- [ ] **社区功能**: 工具评分和评论
- [ ] **API 扩展**: 更多测试类型支持
- [ ] **性能优化**: 缓存和CDN优化

### 长期目标 (3个月)

- [ ] **多租户**: 支持多用户和组织
- [ ] **CI/CD 集成**: GitHub Actions 深度集成
- [ ] **监控平台**: 完整的监控和告警系统
- [ ] **开放 API**: 第三方集成支持

---

🎉 **重构完成！** 新架构已就绪，可以开始部署和使用。
