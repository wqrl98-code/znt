# -*- coding: utf-8 -*-
"""
Chat Widget - 稳定内核版 (Stable Core)
修复：渲染线程死锁、参数不匹配导致的无输出问题
特性：兼容旧版接口，自动适应新版算法输出

修复说明：使用 9-chatwai.txt 中的 _scroll_to_bottom 方法和气泡样式优化
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextBrowser, QLineEdit,
    QPushButton, QHBoxLayout
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QTextCursor


class ChatWidget(QWidget):
    # 信号：发送用户指令
    message_sent = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 1. 历史消息显示区 (使用最稳定的 QTextBrowser)
        self.history_display = QTextBrowser()
        self.history_display.setOpenExternalLinks(True)
        # 样式表：深色护眼模式，优化字距
        self.history_display.setStyleSheet("""
            QTextBrowser {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: none;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                font-size: 15px;
                padding: 15px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(self.history_display)

        # 2. 底部输入区
        input_layout = QHBoxLayout()

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("在此输入指令，例如: '深度解读文档《...》' 或 '按照人民日报风格仿写...'")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #333337;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #007acc; }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)

        self.send_btn = QPushButton("发送 / Send")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setFixedWidth(120)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 12px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #0098ff; }
            QPushButton:disabled { background-color: #333; color: #888; }
        """)
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)

        layout.addLayout(input_layout)

    def send_message(self):
        text = self.input_field.text().strip()
        if not text: return

        # 先显示用户自己的消息
        self.append_message("You", text, style="User")
        self.input_field.clear()

        # 发射信号给主系统
        self.message_sent.emit(text)

    def append_message(self, role, text, style="Normal"):
        """
        🔥 核心修复：多态参数处理
        无论调用方传 (role, text) 还是 (role, text, style)，都不会报错。
        """
        # 定义颜色映射
        colors = {
            "Athena": "#4fc3f7",  # AI 亮蓝
            "You": "#ffffff",  # 用户 白
            "User": "#ffffff",
            "System": "#ff5252",  # 报错 红
            "Success": "#4caf50",  # 成功 绿
            "Persona": "#ffb74d",  # 人格切换 橙
            "Normal": "#d4d4d4"
        }

        # 容错处理：确保 text 是字符串
        if text is None: text = ""
        text = str(text)

        # 确定颜色
        # 优先使用 style，如果 style 没定义颜色，则看 role，如果都没有，默认白色
        name_color = colors.get(style, colors.get(role, "#ffffff"))

        # 角色显示名优化
        display_name = role
        if role == "Athena":
            display_name = "🧠 Athena AI"
        elif role == "You":
            display_name = "👤 User"
        elif role == "System":
            display_name = "⚙️ System"

        # 文本格式化：将 Markdown 的简单格式转换为 HTML，避免直接渲染失败
        # 1. 转义尖括号，防止代码被当做HTML标签隐藏
        formatted_text = text.replace("<", "&lt;").replace(">", "&gt;")
        # 2. 还原换行符
        formatted_text = formatted_text.replace("\n", "<br>")
        # 3. 简单的粗体支持 - 修复了 9-chatwai.txt 中的错误替换逻辑
        # 正确替换 **text** 为 <b>text</b>
        formatted_text = formatted_text.replace("**", "<b>", 1)
        formatted_text = formatted_text.replace("**", "</b>", 1)

        # 构建 HTML 块 - 结合两种样式优点
        html_content = f"""
        <div style="margin-bottom: 15px; padding: 10px; background-color: #2c2c2c; border-radius: 8px;">
            <div style="color: {name_color}; font-weight: bold; margin-bottom: 8px; font-size: 13px;">{display_name}:</div>
            <div style="color: #e0e0e0; font-size: 15px; white-space: pre-wrap;">{formatted_text}</div>
        </div>
        <hr style="border: 0; border-top: 1px solid #333; margin: 10px 0;">
        """

        self.history_display.append(html_content)
        # 强制滚动到底部 - 使用 9-chatwai.txt 中的优化方法
        self._scroll_to_bottom()

    def append_html(self, html_content):
        """
        直接渲染 HTML 内容
        用于 Deep Thinking 的实时思维流（彩色日志）
        来自 9-chatwai.txt 的修复
        """
        self.history_display.append(html_content)
        self._scroll_to_bottom()

    def clear(self):
        """清空聊天记录 - 来自 9-chatwai.txt 的修复"""
        self.history_display.clear()

    def _scroll_to_bottom(self):
        """自动滚动到底部 - 来自 9-chatwai.txt 的优化方法"""
        scrollbar = self.history_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def set_loading(self, is_loading):
        """控制界面交互状态"""
        self.input_field.setEnabled(not is_loading)
        self.send_btn.setEnabled(not is_loading)
        self.send_btn.setText("Thinking..." if is_loading else "发送 / Send")