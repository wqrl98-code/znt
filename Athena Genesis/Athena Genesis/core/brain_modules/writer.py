# -*- coding: utf-8 -*-
"""
首席执笔人 - 负责根据知识库和人物生成初稿
职责：长文生成、续写、全域深度熔炉、金字塔写作、深度研报模式、智能写作
"""
import os
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from config.genres import get_genre_config
from PyQt6.QtCore import QObject, pyqtSignal


class Writer(QObject):
    """首席执笔人 - 文本生成专家"""

    # PyQt6 信号
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(str)

    def __init__(self, bus, llm, mimicry, io_manager, knowledge_base):
        super().__init__()
        self.bus = bus
        self.llm = llm
        self.mimicry = mimicry
        self.io_manager = io_manager
        self.knowledge_base = knowledge_base

        # 续写缓存
        self.last_generation_tail = ""
        self.last_system_role = ""

        # 全域熔炉上下文
        self.last_global_furnace_context = None

        # 并发配置
        self.MAX_IO_WORKERS = 8
        self.MAX_LLM_WORKERS = 5

    def _emit_log(self, message):
        """统一日志发射方法"""
        self.bus.emit_log(message)
        self.log_signal.emit(message)

    def handle_continuation(self, tail, system_role):
        """
        处理续写请求
        """
        self._emit_log("⚡ [执笔人] 识别到续写指令，启动轻量级续写模式...")

        prompt = f"""
        你现在的身份是：{system_role}

        【上文背景】：
        ...（前文省略）...
        {tail}

        【用户指令】：
        请紧接上文，继续撰写未完成的内容。

        【要求】：
        1. 逻辑严丝合缝，不要重复上文最后一句。
        2. 如果上文是在半句话断开的，请补全它。
        3. 保持原有文风。
        4. 输出字数约800-1000字。
        """

        try:
            continuation = self.llm.chat(prompt, options={"temperature": 0.6})

            # 更新尾巴
            self.last_generation_tail = continuation[-1000:] if len(continuation) > 1000 else continuation

            # 添加交互式引导
            interactive_footer = (
                "\n\n"
                "---"
                "\n> **⚠️ 系统监测**：如果上述内容未显示完整，或者您希望继续扩写：请直接回复"
                "\n>  继续,是我将无缝接续生成。"
            )

            return str(continuation + interactive_footer)
        except Exception as e:
            return f"❌ 续写失败: {str(e)}"

    def intelligent_write(self, topic: str, strategy: dict) -> str:
        """
        智能写作主入口
        :param topic: 写作主题/用户输入
        :param strategy: 策略配置 (audience, tone, genre, etc.)
        :return: 最终文章内容
        """
        self._emit_log(f"✍️ [执笔人] 收到任务：{topic[:20]}... | 策略：{strategy}")

        # 1. 获取风格 DNA (如果有)
        style_instruction = ""
        if hasattr(self.mimicry, 'get_style_instruction'):
            style_instruction = self.mimicry.get_style_instruction()
            if style_instruction:
                self._emit_log("🧬 [拟态] 已注入风格 DNA")

        # 2. 构建系统提示词 (System Prompt)
        genre = strategy.get('genre', '通用')
        audience = strategy.get('audience', '通用读者')
        tone = strategy.get('tone', '客观')

        system_prompt = f"""
你是一位专业的写作专家。
【目标受众】：{audience}
【语调风格】：{tone}
【文章类型】：{genre}

{style_instruction}

请严格遵守上述风格要求。
"""

        # 3. 第一步：生成大纲 (Outline)
        self.progress_signal.emit("正在构建大纲...")
        outline_prompt = f"""
请为主题"{topic}"设计一份详细的写作大纲。
要求：
1. 结构清晰，逻辑递进。
2. 列出核心观点和支撑论据。
3. 不需要写正文，只需要大纲。
"""
        outline = self.llm.chat(outline_prompt, system_prompt=system_prompt)
        self._emit_log(f"📝 大纲已生成 ({len(outline)}字)")

        # 4. 第二步：基于大纲生成全文 (Full Text)
        self.progress_signal.emit("正在根据大纲撰写正文...")
        write_prompt = f"""
请根据以下大纲，撰写一篇完整的文章。
【主题】：{topic}

【大纲】：
{outline}

【要求】：
1. 内容充实，细节丰富。
2. 严格遵循大纲结构。
3. 保持设定的人格和语调。
"""
        # 这里的 timeout 可以设置得更长，由 LLMEngine 内部控制
        article = self.llm.chat(write_prompt, system_prompt=system_prompt)

        self._emit_log("✅ 写作任务完成")
        return article

    def create_outline(self, query, context="", genre_config=None):
        """
        深度研报模式专用：构建内容大纲

        Args:
            query: 主题
            context: 学习到的知识
            genre_config: 文体配置
        Returns:
            大纲文本
        """
        self._emit_log("📋 [执笔人] 构建深度大纲...")

        if genre_config is None:
            genre_config = get_genre_config("通用/默认")

        system_role = genre_config.get("system_prompt", "专业作者")
        structure_guide = genre_config.get("structure_guide", "")

        prompt = f"""
        身份：{system_role}
        用户要求：{query}
        可用素材：{context[:5000] if context else "暂无"}
        结构指南：{structure_guide}

        请构建一个深度大纲，包含：
        1. 前言/引言（核心问题与价值）
        2. 理论框架（核心概念与原理）
        3. 现状分析（当前状况与挑战）
        4. 案例分析（具体实例与数据）
        5. 对策建议（可行方案与步骤）
        6. 结论展望（总结与未来方向）

        请输出详细的大纲，包含每个部分的关键点。
        """

        try:
            outline = self.llm.chat(prompt, options={"temperature": 0.4, "num_ctx": 8000})
            return outline
        except Exception as e:
            self._emit_log(f"❌ 大纲构建失败: {e}")
            return f"# {query} 大纲\n\n1. 引言\n2. 主体\n3. 结论"

    def write_with_context(self, query, outline, context="", temperature=0.7):
        """
        深度研报模式专用：基于大纲和上下文撰写内容

        Args:
            query: 主题
            outline: 大纲
            context: 学习到的知识
            temperature: 温度参数
        Returns:
            完整文章
        """
        self._emit_log("✍️ [执笔人] 基于大纲撰写深度内容...")

        # 分章节撰写
        chapters = []

        # 1. 引言部分
        intro_prompt = f"""
        基于以下大纲和素材，撰写引言部分：

        【主题】：{query}
        【大纲】：{outline}
        【可用素材】：{context[:3000] if context else "暂无"}

        要求：
        1. 吸引读者注意力
        2. 阐明问题重要性
        3. 提出核心观点
        4. 字数约300-500字
        """

        try:
            introduction = self.llm.chat(intro_prompt, options={"temperature": temperature, "num_predict": 800})
            chapters.append(f"# 引言\n\n{introduction}")

            # 2. 主体部分（分段落）
            # 这里可以更精细地拆分大纲，为了简化，我们一次性撰写主体
            body_prompt = f"""
            接续以下引言，撰写文章主体部分：

            【引言】：{introduction[-200:]}
            【完整大纲】：{outline}
            【可用素材】：{context[:5000] if context else "暂无"}

            要求：
            1. 严格遵循大纲结构
            2. 充分使用素材中的数据和案例
            3. 逻辑严谨，论证充分
            4. 字数约1500-2000字
            """

            body = self.llm.chat(body_prompt, options={"temperature": temperature, "num_predict": 2500})
            chapters.append(f"# 主体\n\n{body}")

            # 3. 结论部分
            conclusion_prompt = f"""
            基于以下文章主体，撰写结论部分：

            【主题】：{query}
            【文章主体】：{body[-500:]}

            要求：
            1. 总结全文核心观点
            2. 提出有价值的启示
            3. 展望未来发展
            4. 字数约300-500字
            """

            conclusion = self.llm.chat(conclusion_prompt, options={"temperature": temperature, "num_predict": 800})
            chapters.append(f"# 结论\n\n{conclusion}")

            # 组合全文
            full_text = "\n\n".join(chapters)

            # 保存尾巴供续写
            self.last_generation_tail = full_text[-1500:]
            self.last_system_role = "深度研报作者"

            return full_text

        except Exception as e:
            self._emit_log(f"❌ 内容撰写失败: {e}")
            return f"内容生成失败: {str(e)}"

    def global_deep_furnace(self, query, config=None, file_paths=None, callback=None):
        """
        全域深度熔炉 - 全量阅读+事实提取+大纲构建+分章撰写
        """
        config = config or {}

        # 获取文件路径
        if not file_paths:
            file_paths = self._get_input_files()

        if not file_paths:
            return "❌ 未找到任何可处理的文件，请先导入文档。"

        # 获取文体配置
        genre_name = config.get("genre", "通用/默认")
        genre_cfg = get_genre_config(genre_name)
        system_role = genre_cfg["system_prompt"]
        structure_guide = genre_cfg["structure_guide"]

        # 保存 Role 供续写使用
        self.last_system_role = system_role

        # 阶段一：多线程并发读取与提取
        self._emit_log(f"🔥 [全域熔炉] 启动，处理 {len(file_paths)} 个文件...")

        # 从文件中提取事实
        from .researcher import Researcher
        researcher = Researcher(
            bus=self.bus,
            llm=self.llm,
            mimicry=self.mimicry,
            analyzer=None,
            io_manager=self.io_manager,
            knowledge_base=self.knowledge_base
        )

        global_facts_pool = researcher.extract_facts_from_files(file_paths, query)

        # 阶段二：全域大纲构建
        all_facts_str = "\n".join(global_facts_pool)[:25000]

        outline_prompt = f"""
        身份：{system_role}
        用户要求：{query}
        素材库：{all_facts_str}

        请构建【{genre_name}】深度大纲。
        结构指南：{structure_guide}
        """

        outline = self.llm.chat(outline_prompt, options={"temperature": 0.4, "num_ctx": 8000})

        # 保存上下文
        self.last_global_furnace_context = {
            "query": query,
            "all_facts_str": all_facts_str,
            "outline": outline,
            "genre_name": genre_name,
            "system_role": system_role,
            "structure_guide": structure_guide
        }

        # 阶段三：分章深度撰写
        final_parts = [f"# {query}\n\n"]

        # Part 1: 开篇
        p1_prompt = f"身份：{system_role}\n大纲：{outline}\n基于素材写第一部分(前言)。字数1000。"
        p1 = self.llm.chat(p1_prompt, options={"temperature": 0.6, "num_ctx": 12000})
        final_parts.append(p1)
        self.last_generation_tail = p1[-1500:]

        # Part 2: 核心论述
        p2_prompt = f"身份：{system_role}\n接上文：{p1[-500:]}\n写中间核心部分。字数1500。"
        p2 = self.llm.chat(p2_prompt, options={"temperature": 0.6, "num_ctx": 12000})
        final_parts.append(p2)
        self.last_generation_tail = p2[-1500:]

        # Part 3: 具体举措
        p3_prompt = f"身份：{system_role}\n接上文：{p2[-500:]}\n写具体的举措/任务/对策部分。字数1500。"
        p3 = self.llm.chat(p3_prompt, options={"temperature": 0.6, "num_ctx": 12000})
        final_parts.append(p3)
        self.last_generation_tail = p3[-1500:]

        # Part 4: 结尾
        p4_prompt = f"身份：{system_role}\n接上文：{p3[-500:]}\n写结语。字数800。"
        p4 = self.llm.chat(p4_prompt, options={"temperature": 0.7, "num_ctx": 12000})
        final_parts.append(p4)
        self.last_generation_tail = p4[-1500:]

        full_text = "\n\n".join(final_parts)

        # 质量检查和润色
        polish_prompt = f"""
        你现在的身份是：{system_role}

        请对以下文章进行最终润色和检查：

        {full_text}

        检查要点：
        1. 逻辑连贯性
        2. 事实准确性
        3. 语言流畅度
        4. 结构完整性
        5. 是否符合【{genre_name}】的文体要求

        请输出润色后的完整文章。
        """

        try:
            polished = self.llm.chat(polish_prompt, options={"temperature": 0.4, "num_ctx": 16000})
            return polished
        except Exception as e:
            self._emit_log(f"⚠️ 润色失败，返回原始内容: {e}")
            return full_text

    def global_report(self, query, config=None):
        """
        长文生成引擎
        """
        config = config or {}
        user_temp = config.get("temperature", 0.7)

        # 获取资料库引用信息
        file_list = []
        if hasattr(self.knowledge_base, 'get_all_docs'):
            file_list = self.knowledge_base.get_all_docs()
        elif hasattr(self.knowledge_base, 'data'):
            file_list = list(self.knowledge_base.data.get("documents", {}).keys())

        file_list_str = ", ".join(file_list) if file_list else "用户上传的资料库"

        # 第一步：生成大纲
        outline_prompt = f"""
        你是一位严谨的政策研究员。用户要求：{query}

        现有资料库：[{file_list_str}]

        请列出一个深度大纲。
        ⚠️ 核心要求：
        1. **必须基于资料库内容**：不要编造。
        2. **标注来源**：在每个章节标题后，用括号标注该章节主要参考了哪个文件。
        3. 包含主标题、副标题。
        4. 规划 4-5 个核心章节。
        5. 每个章节下列出 3 个关键点。
        """

        outline = self.llm.chat(outline_prompt, options={"temperature": 0.5})

        # 第二步：分章撰写
        full_article = [f"# 📝 {query} (生成的草稿)\n\n"]

        # 第一章
        part1_prompt = f"""
        基于以下大纲：
        {outline}

        请**只撰写第一章和前言**的内容。

        ⚠️ 要求：
        1. 风格：{self.mimicry.generate_system_prompt()}
        2. 字数：约 1000 字。
        3. 不要写后面的章节。
        4. **必须引用资料库中的内容**。
        """
        part1 = self.llm.chat(part1_prompt, options={"temperature": user_temp, "num_predict": 2000})
        full_article.append(part1)

        # 中间章节
        part2_prompt = f"""
        上文已写：
        {part1[-500:]}

        请接着**撰写中间的核心章节** (第二、三章)。

        ⚠️ 严厉的指令：
        1. 逻辑衔接紧密，不要重复上文的话。
        2. 引用具体案例和数据，尽可能引用资料中的原话。
        3. 字数：约 1500 字。
        """
        part2 = self.llm.chat(part2_prompt, options={"temperature": user_temp, "num_predict": 3000})
        full_article.append(part2)

        # 结尾章节
        part3_prompt = f"""
        上文已写：
        {part2[-500:]}

        请**撰写最后一章和结语**。

        ⚠️ 要求：
        1. 升华主题，要有高度。
        2. 字数：约 800 字。
        3. 总结全文，呼应开头。
        """
        part3 = self.llm.chat(part3_prompt, options={"temperature": user_temp, "num_predict": 2000})
        full_article.append(part3)

        full_text = "\n\n".join(full_article)

        # 缓存尾巴
        self.last_generation_tail = full_text[-1000:]
        self.last_system_role = "严谨的政策研究员"

        # 添加交互式引导
        interactive_footer = (
            "\n\n"
            "---"
            "\n> **⚠️ 系统监测**：如果上述内容未显示完整，或者您希望继续扩写：请直接回复"
            "\n>  继续,是我将无缝接续生成。"
        )

        return full_text + interactive_footer

    def mimicry_write(self, topic, config=None):
        """
        拟态生成
        """
        config = config or {}
        prompt = self.mimicry.generate_system_prompt()
        user_prompt = f"请以该角色的口吻，针对以下主题发表一段深刻见解：\n主题：{topic}"
        return self.llm.chat(user_prompt, prompt)

    def pyramid_write(self, user_input, config=None):
        """
        金字塔写作引擎
        """
        config = config or {}
        audience = config.get("audience", "通用读者")
        goal = config.get("goal", "传递核心价值")
        user_temp = config.get("temperature", 0.7)

        # 获取资料库引用信息
        file_list = []
        if hasattr(self.knowledge_base, 'get_all_docs'):
            file_list = self.knowledge_base.get_all_docs()
        elif hasattr(self.knowledge_base, 'data'):
            file_list = list(self.knowledge_base.data.get("documents", {}).keys())

        file_list_str = ", ".join(file_list) if file_list else "用户上传的资料库"

        # 第一层：骨架清晰
        structure_prompt = f"""
        你是一位顶级编辑。用户想写：{user_input}

        【策略设定】
        - 读者画像：{audience}
        - 核心目标：{goal}

        【可用资料库】
        {file_list_str}

        请设计一个**"动态逻辑框架"**：
        1. **核心观点**：用一句话说清全文到底要表达什么。
        2. **开头**：设计一个"钩子"。
        3. **主体**：设计 3-4 个逻辑层级。
        4. **结尾**：提供"行动号召"或"意想不到的洞见"。
        """

        blueprint = self.llm.chat(structure_prompt, options={"temperature": 0.6})

        # 第二层：血肉丰满
        draft_content = []

        # 撰写开头
        intro_prompt = f"""
        基于此设计图：
        {blueprint}

        请撰写**开头部分**。
        【表达要求】
        - **拒绝模糊**：具体化。
        - **建立共识**：快速告诉读者"我知道你的烦恼"。
        - **引用资料**：基于资料库 [{file_list_str}] 中的事实和数据。
        """
        intro = self.llm.chat(intro_prompt, options={"temperature": user_temp})
        draft_content.append(intro)

        # 撰写主体
        body_prompt = f"""
        基于设计图：{blueprint}

        上文开头已写：{intro[-300:]}

        请撰写**文章主体**。
        【高密度要求】
        - **信息密度**：关键处必须有扎实的案例、数据或细节。
        - **呼吸感**：在转折处适当留白，长短句交替。
        - **具体化**：避免抽象表述。
        - **严格引用**：基于资料库 [{file_list_str}]，禁止编造。
        """
        body = self.llm.chat(body_prompt, options={"temperature": user_temp, "num_predict": 3000})
        draft_content.append(body)

        # 撰写结尾
        outro_prompt = f"""
        上文主体结束于：{body[-300:]}

        请撰写**结尾**。
        【升华要求】
        - **超越预期**：提供一个触动人心的金句。
        - **行动号召**：给出下一步的具体建议。
        - **总结升华**：呼应开头，强化核心观点。
        """
        outro = self.llm.chat(outro_prompt, options={"temperature": user_temp})
        draft_content.append(outro)

        full_draft = "\n\n".join(draft_content)

        # 第三层：匠心打磨
        editor_prompt = f"""
        你是一位极其挑剔的主编。这是刚写好的初稿：

        {full_draft}

        请对照以下**【好稿子核对清单】**进行润色和修剪：
        1. **简洁**：删除一切与"{goal}"无关的废话。
        2. **真诚**：去掉故弄玄虚和夸大其词。
        3. **节奏**：大声朗读（模拟），修改拗口的地方。
        4. **价值**：读者能在3秒内明白此文价值吗？
        5. **引用验证**：检查所有引用是否准确。

        请输出**最终定稿**。
        """

        final_article = self.llm.chat(editor_prompt, options={"temperature": 0.4, "num_ctx": 12000})

        # 缓存尾巴
        self.last_generation_tail = final_article[-1000:]
        self.last_system_role = "顶级编辑/主编"

        return final_article

    def _get_input_files(self):
        """获取输入文件夹中的所有文件"""
        file_paths = []
        if hasattr(self.io_manager, 'paths'):
            inputs_dir = self.io_manager.paths.directories.get('inputs')
            if inputs_dir and os.path.exists(inputs_dir):
                file_paths = [os.path.join(inputs_dir, f) for f in os.listdir(inputs_dir)
                              if not f.startswith("~$") and os.path.isfile(os.path.join(inputs_dir, f))]
        return file_paths

    # 提供统一的写作接口，支持多种模式
    def write(self, topic: str, mode: str = "intelligent", **kwargs) -> str:
        """
        统一写作接口

        Args:
            topic: 写作主题
            mode: 写作模式
                - "intelligent": 智能写作（默认）
                - "continuation": 续写
                - "global_furnace": 全域深度熔炉
                - "global_report": 长文生成
                - "mimicry": 拟态生成
                - "pyramid": 金字塔写作
                - "deep_research": 深度研报
            **kwargs: 其他参数

        Returns:
            生成的文本
        """
        if mode == "intelligent":
            strategy = kwargs.get("strategy", {})
            return self.intelligent_write(topic, strategy)
        elif mode == "continuation":
            tail = kwargs.get("tail", self.last_generation_tail)
            role = kwargs.get("role", self.last_system_role)
            return self.handle_continuation(tail, role)
        elif mode == "global_furnace":
            config = kwargs.get("config", {})
            file_paths = kwargs.get("file_paths", None)
            return self.global_deep_furnace(topic, config, file_paths)
        elif mode == "global_report":
            config = kwargs.get("config", {})
            return self.global_report(topic, config)
        elif mode == "mimicry":
            config = kwargs.get("config", {})
            return self.mimicry_write(topic, config)
        elif mode == "pyramid":
            config = kwargs.get("config", {})
            return self.pyramid_write(topic, config)
        elif mode == "deep_research":
            context = kwargs.get("context", "")
            genre_config = kwargs.get("genre_config", None)
            outline = self.create_outline(topic, context, genre_config)
            temperature = kwargs.get("temperature", 0.7)
            return self.write_with_context(topic, outline, context, temperature)
        else:
            self._emit_log(f"⚠️ 未知写作模式: {mode}，使用智能写作模式")
            strategy = kwargs.get("strategy", {})
            return self.intelligent_write(topic, strategy)