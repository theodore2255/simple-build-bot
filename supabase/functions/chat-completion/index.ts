import "https://deno.land/x/xhr@0.1.0/mod.ts";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const openAIApiKey = Deno.env.get('OPENAI_API_KEY');

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
    if (!openAIApiKey) {
      throw new Error('OpenAI API key not configured');
    }

    const { messages, documentContext } = await req.json();

    // Build the system prompt with document context
    let systemPrompt = `You are a helpful AI assistant that answers questions based on uploaded documents. 
    You should provide accurate, helpful responses based on the context provided from the user's documents.
    
    If you reference information from the documents, be specific about which document or section you're citing.
    If you cannot find relevant information in the provided context, say so clearly.`;

    if (documentContext && documentContext.length > 0) {
      systemPrompt += `\n\nHere is the relevant context from the user's documents:\n${documentContext.join('\n\n')}`;
    }

    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${openAIApiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'gpt-4.1-2025-04-14',
        messages: [
          { role: 'system', content: systemPrompt },
          ...messages
        ],
        max_tokens: 1000,
        temperature: 0.7,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('OpenAI API error:', errorData);
      
      // Handle specific quota error
      if (errorData.error?.code === 'insufficient_quota') {
        return new Response(JSON.stringify({ 
          response: "I apologize, but it seems your OpenAI API account has exceeded its quota. Please check your OpenAI billing dashboard and add credits to continue using the AI features. For now, I can still help you with general questions about document management and RAG systems.",
          isQuotaError: true
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
      
      throw new Error(`OpenAI API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    const aiResponse = data.choices[0].message.content;

    return new Response(JSON.stringify({ 
      response: aiResponse,
      model: 'gpt-4.1-2025-04-14'
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