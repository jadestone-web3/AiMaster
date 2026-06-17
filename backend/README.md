# AiMaster 极简化后端

这是为 AiMaster Chrome 插件准备的极简化后端服务，支持基本功能。

## 🚀 快速启动

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动

### 3. 访问 API 文档

浏览器打开：`http://localhost:8000/docs`

---

## 🔑 默认账号

```
用户名: admin
密码: admin123
```

验证码可以**任意输入**（极简化版本）

---

## ⚙️ 配置 Chrome 插件

1. 打开 Chrome 插件弹窗
2. 点击"💻 打开后台管理"
3. 在设置中修改 API 地址为：`http://localhost:8000`

或者在 `popup.js` 中修改：
```javascript
let API_BASE_URL = 'http://localhost:8000';
```

---

## 📡 API 接口

### 认证相关

- `GET /api/auth/captcha` - 获取验证码
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/refresh` - 刷新 token
- `GET /api/auth/me` - 获取当前用户信息

### 文章和任务

- `POST /api/articles` - 提交文章进行AI改写
- `GET /api/tasks?user=xxx` - 获取任务列表
- `GET /api/tasks/:id` - 获取任务详情

### 其他

- `GET /` - 健康检查
- `GET /health` - 健康检查

---

## 🎯 功能说明

### ✅ 已实现

- [x] 用户登录（JWT 认证）
- [x] 提交文章任务
- [x] 异步任务处理
- [x] 任务进度跟踪
- [x] 获取改写后的文章

### ⚠️ 极简化说明

1. **验证码**：任意输入即可（不验证）
2. **密码**：明文存储（仅用于测试）
3. **AI改写**：模拟实现（添加【AI改写】前缀）
4. **数据存储**：内存存储（重启后丢失）
5. **并发处理**：使用 asyncio（生产环境建议用 Celery）

---

## 🔧 接入真实 AI（可选）

如果需要真实的 AI 改写功能，修改 `main.py` 中的 `process_article` 函数：

```python
async def process_article(task_id: str, article: dict):
    try:
        # 调用 OpenAI API
        import openai

        openai.api_key = "your-api-key"

        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的内容改写助手"},
                {"role": "user", "content": f"请改写以下文章：\n\n{article.get('content', '')}"}
            ]
        )

        rewritten_content = response.choices[0].message.content

        tasks[task_id]["rewrittenArticle"] = {
            "title": f"【AI改写】{article.get('title', '')}",
            "content": rewritten_content
        }
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["progress"] = 100

    except Exception as e:
        print(f"AI改写失败: {e}")
        tasks[task_id]["status"] = "failed"
```

---

## 📝 测试流程

1. 启动后端服务
2. Chrome 插件中使用账号 `admin / admin123` 登录
3. 访问任意支持的新闻网站
4. 点击"爬取文章"
5. 等待任务完成（约5秒）
6. 点击"发布到编辑器"

---

## 🛠️ 生产环境建议

如果要用于生产环境，建议升级：

1. **数据库**：使用 PostgreSQL 或 MySQL 替代内存存储
2. **密码加密**：使用 bcrypt 加密密码
3. **任务队列**：使用 Celery + Redis 处理异步任务
4. **真实验证码**：使用 Pillow 生成图片验证码
5. **AI服务**：接入 OpenAI 或其他 AI 服务
6. **日志系统**：添加日志记录和监控
7. **限流**：添加 API 限流防止滥用

---

## 📄 License

MIT
