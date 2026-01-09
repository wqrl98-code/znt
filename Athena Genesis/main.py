# -*- coding: utf-8 -*-
"""
Athena Genesis - 主程序入口 (架构对齐修复版 v25.0)
Python 3.14+ 兼容版本
修复：ModuleNotFoundError: No module named 'engines.commander'
"""

import sys
import os
import warnings
import types
import shutil
from pathlib import Path

# ==================================================
# 🔧 Python 3.14+ 兼容性补丁
# ==================================================
# 修复 Python 3.14+ 中 distutils 模块可能缺失的问题
try:
    # 尝试导入标准库的 distutils
    import distutils.spawn

    # 使用 shutil.which 替换过时的 find_executable
    distutils.spawn.find_executable = shutil.which
except ImportError:
    # 如果 Python 3.14+ 移除了 distutils，创建兼容层
    fake_distutils = types.ModuleType("distutils")
    fake_spawn = types.ModuleType("distutils.spawn")
    fake_spawn.find_executable = shutil.which
    fake_distutils.spawn = fake_spawn
    sys.modules["distutils"] = fake_distutils
    sys.modules["distutils.spawn"] = fake_spawn

# ==================================================
# 🔇 全局静音设置
# ==================================================
# 系统级警告屏蔽
os.environ["PYTHONWARNINGS"] = "ignore"

# Python 警告过滤器
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 第三方库日志屏蔽
try:
    import logging

    logging.getLogger("GPUtil").setLevel(logging.CRITICAL)
    logging.getLogger("duckduckgo_search").setLevel(logging.CRITICAL)
except Exception:
    pass

# ==================================================
# 🚀 路径配置
# ==================================================
# 确保项目根目录在搜索路径中
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ==================================================
# 🎨 GUI导入
# ==================================================
from PyQt6.QtWidgets import QApplication, QStyleFactory
from PyQt6.QtGui import QFont


# ==================================================
# 🎯 主函数
# ==================================================
def main():
    """应用程序主入口"""
    # 启动日志
    print("=" * 50)
    print("🚀 Athena Genesis 启动中...")
    print(f"📁 工作目录: {PROJECT_ROOT}")
    print("🔧 兼容性补丁: 已启用")
    print("🔇 静音模式: 已激活")
    print("🔧 架构路径: Core Architecture (v25.0)")
    print("=" * 50)

    # 初始化应用
    app = QApplication(sys.argv)

    # 尝试加载应用设置，失败则使用默认名称
    try:
        from config.settings import SETTINGS
        app_name = SETTINGS.APP_NAME
    except ImportError:
        app_name = "Athena Genesis"

    app.setApplicationName(app_name)

    # 设置应用样式
    app.setStyle(QStyleFactory.create("Fusion"))

    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    try:
        # 🔥 关键修复：从 main_window 导入 MainWindow 类
        # 确保 main_window.py 已经更新为使用 core.* 的版本
        from main_window import MainWindow
        window = MainWindow()
        window.show()

        print("✅ 主窗口加载成功")
        print("=" * 50)

        # 进入应用主循环
        sys.exit(app.exec())

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请检查 main_window.py 是否已正确更新，并确保 core 文件夹存在。")
        print("=" * 50)
        input("按任意键退出...")
        sys.exit(1)

    except Exception as e:
        print(f"❌ 运行时错误: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 50)
        input("按任意键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()