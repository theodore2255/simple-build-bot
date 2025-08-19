import { useState, useCallback, useRef, useEffect } from 'react';
import { Send, Bot, User, Paperclip, FileText, Sidebar, X } from 'lucide-react';
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
  type: string;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  fileUri?: string; // Gemini file URI
  file?: File; // Store the original file for direct upload
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
    console.log('Files dropped:', acceptedFiles);
    
    acceptedFiles.forEach(async (file) => {
      const fileId = Math.random().toString(36).substring(7);
      const newFile: UploadedFile = {
        id: fileId,
        name: file.name,
        size: file.size,
        type: file.type,
        status: 'uploading',
        progress: 0,
        file: file,
      };

      setUploadedFiles(prev => [...prev, newFile]);

      try {
        // Update status to processing
        setUploadedFiles(prev => prev.map(f => 
          f.id === fileId ? { ...f, status: 'processing', progress: 25 } : f
        ));

        // Upload file to Gemini API
        const fileUri = await uploadFileToGemini(file);
        console.log('File uploaded to Gemini:', fileUri);
        
        // Update progress
        setUploadedFiles(prev => prev.map(f => 
          f.id === fileId ? { ...f, progress: 75 } : f
        ));
        
        // Update status to completed
        setUploadedFiles(prev => prev.map(f => 
          f.id === fileId ? { ...f, status: 'completed', progress: 100, fileUri: fileUri } : f
        ));

        toast({
          title: "Document processed successfully",
          description: `${file.name} is now ready for queries with Gemini AI`,
        });

      } catch (error) {
        console.error('Error processing file:', error);
        setUploadedFiles(prev => prev.map(f => 
          f.id === fileId ? { ...f, status: 'error', progress: 0 } : f
        ));
        
        toast({
          title: "Processing failed",
          description: `Failed to process ${file.name}. Please try again.`,
          variant: "destructive"
        });
      }
    });
  }, [toast]);

  // Upload file directly to Gemini API
  const uploadFileToGemini = async (file: File): Promise<string> => {
    const geminiApiKey = import.meta.env.VITE_GEMINI_API_KEY || 'AIzaSyCyjfH5GrYf0gaCv0Hb_KIYR6nPEAWrDCs';
    
    // Step 1: Upload the file to Gemini Files API
    const formData = new FormData();
    formData.append('file', file);
    
    const uploadResponse = await fetch(`https://generativelanguage.googleapis.com/upload/v1beta/files?key=${geminiApiKey}`, {
      method: 'POST',
      body: formData,
    });
    
    if (!uploadResponse.ok) {
      const errorText = await uploadResponse.text();
      throw new Error(`Failed to upload file to Gemini: ${uploadResponse.status} ${errorText}`);
    }
    
    const uploadData = await uploadResponse.json();
    console.log('File uploaded to Gemini:', uploadData);
    
    return uploadData.file.uri;
  };


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

    try {
      // Get completed files with Gemini URIs
      const completedFiles = uploadedFiles.filter(f => f.status === 'completed' && f.fileUri);
      
      if (completedFiles.length === 0) {
        const assistantMessage: Message = {
          id: Math.random().toString(36).substring(7),
          type: 'assistant',
          content: "I don't have any documents to work with yet. Please upload some documents first, and I'll be able to answer questions about their content.",
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        // Call Gemini API with direct file references
        try {
          const geminiApiKey = import.meta.env.VITE_GEMINI_API_KEY || 'AIzaSyCyjfH5GrYf0gaCv0Hb_KIYR6nPEAWrDCs';
          
          // Create content parts with file references and user query
          const contentParts = [
            { text: `You are a helpful AI assistant. Analyze the uploaded documents and answer questions based on their content. Here is the user's question: ${input}` },
            ...completedFiles.map(file => ({
              file_data: {
                file_uri: file.fileUri,
                mime_type: file.type
              }
            }))
          ];

          // Format messages for Gemini API with file attachments
          const geminiMessages = [
            {
              role: 'user',
              parts: contentParts
            }
          ];

          const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${geminiApiKey}`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              contents: geminiMessages,
              generationConfig: {
                temperature: 0.7,
                maxOutputTokens: 2000,
              },
            }),
          });

          if (!response.ok) {
            const errorText = await response.text();
            console.error('Gemini API error:', response.status, errorText);
            throw new Error(`Gemini API error: ${response.status} ${errorText}`);
          }

          const data = await response.json();
          
          if (!data.candidates || !data.candidates[0] || !data.candidates[0].content) {
            throw new Error('Invalid response from Gemini API');
          }
          
          const aiResponse = data.candidates[0].content.parts[0].text;

          const assistantMessage: Message = {
            id: Math.random().toString(36).substring(7),
            type: 'assistant',
            content: aiResponse,
            timestamp: new Date(),
            sources: completedFiles.map(file => ({
              document: file.name,
              page: 1,
              relevance: 0.95
            }))
          };

          setMessages(prev => [...prev, assistantMessage]);
        } catch (apiError) {
          console.error('API call failed:', apiError);
          
          const errorMessage: Message = {
            id: Math.random().toString(36).substring(7),
            type: 'assistant',
            content: `I encountered an error while processing your request: ${apiError.message}\n\nPlease try again or check if the documents were uploaded correctly.`,
            timestamp: new Date(),
          };
          
          setMessages(prev => [...prev, errorMessage]);
        }
      }
    } catch (error) {
      console.error('Error processing request:', error);
      const errorMessage: Message = {
        id: Math.random().toString(36).substring(7),
        type: 'assistant',
        content: 'I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    }
    
    setIsLoading(false);
  };

  const findRelevantContent = (question: string, documentContext: string): string => {
    // Simple relevance search - in a real app, you'd use vector embeddings
    const keywords = question.toLowerCase().split(' ').filter(word => word.length > 3);
    const sentences = documentContext.split(/[.!?]+/);
    
    const relevantSentences = sentences.filter(sentence => 
      keywords.some(keyword => sentence.toLowerCase().includes(keyword))
    );
    
    if (relevantSentences.length > 0) {
      return relevantSentences.slice(0, 3).join('. ') + '.';
    }
    
    return documentContext.substring(0, 300) + '...';
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