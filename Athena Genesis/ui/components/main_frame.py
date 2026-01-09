# -*- coding: utf-8 -*-
"""
纯净UI主框架 (MainFrame) - 修复版
职责：只负责组装Sidebar、ChatArea、Dashboard，不包含任何业务逻辑
修复：Splitter比例初始化问题
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSplitter, QVBoxLayout
from PyQt6.QtCore import Qt
from .sidebar import Sidebar
from .chat_area import ChatArea
from .dashboard import Dashboard


class MainFrame(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """初始化纯UI布局，不涉及任何业务逻辑"""
        # 主水平布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建水平分割器
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3e3e42;
            }
            QSplitter::handle:hover {
                background-color: #007acc;
            }
        """)

        # 1. 初始化纯UI组件（不传入任何业务对象）
        self.sidebar = Sidebar()
        self.chat_area = ChatArea()
        self.dashboard = Dashboard()

        # 2. 添加到分割器
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.chat_area)
        self.splitter.addWidget(self.dashboard)

        # 🔥 修复关键：设置初始比例 (侧边栏:聊天区:仪表盘 = 1:3:2)
        # 防止侧边栏被压缩
        self.splitter.setSizes([200, 600, 400])

        # 可选：禁止侧边栏完全折叠
        self.splitter.setCollapsible(0, False)

        # 4. 将分割器放入主布局
        main_layout.addWidget(self.splitter)

    # ==========================================
    # 以下为纯UI操作接口，供控制器调用
    # ==========================================

    def update_status_bar(self, text):
        """更新状态栏文本 - 纯UI操作"""
        if hasattr(self, 'chat_area') and hasattr(self.chat_area, 'status_label'):
            self.chat_area.status_label.setText(text)

    def append_message(self, sender, content, msg_type="normal"):
        """添加消息到聊天区 - 纯UI操作"""
        if hasattr(self, 'chat_area'):
            self.chat_area.append_message(sender, content, msg_type)

    def clear_input(self):
        """清空输入框 - 纯UI操作"""
        if hasattr(self, 'chat_area'):
            self.chat_area.clear_input()

    def get_input(self):
        """获取输入框文本 - 纯UI操作"""
        if hasattr(self, 'chat_area'):
            return self.chat_area.get_input()
        return ""

    def set_loading(self, loading):
        """设置加载状态 - 纯UI操作"""
        if hasattr(self, 'chat_area'):
            self.chat_area.set_loading(loading)

    def get_current_mode(self):
        """获取当前模式 - 纯UI操作"""
        if hasattr(self, 'sidebar') and hasattr(self.sidebar, 'get_current_mode'):
            return self.sidebar.get_current_mode()
        return "chat"

    def update_mode_status(self, mode):
        """更新模式状态显示 - 纯UI操作"""
        if hasattr(self, 'chat_area'):
            self.chat_area.update_mode_status(mode)

    def update_radar_data(self, data):
        """更新雷达图数据 - 纯UI操作"""
        if hasattr(self, 'dashboard') and hasattr(self.dashboard, 'update_radar_data'):
            self.dashboard.update_radar_data(data)