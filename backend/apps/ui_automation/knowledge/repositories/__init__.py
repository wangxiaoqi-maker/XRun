"""
知识库数据访问层（Repository Pattern）

提供数据库操作的抽象，解耦业务逻辑和数据访问
"""
from .base import BaseRepository
from .app_repository import AppRepository
from .page_repository import PageRepository
from .element_repository import ElementRepository

__all__ = [
    "BaseRepository",
    "AppRepository",
    "PageRepository",
    "ElementRepository",
]
