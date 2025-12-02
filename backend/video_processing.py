import os
import requests
import urllib.parse as urlparse
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
# from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings


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
        print(full_transcript)

        return full_transcript, "detected", video_title
    
    except Exception as e:
        print(f"Error fetching transcript from API: {e}")
        return None, None, video_title


def create_vector_store(transcript: str):

    print("Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_text(transcript)
    
    print("Generating embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    print("Creating FAISS vector store...")
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    
    print("Vector store created successfully.")
    return vector_store