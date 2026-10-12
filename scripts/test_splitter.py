from knowledge.ingestion.loaders import DocumentLoader
from knowledge.ingestion.splitter import TextSplitter


def main():
    loader = DocumentLoader()

    documents = loader.load_directory(
        "knowledge/documents"
    )

    splitter = TextSplitter(
        chunk_size=150,
        chunk_overlap=30,
    )

    chunks = splitter.split_documents(
        documents
    )

    print(f"Documents: {len(documents)}")
    print(f"Chunks: {len(chunks)}")

    for chunk in chunks:
        print()
        print("=" * 70)

        print(
            f"file_name: "
            f"{chunk.metadata['file_name']}"
        )

        print(
            f"category: "
            f"{chunk.metadata['category']}"
        )

        print(
            f"chunk_index: "
            f"{chunk.metadata['chunk_index']}"
        )

        print(
            f"chunk_length: "
            f"{chunk.metadata['chunk_length']}"
        )

        print("-" * 70)

        print(chunk.content)


if __name__ == "__main__":
    main()