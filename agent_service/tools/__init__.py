from typing import List

from .convertfiles import ConversionTools
from .readfiles import *
from .structpath import StructPath
from .writefiles import *
from langchain_core.tools import tool, StructuredTool
from langchain_core.tools import Tool



def get_all_tools(base_path: str) -> list[StructuredTool]:
    # 1. 实例化类（这里保存了 base_path 状态）
    convert_files_instance = ConversionTools(base_path)
    read_files_instance = ReadFiles(base_path)
    write_files_instance = WriteFiles(base_path)
    struct_path = StructPath(base_path)

    # 2. 使用 StructuredTool.from_function 包装实例方法
    # 这样 LangChain 就能正确调用绑定了 self 的方法
    tools = [
        StructuredTool.from_function(
            func=convert_files_instance.html_to_pdf,
            name="convert_html_to_pdf",
            description="转换html为pdf"
        ),
        StructuredTool.from_function(
            func=struct_path.read_path,
            name="read_path",
            description="默认的文件读取路径"  # 如果函数有docstring，这里可以省略
        ),
        StructuredTool.from_function(
            func=struct_path.write_path,
            name="write_path",
            description="默认的文件写入路径"  # 如果函数有docstring，这里可以省略
        ),
        StructuredTool.from_function(
            func=read_files_instance.read_raw_json,
            name="read_raw_json",
            description="读取本地JSON文件的内容。输入参数应该是文件的相对路径。" # 如果函数有docstring，这里可以省略
        ),
        StructuredTool.from_function(
            func=read_files_instance.read_referred_html,
            name="read_referred_html",
            description="读取HTML文件的内容。"
        ),
        StructuredTool.from_function(
            func=read_files_instance.read_csv,
            name="read_csv",
            description="读取csv文件的内容。"
        ),
        StructuredTool.from_function(
            func=write_files_instance.write_html,
            name="write_html",
            description="将内容写入HTML文件。"
        ),
        StructuredTool.from_function(
            func=write_files_instance.write_json,
            name="write_json",
            description="将内容写入JSON文件。"
        ),
        StructuredTool.from_function(
            func=write_files_instance.write_text,
            name="write_text",
            description="写入纯文本文件。"
        ),
        StructuredTool.from_function(
            func=write_files_instance.append_text,
            name="append_text",
            description="向文本文件追加内容。"
        ),
    ]

    return tools

