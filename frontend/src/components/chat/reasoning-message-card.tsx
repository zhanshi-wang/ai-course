import React from 'react';
import { ReasoningContent } from './message-card';


export function ReasoningMessageCard({ content }: { content: ReasoningContent }) {
  return (
    <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 text-sm italic text-muted-foreground">
      {content.summary?.map((item, index) => (
        <div key={index} className="mb-2">
          {item.text}
        </div>
      ))}
    </div>
  );
} 