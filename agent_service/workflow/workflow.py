from langchain_core.messages import HumanMessage
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from agent_service.agents.html_generator import html_generator_node, router_after_generator
from agent_service.agents.pdf_generator import pdf_generator_node, router_after_pdf
from agent_service.agents.reviewer import reviewer_node, router_after_reviewer
from agent_service.state.agent_state import AgentState

def pass_feedback_to_generator(state: AgentState):
    """当 Reviewer 拒绝时，增加计数并添加指令"""
    return {
        "revision_count": state.get("revision_count", 0) + 1,
        "messages": [
            HumanMessage(content="审查未通过。请根据上述 REJECT 意见修改 'autoreport.html'。修改完成后回复 DONE。")]
    }


def build_workflow(models:dict, tools) -> StateGraph:
    workflow = StateGraph(AgentState)

    common_model = models["Common"]
    strong_model = models["Strong"]
    fast_model = models["Fast"]

    # 1. 工具节点 (通用)
    tool_node = ToolNode(tools)

    # 2. 添加所有 Agent 节点
    workflow.add_node("html_generator", lambda state: html_generator_node(state, strong_model, tools))
    workflow.add_node("html_tools", tool_node)

    workflow.add_node("reviewer", lambda state: reviewer_node(state, common_model, tools))
    workflow.add_node("review_tools", tool_node)

    workflow.add_node("pdf_generator", lambda state: pdf_generator_node(state, fast_model, tools))
    workflow.add_node("pdf_tools", tool_node)

    # 添加处理驳回逻辑的中间节点
    workflow.add_node("handle_rejection", pass_feedback_to_generator)

    # 3. 设置入口
    workflow.set_entry_point("html_generator")

    # 4. 连线：HTML Generator 循环
    workflow.add_conditional_edges(
        "html_generator",
        router_after_generator,
        {
            "html_tools": "html_tools",
            "reviewer": "reviewer",
            "html_generator": "html_generator"
        }
    )
    workflow.add_edge("html_tools", "html_generator")

    # 逻辑：
    # - 工具调用 -> review_tools
    # - 通过 -> pdf_generator
    # - 驳回 -> handle_rejection (添加反馈信息) -> html_generator (重做)
    # - 犹豫不决 -> reviewer (继续思考)
    workflow.add_conditional_edges(
        "reviewer",
        router_after_reviewer,
        {
            "review_tools": "review_tools",
            "pdf_generator": "pdf_generator",
            "html_generator": "handle_rejection",  # 关键：映射到处理驳回的节点
            "reviewer": "reviewer"
        }
    )
    workflow.add_edge("review_tools", "reviewer")

    # 6. 连线：驳回处理完毕后，强制回滚到 Generator
    workflow.add_edge("handle_rejection", "html_generator")

    # 7. 连线：PDF Generator
    workflow.add_conditional_edges(
        "pdf_generator",
        router_after_pdf,
        {"pdf_tools": "pdf_tools", "__end__": END}
    )
    workflow.add_edge("pdf_tools", "pdf_generator")

    return workflow
