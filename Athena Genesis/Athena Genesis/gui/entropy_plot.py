# -*- coding: utf-8 -*-
"""
量子熵流图 - 崩溃修复版
"""
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
from PyQt6.QtCore import pyqtSlot, Qt


class EnhancedQuantumEntropyPlot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.max_points = 100
        self.entropy_data = np.zeros(self.max_points, dtype=float)
        self.cpu_data = np.zeros(self.max_points, dtype=float)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#1a1a1a')
        self.plot_widget.setYRange(0, 100)
        self.plot_widget.setMouseEnabled(x=False, y=False)  # 禁鼠标防止崩溃
        self.plot_widget.hideButtons()

        self.entropy_curve = self.plot_widget.plot(pen=pg.mkPen('#00e5ff', width=2))
        self.cpu_curve = self.plot_widget.plot(pen=pg.mkPen('#ff4081', width=1, style=Qt.PenStyle.DashLine))
        layout.addWidget(self.plot_widget)

    @pyqtSlot(dict)
    def update_data_safe(self, data):
        """线程安全更新"""
        try:
            cpu = float(data.get('cpu', 0.0) or 0.0)
            ent = float(data.get('entropy', 0.0) or 0.0)

            # 过滤 NaN
            if np.isnan(cpu): cpu = 0.0
            if np.isnan(ent): ent = 0.0

            self.cpu_data[:-1] = self.cpu_data[1:]
            self.cpu_data[-1] = cpu
            self.entropy_data[:-1] = self.entropy_data[1:]
            self.entropy_data[-1] = ent

            self.cpu_curve.setData(self.cpu_data)
            self.entropy_curve.setData(self.entropy_data)
        except Exception:
            pass  # 忽略绘图错误，防止闪退