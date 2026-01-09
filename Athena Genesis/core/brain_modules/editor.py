# core/brain_modules/editor.py
# -*- coding: utf-8 -*-
"""
审稿委员会 - 多Agent审查系统
模块特点：语法纠错、逻辑校对、风格润色、事实核查
"""
import json
import os
import re
import traceback
from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime


class Editor(QObject):
    """审稿委员会 - 深度审查与润色"""

    # 信号定义
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)

    def __init__(self, bus, llm):
        super().__init__()
        self.bus = bus
        self.llm = llm

        # 错误记忆库
        self.memory_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data', 'editor_memory.json'
        )

        # 初始化记忆库
        self.common_errors = self._load_memory()

        # 审查维度权重
        self.weights = {
            "grammar": 0.25,  # 语法错误
            "logic": 0.35,  # 逻辑一致性
            "facts": 0.20,  # 事实准确性
            "style": 0.20  # 风格一致性
        }

        # 专业术语库
        self.professional_terms = {
            "机关": ["体制", "编制", "科层", "职级", "审批"],
            "职场": ["KPI", "OKR", "述职", "晋升", "绩效"],
            "写作": ["立意", "框架", "措辞", "修辞", "文笔"]
        }

    def _load_memory(self):
        """加载审查记忆库"""
        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("common_errors", [])
            except Exception as e:
                self.log_signal.emit(f"⚠️ 加载审稿记忆失败: {e}")
        return []

    def _save_memory(self, error_type, example):
        """保存错误到记忆库"""
        try:
            if os.path.exists(self.memory_path):
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {"common_errors": []}

            # 添加新错误记录
            error_record = {
                "type": error_type,
                "example": example[:100],  # 只保存片段
                "timestamp": datetime.now().isoformat(),
                "count": 1
            }

            # 检查是否已存在相似错误
            for i, record in enumerate(data["common_errors"]):
                if (record["type"] == error_type and
                        record["example"][:50] == example[:50]):
                    record["count"] += 1
                    record["timestamp"] = datetime.now().isoformat()
                    break
            else:
                data["common_errors"].append(error_record)

            # 只保留最近100条
            if len(data["common_errors"]) > 100:
                data["common_errors"] = data["common_errors"][-100:]

            # 保存到文件
            os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)
            with open(self.memory_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.log_signal.emit(f"❌ 保存审稿记忆失败: {e}")

    def review(self, text, context="", check_mode="full"):
        """
        深度审查文本
        Args:
            text: 待审查文本
            context: 上下文信息（可选）
            check_mode: "quick"快速检查 / "full"完整审查 / "strict"严格审查
        Returns:
            (审查结果, 审查报告)
        """
        if not text or len(text.strip()) < 10:
            return text, "文本过短，无需审查"

        self.status_signal.emit("🔍 启动深度审查...")

        original_text = text
        review_report = []

        try:
            # ========== 第1轮：语法与错别字 ==========
            grammar_result = self._check_grammar(text, context)
            if grammar_result["score"] < 0.9:
                text = grammar_result["corrected"]
                review_report.append(f"✅ 语法纠错: 修复了{len(grammar_result['issues'])}处错误")

                # 记录到记忆库
                for issue in grammar_result["issues"][:3]:  # 只记录前3个
                    self._save_memory("grammar", issue.get("text", ""))

            # ========== 第2轮：逻辑一致性 ==========
            if check_mode in ["full", "strict"]:
                logic_result = self._check_logic(text, context)
                if logic_result["score"] < 0.8:
                    text = logic_result["improved"]
                    review_report.append(f"🔧 逻辑优化: {logic_result['summary']}")

            # ========== 第3轮：事实准确性 ==========
            if check_mode == "strict":
                facts_result = self._check_facts(text, context)
                if facts_result["issues"]:
                    text = facts_result["corrected"]
                    review_report.append(f"📊 事实核查: 修正{len(facts_result['issues'])}处疑点")

            # ========== 第4轮：风格润色 ==========
            style_result = self._polish_style(text, context)
            if style_result["improved"]:
                text = style_result["text"]
                review_report.append(f"🎨 风格润色: {style_result['summary']}")

            # ========== 第5轮：可读性评估 ==========
            readability_result = self._check_readability(text)
            review_report.append(f"📖 可读性评分: {readability_result['score']:.1f}/10")

            # 生成最终报告
            if not review_report:
                final_report = "✅ 文本通过所有审查，质量优秀"
            else:
                final_report = "📋 审查报告:\n" + "\n".join([f"- {item}" for item in review_report])

            # 如果是严格模式，添加警告
            if check_mode == "strict":
                if readability_result["score"] < 7:
                    final_report += "\n⚠️ 警告: 可读性较差，建议简化表达"

            self.status_signal.emit("✅ 审查完成")
            return text, final_report

        except Exception as e:
            error_msg = f"审查过程异常: {str(e)}"
            self.log_signal.emit(f"❌ {error_msg}")
            self.log_signal.emit(traceback.format_exc())
            return original_text, f"⚠️ 审查异常: {str(e)}"

    def _check_grammar(self, text, context):
        """语法与错别字检查"""
        # 构建历史错误提示
        error_history = ""
        if self.common_errors:
            recent_errors = [e.get("example", "")[:50] for e in self.common_errors[-3:]]
            error_history = "最近常见错误:\n" + "\n".join([f"- {e}" for e in recent_errors])

        prompt = f"""
        你是中文校对专家，请严格检查以下文本的语法、错别字、标点符号问题。

        {error_history}

        【上下文背景】:
        {context[:200]}

        【待审查文本】:
        {text}

        【审查要求】:
        1. 找出所有语法错误和错别字
        2. 修正错误的标点符号
        3. 保持原文风格不变
        4. 输出格式：先给修正后的完整文本，然后用"【问题列表】"列出具体问题

        【输出格式示例】:
        修正后文本：...

        【问题列表】:
        1. 第X行："原词"应为"正确词"（错误类型）
        """

        response = self.llm.chat(prompt, options={"temperature": 0.1})

        # 解析响应
        issues = []
        corrected_text = text

        # 尝试解析LLM响应
        if "【问题列表】" in response:
            parts = response.split("【问题列表】")
            corrected_text = parts[0].replace("修正后文本：", "").strip()

            # 提取问题列表
            for line in parts[1].split('\n'):
                line = line.strip()
                if line and line[0].isdigit():
                    issues.append({"text": line})

        score = 1.0 - min(len(issues) * 0.1, 0.5)  # 简单评分

        return {
            "score": score,
            "corrected": corrected_text,
            "issues": issues,
            "raw_response": response[:500]  # 保存部分原始响应
        }

    def _check_logic(self, text, context):
        """逻辑一致性检查"""
        prompt = f"""
        请分析以下文本的逻辑一致性，找出矛盾、跳跃或含糊不清的地方。

        【文本背景】:
        {context[:300]}

        【待分析文本】:
        {text}

        【审查维度】:
        1. 前后观点是否一致？
        2. 论证是否严密？
        3. 是否存在逻辑跳跃？
        4. 结论是否合理？

        【输出格式】:
        逻辑评分: X/10
        主要问题: (用项目符号列出)
        优化建议: (用项目符号列出)
        优化后文本: (如果问题严重，请直接给出优化版本)
        """

        response = self.llm.chat(prompt, options={"temperature": 0.2})

        # 解析响应
        improved_text = text
        summary = "逻辑基本通顺"

        if "优化后文本：" in response:
            improved_text = response.split("优化后文本：")[-1].strip()
            summary = "已优化逻辑结构"

        # 提取评分
        import re
        score_match = re.search(r"逻辑评分:\s*(\d+(\.\d+)?)/10", response)
        score = float(score_match.group(1)) / 10 if score_match else 0.7

        return {
            "score": score,
            "improved": improved_text,
            "summary": summary,
            "raw_response": response[:300]
        }

    def _check_facts(self, text, context):
        """事实准确性检查"""
        prompt = f"""
        你是一位事实核查员，请检查以下文本中的事实陈述是否准确。

        【上下文】:
        {context[:500]}

        【待核查文本】:
        {text}

        【核查要求】:
        1. 指出所有可能存在事实错误的地方
        2. 标注缺乏依据的断言
        3. 如果发现明显错误，请给出修正建议
        4. 区分"确定错误"和"需要核实"

        【输出格式】:
        事实核查结果:
        1. [确定错误] 问题描述 -> 建议修正
        2. [需要核实] 问题描述 -> 建议核实
        """

        response = self.llm.chat(prompt, options={"temperature": 0.1})

        # 简单解析
        issues = []
        if "事实核查结果:" in response:
            for line in response.split('\n'):
                if line.strip() and line.strip()[0].isdigit():
                    issues.append(line.strip())

        return {
            "issues": issues,
            "corrected": text,  # 暂不自动修正
            "raw_response": response[:400]
        }

    def _polish_style(self, text, context):
        """风格润色"""
        prompt = f"""
        请对以下文本进行风格润色，提升表达效果。

        【原文风格】:
        {context[:200]}...

        【待润色文本】:
        {text}

        【润色要求】:
        1. 保持原意不变
        2. 提升语言流畅度
        3. 优化句式结构
        4. 适当使用修辞手法
        5. 使表达更生动有力

        【输出格式】:
        润色后文本: ...
        改进说明: (简要说明主要改进点)
        """

        response = self.llm.chat(prompt, options={"temperature": 0.6})

        # 提取润色后文本
        polished_text = text
        summary = "风格保持原样"

        if "润色后文本：" in response:
            parts = response.split("润色后文本：")
            if len(parts) > 1:
                polished_text = parts[1].split("改进说明：")[0].strip()

                # 提取改进说明
                if "改进说明：" in response:
                    summary = response.split("改进说明：")[1].strip()[:100]

        return {
            "improved": polished_text != text,
            "text": polished_text,
            "summary": summary,
            "raw_response": response[:200]
        }

    def _check_readability(self, text):
        """可读性评估"""
        # 简单可读性计算（可以替换为更复杂的算法）
        import re

        # 句子数量
        sentences = re.split(r'[。！？；]', text)
        sentence_count = max(len([s for s in sentences if s.strip()]), 1)

        # 平均句长
        chars_per_sentence = len(text) / sentence_count

        # 长句比例（超过30字为长句）
        long_sentences = sum(1 for s in sentences if len(s.strip()) > 30)
        long_ratio = long_sentences / sentence_count

        # 段落清晰度（通过段落数判断）
        paragraphs = text.split('\n\n')
        paragraph_count = len([p for p in paragraphs if p.strip()])

        # 简单评分算法
        score = 10.0

        # 惩罚过长句子
        if chars_per_sentence > 50:
            score -= 3
        elif chars_per_sentence > 30:
            score -= 1

        # 惩罚过多长句
        if long_ratio > 0.5:
            score -= 2

        # 鼓励适当分段
        if 3 <= paragraph_count <= 10:
            score += 1

        # 确保在0-10分
        score = max(0, min(10, score))

        return {
            "score": score,
            "metrics": {
                "句子数": sentence_count,
                "平均句长": f"{chars_per_sentence:.1f}字",
                "长句比例": f"{long_ratio * 100:.1f}%",
                "段落数": paragraph_count
            }
        }

    def quick_check(self, text):
        """快速检查模式"""
        # 简单检查，不调用LLM
        issues = []

        # 检查常见错误
        common_mistakes = {
            "的得地": ["的", "得", "地"],
            "做作": ["做", "作"],
            "在再": ["在", "再"]
        }

        # 简单实现：统计疑似错误
        for word in ["的", "得", "地"]:
            # 这里可以添加更复杂的检查逻辑
            pass

        return {
            "has_issues": len(issues) > 0,
            "issues": issues,
            "suggestion": "建议进行完整审查" if len(issues) > 0 else "基础检查通过"
        }