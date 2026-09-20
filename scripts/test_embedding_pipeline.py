import sys
from pathlib import Path

# 把上级目录 manu-agent 加入python路径
sys.path.append(str(Path(__file__).parent.parent))
from knowledge.ingestion.embedder import Embedder
from knowledge.ingestion.loaders import DocumentLoader
from knowledge.ingestion.splitter import TextSplitter


def main():
    # 1. 加载知识文档
    loader = DocumentLoader()

    documents = loader.load_directory(
        "knowledge/documents"
    )

    print(
        f"Loaded documents: {len(documents)}"
    )

    # 2. 文档切片
    splitter = TextSplitter(
        chunk_size=500,
        chunk_overlap=100,
    )

    chunks = splitter.split_documents(
        documents
    )

    print(
        f"Created chunks: {len(chunks)}"
    )

    # 3. 加载 Embedding 模型
    print("Loading embedding model...")

    embedder = Embedder()

    # 4. 提取所有 Chunk 的文本
    texts = [
        chunk.content
        for chunk in chunks
    ]

    # 5. 生成 Embedding
    embeddings = embedder.embed_documents(
        texts
    )

    print(
        f"Generated embeddings: "
        f"{len(embeddings)}"
    )

    # 6. 检查结果
    for chunk, embedding in zip(
        chunks,
        embeddings,
    ):
        print()
        print("=" * 60)

        print(
            f"file: "
            f"{chunk.metadata['file_name']}"
        )

        print(
            f"chunk: "
            f"{chunk.metadata['chunk_index']}"
        )

        print(
            f"text length: "
            f"{len(chunk.content)}"
        )

        print(
            f"embedding dimension: "
            f"{len(embedding)}"
        )

        print(
            f"embedding preview: "
            f"{embedding[:5]}"
        )


if __name__ == "__main__":
    main()