
import React, { useEffect, useRef } from 'react';
import { Message as MessageType } from '../services/types';
import { Message } from './Message';

interface MessageListProps {
  messages: MessageType[];
  isLoading: boolean;
}

export const MessageList: React.FC<MessageListProps> = ({ messages, isLoading }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  return (
    <div className="rag-message-list">
      {messages.length === 0 && !isLoading && (
        <div className="rag-empty-state">
          <div className="rag-empty-icon">💬</div>
          <h3>Welcome to RAG Chat</h3>
          <p>Ask me anything about your uploaded documents!</p>
        </div>
      )}
      
      {messages.map((message) => (
        <Message key={message.id} message={message} />
      ))}
      
      {isLoading && (
        <div className="rag-message rag-message-assistant">
          <div className="rag-message-header">
            <span className="rag-message-role">🤖 Assistant</span>
          </div>
          <div className="rag-message-content">
            <div className="rag-typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      )}
      
      <div ref={messagesEndRef} />
    </div>
  );
};

