"""DocumentParserAgent — 文档解析 Agent"""
import os

from autogen_core import RoutedAgent, MessageContext, message_handler

from .mixin import TCGAgentMixin
from .messages import ParseDocumentRequest, AgentResponse
from ..core.logger import get_logger
from ..core.types import FileStatus
from ..services.document_parser import DocumentParserService
from ..repositories.file_repo import FileRepository

logger = get_logger("doc_parser")


def _append_image_descriptions(text: str, image_descriptions: list[dict]) -> str:
    if not image_descriptions:
        return text
    block = "\n\n## 图片内容分析\n"
    for img in image_descriptions:
        page_info = f"（第{img['page']}页）" if img.get("page") else ""
        block += f"- {page_info} {img['description']}\n"
    return text + block


def _build_doc_info(file_id: str, file_name: str, content: str, image_count: int = 0) -> dict:
    return {
        "file_id": file_id,
        "file_name": file_name,
        "content": content,
        "char_count": len(content),
        "image_count": image_count,
    }


class DocumentParserAgent(RoutedAgent, TCGAgentMixin):
    def __init__(self, llm_service, event_bridge, db):
        super().__init__("文档解析")
        self._init_tcg(llm_service, event_bridge, db)
        self._file_repo = FileRepository(db)
        self._parser = DocumentParserService()

    async def _process_file(
        self,
        file_id: str,
        file_record,
        vision_model_id: str | None,
        llm_svc,
        i: int,
        total: int,
    ) -> dict | None:
        file_name = file_record.file_name or "未知文件"
        file_path = file_record.file_path
        percent = int((i / total) * 100) if total else 0

        if not file_path or not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            msg = f"{file_name} 文件不存在或为空，跳过"
            await self.emit_progress(msg, percent=percent)
            await self._file_repo.update_status(
                file_id, FileStatus.ERROR.value, error_message=msg
            )
            return None

        if file_record.status == FileStatus.PARSED.value and file_record.parsed_content:
            await self.emit_progress(
                f"{file_name} 已有解析结果，跳过",
                percent=int(((i + 1) / total) * 100),
            )
            return _build_doc_info(file_id, file_name, file_record.parsed_content, 0)

        return await self._parse_and_save(
            file_id, file_name, file_path, vision_model_id, llm_svc, percent
        )

    async def _parse_and_save(
        self,
        file_id: str,
        file_name: str,
        file_path: str,
        vision_model_id: str | None,
        llm_svc,
        percent: int,
    ) -> dict | None:
        await self.emit_progress(f"正在解析: {file_name}", percent=percent)
        try:
            result = await self._parser.parse_file(
                file_path,
                vision_model_id=vision_model_id,
                llm_service=llm_svc,
            )
            content = _append_image_descriptions(
                result.text, result.image_descriptions
            )
            await self._file_repo.update_status(
                file_id, FileStatus.PARSED.value, parsed_content=content
            )
            return _build_doc_info(
                file_id, file_name, content, len(result.image_descriptions)
            )
        except Exception as e:
            logger.error(f"解析文件失败 {file_name}: {e}")
            await self._file_repo.update_status(
                file_id, FileStatus.ERROR.value, error_message=str(e)
            )
            await self.emit_progress(f"{file_name} 解析失败: {e}")
            return None

    @message_handler
    async def handle_parse_document(
        self, message: ParseDocumentRequest, ctx: MessageContext
    ) -> AgentResponse:
        if not message.file_ids:
            return AgentResponse(success=False, error="未提供文件 ID")

        parsed_docs = []
        total = len(message.file_ids)
        vision_model_id = message.vision_model_id or None
        llm_svc = self._llm_service if vision_model_id else None

        for i, file_id in enumerate(message.file_ids):
            file_record = await self._file_repo.get_by_id(file_id)
            if not file_record:
                percent = int((i / total) * 100) if total else 0
                await self.emit_progress(f"文件 {file_id} 不存在，跳过", percent=percent)
                continue

            doc_info = await self._process_file(
                file_id, file_record, vision_model_id, llm_svc, i, total
            )
            if doc_info:
                parsed_docs.append(doc_info)

        if not parsed_docs:
            return AgentResponse(success=False, error="没有成功解析的文档")

        return AgentResponse(
            success=True,
            data={
                "parsed_documents": parsed_docs,
                "parsed_count": len(parsed_docs),
                "total_chars": sum(d["char_count"] for d in parsed_docs),
            },
        )
