# ui/components/dashboard.py
"""
仪表盘组件 - 综合思维透视版 (合并版本)
整合：六维图、量子熵流图、关键词库、思维链视图
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QGroupBox,
    QTextEdit, QLabel, QTabWidget, QHBoxLayout,
    QSplitter, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSlot
import json

# ================= 组件导入 =================
try:
    from ui.components.radar_widget import EnhancedHexagonRadar

    HAS_RADAR = True
except ImportError:
    HAS_RADAR = False

try:
    from gui.entropy_plot import EnhancedQuantumEntropyPlot

    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False


class Dashboard(QWidget):
    """仪表盘组件 - 综合思维透视版"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """初始化UI - 标签页组织"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标签页容器
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #3e3e42; }
            QTabBar::tab { 
                background: #252526; 
                color: #aaa; 
                padding: 8px 12px; 
                font-weight: bold;
            }
            QTabBar::tab:selected { 
                background: #1e1e1e; 
                color: #fff; 
                border-top: 2px solid #007acc; 
            }
        """)

        # 初始化各标签页
        self.init_overview_tab()  # 概览页 - 原始版本主要内容
        self.init_thought_tab()  # 思维链页 - 思维透视版
        self.init_system_tab()  # 系统监控页
        self.init_analysis_tab()  # 分析页 - 原始版本详细内容

        layout.addWidget(self.tabs)

    # ================= 标签页1: 认知概览 =================
    def init_overview_tab(self):
        """Tab 1: 认知概览 (雷达图 + 关键词 + 风格画像)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 1. 雷达图 (如果可用)
        if HAS_RADAR:
            self.radar = EnhancedHexagonRadar()
            layout.addWidget(self.radar, 2)
        else:
            placeholder = QLabel("📡 六维雷达图组件未加载")
            placeholder.setStyleSheet("color: #ff6b6b; padding: 20px; font-size: 14px;")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(placeholder)

        # 2. 网格布局：关键词库 + 风格画像
        grid_layout = QGridLayout()

        # 左侧：核心关键词库 (原始版本)
        kw_group = QGroupBox("🔑 核心关键词库")
        kw_group.setStyleSheet("QGroupBox { font-weight: bold; color: #e0e0e0; }")
        kw_layout = QVBoxLayout(kw_group)
        self.txt_keywords = QTextEdit()
        self.txt_keywords.setReadOnly(True)
        self.txt_keywords.setPlaceholderText("等待文档注入以生成 DNA 画像...")
        self.txt_keywords.setStyleSheet("""
            QTextEdit {
                background: #252526;
                color: #d4d4d4;
                border: none;
                font-family: 'Consolas', 'Microsoft YaHei';
                font-size: 12px;
                padding: 5px;
            }
        """)
        kw_layout.addWidget(self.txt_keywords)
        grid_layout.addWidget(kw_group, 0, 0)

        # 右侧：风格画像 (原始版本简化版)
        meta_group = QGroupBox("🎭 风格画像概览")
        meta_group.setStyleSheet("QGroupBox { font-weight: bold; color: #e0e0e0; }")
        meta_layout = QVBoxLayout(meta_group)

        self.lbl_tone = QLabel("情感基调: --")
        self.lbl_tone.setStyleSheet("color: #d4d4d4; font-size: 13px; padding: 8px; border-bottom: 1px solid #3e3e42;")

        self.lbl_style = QLabel("特征模式: --")
        self.lbl_style.setStyleSheet("color: #d4d4d4; font-size: 13px; padding: 8px;")

        meta_layout.addWidget(self.lbl_tone)
        meta_layout.addWidget(self.lbl_style)
        meta_layout.addStretch()

        grid_layout.addWidget(meta_group, 0, 1)

        layout.addLayout(grid_layout, 1)

        self.tabs.addTab(tab, "📊 认知概览")

    # ================= 标签页2: 思维链 =================
    def init_thought_tab(self):
        """Tab 2: 思维链 (展示大纲、中间思考过程)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 说明标签
        desc_label = QLabel("🧠 AI 思考过程、大纲生成、策略调整将在此实时显示...")
        desc_label.setStyleSheet("color: #569cd6; font-size: 11px; padding: 5px; border-bottom: 1px solid #3e3e42;")
        layout.addWidget(desc_label)

        # 思维链文本区域
        self.txt_thought = QTextEdit()
        self.txt_thought.setReadOnly(True)
        self.txt_thought.setPlaceholderText("暂无思维链数据。等待AI分析过程开始...")
        self.txt_thought.setStyleSheet("""
            QTextEdit { 
                background-color: #1e1e1e; 
                color: #dcdcdc; 
                font-family: Consolas, "Microsoft YaHei";
                font-size: 11pt;
                border: none;
                padding: 10px;
            }
        """)
        layout.addWidget(self.txt_thought)

        self.tabs.addTab(tab, "🧠 思维链")

    # ================= 标签页3: 系统监控 =================
    def init_system_tab(self):
        """Tab 3: 系统监控 (熵流图 + 资源监控)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 熵流监控 (原始版本)
        if HAS_PLOT:
            ent_group = QGroupBox("🌊 熵流监控")
            ent_group.setStyleSheet("QGroupBox { font-weight: bold; color: #e0e0e0; }")
            el = QVBoxLayout(ent_group)
            self.entropy_plot = EnhancedQuantumEntropyPlot()
            el.addWidget(self.entropy_plot)
            layout.addWidget(ent_group, 3)
        else:
            # 如果模块不存在，创建一个占位符
            ent_group = QGroupBox("🌊 熵流监控 (模块未找到)")
            ent_group.setStyleSheet("QGroupBox { font-weight: bold; color: #e0e0e0; }")
            el = QVBoxLayout(ent_group)
            placeholder = QLabel("熵流监控模块未找到，请检查 gui.entropy_plot 模块")
            placeholder.setStyleSheet("color: #ff6b6b; padding: 20px;")
            el.addWidget(placeholder)
            layout.addWidget(ent_group, 3)

        # 系统资源监控 (思维透视版)
        sys_group = QGroupBox("⚡ 系统状态")
        sys_group.setStyleSheet("QGroupBox { font-weight: bold; color: #e0e0e0; }")
        sys_layout = QVBoxLayout(sys_group)

        self.lbl_resources = QLabel("CPU: 0% | 内存: 0% | GPU: 0%")
        self.lbl_resources.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_resources.setStyleSheet("""
            QLabel {
                color: #4fc3f7;
                font-size: 13px;
                padding: 10px;
                background: #252526;
                border-radius: 4px;
            }
        """)
        sys_layout.addWidget(self.lbl_resources)

        layout.addWidget(sys_group)

        self.tabs.addTab(tab, "⚡ 系统监控")

    # ================= 标签页4: 详细分析 =================
    def init_analysis_tab(self):
        """Tab 4: 详细分析 (原始版本的详细视图)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 词云视图 (原始版本复活版)
        self.word_group = QGroupBox("☁️ 核心词库 (词云视图)")
        self.word_group.setStyleSheet("QGroupBox { font-weight: bold; color: #e0e0e0; }")
        word_layout = QVBoxLayout(self.word_group)

        self.word_display = QTextEdit()
        self.word_display.setReadOnly(True)
        self.word_display.setPlaceholderText("暂无数据。请导入文档并点击【深度解读】以生成词库。")
        self.word_display.setStyleSheet("""
            QTextEdit { 
                background: #252526; 
                color: #4ec9b0; 
                border: 1px solid #3e3e42; 
                font-size: 14px; 
                padding: 10px;
                min-height: 150px;
            }
        """)
        word_layout.addWidget(self.word_display)
        layout.addWidget(self.word_group)

        # 详细风格画像 (原始版本复活版)
        self.style_group = QGroupBox("🎨 风格画像 (详细描述)")
        self.style_group.setStyleSheet("QGroupBox { font-weight: bold; color: #e0e0e0; }")
        style_layout = QVBoxLayout(self.style_group)

        self.style_display = QTextEdit()
        self.style_display.setReadOnly(True)
        self.style_display.setPlaceholderText("暂无数据。请加载人格或分析文档。")
        self.style_display.setStyleSheet("""
            QTextEdit { 
                background: #1e1e1e; 
                color: #ce9178; 
                border: 1px solid #3e3e42; 
                font-family: Consolas;
                font-size: 13px;
                padding: 10px;
                min-height: 200px;
            }
        """)
        style_layout.addWidget(self.style_display)
        layout.addWidget(self.style_group)

        self.tabs.addTab(tab, "📈 详细分析")

    # ================= 数据更新接口 (原始版本方法兼容) =================

    def update_keywords(self, keywords_text):
        """更新关键词显示 - 原始版本方法"""
        self.txt_keywords.setText(keywords_text)

        # 同时更新词云视图
        if keywords_text:
            keywords = [line.strip("• ").strip() for line in keywords_text.split("\n") if line.strip()]
            if keywords:
                self._update_word_cloud(keywords[:20])  # 限制最多20个关键词

    def update_style_profile(self, tone, style):
        """更新风格画像 - 原始版本方法"""
        self.lbl_tone.setText(f"情感基调: {tone}")
        self.lbl_style.setText(f"特征模式: {style}")

        # 同时更新详细风格描述
        style_desc = f"情感基调: {tone}\n\n风格特征: {style}"
        self.style_display.setText(style_desc)

    def update_entropy_plot(self, data):
        """更新熵流图 - 原始版本方法"""
        if hasattr(self, 'entropy_plot') and hasattr(self.entropy_plot, 'update_data_safe'):
            self.entropy_plot.update_data_safe(data)

    def update_dashboard(self, data):
        """
        更新仪表盘数据 - 原始版本复活方法
        data: 包含 'keywords' (list) 和 'style_desc' (str) 或 'analysis' (dict)
        """
        if not data:
            return

        # 更新词库 - 词云视图
        keywords = data.get('keywords', [])
        if keywords:
            self._update_word_cloud(keywords)

            # 同时更新原始关键词显示
            keywords_text = "\n".join([f"• {kw}" for kw in keywords[:15]])  # 限制显示数量
            self.txt_keywords.setText(keywords_text)

        # 更新风格画像
        style_desc = data.get('style_desc', "")
        if style_desc:
            self.style_display.setText(style_desc)

            # 尝试从描述中提取情感和特征
            if "情感基调:" in style_desc and "风格特征:" in style_desc:
                lines = style_desc.split("\n")
                for line in lines:
                    if line.startswith("情感基调:"):
                        tone = line.replace("情感基调:", "").strip()
                        self.lbl_tone.setText(f"情感基调: {tone}")
                    elif line.startswith("风格特征:"):
                        style = line.replace("风格特征:", "").strip()
                        self.lbl_style.setText(f"特征模式: {style}")

        # 如果有分析数据
        analysis = data.get('analysis')
        if analysis:
            try:
                if isinstance(analysis, dict):
                    self.style_display.setText(json.dumps(analysis, indent=2, ensure_ascii=False))
                else:
                    self.style_display.setText(str(analysis))
            except:
                self.style_display.setText("分析数据格式异常")

        # 切换到详细分析标签页
        self.tabs.setCurrentIndex(3)

    # ================= 数据更新接口 (思维透视版方法) =================

    @pyqtSlot(dict)
    def update_data(self, data):
        """更新所有数据 - 思维透视版方法"""
        # 1. 更新雷达图
        if HAS_RADAR and "radar_metrics" in data:
            self.radar.update_data(data["radar_metrics"])

        # 2. 更新关键词
        if "semantic_summary" in data:
            summary = data["semantic_summary"]
            keywords = summary.get("keywords", [])
            if keywords:
                # 格式化显示
                kw_text = " | ".join([f"{k}({w:.2f})" for k, w in keywords[:10]])
                self.txt_keywords.setText(kw_text)

                # 同时更新词云
                kw_list = [k for k, _ in keywords[:15]]
                self._update_word_cloud(kw_list)

            # 更新风格描述
            tone = summary.get("tone_analysis", {}).get("primary_tone", "未知")
            style = summary.get("style_features", "未知")
            self.update_style_profile(tone, style)

    @pyqtSlot(str)
    def append_log(self, message):
        """追加日志到思维链 - 思维透视版方法"""
        # 自动切换到思维链 Tab，如果消息包含特定关键词
        if any(key in message for key in ["大纲", "思考", "策略", "分析", "生成", "总结"]):
            self.tabs.setCurrentIndex(1)

        # 添加时间戳
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 根据消息类型添加不同颜色
        if any(word in message for word in ["错误", "失败", "异常", "警告"]):
            html = f'<div style="color:#f44336; margin:2px;">[{timestamp}] {message}</div>'
        elif any(word in message for word in ["成功", "完成", "就绪"]):
            html = f'<div style="color:#4caf50; margin:2px;">[{timestamp}] {message}</div>'
        elif any(word in message for word in ["思考", "分析", "推理"]):
            html = f'<div style="color:#2196f3; margin:2px;">[{timestamp}] {message}</div>'
        else:
            html = f'<div style="color:#e0e0e0; margin:2px;">[{timestamp}] {message}</div>'

        current_html = self.txt_thought.toHtml()
        self.txt_thought.setHtml(current_html + html)

        # 滚动到底部
        sb = self.txt_thought.verticalScrollBar()
        sb.setValue(sb.maximum())

    @pyqtSlot(dict)
    def update_system_stats(self, stats):
        """更新系统监控数据 - 思维透视版方法"""
        if hasattr(self, 'entropy_plot') and hasattr(self.entropy_plot, 'update_data_safe'):
            self.entropy_plot.update_data_safe(stats)

        cpu = stats.get('cpu', 0)
        mem = stats.get('memory', 0)
        gpu = stats.get('gpu', 0)
        self.lbl_resources.setText(f"CPU: {cpu:.1f}% | 内存: {mem:.1f}% | GPU: {gpu:.1f}%")

        # 高负载警告
        if cpu > 80 or mem > 80:
            self.lbl_resources.setStyleSheet("color: #ff6b6b; font-weight: bold;")

    # ================= 辅助方法 =================

    def _update_word_cloud(self, keywords):
        """更新词云显示"""
        if not keywords:
            self.word_display.clear()
            return

        # 简单的词云模拟展示
        html = "<div style='line-height: 1.8; text-align: center; padding: 10px;'>"
        for i, w in enumerate(keywords[:20]):  # 限制显示数量
            size = 14 + (i % 4) * 6  # 根据索引调整大小
            colors = ["#4ec9b0", "#569cd6", "#dcdcaa", "#9cdcfe", "#c586c0", "#d16969"]
            color = colors[i % len(colors)]
            html += f"<span style='font-size:{size}px; color:{color}; margin: 8px; display: inline-block;'>{w}</span> "
        html += "</div>"
        self.word_display.setHtml(html)

    def clear_all(self):
        """清空所有显示"""
        # 原始版本组件
        self.txt_keywords.clear()
        self.lbl_tone.setText("情感基调: --")
        self.lbl_style.setText("特征模式: --")
        self.word_display.clear()
        self.style_display.clear()

        # 思维透视版组件
        self.txt_thought.clear()
        self.lbl_resources.setText("CPU: 0% | 内存: 0% | GPU: 0%")
        self.lbl_resources.setStyleSheet("color: #4fc3f7;")

        # 清除图形组件
        if hasattr(self, 'entropy_plot') and hasattr(self.entropy_plot, 'clear'):
            self.entropy_plot.clear()

        if HAS_RADAR and hasattr(self, 'radar'):
            self.radar.clear()

    def set_active_tab(self, tab_index):
        """设置当前活动标签页"""
        if 0 <= tab_index < self.tabs.count():
            self.tabs.setCurrentIndex(tab_index)

    def get_current_tab_name(self):
        """获取当前标签页名称"""
        return self.tabs.tabText(self.tabs.currentIndex())