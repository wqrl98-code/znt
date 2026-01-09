# -*- coding: utf-8 -*-
"""
大脑功能区包
包含：总指挥、互联学习专员、首席执笔人、审委会稿、海马体
"""
from core.commander import Commander
from .researcher import Researcher
from .writer import Writer
from .editor import Editor
from .memory import Memory

__all__ = ['Commander', 'Researcher', 'Writer', 'Editor', 'Memory']