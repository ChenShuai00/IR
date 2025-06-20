import re
from urllib.parse import urlparse


def detect_language(text_or_url):
    """检测文本或URL的语言"""
    # 如果是URL，根据域名判断
    if text_or_url.startswith('http'):
        domain = urlparse(text_or_url).netloc
        if any(d in domain for d in ['leiphone.com', 'jiqizhixin.com','aixinzhijie.com','baidu.com','tencent.com']):
            return 'zh'
        return 'en'

    # 如果是文本，根据字符判断
    zh_pattern = re.compile(r'[\u4e00-\u9fa5]')
    zh_chars = len(zh_pattern.findall(text_or_url))
    return 'zh' if zh_chars / max(1, len(text_or_url)) > 0.3 else 'en'