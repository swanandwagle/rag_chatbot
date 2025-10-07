
import React, { useState, useEffect } from 'react';
import { Message as MessageType } from '../services/types';
import { RagApiClient } from '../services/api';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import './ChatInterface.css';

export interface ChatInterfaceProps {
  apiUrl?: string;
  title?: string;
  placeholder?: string;
  onError?: (error: Error) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  apiUrl = 'http://localhost:8000/api/v1',
  title = 'RAG Chat Assistant',
  placeholder = 'Ask a question...',
  onError
}) => {
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [apiClient] = useState(() => new RagApiClient(apiUrl));
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'degraded' | 'disconnected' | 'checking'>('checking');

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const health = await apiClient.getHealth();
      // Consider backend reachable even if Ollama is not connected
      setConnectionStatus(health.ollama_connected ? 'connected' : 'degraded');
    } catch (error) {
      setConnectionStatus('disconnected');
      console.error('Health check failed:', error);
    }
  };

  const handleSendMessage = async (content: string) => {
    // Add user message
    const userMessage: MessageType = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Get response from API
      const response = await apiClient.query({
        query: content,
        top_k: 5,
      });

      // Add assistant message
      const assistantMessage: MessageType = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(response.timestamp),
        sources: response.sources,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: MessageType = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Sorry, I encountered an error: ${(error as Error).message}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      
      if (onError) {
        onError(error as Error);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="rag-chat-container">
      <div className="rag-chat-header">
        <h2 className="rag-chat-title">{title}</h2>
        <div className={`rag-status-indicator rag-status-${connectionStatus}`}>
          <span className="rag-status-dot"></span>
          {connectionStatus === 'connected' && 'Connected'}
          {connectionStatus === 'degraded' && 'Degraded'}
          {connectionStatus === 'disconnected' && 'Disconnected'}
          {connectionStatus === 'checking' && 'Checking...'}
        </div>
      </div>
      
      <MessageList messages={messages} isLoading={isLoading} />
      
      <MessageInput
        onSendMessage={handleSendMessage}
        disabled={isLoading || connectionStatus === 'disconnected'}
        placeholder={placeholder}
      />
    </div>
  );
};

