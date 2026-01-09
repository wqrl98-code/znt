# -*- coding: utf-8 -*-
"""
路径配置中心 (Path Configuration) - 生产环境完整版
负责：定义系统所有的工作目录结构，确保文件存取路径统一
"""
import os

# 1. 自动获取项目根目录 (config文件夹的上级目录)
# __file__ 是当前文件路径，dirname两次回到项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2. 定义工作区根目录 (所有数据存储在这里，不污染代码目录)
WORKSPACE_ROOT = os.path.join(BASE_DIR, "ATHENA_WORKSPACE")

# 3. 🔥 核心目录结构字典 (IOManager 依赖此变量)
# 这是您报错缺失的部分，必须完整定义
ATHENA_DIRS = {
    "root": WORKSPACE_ROOT,
    "inputs": os.path.join(WORKSPACE_ROOT, "Inputs"),  # 存放用户导入的原始文档
    "outputs": os.path.join(WORKSPACE_ROOT, "Outputs"),  # 存放导出的报告、分析结果
    "database": os.path.join(WORKSPACE_ROOT, "Database"),  # 数据库根目录
    "knowledge_base": os.path.join(WORKSPACE_ROOT, "Database", "KnowledgeBase"),  # 知识库 JSON 存储
    "personas": os.path.join(WORKSPACE_ROOT, "Database", "Personas"),  # 人格矩阵 JSON 存储
    "logs": os.path.join(WORKSPACE_ROOT, "Logs"),  # 系统运行日志
    "cache": os.path.join(WORKSPACE_ROOT, "Cache"),  # 临时缓存 (如图片生成)
    "plugins": os.path.join(WORKSPACE_ROOT, "Plugins"),  # 扩展插件目录
    "texts": os.path.join(WORKSPACE_ROOT, "Texts"),  # 纯文本文件存储
    "backups": os.path.join(WORKSPACE_ROOT, "Backups"),  # 备份目录
    "temp": os.path.join(WORKSPACE_ROOT, "Temp")  # 临时文件目录
}


# 4. 兼容性辅助类 (Path Manager)
# 某些旧模块可能仍通过 PATHS.get_path() 调用，保留此类以防万一
class PathManager:
    def __init__(self):
        self.directories = ATHENA_DIRS
        self._ensure_structure()

    def _ensure_structure(self):
        """初始化时自动创建所有目录"""
        for path in self.directories.values():
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                except Exception as e:
                    print(f"❌ [Paths] 创建目录失败 {path}: {e}")

    def get_path(self, dir_key, filename=None):
        """
        获取指定模块的完整路径
        :param dir_key: 目录键名 (如 'inputs', 'personas')
        :param filename: 文件名 (可选)
        :return: 完整绝对路径
        """
        # 如果键不存在，默认回退到 outputs 防止报错
        base_path = self.directories.get(dir_key, self.directories["outputs"])

        if filename:
            return os.path.join(base_path, filename)
        return base_path

    def get_workspace_root(self):
        return WORKSPACE_ROOT


# 5. 全局单例实例
# 供其他模块直接 import PATHS 使用
PATHS = PathManager()