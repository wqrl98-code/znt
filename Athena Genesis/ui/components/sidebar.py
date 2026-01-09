# ui/components/sidebar.py
# -*- coding: utf-8 -*-
"""
侧边栏组件 - 纯净版 (v5.0)
修复：移除内部逻辑干扰，确保按钮点击事件能被主窗口捕获
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QListWidget, QLabel,
    QPushButton, QSlider, QCheckBox, QLineEdit, QComboBox,
    QGridLayout, QDialog, QDialogButtonBox, QScrollArea,
    QSizePolicy, QMessageBox, QFileDialog, QHBoxLayout, QFormLayout, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

# 导入配置
from config.genres import get_genre_names, GENRE_DEFINITIONS

# ===========================================
# 组件导入兼容性处理
# ===========================================

# 尝试导入雷达组件
try:
    from ui.components.radar_widget import EnhancedHexagonRadar

    HAS_RADAR_WIDGET = True
except ImportError:
    HAS_RADAR_WIDGET = False


    class EnhancedHexagonRadar(QWidget):
        def __init__(self):
            super().__init__()
            label = QLabel("🧠 人格雷达")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout = QVBoxLayout(self)
            layout.addWidget(label)

        def update_data(self, data):
            pass

# 尝试导入知识库组件
try:
    from ui.components.knowledge_widget import KnowledgeWidget

    HAS_KNOWLEDGE_WIDGET = True
except ImportError:
    HAS_KNOWLEDGE_WIDGET = False


    class KnowledgeWidget(QWidget):
        query_sent = pyqtSignal(str)

        def __init__(self, kb=None):
            super().__init__()
            self.knowledge_base = kb
            layout = QVBoxLayout(self)
            label = QLabel("🔍 知识库检索")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)

        def show_results(self, res):
            pass

        def search(self, query):
            if query:
                self.query_sent.emit(query)


class Sidebar(QWidget):
    """侧边栏组件 - 纯净版 (v5.0)"""

    # 定义信号供外部连接
    search_triggered = pyqtSignal(str)
    web_toggled = pyqtSignal(bool)
    mode_changed = pyqtSignal(str)
    strategy_changed = pyqtSignal(dict)

    # 原有功能信号
    persona_selected = pyqtSignal(str)
    load_persona_clicked = pyqtSignal()
    new_persona_clicked = pyqtSignal()
    import_doc_clicked = pyqtSignal()
    doc_selected = pyqtSignal(str)
    temp_changed = pyqtSignal(float)
    web_search_toggled = pyqtSignal(bool)

    # 高级功能信号
    analyze_file_clicked = pyqtSignal(str)
    mimic_file_clicked = pyqtSignal(str)
    continue_file_clicked = pyqtSignal(str)

    def __init__(self, brain=None, io_manager=None, mimicry_engine=None, knowledge_base=None, parent=None):
        super().__init__(parent)
        self.brain = brain
        self.io_manager = io_manager
        self.mimicry_engine = mimicry_engine
        self.knowledge_base = knowledge_base

        # 只设置最小和最大宽度，不设置固定宽度
        self.setMinimumWidth(250)
        self.setMaximumWidth(380)

        # 应用样式
        self.setStyleSheet("""
            QWidget { 
                background-color: #252526; 
                color: #e0e0e0; 
                border-right: 1px solid #3e3e42; 
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }
            QGroupBox { 
                font-weight: bold; 
                border: 1px solid #3e3e42; 
                margin-top: 10px; 
                padding-top: 10px;
                border-radius: 4px;
                background: #1e1e1e;
            }
            QGroupBox::title {
                color: #4FC3F7;
                padding-left: 5px;
            }
            QComboBox { 
                background: #333; 
                border: 1px solid #555; 
                padding: 5px; 
                color: white;
                border-radius: 3px;
            }
            QComboBox:hover { border-color: #007acc; }
            QPushButton { 
                text-align: left; 
                padding: 8px; 
                border: none; 
                background: transparent; 
                border-radius: 4px;
            }
            QPushButton:hover { background: #2a2d2e; }
            QPushButton:checked { 
                background: #37373d; 
                border-left: 3px solid #007acc; 
            }
            QListWidget { 
                background: #252526; 
                border: 1px solid #3e3e42;
                font-size: 12px;
                border-radius: 4px;
                color: #cccccc;
            }
            QListWidget::item { 
                padding: 5px; 
                border-bottom: 1px solid #2a2a2a; 
            }
            QListWidget::item:hover { background: #2a2d2e; }
            QListWidget::item:selected { 
                background: #094771; 
                color: white;
            }
            QLabel { color: #cccccc; }
        """)

        # 初始化UI
        self.init_ui()

    def init_ui(self):
        """初始化侧边栏UI - 纯净版设计"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 使用ScrollArea防止内容溢出
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        # 内容容器
        content_widget = QWidget()
        self.layout = QVBoxLayout(content_widget)
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(10, 15, 10, 15)

        # 1. 👥 人格管理区
        self._init_persona_management()

        # 2. 🚀 工作模式选择区
        self._init_mode_control()

        # 3. 🎯 写作策略控制台
        self._init_strategy_console()

        # 4. 🧠 人格雷达组件
        self._init_radar_area()

        # 5. 🔥 思维活跃度控制
        self._init_temperature_control()

        # 6. 🔍 知识库索引
        self._init_knowledge_area()

        # 7. 📂 数据资产空间
        self._init_doc_area()

        # 版本信息
        ver_label = QLabel("Athena Genesis v5.0\n纯净版")
        ver_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver_label.setStyleSheet("color: #555; font-size: 10px; margin-top: 15px;")
        self.layout.addWidget(ver_label)

        # 底部填充
        self.layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def _init_persona_management(self):
        """初始化人格管理区"""
        persona_group = QGroupBox("👥 人格矩阵")
        persona_layout = QVBoxLayout(persona_group)

        # 加载人格按钮 - 暴露给主窗口
        self.btn_load_persona = QPushButton("📂 加载人格存档")
        self.btn_load_persona.setStyleSheet("""
            background: #2b2b2b; 
            color: white;
            border: 1px solid #3e3e42;
            padding: 8px;
            border-radius: 4px;
            font-weight: bold;
        """)

        # 新建人格按钮 - 暴露给主窗口
        self.btn_new_persona = QPushButton("✨ 新建空白人格")
        self.btn_new_persona.setStyleSheet("""
            background: #2b2b2b; 
            color: white;
            border: 1px solid #3e3e42;
            padding: 8px;
            border-radius: 4px;
            font-weight: bold;
        """)

        persona_layout.addWidget(self.btn_load_persona)
        persona_layout.addWidget(self.btn_new_persona)
        self.layout.addWidget(persona_group)

    def _init_mode_control(self):
        """初始化工作模式控制区域"""
        self.mode_group = QGroupBox("🚀 工作模式")
        mode_layout = QVBoxLayout(self.mode_group)
        mode_layout.setContentsMargins(10, 15, 10, 10)

        # 模式选择下拉框
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "💬 通用对话 (本地优先)",
            "🔍 简单问答 (联网搜索)",
            "📝 深度研报 (深度学习+写作)"
        ])
        self.mode_combo.setCurrentIndex(0)
        mode_layout.addWidget(self.mode_combo)

        # 联网开关
        self.web_search_check = QCheckBox("🌐 启用联网搜索")
        self.web_search_check.setStyleSheet("""
            QCheckBox {
                color: #00E676;
                font-weight: bold;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        mode_layout.addWidget(self.web_search_check)

        self.layout.addWidget(self.mode_group)

    def _init_strategy_console(self):
        """初始化写作策略控制台"""
        self.strategy_group = QGroupBox("🎯 写作策略控制台")
        self.strategy_group.setVisible(False)

        strat_layout = QFormLayout(self.strategy_group)
        strat_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        strat_layout.setVerticalSpacing(8)

        # 受众选择
        self.combo_audience = QComboBox()
        self.combo_audience.addItems(["通用读者", "专业人士", "初学者", "决策层", "儿童", "自定义..."])
        self.combo_audience.setCurrentIndex(0)
        strat_layout.addRow("目标受众:", self.combo_audience)

        # 语气选择
        self.combo_tone = QComboBox()
        self.combo_tone.addItems(["客观中立", "热情洋溢", "严肃庄重", "幽默风趣", "批判性", "学术严谨"])
        self.combo_tone.setCurrentIndex(0)
        strat_layout.addRow("语调风格:", self.combo_tone)

        # 核心目标
        self.goal_input = QLineEdit()
        self.goal_input.setPlaceholderText("例：改变认知 / 说服购买 / 引发共鸣")
        strat_layout.addRow("核心目标:", self.goal_input)

        # 文体选择
        self.combo_genre = QComboBox()
        try:
            if GENRE_DEFINITIONS:
                genres = list(GENRE_DEFINITIONS.keys())
                self.combo_genre.addItems(genres)
            else:
                self.combo_genre.addItems(["单位材料/公文", "技术文档", "学术论文", "新闻稿", "个人总结"])
        except:
            self.combo_genre.addItems(get_genre_names() if hasattr(get_genre_names, '__call__') else
                                      ["单位材料/公文", "技术文档", "学术论文", "新闻稿", "个人总结"])

        self.combo_genre.setCurrentText("单位材料/公文")
        strat_layout.addRow("文章体裁:", self.combo_genre)

        self.layout.addWidget(self.strategy_group)

    def _init_radar_area(self):
        """初始化人格雷达区域"""
        self.radar_group = QGroupBox("🧠 人格维度")
        radar_layout = QVBoxLayout(self.radar_group)

        if HAS_RADAR_WIDGET:
            self.radar_widget = EnhancedHexagonRadar()
        else:
            self.radar_widget = EnhancedHexagonRadar()

        self.radar_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.radar_widget.setMinimumHeight(200)

        radar_layout.addWidget(self.radar_widget)
        self.layout.addWidget(self.radar_group)

    def _init_temperature_control(self):
        """初始化思维活跃度控制"""
        self.temp_group = QGroupBox("🔥 思维活跃度控制")
        temp_layout = QVBoxLayout(self.temp_group)

        self.temp_label = QLabel("🧠 思维活跃度: 0.5 (平衡)")
        self.temp_label.setStyleSheet("color: #ecf0f1; font-weight: bold;")
        temp_layout.addWidget(self.temp_label)

        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setMinimum(1)
        self.temp_slider.setMaximum(10)
        self.temp_slider.setValue(5)
        self.temp_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.temp_slider.setTickInterval(1)
        temp_layout.addWidget(self.temp_slider)

        # 低功耗模式选项
        self.low_power_check = QCheckBox("💡 低功耗模式 (响应更快)")
        temp_layout.addWidget(self.low_power_check)

        self.layout.addWidget(self.temp_group)

    def _init_knowledge_area(self):
        """初始化知识库索引区域"""
        self.knowledge_group = QGroupBox("🔍 知识库索引")
        knowledge_layout = QVBoxLayout(self.knowledge_group)

        if HAS_KNOWLEDGE_WIDGET:
            self.knowledge_widget = KnowledgeWidget(self.knowledge_base)
        else:
            self.knowledge_widget = KnowledgeWidget(self.knowledge_base)

        self.knowledge_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.knowledge_widget.setMinimumHeight(180)

        knowledge_layout.addWidget(self.knowledge_widget)

        # 知识库状态标签
        self.knowledge_status = QLabel("就绪")
        self.knowledge_status.setStyleSheet("color: #B0BEC5; font-size: 11px;")
        knowledge_layout.addWidget(self.knowledge_status)

        self.layout.addWidget(self.knowledge_group)

    def _init_doc_area(self):
        """初始化文档库区域"""
        self.doc_group = QGroupBox("📂 数据资产")
        doc_layout = QVBoxLayout(self.doc_group)

        # 导入文档按钮 - 暴露给主窗口
        self.btn_import = QPushButton("➕ 导入文档 / 建立索引")
        self.btn_import.setStyleSheet("""
            background: #2b5c2b; 
            color: white; 
            padding: 10px; 
            margin: 2px;
            border: none;
            border-radius: 4px;
            font-weight: bold;
            text-align: center;
        """)

        doc_layout.addWidget(self.btn_import)

        # 文档列表
        self.doc_list = QListWidget()
        self.doc_list.setMinimumHeight(180)
        self.doc_list.setMaximumHeight(250)
        doc_layout.addWidget(self.doc_list)

        # 高级操作区
        action_layout = QHBoxLayout()

        self.btn_analyze = QPushButton("🔍 深度解读")
        self.btn_mimic = QPushButton("🎭 风格仿写")
        self.btn_continue = QPushButton("✍️ 续写")

        action_style = """
            QPushButton { 
                background: #333; 
                color: #ccc; 
                border: 1px solid #444; 
                border-radius: 4px; 
                padding: 6px; 
                font-size: 11px;
                text-align: center;
                flex: 1;
            }
            QPushButton:hover { 
                background: #444; 
                border-color: #007acc; 
                color: white; 
            }
        """

        for btn in [self.btn_analyze, self.btn_mimic, self.btn_continue]:
            btn.setStyleSheet(action_style)
            action_layout.addWidget(btn)

        doc_layout.addLayout(action_layout)

        self.layout.addWidget(self.doc_group)

    # ===========================================
    # 公共接口方法
    # ===========================================

    def get_current_mode(self):
        """获取当前模式"""
        mode_mapping = {
            "💬 通用对话 (本地优先)": "chat",
            "🔍 简单问答 (联网搜索)": "simple_qa",
            "📝 深度研报 (深度学习+写作)": "deep_write"
        }
        return mode_mapping.get(self.mode_combo.currentText(), "chat")

    def refresh_doc_list(self, documents):
        """刷新文档列表"""
        self.doc_list.clear()
        for doc_name in documents:
            self.doc_list.addItem(doc_name)

    def add_document(self, doc_name):
        """添加单个文档到列表"""
        self.doc_list.addItem(doc_name)

    def update_knowledge_status(self, status_text, is_success=True):
        """更新知识库状态"""
        color = "#4CAF50" if is_success else "#F44336"
        self.knowledge_status.setStyleSheet(f"color: {color}; font-size: 11px;")
        self.knowledge_status.setText(status_text)

    def get_writing_strategy(self):
        """获取写作策略配置"""
        return {
            "audience": self.combo_audience.currentText(),
            "tone": self.combo_tone.currentText(),
            "goal": self.goal_input.text(),
            "genre": self.combo_genre.currentText()
        }

    def is_low_power_mode(self):
        """是否低功耗模式"""
        return self.low_power_check.isChecked()

    def update_list(self, items):
        """外部调用此方法更新列表"""
        self.doc_list.clear()
        for i in items:
            self.doc_list.addItem(i)

    # ===========================================
    # 新增：主窗口可以调用的连接方法
    # ===========================================

    def connect_signals_to_main_window(self, main_window):
        """将所有信号连接到主窗口的槽函数"""
        # 人格管理
        self.btn_load_persona.clicked.connect(main_window.on_load_persona)
        self.btn_new_persona.clicked.connect(main_window.on_new_persona)

        # 文档管理
        self.btn_import.clicked.connect(main_window.on_import_document)
        self.doc_list.itemClicked.connect(lambda item: main_window.on_document_selected(item.text()))

        # 高级操作
        self.btn_analyze.clicked.connect(lambda: main_window.on_analyze_document(self._get_selected_file()))
        self.btn_mimic.clicked.connect(lambda: main_window.on_mimic_document(self._get_selected_file()))
        self.btn_continue.clicked.connect(lambda: main_window.on_continue_document(self._get_selected_file()))

        # 工作模式
        self.mode_combo.currentTextChanged.connect(lambda text: main_window.on_mode_changed(
            self.get_current_mode()))

        # 联网搜索
        self.web_search_check.toggled.connect(main_window.on_web_search_toggled)

        # 思维活跃度
        self.temp_slider.valueChanged.connect(
            lambda value: main_window.on_temperature_changed(value / 10.0))

        # 写作策略
        self.combo_audience.currentTextChanged.connect(
            lambda: main_window.on_strategy_changed(self.get_writing_strategy()))
        self.combo_tone.currentTextChanged.connect(
            lambda: main_window.on_strategy_changed(self.get_writing_strategy()))
        self.combo_genre.currentTextChanged.connect(
            lambda: main_window.on_strategy_changed(self.get_writing_strategy()))
        self.goal_input.textChanged.connect(
            lambda: main_window.on_strategy_changed(self.get_writing_strategy()))

    def _get_selected_file(self):
        """获取选中的文件"""
        items = self.doc_list.selectedItems()
        if not items:
            return None
        return items[0].text()