"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { useRouter, useParams } from "next/navigation";
import { BACKEND_PUBLIC_URL } from "@/lib/api-utils";

type ChatSession = {
  id: string;
  user_id: string;
  name: string;
  created_at: string;
  updated_at: string;
};

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [creatingSession, setCreatingSession] = useState(false);
  const router = useRouter();
  const params = useParams();
  const currentSessionId = params?.sessionId as string;

  // Fetch chat sessions
  const fetchSessions = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_PUBLIC_URL}/chat/sessions`, {
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setSessions(data || []);
    } catch (error) {
      console.error("Failed to fetch sessions:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Create a new chat session and redirect to it
  const createSession = async () => {
    try {
      setCreatingSession(true);
      const response = await fetch(`${BACKEND_PUBLIC_URL}/chat/sessions`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (data?.id) {
        await fetchSessions();
        router.push(`/chat/${data.id}`);
      }
    } catch (error) {
      console.error("Failed to create session:", error);
    } finally {
      setCreatingSession(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  return (
    <div className="flex h-full">
      {/* Sessions Sidebar */}
      <div className="w-64 border-r p-4 overflow-y-auto">
        <div className="flex flex-col h-full">
          <h2 className="text-lg font-semibold mb-4">Chat Sessions</h2>
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <p className="text-muted-foreground text-sm">
                Loading sessions...
              </p>
            ) : sessions.length === 0 ? (
              <p className="text-muted-foreground text-sm">No sessions yet</p>
            ) : (
              <div className="space-y-2">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    className={`p-2 rounded-md cursor-pointer ${
                      session.id === currentSessionId
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-muted"
                    }`}
                    onClick={() => router.push(`/chat/${session.id}`)}
                  >
                    <div className="font-medium truncate">
                      {session.name || "Unnamed chat"}
                    </div>
                    <div className="text-xs opacity-70">
                      {new Date(session.created_at).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <Button
            onClick={createSession}
            className="mt-4 w-full"
            disabled={creatingSession}
          >
            {creatingSession ? "Creating..." : "New Chat"}
          </Button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden">{children}</div>
    </div>
  );
}
