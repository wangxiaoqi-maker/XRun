"""
AI 教学模式 - 知识库模块

该模块实现 App 页面元素知识库的构建和管理，包括：
- 页面截图分析（调用视觉大模型）
- 元素信息存储（MySQL 关系型数据库）
- 向量检索（Milvus 向量数据库）

设计模式：
- 策略模式：Embedding 提供商抽象
- 工厂模式：创建 Embedding 实例
- Repository 模式：数据访问层抽象
- 门面模式：KnowledgeService 统一接口
"""

__version__ = "1.0.0"
