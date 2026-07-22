"use client";

import { toast } from "sonner";
import { apiBaseUrl } from "@/lib/utils";
import { getAccessToken } from "@/lib/auth";
import type {
  AIResponse,
  Conversation,
  EscalationQueueResponse,
  EscalationDetailResponse,
  EscalationActionResponse,
  KnowledgeDocument,
  KnowledgeSearchResponse,
  LoginResponse,
  Organization,
  User,
  VoiceSessionStart,
  VoiceSessionEnd,
  VoiceSessionListItem
} from "@/types/api";

type FetchOptions = RequestInit & { auth?: boolean };

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const isForm = options.body instanceof FormData;
  if (!isForm && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (options.auth !== false) {
    const token = getAccessToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${apiBaseUrl()}${path}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      detail = response.statusText;
    }
    toast.error(typeof detail === "string" ? detail : "Request failed");
    throw new ApiError(typeof detail === "string" ? detail : "Request failed", response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  // Auth
  login: (email: string, password: string) =>
    request<LoginResponse>("/api/v1/users/login", {
      method: "POST",
      auth: false,
      body: JSON.stringify({ email, password })
    }),
  me: () => request<User>("/api/v1/users/me"),

  // Users
  users: () => request<User[]>("/api/v1/users"),

  // Organizations
  organizations: () => request<Organization[]>("/api/v1/organizations", { auth: false }),

  // Knowledge
  knowledge: () => request<KnowledgeDocument[]>("/api/v1/knowledge"),
  uploadKnowledge: (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return request<KnowledgeDocument>("/api/v1/knowledge/upload", {
      method: "POST",
      body
    });
  },
  deleteKnowledge: (id: string) =>
    request<void>(`/api/v1/knowledge/${id}`, { method: "DELETE" }),
  searchKnowledge: (query: string) =>
    request<KnowledgeSearchResponse>("/api/v1/knowledge/search", {
      method: "POST",
      body: JSON.stringify({ query, top_k: 5 })
    }),

  // AI / Chat
  chat: (message: string, conversationId?: string) =>
    request<AIResponse>("/api/v1/ai/chat", {
      method: "POST",
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        source_channel: "chat"
      })
    }),
  conversations: () => request<Conversation[]>("/api/v1/ai/conversations"),

  // Escalations (matching backend routes: /escalations)
  escalations: () => request<EscalationQueueResponse>("/escalations"),
  escalationDetail: (id: string) =>
    request<EscalationDetailResponse>(`/escalations/${id}`),
  dashboardQueue: () => request<EscalationQueueResponse>("/dashboard/queue"),
  assignEscalation: (id: string, assigneeUserId: string, notes?: string) =>
    request<EscalationActionResponse>(`/escalations/${id}/assign`, {
      method: "POST",
      body: JSON.stringify({ assignee_user_id: assigneeUserId, notes: notes ?? null })
    }),
  acceptEscalation: (id: string) =>
    request<EscalationActionResponse>(`/escalations/${id}/accept`, {
      method: "POST",
      body: JSON.stringify({})
    }),
  resolveEscalation: (id: string) =>
    request<EscalationActionResponse>(`/escalations/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify({})
    }),
  closeEscalation: (id: string) =>
    request<EscalationActionResponse>(`/escalations/${id}/close`, {
      method: "POST",
      body: JSON.stringify({})
    }),
  transferEscalation: (id: string, assigneeUserId: string, notes?: string) =>
    request<EscalationActionResponse>(`/escalations/${id}/transfer`, {
      method: "POST",
      body: JSON.stringify({ assignee_user_id: assigneeUserId, notes: notes ?? null })
    }),

  // Voice Sessions
  startVoiceSession: () =>
    request<VoiceSessionStart>("/voice/session/start", {
      method: "POST",
      body: JSON.stringify({})
    }),
  voiceSessions: () => request<VoiceSessionListItem[]>("/voice/sessions"),
  endVoiceSession: (sessionId: string) =>
    request<VoiceSessionEnd>("/voice/session/end", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId })
    })
};
