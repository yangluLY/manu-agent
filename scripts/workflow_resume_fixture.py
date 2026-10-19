
import json

from agent.workflow.graph import build_workflow


def mock_llm(system_prompt, user_input):
    if "任务路由器" in system_prompt:
        return json.dumps({
            "route": "mes",
            "reason": "跨进程恢复测试",
        })

    raise ValueError(
        "测试不应该进入其他 LLM 阶段"
    )


def mock_runner(step, previous_results):
    print(
        f"[Mock MES] 执行任务: {step.task}"
    )

    return "CNC-001 当前设备运行正常"


def create_resume_workflow(checkpointer):
    return build_workflow(
        llm_invoke=mock_llm,
        step_runner=mock_runner,
        checkpointer=checkpointer,
        require_approval=True,
    )


def initial_state():
    return {
        "user_input": "查询 CNC-001 设备运行状态",
        "route": "general",
        "route_reason": "",
        "plan": [],
        "current_step": 0,
        "step_results": [],
        "result": "",
        "final_answer": "",
    }
