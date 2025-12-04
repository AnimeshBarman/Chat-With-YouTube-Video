import os
import requests
import urllib.parse as urlparse
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings


def get_video_id(video_url: str):

    try:
        parsed_url = urlparse.urlparse(video_url)
        
        if parsed_url.hostname and "youtube.com" in parsed_url.hostname:
            query_params = urlparse.parse_qs(parsed_url.query)
            
            if 'v' in query_params and query_params['v']:
                return query_params['v'][0]
            else:
                print("Error: 'v' parameter not found in YouTube URL.")
                return None
                
        elif parsed_url.hostname and "youtu.be" in parsed_url.hostname:

            return parsed_url.path[1:]
            
        else:
            print(f"Error: Unrecognized URL hostname: {parsed_url.hostname}")
            return None
            
    except Exception as e:
        print(f"Error parsing URL '{video_url}': {e}")
        return None


def get_video_title(video_id: str):
    try:
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        oembed_url = f"https://www.youtube.com/oembed?url={video_url}&format=json"
        response = requests.get(oembed_url)
        if response.status_code == 200:
            data = response.json()
            return data.get("title", "Unknown video title..")
        else:
            print(f"oEmbed Failed: {response.status_code}")
            return "Unknown video title..!"
    except Exception as e:
        print(f"Error fetching title: {e}")
        return "Video title not found..!"


def get_transcript(video_url: str, video_id: str):

    api_key = os.getenv("YOUTUBE_TRANSCRIPT_API_KEY")
    if not api_key:
        raise ValueError("Youtube transcript api key not found..!")
    
    video_title = get_video_title(video_id)
    print(f"Video title: {video_title}")

    print(f"Fetching transcript for: {video_id}..")

    url = "https://www.youtube-transcript.io/api/transcripts"
    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "ids": [video_id],
        "lang": "hi, en"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code} - {response.text}")
        
        data = response.json()

        # print(f"Api data: {data}")

        transcript_segment = []

        if isinstance(data, list):
            if len(data)>0:
                item = data[0]
                if 'transcript' in item:
                    transcript_segment = item['transcript']

                elif 'body' in item:
                    transcript_segment = item['body']
                else:
                    print(f"Unknown item key: {item.keys()}")
                    transcript_segment = data

        elif isinstance(data, dict):
            transcript_segment = data.get(video_id) or data.get('transcript')
        
        if not transcript_segment:
            raise Exception(f"No transcript found for ID: {video_id}")
        
        full_transcript = ""
        for seg in transcript_segment:
            text_part = seg.get('text') or seg.get('content') or ""
            full_transcript += text_part + " "

        if not full_transcript or len(full_transcript) < 10:
            raise Exception("Transcript text is empty..!")
        
        print("Transcript fetched successfully..")
        # print(full_transcript)

        return full_transcript, "detected", video_title
    
    except Exception as e:
        print(f"Error fetching transcript from API: {e}")
        return None, None, video_title
    

def get_embedding_JINA_batch(texts: List[str]) -> List[List[float]]:
    JINA_MODEL = "jina-embeddings-v2-base-en"
    JINA_API_KEY = os.getenv("JINA_API_KEY")
    if not JINA_API_KEY:
        raise ValueError("JINA_API_KEY not set in environment")

    try:
        url = "https://api.jina.ai/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {JINA_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": JINA_MODEL,
            "input": texts,
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        return [item["embedding"] for item in data["data"]]

    except Exception as e:
        print(f"Error with JINA: {e}")
        raise

def get_embedding_JINA(text: str) -> List[float]:
    return get_embedding_JINA_batch([text][0])



class JinaEmbeddings(Embeddings):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        all_vectors : List[List[float]] = []
        batch_size = 32
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            print(f"Jina batch {i}-{i + len(batch) - 1}")
            vectors = get_embedding_JINA_batch(batch)
            all_vectors.extend(vectors)
        return all_vectors

    def embed_query(self, text: str) -> List[float]:
        return get_embedding_JINA(text)


def create_vector_store(transcript: str):


    print("Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_text(transcript)

    MAX_CHUNKS = 120
    if len(chunks) > MAX_CHUNKS:
        chunks = chunks[:MAX_CHUNKS]
        print(f"Chunks trimmed to {MAX_CHUNKS}")
    
    print("Generating embeddings...")
    embeddings = JinaEmbeddings()    
    print("Creating FAISS vector store...")
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    
    print("Vector store created successfully.")
    return vector_store