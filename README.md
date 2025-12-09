# 🚀 XRun - AI驱动的一站式自动化测试平台

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![Django](https://img.shields.io/badge/django-4.0+-orange.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

**XRun - 让AI驱动你的自动化测试**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [文档](#-文档) • [更新日志](#-更新日志)

</div>

---

## 📢 重要公告

🎉 **V2.0 重大升级！** 项目已从传统API测试平台升级为AI驱动的一站式自动化测试平台。详见 [迁移说明](MIGRATION_V2.md)

---

## ✨ 功能特性

### 🎯 核心功能

#### 1️⃣ AI UI自动化测试
- 🧠 **智能元素识别**：基于AI的页面元素自动识别和定位
- 🔄 **自愈合能力**：元素变化时自动适应，减少维护成本
- 📝 **自动脚本生成**：录制操作自动生成测试脚本
- 🎨 **可视化设计**：拖拽式测试流程设计

#### 2️⃣ AI接口自动化测试
- 📄 **智能文档解析**：自动解析Swagger/OpenAPI文档
- 🤖 **用例自动生成**：AI生成完整的接口测试用例
- ✅ **智能断言**：自动生成合理的断言规则
- 🔀 **参数智能组合**：自动生成边界值和组合测试

#### 3️⃣ AI功能自动化测试
- 📋 **需求理解**：智能解析需求文档生成测试场景
- 🎯 **场景覆盖**：AI分析确保测试场景全覆盖
- 📊 **风险评估**：预测潜在缺陷和风险点
- 📈 **智能报告**：自动生成洞察性测试报告

#### 4️⃣ 统一测试管理
- 📁 **项目管理**：多项目、多环境管理
- 📝 **用例管理**：测试用例的增删改查
- ⏰ **定时执行**：支持定时任务和CI/CD集成
- 📊 **数据看板**：实时查看测试数据和趋势
- 👥 **团队协作**：支持多人协作和权限管理

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────┐
│                   Web Frontend                      │
│            (React + TypeScript + Ant Design)        │
└────────────────────┬────────────────────────────────┘
                     │ REST API
┌────────────────────┴────────────────────────────────┐
│              Django Backend (Python)                │
├─────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌─────────────────┐  │
│  │ AI Engine│  │  Executor│  │  Test Manager   │  │
│  └──────────┘  └──────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────┐ │
│  │        AI Models (OpenAI / Local LLM)        │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
           │                      │
    ┌──────┴──────┐        ┌─────┴──────┐
    │   Database  │        │   Redis    │
    │   (MySQL)   │        │   (Cache)  │
    └─────────────┘        └────────────┘
```

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Node.js 16+
- MySQL 8.0+
- Redis 6.0+

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/wangxiaoqi-maker/XRun.git
cd XRun

# 2. 安装后端依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp env.example.txt .env
# 编辑 .env 文件，配置数据库和AI API密钥

# 4. 数据库迁移
python manage.py migrate

# 5. 创建超级用户
python manage.py createsuperuser

# 6. 启动后端服务
python manage.py runserver

# 7. 安装前端依赖（新终端）
cd frontend
npm install

# 8. 启动前端服务
npm run dev
```

### 访问应用

- 前端地址：http://localhost:3000
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/swagger/

---

## 📖 文档

- [安装指南](docs/installation.md)
- [使用教程](docs/tutorial.md)
- [API文档](docs/api.md)
- [开发指南](docs/development.md)
- [常见问题](docs/faq.md)

---

## 🛠️ 配置说明

### AI配置

在 `.env` 文件中配置AI服务：

```bash
# OpenAI配置
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4

# 或使用本地模型
LOCAL_LLM_ENDPOINT=http://localhost:11434
LOCAL_LLM_MODEL=llama2
```

### 数据库配置

```bash
DB_NAME=xrun
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

---

## 🗓️ 更新日志

### V2.0.0 (2025-01-01) - 重大升级
- 🎉 项目完全重构，升级为AI驱动平台
- 🔄 项目重命名为 XRun
- ✨ 新增AI UI自动化测试功能
- ✨ 新增AI功能自动化测试
- 🔄 重构接口自动化，增加AI能力
- 🎨 全新的现代化界面
- 📚 完善的文档体系

### V1.x (2022-2024) - 传统API测试平台
- 查看 [V1迁移文档](MIGRATION_V2.md)

---

## 🤝 贡献指南

欢迎贡献！请查看 [贡献指南](CONTRIBUTING.md)

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

## 👥 联系我们

- 作者：[@wangxiaoqi-maker](https://github.com/wangxiaoqi-maker)
- 项目地址：[GitHub](https://github.com/wangxiaoqi-maker/XRun)
- 问题反馈：[Issues](https://github.com/wangxiaoqi-maker/XRun/issues)

---

## ⭐ Star History

如果这个项目对你有帮助，请给个 Star ⭐️

---

<div align="center">

**[⬆ 回到顶部](#-xrun---ai驱动的一站式自动化测试平台)**

Made with ❤️ by wangxiaoqi-maker

</div>
