import { FunctionCallMessageCard } from "./function-call-message-card";
import { NormalMessageCard } from "./normal-message-card";
import { ReasoningMessageCard } from "./reasoning-message-card";

export type NormalMessageContent = {
  type: 'message';
  role?: string;
  content?: string | Array<{ text?: string;[key: string]: unknown }> | Record<string, unknown>;
  id?: string;
  status?: string;
  [key: string]: unknown;
};

export type ReasoningContent = {
  type: 'reasoning';
  summary: Array<{ text: string; type: string }>;
  [key: string]: unknown;
};

export type FunctionCallContent = {
  type: 'function_call';
  arguments?: string;
  call_id: string;
  name?: string;
  id?: string;
  status?: string;
  output?: string;
  [key: string]: unknown;
};

export type OtherMessageContent = {
  type: string;
  [key: string]: unknown;
};

export type MessageContent = NormalMessageContent | ReasoningContent | FunctionCallContent | OtherMessageContent;


type MessageCardProps = {
  content: MessageContent;
  createdAt: string;
  isUser: boolean;
};

export default function MessageCard({ content, createdAt, isUser }: MessageCardProps) {
  if (content.type !== 'message' && content.type !== 'function_call' && content.type !== 'reasoning') {
    return (
      <div>
        <div className={`inline-block px-4 py-2 rounded-lg ${isUser
          ? "bg-primary text-primary-foreground"
          : "bg-muted"
          }`}>
          {JSON.stringify(content)}
        </div>
        <div className="text-xs text-muted-foreground mt-1">
          {new Date(createdAt).toLocaleTimeString()}
        </div>
      </div>
    )
  }

  if (content.type === "reasoning") {
    const reasoningContent = content as ReasoningContent;
    if (reasoningContent.summary && reasoningContent.summary.length > 0) {
      return <ReasoningMessageCard content={reasoningContent} />;
    }
    return null;
  }

  if (content.type === "function_call") {
    return <FunctionCallMessageCard content={content as FunctionCallContent} />;
  }

  return <NormalMessageCard content={content as NormalMessageContent} createdAt={createdAt} isUser={isUser} />;
} 