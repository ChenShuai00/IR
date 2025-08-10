from collections import Counter
import numpy as np
import jieba
from pathlib import Path
from config.settings import SEARCH_CONFIG
from utils.language import detect_language


class SpellChecker:
    def __init__(self):
        # 加载词典
        self.vocab = {
            'en': self._load_vocab(SEARCH_CONFIG['spellcheck']['en_dict']),
            'zh': self._load_vocab(SEARCH_CONFIG['spellcheck']['zh_dict'])
        }

    def _load_vocab(self, filepath):
        """加载词典文件"""
        if not Path(filepath).exists():
            return set()

        with open(filepath, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())

    def correct(self, text):
        """纠正拼写错误"""
        language = detect_language(text)
        if language == 'zh':
            return self._correct_chinese(text)
        return self._correct_english(text)

    def _correct_english(self, text):
        """纠正英文拼写"""
        words = text.split()
        corrected = []

        for word in words:
            if word.lower() in self.vocab['en']:
                corrected.append(word)
                continue

            # 寻找最相似的词
            suggestions = self._get_english_suggestions(word)
            corrected.append(suggestions[0] if suggestions else word)

        return ' '.join(corrected)

    def _correct_chinese(self, text):
        """纠正中文拼写"""
        words = list(jieba.cut(text))
        corrected = []

        for word in words:
            if word in self.vocab['zh']:
                corrected.append(word)
                continue

            # 寻找最相似的中文词
            suggestions = self._get_chinese_suggestions(word)
            corrected.append(suggestions[0] if suggestions else word)

        return ''.join(corrected)

    def _get_english_suggestions(self, word, max_distance=2):
        """获取英文拼写建议"""
        suggestions = []
        for vocab_word in self.vocab['en']:
            if abs(len(vocab_word) - len(word)) > max_distance:
                continue

            distance = self._edit_distance(word.lower(), vocab_word.lower())
            if distance <= max_distance:
                suggestions.append((vocab_word, distance))

        suggestions.sort(key=lambda x: x[1])
        return [s[0] for s in suggestions[:3]]

    def _get_chinese_suggestions(self, word):
        if not word or not self.vocab['zh']:
            return []
            # 如果词汇表中存在该词，认为拼写正确
        if word in self.vocab['zh']:
            return []
        suggestions = []
        # 1. 拼音相似性检查
       
        from pypinyin import pinyin, Style
        # 获取输入词的拼音
        word_pinyin = [item[0] for item in pinyin(word, style=Style.NORMAL)]
        for vocab_word in self.vocab['zh']:
            # 跳过长度差异大的词
            if abs(len(vocab_word) - len(word)) > 1:
                continue
            # 获取候选词拼音
            vocab_pinyin = [item[0] for item in pinyin(vocab_word, style=Style.NORMAL)]
            # 简单拼音相似度计算
            if word_pinyin == vocab_pinyin:
                # 拼音完全相同但字形不同（同音字）
                suggestions.append((vocab_word, 1))
            elif len(word_pinyin) == len(vocab_pinyin):
                # 拼音长度相同，计算相同拼音的数量
                same_pinyin = sum(1 for w, v in zip(word_pinyin, vocab_pinyin) if w == v)
                similarity = same_pinyin / len(word_pinyin)
                if similarity >= 0.5:  # 至少50%拼音相同
                    suggestions.append((vocab_word, 1 - similarity))
        
        # 2. 简单字形相似性检查
        if not suggestions:
            for vocab_word in self.vocab['zh']:
                if len(vocab_word) != len(word):
                    continue

                # 计算相同字符数
                same_chars = sum(1 for w, v in zip(word, vocab_word) if w == v)
                similarity = same_chars / len(word)
                if similarity >= 0.5:  # 至少50%字符相同
                    suggestions.append((vocab_word, 1 - similarity))

        # 3. 排序并返回前3个建议
        suggestions.sort(key=lambda x: x[1])  # 按相似度排序
        print(f"ZH suggestions{suggestions}")
        return [s[0] for s in suggestions[:3]]

    def _edit_distance(self, s1, s2):
        """计算编辑距离"""
        if len(s1) < len(s2):
            return self._edit_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]