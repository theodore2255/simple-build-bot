# RAG Assistant

A powerful document-based AI assistant built with React, Supabase, and Google's Gemini API. Upload documents and ask questions to get intelligent answers based on your content.

## Features

- 📄 **Document Upload**: Support for PDF, TXT, DOC, and DOCX files
- 🤖 **AI-Powered Chat**: Powered by Google's Gemini 1.5 Flash model
- 🔍 **Smart Document Processing**: Automatic text extraction and chunking
- 💾 **Vector Storage**: Documents are processed and stored for quick retrieval
- 🎨 **Modern UI**: Beautiful, responsive interface built with shadcn/ui components
- 🌙 **Dark/Light Theme**: Toggle between themes for comfortable viewing

## Prerequisites

- Node.js 18+ and npm/yarn
- Supabase account and project
- Google AI Studio API key for Gemini

## Setup

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd simple-build-bot
npm install
```

### 2. Environment Variables

Create a `.env.local` file in the root directory:

```env
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 3. Supabase Setup

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Run the migration script from `supabase/migrations/001_create_documents_table.sql`

### 4. Supabase Edge Functions

Deploy the edge functions to your Supabase project:

```bash
# Install Supabase CLI if you haven't already
npm install -g supabase

# Login to Supabase
supabase login

# Link your project
supabase link --project-ref your_project_ref

# Deploy functions
supabase functions deploy chat-completion
supabase functions deploy process-document
```

### 5. Set Environment Variables for Edge Functions

In your Supabase dashboard, go to Settings > Edge Functions and set:

- `GEMINI_API_KEY`: Your Google AI Studio API key

### 6. Run the Application

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## How It Works

1. **Document Upload**: Users drag and drop documents into the interface
2. **Text Extraction**: The system extracts text content from various file formats
3. **Chunking**: Content is split into smaller, searchable chunks
4. **Storage**: Processed documents are stored in Supabase with their content
5. **AI Chat**: When users ask questions, relevant document content is retrieved and sent to Gemini
6. **Intelligent Responses**: Gemini provides answers based on the actual document content

## File Format Support

- **TXT**: Full text extraction
- **PDF**: Basic text extraction (enhanced extraction with proper libraries)
- **DOC/DOCX**: Text content extraction
- **Other formats**: Convert to supported formats for best results

## Architecture

- **Frontend**: React + TypeScript + Vite
- **UI Components**: shadcn/ui + Tailwind CSS
- **Backend**: Supabase Edge Functions
- **AI**: Google Gemini 1.5 Flash API
- **Database**: Supabase PostgreSQL
- **Storage**: Supabase Storage (for future enhancements)

## Troubleshooting

### Gemini API Issues
- Check your API key in Supabase Edge Functions environment variables
- Verify your Google AI Studio quota and billing
- Check the browser console for error messages

### Document Processing Issues
- Ensure documents are in supported formats
- Check file size limits (recommended: under 10MB)
- Verify Supabase connection and permissions

### Database Issues
- Run the migration script to create the documents table
- Check Supabase Row Level Security policies
- Verify your project is properly linked

## Future Enhancements

- [ ] Enhanced PDF text extraction with pdf-parse
- [ ] Word document processing with mammoth.js
- [ ] Vector embeddings for semantic search
- [ ] Document versioning and history
- [ ] Collaborative document sharing
- [ ] Advanced search and filtering
- [ ] Export chat conversations
- [ ] Multi-language support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.
