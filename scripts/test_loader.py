import sys
from pathlib import Path

# 把上级目录 manu-agent 加入python路径
sys.path.append(str(Path(__file__).parent.parent))
from knowledge.ingestion.loaders import DocumentLoader


def main():
    loader = DocumentLoader()

    documents = loader.load_directory(
        "knowledge/documents"
    )

    print(
        f"Loaded documents: {len(documents)}"
    )

    for index, document in enumerate(
        documents,
        start=1,
    ):
        print()
        print("=" * 60)
        print(f"Document {index}")
        print("=" * 60)

        print(
            f"file_name: "
            f"{document.metadata['file_name']}"
        )

        print(
            f"file_type: "
            f"{document.metadata['file_type']}"
        )

        print(
            f"category: "
            f"{document.metadata['category']}"
        )

        print(
            f"source: "
            f"{document.metadata['source']}"
        )

        print()
        print("Content preview:")
        print(document.content[:300])


if __name__ == "__main__":
    main()