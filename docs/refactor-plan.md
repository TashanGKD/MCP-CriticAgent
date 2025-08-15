# Next.js + Python 混合架构重构方案

## 🎯 重构目标

将现有的 Batch MCP 测试框架从 CLI 工具重构为 Web 应用，部署到 Vercel 平台。

### 核心能力保持
- ✅ MCP 工具动态部署和测试
- ✅ GitHub URL → npm 包名映射  
- ✅ 跨平台 MCP 服务器通信
- ✅ JSON/HTML 测试报告生成
- ✅ AgentScope 智能代理集成

### 新增能力
- 🌐 现代化 Web 界面
- ⚡ 实时测试进度显示
- 📊 可视化测试结果
- 🔄 异步任务处理
- 📱 响应式设计

---

## 📁 重构后目录结构

```
batch_mcp/
├── 📁 frontend/                    # Next.js 前端应用
│   ├── app/                        
│   │   ├── page.tsx                # 主测试页面
│   │   ├── layout.tsx              # 根布局
│   │   ├── globals.css             # 全局样式
│   │   └── api/                    # Next.js API Routes (代理)
│   │       └── proxy/[...path].ts  # API 代理到 Python 函数
│   ├── components/                 
│   │   ├── TestForm.tsx            # URL 输入表单
│   │   ├── TestProgress.tsx        # 实时进度组件
│   │   ├── TestResults.tsx         # 结果展示组件
│   │   └── ReportViewer.tsx        # 报告查看器
│   ├── lib/                        
│   │   ├── api.ts                  # API 调用封装
│   │   ├── types.ts                # TypeScript 类型定义
│   │   └── utils.ts                # 工具函数
│   ├── package.json                
│   ├── next.config.js              
│   └── tailwind.config.js          # Tailwind CSS 配置
│
├── 📁 api/                        # Vercel Python Serverless Functions
│   ├── test-mcp.py                # 主测试端点
│   ├── list-tools.py              # 工具列表查询
│   ├── test-status.py             # 测试状态查询
│   └── requirements.txt           # Python 依赖
│
│   ├── utils/                     
│   │   ├── __init__.py
│   │   ├── csv_parser.py          # 保留现有逻辑
│   │   └── validators.py          # 输入验证
│   └── models/                    
│       ├── __init__.py
│       └── test_models.py         # Pydantic 数据模型
│
├── 📁 data/                       # 保持现有数据结构
│   ├── mcp.csv                    
│   ├── mcp_cleaned.csv            
│   └── test_results/              
│
├── 📁 shared/                     # 前后端共享类型定义
│   └── types.py                   # Python 类型定义
│
├── vercel.json                    # Vercel 部署配置
├── requirements.txt               # 根级 Python 依赖
├── package.json                   # 根级 Node.js 配置
└── README.md                      # 更新的文档
```

---

## 🌐 前端技术栈

### 核心框架
- **Next.js 14+**: App Router, SSR/SSG 支持
- **React 18**: 并发特性，Suspense
- **TypeScript**: 类型安全
- **Tailwind CSS**: 原子化 CSS 框架

### 状态管理与数据获取
- **Zustand**: 轻量级状态管理
- **TanStack Query (React Query)**: 服务器状态管理
- **WebSocket/SSE**: 实时通信

### UI 组件库
- **Headless UI**: 无样式组件基础
- **Lucide React**: 图标库
- **React Hook Form**: 表单处理

---

## ⚡ 后端技术栈

### 核心框架
- **Python 3.12**: 现有版本保持
- **Pydantic**: 数据验证和序列化
- **FastAPI/简化版**: 用于 Vercel Functions

### 保留的核心库
- **AgentScope**: 智能代理（如果可用）
- **Rich**: 日志格式化
- **Pandas**: 数据处理
- **Requests**: HTTP 客户端

---

## 🔄 重构实施计划

### 阶段一：基础架构搭建 (第1-2天)
1. ✅ 创建新的目录结构
2. ✅ 初始化 Next.js 项目
3. ✅ 配置 Vercel 部署环境
4. ✅ 创建基础 Python API 函数

### 阶段二：核心功能迁移 (第3-4天)
1. ✅ 重构 MCP 部署器为 API 函数
2. ✅ 迁移 CSV 解析和工具查找逻辑
3. ✅ 创建测试执行 API 端点
4. ✅ 实现基础前端表单

### 阶段三：高级功能实现 (第5-6天)
1. ✅ 实时进度显示
2. ✅ 测试结果可视化
3. ✅ 报告生成和展示
4. ✅ 错误处理和用户反馈

### 阶段四：优化和部署 (第7天)
1. ✅ 性能优化
2. ✅ 响应式设计
3. ✅ 生产环境部署
4. ✅ 文档更新

---

## 🎨 用户界面设计

### 主页面布局
```
┌─────────────────────────────────────┐
│  🧪 Batch MCP Testing Platform     │
├─────────────────────────────────────┤
│                                     │
│  📝 GitHub URL 输入框               │
│  ⚙️  测试选项 (超时/智能模式)        │
│  🚀 [开始测试] 按钮                │
│                                     │
├─────────────────────────────────────┤
│  📊 实时进度显示                   │
│  └── 进度条 + 状态信息              │
├─────────────────────────────────────┤
│  📋 测试结果展示                   │
│  ├── 成功率统计                    │
│  ├── 测试用例列表                  │
│  └── 📄 [查看详细报告] 链接         │
└─────────────────────────────────────┘
```

### 关键交互流程
1. **输入阶段**: URL 验证 → 工具信息预览
2. **测试阶段**: 实时进度 → 状态更新
3. **结果阶段**: 可视化展示 → 报告下载

---

## 🚀 API 设计规范

### 统一响应格式
```typescript
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
}
```

### 核心端点

#### 1. 测试 MCP 工具
```
POST /api/test-mcp
Content-Type: application/json

{
  "url": "https://github.com/upstash/context7",
  "timeout": 600,
  "smart": true,
  "verbose": false
}

Response:
{
  "success": true,
  "data": {
    "task_id": "test_20250815_143022",
    "status": "running",
    "tool_info": {
      "name": "Context7",
      "author": "upstash",
      "package_name": "github:upstash/context7"
    }
  }
}
```

#### 2. 查询测试状态
```
GET /api/test-status/{task_id}

Response:
{
  "success": true,
  "data": {
    "status": "completed",
    "progress": 100,
    "current_step": "生成报告",
    "results": {...},
    "reports": {
      "html": "/reports/test_20250815_143022.html",
      "json": "/reports/test_20250815_143022.json"
    }
  }
}
```

#### 3. 工具搜索
```
GET /api/list-tools?search=context&limit=10

Response:
{
  "success": true,
  "data": {
    "tools": [...],
    "total": 25,
    "page": 1
  }
}
```

---

## 📦 Vercel 部署配置

### vercel.json 完整配置
```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/next",
      "config": {
        "outputDirectory": "frontend/.next"
      }
    },
    {
      "src": "api/*.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "50mb"
      }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/frontend/$1"
    }
  ],
  "env": {
    "OPENAI_API_KEY": "@openai_api_key",
    "OPENAI_BASE_URL": "@openai_base_url", 
    "OPENAI_MODEL": "@openai_model",
    "DASHSCOPE_API_KEY": "@dashscope_api_key",
    "DASHSCOPE_BASE_URL": "@dashscope_base_url",
    "DASHSCOPE_MODEL": "@dashscope_model"
  },
  "functions": {
    "api/test-mcp.py": {
      "maxDuration": 300
    },
    "api/*.py": {
      "maxDuration": 60
    }
  }
}
```

### 环境变量配置
```bash
# AI 服务配置
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# 通义千问配置  
DASHSCOPE_API_KEY=sk-xxx
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen-plus
```

---

## 🔧 技术挑战与解决方案

### 1. Serverless 函数限制
**挑战**: 5分钟执行时间限制，内存限制
**解决方案**: 
- 异步任务队列（Vercel KV + 轮询）
- 流式响应处理
- 分步骤执行和状态保存

### 2. MCP 工具部署
**挑战**: npx 命令在 Serverless 环境执行
**解决方案**:
- 预编译常用工具
- 容器化部署（必要时）
- 本地缓存策略

### 3. 实时进度更新
**挑战**: Serverless 函数无法维持长连接
**解决方案**:
- 长轮询 + 状态存储
- Server-Sent Events (SSE)
- WebSocket (通过第三方服务)

### 4. 数据持久化
**挑战**: 测试结果和报告存储
**解决方案**:
- Vercel Blob Storage
- 临时文件清理策略
- CDN 加速访问

---

## 📋 迁移检查清单

### 核心功能保持
- [ ] MCP 工具 URL 解析和映射
- [ ] 跨平台 npx 部署能力
- [ ] MCP 协议通信实现
- [ ] JSON/HTML 报告生成
- [ ] AgentScope 智能代理集成

### 新增功能实现  
- [ ] 现代化 Web 界面
- [ ] 实时测试进度显示
- [ ] 可视化测试结果
- [ ] 异步任务处理
- [ ] 响应式移动端适配

### 部署和运维
- [ ] Vercel 自动部署配置
- [ ] 环境变量安全管理
- [ ] 错误监控和日志
- [ ] 性能监控和优化
- [ ] 用户反馈收集

---

## 📊 成功指标

### 功能指标
- ✅ 100% 保持现有核心功能
- 🎯 < 3 秒页面加载时间
- 🎯 95%+ API 可用性
- 🎯 支持并发测试

### 用户体验指标
- 🎯 直观的测试流程
- 🎯 实时进度反馈
- 🎯 清晰的结果展示
- 🎯 移动端友好界面

### 技术指标
- 🎯 < 100ms API 响应时间
- 🎯 < 300 秒测试完成时间
- 🎯 零停机部署
- 🎯 自动错误恢复

---

这个重构方案将在保持现有核心功能的基础上，提供现代化的 Web 用户体验，并充分利用 Vercel 平台的优势进行无缝部署。
