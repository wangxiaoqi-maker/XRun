"""
知识库模型基类

与主应用共享数据库连接，使用独立的 Base 便于模块化管理
"""
from sqlalchemy.orm import declarative_base

# 知识库模型基类
# 注意：与主应用的 Base 区分，但共享同一个数据库
KnowledgeBase = declarative_base()
