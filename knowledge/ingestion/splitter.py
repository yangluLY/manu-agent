import sys
from pathlib import Path

# 获取项目根目录（scripts的上一级）
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from dataclasses import dataclass, field
from typing import Any

from knowledge.ingestion.loaders import LoadedDocument

DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 100


@dataclass
class DocumentChunk:
    """
    文档切片后的统一数据结构。

    content:
        当前 Chunk 的文本内容。

    metadata:
        保存来源文件、分类、chunk_index 等信息。
    """

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class TextSplitter:
    """
    知识库文本切分器。

    第一版采用字符长度切分，同时尽量优先在：
    - 段落
    - 换行
    - 中文句号
    - 感叹号
    - 问号
    - 分号

    等自然边界处进行切分。
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_document(
        self,
        document: LoadedDocument,
    ) -> list[DocumentChunk]:
        """
        切分单个 LoadedDocument。
        """

        text_chunks = self.split_text(document.content)

        chunks: list[DocumentChunk] = []

        for index, content in enumerate(text_chunks):
            metadata = document.metadata.copy()

            metadata.update(
                {
                    "chunk_index": index,
                    "chunk_length": len(content),
                }
            )

            chunks.append(
                DocumentChunk(
                    content=content,
                    metadata=metadata,
                )
            )

        return chunks

    def split_documents(
        self,
        documents: list[LoadedDocument],
    ) -> list[DocumentChunk]:
        """
        批量切分多个文档。
        """

        all_chunks: list[DocumentChunk] = []

        for document in documents:
            chunks = self.split_document(document)
            all_chunks.extend(chunks)

        return all_chunks

    def split_text(
        self,
        text: str,
    ) -> list[str]:
        """
        将文本切分为多个 Chunk。
        """

        text = self._normalize_text(text)

        if not text:
            return []

        if len(text) <= self.chunk_size:
            return [text]

        chunks: list[str] = []

        start = 0
        text_length = len(text)

        while start < text_length:
            max_end = min(
                start + self.chunk_size,
                text_length,
            )

            # 已经是最后一段
            if max_end >= text_length:
                chunk = text[start:text_length].strip()

                if chunk:
                    chunks.append(chunk)

                break

            split_end = self._find_split_position(
                text=text,
                start=start,
                max_end=max_end,
            )

            chunk = text[start:split_end].strip()

            if chunk:
                chunks.append(chunk)

            # 下一个 Chunk 向前保留 overlap
            next_start = split_end - self.chunk_overlap

            # 防止异常情况下死循环
            if next_start <= start:
                next_start = split_end

            start = next_start

        return chunks

    def _find_split_position(
        self,
        text: str,
        start: int,
        max_end: int,
    ) -> int:
        """
        在 chunk_size 范围内寻找更自然的切分位置。

        优先级：
        1. 段落
        2. 换行
        3. 中文句号
        4. 感叹号
        5. 问号
        6. 分号
        """

        separators = [
            "\n\n",
            "\n",
            "。",
            "！",
            "？",
            "；",
        ]

        # 防止为了寻找自然边界，把 Chunk 切得太短
        min_split_position = start + int(
            self.chunk_size * 0.5
        )

        for separator in separators:
            position = text.rfind(
                separator,
                min_split_position,
                max_end,
            )

            if position != -1:
                return position + len(separator)

        # 找不到自然边界时直接按字符长度切
        return max_end

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        对输入文本做最基础的清洗。
        """

        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        return text.strip()