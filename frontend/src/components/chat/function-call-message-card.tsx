import React from 'react';
import { FunctionCallContent } from './message-card';

// Define an interface for the context item
interface ContextItem {
  file_id: string;
  file_name: string;
  page_number?: number;
  content: string;
}

// Component for rendering get_context_from_files output
function GetContextFromFilesOutput({ output }: { output: unknown }) {
  let contextData: ContextItem[] = [];
  try {
    contextData = typeof output === 'string'
      ? JSON.parse(output)
      : output;
  } catch {
    return (
      <div className="text-xs text-red-500">Error parsing context data</div>
    );
  }

  // Group items by file_name
  const fileGroups: { [key: string]: number[] } = {};
  contextData.forEach((item: ContextItem) => {
    if (!fileGroups[item.file_name]) {
      fileGroups[item.file_name] = [];
    }
    if (item.page_number) {
      fileGroups[item.file_name].push(item.page_number);
    }
  });

  return (
    <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800 text-sm">
      <div className="text-xs text-muted-foreground mb-1">Files checked:</div>
      <ul className="bg-slate-100 dark:bg-slate-800 p-2 rounded text-xs">
        {Object.entries(fileGroups).map(([fileName, pages], index) => (
          <li key={index} className="mb-1">
            <span className="font-medium">{fileName}</span>
            {pages.length > 0 && (
              <span> - Pages {pages.sort((a, b) => a - b).join(', ')}</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function FunctionCallMessageCard({ content }: { content: FunctionCallContent }) {
  // For get_context_from_files, only show the simplified output
  if (content.name === "get_context_from_files" && content.output) {
    return <GetContextFromFilesOutput output={content.output} />;
  }

  // Parse arguments to display in a more readable format
  const parsedArgs = content.arguments ? JSON.parse(content.arguments) : {};

  return (
    <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800 text-sm">
      <div className="flex items-center gap-2 mb-2 font-medium">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M8 3H5a2 2 0 0 0-2 2v3"></path>
          <path d="M21 8V5a2 2 0 0 0-2-2h-3"></path>
          <path d="M3 16v3a2 2 0 0 0 2 2h3"></path>
          <path d="M16 21h3a2 2 0 0 0 2-2v-3"></path>
          <rect width="10" height="10" x="7" y="7" rx="2"></rect>
        </svg>
        <span>Function Call: {content.name}</span>
      </div>

      <div className="mb-3">
        <div className="text-xs text-muted-foreground mb-1">Arguments:</div>
        <pre className="whitespace-pre-wrap bg-slate-100 dark:bg-slate-800 p-2 rounded text-xs">
          {JSON.stringify(parsedArgs, null, 2)}
        </pre>
      </div>

      {content.output && (
        <div>
          <div className="text-xs text-muted-foreground mb-1">Output:</div>
          <pre className="whitespace-pre-wrap bg-slate-100 dark:bg-slate-800 p-2 rounded text-xs">
            {typeof content.output === 'object'
              ? JSON.stringify(content.output, null, 2)
              : content.output}
          </pre>
        </div>
      )}

      <div className="text-xs text-muted-foreground mt-2">
        Status: {content.status || 'pending'}
      </div>
    </div>
  );
} 