# 邮件批量投递系统 - 职位管理模块

一个使用 AI 驱动的现代化职位管理系统，支持智能解析招聘信息、自动分类和标签生成。

## ✨ 特性

- 🤖 **AI 智能解析**: 使用 OpenAI 或兼容 API 自动解析招聘信息
- 🏷️ **自动分类**: 智能推断行业分类和生成相关标签
- 🎨 **Ins 风格界面**: 现代化、渐变色、卡片式设计
- 📊 **结构化数据**: 自动提取职位要求、薪资、地点等信息
- 🔧 **多 LLM 支持**: 支持 OpenAI、DeepSeek、Groq、Ollama 等

## 🚀 快速开始

### 前置要求

- Python 3.7+
- Node.js 16+
- OpenAI API Key（或兼容接口）

### 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
# 编辑 .env 文件，设置以下内容：
# OPENAI_API_KEY=你的API密钥
# OPENAI_BASE_URL=https://api.openai.com/v1  (可选，默认OpenAI)
# OPENAI_MODEL=gpt-4o-mini  (可选，默认gpt-4o-mini)

# 启动服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端 API 文档: http://localhost:8000/docs

**重要**: 必须在 `.env` 文件中配置 `OPENAI_API_KEY` 才能使用AI解析功能！

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端界面: http://localhost:5173

## 📖 使用指南

### 1. 配置 LLM

**在 `backend/.env` 文件中配置**:

```bash
# 必填：设置你的API密钥
OPENAI_API_KEY=sk-your-api-key-here

# 可选：使用其他兼容API
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# DeepSeek示例
# OPENAI_API_KEY=your-deepseek-key
# OPENAI_BASE_URL=https://api.deepseek.com
# OPENAI_MODEL=deepseek-chat

# Ollama本地示例
# OPENAI_API_KEY=ollama
# OPENAI_BASE_URL=http://localhost:11434/v1
# OPENAI_MODEL=llama3
```

配置后重启后端服务即可。点击界面右上角"⚙️ LLM Status"可查看当前配置状态。

### 2. 添加职位

1. 复制招聘信息（微信公众号、招聘网站等）
2. 粘贴到"Raw Job Posting Content"文本框
3. 点击"🤖 Parse with AI"
4. AI 会自动提取:
   - 职位名称、公司名称
   - 行业分类
   - 相关标签（技能、职位类型等）
   - 职位要求（学历、经验、地点、薪资）
   - 投递邮箱和邮件模板
5. 检查并编辑解析后的信息
6. 点击"💾 Save Job"保存

### 3. 查看职位列表

切换到"📋 Job List"标签查看所有职位，支持:
- 按状态筛选（Active/Draft/Expired）
- 查看标签和行业分类
- 编辑和删除职位

## 🔧 技术栈

### 后端
- **FastAPI**: 高性能异步 Web 框架
- **SQLAlchemy**: ORM 数据库操作
- **SQLite**: 开发数据库（可切换到 PostgreSQL）
- **OpenAI SDK**: LLM 集成

### 前端
- **React + TypeScript**: 类型安全的组件开发
- **Vite**: 快速构建工具
- **Axios**: HTTP 客户端
- **纯 CSS**: Ins 风格设计系统

## 📁 项目结构

```
邮件批量投递/
├── backend/                 # 后端 FastAPI 应用
│   ├── app/
│   │   ├── models/          # 数据库模型
│   │   ├── routers/         # API 路由
│   │   ├── services/        # 业务逻辑（LLM 服务）
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # 数据库连接
│   │   ├── schemas.py       # Pydantic 模型
│   │   └── main.py          # 应用入口
│   ├── requirements.txt     # Python 依赖
│   └── .env                 # 环境变量
│
├── frontend/                # 前端 React 应用
│   ├── src/
│   │   ├── components/      # React 组件
│   │   ├── api.ts           # API 客户端
│   │   ├── App.tsx          # 主应用
│   │   └── index.css        # 设计系统
│   └── package.json         # Node 依赖
│
└── 数据结构.md              # 数据库设计文档
```

## 🎯 核心功能

### LLM 智能解析

使用 Function Calling 确保结构化输出:
- 准确提取职位信息
- 智能推断行业分类
- 自动生成相关标签
- 建议邮件模板

### 自动创建分类和标签

解析时如果发现新的行业或标签会自动创建:
- 行业代码自动生成（如 "互联网/科技" → "internet"）
- 标签分类（skill/job_type/company/position）
- 智能颜色分配（Python → 蓝色，设计 → 粉色）

## 🔐 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| DATABASE_URL | 数据库连接 | sqlite+aiosqlite:///./jobs.db |
| OPENAI_API_KEY | OpenAI API 密钥 | - |
| OPENAI_BASE_URL | API 基础 URL | https://api.openai.com/v1 |
| OPENAI_MODEL | 模型名称 | gpt-4o-mini |
| HOST | 服务器地址 | 0.0.0.0 |
| PORT | 服务器端口 | 8000 |

## 📝 API 端点

### 职位管理
- `POST /api/jobs/parse` - 解析职位信息
- `POST /api/jobs` - 创建职位
- `GET /api/jobs` - 获取职位列表
- `GET /api/jobs/{id}` - 获取职位详情
- `PUT /api/jobs/{id}` - 更新职位
- `DELETE /api/jobs/{id}` - 删除职位

### 配置管理
- `POST /api/config/llm` - 保存 LLM 配置
- `GET /api/config/llm` - 获取 LLM 配置
- `POST /api/config/llm/test` - 测试连接

完整 API 文档: http://localhost:8000/docs

## 🛠️ 开发计划

- [x] 职位数据库基础功能
- [x] LLM 智能解析
- [x] Ins 风格界面
- [ ] 批量导入功能
- [ ] 邮件投递功能
- [ ] 购物车式投递管理
- [ ] 阿里云邮件推送集成

## 📄 License

MIT

## 👨‍💻 Author

Created with ❤️ for efficient job application management
