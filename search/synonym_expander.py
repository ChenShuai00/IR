from collections import defaultdict
from pathlib import Path
from config.settings import SEARCH_CONFIG
from utils.language import detect_language
import jieba


# class SynonymExpander:
#     def __init__(self):
#         # 加载同义词词典
#         self.thesaurus = {
#             'en': self._load_thesaurus(SEARCH_CONFIG['synonyms']['en']),
#             'zh': self._load_thesaurus(SEARCH_CONFIG['synonyms']['zh'])
#         }
#
#         # 初始化中文分词
#         jieba.initialize()
#
#     def _load_thesaurus(self, filepath):
#         """加载同义词词典"""
#         thesaurus = defaultdict(list)
#         if not Path(filepath).exists():
#             return thesaurus
#
#         with open(filepath, 'r', encoding='utf-8') as f:
#             for line in f:
#                 if ':' in line:
#                     word, synonyms = line.strip().split(':', 1)
#                     thesaurus[word] = [s.strip() for s in synonyms.split(',')]
#         return thesaurus
#
#     def expand(self, query):
#         """扩展查询词"""
#         language = detect_language(query)
#         if language == 'zh':
#             return self._expand_chinese(query)
#         return self._expand_english(query)
#
#     def _expand_english(self, query):
#         """扩展英文查询"""
#         words = query.split()
#         expanded = []
#
#         for word in words:
#             expanded.append(word)
#             if word.lower() in self.thesaurus['en']:
#                 expanded.extend(self.thesaurus['en'][word.lower()][:2])  # 添加前2个同义词
#
#         print(f"en:{expanded}")
#         return ' '.join(expanded)
#
#     def _expand_chinese(self, query):
#         """扩展中文查询"""
#         words = list(jieba.cut(query))
#         expanded = []
#
#         for word in words:
#             expanded.append(word)
#             if word in self.thesaurus['zh']:
#                 expanded.extend(self.thesaurus['zh'][word][:2])  # 添加前2个同义词
#
#         print(f"zh:{expanded}")
#         return ''.join(expanded)


class SynonymExpander:
    def __init__(self):
        # 加载同义词词典
        self.thesaurus = {
            'en': self._load_thesaurus(SEARCH_CONFIG['synonyms']['en']),
            'zh': self._load_thesaurus(SEARCH_CONFIG['synonyms']['zh'])
        }

        # 定义布尔运算符集合（不区分大小写）
        self.boolean_operators = {'AND', 'OR', 'NOT'}

        # 初始化中文分词
        jieba.initialize()

    def _load_thesaurus(self, filepath):
        """加载同义词词典"""
        thesaurus = defaultdict(list)
        if not Path(filepath).exists():
            return thesaurus

        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if ':' in line:
                    word, synonyms = line.strip().split(':', 1)
                    thesaurus[word] = [s.strip() for s in synonyms.split(',')]
        return thesaurus

    def expand(self, query):
        """扩展查询词，同义词用 OR 连接，原运算符保留"""
        language = detect_language(query)
        if language == 'zh':
            return self._expand_chinese(query)
        return self._expand_english(query)

    def _expand_english(self, query):
        """处理英文查询：同义词用 OR 连接，原运算符保留"""
        tokens = query.split()
        expanded_tokens = []

        for token in tokens:
            # 如果是运算符，直接保留
            if token.upper() in self.boolean_operators:
                expanded_tokens.append(token)
            else:
                # 获取当前词及其同义词（最多2个）
                synonyms = [token]
                if token.lower() in self.thesaurus['en']:
                    synonyms.extend(self.thesaurus['en'][token.lower()][:2])
                # 用 OR 连接同义词组
                expanded_tokens.append(" OR ".join(synonyms))

        return ' '.join(expanded_tokens)

    def _expand_chinese(self, query):
        """处理中文查询：同义词用 OR 连接，原运算符保留"""
        # 使用 jieba 分词（注意：jieba 可能拆出空格，需过滤）
        words = [w for w in jieba.cut(query) if w.strip()]
        expanded_words = []

        for word in words:
            # 如果是运算符，直接保留（统一大写）
            if word.upper() in self.boolean_operators:
                expanded_words.append(word.upper())
            else:
                # 获取当前词及其同义词（最多2个）
                synonyms = [word]
                if word in self.thesaurus['zh']:
                    synonyms.extend(self.thesaurus['zh'][word][:2])
                # 用 OR 连接同义词组
                expanded_words.append(" OR ".join(synonyms))

        # 中文需重新组合（无空格）
        return ''.join(expanded_words)

