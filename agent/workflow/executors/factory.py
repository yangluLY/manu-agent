
from sqlalchemy.orm import Session

from agent.factory import (
    create_bi_pipeline,
    create_manu_agent,
)
from agent.llm.deepseek_client import DeepSeekClient
from agent.workflow.executors.bi_executor import (
    create_bi_runner,
)
from agent.workflow.executors.mes_executor import (
    create_mes_runner,
)
from agent.workflow.executors.rag_executor import (
    create_rag_runner,
)
from agent.workflow.executors.real import RealStepRunner
from agent.workflow.executors.summary_executor import (
    create_summary_runner,
)
from knowledge.retrieval.retriever import (
    KnowledgeRetriever,
)


def create_real_step_runner(
    db: Session,
    llm: DeepSeekClient | None = None,
) -> RealStepRunner:

    if llm is None:
        llm = DeepSeekClient()

    mes_agent = create_manu_agent(db)
    bi_pipeline = create_bi_pipeline(db)
    retriever = KnowledgeRetriever(db=db)

    return RealStepRunner(
        mes_runner=create_mes_runner(
            mes_agent
        ),
        rag_runner=create_rag_runner(
            retriever
        ),
        bi_runner=create_bi_runner(
            bi_pipeline
        ),
        summary_runner=create_summary_runner(
            llm
        ),
    )
