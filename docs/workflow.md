# 🔧 MCP Testing Framework - 架构与工作流程

## 项目概述

Batch MCP Testing Framework 是一个自动化的 MCP (Model Context Protocol) 工具测试框架，通过 URL 驱动的方式实现 MCP 工具的动态部署、智能测试和详细报告生成。

## 🏗️ 系统架构

```mermaid
graph TB
    subgraph "输入层"
        A[GitHub URL] 
        B[NPM包名]
        C[CSV批量输入]
    end
    
    subgraph "数据层"
        D[(mcp.csv<br/>5000+ 工具数据库)]
        E[.env 配置]
    end
    
    subgraph "核心处理层"
        F[CSV解析器<br/>csv_parser.py]
        G[MCP部署器<br/>simple_mcp_deployer.py]
        H[URL处理器<br/>url_mcp_processor.py]
    end
    
    subgraph "通信层"
        I[MCP通信器<br/>STDIO协议]
        J[异步MCP客户端<br/>async_mcp_client.py]
    end
    
    subgraph "测试层"
        K[基础测试<br/>连通性测试]
        L[AI智能测试<br/>test_agent.py]
        M[验证代理<br/>validation_agent.py]
    end
    
    subgraph "输出层"
        N[JSON报告]
        O[HTML报告]
        P[控制台输出]
        Q[(数据库存储)]
    end
    
    A --> F
    B --> G
    C --> F
    D --> F
    E --> G
    
    F --> H
    F --> G
    G --> I
    H --> J
    
    I --> K
    J --> L
    L --> M
    
    K --> N
    M --> N
    N --> O
    N --> P
    N --> Q
```

## 🔄 核心工作流程

### 1. URL处理流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant CLI as CLI入口
    participant Parser as CSV解析器
    participant DB as 工具数据库
    participant Deployer as MCP部署器
    participant NPX as NPX环境
    
    User->>CLI: test-url "github.com/xxx/mcp-tool"
    CLI->>Parser: 解析URL
    Parser->>DB: 查找匹配的工具信息
    DB->>Parser: 返回包名和配置
    Parser->>CLI: 工具信息
    CLI->>Deployer: 部署请求
    Deployer->>NPX: npx -y @package/name
    NPX->>Deployer: MCP服务器启动
    Deployer->>CLI: 服务器信息
```

### 2. MCP部署和通信流程

```mermaid
flowchart TD
    A[接收包名] --> B{检查Node.js环境}
    B -->|失败| C[环境错误]
    B -->|成功| D[构建NPX命令]
    
    D --> E[尝试标准启动]
    E --> F{启动成功?}
    F -->|失败| G[尝试--stdio参数]
    G --> H{启动成功?}
    H -->|失败| I[部署失败]
    H -->|成功| J[创建通信器]
    F -->|成功| J
    
    J --> K[初始化MCP协议]
    K --> L[发送initialize请求]
    L --> M{协议握手成功?}
    M -->|失败| N[通信失败]
    M -->|成功| O[获取工具列表]
    O --> P[返回服务器信息]
```

### 3. 测试执行流程

```mermaid
graph LR
    subgraph "基础测试模式"
        A1[MCP协议通信测试] --> B1[工具列表获取]
        B1 --> C1[简单工具调用]
        C1 --> D1[基础报告]
    end
    
    subgraph "AI智能测试模式"
        A2[MCP协议通信测试] --> B2[AI分析工具功能]
        B2 --> C2[生成测试用例]
        C2 --> D2[执行智能验证]
        D2 --> E2[AI分析结果]
        E2 --> F2[智能报告]
    end
    
    Start[开始测试] --> Choice{启用--smart?}
    Choice -->|否| A1
    Choice -->|是| A2
    
    D1 --> End[测试完成]
    F2 --> End
```

## 🧩 核心组件详解

### 1. CSV解析器 (csv_parser.py)

**职责**: 管理5000+工具的数据库，提供URL到包名的映射

```mermaid
classDiagram
    class MCPToolInfo {
        +name: str
        +author: str
        +description: str
        +package_name: str
        +requires_api_key: bool
        +api_requirements: List[str]
    }
    
    class CSVParser {
        +find_tool_by_url(url) MCPToolInfo
        +search_tools(query) List[MCPToolInfo]
        +get_tools_by_category(category) List[MCPToolInfo]
        +get_all_tools() List[MCPToolInfo]
    }
    
    CSVParser --> MCPToolInfo
```

### 2. MCP部署器 (simple_mcp_deployer.py)

**职责**: 动态部署和管理MCP服务器进程

```mermaid
classDiagram
    class SimpleMCPDeployer {
        +active_servers: Dict
        +platform_info: Dict
        +deploy_package(package_name) SimpleMCPServerInfo
        +cleanup_server(server_id) bool
        +cleanup_all_servers() void
    }
    
    class SimpleMCPServerInfo {
        +package_name: str
        +process: subprocess.Popen
        +communicator: SimpleMCPCommunicator  
        +server_id: str
        +available_tools: List
        +status: str
        +start_time: float
    }
    
    class SimpleMCPCommunicator {
        +process: subprocess.Popen
        +send_request(request, timeout) Dict
        +start_reader_thread() void
        +cleanup() void
    }
    
    SimpleMCPDeployer --> SimpleMCPServerInfo
    SimpleMCPServerInfo --> SimpleMCPCommunicator
```

### 3. AI智能测试代理

**职责**: 使用大模型生成和执行智能测试用例

```mermaid
graph TD
    A[工具信息分析] --> B[理解功能和参数]
    B --> C[生成测试用例]
    C --> D[构造参数]
    D --> E[执行MCP调用]
    E --> F[分析结果]
    F --> G[生成改进建议]
    
    subgraph "AI代理组件"
        H[TestGeneratorAgent<br/>测试生成代理]
        I[ValidationAgent<br/>验证执行代理]
    end
    
    B --> H
    E --> I
```

## 📊 数据流图

```mermaid
flowchart LR
    subgraph "输入数据"
        A[GitHub URL]
        B[NPM包名] 
        C[批量CSV]
    end
    
    subgraph "处理管道"
        D[URL解析] --> E[包名映射]
        E --> F[NPX部署]
        F --> G[STDIO通信]
        G --> H[测试执行]
        H --> I[结果收集]
    end
    
    subgraph "输出数据"
        J[JSON报告]
        K[HTML报告]
        L[控制台日志]
        M[数据库记录]
    end
    
    A --> D
    B --> F
    C --> D
    
    I --> J
    I --> K
    I --> L
    I --> M
```

## 🔧 关键技术实现

### 1. 跨平台STDIO通信

```python
# 核心通信逻辑
def send_request(self, request, timeout=30):
    """发送MCP请求并等待响应"""
    with self.lock:
        # 构造JSON-RPC请求
        json_request = json.dumps(request) + '\n'
        
        # 发送到MCP服务器stdin
        self.process.stdin.write(json_request.encode())
        self.process.stdin.flush()
        
        # 等待响应
        try:
            response = self.response_queue.get(timeout=timeout)
            return {'success': True, 'data': json.loads(response)}
        except queue.Empty:
            return {'success': False, 'error': '请求超时'}
```

### 2. 自适应部署策略

```python
def _try_start_process(self, cmd, creation_flags, display_name, run_command, package_name):
    """尝试启动进程，带--stdio回退机制"""
    
    # 第一次尝试：标准启动
    try:
        process = subprocess.Popen(cmd, ...)
        if self._test_process_health(process):
            return process
    except:
        pass
    
    # 第二次尝试：添加--stdio参数
    cmd_with_stdio = cmd + ['--stdio']
    try:
        process = subprocess.Popen(cmd_with_stdio, ...)
        if self._test_process_health(process):
            return process
    except:
        pass
        
    return None
```

### 3. AI测试用例生成

```python
async def generate_test_cases(self, tool_info: MCPToolInfo, available_tools: List):
    """使用AI生成针对性测试用例"""
    
    # 分析工具功能
    analysis_prompt = f"""
    分析MCP工具: {tool_info.name}
    可用工具: {available_tools}
    生成3-5个测试用例，包括：
    1. 基础功能测试
    2. 边界条件测试  
    3. 错误处理测试
    """
    
    # 调用AI模型生成
    response = await self.ai_model.generate(analysis_prompt)
    
    # 解析为结构化测试用例
    return self._parse_test_cases(response)
```

## 📈 性能优化策略

### 1. 并发处理
- 使用异步I/O处理MCP通信
- 批量测试支持限流控制
- 智能超时和重试机制

### 2. 资源管理
- 自动清理MCP服务器进程
- 内存使用监控和限制
- 磁盘空间管理

### 3. 错误恢复
- 多级回退策略
- 详细错误诊断
- 自动恢复建议

## 🎯 扩展性设计

### 1. 插件架构
- 支持自定义测试代理
- 可扩展报告格式
- 模块化组件设计

### 2. 配置驱动
- 环境变量配置
- YAML/JSON配置文件
- 运行时参数调整

### 3. 集成能力
- GitHub Actions支持
- CI/CD管道集成
- API接口提供

---

**这个架构确保了框架的可靠性、扩展性和易用性，为MCP生态系统提供了强大的测试基础设施。** 🔧✨
