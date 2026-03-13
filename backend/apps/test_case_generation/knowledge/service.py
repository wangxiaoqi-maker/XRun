"""KnowledgeService — 知识库入库/检索/管理"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from loguru import logger

from .tcg_vector import TcgVectorStore
from .chunker import TextChunker
from ..models import TcgKbDocumentChunk, TcgTestCase, TcgInputFile
from ..repositories.knowledge_repo import KnowledgeRepository


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._vector = TcgVectorStore.get_instance()
        self._chunker = TextChunker()
        self._kb_repo = KnowledgeRepository(db)

    async def index_document(self, project_id: str, file_id: str, parsed_content: str) -> int:
        """文档解析后入库（分块 → embedding → Milvus + DB 元数据）"""
        if not parsed_content or not parsed_content.strip():
            return 0

        chunks = self._chunker.chunk_document(parsed_content, file_id)
        if not chunks:
            return 0

        try:
            count = await self._vector.add_batch(project_id, chunks)

            db_chunks = [
                {
                    "project_id": project_id,
                    "file_id": file_id,
                    "chunk_text": c["content"][:5000],
                    "chunk_index": c["chunk_index"],
                    "section": c.get("section", ""),
                    "vector_id": c["id"],
                }
                for c in chunks
            ]
            await self._kb_repo.batch_create_chunks(db_chunks)

            logger.info(f"文档入库完成: {count} 个分块 | file={file_id[:8]} project={project_id[:8]}")
            return count
        except Exception as e:
            logger.error(f"文档入库失败: {e}")
            return 0

    async def index_test_cases(self, project_id: str, cases: list[dict]) -> int:
        """用例保存后入库"""
        if not cases:
            return 0

        items = [self._chunker.format_test_case(c) for c in cases]
        items = [item for item in items if item["content"].strip()]

        try:
            count = await self._vector.add_batch(project_id, items)
            logger.info(f"用例入库完成: {count} 条 | project={project_id[:8]}")
            return count
        except Exception as e:
            logger.error(f"用例入库失败: {e}")
            return 0

    async def search(self, project_id: str, query: str, top_k: int = 10) -> tuple[str, list[dict]]:
        """检索并格式化为 rag_context"""
        if not query or not query.strip():
            return "", []

        try:
            results = await self._vector.search(project_id, query, top_k)
            context = self._format_rag_context(results)
            return context, results
        except Exception as e:
            logger.error(f"知识库检索失败: {e}")
            return "", []

    async def remove_document(self, project_id: str, file_id: str):
        """删除文档相关的向量和 DB 元数据"""
        await self._vector.delete_by_file(project_id, file_id)
        await self._kb_repo.delete_by_file_id(file_id)

    async def rebuild_project(self, project_id: str) -> int:
        """清空并重建项目知识库"""
        await self._vector.delete_by_project(project_id)
        await self._kb_repo.clear_project(project_id)

        total = 0

        files = await self._db.execute(
            select(TcgInputFile).where(
                TcgInputFile.project_id == project_id,
                TcgInputFile.status == "parsed",
                TcgInputFile.parsed_content.isnot(None),
            )
        )
        for f in files.scalars().all():
            count = await self.index_document(project_id, f.id, f.parsed_content)
            total += count

        cases = await self._db.execute(
            select(TcgTestCase).where(TcgTestCase.project_id == project_id)
        )
        case_list = [
            {
                "id": c.id,
                "name": c.name,
                "priority": c.priority,
                "test_type": c.test_type,
                "preconditions": c.preconditions,
                "test_steps": c.test_steps,
                "module_name": c.module_name,
            }
            for c in cases.scalars().all()
        ]
        if case_list:
            total += await self.index_test_cases(project_id, case_list)

        logger.info(f"知识库重建完成: {total} 条向量 | project={project_id[:8]}")
        return total

    async def get_stats(self, project_id: str) -> dict:
        """获取知识库统计"""
        vector_stats = await self._vector.get_stats(project_id)
        db_stats = await self._kb_repo.get_stats(project_id)
        return {**vector_stats, "db_chunks": db_stats.get("chunk_count", 0)}

    @staticmethod
    def _format_rag_context(results: list[dict]) -> str:
        if not results:
            return ""

        doc_chunks = [r for r in results if r.get("source_type") == "doc_chunk"]
        case_chunks = [r for r in results if r.get("source_type") == "test_case"]

        parts = []

        if doc_chunks:
            parts.append("## 相关需求文档")
            for r in doc_chunks[:5]:
                section = r.get("section", "")
                tag = f"[来源: {section}]" if section else ""
                parts.append(f"{tag}\n{r.get('content', '')}\n")

        if case_chunks:
            parts.append(f"## 历史相似用例（共 {len(case_chunks)} 条）")
            for r in case_chunks[:5]:
                parts.append(r.get("content", ""))
            parts.append("\n请注意避免与历史用例重复，确保新用例覆盖不同的测试角度。")

        return "\n\n".join(parts)
