from flask import Flask, render_template, request, jsonify
import jieba
from search.core import SearchEngine
from search import SpellChecker
from config.settings import WEB_CONFIG
from utils.language import detect_language
import time
from pathlib import Path
from chat.rag import conv_manager, get_rag_response
from chat.agent import get_agent_response
from chat.ReAct.Agent import ReAct, DeepSeekChat
import uuid

react = ReAct(DeepSeekChat())

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

@app.route('/api/agent', methods=['POST'])
def agent_api():
    data = request.get_json()
    session_id = data.get('session_id', str(uuid.uuid4()))
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    try:
        # Get conversation history
        history = conv_manager.get_history(session_id)
        
        # Get agent response
        response = get_agent_response(react, text=message, history=history)

        # Add messages to history
        conv_manager.add_message(session_id, "user", message)
        conv_manager.add_message(session_id, "assistant", response)
        
        return jsonify({
            'answer': response,
            'session_id': session_id
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

@app.route('/spellcheck/suggest')
def spell_suggest():
    spell_checker = SpellChecker()
    if not search_engine:
        return jsonify({'error': 'Search engine not available'}), 500

    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'suggestions': []})

    try:
        # 获取拼写建议
        suggestions = spell_checker._get_english_suggestions(query) if detect_language(query) == 'en' \
                     else spell_checker._get_chinese_suggestions(query)

        return jsonify({
            'suggestions': suggestions[:3]  # 返回最多3个建议
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'suggestions': []
        })

@app.route('/synonyms/suggest')
def synonym_suggest():
    from search.synonym_expander import SynonymExpander
    synonym_expander = SynonymExpander()
    if not search_engine:
        return jsonify({'error': 'Search engine not available'}), 500

    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'synonyms': []})

    try:
        # 获取同义词建议
        language = detect_language(query)
        if language == 'zh':
            words = [w for w in jieba.cut(query) if w.strip()]
        else:
            words = query.split()

        synonyms = []
        for word in words:
            if language == 'zh':
                word_synonyms = synonym_expander.thesaurus['zh'].get(word, [])[:3]
            else:
                word_synonyms = synonym_expander.thesaurus['en'].get(word.lower(), [])[:3]
            
            if word_synonyms:
                synonyms.append({
                    'word': word,
                    'synonyms': word_synonyms
                })

        return jsonify({
            'synonyms': synonyms
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'synonyms': []
        })

if __name__ == '__main__':
    app.run(
        host=WEB_CONFIG['host'],
        port=WEB_CONFIG['port'],
        # debug=WEB_CONFIG['debug']
        debug=False
    )
