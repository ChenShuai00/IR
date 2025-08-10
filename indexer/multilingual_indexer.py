import json
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm  # 进度条库
from config.settings import INDEX_CONFIG
from utils.tokenizer import tokenize
from utils.helpers import load_stopwords


class MultilingualIndexer:
    def __init__(self):
        self.index_dir = Path(INDEX_CONFIG['index_dir'])
        self.documents_path = Path(INDEX_CONFIG['documents_path'])
        self.stopwords = {
            lang: load_stopwords(path)
            for lang, path in INDEX_CONFIG['stopwords'].items()
        }

        # 数据结构
        self.inverted_index = defaultdict(dict)
        self.documents = {}
        self.doc_lengths = {}
        self.avg_doc_length = 0

        # 创建目录（如果不存在）
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.documents_path.parent.mkdir(parents=True, exist_ok=True)

    def process_document(self, doc_id, document):
        """处理单个文档并更新索引"""
        try:
            # 防御性检查
            if not all(k in document for k in ['title', 'content', 'url']):
                raise ValueError("文档缺少必要字段")

            # 自动检测语言
            text = f"{document['title']} {document['content']}"
            language = 'zh' if any('\u4e00' <= c <= '\u9fff' for c in text) else 'en'

            # 分词处理
            tokens = tokenize(text, language)
            if not tokens:
                return 0  # 跳过空内容文档

            # 词频统计（过滤停用词和短词）
            term_freq = defaultdict(int)
            for token in tokens:
                if len(token) > 1 and token not in self.stopwords[language]:
                    term_freq[token] += 1

            # 更新倒排索引
            for term, tf in term_freq.items():
                self.inverted_index[term][doc_id] = tf

            # 存储文档元数据
            self.documents[doc_id] = {
                'url': document['url'],
                'title': document['title'],
                'content': document['content'],
                'language': language,
                'length': len(tokens)
            }

            return len(tokens)

        except Exception as e:
            print(f"\n处理文档 {doc_id} 时出错: {str(e)}")
            return 0

    def build_from_raw_data(self, raw_data_dir):
        """从原始数据构建索引"""
        files = list(Path(raw_data_dir).glob('*.json'))
        if not files:
            raise FileNotFoundError(f"未找到JSON文件于: {raw_data_dir}")

        total_length = 0

        # 使用tqdm进度条
        with tqdm(files, desc="🔄 构建索引", unit="doc",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
            for doc_id, filepath in enumerate(pbar):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        document = json.load(f)

                    length = self.process_document(doc_id, document)
                    total_length += length

                    # 动态更新进度条信息
                    pbar.set_postfix({
                        '词项': len(self.inverted_index),
                        'avg_len': f"{total_length / (doc_id + 1):.1f}" if doc_id > 0 else '0'
                    })

                except json.JSONDecodeError:
                    pbar.write(f"⚠️ 文件解析失败: {filepath.name}")
                except Exception as e:
                    pbar.write(f"⚠️ 处理 {filepath.name} 时出错: {str(e)}")

        # 计算平均文档长度
        if len(self.documents) > 0:
            self.avg_doc_length = total_length / len(self.documents)

        self.save_index()

    def save_index(self):
        """保存索引到文件"""
        # 保存倒排索引
        with open(self.index_dir / 'inverted_index.json', 'w', encoding='utf-8') as f:
            json.dump(self.inverted_index, f, ensure_ascii=False, indent=2)

        # 保存元数据
        with open(self.index_dir / 'meta.json', 'w', encoding='utf-8') as f:
            json.dump({
                'doc_lengths': {doc_id: doc['length']
                                for doc_id, doc in self.documents.items()},
                'avg_doc_length': self.avg_doc_length,
                'total_docs': len(self.documents)
            }, f, ensure_ascii=False, indent=2)

        # 保存文档数据
        with open(self.documents_path, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 索引构建完成！保存到: {self.index_dir}")


if __name__ == "__main__":
    try:
        indexer = MultilingualIndexer()
        indexer.build_from_raw_data('../data/raw_clean')  # 修改为您的实际路径
    except Exception as e:
        print(f"❌ 索引构建失败: {str(e)}")