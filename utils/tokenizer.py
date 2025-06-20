import re
import jieba
from utils.language import detect_language
from config.settings import INDEX_CONFIG
from utils.helpers import load_stopwords


class Tokenizer:
    def __init__(self):
        self.stopwords = {
            'en': load_stopwords(INDEX_CONFIG['stopwords']['en']),
            'zh': load_stopwords(INDEX_CONFIG['stopwords']['zh'])
        }
        jieba.initialize()

    def tokenize(self, text, language='en'):
        """多语言分词"""
        if not text:
            return []

        text = text.lower()

        if language == 'zh':
            return self._tokenize_chinese(text)
        return self._tokenize_english(text)

    def _tokenize_chinese(self, text):
        """中文分词"""
        # 移除标点
        text = re.sub(r'[^\w\s\u4e00-\u9fa5]', '', text)
        words = jieba.lcut(text)
        return [word for word in words
                if word not in self.stopwords['zh'] and len(word) > 1]

    def _tokenize_english(self, text):
        """英文分词"""
        # 移除标点
        text = re.sub(r'[^\w\s]', ' ', text)
        words = re.findall(r'\w+', text)
        return [word for word in words
                if word not in self.stopwords['en'] and len(word) > 2]



tokenize = Tokenizer().tokenize  # 创建默认实例的快捷方式

__all__ = ['Tokenizer', 'tokenize']  # 导出列表