
from agent.llm.deepseek_client import DeepSeekClient
from agent.workflow.graph import build_workflow


def create_deepseek_invoke(
    llm: DeepSeekClient,
):
    """
    将现有 DeepSeekClient 适配为
    LangGraph Router 所需的调用接口。

    llm_invoke(system_prompt, user_input) -> str
    """

    def llm_invoke(
        system_prompt: str,
        user_input: str,
    ) -> str:

        response = llm.create_response(
            input_items=user_input,
            instructions=system_prompt,
        )

        content = response.output_text

        if not content:
            raise ValueError(
                "DeepSeek Router 返回空内容"
            )

        return content

    return llm_invoke


def get_workflow(
    llm: DeepSeekClient | None = None,
):
    """
    创建 V4 LangGraph 工作流。

    复用 ManuAgent 已有的 DeepSeekClient。
    """

    if llm is None:
        llm = DeepSeekClient()

    llm_invoke = create_deepseek_invoke(llm)

    return build_workflow(llm_invoke)
