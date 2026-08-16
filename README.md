# Agent Service

一个基于 LangGraph 的多 Agent 游戏 BI 报告生成工具。项目读取 HTML 报告模板和 JSON 指标数据，自动完成分析文案填充、结果审查与返工，并最终通过 Playwright 生成 PDF 报告。

## 工作流程

```text
report.html + metrics.json
          │
          ▼
   HTML Generator
          │
          ▼
      Reviewer ── REJECT ──> 修改 HTML（最多 3 次）
          │
       APPROVE
          ▼
    PDF Generator
          │
          ▼
autoreport.html + aireport.pdf
```

项目包含三个主要 Agent：

- `html_generator`：读取模板和指标数据，生成分析后的 HTML 报告。
- `reviewer`：检查文案逻辑、数据准确性、小样本风险及占位符是否完整填写。
- `pdf_generator`：使用 Playwright 将审核后的 HTML 转换为 PDF。

## 环境要求

- Python 3.10
- OpenAI API Key
- Playwright Chromium

## 安装

### 使用 Conda

```bash
conda env create -f environment.yml
conda activate agent_service_py310
playwright install chromium
```

### 使用 venv

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Linux 环境如果缺少 Chromium 的系统依赖，可执行：

```bash
playwright install-deps chromium
```

## 配置

在项目根目录创建 `.env` 文件：

```dotenv
OPENAI_API_KEY=your_openai_api_key
```

`.env` 已被 Git 忽略，请勿将真实 API Key 提交到仓库。

当前模型配置位于 `agent_service/model/init_model.py`：

| 角色 | 默认模型 | 用途 |
| --- | --- | --- |
| Strong | `gpt-5.2` | 生成和修改 HTML 报告 |
| Common | `gpt-5.1` | 审核报告内容 |
| Fast | `gpt-4o-mini` | 调用 PDF 转换工具 |

使用前请确认这些模型在你的 OpenAI 账号中可用；如需替换，可直接修改该配置文件。

## 准备输入文件

在一个输出目录中放置以下两个文件：

```text
html/
├── report.html    # HTML 报告模板
└── metrics.json   # BI 指标数据
```

模板中可以使用以下待填内容：

- `...`：需要 Agent 根据指标生成的分析或总结。
- `[上升][下降]`：需要 Agent 根据实际数据选择的内容。

默认输出目录为项目根目录下的 `html/`。

## 运行

在项目根目录执行：

```bash
python -c "from agent_service.analyzier_agent import run_agent; print(run_agent())"
```

也可以指定其他输入/输出目录和会话 ID：

```bash
python -c "from agent_service.analyzier_agent import run_agent; print(run_agent(output_dir='path/to/report', thread_id='report-001'))"
```

`output_dir` 同时作为输入和输出目录，执行完成后会生成：

```text
html/
├── report.html
├── metrics.json
├── autoreport.html
└── aireport.pdf
```

运行过程中，终端会显示当前 Agent、工具调用结果、审查返工次数和累计 Token 消耗。

## 项目结构

```text
agent_service/
├── agents/              # HTML 生成、审核和 PDF Agent
├── messages/            # 各 Agent 的系统提示词
├── model/               # 模型初始化与角色配置
├── state/               # LangGraph 共享状态定义
├── tools/               # 文件读写及 HTML 转 PDF 工具
├── utils/               # 模型调用与 Token 统计
├── workflow/            # LangGraph 工作流和路由逻辑
└── analyzier_agent.py   # 对外运行入口
```

## 注意事项

- 启动时必须能在项目目录或父目录中找到 `.env` 文件，否则当前实现会主动终止运行。
- 每次运行会删除输出目录中已有的 `aireport.pdf`，然后重新生成。
- Reviewer 最多要求修改三次；达到上限后会继续进入 PDF 生成阶段。
- PDF 默认使用约 `410mm × 2900mm` 的长页面尺寸，并保留 HTML 背景样式。
- 输入内容可能会发送给配置的模型提供商，请勿使用未经授权的敏感数据。

## License

本项目暂未声明开源许可证。
