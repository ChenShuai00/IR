import time
from urllib.parse import urlparse

import jieba
from bs4 import BeautifulSoup
from crawler.base_spider import BaseSpider
from config.settings import CRAWLER_CONFIG
from utils.language import detect_language
from pathlib import Path


class MultilingualSpider(BaseSpider):
    def __init__(self):
        super().__init__()
        # 初始化中英文URL队列
        for lang, urls in CRAWLER_CONFIG['seed_urls'].items():
            self.urls_to_visit.update(urls)

        # 初始化中文分词器
        jieba.initialize()
        for keyword in ['人工智能', '机器学习', '深度学习']:
            jieba.add_word(keyword)

    def extract_article(self, url, soup):
        """提取文章内容（多语言支持）"""
        language = detect_language(url)

        title = soup.title.get_text().strip() if soup.title else ""
        content = self._extract_content(soup, language)

        if not content:
            return None

        return {
            'url': url,
            'title': title,
            'content': content,
            'language': language,
            'timestamp': time.time()
        }

    def _extract_content(self, soup, language):
        """根据语言提取内容"""
        if language == 'zh':
            return self._extract_chinese_content(soup)
        return self._extract_english_content(soup)

    def _extract_chinese_content(self, soup):
        """提取中文内容"""
        # 尝试查找常见的中文内容区域
        content_blocks = []
        for selector in ['.article-content', '.content', '.post-body']:
            blocks = soup.select(selector)
            if blocks:
                content_blocks.extend(blocks)

        if not content_blocks:
            # 回退方案：获取所有段落
            content_blocks = soup.find_all('p')

        return '\n\n'.join([p.get_text().strip() for p in content_blocks])

    def _extract_english_content(self, soup):
        """提取英文内容"""
        paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if len(text.split()) > 5:  # 忽略短段落
                paragraphs.append(text)
        return '\n\n'.join(paragraphs)

    def _is_chinese_url(self, url):
        """更准确的中文URL检测"""
        zh_domains = {
            'leiphone.com', 'jiqizhixin.com',  # 配置中的中文站
            'baidu.com', 'tencent.com'  # 潜在关联域名
        }
        return urlparse(url).netloc in zh_domains

    def run(self):
        """运行多语言爬虫"""
        while self.urls_to_visit and self.crawled_count < self.max_pages:

            zh_count = sum(1 for u in self.visited_urls if self._is_chinese_url(u))
            en_count = len(self.visited_urls) - zh_count

            # 如果中文太少，优先抓取中文URL
            if zh_count < en_count // 3:  # 中文至少占25%
                next_url = next((u for u in self.urls_to_visit if self._is_chinese_url(u)), None)
                url = next_url or self.urls_to_visit.pop()
            else:
                url = self.urls_to_visit.pop()


            # url = self.urls_to_visit.pop()

            if url in self.visited_urls:
                continue

            self.visited_urls.add(url)

            response = self.fetch_page(url)
            if not response:
                continue

            # 根据语言设置编码
            language = detect_language(url)
            if language == 'zh':
                response.encoding = 'utf-8'

            soup = BeautifulSoup(response.content.decode('utf-8', errors='ignore'), 'html.parser')
            article = self.extract_article(url, soup)
            self.save_article(article)

            # 提取新链接
            self.extract_links(url, soup)

            print(f"Crawled {self.crawled_count}/{self.max_pages}: {url}")

        print(f"Crawling completed. Total pages crawled: {self.crawled_count}")

if __name__ == "__main__":
    AI_news_spider = MultilingualSpider()
    AI_news_spider.run()
