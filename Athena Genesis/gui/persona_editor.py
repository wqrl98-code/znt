# -*- coding: utf-8 -*-
"""
完整人格管理器 (Persona Editor) - 合并增强版
功能：人格的增删改查、详细数据预览、创建新人格
"""
import os
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QMessageBox,
    QLabel, QGroupBox, QFormLayout, QLineEdit, QDoubleSpinBox,
    QTextEdit, QFrame, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal


class PersonaEditor(QDialog):
    """完整人格管理器 - 合并增强版"""
    # 信号定义
    saved_signal = pyqtSignal(str)  # 旧版信号兼容
    persona_saved = pyqtSignal(str)  # 新版信号兼容
    persona_deleted = pyqtSignal(str)  # 人格删除信号
    persona_updated = pyqtSignal(str)  # 人格更新信号

    def __init__(self, io_manager=None, knowledge_base=None, parent=None):
        super().__init__(parent)
        self.io_manager = io_manager
        self.knowledge_base = knowledge_base
        self.current_editing_file = None
        self.setWindowTitle("人格矩阵管理中心 (Persona Matrix Center)")
        self.resize(1000, 700)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QGroupBox {
                border: 2px solid #3c3c3c;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #4fc3f7;
            }
        """)

        # 初始化路径
        self.init_paths()
        self.init_ui()
        self.load_data()

    def init_paths(self):
        """初始化文件路径"""
        # 如果io_manager存在，使用其路径配置
        if self.io_manager and hasattr(self.io_manager, 'paths'):
            self.personas_dir = self.io_manager.paths.directories.get('personas', 'personas')
        else:
            # 默认路径
            self.personas_dir = os.path.join(os.getcwd(), "ATHENA_WORKSPACE", "Database", "Personas")

        # 确保目录存在
        if not os.path.exists(self.personas_dir):
            os.makedirs(self.personas_dir)
            print(f"📁 创建人格目录: {self.personas_dir}")

    def init_ui(self):
        """初始化用户界面"""
        main_layout = QHBoxLayout(self)

        # ===== 左侧：人格列表区域 =====
        left_group = QGroupBox("👥 人格列表")
        left_layout = QVBoxLayout(left_group)

        # 搜索框
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索人格...")
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #555;
                border-radius: 4px;
                background: #2d2d2d;
            }
        """)
        search_layout.addWidget(self.search_input)
        left_layout.addLayout(search_layout)

        # 人格表格
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["人格名称", "类型", "描述"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemClicked.connect(self.on_item_clicked)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #333;
                gridline-color: #333;
                background: #252525;
                alternate-background-color: #2a2a2a;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #0d47a1;
            }
        """)
        self.table.setAlternatingRowColors(True)
        left_layout.addWidget(self.table)

        # 操作按钮
        btn_layout = QHBoxLayout()

        self.btn_new = QPushButton("🆕 新建人格")
        self.btn_new.clicked.connect(self.create_new_persona)
        self.btn_new.setStyleSheet("""
            QPushButton {
                background: #43a047;
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #388e3c;
            }
        """)

        self.btn_del = QPushButton("🗑️ 删除人格")
        self.btn_del.clicked.connect(self.delete_persona)
        self.btn_del.setStyleSheet("""
            QPushButton {
                background: #d32f2f;
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #c62828;
            }
        """)

        self.btn_refresh = QPushButton("🔄 刷新列表")
        self.btn_refresh.clicked.connect(self.load_data)
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background: #0288d1;
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #0277bd;
            }
        """)

        btn_layout.addWidget(self.btn_new)
        btn_layout.addWidget(self.btn_del)
        btn_layout.addWidget(self.btn_refresh)
        left_layout.addLayout(btn_layout)

        # ===== 右侧：详情编辑区域 =====
        right_group = QGroupBox("🧬 人格基因编辑器")
        right_layout = QVBoxLayout(right_group)

        # 使用标签页组织不同类型的设置
        self.tab_widget = QTabWidget()

        # 标签页1: 基本信息
        tab_basic = QWidget()
        basic_layout = QFormLayout(tab_basic)

        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("输入人格名称...")
        self.edit_name.setStyleSheet("padding: 6px;")

        self.edit_desc = QTextEdit()
        self.edit_desc.setPlaceholderText("描述这个人格的功能和特点...")
        self.edit_desc.setMaximumHeight(80)
        self.edit_desc.setStyleSheet("padding: 6px;")

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText(
            "在这里输入系统指令(System Prompt)...\n例如：你是一个Python专家，你的回答必须简洁专业...")
        self.prompt_input.setMinimumHeight(150)
        self.prompt_input.setStyleSheet("padding: 6px; font-family: 'Consolas', monospace;")

        self.style_input = QLineEdit()
        self.style_input.setPlaceholderText("例如：幽默、严谨、温柔、直接...")
        self.style_input.setStyleSheet("padding: 6px;")

        basic_layout.addRow("🔹 名称:", self.edit_name)
        basic_layout.addRow("🔹 描述:", self.edit_desc)
        basic_layout.addRow("🧠 系统指令:", self.prompt_input)
        basic_layout.addRow("🎨 说话风格:", self.style_input)

        # 标签页2: 人格维度
        tab_dimensions = QWidget()
        dim_layout = QFormLayout(tab_dimensions)

        # 维度编辑器 - 使用两组维度
        dim_group = QGroupBox("人格六维属性 (0.0-1.0)")
        dim_group_layout = QFormLayout(dim_group)

        self.spin_boxes = {}
        dimensions_v1 = ["逻辑性", "创造力", "情感度", "知识广度", "记忆深度", "执行力"]
        dimensions_v2 = ["creativity", "logic", "empathy", "knowledge", "humor", "bias"]

        # 创建第一组维度
        for dim in dimensions_v1:
            sb = QDoubleSpinBox()
            sb.setRange(0.0, 1.0)
            sb.setSingleStep(0.1)
            sb.setDecimals(2)
            sb.setValue(0.5)
            sb.setStyleSheet("padding: 4px;")
            self.spin_boxes[dim] = sb
            dim_group_layout.addRow(f"{dim}:", sb)

        dim_layout.addWidget(dim_group)
        self.tab_widget.addTab(tab_basic, "基本信息")
        self.tab_widget.addTab(tab_dimensions, "人格维度")

        right_layout.addWidget(self.tab_widget)

        # 保存按钮
        self.btn_save = QPushButton("💾 保存人格")
        self.btn_save.clicked.connect(self.save_changes)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background: linear-gradient(to right, #007acc, #005a9e);
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover {
                background: linear-gradient(to right, #0063b1, #004578);
            }
            QPushButton:disabled {
                background: #555;
                color: #999;
            }
        """)
        right_layout.addWidget(self.btn_save)

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #888; padding: 5px;")
        right_layout.addWidget(self.status_label)

        # ===== 添加到主布局 =====
        main_layout.addWidget(left_group, 1)
        main_layout.addWidget(right_group, 1)

    def load_data(self):
        """加载人格数据到表格"""
        try:
            self.table.setRowCount(0)

            # 获取人格文件列表
            personas = self.scan_personas()

            for i, name in enumerate(personas):
                data = self.load_persona_file(name)
                if data:
                    self.table.insertRow(i)
                    self.table.setItem(i, 0, QTableWidgetItem(data.get('name', name)))
                    self.table.setItem(i, 1, QTableWidgetItem(self.get_persona_type(data)))
                    desc = data.get('description', '')
                    if len(desc) > 50:
                        desc = desc[:50] + "..."
                    self.table.setItem(i, 2, QTableWidgetItem(desc))

            self.status_label.setText(f"已加载 {len(personas)} 个人格")

        except Exception as e:
            self.status_label.setText(f"加载失败: {str(e)}")
            print(f"❌ 加载人格数据失败: {e}")

    def scan_personas(self):
        """扫描人格文件"""
        personas = []
        try:
            if os.path.exists(self.personas_dir):
                for file in os.listdir(self.personas_dir):
                    if file.endswith('.json'):
                        personas.append(file[:-5])  # 移除.json扩展名
        except Exception as e:
            print(f"❌ 扫描人格文件失败: {e}")
        return sorted(personas)

    def load_persona_file(self, name):
        """加载具体的人格文件"""
        try:
            file_path = os.path.join(self.personas_dir, f"{name}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"❌ 加载人格文件失败 {name}: {e}")
        return None

    def get_persona_type(self, data):
        """判断人格类型"""
        if data.get('builtin'):
            return "内置"
        elif data.get('dimensions'):
            return "六维"
        else:
            return "基础"

    def on_item_clicked(self, item):
        """点击表格项时加载详细信息"""
        row = item.row()
        name = self.table.item(row, 0).text()

        # 尝试加载文件
        data = self.load_persona_file(name)
        if data:
            self.current_editing_file = name

            # 填充基本信息
            self.edit_name.setText(data.get('name', name))
            self.edit_desc.setPlainText(data.get('description', ''))
            self.prompt_input.setPlainText(data.get('system_prompt', ''))
            self.style_input.setText(data.get('style', ''))

            # 填充维度数据
            dims = data.get('dimensions', {})
            # 处理第一组维度
            for dim_key in ["逻辑性", "创造力", "情感度", "知识广度", "记忆深度", "执行力"]:
                if dim_key in self.spin_boxes:
                    self.spin_boxes[dim_key].setValue(float(dims.get(dim_key, 0.5)))

            # 处理第二组维度（兼容性）
            dim_mapping = {
                "creativity": "创造力",
                "logic": "逻辑性",
                "empathy": "情感度",
                "knowledge": "知识广度",
                "humor": "创造力",  # 近似映射
                "bias": "情感度"  # 近似映射
            }

            for old_key, new_key in dim_mapping.items():
                if old_key in dims and new_key in self.spin_boxes:
                    self.spin_boxes[new_key].setValue(float(dims[old_key]))

            self.status_label.setText(f"正在编辑: {name}")

    def create_new_persona(self):
        """创建新的人格"""
        # 清空编辑器
        self.current_editing_file = None
        self.edit_name.clear()
        self.edit_desc.clear()
        self.prompt_input.clear()
        self.style_input.clear()

        # 重置维度为默认值
        for sb in self.spin_boxes.values():
            sb.setValue(0.5)

        self.status_label.setText("创建新人格 - 请填写信息")
        self.edit_name.setFocus()

    def save_changes(self):
        """保存人格数据"""
        try:
            # 获取基本信息
            name = self.edit_name.text().strip()
            description = self.edit_desc.toPlainText().strip()
            system_prompt = self.prompt_input.toPlainText().strip()
            style = self.style_input.text().strip()

            # 校验
            if not name:
                QMessageBox.warning(self, "缺少信息", "必须填写人格名称！")
                return

            if not system_prompt:
                reply = QMessageBox.question(
                    self, "确认保存",
                    "系统指令为空，AI可能无法正常工作。\n确定要保存吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return

            # 构建维度数据
            dimensions = {}
            for dim_name, spinbox in self.spin_boxes.items():
                dimensions[dim_name] = float(spinbox.value())

            # 构建完整数据
            persona_data = {
                "name": name,
                "description": description,
                "system_prompt": system_prompt,
                "style": style,
                "dimensions": dimensions,
                "version": "2.0",
                "last_modified": self.get_current_time()
            }

            # 确定文件名
            if self.current_editing_file and self.current_editing_file != name:
                # 如果重命名，删除旧文件
                old_path = os.path.join(self.personas_dir, f"{self.current_editing_file}.json")
                if os.path.exists(old_path):
                    os.remove(old_path)

            # 保存文件
            file_path = os.path.join(self.personas_dir, f"{name}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(persona_data, f, ensure_ascii=False, indent=4)

            # 发送信号
            self.saved_signal.emit(name)
            self.persona_saved.emit(name)
            self.persona_updated.emit(name)

            # 更新状态
            self.status_label.setText(f"✅ 已保存: {name}")

            # 刷新列表
            self.load_data()

            # 显示成功消息
            QMessageBox.information(self, "保存成功", f"人格 '{name}' 已保存成功！")

        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存时发生错误：\n{str(e)}")
            print(f"❌ 保存人格失败: {e}")

    def delete_persona(self):
        """删除选中的人格"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "未选择", "请先选择要删除的人格")
            return

        name = self.table.item(row, 0).text()
        if not name:
            return

        # 确认对话框
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要永久删除人格 '{name}' 吗？\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 删除文件
                file_path = os.path.join(self.personas_dir, f"{name}.json")
                if os.path.exists(file_path):
                    os.remove(file_path)

                    # 发送信号
                    self.persona_deleted.emit(name)

                    # 更新UI
                    self.load_data()
                    self.status_label.setText(f"🗑️ 已删除: {name}")

                    # 如果删除的是正在编辑的，清空编辑器
                    if self.current_editing_file == name:
                        self.create_new_persona()

                    QMessageBox.information(self, "删除成功", f"人格 '{name}' 已删除")
                else:
                    QMessageBox.warning(self, "文件不存在", f"找不到文件: {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "删除失败", f"删除时发生错误：\n{str(e)}")
                print(f"❌ 删除人格失败: {e}")

    def filter_table(self):
        """过滤表格内容"""
        search_text = self.search_input.text().lower()

        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break

            # 显示/隐藏行
            self.table.setRowHidden(row, not match)

    def get_current_time(self):
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def closeEvent(self, event):
        """关闭窗口时发出完成信号"""
        self.persona_updated.emit("editor_closed")
        super().closeEvent(event)


# 兼容性导出
class PersonaDialog(PersonaEditor):
    """兼容性别名"""
    pass


# 独立运行的简易版本（如果不需要io_manager）
class SimplePersonaEditor(PersonaEditor):
    """简易版本，不依赖io_manager"""

    def __init__(self, parent=None):
        super().__init__(io_manager=None, parent=parent)
        self.setWindowTitle("简易人格编辑器")