# core/brain_modules/memory.py
# -*- coding: utf-8 -*-
"""
海马体 - 负责短期对话记忆和上下文管理
职责：对话历史管理、上下文提取、记忆压缩
"""


class Memory:
    """海马体 - 记忆管理系统"""

    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base

        # 短期对话记忆
        self.conversation_history = []
        self.max_history_turns = 10

        # 加载风格记忆
        self._load_style_memory()

    def _load_style_memory(self):
        """从知识库加载风格记忆"""
        if hasattr(self.knowledge_base, 'data'):
            try:
                from engines.mimicry_engine import EnhancedMimicryEngine
                mimicry = EnhancedMimicryEngine()
                count = mimicry.load_from_knowledge_base(self.knowledge_base.data)
                print(f"🧠 [记忆] 已加载 {count} 个风格特征因子")
            except Exception as e:
                print(f"风格加载警告: {e}")

    def add_conversation(self, role, content):
        """
        添加对话记录
        """
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": self._get_timestamp()
        })

        # 保持历史长度
        if len(self.conversation_history) > self.max_history_turns * 2:
            self.conversation_history = self.conversation_history[-(self.max_history_turns * 2):]

    def get_history(self, max_turns=None):
        """
        获取对话历史
        """
        if max_turns is None:
            max_turns = self.max_history_turns

        return self.conversation_history[-(max_turns * 2):] if self.conversation_history else []

    def get_history_formatted(self, max_turns=None):
        """
        获取格式化的对话历史
        """
        history = self.get_history(max_turns)

        if not history:
            return ""

        formatted = []
        for turn in history:
            formatted.append(f"{turn['role']}: {turn['content']}")

        return "\n".join(formatted)

    def get_recent_context(self, turns=3):
        """
        获取最近的上下文
        """
        history = self.get_history(turns)

        if not history:
            return ""

        # 提取最近几轮的对话
        context = []
        for turn in history:
            if len(turn['content']) > 100:
                # 截断过长的内容
                context.append(f"{turn['role']}: {turn['content'][:200]}...")
            else:
                context.append(f"{turn['role']}: {turn['content']}")

        return "\n".join(context)

    def clear_history(self):
        """
        清空对话历史
        """
        self.conversation_history = []

    def compress_history(self, max_length=2000):
        """
        压缩历史记录
        """
        if not self.conversation_history:
            return

        total_length = sum(len(turn['content']) for turn in self.conversation_history)

        if total_length <= max_length:
            return

        # 压缩策略：保留最近的对话，压缩早期的对话
        keep_ratio = 0.6  # 保留60%的对话
        keep_count = int(len(self.conversation_history) * keep_ratio)

        if keep_count < 2:
            keep_count = 2

        # 压缩早期的对话
        early_history = self.conversation_history[:-keep_count]
        recent_history = self.conversation_history[-keep_count:]

        # 压缩早期历史（可以进一步优化）
        compressed_early = []
        for i in range(0, len(early_history), 2):
            if i + 1 < len(early_history):
                compressed = self._compress_turn_pair(
                    early_history[i], early_history[i + 1]
                )
                compressed_early.append(compressed)

        self.conversation_history = compressed_early + recent_history

    def _compress_turn_pair(self, turn1, turn2):
        """
        压缩一对对话
        """
        return {
            "role": "系统",
            "content": f"[早期对话摘要] {turn1['role']}: {turn1['content'][:50]}... | {turn2['role']}: {turn2['content'][:50]}...",
            "timestamp": turn1['timestamp']
        }

    def summarize_session(self):
        """
        总结当前会话
        """
        if not self.conversation_history:
            return "暂无对话历史"

        history_text = self.get_history_formatted()

        # 这里可以调用LLM进行总结，暂时用简单方法
        user_turns = [t for t in self.conversation_history if t['role'] == 'User']
        assistant_turns = [t for t in self.conversation_history if t['role'] == 'Athena']

        summary = f"""
        【会话摘要】
        对话轮次: {len(user_turns)} 次用户提问, {len(assistant_turns)} 次助手回复
        对话时长: {self._get_session_duration()}
        主要话题: {self._extract_main_topics()}
        """

        return summary

    def _extract_main_topics(self):
        """
        提取主要话题（简单实现）
        """
        if not self.conversation_history:
            return "无"

        # 提取用户提问中的关键词
        user_contents = [t['content'] for t in self.conversation_history if t['role'] == 'User']

        # 简单关键词提取（实际应用中可用更复杂的方法）
        keywords = []
        for content in user_contents[:3]:  # 只看前3个问题
            words = content.split()[:5]  # 取前5个词
            keywords.extend(words)

        return ", ".join(set(keywords))[:100] + "..."

    def _get_session_duration(self):
        """
        获取会话持续时间
        """
        if not self.conversation_history:
            return "0分钟"

        first_time = self.conversation_history[0]['timestamp']
        last_time = self.conversation_history[-1]['timestamp']

        # 简单计算（实际需要解析时间戳）
        return f"{len(self.conversation_history) * 2}分钟"

    def _get_timestamp(self):
        """
        获取时间戳
        """
        import time
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    def save_to_knowledge_base(self):
        """
        将会话记忆保存到知识库
        """
        if not self.conversation_history:
            return False

        try:
            # 创建会话摘要
            session_summary = self.summarize_session()

            # 保存到知识库
            if hasattr(self.knowledge_base, 'add_session'):
                session_id = self.knowledge_base.add_session(
                    history=self.conversation_history,
                    summary=session_summary
                )
                return True
            else:
                print("知识库不支持会话保存")
                return False

        except Exception as e:
            print(f"保存会话失败: {e}")
            return False

    def load_from_knowledge_base(self, session_id):
        """
        从知识库加载会话记忆
        """
        try:
            if hasattr(self.knowledge_base, 'get_session'):
                session_data = self.knowledge_base.get_session(session_id)
                if session_data:
                    self.conversation_history = session_data.get('history', [])
                    return True
            return False
        except Exception as e:
            print(f"加载会话失败: {e}")
            return False