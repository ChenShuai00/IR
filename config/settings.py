import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# 爬虫配置
CRAWLER_CONFIG = {
    'seed_urls': {
        'en': [
            'https://research.google/blog/',
            'https://openai.com/news/',
            'https://deepmind.com/blog',
            'https://www.microsoft.com/en-us/research/blog/category/artificial-intelligence/',
            'https://blog.tensorflow.org/',
            'https://ai.meta.com/blog/'
        ],
        'zh': [
            'https://www.jiqizhixin.com/',  # 机器之心
            'https://ai.baidu.com/support/news',  # 百度AI博客
            'https://cloud.tencent.com/developer?tab=2'
        ]
    },
    'max_pages': 10000,
    'output_dir': BASE_DIR / 'data/raw_',
    'request_delay': (0.5, 1.5),
    'timeout': 10,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# 索引配置
INDEX_CONFIG = {
    'index_dir': BASE_DIR / 'data/index',
    'documents_path': BASE_DIR / 'data/processed/documents.json',
    'stopwords': {
        'en': BASE_DIR / 'config/stopwords/en_stopwords.txt',
        'zh': BASE_DIR / 'config/stopwords/zh_stopwords.txt'
    }
}

# 搜索配置
SEARCH_CONFIG = {
    'spellcheck': {
        'en_dict': BASE_DIR / 'config/spellcheck/en_dict.txt',
        'zh_dict': BASE_DIR / 'config/spellcheck/zh_dict.txt'
    },
    'synonyms': {
        'en': BASE_DIR / 'config/synonyms/en_thesaurus.txt',
        'zh': BASE_DIR / 'config/synonyms/zh_thesaurus.txt'
    },
    'default_results': 100,
    'max_snippet_length': 200
}

# Web配置
WEB_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True,
    'template_dir': BASE_DIR / 'templates',
    'static_dir': BASE_DIR / 'static'
}