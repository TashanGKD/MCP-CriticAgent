# Supabase 设置操作清单

完成以下步骤设置您的MCP测试数据库：

## ✅ 第一步：创建Supabase项目

### 1.1 访问并登录
- [ ] 打开 https://app.supabase.com
- [ ] 使用GitHub或Google账号登录

### 1.2 创建新项目
- [ ] 点击 "New project" 按钮
- [ ] 选择Organization（通常是您的用户名）
- [ ] **项目名称**：输入 `mcp-testing` 或 `mcp-agent-db`
- [ ] **数据库密码**：设置强密码（记住这个密码！）
- [ ] **区域**：选择 `ap-northeast-1`（亚太东京）或离您最近的区域
- [ ] 点击 "Create new project"
- [ ] 等待2-3分钟完成创建

## ✅ 第二步：获取API密钥

### 2.1 导航到API设置
- [ ] 项目创建完成后，在左侧菜单找到 **Settings**
- [ ] 点击 **API** 子菜单

### 2.2 复制必要信息
- [ ] 复制 **Project URL** （形如：https://xxx.supabase.co）
- [ ] 复制 **service_role** 密钥（点击眼睛图标显示完整密钥）

⚠️ **重要**：service_role密钥有完全数据库访问权限，请妥善保管！

## ✅ 第三步：配置环境变量

### 3.1 编辑.env文件
- [ ] 打开项目根目录的 `.env` 文件
- [ ] 添加以下配置：

```env
# Supabase配置
SUPABASE_URL=你的项目URL
SUPABASE_SERVICE_ROLE_KEY=你的service_role密钥
```

### 3.2 验证.env文件格式
```env
# 示例（替换为您的实际值）
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## ✅ 第四步：初始化数据库

### 4.1 测试连接
```bash
uv run python src/tools/db_migrate.py test
```
**预期输出**：`✅ 数据库连接成功!`

### 4.2 创建表结构
```bash
uv run python src/tools/db_migrate.py init
```
**预期输出**：看到45条SQL语句成功执行

### 4.3 填充示例数据（可选）
```bash
uv run python src/tools/db_migrate.py seed
```

## ✅ 第五步：验证完整配置

### 5.1 运行验证脚本
```bash
uv run python src/tools/setup_validator.py
```

### 5.2 检查验证结果
应该看到：
- ✅ 通过 环境变量配置
- ✅ 通过 Supabase连接  
- ✅ 通过 数据库表结构

## ✅ 第六步：运行完整测试

### 6.1 执行MCP测试
```bash
uv run python src/main.py
```

### 6.2 验证数据库存储
测试完成后，访问Supabase Dashboard中的 **Table Editor**，应该能看到：
- `test_reports` 表中有新的测试记录
- 其他相关表中有对应的数据

---

## 🚨 常见问题解决

### 连接失败
- 检查网络连接
- 确认URL和密钥正确
- 验证.env文件格式

### 表不存在
- 运行 `uv run python src/tools/db_migrate.py init`
- 检查Supabase项目状态

### 权限错误
- 确认使用的是 service_role 密钥，不是 anon 密钥
- 检查密钥是否完整复制

---

## 📞 获得帮助

如果遇到问题：
1. 查看终端详细错误信息
2. 检查 `docs/SUPABASE_SETUP.md` 详细文档
3. 重新验证每个步骤的配置

**完成所有步骤后，您的MCP测试框架就可以将结果存储到Supabase数据库了！** 🎉
