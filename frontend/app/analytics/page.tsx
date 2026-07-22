"use client";

import { AgentUsageChart, VolumeChart } from "@/components/charts/analytics-charts";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/dashboard/page-header";
import { MetricCard } from "@/components/dashboard/metric-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useState } from "react";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Legend,
  Line, LineChart, Pie, PieChart, Cell,
  ResponsiveContainer, Tooltip, XAxis, YAxis
} from "recharts";

const metrics = [
  { label: "Retrieval Success", value: "91%", trend: "+4.6%" },
  { label: "Escalation Rate", value: "7.8%", trend: "-1.2%" },
  { label: "Average Latency", value: "1.8s", trend: "-340ms" },
  { label: "Response Quality", value: "88%", trend: "+2.1%" }
];

const escalationData = [
  { day: "Mon", automated: 38, escalated: 4 },
  { day: "Tue", automated: 50, escalated: 8 },
  { day: "Wed", automated: 45, escalated: 6 },
  { day: "Thu", automated: 62, escalated: 11 },
  { day: "Fri", automated: 55, escalated: 9 },
  { day: "Sat", automated: 32, escalated: 6 },
  { day: "Sun", automated: 27, escalated: 4 }
];

const latencyData = [
  { time: "00:00", latency: 1.2 },
  { time: "04:00", latency: 1.0 },
  { time: "08:00", latency: 2.1 },
  { time: "12:00", latency: 2.4 },
  { time: "16:00", latency: 2.0 },
  { time: "20:00", latency: 1.5 },
  { time: "23:00", latency: 1.1 }
];

const voiceUsageData = [
  { day: "Mon", sessions: 9 },
  { day: "Tue", sessions: 14 },
  { day: "Wed", sessions: 12 },
  { day: "Thu", sessions: 19 },
  { day: "Fri", sessions: 16 },
  { day: "Sat", sessions: 8 },
  { day: "Sun", sessions: 7 }
];

const knowledgeRetrievalData = [
  { day: "Mon", success: 88, failed: 12 },
  { day: "Tue", success: 91, failed: 9 },
  { day: "Wed", success: 85, failed: 15 },
  { day: "Thu", success: 93, failed: 7 },
  { day: "Fri", success: 90, failed: 10 },
  { day: "Sat", success: 87, failed: 13 },
  { day: "Sun", success: 94, failed: 6 }
];

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"];

function EscalationChart() {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={escalationData}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey="day" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="automated" fill="#10b981" radius={[4, 4, 0, 0]} stackId="a" />
        <Bar dataKey="escalated" fill="#ef4444" radius={[4, 4, 0, 0]} stackId="a" />
      </BarChart>
    </ResponsiveContainer>
  );
}

function LatencyChart() {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={latencyData}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey="time" />
        <YAxis domain={[0, 3]} />
        <Tooltip />
        <Area dataKey="latency" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.15} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

function VoiceUsageChart() {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={voiceUsageData}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey="day" />
        <YAxis />
        <Tooltip />
        <Area dataKey="sessions" stroke="#10b981" fill="#10b981" fillOpacity={0.15} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

function KnowledgeRetrievalChart() {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={knowledgeRetrievalData}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey="day" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="success" fill="#3b82f6" radius={[4, 4, 0, 0]} stackId="a" />
        <Bar dataKey="failed" fill="#ef4444" radius={[4, 4, 0, 0]} stackId="a" />
      </BarChart>
    </ResponsiveContainer>
  );
}

export default function AnalyticsPage() {
  const [tab, setTab] = useState("overview");

  return (
    <AppShell>
      <PageHeader title="Analytics" description="Conversation volume, agent usage, knowledge success, escalation rate, latency, voice usage, and quality." />
      <Tabs value={tab} onChange={setTab}>
        <TabsList className="mb-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="voice">Voice</TabsTrigger>
          <TabsTrigger value="latency">Latency</TabsTrigger>
          <TabsTrigger value="knowledge">Knowledge</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <ErrorBoundary>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {metrics.map((metric) => <MetricCard key={metric.label} {...metric} />)}
            </div>
            <div className="mt-4 grid gap-4 xl:grid-cols-2">
              <Card>
                <CardHeader><CardTitle>Conversation Volume</CardTitle></CardHeader>
                <CardContent><VolumeChart /></CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Agent Usage</CardTitle></CardHeader>
                <CardContent><AgentUsageChart /></CardContent>
              </Card>
              <Card className="xl:col-span-2">
                <CardHeader><CardTitle>Escalations vs Automated</CardTitle></CardHeader>
                <CardContent><EscalationChart /></CardContent>
              </Card>
            </div>
          </ErrorBoundary>
        </TabsContent>

        <TabsContent value="voice">
          <ErrorBoundary>
            <div className="grid gap-4 xl:grid-cols-2">
              <Card>
                <CardHeader><CardTitle>Voice Session Volume</CardTitle></CardHeader>
                <CardContent><VoiceUsageChart /></CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Voice Usage Distribution</CardTitle></CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={260}>
                    <PieChart>
                      <Pie data={[
                        { name: "FAQ", value: 45 }, { name: "Lead", value: 25 },
                        { name: "Scheduling", value: 18 }, { name: "Escalation", value: 12 }
                      ]} cx="50%" cy="50%" outerRadius={80} dataKey="value" label>
                        {[
                          { name: "FAQ", value: 45 }, { name: "Lead", value: 25 },
                          { name: "Scheduling", value: 18 }, { name: "Escalation", value: 12 }
                        ].map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          </ErrorBoundary>
        </TabsContent>

        <TabsContent value="latency">
          <ErrorBoundary>
            <Card>
              <CardHeader><CardTitle>Average Latency by Hour</CardTitle></CardHeader>
              <CardContent><LatencyChart /></CardContent>
            </Card>
          </ErrorBoundary>
        </TabsContent>

        <TabsContent value="knowledge">
          <ErrorBoundary>
            <Card>
              <CardHeader><CardTitle>Knowledge Retrieval Success Rate</CardTitle></CardHeader>
              <CardContent><KnowledgeRetrievalChart /></CardContent>
            </Card>
          </ErrorBoundary>
        </TabsContent>
      </Tabs>
    </AppShell>
  );
}
