"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { BACKEND_PUBLIC_URL } from "@/lib/api-utils";

export default function ChatIndex() {
  const router = useRouter();

  useEffect(() => {
    async function getOrCreateSession() {
      try {
        // Try to fetch existing sessions
        const response = await fetch(`${BACKEND_PUBLIC_URL}/chat/sessions`, {
          credentials: "include",
        });

        if (!response.ok) {
          throw new Error(`Error ${response.status}: ${response.statusText}`);
        }

        const sessions = await response.json();

        if (sessions && sessions.length > 0) {
          // Redirect to the most recent session
          router.push(`/chat/${sessions[0].id}`);
        } else {
          // No sessions exist, create one automatically
          const createResponse = await fetch(
            `${BACKEND_PUBLIC_URL}/chat/sessions`,
            {
              method: "POST",
              credentials: "include",
              headers: {
                "Content-Type": "application/json",
              },
            },
          );

          if (!createResponse.ok) {
            throw new Error(
              `Error ${createResponse.status}: ${createResponse.statusText}`,
            );
          }

          const newSession = await createResponse.json();

          if (newSession?.id) {
            router.push(`/chat/${newSession.id}`);
          }
        }
      } catch (error) {
        console.error("Error managing sessions:", error);
      }
    }

    getOrCreateSession();
  }, [router]);

  // Show loading state while redirecting
  return (
    <div className="flex items-center justify-center h-full">
      <p className="text-muted-foreground">Loading chat...</p>
    </div>
  );
}
