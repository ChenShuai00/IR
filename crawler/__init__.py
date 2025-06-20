"""Web Crawlers Package"""
from .multilingual_spider import MultilingualSpider

__all__ = ['MultilingualSpider']

def __init__(self):
    super().__init__()
    print(f"待爬取初始URL数量: {len(self.urls_to_visit)}")  # 检查种子URL是否加载
    print(f"种子URL示例: {list(self.urls_to_visit)[:3]}")    # 打印前3个URL