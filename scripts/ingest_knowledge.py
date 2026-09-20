import sys
from pathlib import Path

# 把上级目录 manu-agent 加入python路径
sys.path.append(str(Path(__file__).parent.parent))
from knowledge.ingestion.pipeline import IngestionPipeline
from services.database.session import SessionLocal

KNOWLEDGE_DIRECTORY = "knowledge/documents"


def main():
    print("=" * 60)
    print("ManuAgent Knowledge Ingestion")
    print("=" * 60)

    db = SessionLocal()

    try:
        pipeline = IngestionPipeline(
            db=db,
        )

        result = pipeline.ingest_directory(
            KNOWLEDGE_DIRECTORY
        )

        print()
        print("=" * 60)
        print("Knowledge ingestion completed")
        print("=" * 60)

        print(
            f"Documents imported: "
            f"{result['documents']}"
        )

        print(
            f"Chunks inserted: "
            f"{result['chunks']}"
        )

        print(
            f"Failed documents: "
            f"{len(result['failed'])}"
        )

        if result["failed"]:
            print()
            print("Failures:")

            for failure in result["failed"]:
                print(
                    f"- {failure['file_name']}: "
                    f"{failure['error']}"
                )

    finally:
        db.close()


if __name__ == "__main__":
    main()