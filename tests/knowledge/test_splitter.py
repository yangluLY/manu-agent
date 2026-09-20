import pytest

from knowledge.ingestion.loaders import LoadedDocument
from knowledge.ingestion.splitter import TextSplitter


def test_split_short_document():
    document = LoadedDocument(
        content="这是一段较短的设备维修知识。",
        metadata={
            "file_name": "test.md",
            "category": "alarm",
        },
    )

    splitter = TextSplitter(
        chunk_size=100,
        chunk_overlap=20,
    )

    chunks = splitter.split_document(document)

    assert len(chunks) == 1
    assert chunks[0].content == document.content
    assert chunks[0].metadata["chunk_index"] == 0


def test_split_long_document():
    text = (
        "主轴温度过高，应检查冷却液。"
        "冷却液不足可能导致主轴温度升高。"
        "同时需要检查冷却泵运行状态。"
        "如果冷却泵异常，应停止设备运行。"
        "设备维修完成后，需要重新确认主轴温度。"
    ) * 10

    document = LoadedDocument(
        content=text,
        metadata={
            "file_name": "alarm.md",
            "category": "alarm",
        },
    )

    splitter = TextSplitter(
        chunk_size=100,
        chunk_overlap=20,
    )

    chunks = splitter.split_document(document)

    assert len(chunks) > 1

    for index, chunk in enumerate(chunks):
        assert chunk.content
        assert chunk.metadata["chunk_index"] == index
        assert chunk.metadata["file_name"] == "alarm.md"


def test_invalid_chunk_size():
    with pytest.raises(ValueError):
        TextSplitter(
            chunk_size=0,
            chunk_overlap=0,
        )


def test_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(ValueError):
        TextSplitter(
            chunk_size=100,
            chunk_overlap=100,
        )