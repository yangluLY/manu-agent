
from agent.workflow.executors.real import (
    RealStepRunner,
)
from agent.workflow.schemas.plan import PlanStep


def test_real_step_runner_dispatch():

    calls = []

    def create_runner(agent_name):

        def runner(step, previous_results):
            calls.append(agent_name)
            return f"{agent_name} executed"

        return runner

    runner = RealStepRunner(
        mes_runner=create_runner("mes"),
        rag_runner=create_runner("rag"),
        bi_runner=create_runner("bi"),
        summary_runner=create_runner("summary"),
    )

    agents = [
        "mes",
        "bi",
        "rag",
        "summary",
    ]

    for index, agent in enumerate(agents, start=1):
        step = PlanStep(
            id=index,
            agent=agent,
            task=f"测试 {agent}",
        )

        output = runner(step, [])

        assert output == f"{agent} executed"

    assert calls == agents
