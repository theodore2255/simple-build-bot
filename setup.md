# Quick Setup Guide for RAG Assistant

## Prerequisites
- Node.js 18+ installed
- Supabase account (free tier works)
- Google AI Studio API key

## Step-by-Step Setup

### 1. Install Dependencies
```bash
npm install
```

### 2. Create Environment File
Create `.env.local` in the root directory:
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
```

### 3. Set Up Supabase Database
1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Copy and paste the contents of `supabase/migrations/001_create_documents_table.sql`
4. Click "Run" to execute the migration

### 4. Deploy Edge Functions
```bash
# Install Supabase CLI globally
npm install -g supabase

# Login to Supabase
supabase login

# Link your project (replace with your project ref)
supabase link --project-ref your-project-ref

# Deploy the functions
supabase functions deploy chat-completion
supabase functions deploy process-document
```

### 5. Set Gemini API Key
1. Go to your Supabase dashboard
2. Navigate to Settings > Edge Functions
3. Add environment variable: `GEMINI_API_KEY` = your Google AI Studio API key

### 6. Test the System
1. Start the development server: `npm run dev`
2. Upload the sample document: `public/sample-document.txt`
3. Ask questions like "What does PanScience Innovations do?" or "What are their core technologies?"

## Troubleshooting

### Common Issues:

**"Gemini API key not configured"**
- Check that you've set the `GEMINI_API_KEY` in Supabase Edge Functions settings

**"Documents table doesn't exist"**
- Run the SQL migration script in Supabase SQL Editor

**"Function not found"**
- Make sure you've deployed both edge functions to Supabase

**"CORS errors"**
- Check that your Supabase project URL is correct in `.env.local`

### Testing with Sample Data:
The system includes a sample document (`public/sample-document.txt`) that you can upload to test the functionality. This document contains information about a fictional company called "PanScience Innovations" and is perfect for testing the RAG capabilities.

## Next Steps
Once the basic setup is working:
1. Try uploading your own documents
2. Test different file types (TXT works best initially)
3. Experiment with different types of questions
4. Consider implementing enhanced PDF processing for production use

## Support
If you encounter issues:
1. Check the browser console for error messages
2. Verify all environment variables are set correctly
3. Ensure Supabase functions are deployed and accessible
4. Check that your Gemini API key has sufficient quota
