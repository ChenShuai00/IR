from typing import Dict, List, Optional, Tuple, Union
from openai import OpenAI
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


class BaseModel:
    def __init__(self, path: str = '') -> None:
        self.path = path

    def chat(self, prompt: str, history: List[dict]) -> str:
        pass

    def load_model(self):
        pass

class InternLM2Chat(BaseModel):
    def __init__(self, path: str = '') -> None:
        super().__init__(path)
        self.load_model()

    def load_model(self):
        print('================ Loading model ================')
        self.tokenizer = AutoTokenizer.from_pretrained(self.path, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(self.path, torch_dtype=torch.float16, trust_remote_code=True).cuda().eval()
        print('================ Model loaded ================')

    def chat(self, prompt: str, history: List[dict], meta_instruction:str ='') -> str:
        response, history = self.model.chat(self.tokenizer, prompt, history, temperature=0.1, meta_instruction=meta_instruction)
        return response, history

class DeepSeekChat(BaseModel):
    def __init__(self, path: str = '', model: str = "deepseek-chat") -> None:
        super().__init__(path)
        self.model = model
        self.api_key=os.getenv("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com"

    def chat(self, prompt: str, history: List[dict]) -> str:
        client = OpenAI(api_key=self.api_key, base_url = self.base_url)
        history.append(
            {"role": "user", "content": prompt},
        ),
        response = client.chat.completions.create(
            model=self.model,
            messages=history,
            max_tokens=4096,
            temperature=1
        )
        return response.choices[0].message.content
    
if __name__ == '__main__':
    model = DeepSeekChat()
    print(model.chat('Hello', []))