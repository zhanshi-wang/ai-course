"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { BACKEND_PUBLIC_WS_URL, BACKEND_PUBLIC_URL } from "@/lib/api-utils";
import { useParams } from "next/navigation";

// A more specific type for the flexible content structure
type MessageContent = {
  type?: string;
  role?: string;
  content?: string | MessageContent;
  [key: string]: unknown;
};

type ChatMessage = {
  id: string;
  session_id: string;
  created_at: string;
  content: MessageContent;
};

export default function Chat() {
  const [currentWs, setCurrentWs] = useState<WebSocket>();
  const [connectionStatus, setConnectionStatus] = useState<
    "connected" | "disconnected" | "error"
  >("disconnected");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const { sessionId } = useParams();

  const isUserMessage = (content: MessageContent): boolean => {
    if (content?.role === "user") {
      return true;
    }

    return false;
  };

  const fetchMessages = useCallback(async () => {
    if (!sessionId) return;

    try {
      setLoading(true);
      const response = await fetch(
        `${BACKEND_PUBLIC_URL}/chat/sessions/${sessionId}/messages`,
        {
          credentials: "include",
        },
      );

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setMessages(data);
    } catch (error) {
      console.error("Failed to fetch messages:", error);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const connectWebSocket = useCallback(() => {
    if (!sessionId) return;

    const ws = new WebSocket(`${BACKEND_PUBLIC_WS_URL}/ws/chat/${sessionId}`);

    ws.onopen = () => {
      setConnectionStatus("connected");

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };

    ws.onmessage = (event) => {
      // Parse the message from the WebSocket
      const message = JSON.parse(event.data);
      console.log("Received message:", message);

      // Add the new message to the messages array
      setMessages((prevMessages) => [...prevMessages, message]);
    };

    ws.onerror = () => {
      setConnectionStatus("error");
    };

    ws.onclose = (event) => {
      setConnectionStatus("disconnected");

      if (event.code === 1000) {
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, 1000);
      }
    };

    setCurrentWs(ws);

    return ws;
  }, [sessionId]);

  const sendMessage = () => {
    if (!currentWs || !input || !sessionId) {
      return;
    }

    // Create a new message object to display instantly in UI
    const newMessage: ChatMessage = {
      id: crypto.randomUUID(),
      session_id: sessionId as string,
      created_at: new Date().toISOString(),
      content: {
        type: "message",
        role: "user",
        content: input,
      },
    };

    // Add user message to UI immediately
    setMessages((prevMessages) => [...prevMessages, newMessage]);

    // Clear input field
    setInput("");

    // Send message to backend
    if (currentWs.readyState === WebSocket.OPEN) {
      currentWs.send(input);
    } else {
      setConnectionStatus("error");

      if (currentWs.readyState === WebSocket.CLOSED) {
        connectWebSocket();
      }
    }
  };

  useEffect(() => {
    fetchMessages();
    const ws = connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      if (ws) {
        ws.close();
      }
    };
  }, [connectWebSocket, fetchMessages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  console.log(messages);

  return (
    <div className="flex flex-col h-full p-4">
      <h1 className="text-2xl font-bold mb-4">Chat</h1>
      <div className="text-sm mb-2">
        Connection status:{" "}
        <span
          className={`font-semibold ${
            connectionStatus === "connected"
              ? "text-green-500"
              : connectionStatus === "error"
                ? "text-red-500"
                : "text-yellow-500"
          }`}
        >
          {connectionStatus}
        </span>
      </div>
      <div className="flex-1 overflow-y-auto mb-4 border rounded-md p-4">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted-foreground">Loading messages...</p>
          </div>
        ) : messages.length === 0 ? (
          <p className="text-center text-muted-foreground">
            No messages yet. Start a conversation!
          </p>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`mb-4 ${isUserMessage(message.content) ? "text-right" : "text-left"}`}
            >
              <div
                className={`inline-block px-4 py-2 rounded-lg ${
                  isUserMessage(message.content)
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                {JSON.stringify(message.content)}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {new Date(message.created_at).toLocaleTimeString()}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Type your message..."
          className="flex-1"
        />
        <Button
          onClick={sendMessage}
          disabled={connectionStatus !== "connected"}
        >
          Send
        </Button>
      </div>
    </div>
  );
}
