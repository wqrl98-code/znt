# ui/components/chat_area.py
"""
聊天显示区 - 修复高对比度问题，保留完整功能
修复：文字颜色与背景相同导致"无反馈"的视觉Bug
增强：消息气泡样式，强制刷新机制，支持三种工作模式
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QScrollArea, QFrame, QLabel, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor, QFont, QTextCharFormat, QTextBlockFormat, QColor
import datetime
import sys


class ChatArea(QWidget):
    """聊天区域组件"""

    # 信号定义
    message_sent = pyqtSignal(str)  # 发送消息信号
    clear_requested = pyqtSignal()  # 清空历史请求信号

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.messages = []

    def init_ui(self):
        """初始化聊天区域UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 模式状态栏
        self.mode_status_bar = QLabel("当前模式: 💬 通用对话")
        self.mode_status_bar.setStyleSheet("""
            QLabel {
                background: #2d2d30;
                color: #4FC3F7;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        self.mode_status_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.mode_status_bar)

        # 聊天历史显示区域 - 使用QTextEdit并修复高对比度问题
        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True)
        self.history_display.setPlaceholderText("💡 系统就绪。请在右侧侧边栏【新建人格】或【加载人格】开始...")
        # 🔥 强制高对比度样式：深色背景，亮色文字
        self.history_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;  /* 确保文字为白色 */
                border: none;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                font-size: 15px;  /* 增大字体 */
                padding: 15px;
                line-height: 1.6;
            }
        """)
        self.history_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.history_display, 4)

        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #333; height: 1px;")
        layout.addWidget(line)

        # 输入区域
        input_frame = QFrame()
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(8)

        # 输入框
        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(80)
        self.input_field.setPlaceholderText("在此输入指令... (按 Ctrl+Enter 发送，Shift+Enter 换行)")
        self.input_field.setStyleSheet("""
            QTextEdit {
                background: #333333;
                color: #ffffff;  /* 确保输入文字为白色 */
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QTextEdit:focus {
                border: 1px solid #007acc;
            }
        """)

        # 安装事件过滤器来处理快捷键
        self.input_field.installEventFilter(self)

        input_layout.addWidget(self.input_field)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.btn_clear = QPushButton("🗑️ 清空历史")
        self.btn_clear.clicked.connect(self.clear_history)
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background: #555;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #666;
            }
        """)

        self.btn_copy = QPushButton("📋 复制历史")
        self.btn_copy.clicked.connect(self.copy_history)
        self.btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy.setStyleSheet("""
            QPushButton {
                background: #444;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #555;
            }
        """)

        self.btn_send = QPushButton("📤 发送")
        self.btn_send.clicked.connect(self.send_message)
        self.btn_send.setFixedSize(100, 40)
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.setStyleSheet("""
            QPushButton {
                background: #007acc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #0098ff;
            }
            QPushButton:pressed {
                background: #005a9e;
            }
            QPushButton:disabled {
                background: #444;
                color: #888;
            }
        """)

        button_layout.addWidget(self.btn_clear)
        button_layout.addWidget(self.btn_copy)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_send)

        input_layout.addLayout(button_layout)
        layout.addWidget(input_frame, 1)

        # 3. 状态标签 (用于显示思考状态) - 从修复版添加
        self.status_label = QPushButton("✅ 就绪")  # 用按钮模拟标签，方便样式
        self.status_label.setFlat(True)
        self.status_label.setStyleSheet("""
            QPushButton {
                text-align: left; 
                color: #888; 
                padding: 2px 10px;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(self.status_label)

    def eventFilter(self, obj, event):
        """处理快捷键"""
        if obj == self.input_field and event.type() == event.Type.KeyPress:
            # Ctrl+Enter 发送
            if event.key() == Qt.Key.Key_Return and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                self.send_message()
                return True
            # Shift+Enter 换行
            elif event.key() == Qt.Key.Key_Return and (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                # 允许默认的换行行为
                return False
            # Enter 发送（如果不需要换行）
            elif event.key() == Qt.Key.Key_Return and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                # 可以根据配置决定是否允许Enter发送
                return False
        return super().eventFilter(obj, event)

    def send_message(self):
        """发送消息"""
        text = self.get_input()
        if text:
            # 发射信号
            self.message_sent.emit(text)

            # 显示用户消息
            self.append_message("用户", text, "User")

            # 清空输入框
            self.clear_input()

            # 保持焦点在输入框
            self.input_field.setFocus()

    def get_input(self):
        """获取输入框内容"""
        return self.input_field.toPlainText().strip()

    def clear_input(self):
        """清空输入框"""
        self.input_field.clear()

    def set_input(self, text):
        """设置输入框内容"""
        self.input_field.setPlainText(text)

    def append_message(self, sender, message, sender_type="User"):
        """添加消息到历史记录 - 增强版，修复显示问题"""
        print(f"📺 [UI] 尝试显示消息: {sender} -> {message[:20]}...")

        # 格式化消息
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # 构建HTML消息
        if sender_type == "User":
            html = self._format_user_message(sender, message, timestamp)
        elif sender_type == "Athena":
            html = self._format_athena_message(sender, message, timestamp)
        elif sender_type == "assistant_web":
            html = self._format_web_message(sender, message, timestamp)
        elif sender_type == "assistant_deep":
            html = self._format_deep_message(sender, message, timestamp)
        elif sender_type == "System":
            html = self._format_system_message(message)
        elif sender_type == "Error":
            html = self._format_error_message(message)
        elif sender_type == "Success":
            html = self._format_success_message(message)
        else:
            html = self._format_default_message(sender, message, timestamp)

        # 移动光标到底部并插入HTML
        self.history_display.moveCursor(QTextCursor.MoveOperation.End)
        self.history_display.insertHtml(html)

        # 添加分隔线
        self.history_display.insertHtml('<hr style="border: 0; border-top: 1px solid #333; margin: 15px 0;">')

        # 移动光标到底部
        self.history_display.moveCursor(QTextCursor.MoveOperation.End)

        # 🔥 强制刷新界面 - 修复"无反馈"问题
        self.history_display.repaint()
        QApplication.processEvents()  # 立即处理UI事件

        # 滚动到底部
        self.scroll_to_bottom()

        # 保存消息到内存
        self.messages.append({
            "sender": sender,
            "message": message,
            "type": sender_type,
            "timestamp": timestamp
        })

    def _format_user_message(self, sender, message, timestamp):
        """格式化用户消息 - 增强对比度"""
        import html
        safe_content = html.escape(message).replace('\n', '<br>')

        return f"""
        <div style="margin-bottom: 15px; margin-left: 20%;">
            <div style="text-align: right; color: #64b5f6; font-size: 11px; margin-bottom: 2px;">
                {timestamp}
            </div>
            <div style="background: #005a9e; color: #ffffff; padding: 10px 15px; 
                 border-radius: 15px 5px 15px 15px; display: inline-block; max-width: 80%;
                 word-wrap: break-word; border-left: 4px solid #64b5f6;">
                {safe_content}
            </div>
            <div style="text-align: right; color: #64b5f6; font-weight: bold; margin-top: 3px;">
                {sender}
            </div>
        </div>
        """

    def _format_athena_message(self, sender, message, timestamp):
        """格式化Athena消息 - 增强对比度"""
        import html
        safe_content = html.escape(message).replace('\n', '<br>')

        return f"""
        <div style="margin-bottom: 15px; margin-right: 20%;">
            <div style="text-align: left; color: #81c784; font-size: 11px; margin-bottom: 2px;">
                {timestamp}
            </div>
            <div style="background: #2d2d30; color: #e0e0e0; padding: 10px 15px; 
                 border-radius: 5px 15px 15px 15px; display: inline-block; max-width: 80%;
                 word-wrap: break-word; border-left: 4px solid #81c784;">
                {safe_content}
            </div>
            <div style="text-align: left; color: #81c784; font-weight: bold; margin-top: 3px;">
                {sender}
            </div>
        </div>
        """

    def _format_web_message(self, sender, message, timestamp):
        """格式化联网搜索消息 - 增强对比度"""
        import html
        safe_content = html.escape(message).replace('\n', '<br>')

        return f"""
        <div style="margin-bottom: 15px; margin-right: 20%;">
            <div style="text-align: left; color: #00E676; font-size: 11px; margin-bottom: 2px;">
                {timestamp} | 🔍 简单问答模式
            </div>
            <div style="background: #1a3c1a; color: #b8f2b8; padding: 10px 15px; 
                 border-radius: 5px 15px 15px 15px; display: inline-block; max-width: 80%;
                 word-wrap: break-word; border-left: 4px solid #00E676;">
                {safe_content}
            </div>
            <div style="text-align: left; color: #00E676; font-weight: bold; margin-top: 3px;">
                {sender} (联网搜索)
            </div>
        </div>
        """

    def _format_deep_message(self, sender, message, timestamp):
        """格式化深度研报消息 - 增强对比度"""
        import html
        safe_content = html.escape(message).replace('\n', '<br>')

        return f"""
        <div style="margin-bottom: 15px; margin-right: 10%;">
            <div style="text-align: left; color: #BA68C8; font-size: 11px; margin-bottom: 2px;">
                {timestamp} | 📝 深度研报模式
            </div>
            <div style="background: #2d1a3c; color: #e2b8f2; padding: 15px 20px; 
                 border-radius: 5px 15px 15px 15px; display: inline-block; max-width: 90%;
                 word-wrap: break-word; border-left: 4px solid #9C27B0; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">
                {safe_content}
            </div>
            <div style="text-align: left; color: #BA68C8; font-weight: bold; margin-top: 3px;">
                {sender} (深度审查通过)
            </div>
        </div>
        """

    def _format_system_message(self, message):
        """格式化系统消息 - 增强对比度"""
        import html
        safe_content = html.escape(message).replace('\n', '<br>')

        return f"""
        <div style="margin-bottom: 10px; text-align: center;">
            <span style="background: #333; color: #ffb74d; padding: 3px 10px; 
                 border-radius: 10px; font-size: 12px; display: inline-block;">
                💡 {safe_content}
            </span>
        </div>
        """

    def _format_error_message(self, message):
        """格式化错误消息 - 增强对比度"""
        import html
        safe_content = html.escape(message).replace('\n', '<br>')

        return f"""
        <div style="margin-bottom: 10px; text-align: center;">
            <span style="background: #4a1a1a; color: #e57373; padding: 3px 10px; 
                 border-radius: 10px; font-size: 12px; display: inline-block;">
                ❌ {safe_content}
            </span>
        </div>
        """

    def _format_success_message(self, message):
        """格式化成功消息 - 增强对比度"""
        import html
        safe_content = html.escape(message).replace('\n', '<br>')

        return f"""
        <div style="margin-bottom: 10px; text-align: center;">
            <span style="background: #1a3c1a; color: #6bff6b; padding: 3px 10px; 
                 border-radius: 10px; font-size: 12px; display: inline-block;">
                ✅ {safe_content}
            </span>
        </div>
        """

    def _format_default_message(self, sender, message, timestamp):
        """格式化默认消息 - 增强对比度"""
        import html
        safe_content = html.escape(message).replace('\n', '<br>')

        return f"""
        <div style="margin-bottom: 15px; margin-right: 20%;">
            <div style="text-align: left; color: #cccccc; font-size: 11px; margin-bottom: 2px;">
                {timestamp}
            </div>
            <div style="background: #2d2d30; color: #e0e0e0; padding: 10px 15px; 
                 border-radius: 5px 15px 15px 15px; display: inline-block; max-width: 80%;
                 word-wrap: break-word; border-left: 4px solid #cccccc;">
                {safe_content}
            </div>
            <div style="text-align: left; color: #cccccc; font-weight: bold; margin-top: 3px;">
                {sender}
            </div>
        </div>
        """

    def handle_brain_result(self, result):
        """处理大脑返回的结果（升级版）"""
        if not isinstance(result, dict):
            # 兼容旧版本
            self.append_message("Athena", str(result), "Athena")
            return

        content = result.get("content", "")
        msg_type = result.get("type", "chat")
        mode = result.get("mode", "chat")

        # 根据模式添加不同的样式
        if mode == "simple_qa":
            # 简单问答模式：添加网络来源标记
            content = f"🔍 {content}\n\n<small style='color: #666;'>📡 联网搜索模式生成</small>"
            role = "assistant_web"
        elif mode == "deep_write":
            # 深度研报模式：添加深度标记
            content = f"📋 {content}\n\n<small style='color: #666;'>🧠 深度研报模式生成 | 已通过多重审查</small>"
            role = "assistant_deep"
        else:
            # 普通聊天模式
            role = "Athena"

        # 添加文档信息（如果有）
        if msg_type == "deep_write":
            content += "\n\n---\n<small>📄 这是一个深度生成的文档，建议保存备用</small>"

        self.append_message("Athena", content, role)

        # 自动滚动到底部
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        """滚动到底部"""
        self.history_display.moveCursor(QTextCursor.MoveOperation.End)
        self.history_display.verticalScrollBar().setValue(
            self.history_display.verticalScrollBar().maximum()
        )

    def update_mode_status(self, mode):
        """更新模式状态显示"""
        mode_display = {
            "chat": "💬 通用对话",
            "simple_qa": "🔍 简单问答",
            "deep_write": "📝 深度研报"
        }

        display_text = mode_display.get(mode, "未知模式")
        self.mode_status_bar.setText(f"当前模式: {display_text}")

    def append_html(self, html_content):
        """直接添加HTML内容"""
        self.history_display.append(html_content)
        self.history_display.moveCursor(QTextCursor.MoveOperation.End)

    def clear_history(self):
        """清空聊天历史"""
        self.history_display.clear()
        self.messages = []
        self.clear_requested.emit()

    def copy_history(self):
        """复制聊天历史到剪贴板"""
        text_content = ""
        for msg in self.messages:
            text_content += f"[{msg['timestamp']}] {msg['sender']}: {msg['message']}\n"

        clipboard = QApplication.clipboard()
        clipboard.setText(text_content)

        self.append_message("系统", "聊天历史已复制到剪贴板", "System")

    def get_history_text(self):
        """获取聊天历史的纯文本"""
        text_content = ""
        for msg in self.messages:
            text_content += f"[{msg['timestamp']}] {msg['sender']}: {msg['message']}\n"
        return text_content

    def get_history_html(self):
        """获取聊天历史的HTML"""
        return self.history_display.toHtml()

    def get_current_time(self):
        """获取当前时间字符串"""
        return datetime.datetime.now().strftime("%H:%M:%S")

    def set_loading(self, is_loading=True):
        """设置加载状态 - 增强版"""
        self.btn_send.setEnabled(not is_loading)
        self.btn_send.setText("思考中..." if is_loading else "📤 发送")

        if is_loading:
            self.btn_send.setStyleSheet("""
                QPushButton {
                    background: #555;
                    color: #aaa;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """)
            self.status_label.setText("🚀 正在高速运转...")
        else:
            self.btn_send.setStyleSheet("""
                QPushButton {
                    background: #007acc;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: #0098ff;
                }
                QPushButton:pressed {
                    background: #005a9e;
                }
            """)
            self.status_label.setText("✅ 就绪")

    def set_enabled(self, enabled):
        """启用/禁用聊天区域"""
        self.input_field.setEnabled(enabled)
        self.btn_send.setEnabled(enabled)
        self.btn_clear.setEnabled(enabled)
        self.btn_copy.setEnabled(enabled)

    def show_welcome_message(self):
        """显示欢迎消息"""
        welcome_html = """
        <div style="text-align: center; margin: 30px 20px; color: #888;">
            <h2 style="color: #4FC3F7;">✨ Athena 智能对话系统</h2>
            <p style="color: #ffffff;">支持三种工作模式：</p>
            <div style="display: flex; justify-content: center; gap: 20px; margin: 20px 0;">
                <div style="background: #2d2d30; padding: 15px; border-radius: 8px; width: 200px;">
                    <h4 style="color: #4FC3F7;">💬 通用对话</h4>
                    <p style="font-size: 12px; color: #cccccc;">智能聊天，上下文感知</p>
                </div>
                <div style="background: #1a3c1a; padding: 15px; border-radius: 8px; width: 200px;">
                    <h4 style="color: #00E676;">🔍 简单问答</h4>
                    <p style="font-size: 12px; color: #cccccc;">联网搜索，快速回答</p>
                </div>
                <div style="background: #2d1a3c; padding: 15px; border-radius: 8px; width: 200px;">
                    <h4 style="color: #BA68C8;">📝 深度研报</h4>
                    <p style="font-size: 12px; color: #cccccc;">深度分析，专业文档</p>
                </div>
            </div>
            <p style="color: #ffffff;">请从右侧侧边栏选择操作开始...</p>
        </div>
        """
        self.history_display.setHtml(welcome_html)