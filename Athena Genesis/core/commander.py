# -*- coding: utf-8 -*-
"""
总指挥 - 混合智能体大脑 (Phase 1 + Phase 2 完整合并版)
职责：
1. 接收 UI 指令，路由到对应 Worker
2. 管理 LLM、Mimicry、Analyzer 等核心引擎的生命周期
3. 与 TaskQueue 交互，确保任务可追踪
4. 保留所有模式功能，兼容旧版架构
5. 整合 Phase 2 的智能体架构
6. 异常熔断修复：确保单一模块失败不导致系统崩溃
"""
import re
import queue
import time
import traceback
import os
import datetime
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from config.settings import SETTINGS
from engines.llm_engine import LLMEngine
from engines.mimicry_engine import EnhancedMimicryEngine
from engines.document_analyzer import DocumentIntelligenceAnalyzer
from config.genres import get_genre_config
from engines.web_searcher import WebKnowledgeEngine, WebSearcher
from core.workers import create_worker, GLOBAL_TASK_QUEUE
from core.brain_modules.researcher import Researcher
from core.brain_modules.writer import Writer
from core.brain_modules.editor import Editor
from core.brain_modules.memory import Memory


class Commander(QObject):
    """
    总指挥 - 混合智能体大脑（全局视野性能优化版 v21.2 + Worker系统架构 + Phase 2 智能体）
    职责：大脑的执行官，负责异步处理耗时任务，管理Worker系统
    整合：Phase 1 所有模式 + Phase 2 智能体架构
    优化：统一任务处理流程，保持完全兼容性
    异常熔断：确保单一模块失败不导致系统崩溃
    """

    # 定义信号
    log_signal = pyqtSignal(str)
    query_result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    mode_changed = pyqtSignal(str)  # 新模式：模式切换信号
    token_signal = pyqtSignal(str)  # 新增：token使用信号

    def __init__(self, bus, io_manager, knowledge_base):
        super().__init__()
        self.bus = bus
        self.io_manager = io_manager
        self.knowledge_base = knowledge_base
        self.task_queue = GLOBAL_TASK_QUEUE

        print("🧠 [Commander] 正在初始化神经中枢...")

        # 系统配置
        self.system_config = {
            "web_enabled": getattr(SETTINGS, "web_search_enabled", False),
            "low_power_mode": False,
            "temperature": 0.7,
            "current_mode": "chat",
            # chat, simple_qa, deep_write, system_cmd, analyze_persona, kb_search, writer, analysis
            "strategy": {
                "audience": "普通用户",
                "goal": "提供有用信息",
                "genre": "通用/默认"
            }
        }

        # 🔥 优化点1：引擎常驻内存 (只初始化一次)
        # 初始化核心模块 - 使用异常熔断机制
        self._init_modules()

        # Worker系统相关
        self.active_workers = {}

        # Phase 2 架构：高级智能体 (传入必要的依赖)
        # 🔥 异常隔离：每个智能体独立初始化，防止单一模块失败导致系统崩溃
        self.writer = None
        self.editor = None
        self.researcher = None
        self._init_agents()

        # 旧版任务队列 (兼容性保留)
        self.legacy_task_queue = []
        self.legacy_thread = None
        self.is_legacy_running = False

        # 会话管理
        self.session_id = f"session_{int(time.time())}"
        self.task_counter = 0

        # 性能监控
        self.performance_stats = {
            "total_tasks": 0,
            "avg_response_time": 0,
            "mode_usage": {
                "chat": 0, "simple_qa": 0, "deep_write": 0, "system_cmd": 0,
                "analyze_persona": 0, "kb_search": 0, "writer": 0, "analysis": 0
            }
        }

        # 新增：记忆变量
        self.current_persona = "默认空间"
        self.last_generation_tail = ""
        self.last_system_role = "专业助手"

        # 连接智能体信号
        self._connect_agent_signals()

        self.bus.emit_log(
            "🧠 [总指挥] 混合智能体大脑已就绪（全局视野性能优化版 v21.2 + Worker系统 + Phase 2 智能体 + 异常熔断）")
        print("🧠 [Commander] 所有模块就绪")

    def _init_modules(self):
        """初始化所有功能模块（优化：只初始化一次，包含异常处理）"""
        try:
            # 核心引擎 - 常驻内存
            self.llm = LLMEngine()
            self.mimicry_engine = EnhancedMimicryEngine()
            self.analyzer = DocumentIntelligenceAnalyzer(self.llm)  # 新版API需要传入llm

            # Phase 1 功能模块
            self.memory = Memory(self.knowledge_base)

            print("✅ [Commander] 基础引擎加载完毕")

        except Exception as e:
            error_msg = f"❌ [Commander] 基础引擎严重故障: {traceback.format_exc()}"
            print(error_msg)
            # 这里如果不抛出，后面也会全崩，所以还是需要抛出
            raise Exception(f"核心引擎初始化失败: {str(e)}")

        # 初始化web引擎（双引擎支持）- 常驻内存
        self._init_web_engines()

    def _init_agents(self):
        """初始化高级智能体（异常隔离版）"""
        # 🔥 异常熔断：每个智能体独立初始化，防止单一模块失败导致系统崩溃

        # 1. 执笔人 (Writer)
        try:
            self.writer = Writer(self.bus, self.llm, self.mimicry_engine, self.io_manager, self.knowledge_base)
            print("✅ [Commander] Writer 初始化成功")
        except Exception as e:
            print(f"⚠️ [Commander] Writer 初始化失败: {traceback.format_exc()}")
            self.writer = None

        # 2. 审稿人 (Editor)
        try:
            self.editor = Editor(self.bus, self.llm)
            print("✅ [Commander] Editor 初始化成功")
        except Exception as e:
            print(f"⚠️ [Commander] Editor 初始化失败: {traceback.format_exc()}")
            self.editor = None

        # 3. 学习专员 (Researcher) - 这就是之前报错的地方
        try:
            self.researcher = Researcher(self.bus, self.llm, self.mimicry_engine, self.analyzer, self.io_manager,
                                         self.knowledge_base)
            print("✅ [Commander] Researcher 初始化成功")
        except Exception as e:
            print(f"❌ [Commander] Researcher 初始化失败: {traceback.format_exc()}")
            self.researcher = None

    def _connect_agent_signals(self):
        """连接各智能体的信号（异常安全版）"""
        # Phase 2 Writer 信号
        if self.writer:
            try:
                if hasattr(self.writer, 'log_signal'):
                    self.writer.log_signal.connect(self.log_signal.emit)
                if hasattr(self.writer, 'progress_signal'):
                    self.writer.progress_signal.connect(self.status_signal.emit)
            except Exception as e:
                print(f"⚠️ 连接 Writer 信号失败: {str(e)}")

        # Phase 1 研究员信号
        if self.researcher:
            try:
                if hasattr(self.researcher, 'log_signal'):
                    self.researcher.log_signal.connect(self.log_signal.emit)
                if hasattr(self.researcher, 'status_signal'):
                    self.researcher.status_signal.connect(self.status_signal.emit)
            except Exception as e:
                print(f"⚠️ 连接 Researcher 信号失败: {str(e)}")

        # Phase 1 编辑信号
        if self.editor:
            try:
                if hasattr(self.editor, 'log_signal'):
                    self.editor.log_signal.connect(self.log_signal.emit)
                if hasattr(self.editor, 'status_signal'):
                    self.editor.status_signal.connect(self.status_signal.emit)
            except Exception as e:
                print(f"⚠️ 连接 Editor 信号失败: {str(e)}")

    def _init_web_engines(self):
        """初始化Web引擎（双引擎支持）- 常驻内存"""
        try:
            # 引擎1：WebKnowledgeEngine（原版复杂引擎）
            self.web_engine = WebKnowledgeEngine(self.io_manager)
            if hasattr(self.web_engine, 'log_signal'):
                self.web_engine.log_signal.connect(self.bus.emit_log)
            self.log_signal.emit("🌐 网络知识引擎已加载")
        except ImportError:
            self.web_engine = None
            self.log_signal.emit("⚠️ 网络知识引擎不可用")
        except Exception as e:
            self.web_engine = None
            self.log_signal.emit(f"⚠️ 网络知识引擎初始化失败: {str(e)}")

        try:
            # 引擎2：WebSearcher（简化版搜索器）
            self.web_searcher = WebSearcher(self.io_manager)
            self.log_signal.emit("🔍 网络搜索器已加载")
        except ImportError:
            self.web_searcher = None
            self.log_signal.emit("⚠️ 网络搜索器不可用，将使用降级方案")
        except Exception as e:
            self.web_searcher = None
            self.log_signal.emit(f"⚠️ 网络搜索器初始化失败: {str(e)}")

    def set_mode(self, mode):
        """
        设置工作模式
        Args:
            mode: "chat"通用对话 / "simple_qa"简单问答 / "deep_write"深度研报 / "system_cmd"系统指令 /
                  "analyze_persona"人格分析 / "kb_search"知识库搜索 / "writer"写作模式 / "analysis"分析模式
        """
        # 扩展模式列表，包含 Phase 2 的模式
        valid_modes = ["chat", "simple_qa", "deep_write", "system_cmd",
                       "analyze_persona", "kb_search", "writer", "analysis"]
        if mode not in valid_modes:
            self.log_signal.emit(f"⚠️ 无效模式: {mode}, 使用默认chat模式")
            mode = "chat"

        old_mode = self.system_config["current_mode"]
        self.system_config["current_mode"] = mode

        # 更新统计
        if mode in self.performance_stats["mode_usage"]:
            self.performance_stats["mode_usage"][mode] += 1

        # 发射模式变更信号
        self.mode_changed.emit(mode)
        self.log_signal.emit(f"🔄 模式切换: {old_mode} -> {mode}")

        # 根据不同模式调整配置
        self._adjust_config_by_mode(mode)

    def _adjust_config_by_mode(self, mode):
        """根据不同模式调整配置"""
        if mode == "simple_qa":
            # 简单问答模式：快速响应，准确优先
            self.system_config["temperature"] = 0.3
            self.system_config["low_power_mode"] = False
        elif mode == "deep_write":
            # 深度研报模式：高质量输出，允许联网
            self.system_config["temperature"] = 0.6
            self.system_config["web_enabled"] = True
            self.system_config["low_power_mode"] = False
        elif mode == "system_cmd":
            # 系统指令模式：禁止联网，快速处理
            self.system_config["web_enabled"] = False
            self.system_config["low_power_mode"] = True
        elif mode == "analyze_persona":
            # 人格分析模式：深度分析，低功耗
            self.system_config["temperature"] = 0.5
            self.system_config["web_enabled"] = False
            self.system_config["low_power_mode"] = True
        elif mode == "kb_search":
            # 知识库搜索模式：快速检索，低功耗
            self.system_config["temperature"] = 0.3
            self.system_config["web_enabled"] = False
            self.system_config["low_power_mode"] = True
        elif mode == "writer":
            # 写作模式：平衡配置，启用联网
            self.system_config["temperature"] = 0.7
            self.system_config["web_enabled"] = True
            self.system_config["low_power_mode"] = False
        elif mode == "analysis":
            # 分析模式：准确分析，低功耗
            self.system_config["temperature"] = 0.4
            self.system_config["web_enabled"] = False
            self.system_config["low_power_mode"] = True
        else:  # chat模式
            # 通用对话模式：平衡配置
            self.system_config["temperature"] = 0.7
            self.system_config["low_power_mode"] = True

    def set_strategy(self, strategy):
        """设置写作策略"""
        if isinstance(strategy, dict):
            self.system_config["strategy"].update(strategy)
            self.log_signal.emit(f"🎯 策略更新: {strategy}")

    def set_temperature(self, temp):
        """设置思维温度"""
        if 0.1 <= temp <= 1.0:
            self.system_config["temperature"] = temp
            self.log_signal.emit(f"🌡️ 思维温度调整为: {temp}")
        else:
            self.log_signal.emit(f"⚠️ 温度值 {temp} 无效，应在0.1-1.0之间")

    def toggle_search(self, enabled):
        """切换联网搜索"""
        self.system_config["web_enabled"] = enabled
        status = "启用" if enabled else "禁用"
        self.log_signal.emit(f"🌐 联网搜索已{status}")

    def set_low_power_mode(self, enabled):
        """设置低功耗模式"""
        self.system_config["low_power_mode"] = enabled
        status = "启用" if enabled else "禁用"
        self.log_signal.emit(f"🔋 低功耗模式已{status}")

    def launch(self, user_input=None, config=None, payload=None, mode=None):
        """
        全能型执行入口（兼容队列和非队列调用）
        Worker系统架构版 + Phase 2 智能体整合 + 异常安全

        Args:
            user_input: 用户输入
            config: 配置参数
            payload: 负载数据
            mode: 执行模式（可选，不指定则使用当前模式）
        Returns:
            String 或 Dict
        """
        if config is None:
            config = {}

        # 如果有指定模式，临时切换
        current_mode = mode if mode else self.system_config["current_mode"]

        # 提取最终输入
        final_input = self._extract_final_input(user_input, payload)

        if not final_input or final_input.strip() == "":
            final_input = " "
            self.log_signal.emit("⚠️ 检测到空输入，已自动填充空格")

        self.log_signal.emit(f"🚀 Worker任务启动 | 模式:{current_mode}")
        self.log_signal.emit(f"📥 输入: {final_input[:100]}...")

        # 1. 策略上下文构建
        strategy_context = self._build_strategy_context(current_mode, config)

        # 2. 路由分发到Worker系统
        try:
            worker = None

            if current_mode in ["chat", "simple_qa", "simple_chat"]:
                # 启动对话线程
                worker = create_worker(
                    "athena",
                    brain=self,  # 将自己传进去，以便Worker调用核心引擎
                    user_input=final_input,
                    config=config,
                    payload=payload,
                    mode=current_mode
                )

            elif current_mode == "writer":
                # Phase 2 写作模式：调用 Writer 智能体
                if not self.writer:
                    self.error_signal.emit("写作模块未就绪，无法执行任务")
                    return {"type": "error", "error": "Writer模块未就绪"}

                worker = create_worker(
                    "athena",
                    brain=self,
                    user_input=final_input,
                    config=strategy_context,  # 传入处理后的策略
                    mode="writer"
                )

            elif current_mode == "analysis":
                # 分析模式（整合 Phase 1 和 Phase 2）
                file_path = payload.get("file_path") if isinstance(payload, dict) else None
                if not file_path:
                    raise ValueError("分析模式需要file_path")

                # 读取文件内容
                content = self.io_manager.read_full_content(file_path)
                worker = create_worker(
                    "analysis",
                    analyzer=self.analyzer,
                    content=content,
                    filename=payload.get("file_name", "unknown"),
                    mode=config.get("analysis_mode", "fast")
                )

            elif current_mode == "deep_write":
                # 深度研报模式使用专门的Worker
                worker = create_worker(
                    "deep_write",
                    brain=self,
                    query=final_input,
                    config=config,
                    strategy_context=strategy_context
                )

            elif current_mode == "analyze_persona":
                # 人格分析模式
                self._handle_persona_analysis()
                return "人格分析任务已启动"

            elif current_mode == "kb_search":
                # 知识库搜索模式
                results = self.knowledge_base.search(final_input)
                return self._format_kb_results(results)

            elif current_mode == "system_cmd":
                # 系统指令模式
                return self._process_system_cmd(final_input, config)

            # 3. 启动Worker并连接信号
            if worker:
                worker_id = id(worker)
                self.active_workers[worker_id] = worker

                # 信号连接
                if hasattr(worker, 'result_signal'):
                    worker.result_signal.connect(self._on_worker_result)
                if hasattr(worker, 'finished'):
                    # 分析模式特殊处理
                    if current_mode == "analysis":
                        worker.finished.connect(lambda: self._on_analysis_finished(worker))
                    else:
                        worker.finished.connect(lambda: self._cleanup_worker(worker_id))

                if hasattr(worker, 'error_signal'):
                    worker.error_signal.connect(self._on_worker_error)

                # 清理钩子
                worker.finished.connect(lambda: self._cleanup_worker(worker_id))

                worker.start()
                self.status_signal.emit(f"正在执行: {current_mode}...")
                return f"✅ 任务已启动到Worker #{worker_id}"

        except Exception as e:
            error_detail = traceback.format_exc()
            self.error_signal.emit(f"❌ 任务启动失败: {str(e)}")
            self.log_signal.emit(f"❌ 异常详情: {error_detail}")
            return str({"type": "error", "error": str(e)})

    def _build_strategy_context(self, mode, config):
        """
        构建策略上下文 (Context Object)
        整合 Phase 1 和 Phase 2 的策略构建
        """
        # Phase 1 策略上下文
        strategy = {
            "mode": mode,
            "target_audience": config.get("audience", self.system_config["strategy"]["audience"]),
            "tone": config.get("tone", "客观"),
            "genre": config.get("genre", self.system_config["strategy"]["genre"]),
            "goal": config.get("goal", self.system_config["strategy"]["goal"]),
            "temperature": self.system_config["temperature"],
            "web_enabled": self.system_config["web_enabled"],
            "recursion_level": 0  # 思考深度
        }

        # 添加 Phase 2 的额外字段
        strategy.update({
            "system_prompt": config.get("system_prompt", ""),
            "audience": config.get("audience", "通用读者"),
        })

        return strategy

    def _on_worker_result(self, result):
        """处理Worker结果"""
        # 特殊处理分析结果
        if result.get("type") == "analysis" and hasattr(self.bus, 'emit_document_analysis'):
            self.bus.emit_document_analysis(result)

        self.query_result_signal.emit(result)
        self.status_signal.emit("就绪")

    def _on_analysis_finished(self, worker):
        """处理分析结果完成"""
        # Phase 2 功能：通知bus分析完成
        if hasattr(self.bus, 'emit_document_analysis'):
            # 这里可以通过worker获取结果，具体实现根据Worker设计
            pass

        self.status_signal.emit("分析完成")

    def _on_worker_error(self, error_msg):
        """统一错误处理"""
        self.error_signal.emit(error_msg)
        self.status_signal.emit("出错")

    def _cleanup_worker(self, worker_id):
        """清理已完成的Worker"""
        if worker_id in self.active_workers:
            del self.active_workers[worker_id]

    def launch_async(self, user_input, mode="chat", config=None):
        """
        异步执行入口（兼容旧版，使用Worker系统）
        注意：旧版可能通过此方法调用，我们将其转换为Worker任务

        Args:
            user_input: 用户输入
            mode: 执行模式
            config: 配置参数
        """
        if config is None:
            config = {}

        # 创建任务并放入全局队列
        task = {
            "type": "async_task",
            "payload": user_input,
            "mode": mode,
            "config": config,
            "commander": self  # 传递当前commander实例
        }

        # 放入全局任务队列
        self.task_queue.put(task)

        self.log_signal.emit(f"📨 异步任务已加入全局队列 | 模式:{mode}")

    def _process_system_cmd(self, query, config):
        """处理系统指令模式"""
        self.log_signal.emit(f"🔒 [System] 执行内部指令: {query}")
        config['web_search'] = False  # 强制关闭联网

        # 简单处理系统指令
        system_prompt = "你是一个系统助手，处理内部指令。"
        response = self.llm.chat(query, system_prompt=system_prompt, options=config)

        return response

    def _format_kb_results(self, results):
        """格式化知识库搜索结果"""
        if isinstance(results, list):
            formatted_results = "\n\n".join([f"📄 {r}" for r in results])
        else:
            formatted_results = str(results)

        return f"📚 知识库检索结果:\n\n{formatted_results}"

    def _extract_final_input(self, user_input, payload):
        """智能解析输入"""
        if user_input is not None:
            if isinstance(user_input, dict):
                return user_input.get("content", str(user_input))
            else:
                return str(user_input)
        elif payload is not None:
            if isinstance(payload, dict):
                if "messages" in payload:
                    messages = payload.get("messages", [])
                    for msg in reversed(messages):
                        if msg.get("role") == "user" and msg.get("content"):
                            return msg.get("content")
                else:
                    return payload.get("content", str(payload))
            else:
                return str(payload)
        return ""

    # ==================================================
    # 🔥🔥🔥 保留旧版核心功能（兼容性）
    # ==================================================

    def start_legacy_thread(self):
        """启动旧版线程（兼容性）"""
        if self.legacy_thread is None:
            self.legacy_thread = LegacyCommanderThread(self)
            self.legacy_thread.start()
            self.is_legacy_running = True
            self.log_signal.emit("🔄 旧版兼容线程已启动")

    def stop_legacy_thread(self):
        """停止旧版线程"""
        if self.legacy_thread:
            self.legacy_thread.stop()
            self.legacy_thread.wait()
            self.legacy_thread = None
            self.is_legacy_running = False
            self.log_signal.emit("🛑 旧版兼容线程已停止")

    def legacy_launch(self, user_input=None, config=None, payload=None, mode=None):
        """
        旧版兼容入口（用于直接调用，不通过Worker）
        保留所有旧版功能
        """
        # 这里可以调用旧版的_legacy_process方法
        # 简化为直接调用原有逻辑
        return self._legacy_process_direct(user_input, config, payload, mode)

    def _legacy_process_direct(self, user_input, config, payload, mode):
        """直接处理逻辑（简化版）"""
        try:
            # 这里应该调用旧版的处理逻辑
            # 为了简化，我们直接使用核心引擎
            final_input = self._extract_final_input(user_input, payload)

            if mode == "system_cmd":
                return self._process_system_cmd(final_input, config or {})
            elif mode == "kb_search":
                results = self.knowledge_base.search(final_input)
                return self._format_kb_results(results)
            else:
                # 其他模式使用LLM直接处理
                system_prompt = "你是一个智能助手。"
                if self.io_manager and self.io_manager.current_persona:
                    system_prompt = f"你现在是【{self.io_manager.current_persona}】。"

                return self.llm.chat(final_input, system_prompt=system_prompt, options=config or {})

        except Exception as e:
            return f"❌ 旧版处理失败: {str(e)}"

    # ==================================================
    # 🔥🔥🔥 新增：全量人格分析 (Batch Analysis)
    # ==================================================
    def _handle_persona_analysis(self):
        """处理全量人格分析"""
        persona = self.io_manager.current_persona
        if not persona:
            self.log_signal.emit("⚠️ 未选择人格空间，无法进行分析")
            return

        self.log_signal.emit(f"🕵️‍♂️ [Analysis] 正在扫描人格空间: {persona} 的所有文档...")

        folder = self.io_manager.get_persona_folder(persona)
        if not os.path.exists(folder):
            self.log_signal.emit("⚠️ 目录为空，跳过分析")
            self.query_result_signal.emit({
                "type": "chat",
                "sender": "System",
                "content": "当前人格空间为空。请点击【导入文档】上传资料，我将为您生成风格画像。"
            })
            return

        # 1. 扫描所有文件
        files = [f for f in os.listdir(folder) if not f.startswith('.') and os.path.isfile(os.path.join(folder, f))]
        if not files:
            self.log_signal.emit("⚠️ 空间内没有文档，无法生成画像。")
            self.query_result_signal.emit({
                "type": "chat",
                "sender": "System",
                "content": "当前人格空间为空。请点击【导入文档】上传资料，我将为您生成风格画像。"
            })
            return

        # 2. 提取摘要
        combined_text = ""
        limit = 5  # 限制读取前5个文件，避免卡太久

        self.log_signal.emit(f"📖 [IO] 正在快速阅览前 {min(limit, len(files))} 个核心文档...")

        # 优先读取文本文件
        text_files = [f for f in files if f.endswith(('.txt', '.md', '.docx', '.pdf'))]
        read_count = 0

        for f in text_files:
            if read_count >= limit:
                break

            content = self._read_file_safe(f, folder)
            if content:
                # 每个文件截取前 1000 字
                combined_text += f"\n--- 文档: {f} ---\n{content[:1000]}\n"
                read_count += 1

        if not combined_text:
            self.log_signal.emit("⚠️ 文档无法读取文本内容")
            return

        # 3. 发送给 LLM 进行综合画像
        prompt = (
            f"基于以下文档片段，请对【{persona}】进行全方位人格/风格画像。\n"
            f"1. 提取5个核心关键词（用逗号分隔）。\n"
            f"2. 生成一段简短的风格描述（100字以内）。\n"
            f"3. 评估其思维维度的各项分值（逻辑、创意、严谨、情感、深度、广度，0.1-1.0之间）。\n"
            f"4. 总结其核心价值观或写作特色。\n\n"
            f"文档内容摘要：\n{combined_text}"
        )

        self.log_signal.emit("🧠 [LLM] 正在构建全息人格画像...")

        # 调用 LLM
        response = self.llm.chat(prompt, system_prompt="你是一个专业的人格侧写师。", options={"temperature": 0.5})

        # 4. 返回结果
        self.query_result_signal.emit({
            "type": "chat",
            "sender": "Athena",
            "content": f"📊 **【{persona}】全量分析报告**\n\n{response}",
            "mode": "analyze_persona"  # 标记模式，前端可特殊处理
        })
        self.status_signal.emit("画像生成完毕")

    def _read_file_safe(self, filename, folder):
        """安全读取文件内容的内部助手"""
        try:
            path = os.path.join(folder, filename)

            # 调用 IOManager 解析
            if hasattr(self.io_manager, 'parse_file'):
                return self.io_manager.parse_file(path)
            else:
                # 回退到普通读取
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
        except Exception as e:
            self.log_signal.emit(f"⚠️ 读取文件失败 {filename}: {str(e)}")
            return ""

    # ==================================================
    # 🔥🔥🔥 网络搜索功能（保留）
    # ==================================================

    def _force_web_search(self, query, config):
        """
        强制联网搜索（核心修复方法）
        """
        # 🔥 修复：系统指令强制不搜索
        if config.get("mode") == "system_cmd" or config.get("system_cmd", False):
            self.log_signal.emit(f"🔒 [System] 系统指令，跳过联网搜索: {query}")
            return ""

        self.log_signal.emit(f"🌍 [Web] 正在强制联网搜索: {query}...")

        search_result = ""

        # 尝试使用简化版搜索器（优先级1）
        if self.web_searcher:
            try:
                search_result = self.web_searcher.search(query)
                if search_result:
                    self.log_signal.emit("✅ [Web] 简化搜索器返回数据")
                    return search_result
            except Exception as e:
                self.log_signal.emit(f"⚠️ [Web] 简化搜索器失败: {str(e)}")

        # 尝试使用复杂引擎（优先级2）
        if self.web_engine:
            try:
                search_result = self.web_engine.search(query)
                if search_result:
                    self.log_signal.emit("✅ [Web] 复杂引擎返回数据")
                    return search_result
            except Exception as e:
                self.log_signal.emit(f"⚠️ [Web] 复杂引擎失败: {str(e)}")

        # 降级到researcher的搜索（优先级3）
        try:
            if self.researcher:
                search_result = self.researcher._search_web_async(query)
                if search_result:
                    self.log_signal.emit("✅ [Web] Researcher返回数据")
                    return search_result
        except Exception as e:
            self.log_signal.emit(f"⚠️ [Web] Researcher搜索失败: {str(e)}")

        # 如果所有方法都失败
        if not search_result:
            self.log_signal.emit("⚠️ [Web] 所有搜索方法均无返回")
            return "⚠️ 网络搜索未返回有效数据，请检查网络连接。"

        return search_result

    def get_performance_stats(self):
        """获取性能统计"""
        return {
            **self.performance_stats,
            "current_mode": self.system_config["current_mode"],
            "web_enabled": self.system_config["web_enabled"],
            "temperature": self.system_config["temperature"],
            "active_tasks": len(self.legacy_task_queue),
            "active_workers": len(self.active_workers),
            "agents_status": {
                "writer": self.writer is not None,
                "editor": self.editor is not None,
                "researcher": self.researcher is not None
            }
        }

    def stop(self):
        """
        紧急制动：停止所有活跃线程和Worker
        """
        # 停止Worker系统
        print(f"🛑 [Commander] 正在停止 {len(self.active_workers)} 个活跃Worker...")
        for worker in list(self.active_workers.values()):
            if hasattr(worker, 'isRunning') and worker.isRunning():
                if hasattr(worker, 'stop'):
                    worker.stop()
                elif hasattr(worker, 'terminate'):
                    worker.terminate()
                if hasattr(worker, 'wait'):
                    worker.wait()
        self.active_workers.clear()

        # 停止旧版线程
        self.stop_legacy_thread()

        self.log_signal.emit("🛑 大脑已安全停止")

    # 兼容性方法
    def isRunning(self):
        return self.is_legacy_running

    def start(self):
        self.start_legacy_thread()

    def wait(self):
        if self.legacy_thread:
            self.legacy_thread.wait()

    def terminate(self):
        self.stop()


class LegacyCommanderThread(QThread):
    """旧版兼容线程（用于运行旧版任务队列）"""

    def __init__(self, commander):
        super().__init__()
        self.commander = commander
        self.is_running = True

    def run(self):
        """线程主入口（旧版单队列模式）"""
        self.commander.log_signal.emit("🔄 旧版兼容线程运行中...")

        while self.is_running:
            try:
                if self.commander.legacy_task_queue:
                    task = self.commander.legacy_task_queue.pop(0)
                    if task is None:
                        break

                    self._process_single_task(task)
                else:
                    time.sleep(0.05)
                    continue

            except Exception as e:
                err_msg = f"旧版线程异常: {str(e)}\n{traceback.format_exc()}"
                self.commander.error_signal.emit(err_msg)
                time.sleep(1)

    def _process_single_task(self, task):
        """处理单个任务（旧版逻辑）"""
        # 这里可以调用旧版的处理逻辑
        # 简化为直接使用commander的legacy_launch
        t_type = task.get("type", "chat")
        payload = task.get("payload", "")
        config = task.get("config", {})
        mode = task.get("mode")

        try:
            result = self.commander.legacy_launch(
                user_input=payload,
                config=config,
                mode=mode or t_type
            )

            # 发送结果
            if result:
                result_package = {
                    "type": "chat",
                    "sender": "Athena",
                    "content": result,
                    "mode": self.commander.system_config["current_mode"],
                    "timestamp": time.time()
                }
                self.commander.query_result_signal.emit(result_package)

        except Exception as e:
            self.commander.error_signal.emit(f"旧版任务处理失败: {str(e)}")

    def stop(self):
        """停止线程"""
        self.is_running = False
        if self.commander.legacy_task_queue:
            self.commander.legacy_task_queue.append(None)
        self.wait()