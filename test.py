from indexer import MultilingualIndexer

try:
    indexer = MultilingualIndexer()
    indexer.build_from_raw_data('./data/raw_clean')  # 修改为您的实际路径
except Exception as e:
        print(f"❌ 索引构建失败: {str(e)}")