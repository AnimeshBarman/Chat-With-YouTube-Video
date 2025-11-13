import urllib.parse as urlparse
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

import yt_dlp
import os
import re
import shutil

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

def _parse_vtt_file(filepath: str):

    transcript = []
    print(f"Parsing VTT file: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('WEBVTT') or '-->' in line or line.startswith('Kind:') or line.startswith('Language:'):
            continue
        
        line = re.sub(r'<[^>]+>', '', line)
        transcript.append(line)
        
    return " ".join(transcript)


def get_transcript(video_url: str, video_id: str):

    temp_sub_dir = f"./temp_subs_{video_id}"
    if not os.path.exists(temp_sub_dir):
        os.makedirs(temp_sub_dir)

    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'sublangs': ['en', 'hi'], 
        'skip_download': True,
        'subformat': 'vtt',
        'outtmpl': os.path.join(temp_sub_dir, '%(id)s.%(language)s.%(ext)s'),
    }

    try:
        print("Downloading subtitles with yt-dlp...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        
        vtt_filepath = None
        downloaded_lang = None
        
        files_in_dir = os.listdir(temp_sub_dir)
        
        for f in files_in_dir:
            if f.endswith('.vtt') and (f'.en.' in f or f.startswith(f'{video_id}.en')):
                vtt_filepath = os.path.join(temp_sub_dir, f)
                downloaded_lang = 'en'
                break 

        if not vtt_filepath:
            for f in files_in_dir:
                if f.endswith('.vtt') and (f'.hi.' in f or f.startswith(f'{video_id}.hi')):
                    vtt_filepath = os.path.join(temp_sub_dir, f)
                    downloaded_lang = 'hi'
                    break 
        
        if not vtt_filepath:
            for f in files_in_dir:
                if f.endswith('.vtt'):
                    vtt_filepath = os.path.join(temp_sub_dir, f)
                    try:
                        downloaded_lang = f.split('.')[-2]
                    except:
                        downloaded_lang = 'unknown'
                    break

        if not vtt_filepath:
            raise Exception("No .vtt subtitle files found by yt-dlp in the directory.")
        

        print(f"Found transcript file: {vtt_filepath}")
        full_transcript = _parse_vtt_file(vtt_filepath)

        print(full_transcript)
        
        return full_transcript, downloaded_lang

    except Exception as e:
        print(f"Error in get_transcript (yt-dlp): {e}")
        return None, None
    
    finally:
        if os.path.exists(temp_sub_dir):
            shutil.rmtree(temp_sub_dir)
            print(f"Cleaned up temp directory: {temp_sub_dir}")


def create_vector_store(transcript: str):

    print("Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_text(transcript)
    
    print("Generating embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    print("Creating FAISS vector store...")
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    
    print("Vector store created successfully.")
    return vector_store