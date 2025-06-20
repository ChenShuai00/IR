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

def evaluate_models(dictionary, corpus, texts, start=2, end=10, step=1):
    coherence_values = []
    perplexity_values = []
    model_list = []
    
    for num_topics in range(start, end+1, step):
        model = models.LdaModel(corpus=corpus,
                              id2word=dictionary,
                              num_topics=num_topics,
                              passes=15)
        model_list.append(model)
        
        # 计算主题一致性
        coherence_model = CoherenceModel(model=model, 
                                       texts=texts, 
                                       dictionary=dictionary, 
                                       coherence='c_v')
        coherence_values.append(coherence_model.get_coherence())
        
        # 计算困惑度
        perplexity_values.append(model.log_perplexity(corpus))
        
        print(f"主题数: {num_topics}, 一致性: {coherence_values[-1]:.4f}, 困惑度: {perplexity_values[-1]:.4f}")
    
    return model_list, coherence_values, perplexity_values

def plot_metrics(coherence_values, perplexity_values, start=2, end=10, step=1):
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    
    x = range(start, end+1, step)
    
    plt.figure(figsize=(12,5))
    
    # 绘制一致性曲线
    plt.subplot(1, 2, 1)
    plt.plot(x, coherence_values, 'b-')
    plt.xlabel("主题数")
    plt.ylabel("一致性得分")
    plt.title("主题一致性")
    
    # 绘制困惑度曲线
    plt.subplot(1, 2, 2)
    plt.plot(x, perplexity_values, 'r-')
    plt.xlabel("主题数")
    plt.ylabel("困惑度")
    plt.title("模型困惑度")
    
    plt.tight_layout()
    plt.savefig('lda_evaluation.png')
    plt.show()

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
    for doc_id, doc in data.items():
        if 'content' in doc and doc.get('language') == 'zh':
            texts.append(preprocess_text(doc['content'], stopwords))
    
    print(f"共处理 {len(texts)} 篇中文文档")
    
    # 创建词典和词袋
    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]
    
    # 评估不同主题数的模型
    print("\n评估不同主题数的模型质量:")
    model_list, coherence_values, perplexity_values = evaluate_models(dictionary, corpus, texts)
    
    # 绘制评估指标
    plot_metrics(coherence_values, perplexity_values)
    
    # 选择最优主题数(一致性最高)
    best_index = coherence_values.index(max(coherence_values))
    best_num_topics = range(2, 11)[best_index]
    print(f"\n最优主题数: {best_num_topics} (一致性得分: {coherence_values[best_index]:.4f})")
    
    # 输出最优模型的主题
    print("\n最优模型的主题分布:")
    for idx, topic in model_list[best_index].print_topics(-1):
        print(f"Topic #{idx}: {topic}")
        print()

if __name__ == "__main__":
    main()
