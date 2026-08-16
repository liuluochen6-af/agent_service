import logging
from typing import Literal

from langchain_core.messages import SystemMessage

from agent_service.messages import get_generator_prompt, get_reviewer_prompt
from agent_service.state.agent_state import AgentState
from agent_service.utils.invoke_with_stats import invoke_model_with_stats



def reviewer_node(state: AgentState, model, tools):
    """审查者节点"""
    # 1. 绑定工具：Reviewer 只能读
    review_tools = [t for t in tools if t.name in ["read_referred_html", "read_raw_json", "write_html"]]
    model_bind = model.bind_tools(review_tools)

    # 2. 构造上下文
    sys_msg = SystemMessage(content=get_reviewer_prompt())

    # 3. 这里的 messages 包含了 Generator 的整个思考过程。
    # 为了防止 Reviewer 被过长的历史干扰，也可以选择只传最后几条，
    # 但为了能看到 Generator 改了什么，我们把整个历史传进去，并追加 System Prompt 强调身份
    # 注意：LangChain 模型通常支持 System Message 在中间，或者作为列表第一个。
    # 这里我们采用追加 System Message 的方式提醒模型切换角色。
    messages = state["messages"] + [sys_msg]

    return invoke_model_with_stats(state, model_bind, messages)

def router_after_reviewer(state: AgentState) -> Literal["review_tools", "pdf_generator", "html_generator", "__end__"]:
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "review_tools"

    content = str(last_message.content).upper()

    if "APPROVE" in content:
        return "pdf_generator"

    elif "REJECT" in content:
        # 检查重试次数
        current_rev = state.get("revision_count", 0)
        if current_rev >= 3:
            logging.warning("⚠️ 达到最大修改次数 (3次)，强制进入 PDF 生成阶段。")
            return "pdf_generator"
        else:
            return "html_generator"

    # 如果没下结论，继续审查
    return "reviewer"

