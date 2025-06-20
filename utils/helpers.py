import json
import os
import re
from pathlib import Path
from config.settings import INDEX_CONFIG


def load_stopwords(filepath):
    """加载停用词表"""
    stopwords = set()
    if not Path(filepath).exists():
        return stopwords

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip()
            if word:
                stopwords.add(word)
    return stopwords


def normalize_text(text):
    """文本规范化处理"""
    if not text:
        return ""

    # 移除多余空白字符
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def contains_keywords(text, keywords):
    """检查文本是否包含关键词"""
    if not text or not keywords:
        return False

    text = text.lower()
    return any(keyword.lower() in text for keyword in keywords)


def load_documents(filepath):
    """加载文档数据"""
    if not Path(filepath).exists():
        return {}

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data, filepath):
    """保存JSON数据"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)