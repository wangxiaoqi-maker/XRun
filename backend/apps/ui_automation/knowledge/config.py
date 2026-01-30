"""
知识库模块配置

支持通过环境变量或 .env 文件配置：
- Embedding 模型（OpenAI / DashScope / 本地模型）
- Milvus 向量数据库连接
"""
from pydantic_settings import BaseSettings
from typing import Optional, Literal
from functools import lru_cache


class EmbeddingConfig(BaseSettings):
    """Embedding 模型配置 - 支持多种模型切换"""
    
    # Embedding 提供商：openai / dashscope / local
    EMBEDDING_PROVIDER: Literal["openai", "dashscope", "local"] = "openai"
    
    # 模型名称
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # 向量维度（需与模型匹配）
    # text-embedding-3-small: 1536
    # text-embedding-3-large: 3072
    # text-embedding-v3 (dashscope): 1024
    # bge-base-zh-v1.5: 768
    EMBEDDING_DIMENSION: int = 1536
    
    # API 配置（从环境变量读取）
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_BASE_URL: Optional[str] = None
    
    # 批量处理配置
    EMBEDDING_BATCH_SIZE: int = 20  # 单批最大文本数
    EMBEDDING_MAX_RETRIES: int = 3  # 最大重试次数
    EMBEDDING_RETRY_DELAY: float = 1.0  # 重试间隔（秒）
    
    class Config:
        env_prefix = ""
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class MilvusConfig(BaseSettings):
    """Milvus 向量数据库配置"""
    
    # Milvus 连接配置
    MILVUS_URI: str = "http://localhost:19530"
    MILVUS_TOKEN: str = "root:Milvus"
    MILVUS_DATABASE: str = "xrun_knowledge"
    MILVUS_COLLECTION: str = "page_elements"
    
    # 连接配置
    MILVUS_TIMEOUT: float = 30.0  # 连接超时（秒）
    MILVUS_POOL_SIZE: int = 10    # 连接池大小
    
    # 索引配置
    MILVUS_INDEX_TYPE: str = "AUTOINDEX"
    MILVUS_METRIC_TYPE: str = "COSINE"  # 余弦相似度
    
    class Config:
        env_prefix = ""
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class AnalyzerConfig(BaseSettings):
    """页面分析器配置"""
    
    # 视觉模型选择
    ANALYZER_VISION_MODEL: str = "qwenvl"  # qwenvl / gpt4v
    
    # 分析配置
    ANALYZER_CONFIDENCE_THRESHOLD: float = 0.6  # 元素置信度阈值
    ANALYZER_MAX_ELEMENTS: int = 50  # 单页面最大元素数
    ANALYZER_TIMEOUT: float = 60.0   # 分析超时（秒）
    
    # 去重配置
    ANALYZER_DEDUP_ENABLED: bool = True  # 启用截图去重
    
    class Config:
        env_prefix = ""
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_embedding_config() -> EmbeddingConfig:
    """获取 Embedding 配置（单例）"""
    return EmbeddingConfig()


@lru_cache()
def get_milvus_config() -> MilvusConfig:
    """获取 Milvus 配置（单例）"""
    return MilvusConfig()


@lru_cache()
def get_analyzer_config() -> AnalyzerConfig:
    """获取分析器配置（单例）"""
    return AnalyzerConfig()
