from typing import Literal

from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage

from agent_service.messages import get_generator_prompt, get_pdf_producer_prompt
from agent_service.state.agent_state import AgentState
from agent_service.utils.invoke_with_stats import invoke_model_with_stats



def pdf_generator_node(state: AgentState, model, tools):
    """PDF 执行者节点 (增加了防死循环逻辑)"""
    # 1. 绑定工具
    pdf_tools = [t for t in tools if t.name == "convert_html_to_pdf"]
    model_bind = model.bind_tools(pdf_tools)

    messages = state["messages"]
    last_msg = messages[-1]

    # 2. 【核心修复】防死循环检测
    # 如果上一条消息是 ToolMessage，说明工具刚刚执行完毕
    if isinstance(last_msg, ToolMessage) or last_msg.type == "tool":
        # 强行注入一条 HumanMessage，告诉模型任务结束
        trigger_msg = HumanMessage(content="系统检测到 PDF 已成功生成。**任务强制结束**。请直接回复 'DONE'，不要再次调用工具。")
        # 这里不加 SystemPrompt 了，因为历史记录里应该已经有了，避免重复累赘
        messages_to_send = messages + [trigger_msg]
    else:
        # 正常进入流程
        sys_msg = SystemMessage(content=get_pdf_producer_prompt())
        trigger_msg = HumanMessage(content="审查已通过 (APPROVE)。请立即生成 PDF。")
        messages_to_send = messages + [sys_msg, trigger_msg]

    return invoke_model_with_stats(state, model_bind, messages_to_send)



def router_after_pdf(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "pdf_tools"
    return "__end__"


