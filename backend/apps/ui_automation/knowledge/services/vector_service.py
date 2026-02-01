"""
向量数据库服务 - Milvus

提供：
- Collection 管理
- 向量插入/删除
- 语义搜索
"""
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger

from ..config import MilvusConfig, EmbeddingConfig, get_milvus_config, get_embedding_config
from .embedding_service import EmbeddingService


class VectorService:
    """
    向量数据库服务 - 基于 Milvus
    
    职责：
    - 管理 Milvus Collection
    - 提供向量的 CRUD 操作
    - 支持语义搜索（带过滤条件）
    """
    
    _instance: Optional['VectorService'] = None
    
    def __init__(
        self,
        milvus_config: Optional[MilvusConfig] = None,
        embedding_config: Optional[EmbeddingConfig] = None
    ):
        self.milvus_config = milvus_config or get_milvus_config()
        self.embedding_config = embedding_config or get_embedding_config()
        
        self._client = None
        self._embedding_service = None
        self._initialized = False
    
    @classmethod
    def get_instance(
        cls,
        milvus_config: Optional[MilvusConfig] = None,
        embedding_config: Optional[EmbeddingConfig] = None
    ) -> 'VectorService':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls(milvus_config, embedding_config)
        return cls._instance
    
    async def initialize(self) -> None:
        """初始化服务"""
        if self._initialized:
            return
        
        try:
            from pymilvus import MilvusClient
            
            # 初始化 Milvus 客户端
            self._client = MilvusClient(
                uri=self.milvus_config.MILVUS_URI,
                token=self.milvus_config.MILVUS_TOKEN,
                timeout=self.milvus_config.MILVUS_TIMEOUT
            )
            
            # 初始化 Embedding 服务
            self._embedding_service = EmbeddingService.get_instance(self.embedding_config)
            await self._embedding_service.initialize()
            
            # 确保 Collection 存在
            await self._ensure_collection()
            
            self._initialized = True
            logger.info(f"✅ VectorService 初始化成功: {self.milvus_config.MILVUS_COLLECTION}")
        except Exception as e:
            logger.error(f"❌ VectorService 初始化失败: {e}")
            raise
    
    async def _ensure_collection(self) -> None:
        """确保 Collection 存在，不存在则创建"""
        from pymilvus import DataType
        
        collection_name = self.milvus_config.MILVUS_COLLECTION
        
        # 在线程池中运行同步操作
        loop = asyncio.get_event_loop()
        has_collection = await loop.run_in_executor(
            None, 
            self._client.has_collection, 
            collection_name
        )
        
        if has_collection:
            logger.debug(f"Collection '{collection_name}' 已存在")
            return
        
        # 创建 Schema
        schema = self._client.create_schema(
            auto_id=False,
            enable_dynamic_field=True  # 支持动态字段扩展
        )
        
        # 主键
        schema.add_field(
            field_name="id",
            datatype=DataType.VARCHAR,
            max_length=36,
            is_primary=True
        )
        
        # 向量字段
        schema.add_field(
            field_name="embedding",
            datatype=DataType.FLOAT_VECTOR,
            dim=self.embedding_config.EMBEDDING_DIMENSION
        )
        
        # 核心字段
        schema.add_field(field_name="description", datatype=DataType.VARCHAR, max_length=2000)
        schema.add_field(field_name="app_name", datatype=DataType.VARCHAR, max_length=100)
        schema.add_field(field_name="page_id", datatype=DataType.VARCHAR, max_length=36)
        schema.add_field(field_name="page_name", datatype=DataType.VARCHAR, max_length=200)
        schema.add_field(field_name="page_type", datatype=DataType.VARCHAR, max_length=50)
        schema.add_field(field_name="element_name", datatype=DataType.VARCHAR, max_length=200)
        schema.add_field(field_name="element_type", datatype=DataType.VARCHAR, max_length=50)
        schema.add_field(field_name="platform", datatype=DataType.VARCHAR, max_length=20)
        schema.add_field(field_name="is_testable", datatype=DataType.BOOL)
        schema.add_field(field_name="test_priority", datatype=DataType.VARCHAR, max_length=20)
        
        # 创建索引
        index_params = self._client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type=self.milvus_config.MILVUS_INDEX_TYPE,
            metric_type=self.milvus_config.MILVUS_METRIC_TYPE
        )
        # 标量索引
        index_params.add_index(field_name="app_name", index_type="AUTOINDEX")
        index_params.add_index(field_name="element_type", index_type="AUTOINDEX")
        index_params.add_index(field_name="page_type", index_type="AUTOINDEX")
        
        # 创建 Collection
        await loop.run_in_executor(
            None,
            lambda: self._client.create_collection(
                collection_name=collection_name,
                schema=schema,
                index_params=index_params
            )
        )
        
        logger.info(f"✅ 创建 Milvus Collection: {collection_name}")
    
    async def add_element(
        self,
        element_id: str,
        description: str,
        metadata: Dict[str, Any]
    ) -> None:
        """
        添加单个元素到向量库
        
        Args:
            element_id: 元素 ID
            description: 用于生成向量的描述文本
            metadata: 元数据（app_name, page_name, element_type 等）
        """
        await self.initialize()
        
        try:
            # 生成向量
            embedding = await self._embedding_service.embed(description)
            
            # 构建数据
            data = {
                "id": element_id,
                "embedding": embedding,
                "description": description[:2000],  # 限制长度
                **metadata
            }
            
            # 插入
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._client.insert(
                    collection_name=self.milvus_config.MILVUS_COLLECTION,
                    data=[data]
                )
            )
            
            logger.debug(f"添加元素到向量库: {element_id}")
        except Exception as e:
            logger.error(f"添加元素失败: {e}")
            raise
    
    async def add_elements_batch(self, elements: List[Dict[str, Any]]) -> int:
        """
        批量添加元素到向量库
        
        Args:
            elements: 元素列表，每个元素包含 id, description, metadata
            
        Returns:
            成功添加的数量
        """
        await self.initialize()
        
        if not elements:
            return 0
        
        try:
            # 提取描述文本
            descriptions = [e["description"] for e in elements]
            
            # 批量生成向量
            embeddings = await self._embedding_service.embed_batch(descriptions)
            
            # 构建数据
            data = []
            for i, element in enumerate(elements):
                item = {
                    "id": element["id"],
                    "embedding": embeddings[i],
                    "description": element["description"][:2000],
                    **element.get("metadata", {})
                }
                data.append(item)
            
            # 批量插入
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._client.insert(
                    collection_name=self.milvus_config.MILVUS_COLLECTION,
                    data=data
                )
            )
            
            logger.info(f"批量添加 {len(data)} 个元素到向量库")
            return len(data)
        except Exception as e:
            logger.error(f"批量添加元素失败: {e}")
            raise
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_expr: Optional[str] = None,
        output_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        语义搜索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            filter_expr: 过滤表达式，如 'app_name == "微信" and element_type == "button"'
            output_fields: 需要返回的字段列表
            
        Returns:
            匹配结果列表，每个元素包含 id, description, similarity_score 等
        """
        await self.initialize()
        
        try:
            # 生成查询向量
            query_embedding = await self._embedding_service.embed(query)
            
            # 默认返回字段
            if output_fields is None:
                output_fields = [
                    "id", "description", "app_name", "page_name", "page_type",
                    "element_name", "element_type", "platform", "is_testable", "test_priority"
                ]
            
            # 搜索
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self._client.search(
                    collection_name=self.milvus_config.MILVUS_COLLECTION,
                    data=[query_embedding],
                    limit=top_k,
                    filter=filter_expr,
                    output_fields=output_fields
                )
            )
            
            # 处理结果
            matches = []
            for hit in results[0]:
                match = {
                    "id": hit["id"],
                    "similarity_score": hit["distance"],  # COSINE 返回的是相似度
                }
                # 添加其他字段
                for field in output_fields:
                    if field != "id" and field in hit.get("entity", {}):
                        match[field] = hit["entity"][field]
                matches.append(match)
            
            return matches
        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            raise
    
    async def delete_by_page(self, page_id: str) -> None:
        """
        删除页面的所有元素向量
        
        Args:
            page_id: 页面 ID
        """
        await self.initialize()
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._client.delete(
                    collection_name=self.milvus_config.MILVUS_COLLECTION,
                    filter=f'page_id == "{page_id}"'
                )
            )
            logger.info(f"删除页面向量: {page_id}")
        except Exception as e:
            logger.error(f"删除页面向量失败: {e}")
            raise
    
    async def delete_element(self, element_id: str) -> None:
        """
        删除单个元素向量
        
        Args:
            element_id: 元素 ID
        """
        await self.delete_by_ids([element_id])
    
    async def delete_by_ids(self, ids: List[str]) -> None:
        """
        按 ID 批量删除元素
        
        Args:
            ids: 元素 ID 列表
        """
        await self.initialize()
        
        if not ids:
            return
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._client.delete(
                    collection_name=self.milvus_config.MILVUS_COLLECTION,
                    ids=ids
                )
            )
            logger.info(f"删除 {len(ids)} 个元素向量")
        except Exception as e:
            logger.error(f"批量删除元素失败: {e}")
            raise
    
    async def delete_by_app(self, app_name: str) -> None:
        """
        删除应用的所有元素向量
        
        Args:
            app_name: 应用名称
        """
        await self.initialize()
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._client.delete(
                    collection_name=self.milvus_config.MILVUS_COLLECTION,
                    filter=f'app_name == "{app_name}"'
                )
            )
            logger.info(f"删除应用向量: {app_name}")
        except Exception as e:
            logger.error(f"删除应用向量失败: {e}")
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取向量库统计信息
        
        Returns:
            统计信息字典
        """
        await self.initialize()
        
        try:
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(
                None,
                lambda: self._client.get_collection_stats(
                    collection_name=self.milvus_config.MILVUS_COLLECTION
                )
            )
            return {
                "collection_name": self.milvus_config.MILVUS_COLLECTION,
                "row_count": stats.get("row_count", 0),
                "dimension": self.embedding_config.EMBEDDING_DIMENSION,
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "collection_name": self.milvus_config.MILVUS_COLLECTION,
                "row_count": 0,
                "error": str(e)
            }
