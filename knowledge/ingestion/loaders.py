from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pypdf import PdfReader

SUPPORTED_FILE_TYPES = {".txt", ".md", ".pdf"}


@dataclass
class LoadedDocument:
    """
    Loader 读取后的统一文档结构。
    """

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentLoader:
    """
    企业知识文档加载器。

    当前支持：
    - TXT
    - Markdown
    - PDF
    """

    def load_file(self, file_path: str | Path) -> LoadedDocument:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Document not found: {path}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        suffix = path.suffix.lower()

        if suffix not in SUPPORTED_FILE_TYPES:
            raise ValueError(
                f"Unsupported file type: {suffix}. "
                f"Supported types: {SUPPORTED_FILE_TYPES}"
            )

        if suffix == ".pdf":
            content = self._load_pdf(path)
        else:
            content = self._load_text(path)

        category = self._get_category(path)

        return LoadedDocument(
            content=content,
            metadata={
                "source": path.as_posix(),
                "file_name": path.name,
                "file_type": suffix.removeprefix("."),
                "category": category,
            },
        )

    def load_directory(
        self,
        directory: str | Path,
    ) -> list[LoadedDocument]:
        """
        递归读取目录下所有支持的知识文档。
        """
        root = Path(directory)

        if not root.exists():
            raise FileNotFoundError(
                f"Document directory not found: {root}"
            )

        if not root.is_dir():
            raise ValueError(
                f"Path is not a directory: {root}"
            )

        documents: list[LoadedDocument] = []

        for path in sorted(root.rglob("*")):
            if (
                path.is_file()
                and path.suffix.lower() in SUPPORTED_FILE_TYPES
            ):
                documents.append(
                    self.load_file(path)
                )

        return documents

    @staticmethod
    def _load_text(path: Path) -> str:
        """
        加载 TXT / Markdown。
        """
        return path.read_text(
            encoding="utf-8"
        ).strip()

    @staticmethod
    def _load_pdf(path: Path) -> str:
        """
        加载 PDF 文本。
        第一版暂时把所有页面文本合并。
        """
        reader = PdfReader(path)

        pages: list[str] = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                pages.append(text.strip())

        return "\n\n".join(pages).strip()

    @staticmethod
    def _get_category(path: Path) -> str | None:
        """
        根据 documents 下一级目录推断知识分类。

        例如：
        knowledge/documents/alarm/test.md

        category = alarm
        """
        parts = path.parts

        try:
            index = parts.index("documents")

            if index + 1 < len(parts) - 1:
                return parts[index + 1]

        except ValueError:
            pass

        return None