"use client";

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Send } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/dashboard/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useRealtimeFeed } from "@/hooks/use-realtime";
import type { AIResponse, Citation } from "@/types/api";

export default function ConversationsPage() {
  const [message, setMessage] = useState("What can Converra AI do?");
  const [conversationId, setConversationId] = useState<string>();
  const [turns, setTurns] = useState<Array<{ role: string; content: string; response?: AIResponse }>>([]);
  const { connected } = useRealtimeFeed();
  const chat = useMutation({
    mutationFn: () => api.chat(message, conversationId),
    onSuccess: (response) => {
      setConversationId(response.conversation_id);
      setTurns((current) => [
        ...current,
        { role: "user", content: message },
        { role: "assistant", content: response.message, response }
      ]);
      setMessage("");
    }
  });

  const latest = turns.findLast((turn) => turn.response)?.response;

  return (
    <AppShell>
      <PageHeader
        title="Live Conversations"
        description="Realtime transcript, confidence, sources, organization context, and human takeover state."
        action={
          <Badge tone={connected ? "success" : "danger"}>
            {connected ? "Realtime Active" : "Realtime Offline"}
          </Badge>
        }
      />
      <ErrorBoundary>
        <div className="grid gap-4 xl:grid-cols-[1.4fr_0.8fr]">
          <Card className="min-h-[620px]">
            <CardHeader>
              <CardTitle>Transcript</CardTitle>
              <Badge tone={latest?.status === "ESCALATED" ? "danger" : "success"}>{latest?.status ?? "READY"}</Badge>
            </CardHeader>
            <CardContent className="flex min-h-[540px] flex-col">
              <div className="flex-1 space-y-3 overflow-auto">
                {turns.length === 0 && (
                  <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                    Send a message to start a conversation
                  </div>
                )}
                {turns.map((turn, index) => (
                  <div key={index} className="rounded-md border bg-background p-3">
                    <div className="mb-1 text-xs uppercase text-muted-foreground">{turn.role}</div>
                    <div className="text-sm">{turn.content}</div>
                  </div>
                ))}
              </div>
              <div className="mt-4 flex gap-2">
                <Input value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Send a customer message" />
                <Button variant="primary" onClick={() => chat.mutate()} disabled={!message || chat.isPending}>
                  <Send className="h-4 w-4" />
                  Send
                </Button>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Conversation State</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <Info label="Conversation ID" value={conversationId ?? "New"} />
              <Info label="Active Agent" value={latest?.agent ?? "n/a"} />
              <Info label="Workflow Stage" value={latest?.workflow_stage ?? "n/a"} />
              <Info label="Confidence" value={latest ? `${Math.round(latest.confidence * 100)}%` : "n/a"} />
              <Info label="Human Takeover" value={latest?.structured_data?.human_mode ? "ACTIVE" : "INACTIVE"} />
              <Info label="Escalation Decision" value={latest?.escalation_decision?.reason ? String(latest.escalation_decision.reason) : "n/a"} />
              <div>
                <div className="mb-2 text-xs text-muted-foreground">Sources used</div>
                <div className="space-y-2">
                  {(latest?.retrieved_sources ?? latest?.citations ?? []).length === 0 && (
                    <div className="text-xs text-muted-foreground">No sources cited</div>
                  )}
                  {(latest?.retrieved_sources ?? latest?.citations ?? []).map((source: Citation) => (
                    <div key={`${source.document_id}-${source.chunk_number}`} className="rounded-md border p-2 text-xs">
                      {source.document} p.{source.page} chunk {source.chunk_number}
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </ErrorBoundary>
    </AppShell>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b pb-3">
      <span className="text-muted-foreground">{label}</span>
      <span className="truncate font-medium">{value}</span>
    </div>
  );
}
