# -*- coding: utf-8 -*-
"""
深度语义分析器 - 高算力版 (完整修复)
"""
import re
import numpy as np
from typing import Dict, Any, List
from collections import Counter

# 尝试导入 NLP 库
try:
    import jieba
    import jieba.posseg as pseg

    HAS_NLP = True
except ImportError:
    HAS_NLP = False


class SemanticAnalyzer:
    """
    语义分析器：负责语气、情感、意图识别
    """

    def __init__(self):
        self.positive_words = {'成功', '优秀', '快乐', '希望', '发展', '创新', '突破', '美好'}
        self.negative_words = {'失败', '糟糕', '痛苦', '失望', '危机', '错误', '遗憾', '恨'}
        # 扩充意图词库
        self.intent_keywords = {
            "narrative": ['然后', '接着', '后来', '曾经', '当时'],
            "persuasive": ['应该', '必须', '显然', '因此', '事实上', '建议'],
            "descriptive": ['仿佛', '犹如', '色彩', '形状', '显得'],
            "lyrical": ['啊', '哦', '心', '感觉', '灵魂']
        }

    def analyze(self, text: str) -> Dict[str, Any]:
        """执行全量语义分析 (适配 Brain 接口)"""
        if not text: return {}

        # 1. 情感分析 (Sentiment)
        words = list(jieba.cut(text)) if HAS_NLP else text.split()
        score = 0
        for w in words:
            if w in self.positive_words:
                score += 1
            elif w in self.negative_words:
                score -= 1

        # 归一化 (-1.0 ~ 1.0)
        sentiment = max(-1.0, min(1.0, score / (len(words) * 0.02 + 1)))

        # 2. 意图识别 (Intent)
        intent_scores = {k: 0 for k in self.intent_keywords}
        for w in words:
            for k, v in self.intent_keywords.items():
                if w in v: intent_scores[k] += 1
        primary_intent = max(intent_scores, key=intent_scores.get)
        if intent_scores[primary_intent] == 0: primary_intent = "informative"

        # 3. 生成标签
        tag = "中性客观"
        if sentiment > 0.3:
            tag = "积极昂扬"
        elif sentiment < -0.3:
            tag = "消极批判"

        # 4. 词性指纹 (如果可用)
        fingerprint = {}
        if HAS_NLP:
            pos_flags = [flag for w, flag in pseg.cut(text[:1000])]  # 采样前1000字
            c = Counter(pos_flags)
            total = len(pos_flags) or 1
            fingerprint = {
                "verbs": (c['v'] + c['vn']) / total,
                "adjectives": (c['a'] + c['ad']) / total
            }

        return {
            "semantic_profile": {
                "sentiment_bias": sentiment,
                "primary_intent": primary_intent,
                "summary_tag": tag,
                "fingerprint": fingerprint
            }
        }