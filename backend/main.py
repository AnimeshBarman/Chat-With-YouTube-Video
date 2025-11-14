from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

import video_processing
import chat_service

load_dotenv() 

app = FastAPI(
    title="Chat with YouTube"
)


class VideoRequest(BaseModel):
    url: str

class ChatRequest(BaseModel):
    video_id: str
    question: str

class ChatResponse(BaseModel):
    answer: str

class SummarizeRequest(BaseModel):
    video_id: str

class SummarizeResponse(BaseModel):
    summary: str


vector_stores = {}
chat_chains = {}
summaries = {}


def generate_and_save_summary(video_id: str, vector_store):
    try:
        print(f"[BG task {video_id}]: summarization started..")
        docs = vector_store.similarity_seach("", k=1000)
        if not docs:
            print(f"{video_id}: docs not found..!")
            return
        
        summary_chain = chat_service.create_summarize_chain()
        result = summary_chain.run(docs)
        summaries[video_id] = result

    except Exception as e:
        print(f"{video_id}: summary generation failed..! ERROR: {e}")
        summaries[video_id] = f"Error: summary not generated.. {str(e)}"


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Server is running..."}

@app.post("/process_video")
def process_video(request: VideoRequest):

    video_id = video_processing.get_video_id(request.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL.")

    if video_id in vector_stores:
        return {"status": "success", "video_id": video_id, "message": "Already processed."}

    transcript, lang = video_processing.get_transcript(request.url, video_id)
    if not transcript:
        raise HTTPException(status_code=500, detail="Could not retrieve transcript.")

    try:
        vector_store = video_processing.create_vector_store(transcript)
        
        chat_chain = chat_service.create_chat_chain(vector_store)
        
        vector_stores[video_id] = vector_store
        chat_chains[video_id] = chat_chain

        print(f"Summarization task added to background..(ID: {video_id}).")
        BackgroundTasks.add_task(generate_and_save_summary, video_id, vector_store)
        
        return {
            "status": "success",
            "video_id": video_id,
            "language": lang
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating vector store: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    chat_chain = chat_chains.get(request.video_id)
    
    if not chat_chain:
        raise HTTPException(status_code=404, detail="Video not processed. Please call /process_video first.")

    try:
        print(f"Chatting with video: {request.video_id}")
        

        result = chat_chain.invoke({"question": request.question})
        
        return ChatResponse(answer=result['answer'])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during chat: {str(e)}")

@app.post("/summarize_video",response_model=SummarizeResponse)
def get_summary(request: SummarizeRequest):
    summary = summaries.get(request.video_id)

    if summary:
        if summary.startswith("Error:"):
            raise HTTPException(status_code=500, detail=summary)
        return SummarizeResponse(summary=summary)
    else:
        if request.video_id not in vector_stores:
            raise HTTPException(status_code=404, detail="Video not processed..!")
        else:
            raise HTTPException(status_code=202, detail="Summary not generated yet..!")
        


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)