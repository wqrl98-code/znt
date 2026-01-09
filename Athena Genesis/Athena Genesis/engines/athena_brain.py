# core/brain_modules/athena_brain.py
# -*- coding: utf-8 -*-
"""
Athena Brain - 大脑总指挥部（精简版）
仅保留总指挥模块的实例化，功能分发到各个子模块
"""
from typing import TYPE_CHECKING
from PyQt6.QtCore import QThread, pyqtSignal

if TYPE_CHECKING:
    # 仅在类型检查时导入，避免循环导入问题
    from core.commander import Commander


class AthenaBrain(QThread):
    # 定义全量信号（与原来一致）
    log_signal = pyqtSignal(str)
    query_result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    mode_changed = pyqtSignal(str)

    def __init__(self, bus, io_manager, knowledge_base):
        super().__init__()
        self.bus = bus
        self.io_manager = io_manager
        self.knowledge_base = knowledge_base

        # 延迟导入，避免立即执行导致的循环依赖
        from core.commander import Commander

        # 初始化总指挥
        self.commander: 'Commander' = Commander(bus, io_manager, knowledge_base)

        # 转发信号
        self.commander.log_signal.connect(self.log_signal.emit)
        self.commander.query_result_signal.connect(self.query_result_signal.emit)
        self.commander.error_signal.connect(self.error_signal.emit)
        self.commander.status_signal.connect(self.status_signal.emit)
        self.commander.mode_changed.connect(self.mode_changed.emit)

        # 任务队列
        self.task_queue = self.commander.task_queue
        self.is_running = True

    def launch(self, user_input=None, config=None, payload=None, mode=None):
        """调用总指挥的launch方法"""
        return self.commander.launch(user_input, config, payload, mode)

    def set_mode(self, mode):
        """设置工作模式"""
        self.commander.set_mode(mode)

    def set_strategy(self, strategy):
        """设置写作策略"""
        self.commander.set_strategy(strategy)

    def set_temperature(self, temp):
        """设置思维温度"""
        self.commander.set_temperature(temp)

    def toggle_search(self, enabled):
        """切换联网搜索"""
        self.commander.toggle_search(enabled)

    def set_low_power_mode(self, enabled):
        """设置低功耗模式"""
        self.commander.set_low_power_mode(enabled)

    def get_performance_stats(self):
        """获取性能统计"""
        return self.commander.get_performance_stats()

    def thread_run(self):
        """调用总指挥的线程运行方法"""
        self.commander.thread_run()

    def run(self):
        """线程主入口"""
        self.thread_run()

    def stop(self):
        """停止线程"""
        self.commander.stop()
        self.wait()