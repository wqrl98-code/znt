# -*- coding: utf-8 -*-
"""
Excel文件解析器
优化版
"""

import pandas as pd
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base_parser import BaseParser
from config.settings import SETTINGS


class ExcelParser(BaseParser):
    """Excel文件解析器"""

    def __init__(self) -> None:
        super().__init__()
        self.supported_extensions = SETTINGS.SUPPORTED_EXTENSIONS.get('excel', ['.xlsx', '.xls', '.xlsm'])
        self.parser_name = "ExcelParser"
        self.max_rows_to_show = 50
        self.max_columns_to_show = 10

    def can_parse(self, file_path: str) -> bool:
        """检查是否能解析Excel文件"""
        return Path(file_path).suffix.lower() in self.supported_extensions

    def parse(self, file_path: str) -> str:
        """解析Excel文件"""
        path_obj = Path(file_path)
        try:
            # 显式使用 ExcelFile 对象，提高多Sheet读取效率
            # engine=None 让 pandas 自动根据后缀选择 (openpyxl/xlrd)
            xls = pd.ExcelFile(file_path)
            sheet_names = xls.sheet_names

            content_lines = [f"[Excel文件: {path_obj.name}]"]
            content_lines.append(f"工作表数量: {len(sheet_names)}")
            content_lines.append(f"工作表列表: {', '.join(sheet_names)}")

            # 解析每个工作表
            # 限制处理的Sheet数量，防止文件过大卡死界面
            max_sheets = 5
            for i, sheet_name in enumerate(sheet_names):
                if i >= max_sheets:
                    content_lines.append(f"\n...剩余 {len(sheet_names) - max_sheets} 个工作表未显示")
                    break

                try:
                    # 读取单个Sheet
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    sheet_content = self._parse_sheet(sheet_name, df)
                    content_lines.extend(sheet_content)
                except Exception as e:
                    content_lines.append(f"[工作表解析错误 '{sheet_name}']: {str(e)}")

            # 显式关闭资源 (虽然 context manager 更好，但 ExcelFile 这种用法需注意)
            xls.close()

            return "\n".join(content_lines)

        except ImportError as e:
            return f"[Excel解析错误] 缺少依赖库 (如 openpyxl 或 xlrd): {str(e)}"
        except Exception as e:
            return f"[Excel解析错误]: {str(e)}"

    def _parse_sheet(self, sheet_name: str, df: pd.DataFrame) -> List[str]:
        """解析单个工作表"""
        lines = []
        lines.append(f"\n=== 工作表: {sheet_name} ===")
        lines.append(f"行数: {len(df)}, 列数: {len(df.columns)}")

        # 显示列名
        if not df.columns.empty:
            columns = list(df.columns)[:self.max_columns_to_show]
            lines.append(f"列名: {', '.join([str(c) for c in columns])}")
            if len(df.columns) > self.max_columns_to_show:
                lines.append(f"...(共{len(df.columns)}列)")

        # 显示数据行
        if not df.empty:
            lines.append("数据预览:")
            # 使用 head() 提高效率
            preview_df = df.head(self.max_rows_to_show)
            cols_to_show = df.columns[:self.max_columns_to_show]

            for i, row in preview_df.iterrows():
                row_values = []
                for col in cols_to_show:
                    val = row[col]
                    # 优化：处理日期类型
                    if isinstance(val, pd.Timestamp):
                        val_str = val.strftime('%Y-%m-%d %H:%M:%S')
                    elif pd.isna(val):
                        val_str = "NaN"
                    else:
                        val_str = str(val)

                    # 截断长文本
                    row_values.append(val_str[:30] + "..." if len(val_str) > 30 else val_str)

                lines.append(f"行{i + 1}: {' | '.join(row_values)}")

            if len(df) > self.max_rows_to_show:
                lines.append(f"...等 {len(df)} 行")

        return lines