"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { DashboardMetric } from "@/types/api";

export function useDashboardData() {
  const realtimeOptions = { refetchInterval: 15_000 };
  const users = useQuery({ queryKey: ["users"], queryFn: api.users, ...realtimeOptions });
  const documents = useQuery({ queryKey: ["knowledge"], queryFn: api.knowledge, ...realtimeOptions });
  const escalations = useQuery({ queryKey: ["escalations"], queryFn: api.dashboardQueue, ...realtimeOptions });
  const conversations = useQuery({ queryKey: ["conversations"], queryFn: api.conversations, ...realtimeOptions });
  const voiceSessions = useQuery({ queryKey: ["voice-sessions"], queryFn: api.voiceSessions, ...realtimeOptions });
  const organizations = useQuery({ queryKey: ["organizations"], queryFn: api.organizations, ...realtimeOptions });
  const me = useQuery({ queryKey: ["me"], queryFn: api.me });

  const metrics = useMemo<DashboardMetric[]>(() => {
    const escalationItems = escalations.data?.items ?? [];
    const docs = documents.data ?? [];
    const activeUsers = (users.data ?? []).filter((user) => user.is_active);
    const allConversations = conversations.data ?? [];
    const calls = voiceSessions.data ?? [];
    const confidenceSamples = escalationItems.map((item) => item.confidence_score);
    const averageConfidence = confidenceSamples.length
      ? `${Math.round((confidenceSamples.reduce((sum, value) => sum + value, 0) / confidenceSamples.length) * 100)}%`
      : "—";
    return [
      { label: "Total Conversations", value: String(allConversations.length), trend: `${allConversations.filter((item) => item.status === "ACTIVE").length} active` },
      { label: "Voice Calls", value: String(calls.length), trend: `${calls.filter((item) => item.is_active).length} live` },
      { label: "Knowledge Documents", value: String(docs.length), trend: `${docs.filter((doc) => doc.status === "READY").length} ready` },
      { label: "Escalations", value: String(escalationItems.length), trend: `${escalationItems.filter((item) => item.status === "PENDING").length} pending` },
      { label: "Organizations", value: String((organizations.data ?? []).length), trend: "available tenants" },
      { label: "Users", value: String(activeUsers.length), trend: me.data?.role ?? "team" },
      { label: "Average Response Time", value: "—", trend: "not recorded yet" },
      { label: "Average Confidence", value: averageConfidence, trend: "from escalation decisions" },
      { label: "Knowledge Retrieval Rate", value: allConversations.length ? `${Math.round((allConversations.filter((item) => item.retrieved_documents.length > 0).length / allConversations.length) * 100)}%` : "—", trend: "retrieved conversations" },
      { label: "Agent Usage", value: allConversations.length ? String(new Set(allConversations.map((item) => item.active_agent).filter(Boolean)).size) : "—", trend: "active agent types" }
    ];
  }, [conversations.data, documents.data, escalations.data, me.data?.role, organizations.data, users.data, voiceSessions.data]);

  return {
    metrics,
    users,
    documents,
    escalations,
    conversations,
    voiceSessions,
    organizations,
    me,
    isLoading: users.isLoading || documents.isLoading || escalations.isLoading || conversations.isLoading || voiceSessions.isLoading || organizations.isLoading || me.isLoading
  };
}
