
import React, { useState } from 'react';
import { Message as MessageType } from '../services/types';
import { SourceCard } from './SourceCard';

interface MessageProps {
  message: MessageType;
}

export const Message: React.FC<MessageProps> = ({ message }) => {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === 'user';

  return (
    <div className={`rag-message ${isUser ? 'rag-message-user' : 'rag-message-assistant'}`}>
      <div className="rag-message-header">
        <span className="rag-message-role">
          {isUser ? '👤 You' : '🤖 Assistant'}
        </span>
        <span className="rag-message-time">
          {message.timestamp.toLocaleTimeString()}
        </span>
      </div>
      <div className="rag-message-content">
        {message.content}
      </div>
      {!isUser && message.sources && message.sources.length > 0 && (
        <div className="rag-message-sources">
          <button
            className="rag-sources-toggle"
            onClick={() => setShowSources(!showSources)}
          >
            📚 {message.sources.length} Source{message.sources.length > 1 ? 's' : ''}
            <span className={`rag-toggle-icon ${showSources ? 'rag-toggle-open' : ''}`}>
              ▼
            </span>
          </button>
          {showSources && (
            <div className="rag-sources-list">
              {message.sources.map((source, idx) => (
                <SourceCard key={idx} source={source} index={idx} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

