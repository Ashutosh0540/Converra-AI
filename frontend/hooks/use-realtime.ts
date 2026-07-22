"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { getAccessToken } from "@/lib/auth";
import { wsBaseUrl } from "@/lib/utils";

export interface RealtimeEvent {
  id: string;
  type: string;
  message: string;
  at: string;
  payload?: Record<string, unknown>;
}

function createRealtimeEvent(type: string, message: string, payload?: Record<string, unknown>): RealtimeEvent {
  return { id: crypto.randomUUID(), type, message, at: new Date().toISOString(), payload };
}

export function useRealtimeFeed() {
  const [events, setEvents] = useState<RealtimeEvent[]>([
    createRealtimeEvent("system", "Realtime layer ready")
  ]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const token = useMemo(() => (typeof window !== "undefined" ? getAccessToken() : null), []);
  const wsUrl = token ? `${wsBaseUrl()}/ws/dashboard?token=${encodeURIComponent(token)}` : null;

  useEffect(() => {
    if (!wsUrl) return;

    let reconnectTimeout: ReturnType<typeof setTimeout>;
    let shouldReconnect = true;

    function connect() {
      if (!wsUrl) return;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        setEvents((prev) => [createRealtimeEvent("system", "WebSocket connected"), ...prev].slice(0, 50));
      };

      ws.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data);
          setEvents((prev) => [
            createRealtimeEvent(data.type ?? "event", data.message ?? JSON.stringify(data), data.payload),
            ...prev
          ].slice(0, 50));
        } catch {
          setEvents((prev) => [
            createRealtimeEvent("event", msg.data),
            ...prev
          ].slice(0, 50));
        }
      };

      ws.onclose = () => {
        setConnected(false);
        wsRef.current = null;
        if (shouldReconnect) {
          reconnectTimeout = setTimeout(connect, 5000);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      shouldReconnect = false;
      clearTimeout(reconnectTimeout);
      wsRef.current?.close();
    };
  }, [wsUrl]);

  const voiceUrl = useMemo(() => {
    return token ? `${wsBaseUrl()}/ws/voice?token=${encodeURIComponent(token)}` : null;
  }, [token]);

  const sendEvent = useRef<(data: string) => void>(() => undefined);

  useEffect(() => {
    if (wsRef.current) {
      sendEvent.current = wsRef.current.send.bind(wsRef.current);
    }
  }, [connected]);

  return { events, connected, voiceUrl, send: sendEvent.current };
}

export function useVoiceWebSocket(url: string | null) {
  const [transcripts, setTranscripts] = useState<Array<{ role: string; content: string }>>([]);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [takeover, setTakeover] = useState(false);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!url) return;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data);
        if (data.type === "transcript_final" && data.payload?.text) {
          setTranscripts((prev) => [...prev, { role: "customer", content: data.payload.text }]);
        }
        if (data.type === "ai_response" && data.payload?.response?.message) {
          setTranscripts((prev) => [...prev, { role: "assistant", content: data.payload.response.message }]);
          setLatencyMs(data.payload?.latency?.total_ms ?? null);
        }
        if (data.type === "human_takeover") {
          setTakeover(true);
        }
      } catch {
        // ignore
      }
    };
    ws.onclose = () => setConnected(false);

    return () => ws.close();
  }, [url]);

  const send = (data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  };

  return { transcripts, connected, latencyMs, takeover, send };
}
