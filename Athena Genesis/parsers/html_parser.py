# -*- coding: utf-8 -*-
"""
HTML文件解析器
优化版
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base_parser import BaseParser
from config.settings import SETTINGS

# 尝试全局导入，避免函数内重复导入
try:
    from bs4 import BeautifulSoup

    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


class HTMLParser(BaseParser):
    """HTML文件解析器"""

    def __init__(self) -> None:
        super().__init__()
        self.supported_extensions = SETTINGS.SUPPORTED_EXTENSIONS.get('html', ['.html', '.htm', '.xhtml'])
        self.parser_name = "HTMLParser"

    def can_parse(self, file_path: str) -> bool:
        """检查是否能解析HTML文件"""
        if not HAS_BS4:
            return False
        return Path(file_path).suffix.lower() in self.supported_extensions

    def parse(self, file_path: str) -> str:
        """解析HTML文件"""
        if not HAS_BS4:
            return "[需要安装 beautifulsoup4 库才能解析HTML文件]"

        try:
            # 宽容模式打开文件
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, 'html.parser')
            path_obj = Path(file_path)

            content_lines = [f"[HTML文件: {path_obj.name}]"]

            # 提取标题
            if soup.title and soup.title.string:
                content_lines.append(f"标题: {soup.title.string.strip()}")

            # 提取正文内容 - 优化逻辑
            text_elements = []

            # 定义提取规则：标签及其显示前缀
            extraction_rules = [
                ('h1', 'H1'), ('h2', 'H2'), ('h3', 'H3'),
                ('p', ''), ('li', '•'), ('td', '|'), ('th', '|')
            ]

            # 遍历提取，每种标签限制数量，防止大量无用信息
            for tag, prefix in extraction_rules:
                elements = soup.find_all(tag)
                count = 0
                for element in elements:
                    if count >= 20: break  # 每种标签最多取前20个

                    text = element.get_text().strip()
                    # 智能清洗：去除多余空白，忽略极短文本
                    text = re.sub(r'\s+', ' ', text)

                    if text and len(text) > 5:
                        display_text = f"{prefix}: {text}" if prefix else text
                        text_elements.append(display_text)
                        count += 1

            # 如果结构化提取内容太少，回退到提取所有文本
            if len(text_elements) < 3:
                all_text = soup.get_text(separator='\n')
                lines = [line.strip() for line in all_text.split('\n') if len(line.strip()) > 5]
                text_elements.extend(lines[:50])

            # 添加到结果，限制总行数
            content_lines.extend(text_elements[:200])

            # 提取链接
            links = soup.find_all('a', href=True)
            if links:
                content_lines.append(f"\n[发现 {len(links)} 个链接]")
                for link in links[:10]:
                    text = link.get_text().strip()
                    href = link['href']
                    # 如果没有文本，用href截断代替
                    display_text = text if text else (href[:30] + '...' if len(href) > 30 else href)
                    content_lines.append(f"{display_text} -> {href}")

            return "\n".join(content_lines)

        except Exception as e:
            return f"[HTML解析错误]: {str(e)}"