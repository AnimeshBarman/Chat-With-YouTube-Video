import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { 
  Send, Loader2, FileVideo, Bot, User, Sparkles, 
  FileText, Menu, Video, RefreshCcw, Trash2
} from "lucide-react";
// Shadcn Components
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

import type { VideoResponse, ChatMessage } from "./types";

const API_URL = "https://chat-with-youtube-video.onrender.com/";

function App() {
  // STATES
  // Video processing 
  const [videoUrl, setVideoUrl] = useState("");
  const [videoData, setVideoData] = useState<VideoResponse | null>(null);
  const [loading, setLoading] = useState(false);
  // Summary
  const [summary, setSummary] = useState<string | null>(null);
  const [isSummaryLoading, setIsSummaryLoading] = useState(false);
  // Chat Service
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  
  const scrollRef = useRef<HTMLDivElement>(null);

  // useEffect(() => {
  //   const refresh = setInterval(() => {
  //     axios.get(`${API_URL}/`)
  //   }, 300000)

  //   return () => clearInterval(refresh)
  // }, [])

  const parseSummary = (text: string) => {
    if (!text) return { abstract: "", points: [] };

    let abstract = text;
    let points: string[] = [];

    if (text.includes("###")) {
      const parts = text.split("###");
      abstract = parts[0].trim();
      const rawPoints = parts[1].trim();
      points = rawPoints.split("\n")
        .map(line => line.trim().replace(/^[-*•]\s*/, ""))
        .filter(line => line.length > 0);
    } 
    else {
      const lines = text.split("\n");
      const abstractLines: string[] = [];
      lines.forEach(line => {
        const trimmed = line.trim();
        if (trimmed.startsWith("-") || trimmed.startsWith("•") || trimmed.startsWith("*") || /^\d+\./.test(trimmed)) {
          points.push(trimmed.replace(/^[-*•\d+.]\s*/, ""));
        } else if (trimmed.length > 0) {
          abstractLines.push(trimmed);
        }
      });
      if (points.length > 0) abstract = abstractLines.join(" ");
    }
    return { abstract, points };
  };


  const handleStartNewVideo = () => {
    setVideoUrl("");
    setVideoData(null);
    setSummary(null);
    setMessages([]);
    setIsSummaryLoading(false);
    toast.info("Ready for a new video!");
  };

  const handleClearChat = () => {
    setMessages([]);
    toast.success("Chat history cleared.");
  };

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
      toast.success("Video processed successfully!");
    } catch (error) {
      console.error(error);
      toast.error("Failed to process video. Check URL.");
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
          toast.success("Insights generated successfully!");
        }
      } catch (error: any) {
        if (error.response?.status !== 202) {
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
      setMessages((prev) => [...prev, { role: "bot", text: "Connection error. Please try again." }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollIntoView({ behavior: "smooth" });
  }, [messages, videoData]);


  const SidebarContent = () => (
    <div className="flex flex-col h-full bg-zinc-950 border-r border-zinc-800">
      <div className="p-4 border-b border-zinc-800 space-y-4">
        <Button 
          onClick={handleStartNewVideo} 
          className="w-full bg-red-600 hover:bg-red-700 gap-2 font-semibold shadow-lg shadow-red-900/20"
        >
          <Video className="w-4 h-4" /> Process New Video
        </Button>
      </div>
      <div className="p-6 text-center mt-10 opacity-50 flex flex-col items-center">
        <FileVideo className="w-12 h-12 mb-3 text-zinc-700" />
        <p className="text-sm text-zinc-500">
          Enter a YouTube URL to get insights and chat with the video content.
        </p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans flex overflow-hidden">
      <Toaster position="bottom-center" theme="dark" />

      <div className="hidden md:flex w-72 flex-col h-screen sticky top-0">
        <div className="p-4 flex items-center gap-2 border-b border-zinc-800 h-[60px] bg-zinc-950">
          <FileVideo className="w-6 h-6 text-red-500" />
          <span className="font-bold text-lg tracking-tight">YT Chatbot</span>
        </div>
        <SidebarContent />
      </div>

      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        
        <div className="md:hidden p-4 border-b border-zinc-800 flex items-center gap-3 bg-zinc-950">
          <Sheet>
            <SheetTrigger asChild><Button variant="ghost" size="icon"><Menu className="w-5 h-5" /></Button></SheetTrigger>
            <SheetContent side="left" className="bg-zinc-950 border-zinc-800 p-0 w-72 text-zinc-100">
              <div className="p-4 flex items-center gap-2 border-b border-zinc-800 h-[60px]">
                <FileVideo className="w-6 h-6 text-red-500" />
                <span className="font-bold text-lg tracking-tight">YT Chatbot</span>
              </div>
              <SidebarContent />
            </SheetContent>
          </Sheet>
          <span className="font-bold">YT Chatbot</span>
        </div>

        <div className="flex-1 p-4 lg:p-6 overflow-hidden bg-zinc-950/50">
          <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
            
            <div className="lg:col-span-1 flex flex-col gap-4 h-full overflow-y-auto pb-4 no-scrollbar">
              
              {!videoData && (
                <Card className="bg-zinc-900 border-zinc-800 shadow-lg animate-in fade-in zoom-in-95 duration-300">
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
                    <Button 
                      onClick={handleProcessVideo} 
                      disabled={loading || !videoUrl}
                      className="w-full bg-red-600 hover:bg-red-700 text-white shadow-md shadow-red-900/20"
                    >
                      {loading ? <Loader2 className="animate-spin mr-2" /> : <Sparkles className="mr-2 w-4 h-4"/>}
                      {loading ? "Processing..." : "Generate Insights"}
                    </Button>
                  </CardContent>
                </Card>
              )}

              {videoData && (
                <Card className="bg-zinc-900 border-zinc-800 flex-1 flex flex-col shadow-lg animate-in slide-in-from-left-5 duration-300 h-full overflow-hidden">
                  <CardHeader className="relative pb-2 shrink-0">
                    <div className="flex justify-between items-start gap-2">
                      <div>
                        <Badge variant="secondary" className="w-fit mb-2 bg-zinc-800 text-zinc-400 border-0">
                          {videoData.language === "detected" ? "Auto-Detected" : videoData.language}
                        </Badge>
                        <CardTitle className=" text-base text-red-500 leading-tight line-clamp-3">VIDEO TITLE: <span className=" text-amber-100">{videoData.title}</span></CardTitle>
                      </div>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        onClick={handleStartNewVideo}
                        className="text-zinc-500 hover:text-white hover:bg-zinc-800 -mt-1 -mr-2"
                        title="Process different video"
                      >
                        <RefreshCcw className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  
                  <CardContent className="flex-1 flex flex-col gap-4 h-full min-h-0 pb-4">
                    
                    <div className="flex-1 bg-zinc-950/50 rounded-xl border border-zinc-800/60 p-4 flex flex-col h-full overflow-hidden">
                      
                      <h4 className="text-[11px] font-bold text-zinc-500 uppercase tracking-widest mb-4 flex items-center gap-2 shrink-0">
                        <Sparkles className="w-3 h-3 text-yellow-500" /> Key Highlights
                      </h4>

                      {isSummaryLoading ? (
                        <div className="space-y-4">
                          <div className="flex items-center gap-2 text-yellow-500/80 text-xs animate-pulse font-medium">
                            <Loader2 className="w-3.5 h-3.5 animate-spin" /> Analyzing content...
                          </div>
                          <div className="space-y-2">
                            <div className="h-2 w-full bg-zinc-800/50 rounded animate-pulse" />
                            <div className="h-2 w-3/4 bg-zinc-800/50 rounded animate-pulse" />
                            <div className="h-2 w-5/6 bg-zinc-800/50 rounded animate-pulse" />
                          </div>
                        </div>
                      ) : summary ? (
                        (() => {
                          const { abstract, points } = parseSummary(summary);
                          return (
                            <div className="flex flex-col h-full overflow-hidden">
                              
                              <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                                {points.length > 0 ? (
                                  <ul className="space-y-3 pb-2">
                                    {points.map((point, i) => (
                                      <li key={i} className="flex gap-3 items-start text-sm text-zinc-300 leading-relaxed group">
                                        <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-green-500/80 shrink-0 group-hover:bg-green-400 transition-colors shadow-[0_0_8px_rgba(34,197,94,0.3)]" />
                                        <span className="opacity-90">{point}</span>
                                      </li>
                                    ))}
                                  </ul>
                                ) : (
                                  <div className="h-full flex items-center justify-center text-zinc-500 italic text-sm">
                                    No specific points found.
                                  </div>
                                )}
                              </div>

                              {abstract && (
                                <div className="mt-auto pt-3 border-t border-zinc-800/50 shrink-0">
                                  <Dialog>
                                    <DialogTrigger asChild>
                                      <Button variant="secondary" size="sm" className="w-full bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs h-8 border border-zinc-700/50">
                                        <FileText className="mr-2 w-3 h-3" /> Read Full Abstract
                                      </Button>
                                    </DialogTrigger>
                                    <DialogContent className="bg-zinc-950 border-zinc-800 text-zinc-100 max-w-xl">
                                      <DialogHeader>
                                        <DialogTitle className="flex items-center gap-2 text-lg">
                                          <Sparkles className="w-5 h-5 text-yellow-500" /> Video Abstract
                                        </DialogTitle>
                                        <DialogDescription className="text-zinc-400">
                                          Detailed summary of {videoData.title}
                                        </DialogDescription>
                                      </DialogHeader>
                                      <div className="mt-4 p-5 bg-zinc-900/50 rounded-xl border border-zinc-800/50 text-sm text-zinc-300 leading-7 tracking-wide max-h-[60vh] overflow-y-auto">
                                        {abstract}
                                      </div>
                                    </DialogContent>
                                  </Dialog>
                                </div>
                              )}

                            </div>
                          );
                        })()
                      ) : (
                        <div className="flex flex-col items-center justify-center h-full text-zinc-600 gap-2 opacity-60">
                          <FileText className="w-8 h-8 stroke-1" />
                          <p className="text-xs italic">Insights will appear here...</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* RIGHT PANEL*/}
            <div className="lg:col-span-2 h-full min-h-0 flex flex-col">
              <Card className="bg-zinc-900 border-zinc-800 h-full flex flex-col shadow-xl overflow-hidden">
                
                <div className="border-b border-zinc-800 p-4 flex items-center justify-between bg-zinc-900/80 backdrop-blur h-[60px] shrink-0 z-10">
                  <div className="flex items-center gap-2">
                    <Bot className="w-5 h-5 text-green-500" />
                    <span className="font-medium text-sm">{videoData ? "Chat Session" : "AI Assistant"}</span>
                  </div>
                  {videoData && (
                    <Button variant="ghost" size="sm" onClick={handleClearChat} className="text-xs text-zinc-400 hover:text-red-400 hover:bg-zinc-800">
                      <Trash2 className="w-3 h-3 mr-1" /> Clear Chat
                    </Button>
                  )}
                </div>
                
                <CardContent className="flex-1 p-0 overflow-hidden relative bg-linear-to-b from-zinc-900/50 to-zinc-950/50">
                  {!videoData ? (
                    <div className="h-full flex flex-col items-center justify-center text-zinc-600 gap-4">
                      <div className="w-16 h-16 rounded-full bg-zinc-900/50 flex items-center justify-center border border-zinc-800 animate-pulse">
                        <Bot className="w-8 h-8 opacity-20" />
                      </div>
                      <p className="text-sm">Process a video to start chatting</p>
                    </div>
                  ) : (
                    <ScrollArea className="h-full w-full p-4">
                      <div className="flex flex-col gap-6 pb-4">
                        
                        <div className="flex gap-3 animate-in fade-in slide-in-from-bottom-2 duration-300">
                          <div className="w-8 h-8 rounded-full bg-green-900/30 flex items-center justify-center border border-green-800 shrink-0">
                            <Bot className="w-4 h-4 text-green-500" />
                          </div>
                          <div className="bg-zinc-800 rounded-2xl rounded-tl-none px-4 py-2 max-w-[85%] text-sm text-zinc-200">
                            Hello! I've analyzed <strong>{videoData.title}</strong>. Ask me anything!
                          </div>
                        </div>

                        {messages.map((msg, idx) => (
                          <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center border shrink-0 shadow-sm
                              ${msg.role === 'user' ? 'bg-blue-600/10 border-blue-600/20' : 'bg-green-600/10 border-green-600/20'}`}>
                              {msg.role === 'user' ? <User className="w-4 h-4 text-blue-500" /> : <Bot className="w-4 h-4 text-green-500" />}
                            </div>
                            <div className={`rounded-2xl px-4 py-2.5 max-w-[85%] text-sm leading-relaxed shadow-sm whitespace-pre-wrap
                              ${msg.role === 'user' 
                                ? 'bg-blue-600 text-white rounded-tr-none' 
                                : 'bg-zinc-800 text-zinc-200 rounded-tl-none border border-zinc-700/50'}`}>
                              {msg.text}
                            </div>
                          </div>
                        ))}
                        {isChatLoading && (
                          <div className="flex gap-3 animate-in fade-in">
                            <div className="w-8 h-8 rounded-full bg-green-600/10 flex items-center justify-center border border-green-600/20">
                              <Bot className="w-4 h-4 text-green-500" />
                            </div>
                            <div className="bg-zinc-800 rounded-2xl rounded-tl-none px-4 py-3 flex items-center gap-1 border border-zinc-700/50">
                              <div className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" />
                              <div className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce delay-75" />
                              <div className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce delay-150" />
                            </div>
                          </div>
                        )}
                        <div ref={scrollRef} />
                      </div>
                    </ScrollArea>
                  )}
                </CardContent>

                <div className="p-4 border-t border-zinc-800 bg-zinc-900 shrink-0 z-10">
                  <form onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }} className="flex gap-3">
                    <Input 
                      placeholder="Ask a question..." value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      disabled={!videoData || isChatLoading}
                      className="bg-zinc-950 border-zinc-700 focus-visible:ring-offset-0 shadow-inner"
                    />
                    <Button type="submit" disabled={!videoData || isChatLoading || !inputMessage.trim()} className="bg-green-600 hover:bg-green-700 shadow-md shadow-green-900/20">
                      <Send className="w-4 h-4" />
                    </Button>
                  </form>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;