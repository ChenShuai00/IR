import json
import math
import re
from pathlib import Path
from collections import defaultdict
from config.settings import INDEX_CONFIG, SEARCH_CONFIG
from indexer import MultilingualIndexer
from utils.tokenizer import tokenize
from utils.language import detect_language
from .spellcheck import SpellChecker
from .synonym_expander import SynonymExpander


class SearchEngine:
    def __init__(self):
        # 初始化组件
        self.all_doc_ids = set( [str(i) for i in range(12500)])
        self.spellchecker = SpellChecker()
        self.synonym_expander = SynonymExpander()


        # 加载索引
        self._load_index()

    def _load_index(self):
        """加载索引数据"""
        index_dir = Path(INDEX_CONFIG['index_dir'])

        # 加载倒排索引
        with open(index_dir / 'inverted_index.json', 'r', encoding='utf-8') as f:
            self.inverted_index = json.load(f)

        # 加载元数据
        with open(index_dir / 'meta.json', 'r', encoding='utf-8') as f:
            meta = json.load(f)
            self.doc_lengths = meta['doc_lengths']
            self.avg_doc_length = meta['avg_doc_length']
            self.total_docs = meta['total_docs']

        # 加载文档
        with open(INDEX_CONFIG['documents_path'], 'r', encoding='utf-8') as f:
            self.documents = json.load(f)

    def preprocess_query(self, query):
        """查询预处理：拼写纠正+同义词扩展"""
        # 拼写纠正
        corrected = self.spellchecker.correct(query)

        # 同义词扩展
        expanded = self.synonym_expander.expand(corrected)
        # expanded if expanded != corrected else corrected

        return corrected

    def search(self, query, top_n=None):
        """执行搜索"""
        if top_n is None:
            top_n = SEARCH_CONFIG['default_results']

        # 预处理查询
        processed_query = self.preprocess_query(query)
        language = detect_language(query)

        # 布尔检索
        doc_ids = self._boolean_search(processed_query, language)

        # 相关性排序
        ranked_docs = self._rank_documents(processed_query, doc_ids, language)

        # 准备结果
        results = []
        for doc_id in ranked_docs[:top_n]:
            doc = self.documents[str(doc_id)]
            results.append({
                'title': doc['title'],
                'url': doc['url'],
                'snippet': self._generate_snippet(doc['content'], processed_query, language),
                'language': doc.get('language', 'en'),
                'score': doc.get('score', 0),
                'category': doc.get('topic_name', '未分类'),
            })

        return results


    # def _boolean_search(self, query, language):
    #     try:
    #         tokens = self._parse_simple_boolean_query(query, language)
    #     except ValueError as e:
    #         return []  # 或抛出异常给前端显示错误信息
    #
    #     if not tokens:
    #         return []
    #
    #     result_docs = None
    #     current_operator = None
    #
    #     for token in tokens:
    #         term = token['term']
    #         operator = token['operator']  # 当前词项的"左操作符"
    #
    #         # 获取文档集合（带缓存优化）
    #         current_docs = set(self.inverted_index.get(term, {}).keys())
    #
    #         # 初始情况
    #         if result_docs is None:
    #             result_docs = current_docs
    #             current_operator = operator
    #             continue
    #
    #         # 应用操作符
    #         if current_operator == 'AND':
    #             result_docs &= current_docs
    #         elif current_operator == 'OR':
    #             result_docs |= current_docs
    #         elif current_operator == 'NOT':
    #             result_docs -= current_docs
    #
    #         # 更新下一个操作符
    #         current_operator = operator
    #
    #         # 短路优化
    #         if not result_docs and current_operator == 'AND':
    #             break
    #
    #     return sorted(int(doc_id) for doc_id in result_docs) if result_docs else []

    def _boolean_search(self, query, language):
        try:
            tokens = self._parse_simple_boolean_query(query, language)
        except ValueError as e:
            return []

        if not tokens:
            return []

        result_docs = None

        for token in tokens:
            term = token['term']
            operator = token['operator']

            current_docs = set(self.inverted_index.get(term, {}).keys())
            print(f"current_docs:{current_docs}")

            if result_docs is None:

                result_docs = current_docs
            else:
                if operator == 'AND':
                    result_docs &= current_docs
                elif operator == 'OR':
                    result_docs |= current_docs
                elif operator == 'NOT':
                    result_docs -= current_docs  # ✅ 正确：从现有结果中减去当前 term 的文档

        return sorted(int(doc_id) for doc_id in result_docs) if result_docs else []

    def _parse_simple_boolean_query(self, query, language):
        """
        修复版布尔查询解析器
        正确处理形如 "AI OR LLM" 的查询
        """
        import re

        # 使用正则分割查询
        parts = re.split(r'\s+(AND|OR|NOT)\s+', query, flags=re.IGNORECASE)

        print(f"parts:{parts}")

        # 检查第一个元素是否是操作符（非法情况）
        if len(parts) > 0 and parts[0].upper() in ['AND', 'OR', 'NOT']:
            raise ValueError("查询不能以操作符开始")

        tokens = []
        next_operator = None  # 下一个词项的操作符
        this_operator = None

        for item in parts:
            if item.upper() in ['AND', 'OR', 'NOT']:
                next_operator = item.upper()
            else:
                # 分词并添加词项
                sub_tokens = tokenize(item, language)
                for term in sub_tokens:
                    tokens.append({
                        'term': term,
                        'operator': next_operator
                    })
                next_operator = None  # 重置操作符

        # 第一个词项不应有操作符
        if tokens:
            tokens[0]['operator'] = None

        print(f"tokens:{tokens}")

        return tokens

    def _rank_documents(self, query, doc_ids, language):
        """基于BM25的相关性排序"""
        tokens = tokenize(query, language)
        if not tokens or not doc_ids:
            return []

        # BM25参数
        k1 = 1.5
        b = 0.75

        scores = defaultdict(float)

        for term in tokens:
            if term not in self.inverted_index:
                continue

            # 计算IDF
            df = len(self.inverted_index[term])
            idf = math.log((self.total_docs - df + 0.5) / (df + 0.5)) + 1.0

            for doc_id in doc_ids:
                doc_id_str = str(doc_id)
                if doc_id_str not in self.inverted_index[term]:
                    continue

                tf = self.inverted_index[term][doc_id_str]
                doc_length = self.doc_lengths[doc_id_str]

                # 计算BM25分数
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * doc_length / self.avg_doc_length)
                scores[doc_id] += idf * numerator / denominator

        # 按分数排序
        return sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    def _generate_snippet(self, content, query, language):
        """生成摘要片段"""
        max_len = SEARCH_CONFIG['max_snippet_length']
        query_terms = set(tokenize(query, language))

        if language == 'zh':
            # 中文摘要
            sentences = re.split(r'[。！？]', content)
            for sentence in sentences:
                if any(term in sentence for term in query_terms):
                    return self._truncate_text(sentence, max_len)
        else:
            # 英文摘要
            sentences = re.split(r'[.!?]', content)
            for sentence in sentences:
                if any(term.lower() in sentence.lower() for term in query_terms):
                    return self._truncate_text(sentence, max_len)

        return self._truncate_text(content, max_len)

    def _truncate_text(self, text, max_length):
        """截断文本"""
        return text[:max_length] + ('...' if len(text) > max_length else '')

    def get_processed_query(self, query):
        """返回查询处理过程信息"""
        corrected = self.spellchecker.correct(query)
        expanded = self.synonym_expander.expand(corrected)

        return {
            'corrected': corrected if corrected != query else None,  # 无纠正时返回None
            'expanded': expanded if expanded != corrected else None  # 无扩展时返回None
        }
