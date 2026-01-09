# -*- coding: utf-8 -*-
"""
人格管理器 (Persona Editor) - 新增模块
负责：人格的增删改查、详细数据预览
"""
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QMessageBox,
    QLabel, QGroupBox, QFormLayout, QLineEdit, QDoubleSpinBox
)
from PyQt6.QtCore import Qt


class PersonaEditor(QDialog):
    def __init__(self, io_manager, parent=None):
        super().__init__(parent)
        self.io_manager = io_manager
        self.setWindowTitle("人格矩阵管理中心 (Persona Matrix Center)")
        self.resize(900, 600)
        self.setStyleSheet("background-color: #1e1e1e; color: #e0e0e0;")
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # 左侧：列表
        left_layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["人格名称", "类型"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemClicked.connect(self.on_item_clicked)
        self.table.setStyleSheet("QTableWidget { border: 1px solid #333; gridline-color: #333; }")
        left_layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_del = QPushButton("🗑️ 删除人格")
        self.btn_del.clicked.connect(self.delete_persona)
        self.btn_del.setStyleSheet("background: #d32f2f; color: white; padding: 8px;")
        btn_layout.addWidget(self.btn_del)
        left_layout.addLayout(btn_layout)

        # 右侧：详情编辑器
        right_group = QGroupBox("🧬 人格基因详情")
        right_layout = QFormLayout(right_group)

        self.edit_name = QLineEdit()
        self.edit_desc = QLineEdit()

        # 维度编辑器
        self.spin_boxes = {}
        dimensions = ["逻辑性", "创造力", "情感度", "知识广度", "记忆深度", "执行力"]
        for dim in dimensions:
            sb = QDoubleSpinBox()
            sb.setRange(0.0, 1.0)
            sb.setSingleStep(0.1)
            self.spin_boxes[dim] = sb
            right_layout.addRow(f"{dim}:", sb)

        self.btn_save = QPushButton("💾 保存修改")
        self.btn_save.clicked.connect(self.save_changes)
        self.btn_save.setStyleSheet("background: #007acc; color: white; padding: 10px; margin-top: 20px;")

        right_layout.addRow("名称:", self.edit_name)
        right_layout.addRow("描述:", self.edit_desc)
        right_layout.addWidget(self.btn_save)

        layout.addLayout(left_layout, 1)
        layout.addWidget(right_group, 1)

    def load_data(self):
        self.table.setRowCount(0)
        personas = self.io_manager.scan_personas()
        for i, name in enumerate(personas):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem("自定义"))

    def on_item_clicked(self, item):
        row = item.row()
        name = self.table.item(row, 0).text()
        data = self.io_manager.load_persona(name)
        if data:
            self.edit_name.setText(data.get('name', name))
            self.edit_desc.setText(data.get('description', ''))
            dims = data.get('dimensions', {})
            for key, sb in self.spin_boxes.items():
                sb.setValue(dims.get(key, 0.5))
            self.current_editing_file = name

    def save_changes(self):
        if not hasattr(self, 'current_editing_file'):
            return

        new_dims = {k: sb.value() for k, sb in self.spin_boxes.items()}
        self.io_manager.save_persona(
            self.edit_name.text(),
            new_dims,
            self.edit_desc.text()
        )
        QMessageBox.information(self, "成功", "人格基因已重组并保存。")
        self.load_data()

    def delete_persona(self):
        row = self.table.currentRow()
        if row < 0:
            return

        name = self.table.item(row, 0).text()
        if not name:
            return

        reply = QMessageBox.question(
            self, "确认", f"确定销毁人格 [{name}] 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 修复：使用正确的路径获取方式
            personas_dir = self.io_manager.paths.directories['personas']
            path = os.path.join(personas_dir, f"{name}.json")

            # 或者如果上面不行，尝试这种方式：
            # path = os.path.join(self.io_manager.paths.directories.get('personas', 'personas'), f"{name}.json")

            try:
                if os.path.exists(path):
                    os.remove(path)
                    QMessageBox.information(self, "成功", f"人格 '{name}' 已删除")
                    self.load_data()  # 刷新列表
                else:
                    QMessageBox.warning(self, "警告", f"文件不存在: {path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")