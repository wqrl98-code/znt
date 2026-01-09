# -*- coding: utf-8 -*-
"""
解析器基类
优化版
"""

import os
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Union
from config.settings import SETTINGS


class BaseParser(ABC):
    """解析器基类 - 定义所有文件解析器的标准接口"""

    def __init__(self) -> None:
        self.supported_extensions: List[str] = []
        self.parser_name: str = "BaseParser"
        self._dependencies_checked: bool = False

    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """检查是否能解析文件"""
        # 优化：统一转为小写并使用 Path 获取后缀
        return Path(file_path).suffix.lower() in self.supported_extensions

    @abstractmethod
    def parse(self, file_path: str) -> str:
        """解析文件内容"""
        pass

    def check_dependencies(self) -> Tuple[bool, str]:
        """检查依赖是否满足 (子类可覆盖)"""
        return True, "所有依赖已满足"

    def safe_parse(self, file_path: str) -> str:
        """
        安全解析，捕获并格式化异常
        优化：增加对 MemoryError 的捕获，使用 pathlib
        """
        path_obj = Path(file_path)

        try:
            if not path_obj.exists():
                return f"[错误] 文件不存在: {file_path}"

            if not self.can_parse(file_path):
                return f"[错误] {self.parser_name} 不支持的文件格式: {path_obj.suffix}"

            # 检查文件大小 (需确保 SETTINGS 有 MAX_FILE_SIZE，否则使用默认值 50MB)
            max_size = getattr(SETTINGS, 'MAX_FILE_SIZE', 50 * 1024 * 1024)
            file_size = path_obj.stat().st_size

            if file_size > max_size:
                return f"[警告] 文件过大 ({file_size / 1024 / 1024:.2f}MB > {max_size / 1024 / 1024:.0f}MB)，建议拆分处理"

            # 执行具体解析逻辑
            content = self.parse(file_path)
            return content

        except MemoryError:
            return f"[严重错误] {self.parser_name}: 文件过大导致内存溢出"
        except Exception as e:
            # 记录异常类名，提供更清晰的调试信息
            return f"[解析错误] {self.parser_name} ({type(e).__name__}): {str(e)}"

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """获取文件基础元数据"""
        try:
            path_obj = Path(file_path)
            stat = path_obj.stat()
            return {
                "filename": path_obj.name,
                "path": str(path_obj.absolute()),
                "size_bytes": stat.st_size,
                "size_human": f"{stat.st_size / 1024:.2f} KB",
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "extension": path_obj.suffix.lower()
            }
        except Exception as e:
            return {"error": f"无法获取文件信息: {str(e)}"}