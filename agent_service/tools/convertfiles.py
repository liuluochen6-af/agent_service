import os
import platform
from pathlib import Path
from typing import Optional

# 引入 Playwright 同步 API
from playwright.sync_api import sync_playwright


class ConversionTools:
    """
    文件格式转换的工具类 (基于 Playwright)。
    """

    def __init__(self, base_path: str = None):
        # 你的 LLM Agent 应该知道如何处理 base_path
        self.base_path = base_path or os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

    def _full(self, path: str) -> str:
        """获取文件的完整绝对路径。"""
        # 使用 os.path.abspath 确保路径规范化
        return os.path.abspath(os.path.join(self.base_path, path))

    def html_to_pdf(self, html_path: str, output_pdf_path: str, options: Optional[dict] = None) -> str:
        """
        使用 Playwright (Chromium) 将 HTML 文件转换为 PDF。
        支持现代 CSS、Flexbox、Grid 和 JavaScript 渲染。

        Args:
            html_path (str): 源 HTML 文件的路径 (相对于 base_path)。
            output_pdf_path (str): 目标 PDF 文件的路径 (相对于 base_path)。
            options (Optional[dict]): 传递给 page.pdf() 的可选配置。
                                     常用键: 'width', 'height', 'format', 'landscape'.

        Returns:
            str: 转换成功的提示信息或错误信息。
        """
        full_html_path = self._full(html_path)
        full_pdf_path = self._full(output_pdf_path)

        if not os.path.exists(full_html_path):
            return f"错误: 找不到源 HTML 文件: {full_html_path}"

        # 确保输出目录存在
        os.makedirs(os.path.dirname(full_pdf_path), exist_ok=True)

        # 将本地文件路径转换为 file:// URL，这对 Playwright 加载本地资源至关重要
        # 使用 pathlib 处理不同操作系统的路径分隔符
        # 在 Linux 上，它会生成 file:///data/bi/ai_report/report.html 格式
        file_url = Path(full_html_path).as_uri()

        # 默认选项：对应你之前的 wkhtmltopdf 配置
        # Playwright 的单位可以是 px, in, cm, mm
        pdf_options = {
            'path': full_pdf_path,
            'print_background': True,  # 关键：打印背景颜色和图片
            'width': '410mm',  # 你之前指定的宽度
            'height': '2900mm',
            # 'format': 'A4',          # 如果设置了 width/height，通常不需要设置 format，除非你想强制 A4
            'margin': {
                'top': '0',
                'right': '0',
                'bottom': '0',
                'left': '0'
            },
            # scale: 1.0 默认值
        }

        # 合并用户传入的选项
        if options:
            pdf_options.update(options)
            # 移除 path 以防用户意外覆盖（我们强制使用 full_pdf_path）
            pdf_options['path'] = full_pdf_path

        try:
            with sync_playwright() as p:
                # 启动 Chromium 浏览器 (headless 模式)
                # args=['--no-sandbox'] 在某些受限的 Linux root 用户环境下是必须的
                launch_args = ['--no-sandbox'] if platform.system() == "Linux" else []

                browser = p.chromium.launch(headless=True, args=launch_args)

                # 创建新页面
                page = browser.new_page()

                # 跳转到本地 HTML 文件
                # wait_until='networkidle' 表示直到网络空闲（没有新的网络请求）至少 500ms
                # 这对于包含外部图片或 JS 渲染图表的报告非常重要
                page.goto(file_url, wait_until="networkidle")

                # 如果有复杂的 JS 动画或图表，有时还需要强制等待一小会儿
                # page.wait_for_timeout(1000)

                # 生成 PDF
                page.pdf(**pdf_options)

                browser.close()

            return f"HTML 文件已成功转换为 PDF (Playwright): {full_pdf_path}"

        except Exception as e:
            error_msg = f"错误: Playwright 转换 PDF 失败。详情: {e}"
            error_str = str(e)

            # 针对 Linux 常见错误的智能提示
            if "Executable doesn't exist" in error_str:
                error_msg += " (提示: 请运行 'playwright install chromium' 安装浏览器内核)"
            elif "error while loading shared libraries" in error_str or "dependencies" in error_str:
                error_msg += " (提示: Linux 系统可能缺少依赖库，请尝试运行 'playwright install-deps')"

            return error_msg

# 示例用法 (仅供测试):
# if __name__ == "__main__":
#     tool = ConversionTools()
#     print(tool.html_to_pdf("report.html", "report.pdf"))