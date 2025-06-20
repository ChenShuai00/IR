from flask import Flask, render_template, request, jsonify
from search.core import SearchEngine
from config.settings import WEB_CONFIG
import time
from pathlib import Path
from chat.rag import conv_manager, get_rag_response
import uuid

app = Flask(__name__,
            template_folder=WEB_CONFIG['template_dir'],
            static_folder=WEB_CONFIG['static_dir'])

# 初始化搜索引擎
try:
    search_engine = SearchEngine()
except Exception as e:
    print(f"Failed to initialize search engine: {str(e)}")
    search_engine = None


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat')
def chat_page():
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat_api():
    data = request.get_json()
    session_id = data.get('session_id', str(uuid.uuid4()))
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    try:
        # Add user message to history
        conv_manager.add_message(session_id, "user", message)
        
        # Get RAG response
        response = get_rag_response(session_id, message)
        
        # Add assistant response to history
        conv_manager.add_message(session_id, "assistant", response["answer"])
        
        return jsonify({
            'answer': response.get("answer", ""),
            'session_id': session_id,
            'documents': response.get("documents", []),
            'context': [doc.metadata for doc in response.get("context", [])] if response.get("context") else []
        })
    except Exception as e:
        return jsonify({
            'error': {
                'message': str(e),
                'type': type(e).__name__
            }
        }), 500


@app.route('/search')
def search():
    if not search_engine:
        return jsonify({'error': 'Search engine not available'}), 500

    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'results': []})

    # 获取分页参数
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    start_time = time.time()
    results = search_engine.search(query)
    elapsed_time = time.time() - start_time

    # 按语言分类结果
    zh_results = [r for r in results if r.get('language') == 'zh']
    en_results = [r for r in results if r.get('language') != 'zh']

    # 计算分页
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    return jsonify({
        'query': query,
        'time': elapsed_time,
        'results': {
            'zh': zh_results[start_idx:end_idx],
            'en': en_results[start_idx:end_idx]
        },
        'count': len(results),
        'zh_count': len(zh_results),
        'en_count': len(en_results),
        'page': page,
        'per_page': per_page,
        'total_pages': max(1, (len(results) + per_page - 1) // per_page)
    })

if __name__ == '__main__':
    app.run(
        host=WEB_CONFIG['host'],
        port=WEB_CONFIG['port'],
        # debug=WEB_CONFIG['debug']
        debug=False
    )
