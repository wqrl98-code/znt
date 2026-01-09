# -*- coding: utf-8 -*-
"""
Athena Genesis 配置文件 - 修复完整版
修复：确保所有必需的属性都存在，包括 PATHS、VERSION 等
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any


# ==========================================
# 关键修复：PathConfig 类
# ==========================================
class PathConfig:
    def __init__(self):
        # 获取项目根目录
        try:
            from config.paths import WORKSPACE_ROOT
            self.base_dir = WORKSPACE_ROOT
        except ImportError:
            # 如果没有配置，则使用当前目录下的 ATHENA_WORKSPACE
            self.base_dir = os.path.join(os.getcwd(), 'ATHENA_WORKSPACE')

        # 确保工作区目录存在
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

        # 定义所有子目录路径
        self.directories = {
            'workspace': self.base_dir,
            'inputs': os.path.join(self.base_dir, 'Inputs'),
            'knowledge_base': os.path.join(self.base_dir, 'KnowledgeBase'),
            'personas': os.path.join(self.base_dir, 'Personas'),
            'persona_spaces': os.path.join(self.base_dir, 'PersonaSpaces'),
            'conversations': os.path.join(self.base_dir, 'Conversations'),
            'exports': os.path.join(self.base_dir, 'Exports'),
            'logs': os.path.join(self.base_dir, 'Logs'),
            'temp': os.path.join(self.base_dir, 'Temp'),
            'cache': os.path.join(self.base_dir, 'Cache')
        }

        # 资源路径
        self.resources = {
            'app_icon': os.path.join(os.path.dirname(__file__), '..', 'resources', 'icon.png'),
            'styles': os.path.join(os.path.dirname(__file__), '..', 'resources', 'styles.qss')
        }

        # 自动创建目录
        self._create_dirs()

    def _create_dirs(self):
        for key, path in self.directories.items():
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                    print(f"✅ [Config] 已创建目录: {path}")
                except Exception as e:
                    print(f"❌ [Config] 目录创建失败 {path}: {e}")

    def get(self, category, key, default=None):
        """通用获取方法"""
        if category == 'directories':
            return self.directories.get(key, default)
        elif category == 'resources':
            return self.resources.get(key, default)
        return default


@dataclass
class AppSettings:
    """应用程序设置"""

    # ==========================
    # 🔥 核心补丁：补全缺失的基础信息
    # ==========================
    APP_NAME: str = "Athena Genesis"
    VERSION: str = "20.1"  # <--- 修复：添加缺失的VERSION属性
    APP_VERSION: str = "20.1.0"
    AUTHOR: str = "User 92078 Enhanced Version"
    COPYRIGHT: str = "Athena Project"
    DEBUG: bool = False  # 添加DEBUG标志

    # UI设置
    WINDOW_WIDTH: int = 1600
    WINDOW_HEIGHT: int = 900
    UI_STYLE: str = "dark"
    FONT_FAMILY: str = "Microsoft YaHei"
    FONT_SIZE: int = 10

    # 工作目录
    try:
        from config.paths import WORKSPACE_ROOT
        WORKSPACE_ROOT = WORKSPACE_ROOT
    except ImportError:
        WORKSPACE_ROOT = os.path.join(os.getcwd(), 'ATHENA_WORKSPACE')

    # 🔥🔥🔥 核心修复：添加 PATHS 属性 🔥🔥🔥
    def __post_init__(self):
        """dataclass 初始化后调用的方法"""
        self.PATHS = PathConfig()

    # 日志设置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 性能设置
    MAX_WORKERS: int = 4
    CHUNK_SIZE: int = 1024 * 1024  # 1MB
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB

    # 生成设置
    DEFAULT_CREATIVITY: int = 50
    MAX_CONTENT_LENGTH: int = 5000
    MIN_CONTENT_LENGTH: int = 100

    # AI设置
    MIN_TRAINING_DOCS: int = 1
    MAX_TRAINING_DOCS: int = 100
    TFIDF_MAX_FEATURES: int = 5000
    KEYWORD_TOP_K: int = 20

    # Ollama 设置
    USE_LLM: bool = True
    OLLAMA_API_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"
    OLLAMA_TIMEOUT: int = 120

    # 支持的文件格式
    SUPPORTED_EXTENSIONS: Dict[str, List[str]] = field(default_factory=lambda: {
        'excel': ['.xlsx', '.xls', '.xlsm'],
        'pdf': ['.pdf'],
        'word': ['.docx', '.doc'],
        'text': ['.txt', '.md', '.py', '.json', '.xml', '.yaml', '.yml', '.ini', '.log'],
        'csv': ['.csv'],
        'html': ['.html', '.htm', '.xhtml'],
        'ppt': ['.pptx', '.ppt'],
        'image': ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp']
    })

    # 大脑模式配置
    BRAIN_MODES: dict = field(default_factory=lambda: {
        "default_mode": "chat",
        "available_modes": ["chat", "simple_qa", "deep_write"],
        "mode_descriptions": {
            "chat": "通用对话模式，本地知识优先",
            "simple_qa": "简单问答模式，快速联网搜索",
            "deep_write": "深度研报模式，多轮审查生成"
        }
    })

    # 审查配置
    EDITOR_SETTINGS: dict = field(default_factory=lambda: {
        "default_check_mode": "full",  # quick/full/strict
        "auto_quick_check": True,
        "save_memory": True,
        "max_issues_per_check": 10
    })

    # 学习专员配置
    RESEARCHER_SETTINGS: dict = field(default_factory=lambda: {
        "max_parallel_searches": 3,
        "search_timeout": 30,
        "min_context_length": 100,
        "enable_knowledge_gap_analysis": True
    })

    # 新增：Web搜索配置
    WEB_SEARCH: dict = field(default_factory=lambda: {
        "enabled": True,
        "search_engine": "google",
        "max_results": 5,
        "timeout": 10
    })

    # 新增：缓存配置
    CACHE: dict = field(default_factory=lambda: {
        "enabled": True,
        "max_size_mb": 100,
        "ttl_hours": 24
    })

    # 为了防止以后还有类似的报错，建议加上这个通用获取方法
    def get(self, key, default=None):
        """安全获取属性值"""
        return getattr(self, key, default)


@dataclass
class ColorScheme:
    """颜色方案"""
    PRIMARY: str = "#1a1a1a"
    SECONDARY: str = "#252525"
    ACCENT: str = "#4fc3f7"
    TEXT: str = "#e0e0e0"
    BORDER: str = "#444444"
    SUCCESS: str = "#00c853"
    WARNING: str = "#ffd600"
    ERROR: str = "#d50000"

    # 聊天消息颜色
    CHAT_COLORS: dict = field(default_factory=lambda: {
        "user": "#2c5282",
        "ai": "#234e52",
        "system": "#4a5568",
        "error": "#742a2a",
        "warning": "#744210",
        "success": "#22543d"
    })


# ==========================================
# 关键：必须实例化，否则无法被 import
# ==========================================
SETTINGS = AppSettings()
COLORS = ColorScheme()

# 添加一些便捷方法
if __name__ == "__main__":
    # 测试配置
    print(f"✅ 配置加载成功:")
    print(f"  应用名称: {SETTINGS.APP_NAME}")
    print(f"  版本: {SETTINGS.VERSION}")
    print(f"  工作区: {SETTINGS.WORKSPACE_ROOT}")
    print(f"  路径配置: {SETTINGS.PATHS.directories}")

    # 测试PATHS属性
    if hasattr(SETTINGS, 'PATHS'):
        print(f"✅ PATHS属性存在")
        print(f"  知识库目录: {SETTINGS.PATHS.get('directories', 'knowledge_base')}")
    else:
        print(f"❌ PATHS属性不存在")