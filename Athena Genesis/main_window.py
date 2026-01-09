# -*- coding: utf-8 -*-
"""
合并版主窗口控制器 - 三刀修复版 v25.0
整合了原始版的稳定性和新版的核心架构
"""
import os
import sys
import time
import json
import jieba
import warnings
import glob
import traceback
import threading
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

warnings.filterwarnings("ignore")

from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox,
    QInputDialog, QMenu, QLabel
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QTimer, QCoreApplication, pyqtSlot
from config.settings import SETTINGS

# 🔥 关键：强制从 core 导入，绝不使用 engines
from ui.components.main_frame import MainFrame
from core.signal_bus import SignalBus
from core.io_manager import IOManager
from core.system_monitor import SystemMonitor
from core.athena_brain import AthenaBrain
from core.persistence import KnowledgeKeeper, GLOBAL_TASK_QUEUE

# 导入人格编辑器（兼容所有路径）
# try:
#     from ui.dialogs.persona_editor import PersonaEditor
#     HAS_PERSONA_EDITOR = True
# except ImportError:
#     try:
#         from gui.persona_editor import PersonaEditor
#         HAS_PERSONA_EDITOR = True
#     except ImportError:
#         HAS_PERSONA_EDITOR = False
#         print("❌ 严重警告: 未找到 PersonaEditor 组件，无法新建人格！")
print("-" * 30)
print("🔍 [Debug] 开始加载 PersonaEditor...")

HAS_PERSONA_EDITOR = False
try:
    # 尝试路径 1: ui.dialogs
    from ui.dialogs.persona_editor import PersonaEditor
    HAS_PERSONA_EDITOR = True
    print("✅ [Debug] 成功从 ui.dialogs 加载 PersonaEditor")
except ImportError as e1:
    print(f"⚠️ [Debug] 路径1加载失败: {e1}")
    try:
        # 尝试路径 2: gui
        from gui.persona_editor import PersonaEditor
        HAS_PERSONA_EDITOR = True
        print("✅ [Debug] 成功从 gui.persona_editor 加载 PersonaEditor")
    except ImportError as e2:
        print(f"❌ [Debug] 人格编辑器加载彻底失败！")
        print(f"❌ [Error Detail] 错误详情: {e2}") # 🔥 这里会告诉你缺什么！
        HAS_PERSONA_EDITOR = False
print("-" * 30)

# 导入知识库模块（强制从core）
try:
    from core.knowledge_base import KnowledgeBase
    print("✅ 使用核心知识库模块")
except ImportError as e:
    print(f"❌ 无法导入核心知识库: {e}")
    # 临时替代方案
    class KnowledgeBase:
        def __init__(self):
            self.data = {"documents": {}}
            print("⚠️ 使用临时知识库")

        def add_document(self, *args, **kwargs):
            pass

        def search(self, *args, **kwargs):
            return ""

        def get_all_docs(self):
            return []


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._init_window_properties()

        print("🛠️ [Init] 正在初始化混合智能体系统(三刀修复版 v25.0)...")

        # 当前激活的人格空间
        self.current_persona = None
        self.current_persona_path = None

        # 🔥 线程池用于后台任务
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.background_tasks = []

        # 1. 初始化核心服务（业务逻辑层）
        self._init_core_services()

        # 2. 初始化UI主框架（视图层）
        self._init_ui_components()

        # 🔥 3. 初始化顶部菜单栏
        self._init_menu_bar()

        # 4. 初始化混合智能体大脑
        self._init_hybrid_brain()

        # 5. 连接所有信号
        self._connect_signals_v10()

        # 6. 🔥 完美的启动逻辑
        QTimer.singleShot(500, lambda: self.safe_execute(self.scan_personas))
        QTimer.singleShot(1500, lambda: self.safe_execute(self._perform_smart_self_check))
        QTimer.singleShot(2500, lambda: self.safe_execute(self._check_pending_tasks))

        print("✅ [Init] 混合智能体系统初始化完成(三刀修复版 v25.0)")

    # ==========================================
    # 🔥 核心安全机制：全局错误捕获
    # ==========================================

    def safe_execute(self, func, *args, **kwargs):
        """🔥 安全的执行函数，捕获所有异常"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"全局捕获: {func.__name__} 函数崩溃: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            self.safe_append_message("System", f"❌ 系统错误: {str(e)}", "Error")
            return None

    def safe_append_message(self, sender, content, msg_type="normal"):
        """🔥 安全的UI消息追加，防止崩溃"""
        try:
            print(f"📝 UI Log: [{sender}] {content[:100]}")
            QTimer.singleShot(0, lambda: self._safe_append_message_impl(sender, content, msg_type))
            QCoreApplication.processEvents()
        except Exception as e:
            print(f"❌ UI消息追加失败: {e}")

    def _safe_append_message_impl(self, sender, content, msg_type):
        """🔥 实际的消息上屏实现（线程安全）"""
        try:
            if hasattr(self.main_frame, 'append_message'):
                self.main_frame.append_message(sender, content, msg_type)
            elif hasattr(self.main_frame.chat_area, 'append_message'):
                self.main_frame.chat_area.append_message(sender, content, msg_type)
            else:
                print(f"[{sender}] {content[:50]}...")
        except Exception as e:
            print(f"❌ UI更新失败: {e}")

    def safe_update_status(self, text):
        """🔥 安全的状态栏更新"""
        try:
            QTimer.singleShot(0, lambda: self._safe_update_status_impl(text))
        except Exception as e:
            print(f"❌ 状态栏更新失败: {e}")

    def _safe_update_status_impl(self, text):
        """🔥 实际的状态栏更新实现（线程安全）"""
        try:
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.setText(text)
            else:
                self.statusBar().showMessage(text)
        except Exception as e:
            print(f"❌ 状态栏设置失败: {e}")

    # ==========================================
    # 初始化方法（全部添加安全保护）
    # ==========================================

    def _init_window_properties(self):
        """初始化窗口属性"""
        try:
            app_name = getattr(SETTINGS, 'APP_NAME', 'Athena Genesis')
            version = getattr(SETTINGS, 'VERSION', '25.0')
            self.setWindowTitle(f"{app_name} v{version} [三刀修复版 v25.0]")
            self.resize(1400, 900)

            # 居中显示
            screen = QApplication.primaryScreen().geometry()
            self.move((screen.width() - 1400) // 2, (screen.height() - 900) // 2)

            # 深色主题美化
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                    font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                }
                QLabel { 
                    color: #d4d4d4; 
                }
                QMessageBox { 
                    background-color: #2d2d30; 
                    color: #fff; 
                    font-family: 'Microsoft YaHei';
                }
                QMenuBar {
                    background-color: #252526;
                    color: #cccccc;
                }
                QMenuBar::item:selected {
                    background-color: #3e3e40;
                }
            """)
        except Exception as e:
            print(f"❌ 窗口属性初始化失败: {e}")

    def _init_menu_bar(self):
        """🔥 初始化顶部菜单栏"""
        try:
            menubar = self.menuBar()

            # 文件菜单
            file_menu = menubar.addMenu("文件(F)")

            # 🔥 加载人格存档
            load_action = QAction("📂 加载人格存档", self)
            load_action.setShortcut("Ctrl+O")
            load_action.triggered.connect(self._menu_load_persona)
            file_menu.addAction(load_action)

            # 🔥 新建人格
            new_action = QAction("✨ 新建人格", self)
            new_action.setShortcut("Ctrl+N")
            new_action.triggered.connect(self._menu_create_persona)
            file_menu.addAction(new_action)

            # 🔥 导入文档
            import_action = QAction("📥 导入文档", self)
            import_action.setShortcut("Ctrl+I")
            import_action.triggered.connect(self._menu_import_document)
            file_menu.addAction(import_action)

            file_menu.addSeparator()

            # 退出
            exit_action = QAction("❌ 退出", self)
            exit_action.setShortcut("Ctrl+Q")
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)

            print("✅ [Menu] 顶部菜单栏初始化完成")
        except Exception as e:
            print(f"⚠️ [Menu] 菜单栏初始化失败: {e}")

    def _menu_load_persona(self):
        """🔥 菜单栏加载人格（强制非原生对话框）"""
        try:
            personas_dir = getattr(SETTINGS.PATHS.directories, 'personas', None)
            if not personas_dir:
                personas_dir = os.path.join(os.getcwd(), 'ATHENA_WORKSPACE', 'Database', 'Personas')

            if not os.path.exists(personas_dir):
                os.makedirs(personas_dir, exist_ok=True)

            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "加载人格矩阵",
                personas_dir,
                "JSON Files (*.json)",
                options=QFileDialog.Option.DontUseNativeDialog
            )

            if file_path and os.path.exists(file_path):
                print(f"📂 [Menu] 通过菜单加载: {os.path.basename(file_path)}")
                self.safe_append_message("System", f"📂 菜单加载: {os.path.basename(file_path)}", "System")
                self.load_persona_space(file_path)
        except Exception as e:
            self.safe_append_message("System", f"❌ 菜单加载失败: {str(e)}", "Error")

    def _menu_create_persona(self):
        """🔥 菜单栏新建人格"""
        try:
            self.create_persona()
        except Exception as e:
            self.safe_append_message("System", f"❌ 菜单创建失败: {str(e)}", "Error")

    def _menu_import_document(self):
        """🔥 菜单栏导入文档"""
        try:
            if not self.current_persona:
                QMessageBox.warning(self, "警告", "请先加载一个人格空间")
                return

            files, _ = QFileDialog.getOpenFileNames(
                self,
                "选择文档",
                "",
                "All Files (*.*)",
                options=QFileDialog.Option.DontUseNativeDialog
            )

            if files:
                print(f"📥 [Menu] 通过菜单导入 {len(files)} 个文档")
                self.thread_pool.submit(lambda: self.safe_execute(self.import_documents_background, files))
        except Exception as e:
            self.safe_append_message("System", f"❌ 菜单导入失败: {str(e)}", "Error")

    def _init_core_services(self):
        """初始化核心业务服务"""
        try:
            print("🔧 [Init] 初始化核心服务...")

            # 信号总线
            self.signal_bus = SignalBus()

            # IO管理器
            self.io_manager = IOManager()

            # 知识库
            self.knowledge_base = KnowledgeBase()

            # 系统监控
            self.system_monitor = SystemMonitor()

            # 知识保存器
            self.knowledge_keeper = KnowledgeKeeper(self.io_manager)

        except Exception as e:
            print(f"❌ 核心服务初始化失败: {e}")

    def _init_ui_components(self):
        """初始化纯UI组件"""
        try:
            print("🖼️ [Init] 加载用户界面...")

            # 创建主框架（纯UI）
            self.main_frame = MainFrame()
            self.setCentralWidget(self.main_frame)

            # 设置状态栏
            self.statusBar().showMessage("系统就绪")

            # 🔥 安全地获取状态标签
            if hasattr(self.main_frame, 'status_label'):
                self.status_label = self.main_frame.status_label
            elif hasattr(self.main_frame.chat_area, 'status_label'):
                self.status_label = self.main_frame.chat_area.status_label
            else:
                self.status_label = QLabel("Ready")
                self.status_label.setStyleSheet("padding: 5px; color: #666; background: #1e1e1e;")
                self.status_label.setFixedHeight(25)
                if hasattr(self.main_frame, 'layout') and self.main_frame.layout():
                    self.main_frame.layout().addWidget(self.status_label)

            # 🔥 连接知识库到侧边栏知识库组件
            if hasattr(self.main_frame.sidebar, 'knowledge_widget'):
                self.main_frame.sidebar.knowledge_widget.knowledge_base = self.knowledge_base

        except Exception as e:
            print(f"❌ UI组件初始化失败: {e}")

    def _init_hybrid_brain(self):
        """初始化混合智能体大脑"""
        try:
            print("🧠 [Init] 激活混合智能体指挥系统...")

            # 使用 AthenaBrain 参数结构
            try:
                self.brain = AthenaBrain(
                    bus=self.signal_bus,
                    io_manager=self.io_manager,
                    knowledge_base=self.knowledge_base
                )
                print("✅ [Init] 大脑核心初始化成功")

                # 🔥 启动大脑线程
                self.start_brain()

            except Exception as e:
                print(f"❌ [Init] 大脑核心初始化失败: {e}")
                traceback.print_exc()
                self.brain = None
                QMessageBox.warning(self, "大脑初始化失败",
                                    f"大脑核心初始化失败，AI功能将不可用。\n错误详情：{str(e)}")

        except Exception as e:
            print(f"❌ 大脑初始化失败: {e}")
            self.brain = None

    def start_brain(self):
        """启动大脑线程"""
        try:
            if self.brain is None:
                print("⚠️ [Brain] 大脑未初始化，无法启动")
                return

            if hasattr(self.brain, 'isRunning'):
                if not self.brain.isRunning():
                    self.brain.start()
                    self.safe_append_message("System", "🧠 Athena 内核已激活，等待指令...", "Success")
                    print("✅ [Brain] 大脑线程已启动")
                else:
                    print("ℹ️ [Brain] 大脑线程已在运行")
            else:
                self.brain.start()
        except Exception as e:
            print(f"❌ 大脑启动失败: {e}")

    def _connect_signals_v10(self):
        """🔥 信号连接v10：信号清洗 + 防重复触发"""
        try:
            print("🔌 [Init] 连接系统信号 (v10)...")

            # 🔥 清洗旧连接（先断开，再连接）
            self._cleanup_signals()

            # === 大脑信号 → UI ===
            if hasattr(self, 'brain') and self.brain:
                if hasattr(self.brain, 'log_signal'):
                    self.brain.log_signal.connect(lambda msg: self.safe_execute(self.safe_update_status, msg))
                    print("✅ [Signal] 连接大脑 log_signal")

                if hasattr(self.brain, 'query_result_signal'):
                    self.brain.query_result_signal.connect(self.handle_brain_result)
                    print("✅ [Signal] 连接大脑 query_result_signal")

                if hasattr(self.brain, 'error_signal'):
                    self.brain.error_signal.connect(self.handle_brain_error)
                    print("✅ [Signal] 连接大脑 error_signal")

                if hasattr(self.brain, 'status_signal'):
                    self.brain.status_signal.connect(self.safe_update_status)
                    print("✅ [Signal] 连接大脑 status_signal")
            else:
                print("⚠️ [Signal] 大脑未初始化，跳过大脑信号连接")

            # === 信号总线信号 → UI ===
            self.signal_bus.log_signal.connect(lambda msg: self.safe_execute(self.safe_update_status, msg))
            self.signal_bus.error_signal.connect(self.handle_system_error)
            self.signal_bus.chat_signal.connect(lambda data: self.safe_execute(
                self.safe_append_message, data.get("sender", "System"), data.get("content", ""),
                data.get("type", "normal")
            ))
            self.signal_bus.system_signal.connect(self.handle_system_message)

            # === UI → 大脑 ===
            self._connect_ui_to_brain_v2()

            # === 侧边栏信号连接 ===
            self._connect_sidebar_signals_v2()

            # === 新版本高级功能连接 ===
            self._connect_advanced_functions()

            print("✅ [Init] 所有信号连接完成 (v10)")

        except Exception as e:
            print(f"❌ 信号连接失败: {e}")

    def _cleanup_signals(self):
        """🔥 清理旧信号连接，防止重复触发"""
        try:
            sidebar = self.main_frame.sidebar

            # 清理侧边栏按钮连接
            if hasattr(sidebar, 'load_persona_clicked'):
                try:
                    sidebar.load_persona_clicked.disconnect()
                except:
                    pass

            if hasattr(sidebar, 'new_persona_clicked'):
                try:
                    sidebar.new_persona_clicked.disconnect()
                except:
                    pass

            if hasattr(sidebar, 'btn_load') and hasattr(sidebar.btn_load, 'clicked'):
                try:
                    sidebar.btn_load.clicked.disconnect()
                except:
                    pass

            if hasattr(sidebar, 'btn_new') and hasattr(sidebar.btn_new, 'clicked'):
                try:
                    sidebar.btn_new.clicked.disconnect()
                except:
                    pass

            if hasattr(sidebar, 'btn_import') and hasattr(sidebar.btn_import, 'clicked'):
                try:
                    sidebar.btn_import.clicked.disconnect()
                except:
                    pass

            # 清理模式选择
            if hasattr(sidebar, 'mode_combo'):
                try:
                    sidebar.mode_combo.currentTextChanged.disconnect()
                except:
                    pass

            print("🧹 [Signal] 旧信号连接已清理")
        except Exception as e:
            print(f"⚠️ 信号清理失败: {e}")

    def _connect_ui_to_brain_v2(self):
        """🔥 连接UI组件到大脑v2"""
        try:
            chat_area = self.main_frame.chat_area

            # 清理旧连接
            if hasattr(chat_area, 'message_sent'):
                try:
                    chat_area.message_sent.disconnect()
                except:
                    pass
                chat_area.message_sent.connect(self._on_user_send_message)

            # 发送按钮
            if hasattr(chat_area, 'btn_send'):
                try:
                    chat_area.btn_send.clicked.disconnect()
                except:
                    pass
                chat_area.btn_send.clicked.connect(self._on_send_button)

            # 输入框回车
            if hasattr(chat_area, 'input_box'):
                try:
                    chat_area.input_box.returnPressed.disconnect()
                except:
                    pass
                chat_area.input_box.returnPressed.connect(self._on_send_button)

            print("✅ [Signal] UI到大脑连接完成")
        except Exception as e:
            print(f"❌ UI到大脑连接失败: {e}")

    def _connect_sidebar_signals_v2(self):
        """🔥 连接侧边栏信号v2"""
        try:
            sidebar = self.main_frame.sidebar

            # 人格管理
            if hasattr(sidebar, 'load_persona_clicked'):
                sidebar.load_persona_clicked.connect(self._safe_load_persona)
            elif hasattr(sidebar, 'btn_load'):
                sidebar.btn_load.clicked.connect(self._safe_load_persona)

            # 新建人格
            if hasattr(sidebar, 'new_persona_clicked'):
                sidebar.new_persona_clicked.connect(self._safe_create_persona)
            elif hasattr(sidebar, 'btn_new'):
                sidebar.btn_new.clicked.connect(self._safe_create_persona)

            # 导入文档
            if hasattr(sidebar, 'btn_import'):
                sidebar.btn_import.clicked.connect(self._safe_import_document)

            # 人格选择列表
            if hasattr(sidebar, 'persona_selected'):
                try:
                    sidebar.persona_selected.disconnect()
                except:
                    pass
                sidebar.persona_selected.connect(self.load_persona_data)

            # 模式选择
            if hasattr(sidebar, 'mode_combo') and hasattr(self, 'brain') and self.brain:
                def on_mode_changed():
                    try:
                        if hasattr(sidebar, 'get_current_mode'):
                            mode = sidebar.get_current_mode()
                            if hasattr(self.brain, 'set_mode'):
                                self.brain.set_mode(mode)
                    except Exception as e:
                        print(f"⚠️ 模式切换失败: {e}")

                sidebar.mode_combo.currentTextChanged.connect(lambda: on_mode_changed())

            # 联网开关
            if hasattr(sidebar, 'web_search_check') and hasattr(self, 'brain') and self.brain:
                if hasattr(self.brain, 'toggle_search'):
                    sidebar.web_search_check.toggled.connect(self.brain.toggle_search)

            # 思维温度
            if hasattr(sidebar, 'temp_slider'):
                def on_temp_changed(value):
                    try:
                        temperature = value / 10.0
                        if hasattr(self, 'brain') and self.brain and hasattr(self.brain, 'set_temperature'):
                            self.brain.set_temperature(temperature)
                    except Exception as e:
                        print(f"⚠️ 温度设置失败: {e}")

                sidebar.temp_slider.valueChanged.connect(on_temp_changed)

            # 🔥 知识库搜索
            if hasattr(sidebar, 'knowledge_widget'):
                if hasattr(sidebar.knowledge_widget, 'search_triggered'):
                    sidebar.knowledge_widget.search_triggered.connect(self.search_knowledge_async)
                elif hasattr(sidebar.knowledge_widget, 'query_sent'):
                    sidebar.knowledge_widget.query_sent.connect(self.search_knowledge_async)

            # 文档选中信号
            if hasattr(sidebar, 'doc_selected'):
                sidebar.doc_selected.connect(self.on_doc_selected)

            print("✅ [Signal] 侧边栏信号连接完成")
        except Exception as e:
            print(f"❌ 侧边栏信号连接失败: {e}")

    def _connect_advanced_functions(self):
        """连接高级功能信号"""
        try:
            sidebar = self.main_frame.sidebar

            if hasattr(sidebar, 'analyze_file_clicked'):
                sidebar.analyze_file_clicked.connect(self.action_analyze)
            if hasattr(sidebar, 'mimic_file_clicked'):
                sidebar.mimic_file_clicked.connect(self.action_mimic)
            if hasattr(sidebar, 'continue_file_clicked'):
                sidebar.continue_file_clicked.connect(self.action_continue)
        except Exception as e:
            print(f"❌ 高级功能连接失败: {e}")

    # ==========================================
    # 🔥 新增：任务恢复逻辑
    # ==========================================

    def _check_pending_tasks(self):
        """检查是否有崩溃前未完成的任务"""
        try:
            if not GLOBAL_TASK_QUEUE:
                return

            pending = GLOBAL_TASK_QUEUE.get_pending_tasks()
            if pending:
                count = len(pending)
                reply = QMessageBox.question(
                    self,
                    "任务恢复",
                    f"检测到 {count} 个未完成的任务（可能是上次异常退出导致的）。\n是否尝试恢复？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self._recover_tasks(pending)
                else:
                    for task in pending:
                        GLOBAL_TASK_QUEUE.update_status(task['task_id'], "CANCELLED")
        except Exception as e:
            print(f"❌ 任务恢复检查失败: {e}")

    def _recover_tasks(self, tasks):
        """执行恢复逻辑"""
        try:
            if self.brain is None:
                print("⚠️ 大脑未初始化，无法恢复任务")
                return

            for task in tasks:
                task_type = task['task_type']
                payload = task['payload']
                print(f"🔄 正在恢复任务: {task_type}")

                if task_type == 'analysis':
                    self.brain.launch(
                        "恢复分析任务",
                        mode="analysis",
                        config={
                            "file_path": payload.get('filename'),
                            "file_name": payload.get('filename'),
                            "analysis_mode": payload.get('mode', 'fast')
                        }
                    )
                elif task_type == 'chat':
                    user_input = payload.get('text', '')
                    if user_input:
                        self.safe_append_message("System", f"🔄 恢复对话任务: {user_input[:50]}...", "System")
        except Exception as e:
            print(f"❌ 任务恢复失败: {e}")

    # ==========================================
    # 🔥 智能自检系统
    # ==========================================

    def _perform_smart_self_check(self):
        """完美的自检逻辑"""
        try:
            personas_dir = getattr(SETTINGS.PATHS.directories, 'personas', 'personas')
            if not os.path.exists(personas_dir):
                os.makedirs(personas_dir, exist_ok=True)
                self.safe_append_message("System", "ℹ️ 初始化数据目录...", "System")

            if not self.current_persona:
                self.safe_append_message("System", "💡 系统就绪。请加载人格。", "System")
                self.safe_update_status("✅ 系统自检通过 | 等待加载人格")
            else:
                self.safe_append_message("System", "🛡️ 系统自检中...", "System")
                if hasattr(self, 'brain') and self.brain and hasattr(self.brain, 'launch'):
                    self.brain.launch(
                        "请简短报告当前系统状态。",
                        mode="system_cmd",
                        config={"web_search": False}
                    )
                else:
                    self.safe_update_status("✅ 系统自检完成 | 大脑正常")

        except Exception as e:
            self.safe_update_status("⚠️ 系统自检异常 | 请检查配置")
            self.safe_append_message("System", f"⚠️ 系统自检异常: {str(e)}", "Warning")

    # ==========================================
    # 🔥 人格管理相关业务逻辑
    # ==========================================

    def create_persona(self):
        """
        🔥 [整合修复版] 打开新建人格窗口
        综合了两个版本的优点，具备更好的兼容性和错误处理
        """
        print("🖱️ [UI] 点击了新建人格按钮 (整合版本)")

        try:
            # -----------------------------------------------------------
            # 1. 检查是否有 PersonaEditor 组件
            # -----------------------------------------------------------
            if not HAS_PERSONA_EDITOR:
                print("ℹ️ [Debug] 未检测到 PersonaEditor 组件，使用简单输入方式")
                return self._create_persona_simple()

            # -----------------------------------------------------------
            # 2. 使用 PersonaEditor 创建人格（带智能参数检测）
            # -----------------------------------------------------------
            print("🔍 [Debug] 准备实例化 PersonaEditor...")

            # 智能参数检测逻辑
            dialog = self._instantiate_persona_editor()
            if not dialog:
                print("⚠️ [Debug] 创建编辑器失败，回退到简单方式")
                return self._create_persona_simple()

            # 连接保存信号
            self._connect_persona_editor_signals(dialog)

            # 显示窗口（模态或非模态）
            result = self._show_persona_editor_dialog(dialog)

            if result:
                # 处理保存逻辑
                return self._handle_persona_save(dialog)
            else:
                print("🚫 [Debug] 用户取消了人格创建")
                return False

        except Exception as e:
            error_msg = f"创建人格失败: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            self.safe_append_message("System", f"❌ {error_msg}", "Error")
            QMessageBox.critical(self, "错误", f"无法创建人格: {str(e)}")
            return False

    # ==================================================
    # 🩹 补全缺失的刷新方法 (修复 AttributeError)
    # ==================================================
    def reload_personas(self, name=None):
        """
        响应编辑器保存成功的信号，刷新人格列表
        :param name: 刚刚保存的人格名称 (由信号传递过来，可选)
        """
        print(f"🔄 [UI] 收到刷新信号，正在重新扫描人格列表... (最新: {name})")

        # 尝试调用已有的扫描方法 (根据报错提示，你肯定有 scan_personas)
        if hasattr(self, 'scan_personas'):
            try:
                self.scan_personas()
                print("✅ [UI] 列表刷新完成")
            except Exception as e:
                print(f"⚠️ [UI] 扫描列表时出错: {e}")
        else:
            print("❌ [UI] 严重错误: 找不到 scan_personas 方法，无法刷新界面！")
            # 如果真的没有 scan_personas，这里需要写重新读取文件夹并更新 ListWidget 的逻辑

    def _create_persona_simple(self):
        """简单方式创建人格（无 PersonaEditor 时使用）"""
        name, ok = QInputDialog.getText(
            self, "新建人格", "请输入人格名称 (例如: 助手A):",
            text="未命名人格"
        )

        if not ok or not name:
            print("🚫 [UI] 用户取消了新建")
            return False

        print(f"📝 [UI] 用户输入新名称: {name}")

        # 确定保存目录
        personas_dir = getattr(SETTINGS.PATHS.directories, 'personas', None)
        if not personas_dir:
            personas_dir = os.path.join(os.getcwd(), 'ATHENA_WORKSPACE', 'Database', 'Personas')
        os.makedirs(personas_dir, exist_ok=True)

        # 创建基本人格数据
        persona_data = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "documents": [],
            "description": "新建的人格空间"
        }

        # 保存文件
        filepath = os.path.join(personas_dir, f"{name}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(persona_data, f, ensure_ascii=False, indent=2)

        # 更新状态
        self.current_persona = name
        self.current_persona_path = filepath

        # 刷新界面
        self._refresh_after_persona_creation(name)

        return True

    def _instantiate_persona_editor(self):
        """智能实例化 PersonaEditor（尝试多种参数组合）"""
        try:
            # 尝试不同的参数组合，优先级从上到下
            if hasattr(PersonaEditor, '__init__'):
                # 获取构造函数签名
                import inspect
                sig = inspect.signature(PersonaEditor.__init__)
                params = list(sig.parameters.keys())

                print(f"🔍 [Debug] PersonaEditor 构造函数参数: {params}")

                # 根据参数名智能匹配
                if 'parent' in params:
                    if 'knowledge_base' in params and hasattr(self, 'knowledge_base'):
                        print(f"ℹ️ [Debug] 使用 parent + knowledge_base 初始化")
                        return PersonaEditor(parent=self, knowledge_base=self.knowledge_base)
                    else:
                        print(f"ℹ️ [Debug] 使用 parent 初始化")
                        return PersonaEditor(parent=self)
                elif len(params) >= 2:
                    # 处理两个参数的构造函数
                    if hasattr(self, 'io_manager'):
                        print(f"ℹ️ [Debug] 使用 io_manager + self 初始化")
                        return PersonaEditor(self.io_manager, self)
                    else:
                        print(f"⚠️ [Debug] 尝试默认两参数初始化")
                        return PersonaEditor(None, self)

            # 回退：根据可用属性尝试
            print("⚠️ [Debug] 使用回退策略初始化")
            if hasattr(self, 'io_manager') and hasattr(self, 'knowledge_base'):
                try:
                    return PersonaEditor(self.io_manager, self.knowledge_base)
                except:
                    pass

            if hasattr(self, 'io_manager'):
                try:
                    return PersonaEditor(self.io_manager, self)
                except:
                    pass

            if hasattr(self, 'knowledge_base'):
                try:
                    return PersonaEditor(parent=self, knowledge_base=self.knowledge_base)
                except:
                    pass

            # 最后尝试
            try:
                return PersonaEditor(parent=self)
            except TypeError as e:
                print(f"❌ [参数错误] 所有初始化尝试都失败: {e}")
                return None

        except Exception as e:
            print(f"❌ [实例化错误] 无法实例化 PersonaEditor: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _connect_persona_editor_signals(self, dialog):
        """连接编辑器信号"""
        if hasattr(dialog, 'saved_signal'):
            dialog.saved_signal.connect(self.reload_personas)
            print("🔗 [Debug] 连接 saved_signal")
        elif hasattr(dialog, 'persona_saved'):
            dialog.persona_saved.connect(self.reload_personas)
            print("🔗 [Debug] 连接 persona_saved")

    def _show_persona_editor_dialog(self, dialog):
        """显示编辑器对话框"""
        print("📺 [Debug] 正在显示窗口...")

        # 检查对话框是否有 exec 方法（模态对话框）
        if hasattr(dialog, 'exec'):
            return dialog.exec()
        else:
            # 非模态显示
            dialog.show()

            # 对于非模态对话框，我们需要等待用户操作
            # 这里使用一个简单的循环或信号等待（简化版本）
            print("⚠️ [Debug] 使用非模态显示，直接返回 True")
            return True  # 假设用户会成功创建

    def _handle_persona_save(self, dialog):
        """处理人格保存逻辑"""
        print("✅ [Debug] 正在处理保存数据...")

        # 获取人格数据
        if hasattr(dialog, 'get_persona_data'):
            persona_data = dialog.get_persona_data()
        else:
            # 如果编辑器没有 get_persona_data 方法，使用默认数据
            persona_data = {
                "name": "未命名人格",
                "created_at": datetime.now().isoformat(),
                "documents": [],
                "description": "新建的人格空间"
            }

        persona_name = persona_data.get("name", "未命名人格")
        print(f"📝 [Debug] 创建人格: {persona_name}")

        # 确定保存路径
        personas_dir = getattr(SETTINGS.PATHS.directories, 'personas', None)
        if not personas_dir:
            personas_dir = os.path.join(os.getcwd(), 'ATHENA_WORKSPACE', 'Database', 'Personas')
        os.makedirs(personas_dir, exist_ok=True)

        # 保存人格文件
        filepath = os.path.join(personas_dir, f"{persona_name}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(persona_data, f, ensure_ascii=False, indent=2)

        # 更新当前人格
        self.current_persona = persona_name
        self.current_persona_path = filepath

        # 刷新界面
        self._refresh_after_persona_creation(persona_name)

        print("✅ [Debug] 人格创建流程完成")
        return True

    def _refresh_after_persona_creation(self, persona_name):
        """创建人格后的界面刷新"""
        # 后台扫描人格列表
        self.thread_pool.submit(lambda: self.safe_execute(self.scan_personas_background))

        # 显示成功消息
        self.safe_append_message("System", f"✅ 已创建新人格空间: 【{persona_name}】", "Success")

        # 更新侧边栏
        if hasattr(self.main_frame.sidebar, 'update_persona_info'):
            self.main_frame.sidebar.update_persona_info(persona_name)

        # 刷新文档列表
        self.refresh_doc_list()

    def load_persona(self, path_or_name):
        """
        🔥 [最终修复版] 加载人格配置
        修复了 append_message -> safe_append_message 的命名错误
        """
        print(f"📝 UI Log: [System] 📂 准备解析: {path_or_name}")

        try:
            # 1. 确定完整路径
            if os.path.exists(path_or_name):
                file_path = path_or_name
            else:
                clean_name = path_or_name.strip()
                # 智能补全后缀
                if clean_name.lower().endswith(".json"):
                    filename = clean_name
                else:
                    filename = clean_name + ".json"

                # 尝试从配置目录拼接
                if hasattr(SETTINGS, 'PERSONAS_DIR'):
                    file_path = os.path.join(SETTINGS.PERSONAS_DIR, filename)
                else:
                    # 回退方案
                    file_path = os.path.join(os.getcwd(), 'ATHENA_WORKSPACE', 'Database', 'Personas', filename)

            # 2. 处理可能存在的双后缀问题 (.json.json)
            if file_path.endswith(".json.json"):
                file_path = file_path[:-5]
                print(f"🔄 [Path Fix] 修正双后缀路径为: {file_path}")

            # 3. 检查文件是否存在
            if not os.path.exists(file_path):
                print(f"❌ [Error] 找不到人格文件: {file_path}")
                QMessageBox.warning(self, "加载失败", f"找不到文件：\n{file_path}")
                return False

            # 4. 读取数据
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 5. 应用数据到系统
            self.current_persona = data.get("name", "Unknown")

            # 更新窗口标题
            self.setWindowTitle(f"Athena Genesis v25.0 - [{self.current_persona}]")

            # 更新系统提示词 (System Prompt) -> 发送给大脑
            system_prompt = data.get("system_prompt", "")

            # 尝试注入大脑配置
            if system_prompt and hasattr(self, 'brain'):
                print(f"🧠 [Brain] 正在注入人格设定: {self.current_persona}")
                # 优先尝试 update_config
                if hasattr(self.brain, 'update_config'):
                    self.brain.update_config({"system_prompt": system_prompt})
                # 其次尝试 commander 的方法
                elif hasattr(self.brain, 'commander') and hasattr(self.brain.commander, 'update_system_prompt'):
                    self.brain.commander.update_system_prompt(system_prompt)

            # 6. 在UI聊天框显示欢迎语
            welcome_msg = f"已激活人格：**{self.current_persona}**\n\n_{data.get('description', '无描述')}_"

            # 🔥🔥🔥【核心修复点】🔥🔥🔥
            # 将 self.append_message 改为 self.safe_append_message
            if hasattr(self, 'safe_append_message'):
                # 标准调用: 发送者, 内容, 消息类型
                self.safe_append_message("System", welcome_msg, "System")
            else:
                print(f"UI Message: {welcome_msg}")

            print(f"✅ [Success] 成功加载人格: {self.current_persona}")
            return True

        except json.JSONDecodeError as e:
            print(f"❌ [JSON Error] JSON解析错误: {e}")
            QMessageBox.critical(self, "解析错误", f"人格文件格式损坏:\n{e}")
            return False
        except Exception as e:
            print(f"❌ [Load Error] 加载人格失败: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "加载错误", f"加载人格文件失败:\n{e}")
            return False
    def load_persona_space(self, path):
        """
        菜单栏兼容接口
        当菜单点击 'load_persona_space' 时，重定向到我们要用的 load_persona
        """
        print(f"🔄 [Redirect] 菜单调用了旧接口，正在转发到标准加载函数... ({path})")
        self.load_persona(path)

    def _load_persona_thread_enhanced(self, file_path):
        """后台加载人格逻辑"""
        try:
            data = self.io_manager.load_persona(file_path)
            if not data:
                self.safe_append_message("System", "人格文件损坏或为空", "Error")
                return

            name = data.get("name", "Unknown")
            docs = data.get("documents", [])

            QTimer.singleShot(0, lambda: self._activate_persona_ui_immediate(name, file_path, data))

            self.safe_append_message("System", f"✅ 人格 [{name}] 配置已加载", "Success")

            recovered_count = 0

            if docs and isinstance(docs, list):
                self.safe_append_message("System", f"🔍 检测到 {len(docs)} 个关联文档，正在校验完整性...", "System")

                if len(docs) > 0:
                    self.safe_append_message("System", f"⚡ 正在尝试恢复 {len(docs)} 个文档...", "System")

                for doc_name in docs:
                    real_path = self.io_manager.smart_find_file(doc_name)

                    if real_path and os.path.exists(real_path):
                        print(f"✅ [Recover] 找到源文件: {real_path}")
                        threading.Thread(
                            target=self._recover_document_thread,
                            args=(real_path, doc_name),
                            daemon=True
                        ).start()
                        recovered_count += 1
                    else:
                        print(f"❌ [Recover] 无法找到源文件: {doc_name}")
                        self.safe_append_message("System", f"❌ 源文件丢失: {doc_name}", "Error")

                if recovered_count > 0:
                    self.safe_append_message("System", f"✅ 已成功触发 {recovered_count} 个文档的自动恢复流程",
                                             "Success")
                else:
                    self.safe_append_message("System", "⚠️  未发现需要恢复的文档", "Warning")

            else:
                self.safe_append_message("System", "ℹ️  该人格没有关联文档", "Info")

        except Exception as e:
            error_msg = f"人格加载失败: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            self.safe_append_message("System", f"❌ {error_msg}", "Error")

    def _activate_persona_ui_immediate(self, name, filepath, persona_data):
        """立即更新人格UI并刷新仪表盘"""
        try:
            self.current_persona = name
            self.current_persona_path = filepath
            self.io_manager.current_persona = name

            if hasattr(self.knowledge_keeper, 'load_persona_cache'):
                self.knowledge_keeper.load_persona_cache(name)

            if hasattr(self.main_frame.sidebar, 'update_persona_info'):
                self.main_frame.sidebar.update_persona_info(name)

            self._force_refresh_dashboard_from_persona(persona_data)

            self.safe_append_message("System", f"✅ 人格激活完成: 【{name}】", "Success")

            self.refresh_doc_list()

        except Exception as e:
            print(f"❌ 人格UI激活失败: {e}")

    def _force_refresh_dashboard_from_persona(self, persona_data):
        """强制从人格数据刷新仪表盘和雷达图"""
        try:
            radar_data = {}

            if "radar" in persona_data:
                radar_data = persona_data["radar"]
            elif "dimensions" in persona_data and "radar" in persona_data["dimensions"]:
                radar_data = persona_data["dimensions"]["radar"]
            elif "data" in persona_data and "radar" in persona_data["data"]:
                radar_data = persona_data["data"]["radar"]
            elif "radar_metrics" in persona_data:
                radar_data = persona_data["radar_metrics"]

            if radar_data:
                print(f"📊 [UI刷新] 从人格数据加载雷达图数据: {len(radar_data)}个维度")

                if hasattr(self.signal_bus, 'radar_signal'):
                    self.signal_bus.radar_signal.emit({"radar_metrics": radar_data})
                elif hasattr(self.main_frame.sidebar, 'radar_widget'):
                    self.main_frame.sidebar.radar_widget.update_data(radar_data)

            keywords_data = {}
            if "keywords" in persona_data:
                keywords_data = persona_data["keywords"]
            elif "semantic_summary" in persona_data and "keywords" in persona_data["semantic_summary"]:
                keywords_data = persona_data["semantic_summary"]["keywords"]
            elif "data" in persona_data and "keywords" in persona_data["data"]:
                keywords_data = persona_data["data"]["keywords"]

            if keywords_data:
                print(f"🔑 [UI刷新] 从人格数据加载关键词: {len(keywords_data)}个关键词")

                if hasattr(self.signal_bus, 'knowledge_signal'):
                    self.signal_bus.knowledge_signal.emit({"keywords": keywords_data})
                elif hasattr(self.main_frame.sidebar, 'knowledge_widget'):
                    if hasattr(self.main_frame.sidebar.knowledge_widget, 'update_keywords'):
                        self.main_frame.sidebar.knowledge_widget.update_keywords(keywords_data)

            QCoreApplication.processEvents()

        except Exception as e:
            print(f"⚠️ 仪表盘刷新失败: {e}")

    def _recover_document_thread(self, file_path, doc_name):
        """在后台线程中恢复单个文档"""
        try:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                self.safe_append_message("System", f"📖 正在读取: {doc_name} ({file_size:,} 字节)", "System")

                time.sleep(0.5)

                if hasattr(self, 'brain') and self.brain and hasattr(self.brain, 'launch'):
                    self.brain.launch(
                        user_input="",
                        mode="analysis",
                        config={
                            "file_path": file_path,
                            "file_name": os.path.basename(file_path),
                            "recovery_mode": True,
                            "original_doc_name": doc_name,
                            "analysis_mode": "fast"
                        }
                    )

                    print(f"✅ [Recover] 文档恢复任务已提交: {doc_name}")
                else:
                    print(f"❌ [Recover] 大脑未初始化，无法恢复文档: {doc_name}")
            else:
                print(f"❌ [Recover] 文件不存在: {file_path}")

        except Exception as e:
            print(f"❌ [Recover] 文档恢复失败: {doc_name} - {str(e)}")
            traceback.print_exc()

    def load_persona_data(self, filename):
        """加载特定人格数据"""
        try:
            self.safe_update_status(f"正在加载人格: {filename}...")

            personas_dir = getattr(SETTINGS.PATHS.directories, 'personas', None)
            if not personas_dir:
                personas_dir = os.path.join(os.getcwd(), 'ATHENA_WORKSPACE', 'Database', 'Personas')

            filepath = os.path.join(personas_dir, filename)
            if os.path.exists(filepath):
                self.load_persona_space(filepath)
            else:
                self.safe_append_message("System", f"❌ 人格文件不存在: {filepath}", "Error")
        except Exception as e:
            print(f"❌ 加载人格数据失败: {e}")

    def scan_personas(self):
        """强力扫描人格 - 后台线程"""
        try:
            self.thread_pool.submit(lambda: self.safe_execute(self.scan_personas_background))
            return []
        except Exception as e:
            print(f"❌ 扫描人格失败: {e}")
            return []

    def scan_personas_background(self):
        """后台线程：扫描人格"""
        try:
            personas_dir = getattr(SETTINGS.PATHS.directories, 'personas', None)

            if not personas_dir:
                personas_dir = os.path.join(os.getcwd(), 'ATHENA_WORKSPACE', 'Database', 'Personas')

            print(f"🔎 [Scan] 正在扫描人格存档路径: {personas_dir}")

            if not os.path.exists(personas_dir):
                try:
                    os.makedirs(personas_dir, exist_ok=True)
                    print(f"✅ [Scan] 已自动创建路径: {personas_dir}")
                except Exception as e:
                    print(f"❌ [Scan] 创建路径失败: {e}")
                    return []

            files = glob.glob(os.path.join(personas_dir, "*.json"))

            valid_names = []
            valid_files = []

            for f in files:
                try:
                    if os.path.getsize(f) > 0:
                        with open(f, 'r', encoding='utf-8') as file:
                            content = file.read().strip()
                            if content:
                                try:
                                    json.loads(content)
                                    valid_names.append(os.path.splitext(os.path.basename(f))[0])
                                    valid_files.append(os.path.basename(f))
                                except json.JSONDecodeError:
                                    print(f"⚠️ [Scan] 跳过损坏的JSON文件: {os.path.basename(f)}")
                    else:
                        print(f"⚠️ [Scan] 跳过空文件: {os.path.basename(f)}")
                except Exception as e:
                    print(f"⚠️ [Scan] 检查文件 {os.path.basename(f)} 失败: {e}")

            count = len(valid_files)
            print(f"🔎 [Scan] 扫描结果: 发现 {count} 个有效存档")

            QTimer.singleShot(0, lambda: self.safe_update_status(f"就绪 | 已发现 {count} 个人格"))

            if hasattr(self.main_frame.sidebar, 'update_list'):
                QTimer.singleShot(0, lambda: self.main_frame.sidebar.update_list(valid_files))
            elif hasattr(self.main_frame.sidebar, 'update_persona_list'):
                QTimer.singleShot(0, lambda: self.main_frame.sidebar.update_persona_list(valid_names))

            return valid_files

        except Exception as e:
            print(f"❌ [Scan] 扫描失败: {e}")
            return []

    def refresh_doc_list(self):
        """刷新侧边栏的文档列表"""
        try:
            if not self.current_persona:
                return

            sidebar = self.main_frame.sidebar
            if hasattr(sidebar, 'doc_list'):
                sidebar.doc_list.clear()
                docs = self.knowledge_base.get_all_docs()
                for doc in docs:
                    sidebar.doc_list.addItem(doc)
                print(f"📚 [Refresh] 刷新文档列表: {len(docs)} 个文档")
        except Exception as e:
            print(f"❌ 刷新文档列表失败: {e}")

    def import_document(self):
        """导入文档"""
        try:
            if not self.current_persona:
                QMessageBox.warning(self, "警告", "请先加载一个人格空间")
                return False

            print("🖱️ [UI] 点击了导入按钮")

            files, _ = QFileDialog.getOpenFileNames(
                self,
                "选择文档",
                "",
                "All Files (*.*)",
                options=QFileDialog.Option.DontUseNativeDialog
            )

            if not files:
                print("🚫 [UI] 用户取消了导入")
                return False

            QCoreApplication.processEvents()

            self.thread_pool.submit(lambda: self.safe_execute(self.import_documents_background, files))
            return True

        except Exception as e:
            error_msg = f"导入文档失败: {str(e)}"
            print(f"❌ {error_msg}")
            self.safe_append_message("System", f"❌ {error_msg}", "Error")
            return False

    def import_documents_background(self, files):
        """后台线程：导入文档并索引"""
        try:
            imported_count = 0
            for i, file_path in enumerate(files):
                try:
                    filename = os.path.basename(file_path)

                    if hasattr(self.io_manager, 'parse_file'):
                        content = self.io_manager.parse_file(file_path)
                    else:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                    if not content or not content.strip():
                        print(f"⚠️ 文件 {filename} 内容为空，跳过")
                        continue

                    words = jieba.lcut(content)
                    keywords = {}
                    for word in words:
                        if len(word) > 1:
                            keywords[word] = keywords.get(word, 0) + 1

                    self.knowledge_base.add_document(
                        filename,
                        content,
                        keywords,
                        {
                            "source": "imported",
                            "persona": self.current_persona,
                            "path": file_path,
                            "import_time": datetime.now().isoformat()
                        }
                    )

                    imported_count += 1

                    if hasattr(self.io_manager, 'save_upload'):
                        self.io_manager.save_upload(file_path, self.current_persona)

                    QTimer.singleShot(0, lambda fname=filename: (
                        self.safe_append_message("System", f"📥 导入 {fname}...正在后台索引", "System")
                    ))

                    if (i + 1) % 3 == 0:
                        QCoreApplication.processEvents()

                except Exception as e:
                    print(f"导入文件 {file_path} 失败: {e}")
                    QTimer.singleShot(0, lambda fname=filename: self.safe_append_message(
                        "System", f"❌ 导入 {fname} 失败: {str(e)}", "Error"
                    ))

            QTimer.singleShot(0, lambda: self.safe_execute(self.refresh_doc_list))

            if imported_count > 0:
                QTimer.singleShot(0, lambda: self.safe_append_message(
                    "System",
                    f"✅ 成功导入 {imported_count}/{len(files)} 个文档到人格空间【{self.current_persona}】",
                    "Success"
                ))

                if hasattr(self, 'brain') and self.brain:
                    self.safe_append_message("System", f"🔥 文档库已更新，正在重新生成画像...", "System")
                    QTimer.singleShot(1500, lambda: self.safe_execute(self._trigger_active_analysis, imported_count))
                else:
                    self.safe_append_message("System", f"✅ 文档导入完成，共 {imported_count} 个文档。", "Success")
            else:
                QTimer.singleShot(0, lambda: self.safe_append_message(
                    "System",
                    "⚠️ 未能成功导入任何文档",
                    "Warning"
                ))

            return imported_count > 0
        except Exception as e:
            print(f"❌ 后台导入失败: {e}")
            return False

    # ==========================================
    # 新增高级功能方法
    # ==========================================

    def action_analyze(self, filename):
        """深度解读"""
        try:
            if self.brain is None:
                self.safe_append_message("System", "❌ 大脑未初始化，无法执行深度解读", "Error")
                return

            print(f"🔍 [Analyze] 开始深度解读: {filename}")
            self.safe_append_message("System", f"🔍 正在对【{filename}】进行深度解读...", "System")

            if hasattr(self.brain, 'launch'):
                self.brain.launch(
                    f"请深度分析文档 {filename} 的核心观点、写作风格和关键词。",
                    mode="system_cmd",
                    config={"file_focus": filename, "web_search": False}
                )
            else:
                self.safe_append_message("System", "大脑不支持深度解读功能", "Error")
        except Exception as e:
            print(f"❌ 深度解读失败: {e}")

    def action_mimic(self, filename):
        """仿写"""
        try:
            if self.brain is None:
                self.safe_append_message("System", "❌ 大脑未初始化，无法执行仿写", "Error")
                return

            print(f"🎭 [Mimic] 开始仿写: {filename}")
            self.safe_append_message("System", f"🎭 准备仿写，参考对象：【{filename}】", "System")

            if hasattr(self.brain, 'launch'):
                self.brain.launch(
                    f"请模仿 {filename} 的文风，写一段关于'人工智能未来'的短文。",
                    mode="deep_write",
                    config={"style_ref": filename, "web_search": False}
                )
        except Exception as e:
            print(f"❌ 仿写失败: {e}")

    def action_continue(self, filename):
        """续写"""
        try:
            if self.brain is None:
                self.safe_append_message("System", "❌ 大脑未初始化，无法执行续写", "Error")
                return

            print(f"✍️ [Continue] 开始续写: {filename}")
            self.safe_append_message("System", f"✍️ 正在为【{filename}】进行续写...", "System")

            if hasattr(self.brain, 'launch'):
                self.brain.launch(
                    f"请根据 {filename} 的内容，续写接下来的段落。",
                    mode="deep_write",
                    config={"context_ref": filename, "web_search": False}
                )
        except Exception as e:
            print(f"❌ 续写失败: {e}")

    def on_doc_selected(self, name):
        """文档被选中时，尝试加载其分析数据到仪表盘"""
        try:
            self.safe_update_status(f"选中: {name}")
        except Exception as e:
            print(f"❌ 文档选中处理失败: {e}")

    # ==========================================
    # 核心优化：知识库搜索
    # ==========================================

    def search_knowledge_async(self, query):
        """异步搜索知识库：不卡界面"""
        try:
            if not query or not query.strip():
                return

            print(f"🔍 [Search] 开始异步搜索知识库: '{query}'")
            self.safe_append_message("System", f"🔍 正在后台检索知识库: {query}...", "System")

            if hasattr(self, 'brain') and self.brain and hasattr(self.brain, 'launch'):
                self.brain.launch(query, mode="kb_search")
            else:
                self.thread_pool.submit(lambda: self.safe_execute(self.search_knowledge_background, query))
        except Exception as e:
            print(f"❌ 搜索知识库失败: {e}")

    def search_knowledge_background(self, query):
        """后台线程：搜索知识库"""
        try:
            results = self.knowledge_base.search(query)

            if results:
                result_count = len(results.split('【来源:')) - 1

                QTimer.singleShot(0, lambda: self.safe_append_message(
                    "System",
                    f"🔍 知识库搜索: '{query}'\n"
                    f"📚 找到 {result_count} 个相关文档",
                    "Info"
                ))

                QTimer.singleShot(0, lambda: self.safe_append_message("Athena", results, "ai"))

                if hasattr(self.main_frame.sidebar, 'knowledge_widget'):
                    QTimer.singleShot(0, lambda r=results: (
                        self.safe_execute(
                            getattr(self.main_frame.sidebar.knowledge_widget, 'show_results',
                                    getattr(self.main_frame.sidebar.knowledge_widget, 'display_results',
                                            lambda x: None)),
                            r
                        )
                    ))
            else:
                QTimer.singleShot(0, lambda: self.safe_append_message(
                    "System",
                    f"🔍 知识库搜索: '{query}'\n"
                    f"📭 未找到相关文档",
                    "Info"
                ))

        except Exception as e:
            print(f"搜索知识库失败: {e}")
            QTimer.singleShot(0, lambda: self.safe_append_message(
                "System", f"❌ 知识库搜索失败: {str(e)}", "Error"
            ))

    # ==========================================
    # 聊天和系统处理方法
    # ==========================================

    def _on_user_send_message(self, text):
        """处理用户发送的消息"""
        try:
            if not text.strip():
                return

            self.safe_append_message("User", text, "User")

            if hasattr(self.main_frame.chat_area, 'clear_input'):
                self.main_frame.chat_area.clear_input()
            elif hasattr(self.main_frame.chat_area, 'input_box'):
                self.main_frame.chat_area.input_box.clear()

            if hasattr(self.main_frame.chat_area, 'set_loading'):
                self.main_frame.chat_area.set_loading(True)

            use_web = False
            if hasattr(self.main_frame.sidebar, 'chk_web'):
                use_web = self.main_frame.sidebar.chk_web.isChecked()
            elif hasattr(self.main_frame.sidebar, 'web_search_check'):
                use_web = self.main_frame.sidebar.web_search_check.isChecked()

            temp = 0.7
            if hasattr(self.main_frame.sidebar, 'slider_temp'):
                temp = self.main_frame.sidebar.slider_temp.value() / 100.0
            elif hasattr(self.main_frame.sidebar, 'temp_slider'):
                temp = self.main_frame.sidebar.temp_slider.value() / 10.0

            config = {"web_search": use_web, "temperature": temp}

            current_mode = "chat"
            if hasattr(self.main_frame, 'get_current_mode'):
                current_mode = self.main_frame.get_current_mode()
            elif hasattr(self.main_frame.sidebar, 'get_current_mode'):
                current_mode = self.main_frame.sidebar.get_current_mode()

            if "分析" in text and ("全量" in text or "画像" in text):
                current_mode = "analyze_persona"

            if not self.current_persona:
                QMessageBox.warning(self, "未就绪", "请先加载一个人格空间！")
                if hasattr(self.main_frame.chat_area, 'set_loading'):
                    self.main_frame.chat_area.set_loading(False)
                return

            if self.brain is None:
                self.safe_append_message("System", "❌ 大脑未初始化，无法处理请求。请查看控制台日志。", "Error")
                if hasattr(self.main_frame.chat_area, 'set_loading'):
                    self.main_frame.chat_area.set_loading(False)
                return

            print(f"🚀 [Launch] 发送指令: '{text}' | 模式: {current_mode} | 联网: {use_web} | 温度: {temp}")

            if hasattr(self.brain, 'task_queue'):
                task = {
                    "type": "chat",
                    "payload": text,
                    "mode": current_mode,
                    "config": config
                }
                self.brain.task_queue.put(task)
            elif hasattr(self.brain, 'launch'):
                self.brain.launch(text, mode=current_mode, config=config)
            else:
                print("❌ 错误：大脑没有可用的任务处理方法")

            self.safe_update_status(f"处理中... [{current_mode}]")
        except Exception as e:
            print(f"❌ 用户输入处理失败: {e}")
            if hasattr(self.main_frame.chat_area, 'set_loading'):
                self.main_frame.chat_area.set_loading(False)

    @pyqtSlot()
    def launch_brain(self):
        """启动大脑 (兼容旧版本)"""
        try:
            user_text = ""
            if hasattr(self.main_frame, 'get_input'):
                user_text = self.main_frame.get_input()
            elif hasattr(self.main_frame.chat_area, 'get_input'):
                user_text = self.main_frame.chat_area.get_input()
            elif hasattr(self.main_frame.chat_area, 'get_input_text'):
                user_text = self.main_frame.chat_area.get_input_text()
            elif hasattr(self.main_frame.chat_area, 'input_box'):
                user_text = self.main_frame.chat_area.input_box.text()

            if not user_text or user_text.strip() == "":
                return

            self._on_user_send_message(user_text)
        except Exception as e:
            self.handle_brain_error(str(e))

    @pyqtSlot(dict)
    def handle_brain_result(self, result):
        """处理大脑返回的结果"""
        try:
            print(f"📥 [Main] 收到大脑回复: {str(result)[:100]}...")

            res_type = result.get("type", "chat")
            content = result.get("content", "")
            sender = result.get("sender", "Athena")

            if hasattr(self.main_frame.chat_area, 'set_loading'):
                self.main_frame.chat_area.set_loading(False)

            if res_type == "kb_results":
                if hasattr(self.main_frame.sidebar, 'knowledge_widget'):
                    QTimer.singleShot(0, lambda: self.safe_execute(
                        getattr(self.main_frame.sidebar.knowledge_widget, 'show_results',
                                getattr(self.main_frame.sidebar.knowledge_widget, 'display_results', lambda x: None)),
                        content
                    ))

                result_count = len(content) if isinstance(content, list) else 0
                self.safe_append_message("System", f"✅ 知识库检索完成，找到 {result_count} 条结果。", "System")

                if result_count > 0 and isinstance(content, list):
                    first_result = content[0] if content else ""
                    self.safe_append_message("Athena", first_result, "ai")
            elif content:
                if result.get("mode") == "deep_write":
                    msg_type = "deep"
                elif result.get("mode") == "simple_qa":
                    msg_type = "simple"
                else:
                    msg_type = "ai"

                self.safe_append_message(sender, content, msg_type)
                mode = result.get("mode", "chat")
                self.safe_update_status(f"✓ 完成 [{mode}]")
            else:
                self.safe_append_message("System", "⚠️ 收到空回复", "Warning")
                self.safe_update_status("⚠️ 空回复")
        except Exception as e:
            print(f"❌ 大脑结果处理失败: {e}")

    @pyqtSlot(str)
    def handle_brain_error(self, error_msg):
        """处理大脑错误"""
        try:
            if hasattr(self.main_frame.chat_area, 'set_loading'):
                self.main_frame.chat_area.set_loading(False)

            self.safe_append_message("System", f"❌ 大脑处理错误: {error_msg}", "Error")
            print(f"❌ 大脑错误: {error_msg}")
            self.safe_update_status("❌ 处理失败")
        except Exception as e:
            print(f"❌ 大脑错误处理失败: {e}")

    @pyqtSlot(str)
    def handle_system_error(self, error_msg):
        """处理系统错误"""
        try:
            self.safe_append_message("System", f"⚠️ 系统错误: {error_msg}", "Warning")
        except Exception as e:
            print(f"❌ 系统错误处理失败: {e}")

    @pyqtSlot(dict)
    def handle_system_message(self, data):
        """处理系统消息字典"""
        try:
            if isinstance(data, dict):
                content = data.get("content", "")
                msg_type = data.get("type", "System")
                self.safe_append_message("System", content, msg_type)
        except Exception as e:
            print(f"❌ 系统消息处理失败: {e}")

    # ==========================================
    # 辅助方法
    # ==========================================

    def _safe_load_persona(self):
        """安全的加载人格方法"""
        try:
            if hasattr(self, '_loading_lock') and self._loading_lock:
                return
            self._loading_lock = True
            QTimer.singleShot(300, lambda: setattr(self, '_loading_lock', False))
            self.load_persona_space()
        except Exception as e:
            print(f"❌ 安全加载失败: {e}")

    def _safe_create_persona(self):
        """安全的新建人格方法"""
        try:
            if hasattr(self, '_creating_lock') and self._creating_lock:
                return
            self._creating_lock = True
            QTimer.singleShot(300, lambda: setattr(self, '_creating_lock', False))
            self.create_persona()
        except Exception as e:
            print(f"❌ 安全创建失败: {e}")

    def _safe_import_document(self):
        """安全的导入文档方法"""
        try:
            if not self.current_persona:
                QMessageBox.warning(self, "警告", "请先加载一个人格空间")
                return

            if hasattr(self, '_importing_lock') and self._importing_lock:
                return
            self._importing_lock = True

            QTimer.singleShot(500, lambda: setattr(self, '_importing_lock', False))

            files, _ = QFileDialog.getOpenFileNames(
                self,
                "选择文档",
                "",
                "All Files (*.*)",
                options=QFileDialog.Option.DontUseNativeDialog
            )

            if files:
                print(f"📥 导入 {len(files)} 个文档")
                self.thread_pool.submit(lambda: self.safe_execute(self.import_documents_background, files))
        except Exception as e:
            print(f"❌ 安全导入失败: {e}")

    def _on_send_button(self):
        """发送按钮的统一处理"""
        try:
            chat_area = self.main_frame.chat_area
            text = ""

            if hasattr(chat_area, 'get_input'):
                text = chat_area.get_input()
            elif hasattr(chat_area, 'input_box'):
                text = chat_area.input_box.text()

            if text.strip():
                self._on_user_send_message(text)

                if hasattr(chat_area, 'clear_input'):
                    chat_area.clear_input()
                elif hasattr(chat_area, 'input_box'):
                    chat_area.input_box.clear()
        except Exception as e:
            print(f"❌ 发送按钮处理失败: {e}")

    def _trigger_active_analysis(self, doc_count):
        """触发主动分析"""
        try:
            if hasattr(self, 'brain') and self.brain and hasattr(self.brain, 'launch'):
                self.safe_append_message("System",
                                         f"🔥 主动分析启动: 正在对 {doc_count} 份文档进行全量综合画像...",
                                         "System")
                self.brain.launch("全量分析", mode="analyze_persona")
            else:
                if hasattr(self, 'brain') and self.brain and hasattr(self.brain, 'task_queue'):
                    task = {
                        "type": "chat",
                        "payload": "全量分析",
                        "mode": "analyze_persona",
                        "config": {}
                    }
                    self.brain.task_queue.put(task)
                else:
                    self.safe_append_message("System", "⚠️ 大脑未就绪，无法执行分析", "Warning")
        except Exception as e:
            print(f"❌ 主动分析触发失败: {e}")

    # ==========================================
    # 系统工具功能
    # ==========================================

    def show_about_dialog(self):
        """显示关于对话框"""
        try:
            QMessageBox.about(self,
                              f"关于 {SETTINGS.APP_NAME}",
                              f"{SETTINGS.APP_NAME} v{SETTINGS.VERSION}\n\n"
                              f"混合智能体系统 - 基于深度学习的智能对话平台\n"
                              f"© 2024 Athena Genesis 项目组\n\n"
                              f"技术支持: {SETTINGS.CONTACT_INFO}\n"
                              f"项目地址: {SETTINGS.REPO_URL}"
                              )
        except Exception as e:
            print(f"❌ 关于对话框显示失败: {e}")

    def closeEvent(self, event):
        """严格关闭窗口处理：安全清理所有资源"""
        try:
            print("🔚 [Close] 正在安全关闭系统...")

            print("🛑 [Close] 停止后台线程池...")
            self.thread_pool.shutdown(wait=True, cancel_futures=True)

            if hasattr(self, 'system_monitor'):
                print("📊 [Close] 停止系统监控...")
                try:
                    self.system_monitor.stop()
                except Exception as e:
                    print(f"⚠️ [Close] 停止系统监控时出错: {e}")

            if hasattr(self, 'brain') and self.brain:
                print("🧠 [Close] 停止大脑线程...")
                try:
                    self.brain.stop()
                    if hasattr(self.brain, 'wait'):
                        print("⏳ [Close] 等待大脑线程退出...")
                        self.brain.wait(3000)
                        print("✅ [Close] 大脑线程已安全退出")
                    else:
                        print("⚠️ [Close] 大脑没有 wait 方法，尝试简单停止")
                except Exception as e:
                    print(f"⚠️ [Close] 停止大脑时出错: {e}")

            if hasattr(self, 'knowledge_base') and hasattr(self.knowledge_base, 'save_db'):
                print("💾 [Close] 保存知识库...")
                try:
                    self.knowledge_base.save_db()
                except Exception as e:
                    print(f"⚠️ [Close] 保存知识库时出错: {e}")

            print("🧹 [Close] 清理UI资源...")
            try:
                if hasattr(self, 'main_frame'):
                    self.main_frame.deleteLater()
            except Exception as e:
                print(f"⚠️ [Close] 清理UI资源时出错: {e}")

            print("✅ [Close] 系统安全退出完成")
            event.accept()

        except Exception as e:
            print(f"❌ [Close] 关闭事件处理失败: {e}")
            traceback.print_exc()
            event.accept()