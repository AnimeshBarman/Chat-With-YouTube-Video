import os
import requests
import urllib.parse as urlparse
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# import yt_dlp
# import re
# import shutil

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

# def _parse_vtt_file(filepath: str):

#     transcript = []
#     print(f"Parsing VTT file: {filepath}")
#     try:
#         with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
#             lines = f.readlines()
    
#         print(f"Parsing file: {filepath} (Total lines: {len(lines)})")

#         for line in lines:
#             line = line.strip()
#             if not line or line.startswith('WEBVTT') or '-->' in line or line.startswith('Kind:') or line.startswith('Language:'):
#                 continue
            
#             line = re.sub(r'<[^>]+>', '', line)

#             if line and not line.isdigit():
#                 if not transcript or transcript[-1] != line:
#                     transcript.append(line)
            
#         full_text =  " ".join(transcript)

#         if len(full_text) < 50:
#             print("Warnung: parsed text is too short..!")

#         return full_text
    
#     except Exception as e:
#         print(f"Error parsing vtt file: {e}")
#         return ""


def get_transcript(video_url: str, video_id: str):

    api_key = os.getenv("YOUTUBE_TRANSCRIPT_API_KEY")
    if not api_key:
        raise ValueError("Youtube transcript api key not found..!")
    
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

        return full_transcript, "detected"
    
    except Exception as e:
        print(f"Error fetching transcript from API: {e}")
        return None, None

    # temp_sub_dir = f"./temp_subs_{video_id}"
    # if not os.path.exists(temp_sub_dir):
    #     os.makedirs(temp_sub_dir)

    # ydl_opts = {
    #     'writesubtitles': True,
    #     'writeautomaticsub': True,
    #     'sublangs': ['hi', 'hi-latn', 'en'], 
    #     'skip_download': True,
    #     'subformat': 'vtt',
    #     'outtmpl': os.path.join(temp_sub_dir, '%(id)s.%(language)s.%(ext)s'),
    #     'http_headers': {
    #         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    #         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8',
    #         'Accept-Language': 'en-us,en;q=0.5',
    #         'Sec-Fetch-Mode': 'navigate',
    #     }
    # }

    # try:
    #     print("Downloading subtitles with yt-dlp...")
    #     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    #         ydl.download([video_url])
        
        
    #     vtt_filepath = None
    #     downloaded_lang = None
        
    #     files_in_dir = os.listdir(temp_sub_dir)
    #     print(f"Files found: {files_in_dir}")

    #     lang_priority = ['hi', 'hi-latn', 'en']
        
    #     for lang in lang_priority:
    #         for f in files_in_dir:
    #             if f.endswith('.vtt') and (f'.{lang}.' in f or f.startswith(f'{video_id}.{lang}')):
    #                 vtt_filepath = os.path.join(temp_sub_dir, f)
    #                 downloaded_lang = lang
    #                 break 
    #         if vtt_filepath:
    #             break

    #     if not vtt_filepath:
    #         for f in files_in_dir:
    #             if f.endswith('.vtt'):
    #                 vtt_filepath = os.path.join(temp_sub_dir, f)
    #                 downloaded_lang = 'unknown'
    #                 break 

    #     if not vtt_filepath:
    #         raise Exception("No .vtt subtitle files found by yt-dlp in the directory.")
        

    #     print(f"Found transcript file: {vtt_filepath}")
    #     full_transcript = _parse_vtt_file(vtt_filepath)

    #     if not full_transcript or len(full_transcript.strip()) == 0:
    #         raise Exception("Text extraction failed..!")
        

    #     print(full_transcript)
        
    #     return full_transcript, downloaded_lang

    # except Exception as e:
    #     print(f"Error in get_transcript (yt-dlp): {e}")
    #     return None, None
    
    # finally:
    #     if os.path.exists(temp_sub_dir):
    #         shutil.rmtree(temp_sub_dir)
    #         print(f"Cleaned up temp directory: {temp_sub_dir}")


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
        model_kwargs={'device':'cpu'}
    )
    
    print("Creating FAISS vector store...")
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    
    print("Vector store created successfully.")
    return vector_store