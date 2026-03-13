"""TextChunker — 文本分块 + 用例格式化"""
import re
import uuid


class TextChunker:
    def __init__(self, chunk_size: int = 800, overlap: int = 100):
        self._chunk_size = chunk_size
        self._overlap = overlap

    def chunk_document(self, text: str, file_id: str) -> list[dict]:
        """按标题分割，超长段落二次切分"""
        if not text or not text.strip():
            return []

        sections = re.split(r'\n(?=#{1,3}\s)', text)
        chunks = []
        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue

            title_match = re.match(r'^(#{1,3})\s+(.+)', sec)
            section_name = title_match.group(2).strip()[:200] if title_match else ""

            if len(sec) <= self._chunk_size:
                chunks.append(self._make_chunk(sec, file_id, section_name, len(chunks)))
            else:
                sub_chunks = self._split_long_text(sec)
                for sub in sub_chunks:
                    chunks.append(self._make_chunk(sub, file_id, section_name, len(chunks)))

        if not chunks and text.strip():
            for sub in self._split_long_text(text):
                chunks.append(self._make_chunk(sub, file_id, "", len(chunks)))

        return chunks

    def _split_long_text(self, text: str) -> list[str]:
        paragraphs = re.split(r'\n{2,}', text)
        results = []
        current = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current) + len(para) + 2 <= self._chunk_size:
                current = f"{current}\n\n{para}" if current else para
            else:
                if current:
                    results.append(current)
                if len(para) > self._chunk_size:
                    for i in range(0, len(para), self._chunk_size - self._overlap):
                        results.append(para[i:i + self._chunk_size])
                else:
                    current = para
                    continue
                current = ""

        if current:
            results.append(current)
        return results or [text[:self._chunk_size]]

    @staticmethod
    def _make_chunk(text: str, file_id: str, section: str, index: int) -> dict:
        return {
            "id": str(uuid.uuid4()),
            "content": text,
            "source_type": "doc_chunk",
            "file_id": file_id,
            "case_id": "",
            "section": section,
            "module_name": "",
            "chunk_index": index,
        }

    @staticmethod
    def format_test_case(case: dict) -> dict:
        """将测试用例格式化为可检索文本"""
        parts = []
        priority = case.get("priority", "P1")
        test_type = case.get("test_type", "功能")
        name = case.get("name", "")
        parts.append(f"[{priority}][{test_type}] {name}")

        if case.get("preconditions"):
            parts.append(f"前置条件: {case['preconditions']}")

        steps = case.get("test_steps") or case.get("steps") or []
        if isinstance(steps, list):
            for i, s in enumerate(steps, 1):
                if isinstance(s, dict):
                    action = s.get("action", "")
                    expected = s.get("expected", "")
                    parts.append(f"步骤{i}: {action}")
                    if expected:
                        parts.append(f"预期{i}: {expected}")
                elif isinstance(s, str):
                    parts.append(f"步骤{i}: {s}")

        module = case.get("module_name", "")
        return {
            "id": str(uuid.uuid4()),
            "content": "\n".join(parts),
            "source_type": "test_case",
            "file_id": "",
            "case_id": case.get("id", ""),
            "section": "",
            "module_name": module,
            "chunk_index": 0,
        }
