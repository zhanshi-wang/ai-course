import React from 'react';
import { NormalMessageContent } from './message-card';
type NormalMessageProps = {
  content: NormalMessageContent;
  createdAt: string;
  isUser: boolean;
};

export function NormalMessageCard({ content, createdAt, isUser }: NormalMessageProps) {
  const extractText = () => {
    // Format where content is an array of objects with text
    if (Array.isArray(content.content)) {
      return content.content
        .map(item => item.text || '')
        .join('\n');
    }

    // Format where content is a string
    if (typeof content.content === 'string') {
      return content.content;
    }

    // Format where content is an object
    if (typeof content.content === 'object' && content.content !== null) {
      return JSON.stringify(content.content);
    }

    // Fallback
    return JSON.stringify(content);
  };

  const messageText = extractText();

  return (
    <div>
      <div className={`inline-block px-4 py-2 rounded-lg ${isUser
        ? "bg-primary text-primary-foreground"
        : "bg-muted"
        }`}>
        {messageText}
      </div>
      <div className="text-xs text-muted-foreground mt-1">
        {new Date(createdAt).toLocaleTimeString()}
      </div>
    </div>
  );
} 