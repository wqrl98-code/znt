# -*- coding: utf-8 -*-
"""
拟态引擎 - 终极聚合修复版 + DNA建模增强版 + 声音特质分析
修复：
1. AttributeError: learned_docs 缺失 ✅
2. 仪表盘风格画像不显示 ✅
3. 词库乱码问题 (增加清洗) ✅
4. 仿写功能失效 ✅
5. 六维图数据丢失、画像不更新 ✅
新增：
- 雷达数据平均值计算 (Radar Aggregation)
- 知识库记忆恢复/导出导入功能
- 风格统计仪表盘数据支持
- 专项仿写提示生成功能
- DNA建模系统 (来自3.txt)：词汇池、节奏波动历史、虚词率历史、雷达历史
- DNA特征翻译为自然语言指令
- 声音特质分析 (来自7-mimiai.txt)：基于标点符号分析叙述声音
"""
import collections
import random
import re
import numpy as np
from typing import Dict, List, Union
from collections import Counter


class EnhancedMimicryEngine:
    def __init__(self):
        self.reset()  # 保留文档2的初始化逻辑

    def reset(self):
        """重置所有状态 (严格隔离模式 + 文档1的完善初始化 + DNA建模系统)"""
        self.learned_docs = 0  # 文档1的关键修复：显式初始化

        # 🔥 核心 DNA 矩阵 (来自3.txt)
        self.dna_matrix = {
            "vocab_pool": Counter(),  # 词池
            "rhythm_stats": [],  # 节奏波动历史
            "particle_ratios": [],  # 虚词率历史
            "punctuation_counts": Counter(),  # 🔥 新增：标点符号统计 (用于声音特质分析)
            "radar_history": {k: [] for k in ["Logic", "Creativity", "Emotion", "Critical", "Struct", "Depth"]}
        }

        self.style_matrix = {
            # 文档1核心属性
            "vocabulary": Counter(),  # 高频词库
            "tone_markers": Counter(),  # 语气特征
            "sentence_templates": [],  # 句式模板
            "sentence_stats": {  # 句子统计数据
                "total_avg_len": 0,
                "count": 0
            },
            "punctuation_profile": Counter(),  # 标点使用习惯
            "sentence_structures": Counter(),  # 句式结构统计
            # 文档2核心属性（保留雷达数据聚合功能）
            "radar_stats": {
                "Logic": 0, "Creativity": 0, "Emotion": 0,
                "Critical": 0, "Struct": 0, "Depth": 0,
                "count": 0
            }
        }
        print("🔄 [Mimicry] 引擎已重置 (包含DNA建模系统+声音特质分析)")  # 文档1的日志提示

    # ==========================================
    # 🔥 核心方法：吞噬分析结果 (整合文档1+文档2+DNA建模全部逻辑)
    # ==========================================
    def ingest(self, analysis_result: Dict):
        """
        吞噬文档分析结果，聚合数据（保留文档2雷达功能 + 文档1完善处理 + DNA建模）
        支持原始风格矩阵和原子级DNA分析结果
        """
        if not analysis_result:
            return

        # 文档计数增加
        self.learned_docs += 1
        summary = analysis_result.get('semantic_summary', {})
        dna = analysis_result.get("style_dna", {})

        # 🔥 获取原子级DNA分析结果 (新增)
        atomic_dna = analysis_result.get("atomic_dna", {})
        atomic_dna_signature = atomic_dna.get("dna_signature", {})
        atomic_radar = atomic_dna.get("atomic_radar_metrics", {})

        # ==========================================
        # 文档2的核心逻辑（保留不删）
        # ==========================================
        # 1. 词汇聚合（用文档1的乱码过滤逻辑优化）
        raw_keywords = summary.get("keywords", {})
        clean_keywords = {}
        # 文档1的增强过滤：支持dict/list类型 + 乱码清洗
        if isinstance(raw_keywords, dict):
            for k, v in raw_keywords.items():
                k_str = str(k)
                if len(k_str) > 1 and re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9]+$', k_str):
                    clean_keywords[k_str] = float(v)
        elif isinstance(raw_keywords, list):
            for k in raw_keywords:
                k_str = str(k)
                if len(k_str) > 1 and re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9]+$', k_str):
                    clean_keywords[k_str] = 1.0
        self.style_matrix["vocabulary"].update(clean_keywords)

        # 2. 句法 DNA 聚合 (移动平均)
        current_avg = dna.get("avg_sentence_length", 20)
        prev_avg = self.style_matrix["sentence_stats"]["total_avg_len"]
        n = self.style_matrix["sentence_stats"]["count"]
        # 增量平均公式（保留文档2逻辑）
        new_avg = (prev_avg * n + current_avg) / (n + 1) if n != 0 else current_avg
        self.style_matrix["sentence_stats"]["total_avg_len"] = new_avg
        self.style_matrix["sentence_stats"]["count"] += 1

        # 3. 标点聚合
        punct = dna.get("punctuation_profile", {})
        self.style_matrix["punctuation_profile"].update(punct)
        # 🔥 同时更新DNA矩阵中的标点统计
        self.dna_matrix["punctuation_counts"].update(punct)

        # 4. 六维雷达聚合 (文档2核心功能，保留不删)
        radar = analysis_result.get("radar_metrics", {})
        r_stats = self.style_matrix["radar_stats"]
        r_count = r_stats["count"]
        # 对6个维度分别计算移动平均
        for key in ["Logic", "Creativity", "Emotion", "Critical", "Struct", "Depth"]:
            curr_val = radar.get(key, 50)
            prev_val = r_stats[key]
            r_stats[key] = (prev_val * r_count + curr_val) / (r_count + 1) if r_count != 0 else curr_val
        r_stats["count"] += 1

        # ==========================================
        # 文档1的增强逻辑（修复功能，补充完善）
        # ==========================================
        # 1. 提取语气特征（修复仪表盘风格画像）
        tone = summary.get('tone', '理性客观')
        if tone:
            self.style_matrix["tone_markers"][tone] += 1

        # 2. 提取句式模板（修复仿写功能）
        patterns = summary.get('patterns', [])
        if patterns:
            self.style_matrix["sentence_templates"].extend(patterns)

        # 3. 吸收句式结构
        structs = summary.get('sentence_structures', {})
        if structs:
            self.style_matrix["sentence_structures"].update(structs)

        # ==========================================
        # 🔥 DNA建模系统融合 (来自3.txt)
        # ==========================================
        # 1. 词汇融合到DNA词池
        self.dna_matrix["vocab_pool"].update(clean_keywords)

        # 2. 节奏DNA融合
        if "rhythm_volatility" in atomic_dna_signature:
            rhythm_val = atomic_dna_signature.get("rhythm_volatility", 0)
            self.dna_matrix["rhythm_stats"].append(rhythm_val)

        # 3. 虚词率DNA融合
        if "particle_ratio" in atomic_dna_signature:
            particle_val = atomic_dna_signature.get("particle_ratio", 0)
            self.dna_matrix["particle_ratios"].append(particle_val)

        # 4. 雷达数据融合到DNA历史
        # 优先使用原子级雷达数据，如果不存在则使用常规雷达数据
        if atomic_radar:
            for key in self.dna_matrix["radar_history"]:
                if key in atomic_radar:
                    self.dna_matrix["radar_history"][key].append(atomic_radar[key])
                else:
                    # 如果没有原子级数据，使用默认值50
                    self.dna_matrix["radar_history"][key].append(50)
        elif radar:  # 使用常规雷达数据
            # 需要映射键名：原radar_metrics使用中文键名
            key_mapping = {
                "逻辑性": "Logic",
                "创造力": "Creativity",
                "同理心": "Emotion",
                "知识广度": "Critical",  # 近似映射
                "记忆深度": "Depth",
                "执行力": "Struct"  # 近似映射
            }
            for cn_key, en_key in key_mapping.items():
                if cn_key in radar and en_key in self.dna_matrix["radar_history"]:
                    # 将0-1的浮点数转换为0-100的整数
                    val = int(radar[cn_key] * 100) if isinstance(radar[cn_key], (int, float)) else 50
                    self.dna_matrix["radar_history"][en_key].append(val)

        # 日志输出（文档1的完善提示 + DNA建模信息）
        print(f"📊 [Mimicry] 已吞噬文档 #{self.learned_docs}: {len(clean_keywords)} 个关键词，平均句长: {new_avg:.1f}")
        print(
            f"🧬 [DNA建模] 节奏波动样本: {len(self.dna_matrix['rhythm_stats'])}, 虚词率样本: {len(self.dna_matrix['particle_ratios'])}")

    # ==========================================
    # 文档2核心方法：获取雷达数据（保留不删）
    # ==========================================
    def get_radar_data(self):
        """获取当前的平均雷达数据 (供 UI 调用)"""
        stats = self.style_matrix["radar_stats"]
        if stats["count"] == 0:
            return {}  # 返回空，UI会处理

        return {
            "Logic": int(stats["Logic"]),
            "Creativity": int(stats["Creativity"]),
            "Emotion": int(stats["Emotion"]),
            "Critical": int(stats["Critical"]),
            "Struct": int(stats["Struct"]),
            "Depth": int(stats["Depth"])
        }

    # ==========================================
    # 🔥 新增方法：获取DNA雷达数据 (来自3.txt)
    # ==========================================
    def get_dna_radar_data(self):
        """计算平均DNA雷达值"""
        if self.learned_docs == 0:
            return {}

        avg_radar = {}
        for k, v_list in self.dna_matrix["radar_history"].items():
            if v_list:
                # 计算平均值并转换为整数
                avg_radar[k] = int(sum(v_list) / len(v_list))
            else:
                avg_radar[k] = 50  # 默认值

        return avg_radar

    # ==========================================
    # 文档1的增强方法（全部保留，修复功能）
    # ==========================================
    def load_from_knowledge_base(self, kb_data: Dict) -> int:
        """
        从知识库恢复记忆
        返回恢复的文档数量
        """
        count = 0
        docs = kb_data.get("documents", {})
        # 重置引擎
        self.reset()
        for doc_name, doc_data in docs.items():
            try:
                # 恢复词汇
                kws = doc_data.get("keywords", {})
                if isinstance(kws, dict):
                    # 过滤乱码（文档1的增强逻辑）
                    clean_kws = {}
                    for k, v in kws.items():
                        k_str = str(k)
                        if len(k_str) > 1 and re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9]+$', k_str):
                            clean_kws[k_str] = v
                    if clean_kws:
                        self.style_matrix["vocabulary"].update(clean_kws)
                        self.dna_matrix["vocab_pool"].update(clean_kws)  # 🔥 同时更新DNA词池
                        count += 1
            except Exception as e:
                print(f"⚠️ [Mimicry] 恢复文档 {doc_name} 时出错: {e}")
        # 更新学习文档计数
        self.learned_docs = count
        print(f"📂 [Mimicry] 从知识库恢复了 {count} 个文档的记忆")
        return count

    def get_style_stats(self) -> Dict:
        """
        获取风格统计信息，用于仪表盘显示
        返回包含各种统计数据的字典
        """
        stats = {
            "learned_docs": self.learned_docs,
            "vocabulary_size": len(self.style_matrix["vocabulary"]),
            "tone": "未定义",
            "avg_sentence_length": self.style_matrix["sentence_stats"]["total_avg_len"],
            "top_keywords": [],
            "top_punctuation": [],
            "sentence_templates_count": len(self.style_matrix["sentence_templates"]),
            "radar_data": self.get_radar_data(),  # 整合文档2的雷达数据到仪表盘
            "dna_radar_data": self.get_dna_radar_data(),  # 🔥 新增DNA雷达数据
            "dna_stats": {  # 🔥 新增DNA统计
                "rhythm_samples": len(self.dna_matrix["rhythm_stats"]),
                "particle_samples": len(self.dna_matrix["particle_ratios"]),
                "avg_rhythm": 0,
                "avg_particle": 0
            }
        }

        # 🔥 计算DNA统计平均值
        if self.dna_matrix["rhythm_stats"]:
            stats["dna_stats"]["avg_rhythm"] = round(
                sum(self.dna_matrix["rhythm_stats"]) / len(self.dna_matrix["rhythm_stats"]), 2)
        if self.dna_matrix["particle_ratios"]:
            stats["dna_stats"]["avg_particle"] = round(
                sum(self.dna_matrix["particle_ratios"]) / len(self.dna_matrix["particle_ratios"]), 4)

        # 获取主要语气
        if self.style_matrix["tone_markers"]:
            tone_items = self.style_matrix["tone_markers"].most_common(1)
            if tone_items:
                stats["tone"] = tone_items[0][0]
        # 获取前10个关键词
        if self.style_matrix["vocabulary"]:
            stats["top_keywords"] = [
                {"word": w, "count": c}
                for w, c in self.style_matrix["vocabulary"].most_common(10)
            ]
        # 获取标点使用情况
        if self.style_matrix["punctuation_profile"]:
            stats["top_punctuation"] = [
                {"symbol": p, "count": c}
                for p, c in self.style_matrix["punctuation_profile"].most_common(5)
            ]
        return stats

    def generate_mimicry_prompt(self, topic: str) -> str:
        """
        生成用于仿写的具体提示
        :param topic: 仿写主题
        :return: 仿写提示
        """
        base_prompt = self.generate_system_prompt()
        # 随机选择一个句式模板作为示例
        example_template = ""
        if self.style_matrix["sentence_templates"]:
            example_template = random.choice(self.style_matrix["sentence_templates"])
        mimicry_prompt = (
            f"{base_prompt}\n\n"
            f"【创作任务】\n"
            f"请以'{topic}'为主题，使用上述风格进行创作。\n"
        )
        if example_template:
            mimicry_prompt += f"【参考句式】\n{example_template}\n\n"
        mimicry_prompt += (
            f"【输出要求】\n"
            f"1. 字数在300-500字之间\n"
            f"2. 保持风格一致性\n"
            f"3. 直接输出内容，无需说明"
        )
        return mimicry_prompt

    def export_style_matrix(self) -> Dict:
        """
        导出风格矩阵，用于人格保存
        注意：Counter 对象需要转为 dict，包含文档2的雷达数据和DNA矩阵
        """
        export_data = {}
        for key, value in self.style_matrix.items():
            if isinstance(value, Counter):
                export_data[key] = dict(value)
            elif isinstance(value, list):
                export_data[key] = value.copy()
            elif isinstance(value, dict):
                export_data[key] = value.copy()
            else:
                export_data[key] = value

        # 🔥 导出DNA矩阵
        dna_export = {}
        for key, value in self.dna_matrix.items():
            if isinstance(value, Counter):
                dna_export[key] = dict(value)
            elif isinstance(value, list):
                dna_export[key] = value.copy()
            elif isinstance(value, dict):
                dna_export[key] = {k: v.copy() if isinstance(v, list) else v for k, v in value.items()}
            else:
                dna_export[key] = value

        export_data["dna_matrix"] = dna_export

        # 添加元数据
        export_data["_meta"] = {
            "learned_docs": self.learned_docs,
            "export_time": "当前时间",  # 实际使用时应该用 datetime
            "version": "MimicryEngine v3.0 (DNA建模增强版+声音特质分析)"
        }
        return export_data

    def import_style_matrix(self, matrix_data: Dict) -> bool:
        """
        导入风格矩阵，用于人格加载（支持文档2的雷达数据导入 + DNA矩阵导入）
        """
        try:
            # 导入style_matrix
            for key in self.style_matrix.keys():
                if key in matrix_data:
                    if key == "vocabulary" and isinstance(matrix_data[key], dict):
                        self.style_matrix["vocabulary"] = Counter(matrix_data[key])
                    elif key == "tone_markers" and isinstance(matrix_data[key], dict):
                        self.style_matrix["tone_markers"] = Counter(matrix_data[key])
                    elif key == "punctuation_profile" and isinstance(matrix_data[key], dict):
                        self.style_matrix["punctuation_profile"] = Counter(matrix_data[key])
                    elif key == "sentence_structures" and isinstance(matrix_data[key], dict):
                        self.style_matrix["sentence_structures"] = Counter(matrix_data[key])
                    # 支持文档2的雷达数据导入
                    elif key == "radar_stats" and isinstance(matrix_data[key], dict):
                        self.style_matrix["radar_stats"] = matrix_data[key].copy()
                    else:
                        self.style_matrix[key] = matrix_data[key]

            # 🔥 导入DNA矩阵
            if "dna_matrix" in matrix_data:
                dna_data = matrix_data["dna_matrix"]
                for key in self.dna_matrix.keys():
                    if key in dna_data:
                        if key == "vocab_pool" and isinstance(dna_data[key], dict):
                            self.dna_matrix["vocab_pool"] = Counter(dna_data[key])
                        elif key == "rhythm_stats" and isinstance(dna_data[key], list):
                            self.dna_matrix["rhythm_stats"] = dna_data[key].copy()
                        elif key == "particle_ratios" and isinstance(dna_data[key], list):
                            self.dna_matrix["particle_ratios"] = dna_data[key].copy()
                        elif key == "punctuation_counts" and isinstance(dna_data[key], dict):
                            self.dna_matrix["punctuation_counts"] = Counter(dna_data[key])
                        elif key == "radar_history" and isinstance(dna_data[key], dict):
                            self.dna_matrix["radar_history"] = {k: v.copy() if isinstance(v, list) else v for k, v in
                                                                dna_data[key].items()}
                        else:
                            self.dna_matrix[key] = dna_data[key]

            # 更新学习文档计数
            if "_meta" in matrix_data and "learned_docs" in matrix_data["_meta"]:
                self.learned_docs = matrix_data["_meta"]["learned_docs"]
            print(f"✅ [Mimicry] 已导入风格矩阵，学习文档: {self.learned_docs}")
            return True
        except Exception as e:
            print(f"❌ [Mimicry] 导入风格矩阵失败: {e}")
            return False

    # ==========================================
    # 🔥 生成系统提示（整合文档1修复 + 文档2核心 + DNA建模翻译 + 7的声音特质分析）
    # ==========================================
    def generate_system_prompt(self):
        """
        生成拟态 Prompt（整合文档1的完善逻辑 + 文档2核心特征 + DNA建模翻译 + 7的声音特质分析）
        核心：将数学特征翻译为自然语言指令 (DNA -> Prompt)
        """
        # 如果没有数据，返回默认提示
        if self.learned_docs == 0 or not self.style_matrix["vocabulary"]:
            return "你是一个通用的 AI 助手，请用客观、专业的语气回答。"

        # ==========================================
        # 文档2的核心特征提取（保留不删）
        # ==========================================
        top_words = [w for w, c in self.style_matrix["vocabulary"].most_common(15)]
        words_str = "、".join(top_words)
        avg_len = self.style_matrix["sentence_stats"]["total_avg_len"]
        if avg_len < 15:
            len_inst = "务必使用短促、有力的短句。"
        elif avg_len > 40:
            len_inst = "多使用复杂的长难句、排比句，体现深度。"
        else:
            len_inst = "长短句结合，保持自然节奏。"
        punct_counter = self.style_matrix["punctuation_profile"]
        top_punct = [p for p, c in punct_counter.most_common(3)]
        punct_str = " ".join(top_punct)

        # ==========================================
        # 文档1的增强特征（修复风格画像 + 仿写功能）
        # ==========================================
        # 语气特征
        tone = "专业理性"
        if self.style_matrix["tone_markers"]:
            tone_items = self.style_matrix["tone_markers"].most_common(1)
            if tone_items:
                tone = tone_items[0][0]

        # 句式模板
        templates = self.style_matrix["sentence_templates"]
        template_str = ""
        if templates:
            sample_count = min(2, len(templates))
            samples = random.sample(templates, sample_count) if len(templates) > sample_count else templates
            template_str = f"请参考以下句式结构进行仿写：\n" + "\n".join([f"- {s}" for s in samples])

        # ==========================================
        # 🔥 DNA建模翻译 (来自3.txt)
        # ==========================================
        # 1. 计算DNA平均特征
        rhythms = self.dna_matrix["rhythm_stats"]
        avg_rhythm = sum(rhythms) / len(rhythms) if rhythms else 0

        particles = self.dna_matrix["particle_ratios"]
        avg_particle = sum(particles) / len(particles) if particles else 0

        # 2. 动态生成DNA风格指令
        # A. 节奏DNA指令
        if avg_rhythm > 15:
            rhythm_dna_inst = "句式极具张力，务必**长短句交替使用**，形成跌宕起伏的阅读节奏。"
        elif avg_rhythm < 5:
            rhythm_dna_inst = "句式工整、平稳，多使用**长度相当的排比句或对偶句**，保持克制。"
        else:
            rhythm_dna_inst = "行文流畅自然，长短适中。"

        # B. 语气DNA指令 (虚词率)
        if avg_particle > 0.08:
            tone_dna_inst = "语气亲切、口语化，多使用'呢、吧、啊'等语气助词，拉近距离。"
        elif avg_particle < 0.03:
            tone_dna_inst = "语气洗练、干脆，**严格控制'的、地、得'及语气词的使用**，体现公文/学术的严谨性。"
        else:
            tone_dna_inst = "语气平和，不偏不倚。"

        # C. 词汇DNA
        dna_top_words = [w for w, c in self.dna_matrix["vocab_pool"].most_common(20)]
        dna_words_str = "、".join(dna_top_words)

        # ==========================================
        # 🔥 声音特质分析 (来自7-mimiai.txt)
        # ==========================================
        voice_instruction = ""
        # 简单判定：感叹号和问号多 -> 热情澎湃；句号多、长句多 -> 冷静克制
        punc_counts = self.dna_matrix.get("punctuation_counts", Counter())
        total_punc = sum(punc_counts.values())
        if total_punc > 0:
            # 统计感叹号和问号（包括中文和英文）
            emotional_ratio = (punc_counts.get('！', 0) + punc_counts.get('？', 0) +
                               punc_counts.get('!', 0) + punc_counts.get('?', 0)) / total_punc
            if emotional_ratio > 0.1:
                voice_instruction = "你的声音是**热情澎湃的倡导者**。多用设问、反问，情绪饱满，建立强烈的共鸣。"
            else:
                voice_instruction = "你的声音是**冷静克制的观察者**。用词精准、客观，不随意宣泄情绪，建立专业信任感。"

        # 风格指令整合
        style_instruction = f"核心词汇场：[{words_str}]，情感基调：{tone}，句式风格：{len_inst}"

        # ==========================================
        # 整合最终提示（保留文档2核心 + 文档1完善要求 + DNA建模翻译 + 声音特质）
        # ==========================================
        prompt = (
            "=== 🧬 DNA 拟态系统已激活 ===\n"
            f"目标作者画像：\n"
            f"1. {style_instruction}\n"
            f"2. **叙述声音**：{voice_instruction}\n"
            f"3. **写作心法**：{rhythm_dna_inst}\n"
            f"\n【详细特征】\n"
            f"- 平均句长：{avg_len:.1f} 字\n"
            f"- 标点特征：[{punct_str}]\n"
            f"- 节奏DNA波动率：{avg_rhythm:.1f}\n"
            f"- 虚词密度：{avg_particle:.3f}\n"
            f"- DNA词汇场：[{dna_words_str}]\n"
        )

        # 添加句式模板
        if template_str:
            prompt += f"\n【句式参考】\n{template_str}\n"

        # DNA认知模式指令
        prompt += (
            f"\n【DNA认知模式】\n"
            f"1. 完全沉浸于该作者的思维逻辑中，不要暴露出 AI 的机械感。\n"
            f"2. 模仿其内在的思考节奏和表达习惯，不仅仅是表面的词汇替换。\n"
            f"3. 保持风格的一致性，包括节奏波动、虚词使用和声音特质。\n"
        )

        # 文档1的创作要求（增强风格一致性）
        prompt += (
            f"\n【创作要求】\n"
            f"1. 禁止出现'作为AI'、'根据要求'等表述，直接输出内容。\n"
            f"2. 字数充实，逻辑严密，保持风格一致性。\n"
            f"3. 必须按照当前人格的方式写作，完全沉浸于指定风格中。\n"
            f"4. 输出时使用符合该风格的标点习惯和句式结构。\n"
            f"5. 注意节奏控制、虚词使用和声音特质，全面符合DNA建模特征。\n"
            f"6. 根据声音特质调整表达方式，保持叙述声音的一致性。"
        )
        return prompt

    # ==========================================
    # 🔥 新增方法：生成DNA专用提示 (来自3.txt)
    # ==========================================
    def generate_dna_prompt(self):
        """
        生成专门基于DNA建模的提示
        用于需要更精确风格模仿的场景
        """
        if self.learned_docs == 0:
            return "你是一个专业的助手。请保持客观、准确。"

        # 计算DNA平均特征
        rhythms = self.dna_matrix["rhythm_stats"]
        avg_rhythm = sum(rhythms) / len(rhythms) if rhythms else 0

        particles = self.dna_matrix["particle_ratios"]
        avg_particle = sum(particles) / len(particles) if particles else 0

        # 词汇场
        dna_top_words = [w for w, c in self.dna_matrix["vocab_pool"].most_common(20)]
        words_str = "、".join(dna_top_words)

        # 声音特质分析
        voice_instruction = ""
        punc_counts = self.dna_matrix.get("punctuation_counts", Counter())
        total_punc = sum(punc_counts.values())
        if total_punc > 0:
            emotional_ratio = (punc_counts.get('！', 0) + punc_counts.get('？', 0) +
                               punc_counts.get('!', 0) + punc_counts.get('?', 0)) / total_punc
            if emotional_ratio > 0.1:
                voice_instruction = "声音是**热情澎湃的倡导者**。多用设问、反问，情绪饱满，建立强烈的共鸣。"
            else:
                voice_instruction = "声音是**冷静克制的观察者**。用词精准、客观，不随意宣泄情绪，建立专业信任感。"

        # 动态生成风格指令
        # 节奏指令
        if avg_rhythm > 15:
            rhythm_inst = "句式极具张力，务必**长短句交替使用**，形成跌宕起伏的阅读节奏。"
        elif avg_rhythm < 5:
            rhythm_inst = "句式工整、平稳，多使用**长度相当的排比句或对偶句**，保持克制。"
        else:
            rhythm_inst = "行文流畅自然，长短适中。"

        # 语气指令 (虚词率)
        if avg_particle > 0.08:
            tone_inst = "语气亲切、口语化，多使用'呢、吧、啊'等语气助词，拉近距离。"
        elif avg_particle < 0.03:
            tone_inst = "语气洗练、干脆，**严格控制'的、地、得'及语气词的使用**，体现公文/学术的严谨性。"
        else:
            tone_inst = "语气平和，不偏不倚。"

        return f"""
【终极拟态模式 (Ultimate Mimicry)】
已激活目标作者的写作 DNA 模型。请严格执行以下特征：

1. **核心词汇场**：高频使用以下词汇或同类词：[{words_str}]。
2. **叙述声音**：{voice_instruction}
3. **节奏 DNA**：{rhythm_inst} (波动率: {avg_rhythm:.1f})
4. **语气 DNA**：{tone_inst} (虚词密度: {avg_particle:.3f})
5. **认知模式**：完全沉浸于该作者的思维逻辑中，不要暴露出 AI 的机械感。
"""