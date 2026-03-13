"""TcgVectorStore — TCG 知识库向量存储，复用现有 Milvus + EmbeddingService"""
import asyncio
import uuid
from typing import Optional

from loguru import logger

_TCG_COLLECTION = "tcg_knowledge"


class TcgVectorStore:
    """单 Collection 设计，通过 project_id 字段隔离项目数据"""

    _instance: Optional["TcgVectorStore"] = None

    def __init__(self):
        self._client = None
        self._embedding = None
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "TcgVectorStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def initialize(self):
        if self._initialized:
            return
        try:
            from pymilvus import MilvusClient
            from apps.ui_automation.knowledge.config import get_milvus_config, get_embedding_config
            from apps.ui_automation.knowledge.services.embedding_service import EmbeddingService

            cfg = get_milvus_config()
            self._client = MilvusClient(uri=cfg.MILVUS_URI, token=cfg.MILVUS_TOKEN)
            self._embedding = EmbeddingService.get_instance(get_embedding_config())
            await self._embedding.initialize()
            await self._ensure_collection()
            self._initialized = True
            logger.info(f"TcgVectorStore 初始化成功: {_TCG_COLLECTION}")
        except Exception as e:
            logger.error(f"TcgVectorStore 初始化失败: {e}")
            raise

    async def _ensure_collection(self):
        from pymilvus import DataType

        has = await asyncio.to_thread(self._client.has_collection, _TCG_COLLECTION)
        if has:
            return

        schema = self._client.create_schema(auto_id=False, enable_dynamic_field=True)
        schema.add_field("id", DataType.VARCHAR, max_length=36, is_primary=True)
        schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=self._embedding.dimension)
        schema.add_field("content", DataType.VARCHAR, max_length=8000)
        schema.add_field("source_type", DataType.VARCHAR, max_length=20)
        schema.add_field("project_id", DataType.VARCHAR, max_length=36)
        schema.add_field("file_id", DataType.VARCHAR, max_length=36)
        schema.add_field("case_id", DataType.VARCHAR, max_length=36)
        schema.add_field("section", DataType.VARCHAR, max_length=200)
        schema.add_field("module_name", DataType.VARCHAR, max_length=200)
        schema.add_field("chunk_index", DataType.INT64)

        from apps.ui_automation.knowledge.config import get_milvus_config
        cfg = get_milvus_config()
        index_params = self._client.prepare_index_params()
        index_params.add_index("embedding", index_type=cfg.MILVUS_INDEX_TYPE, metric_type=cfg.MILVUS_METRIC_TYPE)
        index_params.add_index("project_id", index_type="AUTOINDEX")
        index_params.add_index("source_type", index_type="AUTOINDEX")

        await asyncio.to_thread(
            lambda: self._client.create_collection(
                collection_name=_TCG_COLLECTION, schema=schema, index_params=index_params
            )
        )
        logger.info(f"创建 Milvus Collection: {_TCG_COLLECTION}")

    async def add_batch(self, project_id: str, items: list[dict]) -> int:
        await self.initialize()
        if not items:
            return 0

        texts = [item["content"][:8000] for item in items]
        embeddings = await self._embedding.embed_batch(texts)

        data = []
        for item, emb in zip(items, embeddings):
            data.append({
                "id": item.get("id") or str(uuid.uuid4()),
                "embedding": emb,
                "content": item["content"][:8000],
                "source_type": item.get("source_type", "doc_chunk"),
                "project_id": project_id,
                "file_id": item.get("file_id", ""),
                "case_id": item.get("case_id", ""),
                "section": item.get("section", "")[:200],
                "module_name": item.get("module_name", "")[:200],
                "chunk_index": item.get("chunk_index", 0),
            })

        await asyncio.to_thread(
            lambda: self._client.insert(collection_name=_TCG_COLLECTION, data=data)
        )
        logger.info(f"知识库入库: {len(data)} 条 | project={project_id[:8]}")
        return len(data)

    async def search(
        self, project_id: str, query: str, top_k: int = 10, source_type: str = None,
    ) -> list[dict]:
        await self.initialize()

        query_emb = await self._embedding.embed(query)

        filter_parts = [f'project_id == "{project_id}"']
        if source_type:
            filter_parts.append(f'source_type == "{source_type}"')
        filter_expr = " and ".join(filter_parts)

        output_fields = ["id", "content", "source_type", "file_id", "case_id", "section", "module_name"]

        results = await asyncio.to_thread(
            lambda: self._client.search(
                collection_name=_TCG_COLLECTION,
                data=[query_emb],
                limit=top_k,
                filter=filter_expr,
                output_fields=output_fields,
            )
        )

        matches = []
        for hit in results[0]:
            match = {"id": hit["id"], "score": hit["distance"]}
            for field in output_fields:
                if field != "id" and field in hit.get("entity", {}):
                    match[field] = hit["entity"][field]
            matches.append(match)
        return matches

    async def delete_by_file(self, project_id: str, file_id: str):
        await self.initialize()
        await asyncio.to_thread(
            lambda: self._client.delete(
                collection_name=_TCG_COLLECTION,
                filter=f'project_id == "{project_id}" and file_id == "{file_id}"',
            )
        )
        logger.info(f"知识库删除: file={file_id[:8]} | project={project_id[:8]}")

    async def delete_by_project(self, project_id: str):
        await self.initialize()
        await asyncio.to_thread(
            lambda: self._client.delete(
                collection_name=_TCG_COLLECTION,
                filter=f'project_id == "{project_id}"',
            )
        )
        logger.info(f"知识库清空: project={project_id[:8]}")

    async def get_stats(self, project_id: str) -> dict:
        await self.initialize()
        try:
            doc_results = await asyncio.to_thread(
                lambda: self._client.query(
                    collection_name=_TCG_COLLECTION,
                    filter=f'project_id == "{project_id}" and source_type == "doc_chunk"',
                    output_fields=["id"],
                )
            )
            case_results = await asyncio.to_thread(
                lambda: self._client.query(
                    collection_name=_TCG_COLLECTION,
                    filter=f'project_id == "{project_id}" and source_type == "test_case"',
                    output_fields=["id"],
                )
            )
            return {
                "doc_chunks": len(doc_results),
                "case_vectors": len(case_results),
                "total": len(doc_results) + len(case_results),
            }
        except Exception as e:
            logger.warning(f"获取知识库统计失败: {e}")
            return {"doc_chunks": 0, "case_vectors": 0, "total": 0}
