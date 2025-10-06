
import React from 'react';
import { Source } from '../services/types';

interface SourceCardProps {
  source: Source;
  index: number;
}

export const SourceCard: React.FC<SourceCardProps> = ({ source, index }) => {
  return (
    <div className="rag-source-card">
      <div className="rag-source-header">
        <span className="rag-source-index">#{index + 1}</span>
        <span className="rag-source-filename">{source.filename}</span>
        <span className="rag-source-score">
          {(source.similarity_score * 100).toFixed(1)}% match
        </span>
      </div>
      <div className="rag-source-info">
        Chunk {source.chunk_index + 1} of {source.total_chunks}
      </div>
      <div className="rag-source-preview">
        {source.content_preview}
      </div>
    </div>
  );
};

