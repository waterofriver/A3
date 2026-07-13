"""
JSON 解析工具
============
从 LLM 输出中鲁棒提取 JSON 对象，处理 code fence、markdown 包装、
末尾逗号、解释性文字等常见问题。可被所有 Agent 复用。
"""

import json
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── 私有辅助 ────────────────────────────────────────────────


def _strip_code_fences(text: str) -> str:
    """移除 ```json ... ``` 或 ``` ... ``` 代码块标记，返回内部内容。

    使用贪婪匹配确保匹配到最外层的代码围栏，
    避免 JSON 内容中的 markdown 代码块（如 body_markdown 内的 ```）干扰。
    """
    # 优先匹配 ```json ... ```（带语言标记，允许末尾空白行）
    pattern_json = r'```json\s*\n([\s\S]*?)\n\s*```\s*$'
    match = re.search(pattern_json, text)
    if match:
        return match.group(1).strip()

    # 回退：从第一个 ``` 到最后一个 ```（处理内容中有代码块的场景）
    first_fence = text.find("```")
    last_fence = text.rfind("```")
    if first_fence != -1 and last_fence != -1 and last_fence > first_fence + 3:
        # 去掉开头的 ``` (可能带语言标记)
        after_open = text[first_fence + 3:]
        newline_pos = after_open.find("\n")
        if newline_pos != -1:
            after_open = after_open[newline_pos + 1:]
        # 截取到最后一个 ``` 之前
        inner = after_open[: last_fence - first_fence - 3]
        # 去掉末尾多余的空白行
        inner = inner.rstrip()
        if inner:
            return inner

    return text


def _find_json_object(text: str) -> Optional[str]:
    """
    花括号计数法定位 JSON 对象。
    从第一个 '{' 开始，计数到匹配的 '}' 结束。
    处理嵌套对象和字符串中的花括号。
    """
    start = text.find('{')
    if start == -1:
        return None

    in_string = False
    escape_next = False
    depth = 0

    for i in range(start, len(text)):
        ch = text[i]

        if escape_next:
            escape_next = False
            continue

        if ch == '\\':
            escape_next = True
            continue

        if ch == '"' and not escape_next:
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]

    # 括号未闭合，返回从 start 到末尾（后续 repair 会尝试修复）
    return text[start:]


def _repair_json(text: str) -> str:
    """
    尝试修复常见 JSON 格式问题：
    - 末尾多余逗号: ,} -> } 和 ,] -> ]
    - 中文引号替换为英文引号
    - 不完整结尾：缺失的 } 或 ]
    返回修复后的文本。
    """
    # 1. 移除末尾多余逗号（对象和数组）
    text = re.sub(r',(\s*[}\]])', r'\1', text)

    # 2. 中文引号 → 英文引号（在 JSON 字符串外部可能会有问题，谨慎处理）
    #    仅替换可能作为 JSON key/value 包裹的中文引号
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2018', "'").replace('\u2019', "'")

    # 3. 尝试修复不完整结尾：统计括号数量，补全缺失的 ]
    open_braces = text.count('{') - text.count('}')
    open_brackets = text.count('[') - text.count(']')

    if open_braces > 0:
        text += '}' * open_braces
    if open_brackets > 0:
        text += ']' * open_brackets

    return text


def _extract_partial_json(text: str) -> Optional[dict]:
    """
    正则逐字段提取（最后一层回退）。
    提取已知的字段名，构建部分 dict。
    """
    result: dict = {}

    # 标量字符串字段
    str_fields = [
        'major', 'grade', 'cognitive_style', 'learning_pace',
        'learning_goal_short', 'learning_goal_long',
        'follow_up_question', 'rationale',
    ]
    for field in str_fields:
        pattern = rf'"{field}"\s*:\s*"([^"]*)"'
        match = re.search(pattern, text)
        if match:
            result[field] = match.group(1)

    # is_complete (bool)
    bool_match = re.search(r'"is_complete"\s*:\s*(true|false)', text)
    if bool_match:
        result['is_complete'] = bool_match.group(1) == 'true'

    # interest_domains (字符串数组)
    domains_match = re.search(
        r'"interest_domains"\s*:\s*\[(.*?)\]', text, re.DOTALL
    )
    if domains_match:
        items = re.findall(r'"([^"]*)"', domains_match.group(1))
        if items:
            result['interest_domains'] = items

    # knowledge_base (对象数组)
    kb_match = re.search(
        r'"knowledge_base"\s*:\s*\[([\s\S]*?)\](\s*[,}\]])', text
    )
    if kb_match:
        kb_items = []
        for item_text in re.finditer(
            r'\{(.*?)\}', kb_match.group(1), re.DOTALL
        ):
            kp_id = re.search(r'"knowledge_point_id"\s*:\s*"([^"]*)"', item_text.group(1))
            kp_name = re.search(r'"knowledge_point_name"\s*:\s*"([^"]*)"', item_text.group(1))
            mastery = re.search(r'"mastery"\s*:\s*"([^"]*)"', item_text.group(1))
            if kp_id and kp_name:
                item = {
                    'knowledge_point_id': kp_id.group(1),
                    'knowledge_point_name': kp_name.group(1),
                }
                if mastery:
                    item['mastery'] = mastery.group(1)
                kb_items.append(item)
        if kb_items:
            result['knowledge_base'] = kb_items

    # weak_points (对象数组)
    wp_match = re.search(
        r'"weak_points"\s*:\s*\[([\s\S]*?)\](\s*[,}\]])', text
    )
    if wp_match:
        wp_items = []
        for item_text in re.finditer(
            r'\{(.*?)\}', wp_match.group(1), re.DOTALL
        ):
            kp_id = re.search(r'"knowledge_point_id"\s*:\s*"([^"]*)"', item_text.group(1))
            kp_name = re.search(r'"knowledge_point_name"\s*:\s*"([^"]*)"', item_text.group(1))
            err_pattern = re.search(r'"error_pattern"\s*:\s*"([^"]*)"', item_text.group(1))
            occ_count = re.search(r'"occurrence_count"\s*:\s*(\d+)', item_text.group(1))
            if kp_id and kp_name:
                item = {
                    'knowledge_point_id': kp_id.group(1),
                    'knowledge_point_name': kp_name.group(1),
                }
                if err_pattern:
                    item['error_pattern'] = err_pattern.group(1)
                if occ_count:
                    item['occurrence_count'] = int(occ_count.group(1))
                wp_items.append(item)
        if wp_items:
            result['weak_points'] = wp_items

    # 包含 extracted_fields 嵌套的情况
    ef_match = re.search(r'"extracted_fields"\s*:\s*(\{[\s\S]*?\})\s*[,}\]]', text)
    if ef_match:
        inner = _extract_partial_json(ef_match.group(1))
        if inner:
            result['extracted_fields'] = inner

    return result if result else None


# ── 公开 API ────────────────────────────────────────────────


def extract_json(text: str) -> tuple[Optional[dict], Optional[str]]:
    """
    从 LLM 输出文本中鲁棒提取 JSON 对象。

    按优先级尝试 6 种策略：
    1. 移除 ```json ... ``` 代码块标记
    2. 花括号计数法定位 JSON 对象
    3. json.loads() 直接解析
    4. repair_json() 修复后重试
    5. 正则逐字段提取部分 JSON
    6. 完全失败

    参数:
        text: LLM 原始输出文本

    返回:
        (parsed_dict, error_message)
        - 成功时 error_message 为 None
        - 失败时 parsed_dict 为 None
    """
    if not text or not text.strip():
        return None, "输入文本为空"

    errors: list[str] = []

    # Layer 1: 移除 code fence
    cleaned = _strip_code_fences(text)

    # Layer 2: 花括号计数定位 JSON 对象
    json_str = _find_json_object(cleaned)
    if json_str is None:
        return None, "未找到 JSON 对象（缺少 {} 括号）"

    # Layer 3: 直接解析
    try:
        result = json.loads(json_str)
        logger.debug("Layer 3 (直接解析) 成功")
        return result, None
    except json.JSONDecodeError as e:
        errors.append(f"直接解析失败: {e}")

    # Layer 4: 修复后重试
    repaired = _repair_json(json_str)
    try:
        result = json.loads(repaired)
        logger.debug("Layer 4 (修复后解析) 成功")
        return result, None
    except json.JSONDecodeError as e:
        errors.append(f"修复后解析失败: {e}")

    # Layer 5: 正则提取部分字段
    partial = _extract_partial_json(text)
    if partial:
        logger.debug(f"Layer 5 (正则提取) 成功, 提取了 {len(partial)} 个字段")
        return partial, None

    # Layer 6: 完全失败
    error_msg = "; ".join(errors)
    logger.warning(f"JSON 解析完全失败: {error_msg}")
    return None, error_msg


def repair_json(text: str) -> str:
    """
    修复常见 JSON 格式问题。

    包括：末尾多余逗号、中文引号、不完整括号。

    参数:
        text: 原始 JSON 文本

    返回:
        修复后的 JSON 文本
    """
    return _repair_json(text)
