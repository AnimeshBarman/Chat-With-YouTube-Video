export interface VideoResponse {
  status: string;
  video_id: string;
  language: string;
  title: string;
}

export interface SummaryResponse {
  summary: string;
  detail?: string; // For 202 processing message
}

export interface ChatMessage {
  role: 'user' | 'bot';
  text: string;
}

export interface ChatResponse {
  answer: string;
}