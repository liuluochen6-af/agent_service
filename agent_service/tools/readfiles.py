import json
import logging
import os
import pandas as pd  # <-- 新增导入 pandas

class ReadFiles:

    def __init__(self, base_path: str = None):
        # 自动找到项目根目录
        self.base_path = base_path or os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

    def _full(self, path: str) -> str:
        return os.path.join(self.base_path, path)

    """
    文件读取和内容格式化的工具类。

    该类中的方法被标记为 @tool，可用于 LLM Agent 的工具调用。
    """

    # ----------------------------------------------------------------------
    # 1. 读取原始 JSON 文件 (read_raw_json) - 极速版
    # ----------------------------------------------------------------------
    def read_raw_json(self, json_path: str) -> str:
        """
        读取 JSON 文件并进行 Token 极限压缩（Pandas 加速版）：
        1. 优先尝试转为 DataFrame，利用向量化操作瞬间完成去空值和修约。
        2. 输出为 Markdown（LLM 读表能力最强）或 紧凑 JSON。
        3. 避免使用缓慢的 Python 递归和 YAML dump。
        """
        json_path = self._full(json_path)
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"JSON 文件未找到: {json_path}")

        try:
            # 1. 尝试直接加载为 DataFrame (C语言速度)
            # orient='records' 适用于列表结构，如果失败会抛错，进入 except
            df = pd.read_json(json_path)

            # === Pandas 极速清洗 ===

            # 1. 数值修约：所有数值列保留2位小数 (向量化操作，极快)
            df = df.round(2)

            # 2. 去除全为空的列和行
            df.dropna(axis=1, how='all', inplace=True)
            df.dropna(axis=0, how='all', inplace=True)

            # 3. (可选) 填充剩余的 NaN 为空字符串，减少 Token
            df.fillna("", inplace=True)

            # 4. 转为 Markdown (比 YAML 生成快得多，且 LLM 对表格理解极好)
            return df.to_markdown(index=False)

        except ValueError:
            # === 兜底方案：如果 JSON 结构太复杂（多层嵌套），无法转为表格 ===
            # 使用原生 json 库读取，它是 C 优化的，比 yaml 快得多
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 使用 separators 去除所有空格和换行，极致压缩 Token
            # 虽然不再做递归去空和修约（为了速度），但去空格带来的压缩收益通常最大
            return json.dumps(data, ensure_ascii=False, separators=(',', ':'))

        except Exception as e:
            logging.error(f"JSON 读取优化失败: {e}")
            # 最坏情况，回退到普通读取
            with open(json_path, 'r', encoding='utf-8') as f:
                return f.read()

    # ----------------------------------------------------------------------
    # 2. HTML 格式化 (html_format)
    # ----------------------------------------------------------------------
    def read_referred_html(self, html_path: str) -> str:
        """
        读取HTML

        Args:
            html_path (str): Html路径

        Returns:
            str: HTML 字符串。
        """
        html_path = self._full(html_path)
        # 这里的 os.path.exists 检查可以省略，因为 open() 会抛出 FileNotFoundError
        return open(html_path, 'r', encoding='utf-8').read()

    # ----------------------------------------------------------------------
    # 3. 读取csv
    # ----------------------------------------------------------------------
    def read_csv(self, csv_path: str) -> str:
        """
        读取 CSV 文件，返回前 N 行数据及其列名，以 JSON 字符串格式展示。
        这有助于 Agent 快速了解数据结构，避免读取过大的文件。

        Args:
            csv_path (str): CSV 文件的路径 (相对于 base_path)。

        Returns:
            str: CSV 数据前 N 行的 JSON 字符串表示。

        Raises:
            FileNotFoundError: 如果文件不存在。
            Exception: 如果 pandas 读取文件失败。
        """
        full_csv_path = self._full(csv_path)

        if not os.path.exists(full_csv_path):
            raise FileNotFoundError(f"CSV 文件未找到: {full_csv_path}")

        try:
            # 使用 pandas 读取 CSV 文件，自动检测编码和分隔符
            df = pd.read_csv(full_csv_path)

            # 返回前 N 行数据的 JSON 字符串表示， orient='records' 是列表包裹的字典格式
            return df.to_json(orient='records', force_ascii=False, indent=2)

        except Exception as e:
            logging.error(f"读取 CSV 文件失败: {e}")
            return f"错误: 无法读取或解析 CSV 文件。详情: {e}"