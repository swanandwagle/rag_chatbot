
# RAG System Backend

Backend API for a document-based Q&A system using Retrieval-Augmented Generation (RAG) with local LLMs.

## Features

- **Document Upload & Processing**: Supports PDF, DOCX, PPTX, and TXT files
- **Intelligent Chunking**: Uses Llama LLM to chunk documents while maintaining semantic meaning
- **Vector Search**: FAISS-based vector store for efficient similarity search
- **Local LLM Integration**: Uses Ollama for both embeddings and text generation
- **RESTful API**: FastAPI-based API with automatic documentation
- **No External Database**: FAISS stores vectors and metadata together

## Architecture

```
Document Upload → Text Extraction → LLM Chunking → Embedding Generation → FAISS Storage
                                     (Llama)           (Nomic Embed)

User Query → Query Embedding → Vector Search → Context Retrieval → LLM Generation → Response
              (Nomic Embed)      (FAISS)                              (Llama)
```

## Setup

### Prerequisites

1. Python 3.9+
2. Ollama running with required models:
   ```bash
   ollama pull llama3.1:8b
   ollama pull nomic-embed-text:latest
   ```

### Installation

1. Create virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. Run the application:
   ```bash
   python run.py
   ```

The API will be available at `http://localhost:8000`

API documentation at `http://localhost:8000/docs`

## API Endpoints

### Admin Endpoints

#### Upload Document
```bash
POST /api/v1/admin/upload
Content-Type: multipart/form-data

# Example using curl
curl -X POST "http://localhost:8000/api/v1/admin/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

#### List Documents
```bash
GET /api/v1/admin/documents

# Example
curl "http://localhost:8000/api/v1/admin/documents"
```

### Chat Endpoints

#### Query (Standard Response)
```bash
POST /api/v1/chat/query
Content-Type: application/json

{
  "query": "What is the main topic of the document?",
  "top_k": 5
}

# Example
curl -X POST "http://localhost:8000/api/v1/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "top_k": 5}'
```

#### Query (Streaming Response)
```bash
POST /api/v1/chat/query/stream
Content-Type: application/json

{
  "query": "Explain the concept in detail",
  "top_k": 5
}

# Example
curl -X POST "http://localhost:8000/api/v1/chat/query/stream" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is deep learning?", "top_k": 5}'
```

#### Health Check
```bash
GET /api/v1/chat/health

# Example
curl "http://localhost:8000/api/v1/chat/health"
```

## Configuration

Edit `.env` file to configure:

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.1:8b
EMBEDDING_MODEL=nomic-embed-text:latest

# Application Configuration
UPLOAD_DIR=../data/uploads
FAISS_INDEX_DIR=../data/faiss_index
MAX_UPLOAD_SIZE=50  # MB
CHUNK_SIZE=1000  # Target tokens per chunk
CHUNK_OVERLAP=200  # Overlap between chunks
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── admin.py          # Admin endpoints (upload, list documents)
│   │   └── chat.py           # Chat endpoints (query, health)
│   ├── models/
│   │   └── schemas.py        # Pydantic models for validation
│   ├── services/
│   │   ├── document_processor.py   # Text extraction from documents
│   │   ├── llm_chunker.py         # LLM-based semantic chunking
│   │   ├── ollama_client.py       # Ollama API client
│   │   └── vector_store.py        # FAISS vector store management
│   ├── config.py             # Configuration management
│   └── main.py               # FastAPI application setup
├── .env                      # Environment variables
├── .env.example              # Environment template
├── requirements.txt          # Python dependencies
├── run.py                    # Application runner
└── README.md                 # This file
```

## How It Works

### Document Upload Process

1. **Upload**: User uploads a document via `/api/v1/admin/upload`
2. **Text Extraction**: System extracts text based on file type (PDF, DOCX, etc.)
3. **LLM Chunking**: Llama model analyzes the text and creates semantic chunks
4. **Embedding**: Each chunk is converted to a vector using Nomic Embed
5. **Storage**: Vectors and metadata (including full chunk text) are stored in FAISS

### Query Process

1. **Query Embedding**: User's question is converted to a vector using Nomic Embed
2. **Vector Search**: FAISS finds the most similar document chunks
3. **Context Building**: Retrieved chunks are combined into context
4. **LLM Generation**: Llama generates an answer based on the context
5. **Response**: Answer is returned with source citations

## FAISS Index Details

The system uses FAISS HNSW (Hierarchical Navigable Small World) index for:
- Fast approximate nearest neighbor search
- Good balance between speed and accuracy
- Efficient memory usage

Metadata stored with each vector:
- Document ID
- Original filename
- Full chunk content (for retrieval)
- Chunk index and total chunks
- Upload timestamp

## Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve
```

### Model Not Found
```bash
# Pull required models
ollama pull llama3.1:8b
ollama pull nomic-embed-text:latest

# List installed models
ollama list
```

### Memory Issues
- Reduce `CHUNK_SIZE` in .env
- Use quantized Llama models (e.g., llama3.1:8b-q4_0)
- Limit `top_k` in queries

### FAISS Index Corruption
```bash
# Remove and rebuild index
rm -rf ../data/faiss_index/*
# Re-upload documents
```

## Performance Tips

1. **Chunk Size**: Adjust based on your documents
   - Technical docs: 800-1000 tokens
   - Narrative text: 1200-1500 tokens

2. **Top-K Results**: Balance between context and speed
   - Start with k=5
   - Increase for complex queries
   - Decrease for faster responses

3. **FAISS Index Type**: 
   - Current: HNSW (best for <1M vectors)
   - For larger datasets: Consider IVF indices

4. **Batch Processing**: For multiple uploads, process in parallel

## Next Steps

1. Add authentication and authorization
2. Implement conversation history
3. Add document deletion endpoint
4. Create admin dashboard
5. Add support for more file types
6. Implement hybrid search (vector + keyword)
7. Add query caching
8. Create Docker deployment
