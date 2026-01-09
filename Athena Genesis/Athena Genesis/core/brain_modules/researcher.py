# -*- coding: utf-8 -*-
"""
互联学习专员 - 本地知识检索 + 联网深度学习
模块特点：主动学习、知识缺口分析、智能搜索
"""
import os
import re
import time
import json
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime

# 尝试导入 WebSearcher (兼容性处理)
try:
    from core.web_searcher import WebSearcher
    WEB_SEARCHER_AVAILABLE = True
except ImportError:
    try:
        from engines.web_searcher import WebSearcher
        WEB_SEARCHER_AVAILABLE = True
    except ImportError:
        WebSearcher = None
        WEB_SEARCHER_AVAILABLE = False


class Researcher(QObject):
    """互联学习专员 - 知识检索与主动学习"""

    # 信号定义
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    search_complete = pyqtSignal(dict)

    def __init__(self, bus, llm, mimicry, analyzer, io_manager, knowledge_base):
        super().__init__()
        self.bus = bus
        self.llm = llm
        self.mimicry = mimicry
        self.analyzer = analyzer
        self.io_manager = io_manager
        self.kb = knowledge_base

        # 联网搜索器（如果可用） - 使用统一接口
        self.web_engine = None
        if WEB_SEARCHER_AVAILABLE:
            try:
                self.web_engine = WebSearcher(io_manager)
                self.log_signal.emit("✅ [Researcher] 联网搜索引擎已挂载")
            except Exception as e:
                self.log_signal.emit(f"⚠️ [Researcher] 搜索引擎初始化失败: {e}")
        else:
            self.log_signal.emit("⚠️ [Researcher] 未找到 WebSearcher 模块，联网功能受限")

        # 学习历史
        self.learning_history = []
        self.max_history = 50

        # 并发配置
        self.executor = ThreadPoolExecutor(max_workers=3)

        # 知识缺口库
        self.gap_knowledge_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data', 'knowledge_gaps.json'
        )

    def retrieve_knowledge(self, query, current_persona="默认空间", top_k=3):
        """
        增强版知识检索 - RAG + 主动学习

        Args:
            query: 查询文本
            current_persona: 当前人格空间
            top_k: 返回结果数量
        Returns:
            RAG上下文字符串
        """
        self.status_signal.emit(f"🔍 检索知识: {query[:30]}...")

        try:
            # 1. 本地知识库检索
            local_results = self._search_local(query, top_k)

            # 2. 如果本地结果不足，且允许联网，则尝试联网补充
            if self._needs_web_supplement(local_results, query):
                self.log_signal.emit("🌐 本地知识不足，启动联网补充...")

                # 异步联网搜索
                web_context = self._search_web_async(query)
                if web_context:
                    return f"【本地知识】\n{local_results}\n\n【联网补充】\n{web_context}"

            # 3. 返回本地结果
            if local_results and "未找到" not in local_results:
                return f"【关联记忆检索 ({current_persona})】\n{local_results}"

            return None

        except Exception as e:
            self.log_signal.emit(f"❌ 知识检索失败: {str(e)}")
            return None

    def _search_local(self, query, top_k):
        """本地知识库搜索"""
        try:
            if hasattr(self.kb, 'search'):
                result = self.kb.search(query, top_k=top_k)
                return result if result and len(result) > 10 else "未找到相关内容"
            else:
                # 备用搜索方案
                return self._fallback_local_search(query)
        except Exception as e:
            return f"搜索异常: {str(e)}"

    def _needs_web_supplement(self, local_results, query):
        """判断是否需要联网补充"""
        if not self.web_engine:
            return False

        # 规则：如果本地结果太短或者包含特定关键词
        short_result = local_results and len(local_results) < 200
        has_web_keywords = any(word in query for word in ["最新", "2024", "趋势", "新闻", "联网"])

        return short_result or has_web_keywords

    def _search_web_async(self, query):
        """异步联网搜索"""
        if not self.web_engine:
            return None

        try:
            # 提取搜索关键词
            keywords = self._extract_search_keywords(query)

            # 执行搜索
            results = []
            for kw in keywords[:2]:  # 最多搜索2个关键词
                self.log_signal.emit(f"🌍 正在搜索: {kw}")

                try:
                    # 使用WebSearcher的search方法
                    if hasattr(self.web_engine, 'search'):
                        search_result = self.web_engine.search(kw, max_results=3)
                        # 格式化结果
                        formatted_result = self._format_web_results(search_result)
                        if formatted_result:
                            results.append(f"【{kw}】:\n{formatted_result[:500]}")
                    time.sleep(0.5)  # 礼貌延时
                except Exception as e:
                    self.log_signal.emit(f"⚠️ 搜索 '{kw}' 失败: {e}")

            return "\n\n".join(results) if results else None

        except Exception as e:
            self.log_signal.emit(f"❌ 联网搜索异常: {e}")
            return None

    def _format_web_results(self, results):
        """格式化搜索结果"""
        if isinstance(results, str):
            return results
        if not isinstance(results, list):
            return ""

        text = ""
        for i, res in enumerate(results):
            if isinstance(res, dict):
                title = res.get('title', '无标题')
                body = res.get('body', res.get('snippet', res.get('content', '')))
                link = res.get('href', res.get('link', ''))
                text += f"[{i+1}] {title}\n摘要: {body}\n来源: {link}\n\n"
            elif isinstance(res, str):
                text += f"[{i+1}] {res}\n"
        return text

    def _extract_search_keywords(self, query):
        """从查询中提取搜索关键词"""
        prompt = f"""
        请从以下问题中提取2-3个核心搜索关键词：

        问题：{query}

        要求：
        1. 去掉疑问词（什么、如何、为什么等）
        2. 提取核心名词和动词
        3. 按重要性排序
        4. 每个关键词不超过4个字

        格式：关键词1, 关键词2, 关键词3
        """

        try:
            response = self.llm.chat(prompt, options={"temperature": 0.1})
            keywords = [kw.strip() for kw in response.split(',') if kw.strip()]
            return keywords[:3] if keywords else [query[:10]]
        except:
            # 备用方案：简单分词
            try:
                import jieba
                words = jieba.lcut_for_search(query)
                return [w for w in words if len(w) > 1][:3]
            except:
                # 最后备选
                return [query[:10]]

    def simple_answer(self, query, use_web=True):
        """
        简单联网问答模式
        Args:
            query: 用户问题
            use_web: 是否使用联网搜索
        Returns:
            回答文本
        """
        self.log_signal.emit(f"🌐 执行简单问答: {query[:50]}...")

        try:
            # 1. 尝试本地知识库
            local_answer = self._search_local(query, top_k=2)

            # 2. 如果需要且允许，进行联网搜索
            if use_web and self.web_engine:
                # 检查是否需要最新信息
                if self._needs_fresh_info(query):
                    web_context = self._search_web_async(query)

                    if web_context:
                        # 合并本地和网络信息
                        combined_context = f"{local_answer}\n\n网络补充:\n{web_context}"
                        answer = self._synthesize_answer(query, combined_context)
                        return answer

            # 3. 如果不需要联网或联网失败，直接回答
            if local_answer and "未找到" not in local_answer:
                answer = self._synthesize_answer(query, local_answer)
                return answer

            # 4. 实在找不到，返回通用回复
            return "抱歉，我目前无法回答这个问题。请尝试更具体的问题，或者启用联网搜索功能。"

        except Exception as e:
            self.log_signal.emit(f"❌ 简单问答失败: {str(e)}")
            return f"回答过程出现错误: {str(e)}"

    def _needs_fresh_info(self, query):
        """判断是否需要最新信息"""
        fresh_keywords = [
            "最新", "今天", "近期", "2024", "2025", "今年",
            "新闻", "动态", "趋势", "更新", "刚刚", "最近"
        ]

        query_lower = query.lower()
        return any(keyword in query_lower for keyword in fresh_keywords)

    def _synthesize_answer(self, query, context):
        """基于上下文合成回答"""
        prompt = f"""
        基于以下信息，请用简洁明了的语言回答问题：

        【问题】：
        {query}

        【参考信息】：
        {context}

        【要求】：
        1. 准确回答用户问题
        2. 如果信息不足，明确说明
        3. 保持客观中立
        4. 长度控制在300字以内
        """

        try:
            answer = self.llm.chat(prompt, options={"temperature": 0.3})
            return answer.strip()
        except Exception as e:
            self.log_signal.emit(f"❌ 回答合成失败: {e}")
            return context[:200] + "..."  # 返回原始信息片段

    def deep_learn(self, topic, local_context="", depth="medium"):
        """
        深度学习模式 - 主动填补知识缺口

        Args:
            topic: 学习主题
            local_context: 已有本地上下文
            depth: "quick"快速学习 / "medium"中等深度 / "deep"深度学习
        Returns:
            学习到的知识
        """
        self.log_signal.emit(f"🧠 启动深度学习: {topic}")

        try:
            # 1. 分析知识缺口
            gap_analysis = self._analyze_knowledge_gap(topic, local_context)

            # 2. 根据深度决定搜索策略
            if depth == "quick":
                search_keywords = gap_analysis.get("keywords", [topic])[:2]
            elif depth == "medium":
                search_keywords = gap_analysis.get("keywords", [topic])[:4]
            else:  # deep
                search_keywords = gap_analysis.get("keywords", [topic])[:6]

            # 3. 并行搜索学习
            learned_materials = self._parallel_learn(search_keywords, depth)

            # 4. 知识整合与提炼
            integrated_knowledge = self._integrate_knowledge(
                topic, local_context, learned_materials
            )

            # 5. 记录学习历史
            self._record_learning(topic, search_keywords, len(learned_materials))

            return integrated_knowledge

        except Exception as e:
            self.log_signal.emit(f"❌ 深度学习失败: {str(e)}")
            return f"学习过程出错: {str(e)}"

    def _analyze_knowledge_gap(self, topic, local_context):
        """分析知识缺口"""
        prompt = f"""
        主题：{topic}
        已有资料：{local_context[:500] if local_context else "无"}

        请分析还需要哪些方面的知识，输出格式：

        【知识缺口分析】：
        1. 核心概念澄清：需要明确的定义和边界
        2. 最新进展：需要了解的最新发展
        3. 实践案例：需要具体的应用案例
        4. 相关理论：需要了解的支撑理论

        【搜索关键词建议】：关键词1, 关键词2, 关键词3...
        """

        try:
            response = self.llm.chat(prompt, options={"temperature": 0.2})

            # 解析响应
            gaps = {}
            keywords = [topic]  # 默认包含主题

            if "【搜索关键词建议】" in response:
                kw_part = response.split("【搜索关键词建议】")[1].strip()
                extracted = re.findall(r'[^,，\s]+', kw_part)
                keywords.extend([k.strip() for k in extracted if len(k.strip()) > 1])

            return {
                "analysis": response[:500],
                "keywords": list(set(keywords))[:8]  # 去重并限制数量
            }

        except Exception as e:
            self.log_signal.emit(f"⚠️ 缺口分析异常，使用默认关键词: {e}")
            return {"keywords": [topic, "最新发展", "实践案例"]}

    def _parallel_learn(self, keywords, depth):
        """并行学习多个关键词"""
        learned_materials = []

        # 确定每个关键词的搜索强度
        if depth == "quick":
            max_results = 1
            max_length = 300
        elif depth == "medium":
            max_results = 2
            max_length = 500
        else:  # deep
            max_results = 3
            max_length = 800

        # 并行搜索任务
        futures = {}
        for kw in keywords[:6]:  # 最多6个关键词
            future = self.executor.submit(
                self._single_keyword_learn,
                kw, max_results, max_length
            )
            futures[future] = kw

        # 收集结果
        for future in as_completed(futures):
            kw = futures[future]
            try:
                result = future.result(timeout=30)  # 30秒超时
                if result:
                    learned_materials.append(f"【{kw}】:\n{result}")
            except Exception as e:
                self.log_signal.emit(f"⚠️ 学习关键词 '{kw}' 失败: {e}")

        return learned_materials

    def _single_keyword_learn(self, keyword, max_results, max_length):
        """单个关键词学习"""
        if not self.web_engine:
            return f"未启用联网搜索，无法学习: {keyword}"

        try:
            # 使用WebSearcher的search方法
            if hasattr(self.web_engine, 'search'):
                raw_results = self.web_engine.search(keyword, max_results=max_results)
                if raw_results:
                    # 提炼干货
                    summary = self._summarize_raw_data(raw_results, max_length)
                    return summary
        except Exception as e:
            self.log_signal.emit(f"❌ 学习'{keyword}'异常: {e}")

        return None

    def _summarize_raw_data(self, raw_data, max_length):
        """提炼网络数据"""
        # 如果已经是字符串格式，直接处理
        if isinstance(raw_data, str):
            content = raw_data
        elif isinstance(raw_data, list):
            # 如果是列表，先格式化
            content = self._format_web_results(raw_data)
        else:
            content = str(raw_data)

        prompt = f"""
        请提炼以下内容的干货，去除广告、废话和重复信息：

        {content[:2000]}

        要求：
        1. 提取核心事实和观点
        2. 保持客观准确
        3. 长度不超过{max_length}字
        4. 按重要性排序
        """

        try:
            summary = self.llm.chat(prompt, options={"temperature": 0.1})
            return summary.strip()
        except:
            return content[:max_length]  # 如果提炼失败，返回原始片段

    def _integrate_knowledge(self, topic, local_context, learned_materials):
        """整合学习到的知识"""
        all_materials = "\n\n".join(learned_materials)

        prompt = f"""
        主题：{topic}

        【已有本地知识】：
        {local_context if local_context else "暂无"}

        【新学习到的知识】：
        {all_materials}

        【任务】：整合以上所有知识，形成一个结构化的知识摘要。

        【输出格式】：
        一、核心概念
        二、关键事实
        三、实践启示
        四、学习建议

        【要求】：
        1. 准确引用来源
        2. 去除矛盾信息
        3. 突出重点
        4. 结构清晰
        """

        try:
            integrated = self.llm.chat(prompt, options={"temperature": 0.3})
            return integrated
        except Exception as e:
            self.log_signal.emit(f"❌ 知识整合失败: {e}")
            return all_materials  # 返回原始学习材料

    def _record_learning(self, topic, keywords, material_count):
        """记录学习历史"""
        record = {
            "topic": topic,
            "keywords": keywords,
            "material_count": material_count,
            "timestamp": datetime.now().isoformat(),
            "type": "deep_learn"
        }

        self.learning_history.append(record)

        # 限制历史记录数量
        if len(self.learning_history) > self.max_history:
            self.learning_history = self.learning_history[-self.max_history:]

    def _fallback_local_search(self, query):
        """备用本地搜索方案"""
        try:
            # 如果知识库有data属性，尝试直接搜索
            if hasattr(self.kb, 'data') and 'documents' in self.kb.data:
                docs = self.kb.data['documents']

                # 简单关键词匹配
                results = []
                query_words = set(query.lower().split())

                for doc_name, doc_data in docs.items():
                    content = doc_data.get('content', '').lower()

                    # 计算匹配度
                    match_count = sum(1 for word in query_words if word in content)
                    if match_count > 0:
                        snippet = doc_data.get('summary', content[:100])
                        results.append(f"《{doc_name}》: {snippet}")

                if results:
                    return "\n".join(results[:3])  # 返回前3个结果

            return "未找到相关内容"
        except Exception as e:
            return f"搜索异常: {str(e)}"

    def get_learning_stats(self):
        """获取学习统计"""
        total_searches = len(self.learning_history)
        recent_topics = [h['topic'] for h in self.learning_history[-5:]]

        return {
            "total_searches": total_searches,
            "recent_topics": recent_topics,
            "active": total_searches > 0
        }

    def clear_history(self):
        """清空学习历史"""
        self.learning_history = []
        self.log_signal.emit("🧹 已清空学习历史")

    def research(self, query: str, deep=False) -> str:
        """
        执行研究任务 - 新增的深度思考模式
        :param query: 研究课题
        :param deep: 是否深度模式 (多源整合)
        :return: 研究报告
        """
        self.log_signal.emit(f"🔍 [Researcher] 开始研究课题: {query}")

        # 1. 先查本地知识库
        local_context = ""
        if hasattr(self.kb, 'search'):
            local_context = self.kb.search(query, limit=3)
            if local_context:
                self.log_signal.emit("📚 已提取本地相关知识")

        # 2. 联网搜索 (如果可用)
        web_context = ""
        if self.web_engine and deep:
            self.status_signal.emit("正在联网搜索...")
            try:
                if hasattr(self.web_engine, 'search'):
                    web_results = self.web_engine.search(query, max_results=5)
                    web_context = self._format_web_results(web_results)
                    self.log_signal.emit(f"🌐 联网获取了 {len(web_results)} 条信息")
            except Exception as e:
                self.log_signal.emit(f"⚠️ 联网搜索异常: {e}")

        # 3. 综合生成回答
        self.status_signal.emit("正在整合报告...")
        prompt = f"""
你是一位专业的深度研究员。请根据已知信息回答问题。

【用户课题】：{query}

【本地知识库信息】：
{local_context}

【互联网最新信息】：
{web_context}

要求：
1. 优先使用本地知识库和互联网信息。
2. 如果信息冲突，以最新的互联网信息为准。
3. 结构清晰，分点论述。
4. 注明信息来源（本地/网络）。
"""
        try:
            response = self.llm.chat(prompt)

            # 记录历史
            self.learning_history.append({
                "topic": query,
                "timestamp": time.time(),
                "has_web": bool(web_context),
                "type": "research"
            })

            return response
        except Exception as e:
            self.log_signal.emit(f"❌ 研究过程失败: {e}")
            return f"研究过程出现错误: {str(e)}"

    def deep_research(self, query: str, outline_mode=True) -> str:
        """
        深度研究模式 - 配合Phase 2的大纲模式
        :param query: 研究课题
        :param outline_mode: 是否使用大纲模式
        :return: 深度研究报告
        """
        self.log_signal.emit(f"🔬 [Researcher] 启动深度研究: {query}")

        # 生成研究大纲
        if outline_mode:
            outline = self._generate_research_outline(query)
            self.log_signal.emit(f"📋 生成研究大纲: {outline[:100]}...")

            # 对每个大纲项进行研究
            sections = []
            for i, section in enumerate(self._extract_outline_sections(outline)):
                self.status_signal.emit(f"研究章节 {i+1}: {section[:30]}...")
                section_content = self.research(f"{query} - {section}", deep=True)
                sections.append(f"## {section}\n{section_content}")

            # 整合报告
            report = f"# {query}\n\n## 研究大纲\n{outline}\n\n" + "\n\n".join(sections)
        else:
            # 直接深度研究
            report = self.research(query, deep=True)

        # 记录深度研究历史
        self.learning_history.append({
            "topic": query,
            "timestamp": time.time(),
            "type": "deep_research",
            "outline_mode": outline_mode
        })

        return report

    def _generate_research_outline(self, query):
        """生成研究大纲"""
        prompt = f"""
        请为以下研究课题生成一个详细的研究大纲：

        研究课题：{query}

        要求：
        1. 大纲应包含3-5个主要章节
        2. 每个章节应有2-3个子章节
        3. 大纲应逻辑清晰，覆盖课题的各个方面
        4. 格式使用Markdown标题格式

        例如：
        # 研究课题
        ## 第一章：引言
        ### 1.1 研究背景
        ### 1.2 研究意义
        ## 第二章：理论基础
        ### 2.1 核心概念
        ### 2.2 相关理论
        ## 第三章：现状分析
        ### 3.1 当前发展状况
        ### 3.2 存在问题
        ## 第四章：解决方案
        ### 4.1 建议措施
        ### 4.2 实施步骤
        ## 第五章：结论
        ### 5.1 研究总结
        ### 5.2 未来展望
        """

        try:
            outline = self.llm.chat(prompt, options={"temperature": 0.3})
            return outline
        except Exception as e:
            self.log_signal.emit(f"⚠️ 大纲生成失败: {e}")
            # 返回默认大纲
            return f"""
            # {query}
            ## 第一章：引言
            ## 第二章：核心概念
            ## 第三章：现状分析
            ## 第四章：解决方案
            ## 第五章：结论
            """

    def _extract_outline_sections(self, outline):
        """从大纲中提取章节标题"""
        sections = []
        lines = outline.split('\n')
        for line in lines:
            # 匹配二级和三级标题
            if line.strip().startswith('## ') and not line.strip().startswith('###'):
                section = line.strip()[3:].strip()
                if section and len(section) > 2:
                    sections.append(section)
        return sections[:5]  # 最多5个章节