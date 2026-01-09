# -*- coding: utf-8 -*-
"""
全局异步信号总线
"""

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from typing import Dict, Any, Optional
import traceback


class SignalBus(QObject):
    """全局异步信号总线"""

    # 系统信号
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    finish_signal = pyqtSignal(str)
    system_signal = pyqtSignal(dict)

    # 数据信号
    radar_signal = pyqtSignal(dict)
    plot_signal = pyqtSignal(dict)
    tree_signal = pyqtSignal(dict)
    knowledge_signal = pyqtSignal(dict)

    # 交互信号
    chat_signal = pyqtSignal(str)
    query_result_signal = pyqtSignal(dict)
    document_analysis_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._connected_slots = {}

    @pyqtSlot(str)
    def emit_log(self, message: str) -> None:
        """发射日志信号"""
        self.log_signal.emit(message)

    @pyqtSlot(str)
    def emit_error(self, error: str, details: Optional[str] = None) -> None:
        """发射错误信号"""
        error_msg = f"❌ {error}"
        if details:
            error_msg += f"\n详情: {details}"
        self.error_signal.emit(error_msg)

    @pyqtSlot(dict)
    def emit_plot_data(self, data: Dict[str, Any]) -> None:
        """发射绘图数据"""
        self.plot_signal.emit(data)

    @pyqtSlot(dict)
    def emit_document_analysis(self, filename: str, analysis: Dict[str, Any]) -> None:
        """发射文档分析结果"""
        self.document_analysis_signal.emit({
            "filename": filename,
            "analysis": analysis
        })

    def safe_emit(self, signal: pyqtSignal, *args, **kwargs) -> None:
        """安全发射信号，捕获异常"""
        try:
            signal.emit(*args, **kwargs)
        except Exception as e:
            self.emit_error(f"信号发射失败: {str(e)}", traceback.format_exc())