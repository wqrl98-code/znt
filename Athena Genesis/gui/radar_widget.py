# -*- coding: utf-8 -*-
"""
雷达图组件 - 最终修复版 (整合 1.txt 和 2.txt)
修复：
1. 数据为小数时显示为一个点的问题 (增加了半径映射) ✅
2. 无法显示数据、线条不刷新的问题 ✅
3. 适配 EnhancedMimicryEngine 的字典数据流 ✅
4. AttributeError: 'EnhancedHexagonRadar' object has no attribute 'update_data' ✅
"""
import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QBrush, QPen, QColor, QPolygonF, QFont
from PyQt6.QtCore import Qt, QPointF


class EnhancedHexagonRadar(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(300, 300)
        self.setStyleSheet("background-color: transparent;")

        # 🔥 统一维度定义 (整合两个版本)
        # 使用 4.txt 的维度名称，但保持 3.txt 的适配性
        self.labels = ["逻辑性", "创造力", "同理心", "知识广度", "记忆深度", "执行力"]

        # 🔥 统一数据存储方式
        # 保持 4.txt 的默认数据格式 (0.0-1.0)，但兼容 3.txt 的 0-100 格式
        self.data = {l: 0.1 for l in self.labels}  # 默认给0.1防止完全不可见

        # 🔥 视觉配置 (整合两个版本的优点)
        self.line_color = QColor(0, 255, 204, 180)  # 青色边框 (使用3.txt的颜色)
        self.fill_color = QColor(0, 255, 204, 40)  # 半透明青色填充 (使用3.txt的填充)
        self.bg_color = QColor(60, 60, 60, 100)  # 网格背景 (保持4.txt的深色背景)
        self.text_color = QColor(220, 220, 220)  # 文字颜色 (使用4.txt的颜色)
        self.value_color = QColor(0, 255, 204)  # 数值颜色 (使用3.txt的青色)

    def set_data(self, metrics: dict):
        """
        🔥 增强版：接收数据并刷新
        兼容两种数据格式：
        1. metrics: {"逻辑性": 0.85, ...} (范围 0.0 - 1.0) - 4.txt 格式
        2. metrics: {"Logic": 85, "Creativity": 60...} (范围 0-100) - 3.txt 格式
        3. 自动适配 EnhancedMimicryEngine 的字典数据流
        """
        if not metrics:
            return

        # 🔥 关键修复：统一数据格式处理
        for key in self.labels:
            raw_val = metrics.get(key, 0.2)

            # 🔥 处理 3.txt 的维度名称映射 (兼容性修复)
            if key == "逻辑性" and "Logic" in metrics:
                raw_val = metrics.get("Logic", 0.2)
            elif key == "创造力" and "Creativity" in metrics:
                raw_val = metrics.get("Creativity", 0.2)
            elif key == "同理心" and "Emotion" in metrics:
                raw_val = metrics.get("Emotion", 0.2)
            elif key == "知识广度" and "Critical" in metrics:
                raw_val = metrics.get("Critical", 0.2)
            elif key == "记忆深度" and "Struct" in metrics:
                raw_val = metrics.get("Struct", 0.2)
            elif key == "执行力" and "Depth" in metrics:
                raw_val = metrics.get("Depth", 0.2)

            # 🔥 数据归一化处理
            if not isinstance(raw_val, (int, float)):
                raw_val = 0.2
            else:
                # 如果数据在 0-100 范围内，转换为 0.0-1.0
                if raw_val > 1.0 and raw_val <= 100.0:
                    raw_val = raw_val / 100.0
                # 如果数据为0，给一个最小值避免图形崩坏
                elif raw_val == 0:
                    raw_val = 0.05

            # 🔥 强制限制在 0.05 ~ 1.0 之间，防止图形崩坏
            self.data[key] = max(0.05, min(1.0, float(raw_val)))

        self.update()  # 触发重绘

    # ==========================================================
    # 🔥 核心修复：新增 update_data 方法 (来自2.txt)
    # ==========================================================
    def update_data(self, new_data: dict):
        """
        接收新数据并刷新界面
        :param new_data: 包含维度数据的字典，例如 {"创造力": 0.8, ...}
        """
        if not new_data:
            return

        # 更新内部数据
        # 遍历我们的固定标签，看看新数据里有没有对应的项
        for label in self.labels:
            if label in new_data:
                try:
                    val = float(new_data[label])
                    # 兼容性处理：如果传入的是 0-100，转为 0.0-1.0
                    if val > 1.0:
                        val = val / 100.0
                    # 限制范围
                    val = max(0.0, min(1.0, val))
                    self.data[label] = val
                except (ValueError, TypeError):
                    pass

        # 强制触发 paintEvent 重绘
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. 计算中心点与半径 (使用 4.txt 的计算方式)
        w, h = self.width(), self.height()
        center = QPointF(w / 2, h / 2)
        radius = min(w, h) / 2 * 0.75  # 留出文字边距

        # 2. 绘制背景网格 (整合两个版本)
        # 使用 4.txt 的 5层同心六边形，但使用 3.txt 的虚线风格
        painter.setPen(QPen(self.bg_color, 1, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        for i in range(5, 0, -1):
            ratio = i / 5.0
            self._draw_hexagon(painter, center, radius * ratio)

        # 3. 绘制从中心到顶点的连线 (来自 3.txt 的改进)
        painter.setPen(QPen(self.bg_color, 1, Qt.PenStyle.SolidLine))
        angle_step = 360 / 6
        for i in range(6):
            angle = math.radians(i * angle_step - 90)
            x = center.x() + radius * math.cos(angle)
            y = center.y() + radius * math.sin(angle)
            painter.drawLine(center, QPointF(x, y))

        # 4. 绘制数据区域 (核心修复)
        painter.setPen(QPen(self.line_color, 2))
        painter.setBrush(QBrush(self.fill_color))

        poly = QPolygonF()

        for i, label in enumerate(self.labels):
            angle = math.radians(i * angle_step - 90)  # -90度让第一个点在正上方
            val = self.data.get(label, 0.1)

            # 🔥🔥🔥 核心修复：确保值乘以半径 (解决小数显示为一个点的问题)
            # ✅ 关键修复：值(0.8) * 半径(100px) = 80px长度
            r_val = radius * val

            x = center.x() + r_val * math.cos(angle)
            y = center.y() + r_val * math.sin(angle)
            poly.append(QPointF(x, y))

        painter.drawPolygon(poly)

        # 5. 🔥 绘制中心点 (来自 3.txt 的改进)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawEllipse(center, 3, 3)

        # 6. 🔥 绘制文字标签 (整合两个版本的优点)
        painter.setFont(QFont("Microsoft YaHei", 9, QFont.Weight.Bold))

        for i, label in enumerate(self.labels):
            angle = math.radians(i * angle_step - 90)

            # 🔥 标签位置计算 (使用 4.txt 的距离，稍微调整)
            label_radius = radius * 1.2  # 稍微靠近一点

            # 🔥 主标签位置
            x = center.x() + label_radius * math.cos(angle)
            y = center.y() + label_radius * math.sin(angle)

            # 获取当前数值 (转换为百分比显示)
            value = self.data.get(label, 0.1)
            value_percent = int(value * 100)

            # 🔥 绘制标签文字 (使用 4.txt 的计算方式，但显示两行)
            text_rect = painter.fontMetrics().boundingRect(label)

            # 标签位置微调
            label_x = x - text_rect.width() / 2
            label_y = y - text_rect.height() / 4

            # 绘制标签 (白色)
            painter.setPen(QPen(self.text_color, 1))
            painter.drawText(QPointF(label_x, label_y), label)

            # 🔥 绘制数值 (青色，来自 3.txt)
            value_text = f"{value_percent}%"
            value_rect = painter.fontMetrics().boundingRect(value_text)

            # 数值在标签下方
            value_x = x - value_rect.width() / 2
            value_y = y + value_rect.height()

            painter.setPen(QPen(self.value_color, 1))
            painter.drawText(QPointF(value_x, value_y), value_text)

    def _draw_hexagon(self, painter, center, r, fill=False):
        """绘制六边形 (整合两个版本)"""
        poly = QPolygonF()
        for i in range(6):
            angle = math.radians(i * 60 - 90)
            x = center.x() + r * math.cos(angle)
            y = center.y() + r * math.sin(angle)
            poly.append(QPointF(x, y))

        if fill:
            painter.drawPolygon(poly)
        else:
            painter.drawPolyline(poly)
            # 闭合最后一条线
            painter.drawLine(poly.last(), poly.first())