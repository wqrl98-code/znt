# -*- coding: utf-8 -*-
"""
LLM Engine - 高效连接稳定版 (v21.1)
合并修复：Session 复用连接 + 超长超时 + 算力估算 + 完整错误处理
支持自定义 options 参数
"""
import requests
import json
import time
import math
import traceback
from config.settings import SETTINGS


class LLMEngine:
    def __init__(self):
        self.base_url = SETTINGS.OLLAMA_API_URL if hasattr(SETTINGS, 'OLLAMA_API_URL') else "http://localhost:11434"
        self.model = SETTINGS.OLLAMA_MODEL if hasattr(SETTINGS, 'OLLAMA_MODEL') else "qwen3:8b"
        # 🔥 核心修改：将超时时间设为 1 小时，适应低算力下的长文生成
        self.timeout = 3600
        # 使用 Session 复用 TCP 连接，提高效率
        self.session = requests.Session()

    def estimate_time(self, context_length, predict_length):
        """
        🚀 算力耗时估算器
        根据当前上下文长度和预估输出长度，计算大致等待时间
        """
        # 假设低算力场景 (CPU/内存卸载模式)
        # 处理 Prompt 速度: 约 10-20 token/s
        # 生成速度: 约 1-3 token/s

        process_time = context_length / 15.0  # 预处理耗时
        gen_time = predict_length / 1.5  # 生成耗时 (按最慢估算)

        total_seconds = process_time + gen_time
        return total_seconds

    def chat(self, user_text, system_prompt=None, options=None):
        """
        标准对话接口 (非流式，保证完整性)
        支持传递 options (如 num_ctx, temperature) 参数
        使用 Session 复用连接提高效率
        """
        if options is None:
            options = {}

        # 构建消息列表
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_text})

        # 默认满血参数 (绝不降级)
        default_options = {
            "temperature": 0.6,  # 稍微降低随机性，保证解读准确
            "num_ctx": 12288,  # 强制扩大上下文窗口到 12k，适配长文
            "num_predict": 4096,  # 允许长输出
            "num_gpu": 999  # 尽力调用 GPU
        }

        # 🔥 关键修复：确保传入的 options 覆盖 default_options
        final_options = default_options.copy()
        if options:
            final_options.update(options)  # 这样最稳妥

        payload = {
            "model": self.model,
            "stream": False,  # 强制非流式，避免UI处理复杂
            "messages": messages,
            "options": final_options
        }

        try:
            print(f"[LLM] Sending Request to {self.base_url} (Model: {self.model})")
            print(f"[LLM] Options: {final_options}")
            start = time.time()

            # 🔥 使用 Session 发送请求 (超长 Timeout)，复用 TCP 连接
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )

            duration = time.time() - start
            print(f"[LLM] Response received in {duration:.2f}s ({duration / 60:.2f} minutes)")

            if response.status_code == 200:
                data = response.json()
                content = data.get("message", {}).get("content", "")
                if not content:
                    return "⚠️ 模型返回了空数据，请检查本地 Ollama 显存占用。"
                return content
            else:
                return f"❌ Ollama API 错误: Status {response.status_code} - {response.text}"

        except requests.exceptions.Timeout:
            return "❌ 生成超时。由于算力限制，本次任务耗时超过 60 分钟。"
        except requests.exceptions.ConnectionError:
            return "❌ 无法连接到 Ollama 服务。请确认 Ollama 已在后台运行 (端口 11434)。"
        except Exception as e:
            print(f"❌ LLM 连接失败: {e}")
            traceback.print_exc()
            return f"⚠️ AI 思考中断: {str(e)}"