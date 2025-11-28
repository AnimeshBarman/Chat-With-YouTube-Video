import { useState, useEffect, useRef } from "react";
import axios from "axios";
// Icons
import { Send, Loader2, FileVideo, Bot, User, Sparkles, FileText } from "lucide-react";
// Shadcn Components
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Toaster } from "@/components/ui/sonner"; 
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

import type { VideoResponse, ChatMessage } from "./types";

const API_URL = "http://localhost:8000";

function App() {
  // Video Processing States
  const [videoUrl, setVideoUrl] = useState("");
  const [videoData, setVideoData] = useState<VideoResponse | null>(null);
  const [loading, setLoading] = useState(false);
  
  // Summary States
  const [summary, setSummary] = useState<string | null>(null);
  const [isSummaryLoading, setIsSummaryLoading] = useState(false);

  // Chat States
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  
  const scrollRef = useRef<HTMLDivElement>(null);

  const handleProcessVideo = async () => {
    if (!videoUrl) return;
    setLoading(true);
    setVideoData(null);
    setSummary(null);
    setMessages([]);

    try {
      const res = await axios.post(`${API_URL}/process_video`, { url: videoUrl });
      setVideoData(res.data);
      startPollingSummary(res.data.video_id);
    } catch (error) {
      console.error("Error processing video:", error);
      toast.error("Failed to process video.");
    } finally {
      setLoading(false);
    }
  };

  const startPollingSummary = (videoId: string) => {
    setIsSummaryLoading(true);
    const interval = setInterval(async () => {
      try {
        const res = await axios.post(`${API_URL}/summarize_video`, { video_id: videoId });
        
        if (res.data.summary) {
          setSummary(res.data.summary);
          setIsSummaryLoading(false);
          clearInterval(interval);
          
          toast.success("Summary generated successfully!", {
            description: "Click 'View Summary' to read the insights.",
            duration: 4000,
          });
        }
      } catch (error: any) {
        if (error.response && error.response.status !== 202) {
        }
      }
    }, 5000);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !videoData) return;

    const userMsg = inputMessage;
    setMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setInputMessage("");
    setIsChatLoading(true);

    try {
      const res = await axios.post(`${API_URL}/chat`, {
        video_id: videoData.video_id,
        question: userMsg,
      });
      setMessages((prev) => [...prev, { role: "bot", text: res.data.answer }]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [...prev, { role: "bot", text: "Sorry, something went wrong." }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6 font-sans flex flex-col items-center">
      <Toaster position="bottom-left" theme="dark" />

      <header className="mb-8 text-center space-y-2">
        <div className="flex items-center justify-center gap-2">
          <FileVideo className="w-8 h-8 text-red-500" />
          <h1 className="text-3xl font-bold bg-linear-to-r from-red-500 to-orange-500 bg-clip-text text-transparent">
            Chat with YouTube
          </h1>
        </div>
        <p className="text-zinc-400">Summarize and ask questions to any video instantly.</p>
      </header>

      <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-3 gap-6 h-[82vh]">
        
        {/*LEFT PANEL*/}
        <div className="lg:col-span-1 flex flex-col gap-4 h-full">
          
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <CardTitle>Add Video</CardTitle>
              <CardDescription>Paste YouTube URL to start</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <Input 
                placeholder="https://youtube.com/..." 
                value={videoUrl}
                onChange={(e) => setVideoUrl(e.target.value)}
                className="bg-zinc-950 border-zinc-700"
              />
              
              {/*Dynamic Button*/}
              {!videoData ? (
                <Button 
                  onClick={handleProcessVideo} 
                  disabled={loading || !videoUrl}
                  className="w-full bg-red-600 hover:bg-red-700 text-white"
                >
                  {loading ? <Loader2 className="animate-spin mr-2" /> : <Sparkles className="mr-2 w-4 h-4"/>}
                  {loading ? "Processing..." : "Generate Insights"}
                </Button>
              ) : isSummaryLoading ? (
                <Button disabled className="w-full bg-yellow-600/20 text-yellow-500 border border-yellow-600/50">
                  <Loader2 className="animate-spin mr-2 w-4 h-4" /> Generating Summary...
                </Button>
              ) : (
                <Dialog>
                  <DialogTrigger asChild>
                    <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white">
                      <FileText className="mr-2 w-4 h-4" /> View Summary
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="bg-zinc-900 border-zinc-800 text-zinc-100 max-w-2xl max-h-[80vh] overflow-y-auto">
                    <DialogHeader>
                      <DialogTitle>Video Summary</DialogTitle>
                      <DialogDescription className="text-zinc-400">
                        Key insights generated from the video.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="mt-4 whitespace-pre-wrap leading-relaxed text-zinc-300">
                      {summary}
                    </div>
                  </DialogContent>
                </Dialog>
              )}

            </CardContent>
          </Card>

          {videoData && (
            <Card className="bg-zinc-900 border-zinc-800 flex-1 flex flex-col overflow-hidden">
              <CardHeader>
                <Badge variant="secondary" className="w-fit mb-2 bg-zinc-800 text-zinc-400 border-0">
                  {videoData.language === "detected" ? "Auto-Detected" : videoData.language}
                </Badge>
                <CardTitle className="text-lg leading-tight">{videoData.title}</CardTitle>
              </CardHeader>
              <CardContent className="flex-1">
                <div className="h-full bg-zinc-950/50 rounded-lg border border-zinc-800/50 flex items-center justify-center text-zinc-500 text-sm p-4 text-center">
                  Chat with the bot to explore more details about "{videoData.title}"
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/*RIGHT PANEL*/}
        <div className="lg:col-span-2 h-full">
          <Card className="bg-zinc-900 border-zinc-800 h-full flex flex-col">
            <CardHeader className="border-b border-zinc-800 pb-4">
              <CardTitle className="flex items-center gap-2">
                <Bot className="w-5 h-5 text-green-500" /> 
                AI Chat Assistant
              </CardTitle>
            </CardHeader>
            
            <CardContent className="flex-1 p-0 overflow-hidden relative">
              {!videoData ? (
                <div className="h-full flex flex-col items-center justify-center text-zinc-500 gap-2">
                  <Bot className="w-12 h-12 opacity-20" />
                  <p>Process a video to start chatting</p>
                </div>
              ) : (
                <ScrollArea className="h-full p-4">
                  <div className="flex flex-col gap-4">
                    <div className="flex gap-3">
                      <div className="w-8 h-8 rounded-full bg-green-900/30 flex items-center justify-center border border-green-800">
                        <Bot className="w-4 h-4 text-green-500" />
                      </div>
                      <div className="bg-zinc-800 rounded-2xl rounded-tl-none px-4 py-2 max-w-[80%] text-sm text-zinc-200">
                        Hello! I've watched the video. Ask me anything about it!
                      </div>
                    </div>

                    {messages.map((msg, idx) => (
                      <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center border shrink-0
                          ${msg.role === 'user' ? 'bg-blue-900/30 border-blue-800' : 'bg-green-900/30 border-green-800'}`}>
                          {msg.role === 'user' ? <User className="w-4 h-4 text-blue-500" /> : <Bot className="w-4 h-4 text-green-500" />}
                        </div>
                        <div className={`rounded-2xl px-4 py-2 max-w-[80%] text-sm
                          ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-zinc-800 text-zinc-200 rounded-tl-none'}`}>
                          {msg.text}
                        </div>
                      </div>
                    ))}

                    {isChatLoading && (
                      <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-full bg-green-900/30 flex items-center justify-center border border-green-800">
                          <Bot className="w-4 h-4 text-green-500" />
                        </div>
                        <div className="bg-zinc-800 rounded-2xl rounded-tl-none px-4 py-3 max-w-[80%] flex items-center gap-1">
                          <div className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce" />
                          <div className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce delay-75" />
                          <div className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce delay-150" />
                        </div>
                      </div>
                    )}
                    <div ref={scrollRef} />
                  </div>
                </ScrollArea>
              )}
            </CardContent>

            <div className="p-4 border-t border-zinc-800 bg-zinc-900/50">
              <form 
                onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}
                className="flex gap-2"
              >
                <Input 
                  placeholder="Ask a question about the video..." 
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  disabled={!videoData || isChatLoading}
                  className="bg-zinc-950 border-zinc-700 focus-visible:ring-offset-0"
                />
                <Button 
                  type="submit" 
                  disabled={!videoData || isChatLoading || !inputMessage.trim()}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </form>
            </div>
          </Card>
        </div>

      </div>
    </div>
  );
}

export default App;