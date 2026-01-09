import os
import shutil
import sys


def fix_project_structure():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"🔧 正在诊断目录: {base_dir}")

    # 1. 检查并创建 core 文件夹
    core_dir = os.path.join(base_dir, "core")
    if not os.path.exists(core_dir):
        print("⚠️ 没找到 core 文件夹，正在创建...")
        os.makedirs(core_dir)
    else:
        print("✅ core 文件夹存在")

    # 2. 关键：确保 core/__init__.py 存在
    init_file = os.path.join(core_dir, "__init__.py")
    if not os.path.exists(init_file):
        print("❌ 缺少 core/__init__.py (这会导致导入失败)")
        with open(init_file, 'w') as f:
            f.write("# Core package")
        print("✅ 已自动补全 __init__.py")
    else:
        print("✅ __init__.py 存在")

    # 3. 检查并移动 athena_brain.py
    # 可能在根目录，也可能在 engines 目录，我们要把它搬到 core
    target_brain = os.path.join(core_dir, "athena_brain.py")

    # 检查根目录
    root_brain = os.path.join(base_dir, "athena_brain.py")
    if os.path.exists(root_brain):
        print("⚠️ 发现 athena_brain.py 在根目录，正在移动到 core...")
        try:
            if os.path.exists(target_brain): os.remove(target_brain)
            shutil.move(root_brain, target_brain)
            print("✅ 移动成功")
        except Exception as e:
            print(f"❌ 移动失败: {e}")

    # 4. 检查并移动 commander.py
    target_cmdr = os.path.join(core_dir, "commander.py")
    root_cmdr = os.path.join(base_dir, "commander.py")

    if os.path.exists(root_cmdr):
        print("⚠️ 发现 commander.py 在根目录，正在移动到 core...")
        try:
            if os.path.exists(target_cmdr): os.remove(target_cmdr)
            shutil.move(root_cmdr, target_cmdr)
            print("✅ 移动成功")
        except Exception as e:
            print(f"❌ 移动失败: {e}")

    # 5. 最终验证
    print("-" * 30)
    files_in_core = os.listdir(core_dir)
    print(f"📂 core 文件夹内的文件: {files_in_core}")

    required = ["athena_brain.py", "commander.py", "__init__.py"]
    missing = [f for f in required if f not in files_in_core]

    if missing:
        print(f"❌ 仍然缺失关键文件: {missing}")
        print("请检查你是否把这两个文件保存到了别的地方！")
    else:
        print("🎉 结构验证完美！现在应该可以运行 main.py 了。")


if __name__ == "__main__":
    fix_project_structure()
    input("\n按任意键退出...")