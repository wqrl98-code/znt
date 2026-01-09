# core/brain_modules/athena_brain.py
# -*- coding: utf-8 -*-
"""
Athena Brain - 大脑总指挥部（合并修复版）
整合两个版本的功能，修复导入路径，保留所有方法
"""
from PyQt6.QtCore import QThread, QObject, pyqtSignal
# 🔥 关键：确保从 core 包导入 Commander
from core.commander import Commander


class AthenaBrain(QThread):
    # 定义全量信号（整合两个版本）
    log_signal = pyqtSignal(str)
    query_result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    mode_changed = pyqtSignal(str)
    token_signal = pyqtSignal(str)  # 从第二个版本添加

    def __init__(self, bus, io_manager, knowledge_base):
        super().__init__()
        self.bus = bus
        self.io_manager = io_manager
        self.knowledge_base = knowledge_base

        # 初始化总指挥
        self.commander = Commander(bus, io_manager, knowledge_base)

        # 转发信号
        self.commander.log_signal.connect(self.log_signal.emit)
        self.commander.query_result_signal.connect(self.query_result_signal.emit)
        self.commander.error_signal.connect(self.error_signal.emit)
        self.commander.status_signal.connect(self.status_signal.emit)
        self.commander.mode_changed.connect(self.mode_changed.emit)

        if hasattr(self.commander, 'token_signal'):
            self.commander.token_signal.connect(self.token_signal.emit)

        # 任务队列
        self.task_queue = self.commander.task_queue
        self.is_running = True

    def launch(self, user_input=None, config=None, payload=None, mode=None):
        """调用总指挥的launch方法（兼容两个版本）"""
        if config is None:
            config = {}
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

    # 从第二个版本添加的代理方法（支持 wait 参数）
    def start_thread(self):
        """启动线程（避免与QThread的start冲突）"""
        if not self.commander.isRunning():
            self.commander.start()

    def isRunning(self):
        """检查是否在运行"""
        return self.commander.isRunning()

    def wait_thread(self, *args, **kwargs):
        """等待线程结束"""
        return self.commander.wait(*args, **kwargs)

    def terminate_thread(self):
        """终止线程"""
        self.commander.terminate()