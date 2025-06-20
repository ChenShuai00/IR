import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import MaxNLocator
import numpy as np

# 设置中文显示和美观样式
plt.style.use('ggplot')  # 使用ggplot样式替代seaborn
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def plot_combined_metrics(coherence_scores, perplexity_scores, topic_nums):
    """
    绘制一致性分数和困惑度的组合图表
    """
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # 绘制一致性分数(左轴)
    color = 'tab:blue'
    ax1.set_xlabel('主题数')
    ax1.set_ylabel('一致性得分', color=color)
    ax1.plot(topic_nums, coherence_scores, 'o-', color=color, label='一致性')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
    
    # 绘制困惑度(右轴)
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('困惑度', color=color)
    ax2.plot(topic_nums, perplexity_scores, 's--', color=color, label='困惑度')
    ax2.tick_params(axis='y', labelcolor=color)
    
    # 添加标题和图例
    fig.suptitle('LDA模型评估指标', y=1.02)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center')
    
    plt.tight_layout()
    return fig

def plot_topic_quality(coherence_scores, topic_nums):
    """
    绘制主题质量雷达图
    """
    # 归一化处理
    scores = np.array(coherence_scores)
    norm_scores = (scores - scores.min()) / (scores.max() - scores.min())
    
    angles = np.linspace(0, 2 * np.pi, len(topic_nums), endpoint=False)
    angles = np.concatenate((angles, [angles[0]]))
    norm_scores = np.concatenate((norm_scores, [norm_scores[0]]))
    
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(angles, norm_scores, 'o-', linewidth=2)
    ax.fill(angles, norm_scores, alpha=0.25)
    ax.set_thetagrids(angles[:-1] * 180/np.pi, topic_nums)
    ax.set_title('主题质量雷达图', y=1.1)
    ax.grid(True)
    
    return fig

if __name__ == "__main__":
    # 示例数据(使用用户提供的结果)
    topic_nums = [2, 3, 4, 5, 6, 7, 8]
    coherence_scores = [0.5549, 0.7174, 0.7981, 0.7018, 0.6107, 0.6959, 0.7188]
    perplexity_scores = [-9.3807, -9.2534, -9.2791, -9.2458, -9.4737, -9.4820, -9.5582]
    
    # 绘制组合图表
    fig1 = plot_combined_metrics(coherence_scores, perplexity_scores, topic_nums)
    fig1.savefig('lda_combined_metrics.png')
    
    # 绘制雷达图
    fig2 = plot_topic_quality(coherence_scores, topic_nums)
    fig2.savefig('lda_topic_quality_radar.png')
    
    print("可视化图表已保存为: lda_combined_metrics.png 和 lda_topic_quality_radar.png")
