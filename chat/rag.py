import json
import os
from langchain import hub
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate


class ConversationManager:
    def __init__(self):
        self.conversations = {}  # {session_id: [messages]}

    def add_message(self, session_id, role, content):
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        self.conversations[session_id].append({"role": role, "content": content})

    def get_history(self, session_id, max_turns=5):
        return self.conversations.get(session_id, [])[-max_turns*2:]

conv_manager = ConversationManager()


with open('data/processed/documents.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Prepare documents with metadata
documents = []
for id, doc in data.items():
    documents.append(Document(
        page_content=doc['content'],
        metadata={
            'id': id,
            'title': doc.get('title', ''),
            'url': doc.get('url', ''),
            'language': doc.get('language', ''),
            "topic_name": doc.get('topic_name', ''),
        }
    ))

# Configure local model path
model_name = "all-MiniLM-L6-v2"
model_path = os.path.join("models", model_name)

# Load or download model
if not os.path.exists(model_path):
    os.makedirs("models", exist_ok=True)
    # Download and save model
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    embeddings.client.save(model_path)
else:
    # Load from local
    embeddings = HuggingFaceEmbeddings(model_name=model_path)

# Check if vectorstore exists
vectorstore_path = "data/vectorstore"
if os.path.exists(vectorstore_path):
    # Load existing vectorstore
    vectorstore = Chroma(
        persist_directory=vectorstore_path,
        embedding_function=embeddings
    )
else:
    # Create new vectorstore
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=vectorstore_path
    )

retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 10})


api_key = os.environ["DEEPSEEK_API_KEY"]

llm = ChatOpenAI(
    model="deepseek-chat",
    temperature=1,
    max_tokens=None,
    timeout=None,
    max_retries=3,
    api_key=api_key,
    base_url="https://api.deepseek.com",
)
system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer "
    "the question. Consider the conversation history provided. "
    "If you don't know the answer, say that you don't know. "
    "Keep the answer concise but informative."
    "\n\n"
    "Conversation History:\n"
    "{history}\n\n"
    "Retrieved Context:\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        *[("human" if msg["role"] == "user" else "ai", msg["content"]) 
          for msg in []],  # Placeholder for history
        ("human", "{input}"),
    ]
)


question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

def get_rag_response(session_id, message):
    history = conv_manager.get_history(session_id)
    response = rag_chain.invoke({
        "input": message,
        "history": "\n".join(
            f"{msg['role']}: {msg['content']}" 
            for msg in history
        )
    })
    
    # Format retrieved documents for display
    retrieved_docs = []
    for doc in response["context"]:
        retrieved_docs.append({
            "content": doc.page_content,
            "title": doc.metadata.get("title", ""),
            "url": doc.metadata.get("url", ""),
            "language": doc.metadata.get("language", ""),
            "topic_name": doc.metadata.get("topic_name", "")
        })
    
    return {
        "answer": response["answer"],
        "documents": retrieved_docs,
        "context": response["context"]
    }
