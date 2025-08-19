import "https://deno.land/x/xhr@0.1.0/mod.ts";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const geminiApiKey = Deno.env.get('GEMINI_API_KEY');

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    if (!geminiApiKey) {
      throw new Error('Gemini API key not configured');
    }

    const { messages, documentContext } = await req.json();

    // Build the system prompt with document context
    let systemContent = `You are a helpful AI assistant that answers questions based on uploaded documents. 
    You should provide accurate, helpful responses based on the context provided from the user's documents.
    
    If you reference information from the documents, be specific about which document or section you're citing.
    If you cannot find relevant information in the provided context, say so clearly.`;

    if (documentContext && documentContext.length > 0) {
      systemContent += `\n\nHere is the relevant context from the user's documents:\n${documentContext.join('\n\n')}`;
    }

    // Format messages for Gemini API
    const geminiMessages = messages.map((msg: any) => ({
      role: msg.role === 'assistant' ? 'model' : 'user',
      parts: [{ text: msg.content }]
    }));

    // Add system instruction as the first user message
    geminiMessages.unshift({
      role: 'user',
      parts: [{ text: systemContent }]
    });

    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${geminiApiKey}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        contents: geminiMessages,
        generationConfig: {
          temperature: 0.7,
          maxOutputTokens: 1000,
        },
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('Gemini API error:', errorData);
      
      // Handle specific quota error
      if (errorData.error?.code === 'RESOURCE_EXHAUSTED') {
        return new Response(JSON.stringify({ 
          response: "I apologize, but it seems your Gemini API account has exceeded its quota. Please check your Google AI Studio billing dashboard and increase your quota to continue using the AI features. For now, I can still help you with general questions about document management and RAG systems.",
          isQuotaError: true
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
      
      throw new Error(`Gemini API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    const aiResponse = data.candidates[0].content.parts[0].text;

    return new Response(JSON.stringify({ 
      response: aiResponse,
      model: 'gemini-1.5-flash'
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Error in chat-completion function:', error);
    return new Response(JSON.stringify({ 
      error: error.message || 'An error occurred processing your request'
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});