# 文件路径: core/io_manager.py
# -*- coding: utf-8 -*-
"""
IO Manager - 终极修复版 + 物理隔离 + EPUB支持 + 全量读取 + 全域文件寻址 (Hybrid)
修复：
1. 物理隔离：文件按人格存储在 Inputs/{PersonaName}/ 子目录下 ✅
2. 模块化解析器加载 + 文件归档 + EPUB电子书解析 ✅
3. AttributeError: epub_support 缺失 ✅
4. 智能格式识别与容错加载 ✅
5. EPUB内容读取不全、章节乱序、短章节丢失问题 ✅
6. 新增：read_full_content - 强制读取全量内容（用于深度生成）✅
7. 新增：smart_find_file - 全域搜索文件，解决加载人格时找不到源文件的问题 ✅
8. 🔥 新增：人格存取健壮性修复 - 解决空文件、损坏JSON、默认值问题 ✅
"""
import os
import json
import shutil
import warnings
import importlib
import glob
from pathlib import Path
from datetime import datetime

# 过滤警告
warnings.filterwarnings("ignore")

# 导入 EPUB 解析所需库
try:
    import fitz  # PyMuPDF

    PDF_SUPPORT = True
except ImportError:
    fitz = None
    PDF_SUPPORT = False

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup

    warnings.filterwarnings("ignore", category=UserWarning, module='ebooklib')
    EPUBLIB_SUPPORT = True
except ImportError:
    ebooklib = epub = BeautifulSoup = None
    EPUBLIB_SUPPORT = False

from config.settings import SETTINGS
from parsers.base_parser import BaseParser


class IOManager:
    """
    IO Manager - 终极稳定版 + 物理隔离 + 全量读取 + 全域文件寻址 + 健壮性修复
    修复：
    1. 物理隔离：文件按人格存储在 Inputs/{PersonaName}/ 子目录下
    2. AttributeError: epub_support 缺失
    3. archive_input 缺失
    4. EPUB内容读取不全、章节乱序、短章节丢失
    5. 新增：read_full_content - 强制读取全量内容（用于深度生成）
    6. 新增：smart_find_file - 全域搜索文件，解决加载人格时找不到源文件的问题
    7. 🔥 新增：人格存取健壮性修复 - 解决空文件、损坏JSON、默认值问题
    包含：模块化解析器加载 + 文件归档(archive_input)功能 + EPUB电子书支持 + 智能格式识别 + 物理隔离
    """

    def __init__(self):
        # 🔥 修复：使用 SETTINGS.PATHS 或动态加载路径配置
        try:
            from config.paths import ATHENA_DIRS
            # 构造 paths 对象以兼容旧代码 self.paths.directories
            self.paths = type('Paths', (), {'directories': ATHENA_DIRS})
        except ImportError:
            # 如果 config.paths 不存在，使用 SETTINGS.PATHS
            self.paths = SETTINGS.PATHS

        # 兼容性处理：确保有 directories 属性
        try:
            self.directories = self.paths.directories
        except AttributeError:
            # 降级处理
            base_dir = os.path.join(os.getcwd(), 'ATHENA_WORKSPACE')
            self.directories = {
                'inputs': os.path.join(base_dir, 'Inputs'),
                'personas': os.path.join(base_dir, 'Database', 'Personas'),
                'knowledge_base': os.path.join(base_dir, 'Database', 'KnowledgeBase')
            }

        # 🔥 关键修复：标记功能支持状态
        self.epub_support = EPUBLIB_SUPPORT
        self.pdf_support = PDF_SUPPORT

        # 确保所有工作目录存在
        self._ensure_directories()

        # 自动加载所有解析器
        self.parsers = self._load_parsers()

    def _ensure_directories(self):
        """确保所有系统目录都存在"""
        for key, path in self.directories.items():
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                except Exception as e:
                    print(f"⚠️ [IO] 创建目录失败 {path}: {e}")

    def _load_parsers(self):
        """动态加载 parsers 目录下的所有解析器"""
        loaded_parsers = []
        # 手动注册列表，确保顺序 (例如 PDF 优先于 Image)
        # 注意：这里使用了局部导入，防止循环依赖
        try:
            from parsers.pdf_parser import PDFParser
            loaded_parsers.append(PDFParser())
            print(f"✅ [IO] 已加载解析器: PDF Parser")
        except ImportError as e:
            print(f"⚠️ [IO] PDF 解析器加载失败: {e}")
            # 如果没有 PDF 解析器，使用内置方法
            if self.pdf_support:
                class BuiltinPDFParser(BaseParser):
                    """内置的简单 PDF 解析器"""

                    def __init__(self):
                        self.parser_name = "Builtin PDF Parser"
                        self.supported_extensions = ['.pdf']

                    def can_parse(self, file_path):
                        return file_path.lower().endswith('.pdf')

                    def parse(self, file_path):
                        return self._read_pdf(file_path)

                    def _read_pdf(self, path):
                        """内置 PDF 解析方法"""
                        text = []
                        try:
                            with fitz.open(path) as doc:
                                for page in doc:
                                    t = page.get_text()
                                    if t.strip():
                                        text.append(t)
                            return "\n".join(text)
                        except Exception as e:
                            print(f"PDF 解析错误: {e}")
                            return ""

                    def safe_parse(self, file_path):
                        """安全解析方法"""
                        try:
                            return self.parse(file_path)
                        except Exception as e:
                            print(f"安全解析失败: {e}")
                            return f"[解析失败] {str(e)}"

                loaded_parsers.append(BuiltinPDFParser())
                print(f"✅ [IO] 已加载内置 PDF 解析器")

        # 尝试加载其他解析器
        try:
            from parsers.word_parser import WordParser
            loaded_parsers.append(WordParser())
            print(f"✅ [IO] 已加载解析器: Word Parser")
        except:
            pass

        # 🔥 动态检测并添加 EPUB 解析器
        if self.epub_support:
            try:
                # 尝试导入 EPUB 解析器，如果不存在则使用内置的
                from parsers.epub_parser import EPUPParser
                loaded_parsers.append(EPUPParser())
                print(f"✅ [IO] 已加载 EPUB 解析器")
            except ImportError:
                # 如果外部没有 EPUB 解析器，使用内置的简单版
                class BuiltinEPUPParser(BaseParser):
                    """内置的简单 EPUB 解析器（来自 3.txt）"""

                    def __init__(self):
                        self.parser_name = "Builtin EPUB Parser"
                        self.supported_extensions = ['.epub']

                    def can_parse(self, file_path):
                        return file_path.lower().endswith('.epub')

                    def parse(self, file_path):
                        return self._read_epub(file_path)

                    def safe_parse(self, file_path):
                        """安全解析方法"""
                        try:
                            return self.parse(file_path)
                        except Exception as e:
                            print(f"安全解析失败: {e}")
                            return f"[解析失败] {str(e)}"

                    def _read_epub(self, path):
                        """🔥 来自 3.txt 的 EPUB 解析方法 - 修复版"""
                        text_content = []
                        try:
                            book = epub.read_epub(path)

                            # 策略 A：优先尝试通过 Spine (骨架) 遍历
                            # Spine 定义了书籍的线性阅读顺序，能保证内容完整且有序
                            for item_id_tuple in book.spine:
                                # item_id_tuple 通常是 ('item_id', 'yes/no')
                                item_id = item_id_tuple[0]
                                item = book.get_item_with_id(item_id)

                                if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
                                    content = self._extract_html_text(item.get_content())
                                    if content:
                                        text_content.append(content)

                            # 策略 B：如果 Spine 为空 (罕见情况)，回退到遍历所有文档
                            if not text_content:
                                print("⚠️ Spine 模式未获取到内容，切换至全量扫描模式...")
                                for item in book.get_items():
                                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                                        content = self._extract_html_text(item.get_content())
                                        if content:
                                            text_content.append(content)

                            final_text = "\n\n".join(text_content)

                            # 最后的防线：如果还是空的
                            if not final_text.strip():
                                return "[系统提示：该 EPUB 似乎是纯图片扫描版或加密版，无法提取文字。]"

                            return final_text

                        except Exception as e:
                            print(f"EPUB 解析错误: {e}")
                            return f"[EPUB 读取失败: {str(e)}]"

                    def _extract_html_text(self, html_content):
                        """辅助函数：清洗 HTML"""
                        try:
                            soup = BeautifulSoup(html_content, 'html.parser')

                            # 移除 script 和 style 标签，防止干扰
                            for script in soup(["script", "style"]):
                                script.decompose()

                            # 获取文本，使用换行符分隔块级元素
                            text = soup.get_text(separator='\n')

                            # 去除多余的空行
                            lines = [line.strip() for line in text.splitlines() if line.strip()]
                            return "\n".join(lines)
                        except:
                            return ""

                loaded_parsers.append(BuiltinEPUPParser())
                print(f"✅ [IO] 已加载内置 EPUB 解析器")

        # 继续尝试加载其他解析器...
        parser_classes_to_try = [
            ('excel_parser', 'ExcelParser'),
            ('csv_parser', 'CSVParser'),
            ('ppt_parser', 'PPTParser'),
            ('html_parser', 'HTMLParser'),
            ('image_parser', 'ImageParser'),
        ]

        for module_name, class_name in parser_classes_to_try:
            try:
                module = importlib.import_module(f'parsers.{module_name}')
                parser_class = getattr(module, class_name)
                loaded_parsers.append(parser_class())
                print(f"✅ [IO] 已加载解析器: {class_name}")
            except Exception as e:
                print(f"⚠️ [IO] 解析器 {class_name} 加载失败: {e}")

        return loaded_parsers

    def _get_parser(self, file_path):
        """
        根据文件路径获取匹配的解析器
        :param file_path: 文件路径
        :return: 解析器实例或None
        """
        for parser in self.parsers:
            if hasattr(parser, 'can_parse') and parser.can_parse(file_path):
                return parser
        return None

    # =========================================================
    # 🔥 核心修复：全域文件寻址 (新增功能)
    # =========================================================
    def smart_find_file(self, filename: str) -> str:
        """
        全域搜索文件：解决加载人格时找不到源文件的问题
        搜索顺序：
        1. 绝对路径检查
        2. Inputs 根目录
        3. Inputs 所有子目录 (递归)
        4. Uploads (兼容旧版)
        """
        # 1. 检查是否已经是绝对路径
        if os.path.isabs(filename) and os.path.exists(filename):
            return filename

        target_name = os.path.basename(filename)
        inputs_dir = self.directories.get('inputs', 'Inputs')

        print(f"🔍 [IO] 正在 Inputs 目录中搜寻: {target_name}...")

        # 2. 检查 Inputs 根目录
        candidate = os.path.join(inputs_dir, target_name)
        if os.path.exists(candidate):
            return candidate

        # 3. 递归检查 Inputs 所有子目录
        for root, dirs, files in os.walk(inputs_dir):
            if target_name in files:
                return os.path.join(root, target_name)

        # 4. 最后的尝试：当前工作目录
        if os.path.exists(target_name):
            return os.path.abspath(target_name)

        return None

    # =========================================================
    # 📂 物理隔离核心逻辑 (来自 3.txt)
    # =========================================================
    def get_persona_folder(self, persona_name):
        """
        获取（并创建）特定人格的物理存储文件夹
        例如: data/Inputs/崔浩然/
        """
        if not persona_name:
            persona_name = "Default"

        # 过滤非法字符 (来自 3.txt)
        safe_name = "".join([c for c in persona_name if c.isalnum() or c in (' ', '_', '-')]).strip()

        base_inputs = self.directories.get('inputs')
        target_dir = os.path.join(base_inputs, safe_name)

        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        return target_dir

    def scan_files_in_persona(self, persona_name):
        """
        扫描特定人格文件夹下的所有有效文档
        这是"单一事实来源"，不依赖 JSON (来自 3.txt)
        """
        target_dir = self.get_persona_folder(persona_name)
        all_files = glob.glob(os.path.join(target_dir, "*"))

        valid_files = []
        for f in all_files:
            if os.path.basename(f).startswith("~$"):
                continue
            if os.path.isdir(f):
                continue
            valid_files.append(f)  # 返回绝对路径

        return valid_files

    # ==========================================
    # 🔥 核心修复：文件归档方法 (物理隔离版)
    # ==========================================
    def archive_input(self, file_paths, persona_name=None):
        """
        将用户选择的文件归档到工作区的 Inputs 目录
        🔥 物理隔离版本：文件按人格存储在 Inputs/{PersonaName}/ 子目录下
        :param file_paths: 单个路径字符串 或 路径列表
        :param persona_name: 人格名称，决定存储的子目录
        :return: 归档后的新路径列表
        """
        # 如果没有指定人格名称，使用 Default
        if not persona_name:
            persona_name = "Default"

        # 1. 统一转为列表
        if isinstance(file_paths, str):
            file_paths = [file_paths]

        # 🔥 使用物理隔离的目标目录
        target_dir = self.get_persona_folder(persona_name)
        archived_paths = []

        # 2. 遍历复制
        for src_path in file_paths:
            if not os.path.exists(src_path):
                continue

            file_name = os.path.basename(src_path)
            dst_path = os.path.join(target_dir, file_name)

            try:
                # 如果不是在目标目录里，就复制过去
                if os.path.abspath(src_path) != os.path.abspath(dst_path):
                    # 使用 copy2 保留文件元数据（如创建时间）
                    shutil.copy2(src_path, dst_path)
                    print(f"📦 [IO] 已归档文件到 {persona_name}: {file_name}")
                else:
                    print(f"📂 [IO] 文件已在 {persona_name} 目录: {file_name}")

                archived_paths.append(dst_path)
            except Exception as e:
                print(f"❌ [IO] 归档失败 {file_name}: {e}")
                # 如果复制失败，尝试直接使用原路径（作为降级方案）
                archived_paths.append(src_path)

        return archived_paths

    # ==========================================
    # 🔥 智能文件读取器 (物理隔离兼容版)
    # ==========================================
    def read_file(self, file_path):
        """
        通用读取器 - 智能版本
        支持格式：.txt, .md, .pdf, .epub, .docx 等
        策略：先尝试使用解析器，再使用备用方法
        🔥 注意：此方法接收的是完整文件路径，与物理隔离逻辑兼容
        """
        # 🔥 新增：如果文件不存在，尝试智能查找
        if not os.path.exists(file_path):
            found_path = self.smart_find_file(file_path)
            if found_path:
                file_path = found_path
                print(f"🔍 [IO] 通过智能查找找到文件: {file_path}")
            else:
                return f"[系统错误] 文件不存在: {file_path}"

        ext = os.path.splitext(file_path)[1].lower()

        # 1. 优先使用解析器
        for parser in self.parsers:
            if hasattr(parser, 'can_parse') and parser.can_parse(file_path):
                print(f"📂 使用 {parser.parser_name} 解析: {os.path.basename(file_path)}")
                # 使用安全解析方法
                if hasattr(parser, 'safe_parse'):
                    result = parser.safe_parse(file_path)
                else:
                    result = parser.parse(file_path)
                if result and result.strip():
                    return result

        # 2. 如果没有匹配的解析器，使用扩展名分支 + 备用方法
        try:
            # === PDF 处理 ===
            if ext == '.pdf':
                if self.pdf_support:
                    return self._read_pdf(file_path)
                else:
                    return "[系统提示] 缺少 PyMuPDF 库，无法解析 PDF。"

            # === EPUB 处理 ===
            elif ext == '.epub':
                if self.epub_support:
                    return self._read_epub(file_path)
                else:
                    return "[系统提示] 缺少 EbookLib 库，无法解析 EPUB。"

            # === 纯文本处理 (.txt, .md, .py, etc) ===
            else:
                # 🔥 关键修复：尝试多种编码
                encodings = ['utf-8', 'gbk', 'utf-16', 'latin-1']
                for enc in encodings:
                    try:
                        with open(file_path, 'r', encoding=enc) as f:
                            return f.read()
                    except:
                        continue
                return "[系统错误] 无法识别的文件编码。"

        except Exception as e:
            return f"[读取异常] {str(e)}"

    # ==========================================
    # 🔥 新增：全量内容读取器（用于深度生成）来自7-ioai.txt
    # ==========================================
    def read_full_content(self, file_path):
        """
        🔥 强制读取全量内容 (用于深度生成)
        不进行任何采样和截断，直接调用 Parser 获取 100% 文本。
        """
        # 🔥 新增：如果文件不存在，尝试智能查找
        if not os.path.exists(file_path):
            found_path = self.smart_find_file(file_path)
            if found_path:
                file_path = found_path
                print(f"🔍 [IO] 通过智能查找找到文件: {file_path}")
            else:
                return f"[错误] 文件不存在: {file_path}"

        # 获取对应的解析器
        parser = self._get_parser(file_path)
        if not parser:
            return f"[无法识别文件格式: {os.path.basename(file_path)}]"

        try:
            # 直接调用 parse 获取全文
            content = parser.parse(file_path)

            # 简单的清洗，去除解析器可能添加的元数据标签
            lines = content.split('\n')
            # 过滤掉 "[Word文档: xxx]" 这种系统自动加的头信息
            clean_lines = []
            for line in lines:
                line_stripped = line.strip()
                # 过滤掉解析器添加的元数据行
                if line_stripped.startswith("[Word文档") or line_stripped.startswith("[PDF"):
                    continue
                # 过滤掉以"["开头且包含"文档"的行（来自7-ioai.txt）
                if line_stripped.startswith("[") and "文档" in line_stripped:
                    continue
                clean_lines.append(line)

            return "\n".join(clean_lines)

        except Exception as e:
            print(f"❌ 全量读取失败 {file_path}: {e}")
            # 降级方案：使用简单文本读取
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except:
                return ""

    # ==========================================
    # 🔥 PDF/EPUB 直接读取方法 (物理隔离兼容版)
    # ==========================================
    def _read_pdf(self, path):
        """解析 PDF (备用方法)"""
        if not self.pdf_support:
            return "[错误：PyMuPDF 库未安装，无法解析 PDF]"

        text = []
        try:
            with fitz.open(path) as doc:
                for page in doc:
                    t = page.get_text()
                    if t.strip():
                        text.append(t)
            return "\n".join(text)
        except Exception as e:
            print(f"PDF 解析错误: {e}")
            return ""

    def _read_epub(self, path):
        """
        🔥 解析 EPUB (修复版：基于 Spine 读取完整内容)
        解决：内容读取不全、章节乱序、短章节丢失
        """
        if not self.epub_support:
            return "[错误：EPUB 支持库未安装，无法解析 EPUB 文件。请安装：pip install ebooklib beautifulsoup4]"

        text_content = []
        try:
            book = epub.read_epub(path)

            # 策略 A：优先尝试通过 Spine (骨架) 遍历
            # Spine 定义了书籍的线性阅读顺序，能保证内容完整且有序
            for item_id_tuple in book.spine:
                # item_id_tuple 通常是 ('item_id', 'yes/no')
                item_id = item_id_tuple[0]
                item = book.get_item_with_id(item_id)

                if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
                    content = self._extract_html_text(item.get_content())
                    if content:
                        text_content.append(content)

            # 策略 B：如果 Spine 为空 (罕见情况)，回退到遍历所有文档
            if not text_content:
                print("⚠️ Spine 模式未获取到内容，切换至全量扫描模式...")
                for item in book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT:
                        content = self._extract_html_text(item.get_content())
                        if content:
                            text_content.append(content)

            final_text = "\n\n".join(text_content)

            # 最后的防线：如果还是空的
            if not final_text.strip():
                return "[系统提示：该 EPUB 似乎是纯图片扫描版或加密版，无法提取文字。]"

            return final_text

        except Exception as e:
            print(f"EPUB 解析错误: {e}")
            return f"[EPUB 读取失败: {str(e)}]"

    def _extract_html_text(self, html_content):
        """辅助函数：清洗 HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # 移除 script 和 style 标签，防止干扰
            for script in soup(["script", "style"]):
                script.decompose()

            # 获取文本，使用换行符分隔块级元素
            text = soup.get_text(separator='\n')

            # 去除多余的空行
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            return "\n".join(lines)
        except:
            return ""

    # ==========================================
    # 🔥 人格存储功能 (Persona Editor 依赖) (物理隔离版 + 健壮性修复)
    # ==========================================
    def save_persona(self, name, data, mode="FullState", desc=""):
        """
        保存人格数据 (物理隔离版 + 健壮性修复)
        🔥 修改：JSON 仅作元数据存储，不作文件索引 (来自 3.txt)
        🔥 增强：确保不写空文件，提供默认值，自动保留旧文档关联
        """
        persona_dir = self.directories.get('personas')
        if not os.path.exists(persona_dir):
            os.makedirs(persona_dir, exist_ok=True)

        path = os.path.join(persona_dir, f"{name}.json")

        # 🔥 健壮性修复：构造完整 Payload，确保不是 None
        try:
            # 如果是更新现有文件，保留原有的 documents 列表
            documents = []
            if os.path.exists(path):
                try:
                    old_data = self._safe_load_persona_file(path)
                    if isinstance(old_data, dict) and "documents" in old_data:
                        documents = old_data["documents"]
                except:
                    pass

            payload = {
                "name": name,
                "description": desc or f"{name} 的人格矩阵",
                "mode": mode,
                "created_at": str(datetime.now()),
                "dimensions": data if data else {},  # 🔥 确保不是 None
                "documents": documents  # 保留关联文档列表
            }

            with open(path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            print(f"✅ [IO] 人格 [{name}] 已保存至 {path}")
            return True
        except Exception as e:
            print(f"❌ [IO] 人格保存失败: {e}")
            return False

    def _safe_load_persona_file(self, file_path):
        """
        安全加载人格文件 (内部方法)
        :param file_path: 完整文件路径
        :return: 加载的数据或默认值
        """
        default_persona = {
            "name": os.path.basename(file_path).replace('.json', ''),
            "description": "自动修复的人格存档",
            "documents": [],
            "dimensions": {}
        }

        try:
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                print(f"⚠️ [IO] 人格文件为空: {file_path}")
                return default_persona

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 校验关键字段
            if not isinstance(data, dict):
                print(f"⚠️ [IO] 人格文件不是有效的JSON对象: {file_path}")
                return default_persona

            # 🔥 兼容性处理：如果旧文件使用 "data" 字段，映射为 "dimensions"
            if "data" in data and "dimensions" not in data:
                data["dimensions"] = data.pop("data")

            return data

        except json.JSONDecodeError:
            print(f"❌ [IO] 人格文件损坏(JSON格式错误): {file_path}")
            return default_persona
        except Exception as e:
            print(f"❌ [IO] 加载人格失败: {e}")
            return default_persona

    def load_persona(self, name):
        """
        加载特定人格数据 (健壮性修复版)
        :param name: 人格名称 (不带.json后缀)
        :return: 人格数据字典，即使文件损坏也返回默认值
        """
        path = os.path.join(self.directories.get('personas'), f"{name}.json")
        return self._safe_load_persona_file(path)

    def scan_personas(self):
        """扫描所有存档的人格 (JSON)"""
        persona_dir = self.directories.get('personas')
        if not os.path.exists(persona_dir):
            return []

        files = [f.replace('.json', '') for f in os.listdir(persona_dir) if f.endswith('.json')]
        return sorted(files)

    # ==========================================
    # 🔥 通用文件读取器 (物理隔离兼容版)
    # ==========================================
    def read_file_simple(self, file_path):
        """
        简化版文件读取器
        读取文件内容，自动识别格式
        """
        # 🔥 新增：如果文件不存在，尝试智能查找
        if not os.path.exists(file_path):
            found_path = self.smart_find_file(file_path)
            if found_path:
                file_path = found_path
            else:
                return None

        ext = os.path.splitext(file_path)[1].lower()

        try:
            # === 分支 1: PDF ===
            if ext == '.pdf':
                return self._read_pdf(file_path)

            # === 分支 2: EPUB (新增) ===
            elif ext == '.epub':
                return self._read_epub(file_path)

            # === 分支 3: 纯文本 ===
            else:
                # 尝试多种编码
                encodings = ['utf-8', 'gbk', 'utf-16', 'latin-1']
                for enc in encodings:
                    try:
                        with open(file_path, 'r', encoding=enc) as f:
                            return f.read()
                    except:
                        continue
                return None
        except Exception as e:
            print(f"❌ [IO] 读取文件失败 {file_path}: {e}")
            return None

    # ==========================================
    # 🔥 文件扫描功能 (物理隔离版)
    # ==========================================
    def get_inputs_dir(self):
        """获取输入目录根路径"""
        return self.directories.get('inputs')

    def get_persona_inputs_dir(self, persona_name):
        """获取特定人格的输入目录路径"""
        return self.get_persona_folder(persona_name)

    def list_input_files(self, persona_name=None):
        """
        列出输入目录中的所有文件 (物理隔离版)
        :param persona_name: 人格名称，如果为None则列出根目录文件
        """
        if persona_name:
            # 列出特定人格文件夹下的文件
            target_dir = self.get_persona_folder(persona_name)
            if not os.path.exists(target_dir):
                return []

            files = []
            for f in os.listdir(target_dir):
                fpath = os.path.join(target_dir, f)
                if os.path.isfile(fpath) and not f.startswith("~$"):
                    files.append(f)
            return files
        else:
            # 列出根目录文件 (兼容旧代码)
            inputs_dir = self.get_inputs_dir()
            if not os.path.exists(inputs_dir):
                return []

            files = []
            for f in os.listdir(inputs_dir):
                fpath = os.path.join(inputs_dir, f)
                if os.path.isfile(fpath) and not f.startswith("~$"):
                    files.append(f)
            return files

    def get_file_info(self, file_name, persona_name=None):
        """
        获取文件信息 (物理隔离版)
        :param file_name: 文件名
        :param persona_name: 人格名称
        """
        if persona_name:
            # 在特定人格文件夹中查找
            target_dir = self.get_persona_folder(persona_name)
            file_path = os.path.join(target_dir, file_name)
        else:
            # 在根目录中查找 (兼容旧代码)
            inputs_dir = self.get_inputs_dir()
            file_path = os.path.join(inputs_dir, file_name)

        if not os.path.exists(file_path):
            # 🔥 新增：尝试智能查找
            found_path = self.smart_find_file(file_name)
            if found_path:
                file_path = found_path
            else:
                return None

        return {
            'name': file_name,
            'path': file_path,
            'size': os.path.getsize(file_path),
            'modified': datetime.fromtimestamp(os.path.getmtime(file_path)),
            'extension': os.path.splitext(file_name)[1].lower()
        }

    def check_epub_support(self):
        """检查 EPUB 支持状态"""
        status = {
            'pdf_support': self.pdf_support,
            'fitz_available': PDF_SUPPORT,
            'epublib_available': EPUBLIB_SUPPORT,
            'epub_support': self.epub_support,
            'missing_libraries': []
        }

        if not PDF_SUPPORT:
            status['missing_libraries'].append('PyMuPDF (fitz)')
        if not EPUBLIB_SUPPORT:
            status['missing_libraries'].extend(['ebooklib', 'beautifulsoup4'])

        return status