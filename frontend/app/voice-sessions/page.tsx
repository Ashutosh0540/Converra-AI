"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Mic, Radio, Send, Square } from "lucide-react";
import { useMemo, useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/dashboard/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";
import { apiBaseUrl } from "@/lib/utils";
import { useVoiceWebSocket } from "@/hooks/use-realtime";

export default function VoiceSessionsPage() {
  const client = useQueryClient();
  const [message, setMessage] = useState("");
  const start = useMutation({ mutationFn: api.startVoiceSession, onSuccess: () => client.invalidateQueries({ queryKey: ["voice-sessions"] }) });
  const end = useMutation({ mutationFn: api.endVoiceSession, onSuccess: () => client.invalidateQueries({ queryKey: ["voice-sessions"] }) });
  const session = start.data;
  const socketUrl = useMemo(() => {
    if (!session) return null;
    const token = getAccessToken();
    return `${apiBaseUrl().replace(/^http/, "ws")}${session.websocket_url}?token=${encodeURIComponent(token ?? "")}`;
  }, [session]);
  const voice = useVoiceWebSocket(socketUrl);

  const sendTranscript = () => {
    if (!session || !message.trim()) return;
    voice.send({ type: "text", session_id: session.session_id, text: message.trim(), is_final: true });
    setMessage("");
  };

  return (
    <AppShell>
      <PageHeader title="Voice Sessions" description="Live voice transcript, latency, active agent, connection health, and human takeover state." action={<div className="flex gap-2"><Badge tone={voice.connected ? "success" : "warning"}>{voice.connected ? "CONNECTED" : "IDLE"}</Badge>{session && <Button size="sm" variant="ghost" onClick={() => end.mutate(session.session_id)} disabled={end.isPending}><Square className="h-4 w-4" />End</Button>}<Button size="sm" variant="primary" onClick={() => start.mutate()} disabled={start.isPending || Boolean(session)}><Mic className="h-4 w-4" />{start.isPending ? "Starting..." : "Start Session"}</Button></div>} />
      <ErrorBoundary>
        <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
          <Card className="min-h-[520px]"><CardHeader><CardTitle>Live Transcript</CardTitle><Badge tone={voice.takeover ? "warning" : "success"}>{voice.takeover ? "HUMAN TAKEOVER" : "AI ACTIVE"}</Badge></CardHeader><CardContent className="flex min-h-[420px] flex-col"><div className="flex-1 space-y-2 overflow-auto">{voice.transcripts.length === 0 ? <div className="flex h-full items-center justify-center text-sm text-muted-foreground">Start a session and send text or microphone audio through the voice WebSocket.</div> : voice.transcripts.map((turn, index) => <div key={index} className="rounded-md border bg-background p-3 text-sm"><div className="mb-1 text-xs uppercase text-muted-foreground">{turn.role}</div>{turn.content}</div>)}</div><div className="mt-4 flex gap-2"><Input value={message} onChange={(event) => setMessage(event.target.value)} onKeyDown={(event) => event.key === "Enter" && sendTranscript()} placeholder="Send a transcript turn" disabled={!voice.connected || voice.takeover} /><Button variant="primary" onClick={sendTranscript} disabled={!voice.connected || !message.trim() || voice.takeover}><Send className="h-4 w-4" />Send</Button></div></CardContent></Card>
          <Card><CardHeader><CardTitle>Session State</CardTitle><Radio className={voice.connected ? "h-4 w-4 text-emerald-500" : "h-4 w-4 text-muted-foreground"} /></CardHeader><CardContent className="space-y-3 text-sm"><Row label="Session ID" value={session?.session_id ?? "Not started"} /><Row label="Conversation ID" value={session?.conversation_id ?? "n/a"} /><Row label="Active Agent" value={session?.active_agent ?? "Routing"} /><Row label="Status" value={voice.takeover ? "HUMAN TAKEOVER" : session?.status ?? "n/a"} /><Row label="Round-trip latency" value={voice.latencyMs ? `${Math.round(voice.latencyMs)}ms` : "Awaiting turn"} /><Row label="Microphone" value="Ready for WebSocket audio" /><Row label="Speaking" value={voice.transcripts[voice.transcripts.length - 1]?.role === "assistant" ? "Assistant" : "Customer / idle"} /></CardContent></Card>
        </div>
      </ErrorBoundary>
    </AppShell>
  );
}

function Row({ label, value }: { label: string; value: string }) { return <div className="flex justify-between gap-3 border-b pb-3"><span className="text-muted-foreground">{label}</span><span className="max-w-[260px] truncate text-right font-medium">{value}</span></div>; }
