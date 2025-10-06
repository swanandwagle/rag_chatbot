
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
}

export interface Source {
  filename: string;
  chunk_index: number;
  total_chunks: number;
  similarity_score: number;
  content_preview: string;
}

export interface ChatRequest {
  query: string;
  top_k?: number;
  conversation_history?: Array<{
    role: string;
    content: string;
  }>;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  query: string;
  timestamp: string;
}

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  status: string;
  message: string;
  chunks_created: number;
  timestamp: string;
}

export interface HealthResponse {
  status: string;
  ollama_connected: boolean;
  llm_model: string;
  embedding_model: string;
  total_documents: number;
  total_chunks: number;
}

