# -*- coding: utf-8 -*-
"""
后台工作线程模块 - 终极防御融合稳定版 V6.1
融合终极防御融合版V6.0 + V6.1统一TaskQueue改进
保留所有核心线程、保险丝机制和兼容性
统一使用 core.persistence 的 GLOBAL_TASK_QUEUE
"""

print("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")
print("✅✅✅ WORKERS.PY (终极防御融合稳定版 V6.1) 已加载 ✅✅✅")
print("✅ 融合V6.0核心逻辑 + V6.1统一TaskQueue")
print("✅ 支持Writer智能写作 + 三层保险丝 + 全量线程")
print("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")

import os
import shutil
import time
import uuid
import traceback
from PyQt6.QtCore import QThread, pyqtSignal

# 🔥 核心修正：从 persistence 导入单例，而不是自己创建
try:
    from core.persistence import GLOBAL_TASK_QUEUE

    print("✅ 已加载全局TaskQueue单例")
except ImportError:
    # 降级处理，防止IDE报错
    print("⚠️ 无法导入 TaskQueue，使用虚拟队列")


    class MockQueue:
        def add_task(self, *args): return "mock_id"

        def update_status(self, *args): pass


    GLOBAL_TASK_QUEUE = MockQueue()


# ==========================================
# 工具函数：任务记录管理 (V6.1改进版)
# ==========================================
def _register_task(task_type, task_info):
    """注册任务到持久化队列 - 使用全局单例"""
    return GLOBAL_TASK_QUEUE.add_task(task_type, task_info)


def _update_task_status(task_id, status, extra_info=None):
    """更新任务状态 - 使用全局单例"""
    if task_id is not None:
        GLOBAL_TASK_QUEUE.update_status(task_id, status, extra_info)


# ==========================================
# 1. 文档分析线程 (AnalysisWorker) - V6.1改进版
# ==========================================
class AnalysisWorker(QThread):
    """
    文档分析线程 - V6.1改进版
    融合V6.0的多分析模式 + V6.1的统一TaskQueue
    """
    finished = pyqtSignal(dict)  # 分析完成信号
    error = pyqtSignal(str)  # 错误信号
    progress = pyqtSignal(str)  # 进度信号

    def __init__(self, analyzer, content, filename, mode="fast", **kwargs):
        """
        初始化文档分析线程

        Args:
            analyzer: DocumentIntelligenceAnalyzer实例
            content: 文档内容
            filename: 文件名
            mode: 分析模式 ("fast", "deep", "llm")
            **kwargs: 其他参数（如filepath）
        """
        super().__init__()
        self.analyzer = analyzer
        self.content = content
        self.filename = filename
        self.mode = mode
        self.kwargs = kwargs

        # TraceID和取消机制
        self.task_id = str(uuid.uuid4())[:8]  # 简短TraceID
        self.is_cancelled = False

        # filepath属性
        if 'filepath' in kwargs:
            self.filepath = kwargs['filepath']
        else:
            self.filepath = filename

    def run(self):
        """执行文档分析"""
        # V6.1: 注册任务到全局队列
        db_task_id = _register_task("analysis", {
            "filename": self.filename,
            "mode": self.mode,
            "size": len(self.content) if self.content else 0
        })
        _update_task_status(db_task_id, "RUNNING")

        try:
            print(f"🔍 [AnalysisWorker-{self.task_id}] 启动分析: {self.filename}, 模式: {self.mode}")

            result = None

            # 融合两个版本的调用逻辑
            if self.mode == "fast":
                # 优先使用fast_analyze
                if hasattr(self.analyzer, 'fast_analyze'):
                    result = self.analyzer.fast_analyze(self.content, self.filename)
                elif hasattr(self.analyzer, 'diagnose_analysis'):
                    result = self.analyzer.diagnose_analysis(self.content, self.filename)
                    # 补全fast模式可能缺失的字段
                    if result and "radar_metrics" not in result:
                        result["radar_metrics"] = {"逻辑性": 0.5, "创造力": 0.5}
                elif hasattr(self.analyzer, 'deep_analyze'):
                    # 降级到深度分析
                    print(f"[AnalysisWorker-{self.task_id}] fast_analyze不存在，降级到deep_analyze")
                    result = self.analyzer.deep_analyze(self.content, self.filename)
                else:
                    raise AttributeError("analyzer没有可用的分析方法")

            elif self.mode == "llm":
                # 优先使用llm_analyze
                if hasattr(self.analyzer, 'llm_analyze'):
                    result = self.analyzer.llm_analyze(self.content, self.filename)
                elif hasattr(self.analyzer, 'deep_analyze'):
                    # 降级到深度分析
                    print(f"[AnalysisWorker-{self.task_id}] llm_analyze不存在，降级到deep_analyze")
                    result = self.analyzer.deep_analyze(self.content, self.filename)
                else:
                    raise AttributeError("analyzer没有可用的分析方法")

            else:  # deep模式
                # 默认使用deep_analyze
                if hasattr(self.analyzer, 'deep_analyze'):
                    result = self.analyzer.deep_analyze(self.content, self.filename)
                else:
                    raise AttributeError("analyzer没有deep_analyze方法")

            # 检查是否被取消
            if self.is_cancelled:
                print(f"🛑 [AnalysisWorker-{self.task_id}] 任务已取消")
                _update_task_status(db_task_id, "CANCELLED")
                return

            # 处理结果
            if result is None:
                raise ValueError("分析结果为空")

            # 补充filepath用于缓存
            if isinstance(result, dict):
                if "document_info" in result:
                    # 确保document_info存在filepath字段
                    result["document_info"]["filepath"] = self.filepath

                    # 确保有分析模式标识
                    if "analysis_mode" not in result["document_info"]:
                        result["document_info"]["analysis_mode"] = self.mode

            # 任务完成
            _update_task_status(db_task_id, "COMPLETED")
            self.finished.emit(result)

        except Exception as e:
            error_msg = f"文档分析失败: {str(e)}"
            print(f"❌ [AnalysisWorker-{self.task_id}] 异常: {traceback.format_exc()}")
            _update_task_status(db_task_id, "FAILED", {"error": str(e)})
            self.error.emit(error_msg)

    def stop(self):
        """停止分析"""
        self.is_cancelled = True
        self.wait()


# ==========================================
# 2. 深思与对话线程 (DeepThinkingWorker) - V6.1改进版
# ==========================================
class DeepThinkingWorker(QThread):
    """
    🚀 深度思考工作线程 - V6.1改进版
    融合V6.0的直接调用逻辑和保险丝机制 + V6.1的统一TaskQueue
    """

    # 进度信号
    progress_update = pyqtSignal(int, str)
    progress = pyqtSignal(str)

    # 思维流信号
    thought_stream = pyqtSignal(str)

    # 完成信号
    finished = pyqtSignal(str)  # 最终结果信号
    finished_signal = pyqtSignal(str)  # 兼容信号
    result_signal = pyqtSignal(dict)  # 返回完整结果

    # 错误信号
    error = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    error_signal_phase1 = pyqtSignal(str)

    def __init__(self, brain, user_input, file_paths=None, config=None):
        """
        初始化深思工作线程

        Args:
            brain: AthenaBrain实例
            user_input: 用户输入文本
            file_paths: 文件路径列表 (可为空)
            config: 配置字典
        """
        super().__init__()
        self.brain = brain
        self.user_input = user_input
        self.file_paths = file_paths or []
        self.config = config or {}

        # TraceID和取消机制
        self.task_id = str(uuid.uuid4())[:8]
        self.is_cancelled = False

        print(f"[DeepThinkingWorker-{self.task_id}] 初始化: {user_input[:50]}...")
        print(f"[DeepThinkingWorker-{self.task_id}] 文件数量: {len(self.file_paths)}")

    def run(self):
        """
        🔥 V6.1改进版运行逻辑
        使用统一的GLOBAL_TASK_QUEUE
        """
        # V6.1: 注册任务到全局队列
        task_mode = "llm_deep" if len(self.file_paths) > 0 else "llm_chat"
        db_task_id = _register_task(task_mode, {
            "input_preview": self.user_input[:50],
            "file_count": len(self.file_paths),
            "mode": "deep_thinking"
        })
        _update_task_status(db_task_id, "RUNNING")

        try:
            # 1. 注入配置
            if hasattr(self.brain, 'current_config'):
                self.brain.current_config = self.config

            # 2. 发送开始处理的思维流
            self.thought_stream.emit(
                "<div style='color:#4caf50; font-weight:bold; margin-bottom:5px;'>"
                f"🚀 [任务{self.task_id}] Athena开始处理请求..."
                "</div>"
            )

            # 发送进度信号
            self.progress.emit("开始深度思考处理...")

            # 3. 定义回调函数
            def callback(percent, message, detail=None):
                """进度和思维流回调函数"""
                # 检查是否被取消
                if self.is_cancelled:
                    return

                # 发送进度更新
                self.progress_update.emit(percent, message)
                self.progress.emit(f"{percent}%: {message}")

                # 发送思维流
                if detail:
                    log_html = (
                        f"<div style='margin-top:2px; padding-left:10px;'>"
                        f"<span style='color:#00e5ff;'>▶</span> "
                        f"<span style='color:#ccc;'>{message}</span>"
                        f"<span style='color:#888; font-style:italic;'> → {detail}</span>"
                        f"</div>"
                    )
                else:
                    log_html = (
                        f"<div style='margin-top:2px; padding-left:10px;'>"
                        f"<span style='color:#4caf50;'>✓</span> "
                        f"<span style='color:#ccc;'>{message}</span>"
                        f"</div>"
                    )
                self.thought_stream.emit(log_html)

            # 4. 模式判断
            deep_keywords = [
                "写一篇", "写一个", "5000字", "所有文件", "稿件",
                "全量", "深度报告", "长文", "深思", "总结", "分析报告",
                "撰写", "编写", "创作", "报告", "文章"
            ]

            has_file_reference = any(keyword in self.user_input.lower()
                                     for keyword in ["文件", "文档", "资料", "材料", "内容"])

            # 模式判断逻辑
            is_deep_mode = (
                    any(k in self.user_input for k in deep_keywords) or
                    (has_file_reference and len(self.file_paths) > 0) or
                    len(self.file_paths) >= 3 or
                    self.config.get("mode") == "deep" or
                    "深度" in self.user_input or
                    "报告" in self.user_input
            )

            # 检查是否有联网搜索配置
            has_web_search = self.config.get("enable_web", False)

            # 🔥 5. 核心调用逻辑
            raw_result = None

            if is_deep_mode and hasattr(self.brain, 'global_deep_furnace'):
                # === 模式 A: 深思熔炉 (写长文) ===
                self.thought_stream.emit(
                    "<div style='color:#00bcd4; font-weight:bold; margin-top:5px;'>"
                    "🚀 启动多线程深思熔炉..."
                    "</div>"
                )

                if len(self.file_paths) > 0:
                    self.thought_stream.emit(
                        f"<div style='color:#ccc; padding-left:15px;'>"
                        f"📁 将分析 {len(self.file_paths)} 个文件..."
                        f"</div>"
                    )

                # 启动全量熔炉模式
                raw_result = self.brain.global_deep_furnace(
                    self.user_input,
                    self.file_paths,
                    callback=callback
                )

                self.thought_stream.emit(
                    "<div style='color:#4caf50; font-weight:bold; margin-top:5px;'>"
                    "✅ 深思熔炉处理完成！"
                    "</div>"
                )

            else:
                # === 模式 B: 普通对话 / 联网搜索 ===

                # 发送处理中的思维流
                if has_web_search:
                    self.thought_stream.emit(
                        "<div style='color:#ff9800; font-weight:bold; margin-top:5px;'>"
                        "🌐 联网搜索已启用，正在获取最新信息..."
                        "</div>"
                    )
                else:
                    self.thought_stream.emit(
                        "<div style='color:#4caf50; margin-top:5px;'>"
                        "💭 正在思考中，请稍候..."
                        "</div>"
                    )

                print(f"[DeepThinkingWorker-{self.task_id}] 调用 brain.launch(user_input='{self.user_input[:50]}...')")

                # 🔥🔥🔥 关键修改：使用 launch 方法
                try:
                    # 优先使用直接调用方式
                    raw_result = self.brain.launch(user_input=self.user_input, config=self.config)
                except TypeError as e:
                    # 如果参数不匹配，尝试其他调用方式
                    print(f"[DeepThinkingWorker-{self.task_id}] 参数不匹配，尝试备用调用方式: {e}")
                    try:
                        # 尝试不带config参数
                        raw_result = self.brain.launch(self.user_input)
                    except Exception as e2:
                        print(f"[DeepThinkingWorker-{self.task_id}] 第二次调用失败: {e2}")
                        # 尝试使用chat方法
                        if hasattr(self.brain, 'chat'):
                            raw_result = self.brain.chat(self.user_input)
                        else:
                            # 最后尝试
                            raw_result = f"无法调用大脑: {str(e2)}"

                self.thought_stream.emit(
                    "<div style='color:#4caf50; font-weight:bold; margin-top:5px;'>"
                    "✅ 思考完成！"
                    "</div>"
                )

            # 检查是否被取消
            if self.is_cancelled:
                print(f"🛑 [DeepThinkingWorker-{self.task_id}] 任务已取消")
                _update_task_status(db_task_id, "CANCELLED")
                return

            # 🔥 6. 终极保险丝：确保返回的总是字符串
            safe_response = self._ultimate_safe_convert(raw_result)

            # 最终检查
            if not safe_response or safe_response.isspace():
                safe_response = "Athena返回了空内容，请检查配置或重试。"

            print(f"[DeepThinkingWorker-{self.task_id}] 最终输出长度: {len(safe_response)} 字符")

            # 任务完成
            _update_task_status(db_task_id, "COMPLETED", {"length": len(safe_response)})

            # 🔥 7. 发射信号（兼容两个版本）
            # V6.0信号
            self.finished.emit(safe_response)
            self.finished_signal.emit(safe_response)

            # 完整结果信号
            self.result_signal.emit({
                "type": "chat",
                "sender": "Athena",
                "content": safe_response,
                "mode": "deep_thinking",
                "task_id": self.task_id
            })

        except Exception as e:
            # 记录完整错误信息
            error_trace = traceback.format_exc()
            print(f"❌ [DeepThinkingWorker-{self.task_id}] 异常: {error_trace}")

            # 更新任务状态
            _update_task_status(db_task_id, "FAILED", {"error": str(e)})

            # 发送错误思维流
            error_html = (
                f"<div style='color:#ff5252; font-weight:bold; margin-top:10px; padding:8px; "
                f"background-color:#ffebee; border-left:4px solid #f44336;'>"
                f"❌ [任务{self.task_id}] 运行出错: {str(e)}"
                f"</div>"
            )
            self.thought_stream.emit(error_html)

            # 发送错误信号
            error_msg = f"❌ 运行出错: {str(e)}"
            self.error.emit(error_msg)
            self.error_signal.emit(error_msg)
            self.error_signal_phase1.emit(error_msg)

    def _ultimate_safe_convert(self, raw_result):
        """🔥 终极保险丝转换"""
        if raw_result is None:
            return "Athena没有返回内容。"
        elif isinstance(raw_result, dict):
            # 尝试多个可能的字段
            for field in ['content', 'text', 'response', 'answer', 'result']:
                if field in raw_result:
                    value = raw_result[field]
                    if value is not None:
                        return str(value)
            return str(raw_result)
        else:
            return str(raw_result)

    def stop(self):
        """停止任务"""
        self.is_cancelled = True
        self.wait()


# ==========================================
# 3. Athena对话线程 (AthenaThread) - V6.1改进版
# ==========================================
class AthenaThread(QThread):
    """
    Athena对话线程 - V6.1改进版
    融合V6.0的信号兼容性 + V6.1的统一TaskQueue
    支持Writer智能写作和路由逻辑
    """

    # V6.0信号名称 (保持兼容)
    response_ready = pyqtSignal(str)
    signal_response = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    signal_error = pyqtSignal(str)

    # Phase 1信号
    result_signal = pyqtSignal(dict)
    token_signal = pyqtSignal(str)  # 流式输出 (预留)
    error_signal = pyqtSignal(str)

    def __init__(self, brain, user_input, config=None, payload=None, mode="chat"):
        """
        初始化Athena对话线程 V6.1

        Args:
            brain: 实际上是Commander实例
            user_input: 用户输入
            config: 配置字典
            payload: 附加数据
            mode: 对话模式 (支持writer模式)
        """
        super().__init__()
        self.brain = brain
        self.user_input = user_input
        self.config = config or {}
        self.payload = payload
        self.mode = mode

        # TraceID
        self.task_id = str(uuid.uuid4())[:8]

        print(f"🤖 [AthenaThread-V6.1-{self.task_id}] 初始化，模式: {self.mode}")

    def run(self):
        """执行普通对话 - V6.1改进版"""
        # V6.1: 注册任务到全局队列
        db_task_id = _register_task(f"llm_{self.mode}", {
            "input_preview": self.user_input[:50],
            "mode": self.mode
        })
        _update_task_status(db_task_id, "RUNNING")

        try:
            print(f"🤖 [AthenaThread-V6.1-{self.task_id}] 启动模式: {self.mode}")

            response_content = ""

            # 🔥 核心路由逻辑 🔥
            if self.mode == "writer":
                # 调用 Writer 智能写作
                print(f"📝 [AthenaThread-V6.1] 启动智能写作模式")

                if hasattr(self.brain, 'writer') and self.brain.writer is not None:
                    self.response_ready.emit("🚀 开始智能写作，请稍候...")

                    # 调用Writer智能写作模块
                    response_content = self.brain.writer.intelligent_write(
                        topic=self.user_input,
                        strategy=self.config
                    )

                    print(f"📝 [AthenaThread-V6.1] 智能写作完成，长度: {len(response_content)}")
                else:
                    error_msg = "❌ 错误：Writer 模块未初始化"
                    print(f"⚠️ [AthenaThread-V6.1] {error_msg}")

                    # 降级方案：使用LLM进行写作
                    response_content = f"{error_msg}\n\n将使用普通LLM进行写作..."
                    if hasattr(self.brain, 'llm') and hasattr(self.brain.llm, 'chat'):
                        fallback_response = self.brain.llm.chat(
                            f"请帮我写一篇关于'{self.user_input}'的文章",
                            system_prompt="你是一个专业的写作助手。"
                        )
                        response_content += f"\n\n{fallback_response}"

            elif self.mode == "simple_chat":
                # 简单对话
                if hasattr(self.brain, 'llm') and hasattr(self.brain.llm, 'chat'):
                    response_content = self.brain.llm.chat(
                        self.user_input,
                        system_prompt="你是一个简洁的助手。",
                        options=self.config.get("options", {})
                    )
                else:
                    # 降级调用方式
                    response_content = self._fallback_chat()

            elif self.mode == "deep":
                # 深度对话模式
                print(f"🧠 [AthenaThread-V6.1] 启动深度对话模式")

                sys_prompt = self.config.get("system_prompt",
                                             "你是一个深度思考的智能助手，能够深入分析问题并提供详尽的回答。")
                if hasattr(self.brain, 'llm') and hasattr(self.brain.llm, 'chat'):
                    response_content = self.brain.llm.chat(
                        self.user_input,
                        system_prompt=sys_prompt,
                        options={
                            "temperature": 0.7,
                            "max_tokens": 2000,
                            **self.config.get("options", {})
                        }
                    )
                else:
                    response_content = self._fallback_chat()

            else:
                # 默认路由给Commander的通用处理
                sys_prompt = self.config.get("system_prompt", "你是一个智能助手。")
                if hasattr(self.brain, 'llm') and hasattr(self.brain.llm, 'chat'):
                    response_content = self.brain.llm.chat(
                        self.user_input,
                        system_prompt=sys_prompt
                    )
                else:
                    # 降级调用方式
                    response_content = self._fallback_chat()

            # 🔥 终极保险丝：确保响应是字符串
            safe_response = self._safe_convert_response(response_content)

            # 最终检查
            if not safe_response or safe_response.isspace():
                safe_response = "Athena返回了空内容，请检查配置或重试。"

            print(f"[AthenaThread-V6.1-{self.task_id}] 最终输出长度: {len(safe_response)} 字符")

            _update_task_status(db_task_id, "COMPLETED", {"length": len(safe_response)})

            # 构建标准返回格式
            result = {
                "type": "chat",
                "sender": "Athena",
                "content": safe_response,
                "mode": self.mode,
                "task_id": self.task_id
            }

            # 发射所有兼容信号
            self.result_signal.emit(result)
            self.response_ready.emit(safe_response)
            self.signal_response.emit(safe_response)

        except Exception as e:
            print(f"❌ [AthenaThread-V6.1-{self.task_id}] 致命错误: {traceback.format_exc()}")
            _update_task_status(db_task_id, "FAILED", {"error": str(e)})

            error_msg = f"普通对话失败: {str(e)}"
            # 发射所有错误信号
            self.error_signal.emit(error_msg)
            self.error_occurred.emit(error_msg)
            self.signal_error.emit(error_msg)

    def _fallback_chat(self):
        """备用调用方式 - 保持向后兼容"""
        try:
            print(f"[AthenaThread-V6.1-{self.task_id}] 使用备用调用方式")

            raw_response = None

            # 优先使用launch方法
            if hasattr(self.brain, 'launch'):
                try:
                    raw_response = self.brain.launch(user_input=self.user_input, config=self.config)
                except TypeError:
                    raw_response = self.brain.launch(self.user_input)
            elif hasattr(self.brain, 'chat'):
                raw_response = self.brain.chat(self.user_input)
            else:
                return "brain没有可用的对话方法"

            # 保险丝转换
            return self._safe_convert_response(raw_response)
        except Exception as e:
            return f"备用调用失败: {str(e)}"

    def _safe_convert_response(self, raw_response):
        """🔥 保险丝转换响应"""
        if raw_response is None:
            return "Athena没有返回内容。"
        elif isinstance(raw_response, dict):
            for field in ['content', 'text', 'response', 'answer']:
                if field in raw_response:
                    value = raw_response[field]
                    if value is not None:
                        return str(value)
            return str(raw_response)
        else:
            return str(raw_response)


# ==========================================
# 4. 批量分析线程 (BatchAnalysisWorker) - V6.1改进版
# ==========================================
class BatchAnalysisWorker(QThread):
    """
    批量文档分析线程 - V6.1改进版
    融合V6.0的停止机制和进度信号 + V6.1的统一TaskQueue
    """
    progress = pyqtSignal(int, int)  # (当前, 总数)
    detailed_progress = pyqtSignal(int, int, str)  # (当前, 总数, 文件名)
    file_finished = pyqtSignal(str, dict)  # (文件名, 结果)
    finished = pyqtSignal(list)  # 完成信号
    all_finished = pyqtSignal()  # 全部完成信号
    error = pyqtSignal(str, str)  # (文件名, 错误信息)

    # 兼容信号
    progress_phase1 = pyqtSignal(str)

    def __init__(self, analyzer, file_list=None, contents=None, filenames=None, mode="fast"):
        """
        初始化批量分析线程
        """
        super().__init__()
        self.analyzer = analyzer
        self.mode = mode
        self.is_running = True  # 停止机制
        self.task_id = str(uuid.uuid4())[:8]  # TraceID

        # 处理不同的参数格式
        if file_list is not None:
            # V6.0格式
            self.file_list = file_list
            self.use_v4_format = True
        elif contents is not None and filenames is not None:
            # V6.0另一种格式
            self.contents = contents
            self.filenames = filenames
            self.use_v4_format = False
        else:
            raise ValueError("必须提供有效的文件数据")

    def run(self):
        """执行批量分析"""
        try:
            # V6.1: 注册批量任务到全局队列
            total_files = len(self.file_list) if self.use_v4_format else len(self.contents)
            db_task_id = _register_task("batch_analysis", {
                "file_count": total_files,
                "mode": self.mode
            })
            _update_task_status(db_task_id, "RUNNING")

            if self.use_v4_format:
                # 使用V6.0的格式
                total = len(self.file_list)
                results = []

                for i, (filepath, content) in enumerate(self.file_list):
                    if not self.is_running:
                        break

                    try:
                        # 发送进度
                        self.progress.emit(i + 1, total)
                        self.detailed_progress.emit(i + 1, total, filepath)
                        self.progress_phase1.emit(f"处理文件 {i + 1}/{total}: {filepath}")

                        # 执行分析
                        result = self.analyzer.deep_analyze(content, filepath)

                        # 发送文件完成信号
                        self.file_finished.emit(filepath, result)
                        results.append(result)

                    except Exception as e:
                        error_msg = f"批量分析出错 {filepath}: {e}"
                        print(f"❌ [BatchAnalysisWorker-{self.task_id}] {error_msg}")
                        self.error.emit(filepath, str(e))

                # 发送完成信号
                self.all_finished.emit()
                self.finished.emit(results)

            else:
                # 使用V6.0的另一种格式
                results = []
                total = len(self.contents)

                for i, (content, filename) in enumerate(zip(self.contents, self.filenames), 1):
                    if not self.is_running:
                        break

                    try:
                        # 发送进度
                        self.progress.emit(i, total)
                        self.detailed_progress.emit(i, total, filename)
                        self.progress_phase1.emit(f"处理文件 {i}/{total}: {filename}")

                        # 根据模式分析
                        if self.mode == "fast" and hasattr(self.analyzer, 'fast_analyze'):
                            result = self.analyzer.fast_analyze(content, filename)
                        elif self.mode == "llm" and hasattr(self.analyzer, 'llm_analyze'):
                            result = self.analyzer.llm_analyze(content, filename)
                        else:
                            result = self.analyzer.deep_analyze(content, filename)

                        # 发送文件完成信号
                        self.file_finished.emit(filename, result)
                        results.append(result)

                    except Exception as e:
                        error_msg = f"批量分析失败 {filename}: {e}"
                        print(f"❌ [BatchAnalysisWorker-{self.task_id}] {error_msg}")
                        self.error.emit(filename, str(e))

                # 发送完成信号
                self.all_finished.emit()
                self.finished.emit(results)

            # V6.1: 更新任务状态
            _update_task_status(db_task_id, "COMPLETED", {"processed": len(results)})

        except Exception as e:
            error_msg = f"批量分析线程异常: {str(e)}"
            print(f"❌ [BatchAnalysisWorker-{self.task_id}] {error_msg}")
            traceback.print_exc()

            if 'db_task_id' in locals():
                _update_task_status(db_task_id, "FAILED", {"error": str(e)})

    def stop(self):
        """停止批量分析"""
        self.is_running = False


# ==========================================
# 5-9. 其他线程类 (保留V6.0完整实现，更新为V6.1)
# ==========================================

# 5. 文件读取线程 (FileReaderWorker) - V6.1版
class FileReaderWorker(QThread):
    """
    文件读取线程 - V6.1版
    使用统一的GLOBAL_TASK_QUEUE
    """
    # 信号
    finished = pyqtSignal(str, str)  # (file_path, content)
    progress = pyqtSignal(int, str)  # (进度百分比, 文件名)
    file_loaded = pyqtSignal(str, str, str)  # (文件名, 内容, 错误信息)
    all_finished = pyqtSignal(int)  # 读取的文件总数
    error = pyqtSignal(str)

    def __init__(self, io_manager=None, file_path=None, file_paths=None, encoding="utf-8"):
        super().__init__()
        self.io_manager = io_manager
        self.file_path = file_path
        self.file_paths = file_paths or ([] if file_path is None else [file_path])
        self.encoding = encoding
        self.task_id = str(uuid.uuid4())[:8]

    def run(self):
        """读取文件"""
        try:
            # 注册任务
            db_task_id = _register_task("file_reading", {
                "file_count": len(self.file_paths),
                "encoding": self.encoding
            })
            _update_task_status(db_task_id, "RUNNING")

            total = len(self.file_paths)
            read_count = 0

            for i, file_path in enumerate(self.file_paths, 1):
                try:
                    # 发送进度
                    progress_percent = int((i / total) * 100)
                    self.progress.emit(progress_percent, file_path)

                    # 读取文件
                    content = None

                    if self.io_manager and hasattr(self.io_manager, 'read_file'):
                        # 使用io_manager
                        content = self.io_manager.read_file(file_path)
                    else:
                        # 使用直接读取
                        with open(file_path, 'r', encoding=self.encoding, errors='ignore') as f:
                            content = f.read()

                    # 发送文件内容
                    self.finished.emit(file_path, content)
                    self.file_loaded.emit(file_path, content, "")
                    read_count += 1

                except Exception as e:
                    error_msg = f"读取失败: {str(e)}"
                    print(f"❌ [FileReaderWorker-{self.task_id}] 读取文件失败 {file_path}: {error_msg}")
                    self.error.emit(error_msg)
                    self.file_loaded.emit(file_path, "", error_msg)

            # 发送完成信号
            self.all_finished.emit(total)
            _update_task_status(db_task_id, "COMPLETED", {"read_count": read_count})

        except Exception as e:
            error_msg = f"文件读取线程异常: {str(e)}"
            print(f"❌ [FileReaderWorker-{self.task_id}] {error_msg}")
            self.error.emit(error_msg)

            if 'db_task_id' in locals():
                _update_task_status(db_task_id, "FAILED", {"error": str(e)})


# 6. 缓存清理线程 (CacheCleanerWorker) - V6.1版
class CacheCleanerWorker(QThread):
    """
    缓存清理线程 - V6.1版
    使用统一的GLOBAL_TASK_QUEUE
    """
    # 信号
    simple_finished = pyqtSignal(bool, str)  # (是否成功, 消息)
    progress = pyqtSignal(int, str)  # (进度百分比, 状态)
    finished = pyqtSignal(bool, str)  # (是否成功, 消息)

    def __init__(self, cache_dir=None, cache_manager=None):
        super().__init__()
        self.cache_dir = cache_dir
        self.cache_manager = cache_manager
        self.task_id = str(uuid.uuid4())[:8]

    def run(self):
        """执行缓存清理"""
        # 注册任务
        db_task_id = _register_task("cache_clean", {
            "cache_dir": self.cache_dir,
            "has_manager": self.cache_manager is not None
        })
        _update_task_status(db_task_id, "RUNNING")

        try:
            # 发送开始进度
            self.progress.emit(10, "开始清理缓存...")

            cleaned_count = 0

            if self.cache_manager is not None:
                # 使用cache_manager
                if hasattr(self.cache_manager, 'clean_expired'):
                    cleaned_count = self.cache_manager.clean_expired()
                    self.progress.emit(50, f"已清理 {cleaned_count} 个过期缓存")

                if hasattr(self.cache_manager, 'clean_oversized'):
                    oversized_count = self.cache_manager.clean_oversized()
                    cleaned_count += oversized_count
                    self.progress.emit(80, f"已清理 {oversized_count} 个过大缓存")

                if hasattr(self.cache_manager, 'get_stats'):
                    stats = self.cache_manager.get_stats()
                    self.progress.emit(100, "缓存清理完成")
                    msg = f"缓存清理完成。当前缓存: {stats.get('total', 0)} 个文件"
                    self.finished.emit(True, msg)
                    self.simple_finished.emit(True, msg)
                else:
                    msg = f"缓存清理完成，共清理 {cleaned_count} 个文件"
                    self.finished.emit(True, msg)
                    self.simple_finished.emit(True, msg)

            elif self.cache_dir is not None:
                # 使用直接清理
                if os.path.exists(self.cache_dir):
                    self.progress.emit(30, f"扫描缓存目录: {self.cache_dir}")

                    for filename in os.listdir(self.cache_dir):
                        file_path = os.path.join(self.cache_dir, filename)
                        try:
                            if os.path.isfile(file_path) or os.path.islink(file_path):
                                os.unlink(file_path)
                                cleaned_count += 1
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                                cleaned_count += 1
                        except Exception as e:
                            print(f"[CacheCleanerWorker-{self.task_id}] 清理失败 {file_path}: {e}")

                    self.progress.emit(100, "缓存清理完成")
                    msg = f"清理完成，共清理 {cleaned_count} 个文件/目录"
                    self.finished.emit(True, msg)
                    self.simple_finished.emit(True, msg)
                else:
                    msg = "缓存目录不存在"
                    self.finished.emit(True, msg)
                    self.simple_finished.emit(True, msg)
            else:
                error_msg = "未提供缓存目录或缓存管理器"
                self.finished.emit(False, error_msg)
                self.simple_finished.emit(False, error_msg)

            _update_task_status(db_task_id, "COMPLETED", {"cleaned_count": cleaned_count})

        except Exception as e:
            error_msg = f"缓存清理失败: {str(e)}"
            print(f"❌ [CacheCleanerWorker-{self.task_id}] {error_msg}")
            self.finished.emit(False, error_msg)
            self.simple_finished.emit(False, error_msg)

            if 'db_task_id' in locals():
                _update_task_status(db_task_id, "FAILED", {"error": str(e)})


# 7. 备用对话线程 (SimpleChatWorker) - V6.1版
class SimpleChatWorker(QThread):
    """
    极简版对话线程 - V6.1版
    使用统一的GLOBAL_TASK_QUEUE
    """
    # 信号名称
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, brain, user_input, config=None):
        super().__init__()
        self.brain = brain
        self.user_input = user_input
        self.config = config or {}
        self.task_id = str(uuid.uuid4())[:8]

    def run(self):
        """执行简单对话"""
        # 注册任务
        db_task_id = _register_task("simple_chat", {
            "input_preview": self.user_input[:50]
        })
        _update_task_status(db_task_id, "RUNNING")

        try:
            print(f"[SimpleChatWorker-{self.task_id}] 处理用户输入: {self.user_input[:50]}...")

            raw_response = None

            # 防御性调用
            if hasattr(self.brain, 'chat'):
                raw_response = self.brain.chat(self.user_input)
            elif hasattr(self.brain, 'launch'):
                try:
                    raw_response = self.brain.launch(user_input=self.user_input, config=self.config)
                except TypeError:
                    raw_response = self.brain.launch(self.user_input)
            else:
                error_msg = "brain没有可用的对话方法 (chat 或 launch)"
                print(f"[SimpleChatWorker-{self.task_id}] {error_msg}")
                _update_task_status(db_task_id, "FAILED", {"error": error_msg})
                self.error_occurred.emit(error_msg)
                self.error.emit(error_msg)
                return

            # 清洗（确保绝对是字符串）
            safe_response = ""
            if raw_response is None:
                safe_response = "..."
            elif isinstance(raw_response, dict):
                safe_response = raw_response.get('content', str(raw_response))
            else:
                safe_response = str(raw_response)

            # 发射信号
            self.response_ready.emit(safe_response)
            self.finished.emit(safe_response)
            _update_task_status(db_task_id, "COMPLETED", {"length": len(safe_response)})

        except Exception as e:
            error_msg = f"简单对话失败: {str(e)}"
            print(f"[SimpleChatWorker-{self.task_id}] {error_msg}")
            traceback.print_exc()
            _update_task_status(db_task_id, "FAILED", {"error": str(e)})
            self.error_occurred.emit(error_msg)
            self.error.emit(error_msg)


# 8. 文件处理线程 (FileProcessorWorker) - V6.1版
class FileProcessorWorker(QThread):
    """
    通用文件处理线程 - V6.1版
    使用统一的GLOBAL_TASK_QUEUE
    """
    # 信号
    simple_progress = pyqtSignal(int, str)  # (进度百分比, 状态)
    file_processed = pyqtSignal(str, object, str)  # (文件名, 数据, 错误信息)
    simple_finished = pyqtSignal(int)  # 处理完成的数量
    progress = pyqtSignal(int, str)  # (进度百分比, 状态)
    finished = pyqtSignal(int)  # 处理完成的数量

    def __init__(self, processor_func, file_paths, **kwargs):
        super().__init__()
        self.processor_func = processor_func
        self.file_paths = file_paths
        self.kwargs = kwargs
        self.task_id = str(uuid.uuid4())[:8]

    def run(self):
        """处理所有文件"""
        # 注册任务
        db_task_id = _register_task("file_processing", {
            "file_count": len(self.file_paths),
            "processor": self.processor_func.__name__ if hasattr(self.processor_func, '__name__') else "unknown"
        })
        _update_task_status(db_task_id, "RUNNING")

        processed_count = 0
        total = len(self.file_paths)

        for i, file_path in enumerate(self.file_paths, 1):
            try:
                # 发送进度
                progress_percent = int((i / total) * 100)
                self.progress.emit(progress_percent, f"处理: {file_path}")
                self.simple_progress.emit(progress_percent, f"处理: {file_path}")

                # 处理文件
                result = self.processor_func(file_path, **self.kwargs)
                self.file_processed.emit(file_path, result, "")
                processed_count += 1

            except Exception as e:
                error_msg = f"处理失败: {str(e)}"
                print(f"❌ [FileProcessorWorker-{self.task_id}] 处理文件失败 {file_path}: {error_msg}")
                self.file_processed.emit(file_path, None, error_msg)

        # 发送完成信号
        self.finished.emit(processed_count)
        self.simple_finished.emit(processed_count)
        _update_task_status(db_task_id, "COMPLETED", {"processed_count": processed_count})


# ==========================================
# 9. 稳定版Athena线程 (StableAthenaThread) - V6.1增强版
# ==========================================
class StableAthenaThread(QThread):
    """
    稳定版Athena线程 - V6.1增强版
    专门为Commander架构设计，支持Writer模式
    使用统一的GLOBAL_TASK_QUEUE
    """
    result_signal = pyqtSignal(dict)  # 返回完整结果
    token_signal = pyqtSignal(str)  # 流式输出 (预留)
    error_signal = pyqtSignal(str)

    # 兼容性信号
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, brain, user_input, config=None, payload=None, mode="chat"):
        super().__init__()
        self.brain = brain  # 这里传入的其实是Commander
        self.user_input = user_input
        self.config = config or {}
        self.payload = payload
        self.mode = mode
        self.task_id = str(uuid.uuid4())[:8]

    def run(self):
        # 注册任务
        db_task_id = _register_task(f"llm_{self.mode}", {
            "input_preview": self.user_input[:50],
            "mode": self.mode
        })
        _update_task_status(db_task_id, "RUNNING")

        try:
            print(f"🤖 [StableAthenaThread-V6.1-{self.task_id}] 启动模式: {self.mode}")

            response_content = ""

            # 🔥 V6.1增强：支持Writer模式 🔥
            if self.mode == "writer":
                # 调用Writer智能写作
                print(f"📝 [StableAthenaThread-V6.1] 启动智能写作模式")

                if hasattr(self.brain, 'writer') and self.brain.writer is not None:
                    # 发送开始信号
                    self.response_ready.emit("🚀 开始智能写作，请稍候...")

                    # 调用Writer模块
                    response_content = self.brain.writer.intelligent_write(
                        topic=self.user_input,
                        strategy=self.config
                    )

                    print(f"📝 [StableAthenaThread-V6.1] 智能写作完成，长度: {len(response_content)}")
                else:
                    error_msg = "❌ 错误：Writer 模块未初始化"
                    print(f"⚠️ [StableAthenaThread-V6.1] {error_msg}")
                    response_content = error_msg

            elif self.mode == "simple_chat":
                # 简单对话
                if hasattr(self.brain, 'llm') and hasattr(self.brain.llm, 'chat'):
                    response_content = self.brain.llm.chat(
                        self.user_input,
                        system_prompt="你是一个有用的助手。",
                        options=self.config.get("options", {})
                    )
                else:
                    response_content = "LLM模块不可用"

            else:
                # 默认路由
                sys_prompt = self.config.get("system_prompt", "你是一个智能助手。")
                if hasattr(self.brain, 'llm') and hasattr(self.brain.llm, 'chat'):
                    response_content = self.brain.llm.chat(
                        self.user_input,
                        system_prompt=sys_prompt
                    )
                else:
                    response_content = "LLM模块不可用"

            # 🔥 保险丝：确保响应是字符串
            if response_content is None:
                response_content = "Athena没有返回内容。"
            elif not isinstance(response_content, str):
                response_content = str(response_content)

            _update_task_status(db_task_id, "COMPLETED", {"length": len(response_content)})

            # 构建标准返回格式
            result = {
                "type": "chat",
                "sender": "Athena",
                "content": response_content,
                "mode": self.mode,
                "task_id": self.task_id
            }

            # 发射所有信号
            self.result_signal.emit(result)
            self.response_ready.emit(response_content)

        except Exception as e:
            print(f"❌ [StableAthenaThread-V6.1-{self.task_id}] 致命错误: {traceback.format_exc()}")
            _update_task_status(db_task_id, "FAILED", {"error": str(e)})

            error_msg = f"StableAthenaThread错误: {str(e)}"
            self.error_signal.emit(error_msg)
            self.error_occurred.emit(error_msg)


# ==========================================
# 10. 智能兼容性包装器 (V6.1增强版)
# ==========================================
def create_worker(worker_type, *args, **kwargs):
    """
    智能创建Worker的兼容性函数 - V6.1增强版
    根据参数自动选择合适的Worker类，支持Writer模式
    使用统一的GLOBAL_TASK_QUEUE
    """
    print(f"[create_worker-V6.1] 创建 {worker_type} Worker, 参数: {kwargs.get('mode', 'default')}")

    # 🔥 支持writer模式的路由 🔥
    if worker_type == "analysis":
        return AnalysisWorker(*args, **kwargs)
    elif worker_type == "deep_thinking":
        return DeepThinkingWorker(*args, **kwargs)
    elif worker_type == "chat" or worker_type == "athena":
        # 根据mode参数选择使用哪个版本的Athena线程
        mode = kwargs.get("mode", "chat")

        if mode == "writer":
            print(f"[create_worker-V6.1] Writer模式，使用AthenaThread")
            return AthenaThread(*args, **kwargs)
        elif mode in ["simple_chat", "writer"]:
            # 使用Phase 1专用线程（增强版）
            return StableAthenaThread(*args, **kwargs)
        else:
            # 使用兼容线程（支持Phase 2）
            return AthenaThread(*args, **kwargs)
    elif worker_type == "stable_athena":
        # 显式指定使用稳定版
        return StableAthenaThread(*args, **kwargs)
    elif worker_type == "batch_analysis":
        return BatchAnalysisWorker(*args, **kwargs)
    elif worker_type == "file_reader":
        return FileReaderWorker(*args, **kwargs)
    elif worker_type == "cache_cleaner":
        return CacheCleanerWorker(*args, **kwargs)
    elif worker_type == "simple_chat":
        return SimpleChatWorker(*args, **kwargs)
    elif worker_type == "file_processor":
        return FileProcessorWorker(*args, **kwargs)
    else:
        raise ValueError(f"未知的Worker类型: {worker_type}")


# ==========================================
# 11. 导出所有Worker类
# ==========================================
__all__ = [
    # 核心线程
    'AnalysisWorker',
    'DeepThinkingWorker',
    'AthenaThread',
    'StableAthenaThread',

    # 辅助线程
    'BatchAnalysisWorker',
    'FileReaderWorker',
    'CacheCleanerWorker',
    'SimpleChatWorker',
    'FileProcessorWorker',

    # 工具函数
    'create_worker',

    # 常量
    'GLOBAL_TASK_QUEUE',
    '_register_task',
    '_update_task_status'
]

print("🔥🔥🔥 WORKERS.PY V6.1 加载完成，所有线程类已就绪 🔥🔥🔥")
print("✅ 保留V6.0所有功能 + 集成V6.1统一TaskQueue改进")
print("✅ 支持Writer智能写作 + 增强路由逻辑 + 完全向后兼容")
print("🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥")