"""
Embedding 服务 - 文本向量化

设计模式：
- 策略模式（Strategy Pattern）：抽象 Embedding 提供商接口，支持多种实现
- 工厂模式（Factory Pattern）：根据配置创建具体的提供商实例

支持的 Embedding 提供商：
- OpenAI: text-embedding-3-small / text-embedding-3-large / text-embedding-ada-002
- DashScope: text-embedding-v3（通义千问）
- Local: 本地模型（预留接口）
"""
import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Type
from loguru import logger

from ..config import EmbeddingConfig, get_embedding_config


class BaseEmbeddingProvider(ABC):
    """
    Embedding 提供商基类（策略模式 - Strategy）
    
    所有 Embedding 提供商必须实现此接口
    """
    
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化提供商（延迟初始化）"""
        pass
    
    @abstractmethod
    async def generate(self, text: str) -> List[float]:
        """
        生成单个文本的向量
        
        Args:
            text: 输入文本
            
        Returns:
            向量列表（维度由配置决定）
        """
        pass
    
    @abstractmethod
    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成文本向量
        
        Args:
            texts: 输入文本列表
            
        Returns:
            向量列表的列表
        """
        pass
    
    @property
    def dimension(self) -> int:
        """获取向量维度"""
        return self.config.EMBEDDING_DIMENSION
    
    @property
    def model_name(self) -> str:
        """获取模型名称"""
        return self.config.EMBEDDING_MODEL


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenAI Embedding 提供商
    
    支持模型：
    - text-embedding-3-small (1536 维)
    - text-embedding-3-large (3072 维)
    - text-embedding-ada-002 (1536 维)
    """
    
    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        self._client = None
    
    async def initialize(self) -> None:
        """初始化 OpenAI 客户端"""
        if self._initialized:
            return
        
        try:
            from openai import AsyncOpenAI
            
            self._client = AsyncOpenAI(
                api_key=self.config.EMBEDDING_API_KEY,
                base_url=self.config.EMBEDDING_BASE_URL,
                timeout=30.0
            )
            self._initialized = True
            logger.info(f"✅ OpenAI Embedding 初始化成功: {self.model_name}")
        except Exception as e:
            logger.error(f"❌ OpenAI Embedding 初始化失败: {e}")
            raise
    
    async def generate(self, text: str) -> List[float]:
        """生成单个文本向量"""
        if not self._initialized:
            await self.initialize()
        
        try:
            response = await self._client.embeddings.create(
                model=self.model_name,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI Embedding 生成失败: {e}")
            raise
    
    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本向量"""
        if not self._initialized:
            await self.initialize()
        
        if not texts:
            return []
        
        try:
            # OpenAI API 支持批量请求
            response = await self._client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            # 按照输入顺序返回
            return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
        except Exception as e:
            logger.error(f"OpenAI Embedding 批量生成失败: {e}")
            raise


class DashScopeEmbeddingProvider(BaseEmbeddingProvider):
    """
    通义千问 Embedding 提供商（DashScope）
    
    支持模型：
    - text-embedding-v3 (1024 维)
    - text-embedding-v2 (1536 维)
    """
    
    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
    
    async def initialize(self) -> None:
        """初始化 DashScope"""
        if self._initialized:
            return
        
        try:
            import dashscope
            dashscope.api_key = self.config.EMBEDDING_API_KEY
            self._initialized = True
            logger.info(f"✅ DashScope Embedding 初始化成功: {self.model_name}")
        except Exception as e:
            logger.error(f"❌ DashScope Embedding 初始化失败: {e}")
            raise
    
    async def generate(self, text: str) -> List[float]:
        """生成单个文本向量"""
        if not self._initialized:
            await self.initialize()
        
        try:
            from dashscope import TextEmbedding
            
            # DashScope 的 API 是同步的，需要在线程池中运行
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: TextEmbedding.call(
                    model=self.model_name,
                    input=text
                )
            )
            
            if response.status_code != 200:
                raise Exception(f"DashScope API 错误: {response.message}")
            
            return response.output['embeddings'][0]['embedding']
        except Exception as e:
            logger.error(f"DashScope Embedding 生成失败: {e}")
            raise
    
    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本向量"""
        if not self._initialized:
            await self.initialize()
        
        if not texts:
            return []
        
        try:
            from dashscope import TextEmbedding
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: TextEmbedding.call(
                    model=self.model_name,
                    input=texts
                )
            )
            
            if response.status_code != 200:
                raise Exception(f"DashScope API 错误: {response.message}")
            
            # DashScope 按顺序返回
            return [item['embedding'] for item in response.output['embeddings']]
        except Exception as e:
            logger.error(f"DashScope Embedding 批量生成失败: {e}")
            raise


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """
    本地 Embedding 提供商（预留接口）
    
    可用于部署本地模型如：
    - BGE-base-zh-v1.5
    - M3E
    - Sentence-Transformers
    """
    
    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        self._model = None
    
    async def initialize(self) -> None:
        """初始化本地模型"""
        if self._initialized:
            return
        
        # 预留：加载本地模型
        logger.warning("⚠️ 本地 Embedding 模型暂未实现")
        self._initialized = True
    
    async def generate(self, text: str) -> List[float]:
        """生成单个文本向量"""
        raise NotImplementedError("本地 Embedding 模型暂未实现")
    
    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本向量"""
        raise NotImplementedError("本地 Embedding 模型暂未实现")


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """
    Ollama 本地 Embedding 提供商
    
    支持模型：
    - nomic-embed-text (768 维) - 轻量快速，推荐
    - mxbai-embed-large (1024 维)
    - bge-m3 (1024 维) - 中文效果最佳
    - snowflake-arctic-embed (1024 维)
    
    使用前需要：
    1. 安装 Ollama: brew install ollama
    2. 启动服务: ollama serve
    3. 拉取模型: ollama pull nomic-embed-text
    """
    
    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        self._base_url = config.EMBEDDING_BASE_URL or "http://localhost:11434"
    
    async def initialize(self) -> None:
        """初始化 Ollama 连接"""
        if self._initialized:
            return
        
        try:
            import httpx
            
            # 测试连接
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                if response.status_code != 200:
                    raise Exception(f"Ollama 服务未启动或无法连接: {response.status_code}")
                
                # 检查模型是否已安装
                models = response.json().get("models", [])
                model_names = [m.get("name", "").split(":")[0] for m in models]
                
                if self.model_name not in model_names and f"{self.model_name}:latest" not in [m.get("name") for m in models]:
                    logger.warning(f"⚠️ 模型 {self.model_name} 未安装，请运行: ollama pull {self.model_name}")
            
            self._initialized = True
            logger.info(f"✅ Ollama Embedding 初始化成功: {self.model_name} @ {self._base_url}")
        except ImportError:
            raise ImportError("请安装 httpx: pip install httpx")
        except Exception as e:
            logger.error(f"❌ Ollama Embedding 初始化失败: {e}")
            raise
    
    async def generate(self, text: str) -> List[float]:
        """生成单个文本向量"""
        if not self._initialized:
            await self.initialize()
        
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self._base_url}/api/embeddings",
                    json={
                        "model": self.model_name,
                        "prompt": text
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"Ollama API 错误: {response.status_code} - {response.text}")
                
                result = response.json()
                embedding = result.get("embedding", [])
                
                if not embedding:
                    raise Exception("Ollama 返回空向量")
                
                return embedding
                
        except Exception as e:
            logger.error(f"Ollama Embedding 生成失败: {e}")
            raise
    
    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本向量（Ollama 不支持批量，逐个处理）"""
        if not self._initialized:
            await self.initialize()
        
        if not texts:
            return []
        
        results = []
        for text in texts:
            embedding = await self.generate(text)
            results.append(embedding)
        
        return results


class EmbeddingProviderFactory:
    """
    Embedding 提供商工厂（工厂模式 - Factory）
    
    根据配置创建具体的 Embedding 提供商实例
    """
    
    _providers: Dict[str, Type[BaseEmbeddingProvider]] = {
        "openai": OpenAIEmbeddingProvider,
        "dashscope": DashScopeEmbeddingProvider,
        "local": LocalEmbeddingProvider,
        "ollama": OllamaEmbeddingProvider,
    }
    
    @classmethod
    def create(cls, config: Optional[EmbeddingConfig] = None) -> BaseEmbeddingProvider:
        """
        创建 Embedding 提供商实例
        
        Args:
            config: Embedding 配置，默认使用全局配置
            
        Returns:
            Embedding 提供商实例
            
        Raises:
            ValueError: 不支持的提供商类型
        """
        config = config or get_embedding_config()
        provider_name = config.EMBEDDING_PROVIDER.lower()
        
        if provider_name not in cls._providers:
            raise ValueError(
                f"不支持的 Embedding 提供商: {provider_name}，"
                f"可选: {list(cls._providers.keys())}"
            )
        
        provider_class = cls._providers[provider_name]
        return provider_class(config)
    
    @classmethod
    def register(cls, name: str, provider_class: Type[BaseEmbeddingProvider]) -> None:
        """
        注册自定义提供商
        
        Args:
            name: 提供商名称
            provider_class: 提供商类
        """
        cls._providers[name.lower()] = provider_class
        logger.info(f"注册 Embedding 提供商: {name}")
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """列出所有可用的提供商"""
        return list(cls._providers.keys())


class EmbeddingService:
    """
    Embedding 服务 - 高层封装
    
    提供：
    - 自动重试机制
    - 批量处理优化
    - 缓存支持（可选）
    """
    
    _instance: Optional['EmbeddingService'] = None
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or get_embedding_config()
        self._provider = EmbeddingProviderFactory.create(self.config)
        self._initialized = False
    
    @classmethod
    def get_instance(cls, config: Optional[EmbeddingConfig] = None) -> 'EmbeddingService':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance
    
    async def initialize(self) -> None:
        """初始化服务"""
        if self._initialized:
            return
        await self._provider.initialize()
        self._initialized = True
    
    @property
    def dimension(self) -> int:
        """获取向量维度"""
        return self._provider.dimension
    
    async def embed(self, text: str) -> List[float]:
        """
        生成单个文本的向量
        
        支持自动重试
        """
        await self.initialize()
        
        for attempt in range(self.config.EMBEDDING_MAX_RETRIES):
            try:
                return await self._provider.generate(text)
            except Exception as e:
                if attempt < self.config.EMBEDDING_MAX_RETRIES - 1:
                    logger.warning(f"Embedding 生成失败，重试 {attempt + 1}/{self.config.EMBEDDING_MAX_RETRIES}: {e}")
                    await asyncio.sleep(self.config.EMBEDDING_RETRY_DELAY * (attempt + 1))
                else:
                    raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成文本向量
        
        自动分批处理，避免单次请求过大
        """
        await self.initialize()
        
        if not texts:
            return []
        
        results = []
        batch_size = self.config.EMBEDDING_BATCH_SIZE
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            for attempt in range(self.config.EMBEDDING_MAX_RETRIES):
                try:
                    batch_results = await self._provider.generate_batch(batch)
                    results.extend(batch_results)
                    break
                except Exception as e:
                    if attempt < self.config.EMBEDDING_MAX_RETRIES - 1:
                        logger.warning(f"Embedding 批量生成失败，重试 {attempt + 1}: {e}")
                        await asyncio.sleep(self.config.EMBEDDING_RETRY_DELAY * (attempt + 1))
                    else:
                        raise
        
        return results
    
    async def embed_with_metadata(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成向量并附带元数据
        
        Args:
            text: 输入文本
            metadata: 元数据
            
        Returns:
            包含向量和元数据的字典
        """
        embedding = await self.embed(text)
        return {
            "text": text,
            "embedding": embedding,
            "metadata": metadata
        }
