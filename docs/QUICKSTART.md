# 🚀 Supabase快速开始（5分钟设置）

## 📝 您现在需要做什么

您已经有了完整的代码和文档，现在只需要完成Supabase的设置：

### 1️⃣ 创建Supabase项目（2分钟）

```
1. 访问：https://app.supabase.com
2. 登录（使用GitHub/Google账号）
3. 点击 "New project"
4. 填写：
   - 项目名：mcp-testing （推荐）
   - 密码：设置一个强密码
   - 区域：ap-northeast-1 （亚洲）
5. 等待创建完成
```

### 2️⃣ 获取API信息（1分钟）

```
1. 项目创建完成后
2. 左侧菜单 → Settings → API
3. 复制两个值：
   - Project URL（项目地址）
   - service_role key（服务密钥，点击眼睛图标显示）
```

### 3️⃣ 更新.env文件（1分钟）

```env
# 在 .env 文件中添加：
SUPABASE_URL=你复制的项目地址
SUPABASE_SERVICE_ROLE_KEY=你复制的服务密钥
```

### 4️⃣ 初始化数据库（2分钟）

**通过Supabase Dashboard执行SQL**

```
1. 访问您的Supabase项目Dashboard
2. 左侧菜单 → SQL Editor
3. 点击 "New query" 
4. 复制 database/init_complete.sql 的全部内容
5. 粘贴到编辑器并点击 "Run"
6. 确认看到成功消息（包含表创建和RLS策略）
```

然后验证配置：
```bash
uv run python src/tools/setup_validator.py
```

## ✅ 完成！

如果看到"🎉 所有验证都通过!"，就可以运行：
```bash
uv run python src/main.py
```

## 🆘 需要帮助？

- 详细步骤：查看 `docs/SUPABASE_CHECKLIST.md`
- 完整文档：查看 `docs/SUPABASE_SETUP.md`
- 有问题时查看终端错误信息
