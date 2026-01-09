# -*- coding: utf-8 -*-
"""
PDF文件解析器 - 报纸排版修复版
"""
import os
import re
from .base_parser import BaseParser


class PDFParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.pdf']
        self.parser_name = "PDFParser"

    def can_parse(self, file_path: str) -> bool:
        return file_path.lower().endswith('.pdf')

    def parse(self, file_path: str) -> str:
        if not os.path.exists(file_path): return ""
        print(f"📖 解析PDF: {os.path.basename(file_path)}")

        text_content = []
        try:
            import pdfplumber
            # 关键：detect_vertical 用于报纸分栏
            laparams = {"detect_vertical": True, "all_texts": True}

            with pdfplumber.open(file_path, laparams=laparams) as pdf:
                for page in pdf.pages:
                    # x_tolerance=2 防止跨栏合并
                    text = page.extract_text(x_tolerance=2, y_tolerance=3, layout=False)
                    if text: text_content.append(text)

            full_text = "\n\n".join(text_content)
            # 清洗
            full_text = re.sub(r'\d+\s+\d+\s+obj', '', full_text)
            full_text = re.sub(r'endobj', '', full_text)
            # 修复中文换行问题
            full_text = re.sub(r'([\u4e00-\u9fa5])\n([\u4e00-\u9fa5])', r'\1\2', full_text)

            return full_text.strip()
        except Exception as e:
            return f"[PDF解析失败] {str(e)}"