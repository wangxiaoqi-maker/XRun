"""
知识库服务层

包含：
- EmbeddingService: 文本向量化服务（策略模式）
- VectorService: 向量数据库服务（Milvus）
- PageAnalyzerService: 页面分析服务（调用视觉大模型）
- KnowledgeService: 知识库门面服务（Facade 模式）
"""
from .embedding_service import (
    BaseEmbeddingProvider,
    OpenAIEmbeddingProvider,
    DashScopeEmbeddingProvider,
    EmbeddingProviderFactory,
    EmbeddingService,
)
from .vector_service import VectorService
from .page_analyzer_service import PageAnalyzerService
from .knowledge_service import KnowledgeService

__all__ = [
    "BaseEmbeddingProvider",
    "OpenAIEmbeddingProvider", 
    "DashScopeEmbeddingProvider",
    "EmbeddingProviderFactory",
    "EmbeddingService",
    "VectorService",
    "PageAnalyzerService",
    "KnowledgeService",
]
