# -*- coding: utf-8 -*-
"""
知识库展示组件 - 独立模块版
解决：搜索跳转问题、节点显示为0问题
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit,
    QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt


class KnowledgeWidget(QWidget):
    # 信号：发送查询文本
    query_sent = pyqtSignal(str)

    def __init__(self, knowledge_base):
        super().__init__()
        self.knowledge_base = knowledge_base
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 1. 顶部搜索栏
        search_layout = QHBoxLayout()
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("在此检索知识库 (不会跳转到聊天)...")
        self.query_input.returnPressed.connect(self.on_search_clicked)
        self.query_input.setStyleSheet("padding: 8px; border: 1px solid #444; background: #222; color: white;")

        search_btn = QPushButton("🔍 知识检索")
        search_btn.setFixedWidth(120)
        search_btn.clicked.connect(self.on_search_clicked)
        search_btn.setStyleSheet("padding: 8px; background: #333; color: white; border: 1px solid #555;")

        search_layout.addWidget(self.query_input)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)

        # 2. 结果显示区
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00e5ff;
                font-family: 'Consolas', 'Microsoft YaHei';
                border: 1px solid #333;
                padding: 10px;
                font-size: 13px;
            }
        """)
        self.result_display.setPlaceholderText("等待检索... 结果将直接显示在这里。")
        layout.addWidget(self.result_display)

        # 3. 底部统计栏 (解决显示0的问题)
        self.stats_container = QWidget()
        stats_layout = QHBoxLayout(self.stats_container)
        self.node_label = QLabel("🔗 知识节点: 0")
        self.edge_label = QLabel("⚡ 关联关系: 0")
        self.doc_label = QLabel("📄 已索引文档: 0")

        for lbl in [self.node_label, self.edge_label, self.doc_label]:
            lbl.setStyleSheet("color: #888; font-weight: bold; padding: 5px;")
            stats_layout.addWidget(lbl)

        layout.addWidget(self.stats_container)

    def on_search_clicked(self):
        text = self.query_input.text().strip()
        if not text: return

        self.result_display.append(f"\n======== 正在检索: {text} ========")
        self.query_sent.emit(text)

    def show_results(self, results: str):
        """直接在当前组件显示结果，不跳转"""
        self.result_display.append(results)
        self.result_display.append("==================================\n")
        sb = self.result_display.verticalScrollBar()
        sb.setValue(sb.maximum())

    def update_content(self, data):
        """接收系统日志 (过滤System空消息)"""
        if isinstance(data, dict):
            # 可以在这里处理结构化数据
            pass
        elif isinstance(data, str) and "System" not in data:
            self.result_display.append(f"ℹ️ {data}")

    def update_stats(self, nodes, edges, docs):
        """更新底部统计数据"""
        self.node_label.setText(f"🔗 知识节点: {nodes}")
        self.edge_label.setText(f"⚡ 关联关系: {edges}")
        self.doc_label.setText(f"📄 已索引文档: {docs}")

    def clear_display(self):
        self.result_display.clear()

    def export_content(self):
        content = self.result_display.toPlainText()
        if not content: return
        path, _ = QFileDialog.getSaveFileName(self, "导出记录", "knowledge_log.txt")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)