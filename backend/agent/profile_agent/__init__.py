"""
Profile Agent 包
===============

画像构建 Agent，从学生自由对话中提取 6 维度学习画像。

用法::

    from profile_agent import ProfileAgent

    agent = ProfileAgent()
    result = agent.extract("我在读计算机大三")
"""

from .profile_agent import ProfileAgent, ProfileExtractionResult

__all__ = [
    "ProfileAgent",
    "ProfileExtractionResult",
]
