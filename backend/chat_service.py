import os
from dotenv import load_dotenv
from operator import itemgetter

from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableBranch
from langchain_core.messages import AIMessage, HumanMessage

load_dotenv() 

def get_llm():
    api_key = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if not api_key:
        raise ValueError("HUGGINGFACEHUB_API_TOKEN not found in .env file.")
        
    llm_endpoint = HuggingFaceEndpoint(
        repo_id="MiniMaxAI/MiniMax-M2",
        huggingfacehub_api_token=api_key,
        task="conversational",
        max_new_tokens=512,
        temperature=0.1
    )

    llm = ChatHuggingFace(llm=llm_endpoint)
    return llm

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def create_chat_chain(vector_store):

    llm = get_llm()
    
    retriever = vector_store.as_retriever(
        search_kwargs = {'k': 4}
    )

    condense_question_template = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    condense_question_prompt = ChatPromptTemplate.from_messages([
        ("system", condense_question_template),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ])

    qa_template = (
    "You are an intelligent video assistant who has watched this video. "
    "Answer the user's question based ONLY on the video context provided below. "
    "Do not say 'According to the passage' or 'Based on the excerpt'. "
    "Answer directly and naturally. "
    "If the answer is not in the context, strictly say 'I couldn't find that information in the video.'\n\n"
    "Video Context:\n{context}"
)
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_template),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ])
    
    create_question_chain = (
        condense_question_prompt | llm | StrOutputParser()
    )

    conversation_chain = RunnableBranch(
        (
            lambda x: bool(x.get("chat_history")),
            create_question_chain,
        ),
        (lambda x: x["question"]),
    )

    rag_chain = (
        {
            "context": conversation_chain | retriever | format_docs,
            "question": lambda x: x["question"],
            "chat_history": lambda x: x.get("chat_history", []),
        }
        | qa_prompt
        | llm
        | StrOutputParser()
    )
 
    return rag_chain


def generate_summary(vector_store):
    
    print("Loading summarization chain..")

    llm = get_llm()

    docs = vector_store.similarity_search("comprehensive summary of the video content", k=7)
    if not docs:
        print("No content found..!")
        return "No content found to summarize.."
    
    # map_prompt = ChatPromptTemplate.from_template("Summarize this chunk:\n\n{context}")
    # map_chain = map_prompt | llm | StrOutputParser()

    # summaries = []

    # limited_docs = docs[:5]    
    # print(f"Processing {len(limited_docs)} chunks for summary...") 
    # for i, doc in enumerate(limited_docs):
    #     try:
    #         res = map_chain.invoke({"context": doc.page_content})
    #         summaries.append(res)
    #     except Exception as e:
    #         print(f"Error in map_chain.invoke {i}: {e}")


    # if not summaries: return "Failed to generate summary..!"
            

    combined_text = "\n\n".join([doc.page_content for doc in docs])

    summary_prompt = ChatPromptTemplate.from_template(
        "You are an expert video analyst. Read the context below and provide a structured summary.\n"
        "IMPORTANT: Output MUST be in English only.\n\n"
        "Output Format:\n"
        "1. A short abstract (2-3 sentences).\n"
        "2. 5-7 key bullet points.\n\n"
        "Strictly use this separator format:\n"
        "[Abstract Paragraph]\n"
        "###\n"
        "[Bullet Points]\n\n"
        "Context from video:\n{context}"
    )

    chain = summary_prompt | llm | StrOutputParser()
 
    try:
        print("Invoking LLM for Summary...")
        res = chain.invoke({"context": combined_text})
        print("Summary Generated Successfully!")
        return res
    except Exception as e:
        print(f"Summary Generation Failed: {e}")
        return f"Error: Could not generate summary. {str(e)}"