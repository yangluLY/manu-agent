import sys
from pathlib import Path

# 把上级目录 manu-agent 加入python路径
sys.path.append(str(Path(__file__).parent.parent))
from knowledge.retrieval.rag_service import RAGService
from services.database.session import SessionLocal


def main():
    db = SessionLocal()

    try:
        rag = RAGService(db)

        question = (
            "CNC主轴温度过高应该怎么处理？"
        )

        print("=" * 70)
        print(f"Question: {question}")
        print("=" * 70)

        result = rag.query(
            question=question,
            top_k=3,
        )

        print()
        print("Answer:")
        print(result.answer)

        print()
        print("=" * 70)
        print("Sources:")
        print("=" * 70)

        for source in result.sources:
            print(
                f"- {source.document_name}"
                f" / chunk={source.chunk_index}"
                f" / score={source.score:.4f}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()