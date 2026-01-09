# -*- coding: utf-8 -*-
"""
图片OCR解析器
优化版
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from .base_parser import BaseParser
from config.settings import SETTINGS

# 检查依赖
try:
    from PIL import Image, ImageEnhance, ImageFilter
    import pytesseract

    HAS_OCR = True
except ImportError:
    HAS_OCR = False


class ImageParser(BaseParser):
    """图片OCR解析器"""

    def __init__(self) -> None:
        super().__init__()
        self.supported_extensions = SETTINGS.SUPPORTED_EXTENSIONS.get('image',
                                                                      ['.jpg', '.jpeg', '.png', '.bmp', '.tiff'])
        self.parser_name = "ImageParser"

    def can_parse(self, file_path: str) -> bool:
        """检查是否能解析图片文件"""
        if not HAS_OCR:
            return False
        return Path(file_path).suffix.lower() in self.supported_extensions

    def parse(self, file_path: str) -> str:
        """使用OCR解析图片"""
        if not HAS_OCR:
            return "[需要安装 pytesseract 和 pillow 库才能进行OCR识别]"

        try:
            # 使用 context manager 确保图片资源释放 (虽然 PIL Image Lazy Load, 但 explicit is better)
            with Image.open(file_path) as image:
                # 必须加载图像数据，因为 open 只是懒加载
                image.load()

                content_lines = [f"[图片OCR结果: {Path(file_path).name}]"]
                content_lines.append(f"图片尺寸: {image.size[0]}x{image.size[1]}")
                content_lines.append(f"图片模式: {image.mode}")

                # 预处理图片 (拷贝一份进行处理，不影响原对象)
                processed_image = self._preprocess_image(image.copy())

                # OCR识别逻辑
                try:
                    # 1. 尝试中英文混合识别
                    text = pytesseract.image_to_string(processed_image, lang='chi_sim+eng')
                    if text.strip():
                        content_lines.append("\n识别结果 (Mix):")
                        content_lines.append(text.strip())
                    else:
                        raise ValueError("Empty result")

                except Exception:
                    # 2. 如果混合识别失败或结果为空，尝试分步识别
                    try:
                        content_lines.append("\n[尝试分步识别模式...]")
                        combined_text = []

                        # 中文
                        try:
                            text_cn = pytesseract.image_to_string(processed_image, lang='chi_sim')
                            if text_cn.strip():
                                combined_text.append(f"--- 中文识别 ---\n{text_cn.strip()}")
                        except:
                            pass

                        # 英文
                        try:
                            text_en = pytesseract.image_to_string(processed_image, lang='eng')
                            if text_en.strip():
                                combined_text.append(f"--- 英文识别 ---\n{text_en.strip()}")
                        except:
                            pass

                        if combined_text:
                            content_lines.extend(combined_text)
                        else:
                            content_lines.append("\n[未识别到有效文字内容]")

                    except Exception as e:
                        content_lines.append(f"\n[OCR识别严重错误]: {str(e)}")

                return "\n".join(content_lines)

        except Exception as e:
            return f"[图片解析流程错误]: {str(e)}"

    def _preprocess_image(self, image: 'Image.Image') -> 'Image.Image':
        """预处理图片以提高OCR精度"""
        try:
            # 1. 转换为灰度图
            if image.mode != 'L':
                image = image.convert('L')

            # 2. 增强对比度
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)

            # 3. 增强锐度
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)

            # 4. 二值化处理 (自适应或固定阈值)
            # 这里保持原逻辑的固定阈值，但增加异常保护
            threshold = 128
            image = image.point(lambda x: 255 if x > threshold else 0)

            # 5. 去噪
            image = image.filter(ImageFilter.MedianFilter(size=3))

            return image
        except Exception as e:
            # 如果预处理出错，记录日志并返回原图，起码能运行
            print(f"Image preprocessing failed: {e}")
            return image