import sys
from pathlib import Path

import numpy as np

# 把上级目录 manu-agent 加入python路径
sys.path.append(str(Path(__file__).parent.parent))
from knowledge.ingestion.embedder import (
    EMBEDDING_DIM,
    Embedder,
)


def main():
    print("Loading embedding model...")

    embedder = Embedder()

    print("Model loaded successfully.")
    print()

    documents = [
        "主轴温度过高可能由冷却液不足导致。",
        "冷却泵异常可能导致主轴冷却能力下降。",
        "原材料库存不足时需要及时补充库存。",
    ]

    print("Generating document embeddings...")

    document_embeddings = embedder.embed_documents(
        documents
    )

    print(
        f"Document embeddings: "
        f"{len(document_embeddings)}"
    )

    for index, embedding in enumerate(
        document_embeddings
    ):
        print(
            f"Document {index}: "
            f"dimension={len(embedding)}"
        )

    print()
    print("Generating query embedding...")

    query = "CNC主轴温度太高怎么办？"

    query_embedding = embedder.embed_query(
        query
    )

    print(f"Query: {query}")
    print(
        f"Embedding dimension: "
        f"{len(query_embedding)}"
    )

    print(
        f"First 10 values: "
        f"{query_embedding[:10]}"
    )

    assert len(query_embedding) == EMBEDDING_DIM

    for embedding in document_embeddings:
        assert len(embedding) == EMBEDDING_DIM

    print()
    print("Embedding test passed.")

    print()

    query_vector = np.array(
        query_embedding
    )

    for index, embedding in enumerate(
        document_embeddings
    ):
        document_vector = np.array(
            embedding
        )

        similarity = np.dot(
            query_vector,
            document_vector,
        )

        print(
            f"{similarity:.4f} "
            f"- {documents[index]}"
        )
        
print("Similarity:")




if __name__ == "__main__":
    main()