
import React from 'react';
import { ChatInterface } from './components/ChatInterface';
import './App.css';

function App() {
  const handleError = (error: Error) => {
    console.error('Chat error:', error);
  };

  return (
    <div className="app">
      <div className="app-container">
        <ChatInterface
          apiUrl={import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}
          title="RAG Chat Assistant"
          placeholder="Ask a question about your documents..."
          onError={handleError}
        />
      </div>
    </div>
  );
}

export default App;

