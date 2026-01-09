# -*- coding: utf-8 -*-
"""
系统监控器 - 合并修复版
整合系统监控功能并修复线程停止问题
"""

import os
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

# 改为相对导入或条件导入
try:
    from config.settings import SETTINGS
except ImportError:
    SETTINGS = {}

try:
    from PyQt6.QtCore import QObject, pyqtSignal

    HAS_PYQT6 = True
except ImportError:
    # 创建一个虚拟的QObject和pyqtSignal用于非Qt环境
    class QObject:
        def __init__(self):
            pass


    def pyqtSignal(*args, **kwargs):
        class DummySignal:
            def emit(self, *args):
                pass

            def connect(self, *args):
                pass

        return DummySignal()


    HAS_PYQT6 = False


@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: str
    cpu_usage: float
    memory_usage: float
    memory_total: float  # GB
    memory_used: float  # GB
    disk_usage: float
    gpu_usage: float
    gpu_memory_usage: float
    process_count: int
    thread_count: int
    network_io: Dict[str, float] = field(default_factory=dict)
    disk_io: Dict[str, float] = field(default_factory=dict)


class SystemMonitor(QObject):
    """系统监控器 - 合并修复版"""

    # 信号定义
    update_signal = pyqtSignal(dict)
    metrics_update_signal = pyqtSignal(SystemMetrics)

    def __init__(self, interval=2):
        super().__init__()
        self.interval = interval
        self._is_running = False
        self._thread = None

        # 依赖检查
        self.has_psutil = True
        self.has_gputil = False
        self._init_dependencies()

        # 历史数据
        self.history: List[SystemMetrics] = []
        self.max_history = 100

        # 进程信息
        self.pid = os.getpid()

        # 线程锁
        self._lock = threading.Lock()

        # 线程停止事件
        self._stop_event = threading.Event()

    def _init_dependencies(self) -> None:
        """初始化依赖"""
        try:
            import psutil
            self.has_psutil = True
        except ImportError:
            self.has_psutil = False

        try:
            import GPUtil
            self.has_gputil = True
        except ImportError:
            self.has_gputil = False

    def start(self):
        """启动监控线程"""
        if self._is_running:
            return
        self._is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """🔥 修复：停止监控线程"""
        self._is_running = False
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            # 等待线程结束，设置超时
            self._thread.join(timeout=1.0)

            # 如果线程仍然存活，尝试中断
            if self._thread.is_alive():
                print("警告：监控线程未能正常停止")

    def _monitor_loop(self):
        """监控循环"""
        while self._is_running and not self._stop_event.is_set():
            try:
                # 获取系统指标
                metrics = self.get_system_metrics()

                # 发送完整指标信号
                if HAS_PYQT6:
                    self.metrics_update_signal.emit(metrics)

                # 发送简化指标信号（兼容原信号）
                if HAS_PYQT6:
                    self.update_signal.emit({
                        "cpu": metrics.cpu_usage,
                        "memory": metrics.memory_usage
                    })
                else:
                    # 非Qt环境下，直接打印或处理数据
                    print(f"CPU: {metrics.cpu_usage:.1f}%, Memory: {metrics.memory_usage:.1f}%")

                # 使用事件等待，可以响应停止事件
                self._stop_event.wait(self.interval)

            except Exception as e:
                print(f"监控循环异常: {e}")
                break

        print("监控线程已停止")

    def get_system_metrics(self) -> SystemMetrics:
        """获取系统指标"""
        metrics = SystemMetrics(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            cpu_usage=0,
            memory_usage=0,
            memory_total=0,
            memory_used=0,
            disk_usage=0,
            gpu_usage=0,
            gpu_memory_usage=0,
            process_count=0,
            thread_count=0,
            network_io={},
            disk_io={}
        )

        if self.has_psutil:
            metrics = self._get_psutil_metrics(metrics)

        if self.has_gputil:
            metrics = self._get_gpu_metrics(metrics)

        # 添加到历史（线程安全）
        with self._lock:
            self.history.append(metrics)
            if len(self.history) > self.max_history:
                self.history.pop(0)

        return metrics

    def _get_psutil_metrics(self, metrics: SystemMetrics) -> SystemMetrics:
        """使用psutil获取指标"""
        try:
            import psutil

            # CPU使用率
            metrics.cpu_usage = psutil.cpu_percent(interval=0.1)

            # 内存使用情况
            memory = psutil.virtual_memory()
            metrics.memory_usage = memory.percent
            metrics.memory_total = memory.total / (1024 ** 3)  # GB
            metrics.memory_used = memory.used / (1024 ** 3)  # GB

            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            metrics.disk_usage = disk.percent

            # 进程和线程数
            metrics.process_count = len(psutil.pids())
            metrics.thread_count = psutil.cpu_count(logical=True)

            # 网络IO
            net_io = psutil.net_io_counters()
            metrics.network_io = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }

            # 磁盘IO
            disk_io = psutil.disk_io_counters()
            metrics.disk_io = {
                "read_count": disk_io.read_count,
                "write_count": disk_io.write_count,
                "read_bytes": disk_io.read_bytes,
                "write_bytes": disk_io.write_bytes
            }

        except Exception as e:
            print(f"获取系统指标失败: {e}")

        return metrics

    def _get_gpu_metrics(self, metrics: SystemMetrics) -> SystemMetrics:
        """获取GPU指标"""
        try:
            import GPUtil

            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # 取第一个GPU
                metrics.gpu_usage = gpu.load * 100
                metrics.gpu_memory_usage = gpu.memoryUtil * 100

        except Exception as e:
            print(f"获取GPU指标失败: {e}")

        return metrics

    def get_process_metrics(self) -> Dict[str, Any]:
        """获取当前进程指标"""
        if not self.has_psutil:
            return {}

        try:
            import psutil

            process = psutil.Process(self.pid)
            with process.oneshot():
                return {
                    "pid": self.pid,
                    "name": process.name(),
                    "cpu_percent": process.cpu_percent(interval=0.1),
                    "memory_percent": process.memory_percent(),
                    "memory_rss_mb": process.memory_info().rss / (1024 ** 2),
                    "memory_vms_mb": process.memory_info().vms / (1024 ** 2),
                    "num_threads": process.num_threads(),
                    "num_fds": len(process.open_files()),
                    "status": process.status(),
                    "create_time": datetime.fromtimestamp(process.create_time()).strftime(
                        "%Y-%m-%d %H:%M:%S"),
                    "exe": process.exe()
                }

        except Exception as e:
            print(f"获取进程指标失败: {e}")
            return {}

    def get_metrics_summary(self) -> Dict[str, str]:
        """获取指标摘要"""
        metrics = self.get_system_metrics()
        process_metrics = self.get_process_metrics()

        summary = {
            "CPU使用率": f"{metrics.cpu_usage:.1f}%",
            "内存使用率": f"{metrics.memory_usage:.1f}%",
            "内存使用": f"{metrics.memory_used:.1f} / {metrics.memory_total:.1f} GB",
            "磁盘使用率": f"{metrics.disk_usage:.1f}%",
            "GPU使用率": f"{metrics.gpu_usage:.1f}%",
            "GPU显存使用率": f"{metrics.gpu_memory_usage:.1f}%",
            "系统进程数": str(metrics.process_count),
            "系统线程数": str(metrics.thread_count),
            "监控时间": metrics.timestamp
        }

        if process_metrics:
            summary.update({
                "进程CPU": f"{process_metrics.get('cpu_percent', 0):.1f}%",
                "进程内存": f"{process_metrics.get('memory_percent', 0):.1f}%",
                "进程线程数": str(process_metrics.get('num_threads', 0))
            })

        return summary

    def get_history_trend(self, metric_name: str) -> List[float]:
        """获取历史趋势数据（线程安全）"""
        with self._lock:
            if not self.history:
                return []

            values = []
            for metrics in self.history:
                if hasattr(metrics, metric_name):
                    values.append(getattr(metrics, metric_name))

            return values

    def is_system_healthy(self) -> Tuple[bool, str]:
        """检查系统健康状态"""
        metrics = self.get_system_metrics()
        warnings = []

        # CPU检查
        if metrics.cpu_usage > 90:
            warnings.append(f"CPU使用率过高: {metrics.cpu_usage:.1f}%")

        # 内存检查
        if metrics.memory_usage > 90:
            warnings.append(f"内存使用率过高: {metrics.memory_usage:.1f}%")

        # 磁盘检查
        if metrics.disk_usage > 95:
            warnings.append(f"磁盘空间不足: {metrics.disk_usage:.1f}%")

        if warnings:
            return False, "; ".join(warnings)

        return True, "系统运行正常"

    def get_simple_metrics(self) -> Dict[str, float]:
        """获取简化指标（兼容旧接口）"""
        metrics = self.get_system_metrics()
        return {
            "cpu": metrics.cpu_usage,
            "memory": metrics.memory_usage,
            "disk": metrics.disk_usage,
            "gpu": metrics.gpu_usage
        }

    def is_running(self) -> bool:
        """检查监控是否在运行"""
        return self._is_running


# 非Qt环境下的简单使用示例
if __name__ == "__main__" and not HAS_PYQT6:
    monitor = SystemMonitor(interval=1)
    monitor.start()

    try:
        # 运行10秒后停止
        time.sleep(10)
    finally:
        monitor.stop()
        print("监控器已停止")