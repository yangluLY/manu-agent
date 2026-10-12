import sys
from pathlib import Path

# 把上级目录 manu-agent 加入python路径
sys.path.append(str(Path(__file__).parent.parent))
from agent.tools.knowledge_tools import (
    KnowledgeTools,
)
from knowledge.retrieval.retriever import (
    KnowledgeRetriever,
)
from services.database.session import SessionLocal


def main():
    db = SessionLocal()

    try:
        retriever = KnowledgeRetriever(
            db=db,
        )   

        tools = KnowledgeTools(
            retriever=retriever,
        )

        result = tools.search_knowledge(
            query="CNC主轴温度过高应该怎么处理？",
            top_k=3,
            category="alarm",
        )

        print(
            result.model_dump_json(
                indent=2,
            )
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()