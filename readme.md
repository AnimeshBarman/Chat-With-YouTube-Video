# Chat with YT (YouTube Video Chatbot)

This project is a powerful backend API that allows you to "chat" with any YouTube video. It fetches the video transcript, processes it using an AI Language Model, and allows you to ask questions, get summaries, and retrieve information from the video content.

This backend is built to be fast and responsive, using background tasks to handle slow processes like summarization, ensuring the user can start chatting immediately.

## 🚀 Core Features

* **Chat with Video:** Ask specific questions about the video's content.
* **Conversational Memory:** The chatbot remembers previous questions, allowing for follow-up conversations.
* **Full Video Summarization:** Get a complete summary of the entire video, generated in the background.
* **Fast Processing:** The user can start chatting (Q&A) almost immediately while the full summary is prepared in the background.
* **Multilingual Support:** Uses `yt-dlp` and multilingual embedding models to support videos in various languages (e.g., English, Hindi).

## 🛠️ Tech Stack

* **Framework:** **FastAPI** for the high-performance, asynchronous API.
* **AI Core:** **LangChain** to manage all AI logic, memory, and data flows.
* **Transcript Fetching:** **`yt-dlp`** for reliably downloading video transcripts.
* **Vector Store:** **FAISS** (in-memory) for creating fast and efficient semantic search indexes from the transcript.
* **LLM:** **Mistral-7B** (or any other) via **Hugging Face Hub**.
* **Embeddings:** **`paraphrase-multilingual-MiniLM-L12-v2`** (a multilingual model) to understand text from different languages.

## ⚙️ How It Works (Architecture)

This project uses two different AI techniques for its two main features:

1.  **For Q&A (`/chat`):**
    * **RAG (Retrieval-Augmented Generation):** When you ask a question, the system searches the FAISS vector store for the 5 most relevant "chunks" of the transcript.
    * **ConversationalRetrievalChain:** This chain takes your question, the chat history, and the retrieved chunks to generate an accurate answer, providing a seamless chat experience.

2.  **For Summarization (`/summarize_video`):**
    * **Background Task:** When a video is first processed, a background job is started.
    * **MapReduce:** This job uses LangChain's `load_summarize_chain` to read *all* chunks of the video, create small summaries for each, and then combine those small summaries into one final, comprehensive summary.
    * **Fetch on Demand:** The `/summarize_video` endpoint simply retrieves this pre-generated summary once it's ready.

## 🏁 Getting Started

### 1. Clone the Repository

```bash
git clone [https://github.com/AnimeshBarman/Chat-with-YT.git](https://github.com/AnimeshBarman/Chat-with-YT.git)
cd Chat-with-YT