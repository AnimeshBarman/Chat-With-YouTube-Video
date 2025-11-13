import os
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv

load_dotenv() 

def get_llm():
    api_key = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if not api_key:
        raise ValueError("HUGGINGFACEHUB_API_TOKEN not found in .env file.")
        
    llm_endpoint = HuggingFaceEndpoint(
        repo_id="mistralai/Mistral-7B-Instruct-v0.2",
        huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
        task="conversational",
        max_new_tokens=512,
        temperature=0.1
    )

    llm = ChatHuggingFace(llm=llm_endpoint)
    return llm

def create_chat_chain(vector_store):

    llm = get_llm()
    
    retriever = vector_store.as_retriever(
        search_kwargs = {'k': 5}
    )
    

    memory = ConversationBufferMemory(
        memory_key="chat_history", 
        return_messages=True
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory
    )
    
    return chain