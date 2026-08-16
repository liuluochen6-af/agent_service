from typing import TypedDict, Annotated, List, Union
from langchain_core.messages import BaseMessage
import operator

def add_messages(left: list, right: list):
    """标准的 LangGraph 消息追加逻辑"""
    return left + right

class AgentState(TypedDict):
    # 消息历史
    messages: Annotated[List[BaseMessage], add_messages]
    # 记录当前的迭代次数（防止 Reviewer 和 Generator 无限扯皮）
    revision_count: int
    # Token 统计
    total_input_tokens: int
    total_output_tokens: int