import os
import logging

from dotenv import load_dotenv, find_dotenv
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver

# 引入自定义模块 (请确保这些文件已按上述步骤修改)
from .state.agent_state import AgentState
from .tools import get_all_tools
from .model import init_model
from .workflow.workflow import build_workflow

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "html"))


# ========== 环境与配置 ==========
def load_key() -> bool:
    dotenv_path = find_dotenv()
    if dotenv_path:
        load_dotenv(dotenv_path)
        logging.info(f"成功加载环境变量文件: {dotenv_path}")
        return True
    else:
        logging.warning("未找到 .env 文件，将使用系统已有的环境变量。")
        return False


def env_init():
    logging.basicConfig(level=logging.INFO)
    if not load_key():
        raise ValueError("API Key 配置缺失，无法启动 Agent。")
    logging.info("BASE_PATH: %s", BASE_PATH)

# ========== 运行逻辑 ==========
def stream_run(app, initial_state: AgentState, thread_id: str):
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 60  # 增加递归上限，因为多 Agent 交互步骤更多
    }
    print(f"\n--- LangGraph 多 Agent 工作流启动 (Thread: {thread_id}) ---\n")

    try:
        for event in app.stream(initial_state, config=config, stream_mode="updates"):
            for node_name, node_output in event.items():

                # 处理纯状态更新节点 (如 handle_rejection)
                if node_name == "handle_rejection":
                    print(f"\n[System]: 审查驳回，第 {node_output.get('revision_count')} 次重试。")
                    continue

                if "messages" not in node_output:
                    continue

                last_message = node_output["messages"][-1]

                # 打印 Token 消耗
                run_input = node_output.get("total_input_tokens", 0)
                run_output = node_output.get("total_output_tokens", 0)

                if node_name in ["html_generator", "reviewer", "pdf_generator"]:
                    print(f"\n[Agent: {node_name}]:")
                    # 打印部分内容预览
                    content_preview = str(last_message.content)[:100].replace('\n', ' ')
                    print(f"   Action: {content_preview}...")

                    if run_input > 0:
                        print(f"   💰 累计消耗: {run_input + run_output}")

                elif "tools" in node_name:
                    print(f"\n[Tool 执行]: {last_message.name if hasattr(last_message, 'name') else 'Result'}")
                    print(f"   Result: {str(last_message.content)[:100]}...")

        print("\n--- 任务结束 ---")
        return app.get_state(config)

    except Exception as e:
        logging.error(f"Stream run error: {e}")
        raise e


def run_agent(output_dir: str = "html", thread_id: str = "report_generator_multi"):
    target_pdf_name = "aireport.pdf"
    target_html_name = "autoreport.html"

    pdf_path = os.path.join(output_dir, target_pdf_name)
    html_path = os.path.join(output_dir, target_html_name)

    try:
        # 1. 环境初始化
        env_init()
        logging.info(f"任务目标路径: {output_dir}")

        # 2. 清理旧文件
        if os.path.exists(pdf_path):
            logging.info(f"发现旧的 {target_pdf_name}，正在清理...")
            try:
                os.remove(pdf_path)
            except OSError as e:
                logging.warning(f"清理旧 PDF 失败: {e}")

        # 3. 初始化模型与工具
        try:
            models = init_model()
            tools = get_all_tools(base_path=output_dir)
        except Exception as e:
            logging.critical(f"❌ 初始化失败: {e}")
            raise RuntimeError(f"模型/工具初始化失败: {e}")

        # 4. 构建与编译 Graph
        workflow = build_workflow(models, tools)
        checkpointer = MemorySaver()
        app = workflow.compile(checkpointer=checkpointer)

        # 5. 准备初始状态
        # 注意：这里不再一次性把 SystemPrompt 放进去，而是由各节点自己管理
        initial_state = {
            "messages": [HumanMessage(content="请开始分析 report.html 并根据 metrics.json 生成报告。")],
            "revision_count": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0
        }

        # 6. 执行
        final_state = stream_run(app, initial_state, thread_id)

        # 7. 结果验证
        if final_state:
            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1024:
                logging.info(f"✅ [SUCCESS] PDF 生成成功: {pdf_path}")
                return pdf_path
            elif os.path.exists(html_path):
                err_msg = f"⚠️ [PARTIAL] 生成了 HTML 但未生成 PDF。"
                logging.error(err_msg)
                raise FileNotFoundError(err_msg)
            else:
                err_msg = f"❌ [FAILURE] 未生成任何文件。"
                logging.error(err_msg)
                raise FileNotFoundError(err_msg)
        else:
            raise RuntimeError("Agent 流程异常终止。")

    except Exception as e:
        logging.critical(f"❌ [CRITICAL] 流程中断: {e}", exc_info=True)
        raise e