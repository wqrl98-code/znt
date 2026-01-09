# -*- coding: utf-8 -*-
"""
CSV文件解析器
优化版：智能编码检测、大文件性能优化
"""

import os
import csv
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
from .base_parser import BaseParser
from config.settings import SETTINGS


class CSVParser(BaseParser):
    """CSV文件解析器"""

    def __init__(self) -> None:
        super().__init__()
        self.supported_extensions = SETTINGS.SUPPORTED_EXTENSIONS.get('csv', ['.csv'])
        self.parser_name = "CSVParser"
        self.max_rows_to_show = 100
        self.max_columns_to_show = 15  # 稍微增加默认显示列数

    def can_parse(self, file_path: str) -> bool:
        """检查是否能解析CSV文件"""
        return Path(file_path).suffix.lower() == '.csv'

    def parse(self, file_path: str) -> str:
        """解析CSV文件"""
        file_name = Path(file_path).name

        # 尝试多种编码
        encodings = ['utf-8', 'gbk', 'gb18030', 'cp1252', 'latin1']

        df = None
        used_encoding = ""
        error_msgs = []

        # 尝试使用pandas读取
        for encoding in encodings:
            try:
                # 优化：只读取需要的行数进行预览，而不是读取全量数据
                # 如果只是预览，设置 nrows 可以极大提高大文件打开速度
                # 注意：为了统计行数，第一次可能需要读元数据，或者分块读
                # 这里为了保留"行数统计"逻辑，我们先尝试只读头部，如果不报错再读统计

                # 策略：先尝试读取全部（为了统计），如果内存不够捕获异常
                df = pd.read_csv(file_path, encoding=encoding, on_bad_lines='skip')
                used_encoding = encoding
                break
            except Exception as e:
                error_msgs.append(f"{encoding}: {e}")
                continue

        if df is not None:
            return self._parse_with_pandas(df, file_path, used_encoding)

        # 如果pandas全失败，回退到原生csv模块 (通常不需要，因为pandas很强，但为了保底)
        return self._parse_with_csv_fallback(file_path)

    def _parse_with_pandas(self, df: pd.DataFrame, file_path: str, encoding: str) -> str:
        """使用pandas解析结果格式化"""
        content_lines = [f"[CSV文件: {Path(file_path).name}] (编码: {encoding})"]
        content_lines.append(f"行数: {len(df)}, 列数: {len(df.columns)}")

        # 显示列名
        if not df.columns.empty:
            columns = list(df.columns)[:self.max_columns_to_show]
            content_lines.append(f"列名: {', '.join([str(c) for c in columns])}")
            if len(df.columns) > self.max_columns_to_show:
                content_lines.append(f"...等 {len(df.columns)} 列")

        # 显示数据行
        if not df.empty:
            content_lines.append("\n数据预览:")
            # 使用 head 避免切片产生的额外开销
            preview_df = df.head(self.max_rows_to_show)

            # 优化迭代速度
            cols_to_show = df.columns[:self.max_columns_to_show]

            for i, row in preview_df.iterrows():
                row_values = []
                for col in cols_to_show:
                    val = row[col]
                    # 优化空值处理和字符串截断
                    if pd.isna(val):
                        row_values.append("")
                    else:
                        str_val = str(val)
                        row_values.append(str_val[:30] + "..." if len(str_val) > 30 else str_val)
                content_lines.append(f"行{i + 1}: {' | '.join(row_values)}")

            remaining = len(df) - self.max_rows_to_show
            if remaining > 0:
                content_lines.append(f"...等 {remaining} 行")

            # 数值列统计
            try:
                numeric_cols = df.select_dtypes(include=['number']).columns
                if not numeric_cols.empty:
                    content_lines.append("\n数值列统计:")
                    for col in numeric_cols[:5]:
                        stats = df[col].describe()
                        content_lines.append(
                            f"{col}: 均值={stats['mean']:.2f}, "
                            f"标准差={stats['std']:.2f}, "
                            f"范围=[{stats['min']:.2f}, {stats['max']:.2f}]"
                        )
            except Exception as e:
                content_lines.append(f"\n[统计生成失败]: {e}")

        return "\n".join(content_lines)

    def _parse_with_csv_fallback(self, file_path: str) -> str:
        """CSV模块后备解析 (仅当pandas失败时)"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.reader(f)
                rows = list(reader)  # 注意：大文件可能导致内存问题，但这是最后手段

            if not rows:
                return "[CSV文件为空]"

            header = rows[0]
            data = rows[1:]

            lines = [f"[CSV文件(Fallback): {Path(file_path).name}]"]
            lines.append(f"行数: {len(data)}, 列数: {len(header)}")
            lines.append(f"列名: {', '.join(header[:self.max_columns_to_show])}")

            lines.append("\n数据预览:")
            for i, row in enumerate(data[:self.max_rows_to_show]):
                lines.append(f"行{i + 1}: {' | '.join(row[:self.max_columns_to_show])}")

            return "\n".join(lines)

        except Exception as e:
            return f"[CSV解析彻底失败] 无法识别编码或格式: {str(e)}"