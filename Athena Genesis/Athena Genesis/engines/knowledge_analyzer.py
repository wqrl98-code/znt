# -*- coding: utf-8 -*-
"""
知识分析器 - 接口适配版
"""
import os
import re
from typing import Dict, Any, List


class KnowledgeAnalyzer:
    def analyze(self, text: str, semantic_data: Dict = None, file_path: str = None) -> Dict[str, Any]:
        """统一分析接口"""
        if not text: return {}

        # 1. 思考模式分析
        thinking_mode = "混合思维"
        if text.count("例如") > text.count("因此"):
            thinking_mode = "归纳思维 (重案例)"
        elif text.count("因此") > text.count("例如"):
            thinking_mode = "演绎思维 (重逻辑)"

        # 2. 捕捉灵光一现 (金句)
        sparks = []
        sentences = re.split(r'[。！？\n]', text)
        for sent in sentences:
            sent = sent.strip()
            # 简单的金句判断逻辑：包含哲理性词汇且短小精悍
            if 5 < len(sent) < 30 and any(w in sent for w in ['本质', '核心', '原来', '顿悟', '只有', '才']):
                sparks.append(sent)

        # 构建返回结果
        result = {
            "thinking_mode": {"mode": thinking_mode},
            "sparks_of_inspiration": sparks[:3],  # 取前3个
            "depth_score": 0.5 + (0.1 * len(sparks))
        }

        # 添加document_info信息
        if file_path:
            result["document_info"] = {
                "filename": os.path.basename(file_path),
                "filepath": file_path,  # 👈 按照要求添加这一行
            }

        return result

    def deep_analyze(self, text: str, file_path: str = None, semantic_data: Dict = None) -> Dict[str, Any]:
        """深度分析方法，包含完整的文档信息"""
        # 调用分析接口
        analysis_result = self.analyze(text, semantic_data, file_path)

        # 如果已经有document_info（通过analyze方法添加），则直接返回
        if "document_info" in analysis_result:
            return analysis_result

        # 否则创建完整的返回结构
        return {
            "document_info": {
                "filename": os.path.basename(file_path) if file_path else "unknown",
                "filepath": file_path if file_path else "unknown",
            },
            **analysis_result
        }