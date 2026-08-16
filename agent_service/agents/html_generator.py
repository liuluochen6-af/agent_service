from typing import Literal

from langchain_core.messages import SystemMessage

from agent_service.messages import get_generator_prompt
from agent_service.state.agent_state import AgentState
from agent_service.utils.invoke_with_stats import invoke_model_with_stats


def html_generator_node(state: AgentState, model, tools):
    """HTML 生成者节点"""
    # 1. 绑定工具：Generator 只能读写 HTML 和读 JSON
    gen_tools = [t for t in tools if t.name in ["read_referred_html", "read_raw_json", "write_html"]]
    model_bind = model.bind_tools(gen_tools)

    # 2. 构造上下文
    # 如果历史记录里还没有 SystemPrompt (或者是在重试)，我们需要确保生成者知道自己的角色
    current_messages = state["messages"]

    # 简单策略：如果是第一轮，插入 System Prompt
    # 如果是返工(REJECT)，router 会插入一条 HumanMessage 指令，这里只需继续 invoke
    if not any(isinstance(m, SystemMessage) and "HTML生成专家" in m.content for m in current_messages):
        sys_msg = SystemMessage(content=get_generator_prompt())
        messages = [sys_msg] + current_messages
    else:
        messages = current_messages

    return invoke_model_with_stats(state, model_bind, messages)

def router_after_generator(state: AgentState) -> Literal["html_tools", "reviewer", "__end__"]:
    last_message = state["messages"][-1]

    # 1. 如果有工具调用，继续在生成器循环
    if last_message.tool_calls:
        return "html_tools"

    # 2. 如果生成器回复 DONE，进入审查
    if "DONE" in str(last_message.content):
        return "reviewer"

    # 默认情况继续生成 (或者强制让它生成)
    return "html_generator"  # 这里可以改回 html_generator 让它继续思考，直到输出 DONE

