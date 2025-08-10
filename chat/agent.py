
def get_agent_response(agent,text, history=None):
    if history is None:
        history = [{"role": "system", "content": agent.system_prompt}]
    
    # Convert history format if needed
    react_history = []
    for msg in history:
        if msg['role'] == 'user':
            react_history.append({"role": "user", "content": msg['content']})
        elif msg['role'] == 'assistant':
            react_history.append({"role": "assistant", "content": msg['content']})
    
    response = agent.text_completion(text=text, history=react_history)
    return response
