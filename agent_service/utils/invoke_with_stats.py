from agent_service.state.agent_state import AgentState


def invoke_model_with_stats(state: AgentState, model_bind, messages_to_send):
    """
    通用函数：调用模型并更新 State 中的 Token 统计
    """
    current_total_input = state.get("total_input_tokens", 0)
    current_total_output = state.get("total_output_tokens", 0)

    # 调用模型
    response = model_bind.invoke(messages_to_send)

    # 解析消耗
    usage_meta = response.response_metadata.get("token_usage", {}) or response.response_metadata.get("usage", {})
    this_step_input = usage_meta.get("prompt_tokens", 0)
    this_step_output = usage_meta.get("completion_tokens", 0)

    return {
        "messages": [response],
        "total_input_tokens": current_total_input + this_step_input,
        "total_output_tokens": current_total_output + this_step_output
    }