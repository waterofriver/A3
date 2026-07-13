# -*- coding: utf-8 -*-
"""
DAG 加载工具
===========
从 JSON 文件加载 KnowledgeDAG 的实用函数。
"""

import json

from ..models import KnowledgeDAG


def load_knowledge_dag(json_path: str) -> KnowledgeDAG:
    """从 JSON 文件加载知识 DAG，使用 Pydantic model_validate。

    参数:
        json_path: JSON 文件路径，内容需符合 KnowledgeDAG 的 schema

    返回:
        KnowledgeDAG: 验证后的知识 DAG 模型

    异常:
        FileNotFoundError: 文件不存在
        json.JSONDecodeError: JSON 格式错误
        pydantic.ValidationError: 数据不符合 KnowledgeDAG schema
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return KnowledgeDAG.model_validate(data)
