# -*- coding: utf-8 -*-
"""
终极雅典娜智能系统 (Athena Genesis)
根包初始化
"""

__version__ = '20.1.0'
__author__ = 'User 92078 Enhanced Version'
__all__ = []

# 尝试导出核心组件，允许部分组件缺失（增强鲁棒性）
try:
    from _backup_legacy.main_window import AthenaGenesisWindow
    __all__.append('AthenaGenesisWindow')
except ImportError:
    pass

try:
    from engines.athena_brain import AthenaBrain
    __all__.append('AthenaBrain')
except ImportError:
    pass

try:
    from engines.document_analyzer import DocumentIntelligenceAnalyzer
    __all__.append('DocumentIntelligenceAnalyzer')
except ImportError:
    pass

try:
    from core.knowledge_base import KnowledgeBase
    __all__.append('KnowledgeBase')
except ImportError:
    pass