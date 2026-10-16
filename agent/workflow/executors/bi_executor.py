
from agent.analytics.pipeline import BIPipeline
from agent.workflow.schemas.plan import PlanStep
from agent.workflow.schemas.result import AgentOutput


def create_bi_runner(
    pipeline: BIPipeline,
):

    def run(
        step: PlanStep,
        previous_results: list[dict],
    ) -> AgentOutput:

        if step.agent != "bi":
            raise ValueError(
                "当前步骤不是 BI 任务"
            )

        # 提取已完成步骤的信息
        context = "\n".join(
            (
                f"{item['agent']}: "
                f"{item['output']}"
            )
            for item in previous_results
        )

        question = step.task

        if context:
            question += (
                "\n\n前序步骤参考信息：\n"
                f"{context}\n"
                "请以实际数据库查询结果为准。"
            )

        # 复用 V3 BI Pipeline
        result = pipeline.run(
            question=question,
        )

        # 完整保留 V3 的分析结果
        analysis = result.analysis.model_dump(
            mode="json"
        )

        query_data = result.data.model_dump(
            mode="json"
        )

        output = (
            f"BI 分析：{analysis['summary']}\n"
            f"关键发现："
            f"{'; '.join(analysis['key_findings'])}"
        )

        return AgentOutput(
            output=output,

            sql=result.sql,

            data={
                "question": result.question,
                "query_result": query_data,
                "analysis": analysis,
                "retry_count": result.retry_count,
            },

            # ECharts 可直接使用的 option
            chart=result.echarts_option,
        )

    return run
