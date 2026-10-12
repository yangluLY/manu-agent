import sys
from pathlib import Path

# 把上级目录 manu-agent 加入python路径
sys.path.append(str(Path(__file__).parent.parent))
from knowledge.retrieval.retriever import KnowledgeRetriever
from services.database.session import SessionLocal


def main():
    db = SessionLocal()

    try:
        retriever = KnowledgeRetriever(db)

        query = "CNC主轴温度过高怎么办？"

        print(f"Query: {query}")
        print()

        results = retriever.search(
            query=query,
            top_k=3,
        )

        print(f"Results: {len(results)}")

        for index, result in enumerate(
            results,
            start=1,
        ):
            print()
            print("=" * 70)
            print(f"Result {index}")
            print(f"Score: {result.score:.4f}")
            print(
                f"Document: "
                f"{result.document_name}"
            )
            print(
                f"Chunk: "
                f"{result.chunk_index}"
            )
            print("-" * 70)
            print(result.content)

    finally:
        db.close()


if __name__ == "__main__":
    main()