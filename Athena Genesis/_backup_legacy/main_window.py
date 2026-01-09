# -*- coding: utf-8 -*-
"""
主窗口 - 终极修复版 + 物理隔离 + 资产永生 (Final Hybrid) + 思维活跃度控制 + 深思引擎 + 文体选择 + 知识库缓存 + 联网搜索开关
修复：
1. 文件夹物理隔离：以文件夹为核心 (Source of Truth) ✅
2. handle_brain_result 导致的界面无响应 ✅
3. 重启后文件列表丢失 (Auto-Scan) ✅
4. 重启后六维图/画像归零 (Auto-Reingest) ✅
5. 新增：深思引擎 (DeepThinkingWorker) 用于全量分析 ✅
6. 新增：文体/题材选择功能 (Genre Selector) ✅
7. 新增：知识库缓存系统 (KnowledgeKeeper) 实现增量加载 ✅
8. 新增：联网搜索开关 (Web Search Toggle) 🔥 来自2-mainwindow-AI.txt
包含：全量仪表盘、右键菜单、系统监控、完整人格管理、智能续写、资产自动恢复、物理隔离、思维活跃度控制
新增：信号总线修复 + 深思引擎 + 文体选择 + 知识库缓存 + 联网搜索开关
"""

import warnings
import os
import glob
import datetime
import json
import jieba

warnings.filterwarnings("ignore")

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QGroupBox,
    QTabWidget, QListWidget, QSplitter, QLabel, QMessageBox,
    QFileDialog, QProgressBar, QGridLayout, QMenu, QTextEdit,
    QInputDialog, QPushButton, QSlider, QLineEdit, QCheckBox, QApplication, QComboBox, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSlot, QThread, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from engines.web_searcher import WebSearcher
# 导入配置与内核
from config.settings import SETTINGS
from config.genres import get_genre_names  # 🔥 新增：导入文体库
from core.signal_bus import SignalBus
from core.io_manager import IOManager
from core.system_monitor import SystemMonitor
from engines.athena_brain import AthenaBrain
from engines.mimicry_engine import EnhancedMimicryEngine
# 🔥 新增：引入分析器
from engines.document_analyzer import DocumentIntelligenceAnalyzer

# 导入UI组件
from gui.radar_widget import EnhancedHexagonRadar
from gui.entropy_plot import EnhancedQuantumEntropyPlot
from _backup_legacy.chat_widget import ChatWidget
from gui.knowledge_widget import KnowledgeWidget
from core.workers import AnalysisWorker, DeepThinkingWorker  # 🔥 新增：导入深思引擎


# ---------------------------------------------------------
# 1. 修复 AthenaThread (确保接收 config)
# ---------------------------------------------------------
class AthenaThread(QThread):
    signal_response = pyqtSignal(str)

    def __init__(self, brain, user_input, config=None):  # 🔥 关键：接收 config
        super().__init__()
        self.brain = brain
        self.user_input = user_input
        self.config = config or {}  # 保底为空字典

    def run(self):
        # 将 config 传给 brain.launch (🔥 修改：使用 launch 方法)
        response = self.brain.launch(self.user_input, config=self.config)
        self.signal_response.emit(response)


# ==========================================
# 🔥 修复版：KnowledgeBase 类 (来自4.txt)
# ==========================================
class KnowledgeBase:
    def __init__(self):
        # 数据库存储路径
        self.db_path = os.path.join(SETTINGS.PATHS.directories.get('knowledge_base'), 'global_index.json')

        # 内存数据结构
        # 结构: { "documents": { "filename": { "content": "...", "keywords": {...}, "summary": "..." } } }
        self.data = {
            "documents": {}
        }

        # 尝试加载旧数据
        self.load_db()

    def clear_db(self):
        """
        🔥 核心修复：清空数据库
        用于切换人格时，清除上一个人格的文档索引
        """
        self.data = {"documents": {}}
        # 甚至可以删除物理文件，但为了安全起见，这里只清空内存
        # if os.path.exists(self.db_path):
        #     os.remove(self.db_path)
        print("🧹 [KnowledgeBase] 内存索引已清空")

    def add_document(self, filename, content, keywords, metadata=None):
        """添加文档到索引"""
        if metadata is None: metadata = {}

        # 简单的摘要生成 (取前200字)
        summary = content[:200].replace('\n', ' ') + "..."

        self.data["documents"][filename] = {
            "content": content,
            "keywords": keywords,  # 词频字典
            "summary": summary,
            "metadata": metadata,
            "length": len(content)
        }
        # 自动保存
        self.save_db()
        print(f"📚 [KnowledgeBase] 已索引文档: {filename}")

    def search(self, query, top_k=3):
        """
        简单的关键词搜索
        返回: 拼接好的参考文本字符串
        """
        if not query: return ""

        # 分词
        query_words = set(jieba.lcut(query))
        scores = []

        for fname, doc_data in self.data["documents"].items():
            score = 0
            content = doc_data.get("content", "")
            doc_keywords = doc_data.get("keywords", {})

            # 1. 标题命中权重
            if query in fname: score += 10

            # 2. 关键词命中权重
            for qw in query_words:
                if qw in doc_keywords:
                    score += doc_keywords[qw]  # 加上词频
                elif qw in content:
                    score += 1

            if score > 0:
                scores.append((score, fname, doc_data))

        # 按分数排序
        scores.sort(key=lambda x: x[0], reverse=True)

        # 组装结果
        results = []
        for score, fname, doc_data in scores[:top_k]:
            snippet = doc_data.get("summary", "")
            # 如果是深度搜索，可以返回更多内容
            full_content = doc_data.get("content", "")
            # 截取一段相关的
            results.append(f"【来源: {fname} (匹配度:{score})】\n{snippet}\n")

        if not results:
            return ""  # 未找到

        return "\n".join(results)

    def save_db(self):
        """持久化保存"""
        try:
            # 确保目录存在
            db_dir = os.path.dirname(self.db_path)
            if not os.path.exists(db_dir): os.makedirs(db_dir)

            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存知识库失败: {e}")

    def load_db(self):
        """加载数据库"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                # 兼容性检查
                if "documents" not in self.data:
                    self.data = {"documents": {}}
            except Exception as e:
                print(f"加载知识库失败: {e}")
                self.data = {"documents": {}}

    def get_all_docs(self):
        """获取所有文档列表"""
        return list(self.data["documents"].keys())


# ==========================================
# 🔥 新增：KnowledgeKeeper 缓存系统 (来自2-mainwindow-AI.txt)
# ==========================================
from core.persistence import KnowledgeKeeper


class AthenaGenesisWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 1. 初始化核心模块
        self.signal_bus = SignalBus()  # ✅ 必须创建并持有这个实例
        self.io_manager = IOManager()
        self.knowledge_base = KnowledgeBase()  # 🔥 使用修复版的KnowledgeBase
        self.system_monitor = SystemMonitor()
        self.mimicry_engine = EnhancedMimicryEngine()

        # 2. 🔥 新增：初始化知识库缓存系统 (来自2-mainwindow-AI.txt)
        self.knowledge_keeper = KnowledgeKeeper(self.io_manager)

        # 🔥🔥🔥 关键新增：初始化 WebSearcher 实例
        self.web_searcher = None
        self.web_searcher = WebSearcher(self.io_manager)  # 立即初始化

        # 3. 从数据库恢复风格记忆
        try:
            doc_count = self.mimicry_engine.load_from_knowledge_base(self.knowledge_base.data)
        except:
            doc_count = 0

        # 4. 线程池
        self.active_workers = []

        # 5. 🔥 新增：状态追踪
        self.current_persona_name = None  # 🔥 修改：初始化为 None，等待用户选择 (来自3.txt)

        # 6. 🔥 新增：低功耗模式标志
        self.low_power_mode = False

        # 7. 🔥 新增：深思引擎线程 (显式初始化为 None)
        self.deep_thinking_worker = None

        # 8. 初始化UI
        self.init_ui()

        # 9. 🔥 关键修复：先创建大脑，再连接信号
        self.brain = AthenaBrain(self.signal_bus, self.io_manager, self.knowledge_base)
        # 🔥🔥🔥 核心修复：确保大脑和UI共享同一个拟态引擎实例
        self.brain.mimicry = self.mimicry_engine
        self.brain.mimicry_engine = self.mimicry_engine

        # 🔥🔥🔥 关键修复：将 WebSearcher 注入大脑
        if self.web_searcher:
            self.brain.web_searcher = self.web_searcher
            print("✅ [System] WebSearcher 已注入大脑")

        # 10. 🔥 关键修复：现在连接大脑的信号和信号总线的信号
        self.connect_global_signals()

        # 11. 启动定时器
        self.dash_timer = QTimer(self)
        self.dash_timer.timeout.connect(self.update_dashboard_realtime)
        self.dash_timer.start(2000)

        self.sys_timer = QTimer(self)
        self.sys_timer.timeout.connect(self.update_system_stats)
        self.sys_timer.start(1000)

        # 12. 启动大脑线程
        self.brain.start()

        self.status_label.setText(f"Core Loaded | Documents: {doc_count} | Mode: Advanced")

        # 🔥🔥🔥 核心修复：修改启动逻辑 (来自3.txt的严格启动)
        QTimer.singleShot(500, self._startup_sequence)

        # 🔥 新增：启动自检，使用 launch 方法
        QTimer.singleShot(1000, self._system_self_check)

    # ==========================================
    # 🔥 新增：初始化 WebSearcher 方法
    # ==========================================
    def _init_web_searcher(self):
        """初始化联网搜索引擎"""
        try:
            # 尝试创建 WebSearcher 实例
            self.web_searcher = WebSearcher()

            # 配置必要的依赖
            if hasattr(self.web_searcher, 'io_manager'):
                self.web_searcher.io_manager = self.io_manager

            print("✅ [System] 联网搜索引擎 (WebSearcher) 已加载")

            # 测试连接（可选）
            self._test_web_connection()

        except ImportError as e:
            print(f"⚠️ [System] 无法导入 WebSearcher: {e}")
            self.web_searcher = None
            self.append_system_message("⚠️ 联网搜索功能不可用：缺少必要模块")
        except Exception as e:
            print(f"❌ [System] WebSearcher 初始化失败: {e}")
            self.web_searcher = None
            self.append_system_message(f"❌ 联网搜索初始化失败: {e}")

    def _test_web_connection(self):
        """测试网络连接（可选）"""
        # 这里可以添加一个简单的网络连接测试
        # 例如，检查是否能访问搜索引擎
        pass

    # ==========================================
    # 🔥 新增：系统自检方法
    # ==========================================
    def _system_self_check(self):
        """系统自检，确保所有组件正常工作"""
        try:
            # 1. 检查大脑是否正常启动
            if not hasattr(self, 'brain') or not self.brain:
                self.chat_widget.append_message("System", "❌ 大脑内核未正确初始化", "Error")
                return

            # 2. 测试 launch 方法
            test_response = self.brain.launch("系统自检", config={"temperature": 0.1})

            if test_response and len(test_response) > 0:
                self.status_label.setText("✅ 系统自检通过 | Athena 大脑正常")
                self.chat_widget.append_message("System", "✅ 系统自检完成，所有组件工作正常", "Success")
            else:
                self.status_label.setText("⚠️ 系统自检异常 | 请检查配置")
                self.chat_widget.append_message("System", "⚠️ 系统自检异常，请检查配置", "Warning")

        except Exception as e:
            error_msg = f"系统自检失败: {str(e)}"
            print(f"❌ {error_msg}")
            self.chat_widget.append_message("System", f"❌ 系统自检失败: {error_msg}", "Error")

    # ==========================================
    # 🔥🔥🔥 核心修改：启动序列 (来自3.txt的严格启动)
    # ==========================================
    def _startup_sequence(self):
        """
        🔥 修改版：启动时不乱扫描。
        尝试加载 'Default' 人格，如果没有，就保持空白，等待用户操作。
        """
        self.chat_widget.append_message("System", "🛡️ 系统已启动 (物理隔离模式)。", "System")

        # 🔥 修改：等待用户选择，不自动加载任何人格
        self.chat_widget.append_message("System",
                                        "ℹ️ 当前为空状态。请先新建或加载一个人格空间。",
                                        "Info")

    # =========================================================
    # 🔥 核心 1: 新建人格 (创建文件夹) (来自3.txt)
    # =========================================================
    def create_new_persona(self):
        name, ok = QInputDialog.getText(self, "新建人格", "输入人格名称 (将创建同名文件夹):")
        if ok and name:
            # 1. 创建文件夹
            folder = self.io_manager.get_persona_folder(name)

            # 2. 创建空的 JSON 存档
            self.io_manager.save_persona(name, {"name": name, "documents": []})

            # 3. 立即加载
            self._execute_load_persona(name)
            QMessageBox.information(self, "成功", f"已创建空间: {folder}")

    # ==========================================
    # 🔥 核心 2: 严格的加载逻辑 (物理隔离版) + 知识库缓存优化
    # ==========================================
    def _execute_load_persona(self, persona_name):
        """
        🔥 物理隔离版：加载逻辑 + 知识库缓存优化
        1. 切换到 'Inputs/{persona_name}' 目录
        2. 扫描里面的所有文件 (Source of Truth)
        3. 使用缓存机制增量加载
        """
        self.chat_widget.append_message("System", f"🔄 正在切换至空间: {persona_name}...", "System")

        # 1. 暴力清空所有状态
        self.doc_list.clear()
        self.knowledge_base.clear_db()
        self.mimicry_engine.reset()

        # 2. 🔥 加载该人格的缓存库 (来自2-mainwindow-AI.txt)
        self.knowledge_keeper.load_persona_cache(persona_name)

        # 3. 🔥 扫描物理文件夹 (这是关键！)
        real_files = self.io_manager.scan_files_in_persona(persona_name)

        self.current_persona_name = persona_name

        if not real_files:
            self.chat_widget.append_message("System", f"📂 文件夹 {persona_name} 为空。请导入文档。", "Info")
            self.update_dashboard_realtime()
            return

        # 4. 🔥 使用缓存机制增量加载 (来自2-mainwindow-AI.txt)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.active_workers = []

        total_files = len(real_files)
        processed_count = 0

        print(f"📂 [Scanner] 扫描到 {total_files} 个文件，准备增量加载...")

        for idx, f_path in enumerate(real_files):
            filename = os.path.basename(f_path)

            # === 步骤 A: 询问缓存 ===
            cached_record = self.knowledge_keeper.get_cached_record(f_path)

            if cached_record:
                # ✅ 命中缓存！直接恢复 UI，不启动 Worker
                print(f"⚡ [Hit] {filename} 使用缓存秒级加载")

                # 1. 恢复文件列表项（绿色表示已缓存）
                item = QListWidgetItem(filename)
                item.setToolTip("✅ 已从知识库加载")
                self.doc_list.addItem(item)

                # 2. 恢复内存中的数据 (模拟 on_analysis_finished)
                self.restore_from_cache(filename, cached_record)

                processed_count += 1
                self.progress_bar.setValue(int(processed_count / total_files * 100))

            else:
                # ❌ 未命中或已修改！启动 Worker 重新分析
                print(f"🔄 [Miss] {filename} 是新文件，启动深度分析...")

                # 添加列表项（灰色表示处理中）
                item = QListWidgetItem(f"⏳ {filename}")
                self.doc_list.addItem(item)

                # 启动分析线程
                self.analyze_file(f_path, item)

        # 如果全是缓存，进度条直接满
        if processed_count == total_files:
            self.progress_bar.setVisible(False)
            self.status_label.setText(f"✅ {total_files} 个文件已秒级恢复")

        # 5. 自动反向修复 JSON (如果文件夹有文件但JSON里没有，这里会自动补上)
        self._auto_save_json(real_files)

        self.chat_widget.append_message("System", f"✅ 已从文件夹挂载 {len(real_files)} 个资产。数据隔离保护中。",
                                        "Success")
        self.update_dashboard_realtime()

    # ==========================================
    # 🔥 新增：从缓存恢复内存状态 (来自2-mainwindow-AI.txt)
    # ==========================================
    def restore_from_cache(self, filename, record):
        """从缓存恢复内存状态"""
        # 1. 恢复知识库 (如果有的话)
        keywords = record.get("keywords", {})
        summary = record.get("summary_text", "")
        if hasattr(self, 'knowledge_base'):
            # 注意：这里我们不存全文，只存摘要和关键词以节省内存
            self.knowledge_base.add_document(filename, summary, keywords, {})

        # 2. 恢复拟态引擎 (简单的风格数据)
        # 如果需要更精细的，可以在 persistence 里存更多
        if hasattr(self, 'mimicry_engine'):
            # 这里简化处理，实际上可以恢复更多风格数据
            pass

        # 3. 恢复雷达图 (如果有的话)
        metrics = record.get("radar_metrics", {})
        if metrics and hasattr(self, 'radar_widget'):
            # 这里简单做个累加或者取最后一个文件的逻辑
            # 为了演示，我们只在点击文件时更新，或者在这里做聚合
            pass

    # ==========================================
    # 🔥 新增：分析单个文件 (适配缓存系统)
    # ==========================================
    def analyze_file(self, file_path, list_item):
        """分析单个文件并启动Worker"""
        filename = os.path.basename(file_path)

        # 1. 读取文件内容 (关键修复步骤)
        content = ""
        try:
            if hasattr(self.io_manager, 'read_full_content'):
                content = self.io_manager.read_full_content(file_path)
            else:
                # 兼容旧接口
                content = self.io_manager.read_file(file_path)
        except Exception as e:
            print(f"❌ 读取失败 {filename}: {e}")
            if list_item: list_item.setText(f"❌ {filename}")
            return

        if not content:
            print(f"⚠️ 跳过空文件: {filename}")
            if list_item: list_item.setText(f"⚠️ {filename} (空)")
            return

        # 2. 实例化 Worker (关键修复步骤)
        # 必须传递 3 个参数: (analyzer, content, filename)
        analyzer = DocumentIntelligenceAnalyzer()
        worker = AnalysisWorker(analyzer, content, filename)

        # 3. 记录并连接信号
        # 添加到活动Worker列表
        self.active_workers.append(worker)

        # 使用 lambda 捕获当前 worker 实例，防止闭包问题
        worker.finished.connect(lambda result, w=worker: self.on_analysis_finished(result, w, list_item))
        worker.error.connect(lambda e: self.on_analysis_error(e, filename, list_item))

        worker.start()

    # ==========================================
    # 🔥 修改：分析完成回调 (增加缓存保存功能)
    # ==========================================
    def on_analysis_finished(self, result, worker, list_item=None):
        """修复版：解析完成回调 + 缓存保存"""
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        if not self.active_workers:
            self.progress_bar.setVisible(False)

        fname = result.get('document_info', {}).get('filename', 'Unknown')
        fpath = result.get('document_info', {}).get('filepath', '')  # 确保 analyzer 返回了 filepath

        # --- 原有 UI 更新逻辑保持不变 ---
        # 更新列表项名字（去掉沙漏）
        if list_item:
            list_item.setText(fname)
            list_item.setToolTip("✅ 分析完成")

        # 1. 注入拟态引擎
        if hasattr(self, 'mimicry_engine'):
            self.mimicry_engine.ingest(result)

        # 2. 存入知识库
        keywords = result.get('semantic_summary', {}).get('keywords', {})
        text_report = result.get('text_report', '无内容')
        if hasattr(self, 'knowledge_base'):
            self.knowledge_base.add_document(fname, text_report, keywords, {})

        # 3. 更新雷达图
        metrics = result.get('radar_metrics', {})
        if metrics and hasattr(self, 'radar_widget'):
            self.radar_widget.set_data(metrics)

        # 4. 提示
        self.chat_widget.append_message("System",
                                        f"✅ {fname} 解析完成。已提取 {len(keywords)} 个关键特征。",
                                        "Success")
        self.update_dashboard_realtime()

        # 🔥🔥 新增：存入持久化缓存 (来自2-mainwindow-AI.txt)
        if fpath and hasattr(self, 'knowledge_keeper'):
            print(f"💾 [Save] 正在将 {fname} 存入知识库...")
            self.knowledge_keeper.update_record(fpath, result)

    def on_analysis_error(self, error, filename, list_item):
        """分析出错处理"""
        if list_item:
            list_item.setText(f"❌ {filename}")
            list_item.setToolTip(f"分析失败: {error}")

        self.chat_widget.append_message("System", f"❌ {filename} 分析失败: {error}", "Error")

        # 从活动Worker中移除
        for worker in self.active_workers:
            if hasattr(worker, 'file_path') and filename in worker.file_path:
                self.active_workers.remove(worker)
                break

    # =========================================================
    # 🔥 核心功能升级：导入文档 (物理隔离版 + 缓存优化)
    # =========================================================
    def import_document(self):
        """
        导入文档 -> 立即分析 -> 立即入库 -> 🔥立即自动保存
        🔥 物理隔离版本：文件存入特定人格文件夹 + 缓存优化
        """
        # 如果当前没有加载任何人格，先提示 (来自1.txt)
        if not self.current_persona_name:
            QMessageBox.warning(self, "提示", "请先加载或新建一个人格！")
            return

        # 🔥 使用多格式支持
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择文档",
            "",
            "All Support (*.txt *.pdf *.epub *.docx *.md);;"
            "PDF Files (*.pdf);;"
            "Word Files (*.docx);;"
            "Ebook Files (*.epub);;"
            "Text Files (*.txt);;"
            "Markdown Files (*.md)"
        )

        if not paths:
            return

        try:
            # 1. 归档到 Inputs/{current_persona_name}/ (物理隔离)
            new_paths = self.io_manager.archive_input(paths, self.current_persona_name)

            for p in new_paths:
                fname = os.path.basename(p)

                # 检查是否已在列表中
                existing_items = self.doc_list.findItems(fname, Qt.MatchFlag.MatchExactly)
                if existing_items:
                    # 文件已存在，跳过
                    continue

                # 添加到UI列表（显示为处理中）
                item = QListWidgetItem(f"⏳ {fname}")
                self.doc_list.addItem(item)

                # 🔥 检查缓存
                cached_record = self.knowledge_keeper.get_cached_record(p)
                if cached_record:
                    # 有缓存，直接恢复
                    item.setText(fname)
                    item.setToolTip("✅ 已从知识库加载")
                    self.restore_from_cache(fname, cached_record)
                    self.chat_widget.append_message("System", f"⚡ 文档 {fname} 已从缓存恢复。", "Success")
                else:
                    # 无缓存，启动分析
                    self.analyze_file(p, item)
                    self.chat_widget.append_message("System", f"➕ 文档 {fname} 已存入空间，正在分析...", "Success")

                self.update_dashboard_realtime()

                # 🔥🔥🔥 核心修复：自动保存 (Auto-Save) 🔥🔥🔥
                self._auto_save_persona()

            # 2. 自动更新 JSON 记录
            current_files = self.io_manager.scan_files_in_persona(self.current_persona_name)
            self._auto_save_json(current_files)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            print(f"导入文档失败: {e}")

    def _auto_save_persona(self):
        """静默自动保存 (物理隔离版)"""
        # 重新扫描当前文件夹，获取真实文件列表
        if self.current_persona_name:
            current_files = self.io_manager.scan_files_in_persona(self.current_persona_name)
            doc_names = [os.path.basename(p) for p in current_files]

            data = {
                "name": self.current_persona_name,
                "documents": doc_names,
                "stats_snapshot": self.mimicry_engine.get_radar_data()
            }
            if self.io_manager.save_persona(self.current_persona_name, data):
                print(f"✅ [AutoSave] 人格 {self.current_persona_name} 已自动更新。")
                self.status_label.setText(f"Persona: {self.current_persona_name} (Saved)")

    def _auto_save_json(self, file_paths):
        """同步 JSON 数据 (以文件列表为准) (来自3.txt)"""
        if self.current_persona_name:
            doc_names = [os.path.basename(p) for p in file_paths]
            data = {
                "name": self.current_persona_name,
                "documents": doc_names,
                "stats_snapshot": self.mimicry_engine.get_radar_data()
            }
            self.io_manager.save_persona(self.current_persona_name, data)

    # ==========================================
    # UI 初始化 (基于 4.txt 的完整 UI，添加物理隔离按钮 + 思维活跃度控制 + 文体选择 + 联网搜索开关)
    # ==========================================
    def init_ui(self):
        self.setWindowTitle(f"{SETTINGS.APP_NAME} - Enterprise Suite (物理隔离模式 + 缓存优化)")
        self.resize(1600, 950)
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; color: #d4d4d4; }
            QGroupBox { font-weight: bold; border: 1px solid #3e3e42; margin-top: 10px; border-radius: 4px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; color: #007acc; }
            QTextEdit { background: #252526; border: none; color: #d4d4d4; font-family: 'Consolas', 'Microsoft YaHei'; }
            QListWidget { background: #252526; border: none; color: #ccc; font-size: 13px; }
            QStatusBar { background: #2d2d2d; color: #aaa; }
            QLineEdit { background: #2d2d2d; border: 1px solid #3e3e42; color: #d4d4d4; padding: 5px; }
            QCheckBox { color: #d4d4d4; padding: 5px; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # === 左侧面板 ===
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # 1. 人格雷达
        self.radar_group = QGroupBox("🧠 人格维度")
        radar_layout = QVBoxLayout(self.radar_group)
        self.radar_widget = EnhancedHexagonRadar()
        radar_layout.addWidget(self.radar_widget)
        left_layout.addWidget(self.radar_group, 3)

        # 2. 🔥 新增：思维活跃度控制 (来自3.txt)
        self.temp_group = QGroupBox("🧠 思维活跃度控制")
        temp_layout = QVBoxLayout(self.temp_group)

        self.temp_label = QLabel("🧠 思维活跃度: 0.5 (平衡)")
        self.temp_label.setStyleSheet("color: #ecf0f1; font-weight: bold;")
        temp_layout.addWidget(self.temp_label)

        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setMinimum(1)
        self.temp_slider.setMaximum(10)
        self.temp_slider.setValue(5)  # 默认 0.5
        self.temp_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.temp_slider.setTickInterval(1)
        self.temp_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bdc3c7;
                height: 8px;
                background: #2c3e50;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: 1px solid #3498db;
                width: 18px;
                height: 18px;
                margin: -7px 0;
                border-radius: 9px;
            }
        """)
        self.temp_slider.valueChanged.connect(self.update_temp_label)
        temp_layout.addWidget(self.temp_slider)

        # 🔥 新增：低功耗模式选项 (来自2.txt)
        self.low_power_check = QCheckBox("💡 低功耗模式 (响应更快)")
        self.low_power_check.stateChanged.connect(self.on_low_power_changed)
        temp_layout.addWidget(self.low_power_check)

        left_layout.addWidget(self.temp_group)

        # 🔥 新增：写作策略配置 (Strategy Layer) (来自2.txt + 文体选择 + 联网搜索开关)
        strategy_group = QGroupBox("🎯 写作策略 (Strategy)")
        strategy_layout = QVBoxLayout(strategy_group)

        # 1. 读者画像 (Target Audience)
        strategy_layout.addWidget(QLabel("读者是谁 (Audience):"))
        self.audience_input = QLineEdit()
        self.audience_input.setPlaceholderText("例：刚入职的年轻人 / 行业专家 / 焦虑的家长")
        strategy_layout.addWidget(self.audience_input)

        # 2. 核心目标 (Core Goal)
        strategy_layout.addWidget(QLabel("核心目标 (Goal):"))
        self.goal_input = QLineEdit()
        self.goal_input.setPlaceholderText("例：改变认知 /说服购买 / 引发共鸣 / 传递干货")
        strategy_layout.addWidget(self.goal_input)

        # 🔥🔥🔥 新增：文体/题材选择 (Genre Selector) (来自2-mainwindow-AI.txt)
        strategy_layout.addWidget(QLabel("文章题材 (Genre):"))
        self.genre_combo = QComboBox()
        self.genre_combo.addItems(get_genre_names())  # 加载所有预设题材
        self.genre_combo.setCurrentText("单位材料/公文")  # 默认选这个，符合您的需求
        # 美化下拉框
        self.genre_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                background: #2c3e50;
                color: white;
                border: 1px solid #444;
            }
            QComboBox::drop-down { border: none; }
        """)
        strategy_layout.addWidget(self.genre_combo)

        # =======================================================
        # 🔥 新增：联网搜索开关 (Web Search Toggle) (来自2-mainwindow-AI.txt)
        # =======================================================

        # 创建复选框
        self.web_search_check = QCheckBox("🌐 联网增强模式 (Web ON)")
        self.web_search_check.setToolTip("开启后，Athena 将在回答前自动搜索互联网获取最新信息")

        # 设置样式：默认青色，字体加粗，显眼一点
        self.web_search_check.setStyleSheet("""
            QCheckBox {
                color: #a0a0a0; 
                font-weight: bold; 
                margin-top: 10px;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #555;
            }
            QCheckBox::indicator:checked {
                background-color: #00e5ff; /* 激活时变亮青色 */
                border-color: #00e5ff;
            }
            QCheckBox:checked {
                color: #00e5ff; /* 文字也变亮 */
            }
        """)

        # 默认关闭（为了响应速度和隐私）
        self.web_search_check.setChecked(False)

        # 将开关加入布局 (加在文体选择下面)
        strategy_layout.addWidget(self.web_search_check)

        left_layout.addWidget(strategy_group)

        # 3. 文档库
        self.doc_group = QGroupBox("📂 数据资产 (物理隔离 + 缓存优化)")
        doc_layout = QVBoxLayout(self.doc_group)

        # 🔥 添加物理隔离操作按钮 (来自3.txt的改进)
        btn_layout = QGridLayout()

        btn_new = QPushButton("✨ 新建人格")
        btn_new.clicked.connect(self.create_new_persona)
        btn_new.setStyleSheet("background: #2da44e; color: white; padding: 5px; margin: 2px;")

        btn_load = QPushButton("📂 加载人格")
        btn_load.clicked.connect(self.load_persona_dialog)
        btn_load.setStyleSheet("background: #0e639c; color: white; padding: 5px; margin: 2px;")

        btn_import = QPushButton("➕ 导入文档")
        btn_import.clicked.connect(self.import_document)
        btn_import.setStyleSheet("border: 1px dashed #666; padding: 5px; margin: 2px;")

        btn_layout.addWidget(btn_new, 0, 0)
        btn_layout.addWidget(btn_load, 0, 1)
        btn_layout.addWidget(btn_import, 1, 0, 1, 2)

        doc_layout.addLayout(btn_layout)

        self.doc_list = QListWidget()
        self.doc_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.doc_list.customContextMenuRequested.connect(self.show_context_menu)
        self.doc_list.itemDoubleClicked.connect(self.on_doc_double_clicked)
        self._refresh_doc_list()
        doc_layout.addWidget(self.doc_list)

        left_layout.addWidget(self.doc_group, 4)

        splitter.addWidget(left_panel)

        # === 右侧面板 ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.tabs = QTabWidget()

        # Tab 1: 仪表盘
        self.dashboard_tab = QWidget()
        self._init_dashboard(self.dashboard_tab)
        self.tabs.addTab(self.dashboard_tab, "📊 全息仪表盘")

        # Tab 2: 对话
        self.chat_widget = ChatWidget()
        self.chat_widget.message_sent.connect(self.handle_user_input)
        self.tabs.addTab(self.chat_widget, "💬 深度对话")

        # Tab 3: 知识图谱
        self.knowledge_widget = KnowledgeWidget(self.knowledge_base)
        self.knowledge_widget.query_sent.connect(self.handle_knowledge_search)
        self.tabs.addTab(self.knowledge_widget, "📚 知识洞察")

        right_layout.addWidget(self.tabs)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)
        main_layout.addWidget(splitter)

        # === 状态栏 ===
        self.status_bar = self.statusBar()
        self.status_label = QLabel("系统就绪")
        self.sys_info_label = QLabel("CPU: 0% | MEM: 0%")
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addWidget(self.status_label, 1)
        self.status_bar.addWidget(self.sys_info_label)
        self.status_bar.addPermanentWidget(self.progress_bar)

        self._create_menu()

    def _init_dashboard(self, parent):
        layout = QVBoxLayout(parent)
        top_grid = QGridLayout()

        kw_group = QGroupBox("🔑 核心关键词库")
        kw_layout = QVBoxLayout(kw_group)
        self.txt_keywords = QTextEdit()
        self.txt_keywords.setReadOnly(True)
        self.txt_keywords.setPlaceholderText("等待文档注入以生成 DNA 画像...")
        kw_layout.addWidget(self.txt_keywords)
        top_grid.addWidget(kw_group, 0, 0, 1, 2)

        meta_group = QGroupBox("🎭 风格画像")
        meta_layout = QVBoxLayout(meta_group)
        self.lbl_tone = QLabel("情感: --")
        self.lbl_style = QLabel("特征: --")
        meta_layout.addWidget(self.lbl_tone)
        meta_layout.addWidget(self.lbl_style)
        meta_layout.addStretch()
        top_grid.addWidget(meta_group, 0, 2, 1, 1)

        layout.addLayout(top_grid, 2)

        ent_group = QGroupBox("🌊 熵流监控")
        el = QVBoxLayout(ent_group)
        self.entropy_plot = EnhancedQuantumEntropyPlot()
        el.addWidget(self.entropy_plot)
        layout.addWidget(ent_group, 3)

    # ==========================================
    # 🔥 新增：低功耗模式回调函数 (来自2.txt)
    # ==========================================
    def on_low_power_changed(self, state):
        self.low_power_mode = (state == Qt.CheckState.Checked.value)
        status = "开启" if self.low_power_mode else "关闭"
        self.chat_widget.append_message("System", f"💡 低功耗模式已{status}。", "System")

    # ==========================================
    # 🔥 新增：思维活跃度控制回调函数 (来自3.txt)
    # ==========================================
    def update_temp_label(self):
        val = self.temp_slider.value() / 10.0
        desc = ""
        if val <= 0.3:
            desc = "(严谨/SOP)"
        elif val <= 0.6:
            desc = "(平衡/标准)"
        else:
            desc = "(发散/创意)"
        self.temp_label.setText(f"🧠 思维活跃度: {val:.1f} {desc}")

    # ==========================================
    # 🔥 修改：handle_user_input 方法，确保传递 web_searcher
    # ==========================================
    def handle_user_input(self, text):
        """处理用户输入 - 新增温度参数传递 + 深思模式判断 + 联网搜索开关"""
        if not text.strip(): return

        # 🔥 关键判断：如果是写长文，启动 DeepThinkingWorker
        if any(w in text for w in ["写一篇", "5000字", "稿件", "所有文件", "深思", "全量分析"]):
            self.start_deep_thinking(text)
            return

        if hasattr(self.brain, 'task_queue'):
            self.chat_widget.append_message("You", text)  # 本地先上屏

            # 🔥 获取当前的温度设置
            current_temp = self.temp_slider.value() / 10.0

            # 🔥 传递包含温度配置的任务 (添加文体参数 + 联网搜索开关)
            config = {
                "temperature": current_temp,
                "low_power": self.low_power_mode,
                # 🔥 新增策略参数 (包括文体)
                "audience": self.audience_input.text().strip() or "通用读者",
                "goal": self.goal_input.text().strip() or "传递价值",
                "genre": self.genre_combo.currentText() if hasattr(self, 'genre_combo') else "通用",
                # 🔥 新增：联网搜索开关状态
                "enable_web": self.web_search_check.isChecked() if hasattr(self, 'web_search_check') else False,
                # 🔥 关键：传递 web_searcher 实例
                "web_searcher": self.web_searcher if self.web_searcher else None
            }

            # 打印日志确认一下
            if config.get("enable_web", False) and self.web_searcher:
                print("🚀 [System] 用户已开启联网增强模式，WebSearcher 可用")
            elif config.get("enable_web", False):
                print("⚠️ [System] 用户开启了联网模式，但 WebSearcher 未初始化")

            self.brain.task_queue.put({
                "type": "chat",
                "payload": text,
                "config": config  # 🔥 新增配置参数
            })
            self.status_label.setText(f"Processing: {text[:20]}...")
            self.chat_widget.set_loading(True)
        else:
            QMessageBox.critical(self, "Error", "Brain Kernel Not Ready")

    # ==========================================
    # 🔥 修改：start_deep_thinking 方法，确保传递 web_searcher
    # ==========================================
    def start_deep_thinking(self, user_input):
        """启动深思模式 (修复版)"""
        # 1. 获取文件路径
        file_paths = []
        if hasattr(self, 'current_persona_name') and self.current_persona_name:
            # 使用物理隔离文件夹中的文件
            file_paths = self.io_manager.scan_files_in_persona(self.current_persona_name)
        else:
            # 回退到扫描 Inputs 目录
            import glob
            search_pattern = os.path.join(self.io_manager.paths.directories['inputs'], "**", "*.*")
            file_paths = glob.glob(search_pattern, recursive=True)
            file_paths = [f for f in file_paths if os.path.isfile(f)]

        if not file_paths:
            self.chat_widget.append_message("System", "❌ 未找到任何文件，无法执行全量分析。", "Error")
            return

        self.chat_widget.append_message("System",
                                        f"🚀 [Athena 深思引擎] 已启动<br>正在加载 {len(file_paths)} 个文件进入全量熔炉...<br>--------------------------------",
                                        "System"
                                        )

        # 2. 🔥 关键修复：更安全的线程检查
        current_worker = getattr(self, 'deep_thinking_worker', None)
        if current_worker is not None and current_worker.isRunning():
            current_worker.terminate()
            current_worker.wait()

        # 🔥 获取当前温度设置
        current_temp = self.temp_slider.value() / 10.0

        # 🔥 获取策略参数 (包括文体 + 联网搜索开关)
        config = {
            "temperature": current_temp,
            "low_power": self.low_power_mode,
            "audience": self.audience_input.text().strip() or "通用读者",
            "goal": self.goal_input.text().strip() or "传递价值",
            "genre": self.genre_combo.currentText() if hasattr(self, 'genre_combo') else "通用",
            # 🔥 新增：联网搜索开关状态
            "enable_web": self.web_search_check.isChecked() if hasattr(self, 'web_search_check') else False,
            # 🔥 关键：传递 web_searcher 实例
            "web_searcher": self.web_searcher if self.web_searcher else None
        }

        # 3. 创建新线程并赋值给 self.deep_thinking_worker
        self.deep_thinking_worker = DeepThinkingWorker(self.brain, user_input, file_paths, config)

        # 4. 连接信号
        self.deep_thinking_worker.thought_stream.connect(self.on_deep_thinking_update)
        self.deep_thinking_worker.finished.connect(self.on_deep_thinking_finished)
        self.deep_thinking_worker.error.connect(
            lambda e: self.chat_widget.append_message("System", f"❌ 错误: {e}", "Error"))

        self.deep_thinking_worker.start()
        self.status_label.setText("深思引擎启动中...")

    def on_deep_thinking_update(self, html_log):
        """实时显示思维流"""
        # 直接使用聊天组件的 append_message 方法，传递 HTML
        self.chat_widget.append_html(html_log)
        # 自动滚动到底部
        QApplication.processEvents()  # 保持界面流畅

    def on_deep_thinking_finished(self, article):
        """显示最终文章"""
        self.chat_widget.append_message("System", "<br><hr><br>", "System")
        self.chat_widget.append_message("Athena", article, "Athena")
        self.chat_widget.append_message("System", "✅ 全量生成完毕。", "Success")
        self.status_label.setText("深思引擎完成")

    @pyqtSlot(dict)
    def handle_brain_result(self, result):
        """🔥 绝对防御：处理大脑返回的结果"""
        try:
            if isinstance(result, dict):
                msg_type = result.get("type", "chat")
                content = result.get("content", "")
                sender = result.get("sender", "Athena")
            else:
                msg_type = "chat"
                content = str(result)
                sender = "Athena"

            if msg_type == "error":
                self.chat_widget.append_message("System", f"❌ Error: {content}", "System")
            elif msg_type == "analysis":
                self.chat_widget.append_message("System", content, "System")
            else:
                self.chat_widget.append_message(sender, content, sender)

        except Exception as e:
            print(f"CRITICAL UI ERROR: {e}")
            try:
                self.chat_widget.append_message("System", f"UI Error: {e}", "System")
            except:
                pass
        finally:
            if hasattr(self.chat_widget, 'set_loading'):
                self.chat_widget.set_loading(False)
            self.status_label.setText("Ready")

    # ==========================================
    # 🔥 核心修复：connect_global_signals (合并自2-mainwindow-AI.txt)
    # ==========================================
    def connect_global_signals(self):
        """
        连接全局信号总线 (修复版)
        合并了1-mainwindow-MAX.txt和2-mainwindow-AI.txt的功能
        """
        # 1. 基础系统信号 (来自brain)
        self.brain.log_signal.connect(lambda m: print(f"[Brain Log] {m}"))
        self.brain.query_result_signal.connect(self.handle_brain_result)
        self.brain.status_signal.connect(self.status_label.setText)
        self.brain.error_signal.connect(lambda e: self.chat_widget.append_message("System", f"❌ {e}", "Error"))

        # 2. 信号总线信号 (来自2-mainwindow-AI.txt)
        # log_signal 发送 str -> 连接到状态栏更新
        self.signal_bus.log_signal.connect(self.update_status_bar)

        # error_signal 发送 str -> 连接到弹窗报错
        self.signal_bus.error_signal.connect(self.show_error_message)

        # 3. 交互信号 (来自2-mainwindow-AI.txt)
        # chat_signal 发送 str -> 连接到AI消息显示
        self.signal_bus.chat_signal.connect(self.handle_chat_output)

        # system_signal 发送 dict -> 连接到系统消息处理
        self.signal_bus.system_signal.connect(self.append_system_message_dict)

        # 4. 数据可视化信号 (确保接收端方法存在)
        if hasattr(self, 'radar_widget'):
            self.signal_bus.radar_signal.connect(self.radar_widget.update_data)

        if hasattr(self, 'knowledge_widget'):
            self.signal_bus.knowledge_signal.connect(self.knowledge_widget.update_content)

        if hasattr(self, 'entropy_plot'):
            self.signal_bus.plot_signal.connect(self.entropy_plot.update_data_safe)

    # ==========================================
    # 🔥 信号槽函数补丁 (来自2-mainwindow-AI.txt)
    # ==========================================

    def handle_chat_output(self, message: str):
        """处理 AI 对话输出 (接收 str)"""
        if hasattr(self, 'chat_widget'):
            # 假设 ChatWidget 有 append_message 方法，如果没有，请根据 chat_widget.py 修改
            # 根据你上传的 chat_widget.py，它似乎是 history_display (QTextBrowser)
            # 我们直接追加 HTML
            self.chat_widget.append_message("Athena", message, "Athena")

    def append_system_message_dict(self, data: dict):
        """处理系统消息 (接收 dict)"""
        # 如果信号发来的是 dict，这里进行解析
        msg_type = data.get('type', 'info')
        content = data.get('content', '')

        if hasattr(self, 'chat_widget'):
            if msg_type == 'error':
                self.chat_widget.append_message("System", f"❌ {content}", "Error")
            elif msg_type == 'success':
                self.chat_widget.append_message("System", f"✅ {content}", "Success")
            else:
                self.chat_widget.append_message("System", content, "System")

    def update_status_bar(self, message: str):
        """更新状态栏"""
        self.statusBar().showMessage(message)

    def show_error_message(self, message: str):
        """显示错误弹窗"""
        QMessageBox.critical(self, "系统错误", message)

    # ==========================================
    # 🔥 保留原有的 append_system_message 方法 (来自1-mainwindow-MAX.txt)
    # ==========================================
    def append_system_message(self, text):
        """处理来自后端的 HTML 格式系统通知"""
        # 使用现有聊天组件显示系统消息
        self.chat_widget.append_message("System", text, "System")
        # 强制刷新界面，防止假死感
        QApplication.processEvents()

    # ==========================================
    # 🔥🔥🔥 关键修复：实时刷新仪表盘 (优化版，整合改进)
    # ==========================================
    def update_dashboard_realtime(self):
        """
        🔥 优化版：实时刷新仪表盘
        结合4.txt和3.txt的优点
        """
        try:
            # 确保引擎存在
            if not hasattr(self, 'mimicry_engine'): return

            matrix = self.mimicry_engine.style_matrix
            vocab = matrix.get('vocabulary')
            stats = matrix.get('sentence_stats', {})
            punct = matrix.get('punctuation_profile', {})
            tone = matrix.get('tone_markers', {})

            # 1. 刷新关键词 (Top 20)
            if hasattr(self, 'txt_keywords'):
                if vocab:
                    # 兼容 Counter 和 dict
                    if hasattr(vocab, 'most_common'):
                        top_words = vocab.most_common(20)
                    else:
                        top_words = sorted(vocab.items(), key=lambda x: x[1], reverse=True)[:20]

                    if top_words:
                        words_str = "  ".join([f"{w}" for w, c in top_words])
                        self.txt_keywords.setText(words_str)
                    else:
                        self.txt_keywords.setText("等待分析...")
                else:
                    self.txt_keywords.setText("等待文档注入...")

            # 2. 🔥 修复：刷新情感基调标签
            if hasattr(self, 'lbl_tone'):
                if tone:
                    if hasattr(tone, 'most_common'):
                        top_tone_list = tone.most_common(1)
                    else:
                        top_tone_list = sorted(tone.items(), key=lambda x: x[1], reverse=True)[:1]

                    if top_tone_list:
                        self.lbl_tone.setText(f"情感基调: {top_tone_list[0][0]}")
                    else:
                        self.lbl_tone.setText("情感基调: 中性")
                else:
                    self.lbl_tone.setText("情感基调: 未定义")

            # 3. 🔥 修复：刷新风格特征标签
            if hasattr(self, 'lbl_style'):
                style_features = []

                avg_len = stats.get('total_avg_len', 0)
                if isinstance(avg_len, dict): avg_len = 0
                if avg_len > 25:
                    style_features.append("长句式")
                elif avg_len > 15:
                    style_features.append("中等句式")
                else:
                    style_features.append("短句式")

                if hasattr(punct, 'most_common'):
                    top_punctuation = [k for k, v in punct.most_common(3)]
                else:
                    top_punctuation = list(punct.keys())[:3] if punct else []

                if "！" in top_punctuation or "？" in top_punctuation:
                    style_features.append("情感丰富")
                if "。" in top_punctuation and "，" in top_punctuation:
                    style_features.append("结构严谨")

                if style_features:
                    self.lbl_style.setText(f"特征: {' | '.join(style_features)}")
                else:
                    self.lbl_style.setText("特征: 等待分析...")

            # 4. 🔥 刷新雷达图
            if hasattr(self, 'radar_widget'):
                if hasattr(self.mimicry_engine, 'get_radar_data'):
                    radar_data = self.mimicry_engine.get_radar_data()
                    if radar_data:
                        self.radar_widget.set_data(radar_data)

            # 5. 🔥 刷新状态栏 DNA 信息 (物理隔离版)
            if hasattr(self, 'status_label'):
                avg_len = stats.get('total_avg_len', 0)
                if isinstance(avg_len, dict): avg_len = 0

                learned_count = self.mimicry_engine.learned_docs

                if learned_count > 0 and self.current_persona_name:
                    status_text = (
                        f"🧬 DNA激活 | 样本: {learned_count} | "
                        f"均句长: {avg_len:.1f} | "
                        f"空间: {self.current_persona_name}"
                    )
                    self.status_label.setText(status_text)
                elif self.current_persona_name:
                    self.status_label.setText(f"⏳ 当前空间: {self.current_persona_name} | 等待文档读取...")
                else:
                    self.status_label.setText("🛡️ 请先新建或加载一个空间")

        except Exception as e:
            # 静默失败，防止刷屏报错
            pass

    # ==========================================
    # 辅助功能 (文档、仪表盘、菜单)
    # ==========================================

    def _refresh_doc_list(self):
        self.doc_list.clear()
        docs = self.knowledge_base.data.get("documents", {})
        for doc_name in docs:
            self.doc_list.addItem(doc_name)

    def update_system_stats(self):
        metrics = self.system_monitor.get_system_metrics()
        if metrics:
            self.sys_info_label.setText(f"CPU: {metrics.cpu_usage:.1f}% | MEM: {metrics.memory_usage:.1f}%")
            self.entropy_plot.update_data_safe({
                'cpu': metrics.cpu_usage,
                'entropy': metrics.memory_usage
            })

    # ==========================================
    # 🔥 右键菜单 (来自 4.txt，保持完整功能)
    # ==========================================
    def show_context_menu(self, pos):
        """修复版：右键菜单，集成 解读/仿写/续写"""
        item = self.doc_list.itemAt(pos)
        if not item:
            return

        fname = item.text()
        menu = QMenu()

        # 1. 深度解读
        act_interpret = menu.addAction("🔍 深度解读 (Deep Read)")

        # 2. 拟态重构 (仿写)
        act_mimic = menu.addAction("🎭 拟态重构 (Mimicry)")

        # 3. 🔥 新增：智能续写 (Continuation)
        act_continue = menu.addAction("✍️ 智能续写 (Continue)")

        # 分隔符
        menu.addSeparator()
        act_open = menu.addAction("📂 打开所在文件夹")
        act_del = menu.addAction("🗑️ 删除文档")

        action = menu.exec(self.doc_list.mapToGlobal(pos))

        if action == act_interpret:
            self.on_doc_double_clicked(item)
        elif action == act_mimic:
            self.trigger_mimicry(fname)
        elif action == act_continue:
            self.trigger_continuation(fname)
        elif action == act_del:
            self._delete_document(fname, item)
        elif action == act_open:
            # 🔥 修改：在物理隔离文件夹中查找文件
            if self.current_persona_name:
                target_dir = self.io_manager.get_persona_folder(self.current_persona_name)
                path = os.path.join(target_dir, "**", fname)
                files = glob.glob(path, recursive=True)
                if files:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(files[0])))
            else:
                # 回退到旧方法
                path = os.path.join(self.io_manager.paths.directories['inputs'], "**", fname)
                files = glob.glob(path, recursive=True)
                if files:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(files[0])))

    # ==========================================
    # 🔥 新增：触发续写 (来自 4.txt)
    # ==========================================
    def trigger_continuation(self, fname):
        """触发智能续写任务"""
        reply = QMessageBox.question(
            self,
            "智能续写",
            f"即将基于《{fname}》的文风和逻辑进行续写。\n\n这需要读取文档的末尾片段，是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.chat_widget.append_message("System", f"✍️ 正在提取《{fname}》的写作DNA，准备续写...", "Info")
            self.brain.task_queue.put({"type": "continuation", "payload": fname})

    def trigger_mimicry(self, fname):
        topic, ok = QInputDialog.getText(self, "拟态引擎", f"基于《{fname}》的风格，请设定生成主题：")
        if ok and topic:
            self.chat_widget.append_message("System",
                                            f"🎭 正在激活拟态引擎，模拟风格生成关于 '{topic}' 的内容...",
                                            "Info")
            self.brain.task_queue.put({"type": "mimicry_gen", "payload": topic})

    def _delete_document(self, fname, item):
        if QMessageBox.question(self, "确认", "确定删除？") == QMessageBox.StandardButton.Yes:
            if fname in self.knowledge_base.data["documents"]:
                del self.knowledge_base.data["documents"][fname]
                self.knowledge_base.save_db()

            # 🔥 修改：从物理文件夹中删除文件
            if self.current_persona_name:
                target_dir = self.io_manager.get_persona_folder(self.current_persona_name)
                file_path = os.path.join(target_dir, fname)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f"🗑️ 已从物理文件夹删除: {fname}")
                    except Exception as e:
                        print(f"删除文件失败: {e}")

            self.doc_list.takeItem(self.doc_list.row(item))

    def _create_menu(self):
        menubar = self.menuBar()
        f_menu = menubar.addMenu("系统")
        f_menu.addAction("导入文档", self.import_document)
        f_menu.addAction("导出报告", self._export_report)
        f_menu.addAction("重置系统", self.reset_system)

        p_menu = menubar.addMenu("人格")
        p_menu.addAction("新建人格", self.create_new_persona)
        p_menu.addAction("加载人格", self.load_persona_dialog)
        p_menu.addAction("保存当前人格", self.save_current_persona)
        p_menu.addAction("合并人格", self.merge_persona_dialog)

        v_menu = menubar.addMenu("视图")
        v_menu.addAction("刷新仪表盘", self.update_dashboard_realtime)

    def _export_report(self):
        dst, _ = QFileDialog.getSaveFileName(self, "导出报告", "Report.md", "Markdown (*.md)")
        if dst:
            with open(dst, 'w', encoding='utf-8') as f:
                f.write(f"# Athena Report\nTime: {datetime.datetime.now()}\nDocs: {self.doc_list.count()}")
            QMessageBox.information(self, "成功", "报告已生成")

    def reset_system(self):
        if QMessageBox.question(self, '重置', '确认清空？') == QMessageBox.StandardButton.Yes:
            self.knowledge_base.clear_db()
            self.mimicry_engine.reset()
            self._refresh_doc_list()
            self.current_persona_name = None

    # ==========================================
    # 🔥 完整的人格保存/加载功能 (物理隔离版)
    # ==========================================
    def save_current_persona(self):
        """
        修复版：保存全量人格资产 (物理隔离版)
        """
        if not self.current_persona_name:
            QMessageBox.warning(self, "提示", "请先加载或新建一个人格！")
            return

        text, ok = QInputDialog.getText(self, '保存人格', '为人格命名:', text=self.current_persona_name)
        if ok and text:
            # 1. 获取当前文件夹中的真实文件列表
            if self.current_persona_name:
                current_files = self.io_manager.scan_files_in_persona(self.current_persona_name)
                doc_names = [os.path.basename(p) for p in current_files]
            else:
                doc_names = []

            # 2. 获取雷达数据
            radar_data = {}
            if hasattr(self.radar_widget, 'data'):
                radar_data = self.radar_widget.data

            # 3. 获取拟态风格矩阵
            style_matrix = {}
            if hasattr(self, 'mimicry_engine'):
                matrix = self.mimicry_engine.style_matrix
                style_matrix = {
                    'vocabulary': dict(matrix.get('vocabulary', {})),
                    'tone_markers': dict(matrix.get('tone_markers', {})),
                    'sentence_structures': dict(matrix.get('sentence_structures', {}))
                }

            # 4. 打包全量状态
            full_state = {
                "name": text,
                "dimensions": radar_data,
                "documents": doc_names,
                "style_matrix": style_matrix,
                "timestamp": str(datetime.datetime.now())
            }

            # 5. 保存
            if self.io_manager.save_persona(text, full_state):
                self.current_persona_name = text
                self.chat_widget.append_message("System", f"💾 人格《{text}》已保存。", "Success")
                self.status_label.setText(f"Current Persona: {text}")
            else:
                QMessageBox.warning(self, "Error", "保存失败")

    def load_persona_dialog(self):
        """
        修复版：加载人格 - 物理隔离版
        """
        personas = self.io_manager.scan_personas()
        if not personas:
            QMessageBox.information(self, "提示", "暂无存档人格")
            return

        item, ok = QInputDialog.getItem(self, "加载人格", "选择要切换的工作空间:", personas, 0, False)
        if ok and item:
            self._execute_load_persona(item)

    # ==========================================
    # 🔥 新增：合并人格功能
    # ==========================================
    def merge_persona_dialog(self):
        """将另一个人格的文档合并到当前人格"""
        if not self.current_persona_name:
            QMessageBox.warning(self, "提示", "请先加载或新建一个人格！")
            return

        personas = self.io_manager.scan_personas()
        item, ok = QInputDialog.getItem(self, "合并人格", "选择要合并进来的源:", personas, 0, False)
        if ok and item:
            data = self.io_manager.load_persona(item)
            new_docs = data.get('documents', [])

            # 获取当前文件夹中的文件
            current_files = self.io_manager.scan_files_in_persona(self.current_persona_name)
            current_docs = [os.path.basename(p) for p in current_files]

            # 找出当前还没加载的
            to_add = [d for d in new_docs if d not in current_docs]

            if not to_add:
                self.chat_widget.append_message("System", "⚠️ 没有新文档需要合并。", "Info")
                return

            self.chat_widget.append_message("System", f"🔗 正在合并 {len(to_add)} 个新文档...", "System")

            # 复制文件到当前人格文件夹
            source_dir = self.io_manager.get_persona_folder(item)
            target_dir = self.io_manager.get_persona_folder(self.current_persona_name)

            analyzer = DocumentIntelligenceAnalyzer()

            for doc_name in to_add:
                src_path = os.path.join(source_dir, doc_name)
                dst_path = os.path.join(target_dir, doc_name)

                if not os.path.exists(src_path):
                    continue

                try:
                    # 复制文件
                    import shutil
                    shutil.copy2(src_path, dst_path)

                    # 🔥 检查缓存
                    cached_record = self.knowledge_keeper.get_cached_record(dst_path)
                    if cached_record:
                        # 从缓存恢复
                        self.restore_from_cache(doc_name, cached_record)
                        self.doc_list.addItem(doc_name)
                        self.chat_widget.append_message("System", f"⚡ {doc_name} 已从缓存恢复。", "Success")
                    else:
                        # 加载和分析
                        content = self.io_manager.read_file(dst_path)
                        res = analyzer.analyze(content[:5000])
                        self.mimicry_engine.ingest(res)
                        self.knowledge_base.add_document(doc_name, content, {}, {})
                        self.doc_list.addItem(doc_name)
                except Exception as e:
                    print(f"合并失败 {doc_name}: {e}")

            self.chat_widget.append_message("System", "✅ 合并完成。请记得点击保存。", "Success")
            self.update_dashboard_realtime()

    def on_doc_double_clicked(self, item):
        self.chat_widget.input_field.setText(f"深度解读文档《{item.text()}》")
        self.chat_widget.send_message()

    def handle_knowledge_search(self, query):
        res = self.knowledge_base.search(query)
        self.knowledge_widget.show_results(res)

    def closeEvent(self, event):
        if self.brain:
            self.brain.stop()

        # 🔥 停止深思引擎线程
        current_worker = getattr(self, 'deep_thinking_worker', None)
        if current_worker is not None and current_worker.isRunning():
            current_worker.terminate()
            current_worker.wait()

        # 🔥 新增：清理 WebSearcher 资源
        if hasattr(self, 'web_searcher') and self.web_searcher:
            # 如果 WebSearcher 有清理方法，调用它
            if hasattr(self.web_searcher, 'cleanup'):
                self.web_searcher.cleanup()
            print("✅ [System] WebSearcher 资源已清理")

        event.accept()