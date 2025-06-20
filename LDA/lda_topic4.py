import json
import jieba
import matplotlib.pyplot as plt
from gensim import corpora, models
from gensim.models import CoherenceModel
import os


# 加载停用词
def load_stopwords(stopwords_path):
    with open(stopwords_path, 'r', encoding='utf-8') as f:
        stopwords = set([line.strip() for line in f])
    return stopwords

# 文本预处理
def preprocess_text(text, stopwords):
    import re
    # 去除标点等特殊字符
    text = re.sub(r'[^\w\s]', '', text)
    words = jieba.cut(text)
    return [word for word in words 
           if word not in stopwords 
           and not word.isascii() 
           and len(word) > 1]

# 读取JSON文件
def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# 主函数
def main():
    # 配置路径
    stopwords_path = 'config/stopwords/zh_stopwords.txt'
    documents_path = 'data/processed/documents.json'
    
    # 加载停用词
    stopwords = load_stopwords(stopwords_path)
    
    # 预处理中文文档
    data = read_json_file(documents_path)
    texts = []
    doc_ids = []
    for doc_id, doc in data.items():
        if 'content' in doc and doc.get('language') == 'zh':
            texts.append(preprocess_text(doc['content'], stopwords))
            doc_ids.append(doc_id)
    
    print(f"共处理 {len(texts)} 篇中文文档")
    
    # 创建词典和词袋
    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]
    
    # 创建主题数为4的LDA模型
    print("\n创建主题数为4的LDA模型...")
    lda_model = models.LdaModel(corpus=corpus,
                              id2word=dictionary,
                              num_topics=2,
                              passes=15)
    
    # 计算模型质量指标
    coherence_model = CoherenceModel(model=lda_model, 
                                   texts=texts, 
                                   dictionary=dictionary, 
                                   coherence='c_v')
    coherence = coherence_model.get_coherence()
    perplexity = lda_model.log_perplexity(corpus)
    
    print(f"\n模型评估指标:")
    print(f"一致性得分: {coherence:.4f}")
    print(f"困惑度: {perplexity:.4f}")
    
    # 输出主题分布
    print("\n主题分布:")
    for idx, topic in lda_model.print_topics(-1):
        print(f"Topic #{idx}: {topic}")
        print()
    
    # 为每个文档分配主题
    print("\n文档主题分配:")
    doc_topics = {}
    for i, doc_id in enumerate(doc_ids):
        bow = corpus[i]
        topic_dist = lda_model.get_document_topics(bow)
        dominant_topic = max(topic_dist, key=lambda x: x[1])[0]
        doc_topics[doc_id] = dominant_topic

    
    # 定义主题名称映射
    topic_names = {
        0: "技术",
        1: "应用"
    }
    
    # 更新原始数据并保存
    for doc_id, topic in doc_topics.items():
        data[doc_id]['topic'] = topic
        data[doc_id]['topic_name'] = topic_names[topic]
    
    output_path = 'data/processed/documents_with_topics.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到 {output_path}")

if __name__ == "__main__":
    main()
