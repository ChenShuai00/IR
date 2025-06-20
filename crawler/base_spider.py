import json
import time
import random
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests
from pathlib import Path
from config.settings import CRAWLER_CONFIG


class BaseSpider:
    def __init__(self):
        self.visited_urls = set()
        self.urls_to_visit = set()
        self.output_dir = Path(CRAWLER_CONFIG['output_dir'])
        self.max_pages = CRAWLER_CONFIG['max_pages']
        self.crawled_count = 0

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def is_allowed_url(self, url):
        """检查URL是否在允许的域名内"""
        parsed = urlparse(url)
        allowed_domains = [
            urlparse(u).netloc
            for lang_urls in CRAWLER_CONFIG['seed_urls'].values()
            for u in lang_urls
        ]
        return any(domain in parsed.netloc for domain in allowed_domains)

    def extract_links(self, url, soup):
        """从页面提取链接"""
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            if self.is_allowed_url(full_url) and full_url not in self.visited_urls:
                self.urls_to_visit.add(full_url)

    def save_article(self, article):
        """保存文章到文件"""
        if not article:
            return

        filename = f"{hash(article['url'])}_{int(article['timestamp'])}.json"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(article, f, ensure_ascii=False, indent=2)

        self.crawled_count += 1

    def fetch_page(self, url):
        """获取页面内容"""
        delay = random.uniform(*CRAWLER_CONFIG['request_delay'])
        time.sleep(delay)

        try:
            response = requests.get(
                url,
                headers={'User-Agent': CRAWLER_CONFIG['user_agent']},
                timeout=CRAWLER_CONFIG['timeout']
            )
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None

    def run(self):
        """运行爬虫"""
        raise NotImplementedError("Subclasses must implement run() method")