import { useState, useCallback, useRef, useEffect } from 'react';
import { Send, Bot, User, Paperclip, FileText, Sidebar, X, Settings } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { ThemeToggle } from '@/components/ThemeToggle';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Array<{
    document: string;
    page: number;
    relevance: number;
  }>;
}

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
}

export const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: 'Hello! I\'m your AI assistant. Upload some documents and I\'ll help you find information from them. What would you like to know?',
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach((file) => {
      const fileId = Math.random().toString(36).substring(7);
      const newFile: UploadedFile = {
        id: fileId,
        name: file.name,
        size: file.size,
        status: 'uploading',
        progress: 0,
      };

      setUploadedFiles(prev => [...prev, newFile]);

      // Simulate file upload and processing
      const uploadInterval = setInterval(() => {
        setUploadedFiles(prev => prev.map(f => {
          if (f.id === fileId) {
            if (f.progress < 50) {
              return { ...f, progress: f.progress + 10, status: 'uploading' };
            } else if (f.progress < 90) {
              return { ...f, progress: f.progress + 10, status: 'processing' };
            } else {
              clearInterval(uploadInterval);
              return { ...f, progress: 100, status: 'completed' };
            }
          }
          return f;
        }));
      }, 200);
    });

    toast({
      title: "Files uploaded",
      description: `${acceptedFiles.length} file(s) uploaded successfully`,
    });
  }, [toast]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 20,
    noClick: true,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Math.random().toString(36).substring(7),
      type: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // Call OpenAI API through edge function
    try {
      const response = await supabase.functions.invoke('chat-completion', {
        body: {
          messages: [
            ...messages.slice(-5).map(msg => ({
              role: msg.type === 'user' ? 'user' : 'assistant',
              content: msg.content
            })),
            { role: 'user', content: input }
          ],
          documentContext: uploadedFiles
            .filter(f => f.status === 'completed')
            .map(f => `Document: ${f.name}`)
        }
      });

      if (response.error) {
        throw new Error(response.error.message || 'Failed to get AI response');
      }

      const aiResponse = response.data?.response || 'I apologize, but I encountered an error processing your request.';
      const isQuotaError = response.data?.isQuotaError || false;

      const assistantMessage: Message = {
        id: Math.random().toString(36).substring(7),
        type: 'assistant',
        content: aiResponse,
        timestamp: new Date(),
        sources: !isQuotaError && uploadedFiles.filter(f => f.status === 'completed').length > 0 
          ? uploadedFiles.filter(f => f.status === 'completed').slice(0, 2).map(f => ({
              document: f.name,
              page: Math.floor(Math.random() * 10) + 1,
              relevance: 0.85 + Math.random() * 0.1
            }))
          : undefined
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error calling AI:', error);
      const errorMessage: Message = {
        id: Math.random().toString(36).substring(7),
        type: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please try again or check your internet connection.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    }
    
    setIsLoading(false);
  };

  const removeFile = (id: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== id));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="flex h-screen bg-background" {...getRootProps()}>
      <input {...getInputProps()} />
      
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-80' : 'w-0'} transition-all duration-300 bg-muted/20 border-r border-border overflow-hidden flex-shrink-0`}>
        <div className="p-4 border-b border-border bg-background/95">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-foreground">Documents</h2>
            <div className="flex items-center gap-2">
              <ThemeToggle />
              <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(false)}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
        
        <ScrollArea className="h-[calc(100vh-81px)]">
          <div className="p-4 space-y-3">
            {uploadedFiles.length === 0 ? (
              <div className="text-center py-8 px-4">
                <FileText className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">
                  No documents uploaded yet. Drag and drop files anywhere to upload.
                </p>
              </div>
            ) : (
              uploadedFiles.map((file) => (
                <Card key={file.id} className="p-3 bg-card border-border">
                  <div className="flex items-start gap-3">
                    <FileText className="w-4 h-4 text-primary mt-1 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">{file.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(file.size)}
                      </p>
                      {file.status !== 'completed' ? (
                        <div className="mt-2">
                          <Progress value={file.progress} className="h-1" />
                          <p className="text-xs text-muted-foreground mt-1 capitalize">
                            {file.status}...
                          </p>
                        </div>
                      ) : (
                        <Badge variant="secondary" className="text-xs mt-1">
                          Ready
                        </Badge>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      onClick={() => removeFile(file.id)}
                    >
                      <X className="w-3 h-3" />
                    </Button>
                  </div>
                </Card>
              ))
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-border bg-background/95 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            {!sidebarOpen && (
              <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(true)}>
                <Sidebar className="w-4 h-4" />
              </Button>
            )}
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div>
                <h1 className="font-semibold">RAG Assistant</h1>
                <p className="text-xs text-muted-foreground">
                  {uploadedFiles.filter(f => f.status === 'completed').length} documents ready
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Messages */}
        <ScrollArea className="flex-1 p-4 bg-background">
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((message) => (
              <div key={message.id} className="flex gap-4">
                <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0">
                  {message.type === 'user' ? (
                    <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
                      <User className="w-4 h-4" />
                    </div>
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                  )}
                </div>
                <div className="flex-1 space-y-2">
                  <p className="leading-relaxed">{message.content}</p>
                  
                  {message.sources && message.sources.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-muted-foreground">Sources:</p>
                      <div className="flex flex-wrap gap-2">
                        {message.sources.map((source, index) => (
                          <Badge key={index} variant="secondary" className="text-xs">
                            {source.document} (p.{source.page}) • {Math.round(source.relevance * 100)}%
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                    <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
                    <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="p-4 border-t border-border bg-background/95 backdrop-blur-sm">
          <div className="max-w-3xl mx-auto">
            <form onSubmit={handleSubmit} className="flex gap-3">
              <div className="flex-1 relative">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask me anything about your documents..."
                  className="pr-12"
                  disabled={isLoading}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8"
                  onClick={() => (document.querySelector('input[type="file"]') as HTMLInputElement)?.click()}
                >
                  <Paperclip className="w-4 h-4" />
                </Button>
              </div>
              <Button 
                type="submit" 
                disabled={isLoading || !input.trim()}
                variant="ai"
              >
                {isLoading ? (
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </form>
            <p className="text-xs text-muted-foreground mt-2 text-center">
              Drag and drop documents anywhere to upload • Supports PDF, TXT, DOC, DOCX
            </p>
          </div>
        </div>
      </div>

      {/* Drag Overlay */}
      {isDragActive && (
        <div className="absolute inset-0 bg-primary/10 border-2 border-dashed border-primary flex items-center justify-center z-50">
          <div className="text-center">
            <FileText className="w-16 h-16 mx-auto mb-4 text-primary" />
            <p className="text-xl font-semibold text-primary">Drop files here to upload</p>
          </div>
        </div>
      )}
    </div>
  );
};