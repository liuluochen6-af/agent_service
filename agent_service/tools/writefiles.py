import json
import os
from typing import Dict, Any
from langchain_core.tools import tool


class WriteFiles:
    def __init__(self, base_path: str = None):
        self.base_path = base_path or os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

    def _full(self, path: str) -> str:
        return os.path.join(self.base_path, path)
    """
    文件写入和内容保存的工具类。

    该类中的方法被标记为 @tool，可用于 LLM Agent 的工具调用。
    """

    # ----------------------------------------------------------------------
    # 1. 写入 JSON 文件 (write_json)
    # ----------------------------------------------------------------------
    def write_json(self, json_path: str, data: Dict[str, Any]) -> str:
        """
        将字典写入指定路径的 JSON 文件。

        Args:
            json_path (str): 要写入的 JSON 文件路径。
            data (Dict[str, Any]): 要保存的数据字典。

        Returns:
            str: 写入成功的提示信息。
        """
        json_path = self._full(json_path)
        folder = os.path.dirname(json_path)
        os.makedirs(folder, exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return f"JSON 文件已成功写入: {json_path}"

    # ----------------------------------------------------------------------
    # 2. 写入纯文本文件 (write_text)
    # ----------------------------------------------------------------------
    def write_text(self, file_path: str, text: str) -> str:
        """
        将字符串写入文本文件。

        Args:
            file_path (str): 保存文件的路径。
            text (str): 要写入的文本内容。

        Returns:
            str: 写入成功信息。
        """
        file_path = self._full(file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return f"文本文件已成功写入: {file_path}"

    # ----------------------------------------------------------------------
    # 3. 写入 HTML 文件 (write_html)
    # ----------------------------------------------------------------------
    def write_html(self, html_path: str, html_content: str) -> str:
        """
        将 HTML 字符串写入文件。

        Args:
            html_path (str): HTML 文件路径。
            html_content (str): HTML 字符串。

        Returns:
            str: 写入成功信息。
        """
        html_path = self._full(html_path)
        os.makedirs(os.path.dirname(html_path), exist_ok=True)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return f"HTML 文件已成功写入: {html_path}"

    # ----------------------------------------------------------------------
    # 4. 附加内容到文本文件 (append_text)
    # ----------------------------------------------------------------------
    def append_text(self, file_path: str, content: str) -> str:
        """
        在文件末尾追加文本内容，如果文件不存在则创建。

        Args:
            file_path (str): 文件路径。
            content (str): 要追加的内容。

        Returns:
            str: 操作成功信息。
        """
        file_path = self._full(file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content)
        return f"内容已追加到文件: {file_path}"
