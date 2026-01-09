# -*- coding: utf-8 -*-
"""
文档智能分析器 - 企业级完整版 + 乱码清洗 + 原子级DNA分析 (终极修复增强版)
包含：全量关键词(Top100)、正则句式挖掘、NLP情感分析、雷达图真实算法、文件意图识别、原子级DNA分析
新增：极速扫描模式(fast_analyze) + LLM深度分析模式
修复：核心关键词出现乱码、空格、控制符问题
增强：整合原子级分析(词级、句级、词性、逻辑关联词分析)
"""
import re
import jieba
import jieba.analyse
import jieba.posseg as pseg
import collections
import math
import numpy as np
from collections import Counter


class DocumentIntelligenceAnalyzer:
    """
    深度解构文档，提取灵魂特征 + 原子级DNA分析
    支持三种模式：
    1. deep_analyze: 全量深度分析 (规则算法)
    2. fast_analyze: 极速扫描模式 (0.01s/文件)
    3. llm_analyze: LLM深度解读 (需提供LLM引擎)
    """

    def __init__(self, llm_engine=None):
        # 🔥 扩展停用词表 (来自无标题.txt)
        self.stop_words = {
            '的', '了', '和', '是', '就', '都', '而', '及', '与', '在',
            '这', '那', '有', '个', '之', '上', '下', '我们', '你们',
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
            ' ', '\t', '\n', '\r', '\xa0', '\u3000',  # 空白字符
        }

        # 🔥 新增：原子级分析组件 (来自3.txt)
        # 语气助词库 (CR1.2 情感权重)
        self.particles = {'吗', '呢', '啊', '呀', '吧', '罢', '呗', '嘞', '哇'}
        # 逻辑关联词 (CR1.3 句子结构)
        self.logic_markers = {
            '因果': ['因为', '所以', '因此', '导致', '致使'],
            '转折': ['但是', '然而', '不过', '却', '虽然'],
            '递进': ['而且', '并且', '不仅', '甚至', '更'],
            '条件': ['只要', '只有', '除非', '无论']
        }

        # LLM引擎 (可选，用于深度分析)
        self.llm = llm_engine

        # 初始化jieba，加载自定义词典（可选）
        try:
            jieba.initialize()
        except:
            pass

    # ==========================================
    # 🔥🔥🔥 核心修复：新增 fast_analyze 方法 🔥🔥🔥
    # ==========================================
    def fast_analyze(self, content, filename):
        """
        ⚡ [极速模式] 快速扫描，不消耗 LLM 资源
        速度：0.01s / 文件
        返回精简版分析结果
        """
        if not content:
            return self._empty_fast_result(filename)

        # 1. 物理特征
        length = len(content)

        # 2. 提取摘要 (取前 200 字 + 简单的清洗)
        summary = content[:300].replace('\n', ' ').strip() + "..."

        # 3. 提取关键词 (使用 Jieba TF-IDF 算法)
        try:
            tags = jieba.analyse.extract_tags(content, topK=8)
            keywords = {tag: 1.0 for tag in tags}
        except:
            keywords = {}

        # 4. 估算雷达图数据 (基于关键词匹配)
        metrics = self._calculate_metrics_rule_based(content)

        return {
            "document_info": {
                "filename": filename,
                "length": length,
                "filepath": filename,  # 确保有这个字段
                "analysis_mode": "fast"
            },
            "semantic_summary": {
                "keywords": keywords,
                "sentiment": "neutral"
            },
            "radar_metrics": metrics,
            "text_report": f"【快速扫描摘要】\n{summary}\n\n(双击文档列表可进行深度 AI 解读)"
        }

    def _calculate_metrics_rule_based(self, text):
        """基于规则快速生成六维数据 (无需 LLM)"""
        base_score = 60
        text_sample = text[:5000] if len(text) > 5000 else text

        # 简单的关键词命中计数
        logic_score = base_score + text_sample.count("因为") * 2 + text_sample.count("数据") * 2
        emotion_score = base_score + text_sample.count("！") * 5 + text_sample.count("感动") * 5
        depth_score = base_score + len(text) / 1000  # 字数越多越深

        return {
            "logic": min(95, logic_score),
            "emotion": min(95, emotion_score),
            "creativity": 70,
            "depth": min(95, depth_score),
            "structure": 80,
            "practicality": 80
        }

    # ==========================================
    # 🔥🔥🔥 新增 LLM 深度分析模式 🔥🔥🔥
    # ==========================================
    def llm_analyze(self, content, filename):
        """
        [深度模式] 调用 LLM 进行精读
        需要初始化时传入 llm_engine
        """
        if not content:
            return self._empty_llm_result(filename)

        # 尝试调用 LLM，如果没有 LLM 则返回规则分析结果
        if not self.llm:
            # 如果没有LLM引擎，则使用fast_analyze作为兜底
            result = self.fast_analyze(content, filename)
            result["document_info"]["analysis_mode"] = "fast (no LLM)"
            result["text_report"] = "LLM 未连接，已使用快速扫描模式"
            return result

        # 构建LLM提示词
        summary_prompt = f"请阅读文件《{filename}》，提炼核心观点和数据。\n内容：{content[:5000]}"

        try:
            # 调用LLM
            result_text = self.llm.chat(summary_prompt, options={"temperature": 0.3})
        except Exception as e:
            # LLM调用失败，回退到规则分析
            print(f"LLM分析失败: {e}")
            result = self.fast_analyze(content, filename)
            result["document_info"]["analysis_mode"] = "fast (LLM failed)"
            result["text_report"] = f"LLM分析失败，已使用快速扫描模式\n错误信息: {str(e)}"
            return result

        # 获取规则分析的雷达图数据
        metrics = self._calculate_metrics_rule_based(content)

        # 提取关键词
        try:
            tags = jieba.analyse.extract_tags(content, topK=15)
            keywords = {tag: 1.0 for tag in tags}
        except:
            keywords = {}

        return {
            "document_info": {
                "filename": filename,
                "length": len(content),
                "filepath": filename,
                "analysis_mode": "llm"
            },
            "text_report": result_text,
            "radar_metrics": metrics,
            "semantic_summary": {
                "keywords": keywords,
                "llm_analysis": True
            }
        }

    def deep_analyze(self, content: str, filename: str) -> dict:
        """
        执行全流程深度分析 (规则算法版)
        整合了乱码清洗功能 + 原子级DNA分析
        """
        if not content:
            return self._empty_result(filename)

        # 🔥 1. 深度清洗文本 (解决乱码核心，来自无标题.txt)
        # 仅保留：中文、英文、数字、基本标点
        # 去除不可见字符、特殊符号
        clean_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？：；、\.,!\?:"\'\-\s]', '', content)

        # 移除连续的空格和换行
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        # 如果没有有效内容，返回空结果
        if len(clean_text) < 10:
            return self._empty_result(filename)

        total_length = len(clean_text)

        # 🔥 2. 全量关键词提取 (Top 100, 必须全量以供仪表盘展示)
        # 允许的词性：名词、动词、形容词、专名
        allow_pos = ('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn', 'a', 'ad', 'an')

        try:
            keywords = jieba.analyse.extract_tags(
                clean_text, topK=100, withWeight=True, allowPOS=allow_pos
            )
        except Exception as e:
            print(f"关键词提取失败: {e}")
            # 降级方案：使用简单的分词统计
            words = jieba.lcut(clean_text)
            valid_words = [w for w in words if len(w.strip()) > 1 and w not in self.stop_words]
            word_counter = Counter(valid_words)
            keywords = [(word, count) for word, count in word_counter.most_common(50)]

        # 🔥 关键词清洗：去除停用词和乱码
        keyword_dict = {}
        for k, v in keywords:
            k_str = str(k).strip()
            # 过滤条件：不在停用词中，长度>1，仅包含有效字符
            if (k_str not in self.stop_words and
                    len(k_str) > 1 and
                    re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9]+$', k_str)):
                keyword_dict[k_str] = float(v)

        # 如果关键词太少，使用备用关键词提取方法
        if len(keyword_dict) < 5:
            keyword_dict = self._extract_keywords_fallback(clean_text)

        # 3. 句式结构深度挖掘 (用于仿写引擎)
        patterns = self._extract_sentence_patterns(clean_text)

        # 4. 深度情感与基调分析 (生成描述性文本)
        tone_desc = self._analyze_tone_depth(clean_text)

        # 5. 意图识别 (自动判断文档类型)
        intent = self._analyze_intent(clean_text, filename)

        # 6. 雷达图六维指标真实计算 (核心算法)
        metrics = self._calculate_real_metrics(clean_text, keyword_dict)

        # 7. 🔥 句子结构分析 (来自无标题.txt)
        style_dna = self._analyze_style_dna(clean_text)

        # 8. 🔥 原子级DNA分析 (来自3.txt) - 新增
        atomic_dna = self._analyze_atomic_dna(content)  # 使用原始内容进行原子级分析

        # 9. 生成摘要 (截取开头+关键句)
        summary = clean_text[:800].replace('\n', ' ') + "..." if len(clean_text) > 800 else clean_text

        # 10. 组装完整数据包
        return {
            "document_info": {
                "filename": filename,
                "length": total_length,
                "file_type": filename.split('.')[-1].upper() if '.' in filename else "TXT",
                "sentence_count": style_dna.get("sentence_count", 0),
                "analysis_mode": "deep"
            },
            "text_report": summary,
            "intent": intent,
            "semantic_summary": {
                "keywords": keyword_dict,
                "tone": tone_desc,
                "patterns": patterns,
                "sentence_structures": style_dna.get("sentence_structures", {})
            },
            "radar_metrics": metrics,
            "style_dna": style_dna,  # 🔥 原有风格DNA
            "atomic_dna": atomic_dna  # 🔥 新增原子级DNA分析
        }

    # ==========================================
    # 🔥 新增方法：原子级DNA分析 (来自3.txt)
    # ==========================================
    def _analyze_atomic_dna(self, text: str) -> dict:
        """
        原子级DNA分析 (CR1.1字级, CR1.2词级, CR1.3句级)
        返回深层写作DNA特征
        """
        if not text or len(text.strip()) == 0:
            return self._empty_atomic_dna()

        # 原子级分析使用原始文本（不进行深度清洗，保留所有字符）
        clean_text = re.sub(r'\s+', '', text)  # 仅去除空白字符
        sentences = re.split(r'[。！？\n]', clean_text)
        sentences = [s for s in sentences if len(s) > 1]

        # === Level 1: 原子级分析 (词性与用词偏好) ===
        words_flags = list(pseg.cut(clean_text))  # 词+词性

        # 统计词性密度 (CR1.2)
        pos_counts = Counter([flag for word, flag in words_flags])
        total_words = len(words_flags)

        # 虚词率 (的/地/得 使用习惯)
        u_count = pos_counts.get('u', 0)  # 助词
        adj_count = pos_counts.get('a', 0)  # 形容词
        idiom_count = pos_counts.get('i', 0)  # 成语

        # === Level 2: 节奏与句法 (CR1.3) ===
        sentence_lens = [len(s) for s in sentences]
        if sentence_lens:
            avg_len = np.mean(sentence_lens)
            std_dev = np.std(sentence_lens)  # 节奏波动率 (重要DNA)
            max_len = np.max(sentence_lens)
        else:
            avg_len, std_dev, max_len = 0, 0, 0

        # 标点指纹 (CR1.3 标点偏好)
        punct_raw = re.findall(r'[，。！？：；……—]', text)
        punct_counter = Counter(punct_raw)

        # === Level 3: 逻辑与修辞 (CR1.3) ===
        logic_profile = {k: 0 for k in self.logic_markers}
        for type_, keywords in self.logic_markers.items():
            for kw in keywords:
                logic_profile[type_] += text.count(kw)

        # === DNA 建模 (计算六维雷达分) ===
        # 1. 逻辑性 (Logic): 关联词密度 + 平均句长
        score_logic = min(95, int(logic_profile['因果'] * 5 + logic_profile['转折'] * 5 + avg_len * 0.5 + 30))

        # 2. 创造力 (Creativity): 形容词密度 + 成语密度
        score_creat = min(95, int((adj_count / max(1, total_words)) * 200 + idiom_count * 10 + 40))

        # 3. 情感度 (Emotion): 语气词 + 感叹号
        particle_count = sum(text.count(p) for p in self.particles)
        score_emo = min(95, int(particle_count * 5 + punct_counter.get('！', 0) * 8 + 30))

        # 4. 严谨度 (Critical): 句长波动低(稳) + 助词少(干练)
        # 波动率越低，结构越稳；助词越少，越像公文
        if total_words > 0:
            score_crit = min(95, int(100 - std_dev + (100 - (u_count / total_words * 500))))
        else:
            score_crit = 50
        if score_crit < 40:
            score_crit = 50

        # 5. 结构感 (Struct): 标点丰富度 + 逻辑词总数
        score_struct = min(95, int(len(punct_counter) * 10 + sum(logic_profile.values()) * 2 + 40))

        # 6. 深度 (Depth): 篇幅 + 长难句比例
        long_sentence_ratio = sum(1 for l in sentence_lens if l > 40) / max(1, len(sentence_lens))
        score_depth = min(95, int(long_sentence_ratio * 100 + avg_len + 20))

        # 提取高频实词 (用于Mimicry)
        keywords = [w for w, f in words_flags if f.startswith('n') or f.startswith('v') or f.startswith('a')]
        vocab_counter = Counter(keywords)

        return {
            "dna_signature": {
                "avg_len": round(avg_len, 1),
                "rhythm_volatility": round(std_dev, 1),  # 节奏波动
                "particle_ratio": round(u_count / max(1, total_words), 3) if total_words > 0 else 0,  # 虚词率
                "idiom_usage": idiom_count,
                "logic_map": logic_profile,
                "pos_density": dict(pos_counts.most_common(20))  # 词性密度分布
            },
            "atomic_radar_metrics": {
                "Logic": score_logic,
                "Creativity": score_creat,
                "Emotion": score_emo,
                "Critical": score_crit,
                "Struct": score_struct,
                "Depth": score_depth
            },
            "atomic_keywords": dict(vocab_counter.most_common(50))
        }

    def _empty_atomic_dna(self):
        """返回空的原子级DNA分析结果"""
        return {
            "dna_signature": {
                "avg_len": 0,
                "rhythm_volatility": 0,
                "particle_ratio": 0,
                "idiom_usage": 0,
                "logic_map": {},
                "pos_density": {}
            },
            "atomic_radar_metrics": {
                "Logic": 20, "Creativity": 20, "Emotion": 20,
                "Critical": 20, "Struct": 20, "Depth": 20
            },
            "atomic_keywords": {}
        }

    # ==========================================
    # 🔥 核心方法：句式结构挖掘 (来自1.txt)
    # ==========================================
    def _extract_sentence_patterns(self, text):
        """
        正则挖掘经典句式 (Few-Shot Prompting 素材)
        """
        # 按标点断句
        sentences = re.split(r'[。！？；]', text)
        patterns = []

        # 触发词库：覆盖公文、新闻、学术等多种风格
        triggers = [
            "我们要", "坚持", "推进", "强调", "指出", "意味着",
            "必须看到", "总的来看", "值得注意的是", "核心在于",
            "不仅", "既要", "是以", "旨在", "围绕"
        ]

        seen = set()

        for s in sentences:
            s = s.strip()
            # 长度过滤：太短无意义，太长LLM学不会
            if 8 < len(s) < 60:
                for t in triggers:
                    if s.startswith(t):
                        if s not in seen:
                            patterns.append(s)
                            seen.add(s)
                        break

        # 返回前15个高质量句式
        return list(patterns)[:15]

    # ==========================================
    # 🔥 核心方法：深度情感分析 (来自1.txt)
    # ==========================================
    def _analyze_tone_depth(self, text):
        """
        基于词袋模型的深度情感分析
        """
        score = 0
        # 扩充情感词典
        pos_words = ["突破", "创新", "增长", "胜利", "辉煌", "坚持", "伟大", "显著", "优化", "机遇", "完善", "提升"]
        neg_words = ["挑战", "困难", "严峻", "风险", "遏制", "压力", "不足", "矛盾", "滞后", "复杂", "下滑", "瓶颈"]

        for w in pos_words:
            score += text.count(w)
        for w in neg_words:
            score -= text.count(w) * 1.2  # 负面词权重略高

        # 判定基调
        base_tone = ""
        if score > 20:
            base_tone = "激昂向上、充满信心"
        elif score > 5:
            base_tone = "稳中求进、客观积极"
        elif score > -5:
            base_tone = "审慎冷静、直面挑战"
        elif score > -20:
            base_tone = "忧患意识、严肃批判"
        else:
            base_tone = "形势严峻、极度悲观"

        return base_tone

    # ==========================================
    # 🔥 核心方法：文档意图分类 (来自1.txt)
    # ==========================================
    def _analyze_intent(self, text, filename):
        """文档意图分类"""
        header = text[:300]
        if "通知" in filename or "关于" in filename:
            return "行政通知"
        if "报告" in filename or "总结" in filename:
            return "工作汇报"
        if "法" in filename or "条例" in filename:
            return "法律法规"
        if "研究" in header or "实验" in header:
            return "学术研究"
        return "通用资讯"

    # ==========================================
    # 🔥 核心方法：雷达图六维指标真实计算 (来自1.txt)
    # ==========================================
    def _calculate_real_metrics(self, text, keywords):
        """
        雷达图六维指标真实计算算法
        """
        L = max(len(text), 1)

        # 1. 逻辑性 (连接词密度)
        logic_kws = ['因此', '所以', '然而', '但是', '鉴于', '综上', '一方面', '同时']
        c_logic = sum(text.count(w) for w in logic_kws)
        score_logic = min(0.95, (c_logic / L) * 1000 / 10)  # 归一化

        # 2. 创造力 (新颖词汇+关键词离散度)
        create_kws = ['创新', '突破', '首创', '新质', '改革', '前沿', '独创']
        c_create = sum(text.count(w) for w in create_kws)
        diversity = len(keywords) / 100.0
        score_create = min(0.95, (c_create / L * 1000 / 5) * 0.6 + diversity * 0.4)

        # 3. 同理心 (人称代词与情感词)
        empathy_kws = ['我们', '大家', '人民', '群众', '感受', '心声', '关怀']
        c_emp = sum(text.count(w) for w in empathy_kws)
        score_emp = min(0.95, (c_emp / L) * 1000 / 8)

        # 4. 知识广度 (关键词权重总和)
        total_weight = sum(keywords.values())
        score_breadth = min(0.95, total_weight / 25.0)

        # 5. 记忆深度 (历史引用与篇幅)
        depth_kws = ['历史', '回顾', '过去', '以来', '百年', '根源']
        c_depth = sum(text.count(w) for w in depth_kws)
        score_depth = min(0.95, (c_depth / L * 1000 / 5) * 0.3 + min(1.0, L / 5000.0) * 0.7)

        # 6. 执行力 (动词密度)
        action_kws = ['落实', '执行', '实施', '推进', '完成', '确保', '行动', '打赢']
        c_act = sum(text.count(w) for w in action_kws)
        score_exec = min(0.95, (c_act / L) * 1000 / 10)

        # 保底修正 (防止雷达图缩成一点)
        def clamp(v):
            return max(0.25, v)

        return {
            "逻辑性": clamp(score_logic),
            "创造力": clamp(score_create),
            "同理心": clamp(score_emp),
            "知识广度": clamp(score_breadth),
            "记忆深度": clamp(score_depth),
            "执行力": clamp(score_exec)
        }

    # ==========================================
    # 🔥 核心方法：风格DNA分析 (来自无标题.txt)
    # ==========================================
    def _analyze_style_dna(self, text):
        """
        分析文档的风格DNA
        包括：平均句长、标点使用、句子结构等
        """
        if not text:
            return {
                "avg_sentence_length": 0,
                "sentence_volatility": 0,
                "punctuation_profile": {},
                "sentence_count": 0,
                "sentence_structures": {}
            }

        # 1. 标点符号指纹
        punctuations = re.findall(r'[！。？，、：；……]', text)
        punct_counter = Counter(punctuations)

        # 2. 句子分割
        sentences = re.split(r'[。！？]', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]  # 忽略太短的碎片

        sentence_count = len(sentences)

        # 3. 句子长度分析
        if sentences:
            lens = [len(s) for s in sentences]
            avg_len = np.mean(lens) if lens else 0
            std_dev = np.std(lens) if len(lens) > 1 else 0
        else:
            avg_len = 0
            std_dev = 0

        # 4. 句子结构分析（句式开头词）
        sentence_structures = Counter()
        for s in sentences:
            # 获取前2个字符作为句式特征
            if len(s) >= 2:
                prefix = s[:2]
                if re.match(r'^[\u4e00-\u9fa5]+$', prefix):  # 确保是中文字符
                    sentence_structures[prefix] += 1

        return {
            "avg_sentence_length": round(avg_len, 1),
            "sentence_volatility": round(std_dev, 1),
            "punctuation_profile": dict(punct_counter.most_common(10)),
            "sentence_count": sentence_count,
            "sentence_structures": dict(sentence_structures.most_common(10))
        }

    # ==========================================
    # 🔥 备用方法：备用关键词提取
    # ==========================================
    def _extract_keywords_fallback(self, text):
        """
        备用关键词提取方法
        当主方法失败时使用
        """
        # 基础分词
        words = jieba.lcut(text)

        # 过滤：必须长度>1，且不在停用词中
        valid_words = [w for w in words if len(w.strip()) > 1 and w not in self.stop_words]

        # 统计词频
        word_counter = Counter(valid_words)

        # 取前50个高频词
        top_words = word_counter.most_common(50)

        # 转换为权重格式（使用词频的log作为权重）
        keyword_dict = {}
        if top_words:
            max_freq = top_words[0][1]
            for word, freq in top_words:
                # 归一化权重 (0.1-1.0)
                weight = 0.1 + 0.9 * (freq / max_freq) if max_freq > 0 else 0.1
                keyword_dict[word] = round(weight, 2)

        return keyword_dict

    # ==========================================
    # 🔥 简化版分析接口
    # ==========================================
    def analyze(self, content: str) -> dict:
        """
        简化版分析接口（兼容无标题.txt的接口）
        默认使用深度分析模式
        """
        return self.deep_analyze(content, "unknown.txt")

    # ==========================================
    # 🔥 空结果生成器
    # ==========================================
    def _empty_result(self, filename="unknown.txt"):
        """返回空结果（深度分析模式）"""
        return {
            "document_info": {
                "filename": filename,
                "length": 0,
                "file_type": "UNKNOWN",
                "sentence_count": 0,
                "analysis_mode": "deep"
            },
            "text_report": "",
            "intent": "未知类型",
            "semantic_summary": {
                "keywords": {},
                "tone": "中性",
                "patterns": [],
                "sentence_structures": {}
            },
            "radar_metrics": {
                "逻辑性": 0.5,
                "创造力": 0.5,
                "同理心": 0.5,
                "知识广度": 0.5,
                "记忆深度": 0.5,
                "执行力": 0.5
            },
            "style_dna": {
                "avg_sentence_length": 0,
                "sentence_volatility": 0,
                "punctuation_profile": {},
                "sentence_count": 0,
                "sentence_structures": {}
            },
            "atomic_dna": self._empty_atomic_dna()  # 🔥 新增原子级DNA空结果
        }

    def _empty_fast_result(self, filename="unknown.txt"):
        """返回空结果（快速分析模式）"""
        return {
            "document_info": {
                "filename": filename,
                "length": 0,
                "filepath": filename,
                "analysis_mode": "fast"
            },
            "semantic_summary": {
                "keywords": {},
                "sentiment": "neutral"
            },
            "radar_metrics": {
                "logic": 60,
                "emotion": 60,
                "creativity": 70,
                "depth": 60,
                "structure": 80,
                "practicality": 80
            },
            "text_report": "文档为空或无法分析"
        }

    def _empty_llm_result(self, filename="unknown.txt"):
        """返回空结果（LLM分析模式）"""
        return {
            "document_info": {
                "filename": filename,
                "length": 0,
                "filepath": filename,
                "analysis_mode": "llm"
            },
            "text_report": "文档为空或无法分析",
            "radar_metrics": {
                "logic": 60,
                "emotion": 60,
                "creativity": 70,
                "depth": 60,
                "structure": 80,
                "practicality": 80
            },
            "semantic_summary": {
                "keywords": {},
                "llm_analysis": False
            }
        }

    # ==========================================
    # 🔥 批量分析
    # ==========================================
    def batch_analyze(self, contents: list, filenames: list, mode="deep") -> list:
        """
        批量分析多个文档
        mode: "deep" | "fast" | "llm"
        """
        results = []
        for content, filename in zip(contents, filenames):
            try:
                if mode == "fast":
                    result = self.fast_analyze(content, filename)
                elif mode == "llm":
                    result = self.llm_analyze(content, filename)
                else:  # deep
                    result = self.deep_analyze(content, filename)
                results.append(result)
            except Exception as e:
                print(f"分析文档 {filename} 时出错: {e}")
                if mode == "fast":
                    results.append(self._empty_fast_result(filename))
                elif mode == "llm":
                    results.append(self._empty_llm_result(filename))
                else:
                    results.append(self._empty_result(filename))

        return results

    # ==========================================
    # 🔥 文本清洗接口
    # ==========================================
    def clean_text(self, content: str) -> str:
        """
        对外提供的文本清洗接口
        """
        if not content:
            return ""

        # 深度清洗文本
        clean_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？：；、\.,!\?:"\'\-\s]', '', content)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        return clean_text

    # ==========================================
    # 🔥 诊断模式
    # ==========================================
    def diagnose_analysis(self, content: str, filename: str) -> dict:
        """
        诊断模式：返回分析过程中的中间结果
        用于调试和优化
        """
        # 原始文本信息
        original_length = len(content) if content else 0

        # 清洗后的文本
        clean_text = self.clean_text(content)
        clean_length = len(clean_text)

        # 分词测试
        words = jieba.lcut(clean_text) if clean_text else []
        word_count = len(words)

        # 关键词提取测试
        try:
            test_keywords = jieba.analyse.extract_tags(
                clean_text, topK=20, withWeight=False
            ) if clean_text else []
        except:
            test_keywords = []

        return {
            "diagnostics": {
                "original_length": original_length,
                "clean_length": clean_length,
                "word_count": word_count,
                "clean_text_sample": clean_text[:200] + "..." if clean_text else "",
                "test_keywords": test_keywords[:10],
                "stop_words_count": len(self.stop_words),
                "atomic_components": {
                    "particles": len(self.particles),
                    "logic_markers": len(self.logic_markers)
                },
                "llm_available": self.llm is not None
            },
            "full_analysis": self.deep_analyze(content, filename) if content else self._empty_result(filename)
        }