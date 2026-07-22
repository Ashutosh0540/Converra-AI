"use client";

import { AppShell } from "@/components/layout/app-shell";
import { ActivityFeed } from "@/components/dashboard/activity-feed";
import { MetricCard } from "@/components/dashboard/metric-card";
import { PageHeader } from "@/components/dashboard/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { AgentUsageChart, VolumeChart } from "@/components/charts/analytics-charts";
import { useDashboardData } from "@/hooks/use-dashboard-data";
import { useRealtimeFeed } from "@/hooks/use-realtime";

export default function DashboardPage() {
  const { metrics, isLoading } = useDashboardData();
  const { events, connected } = useRealtimeFeed();

  return (
    <AppShell>
      <PageHeader
        title="Dashboard Home"
        description="A live operational view across conversations, voice, knowledge, and human support."
        action={
          <Badge tone={connected ? "success" : "danger"}>
            {connected ? "WebSocket Connected" : "WebSocket Disconnected"}
          </Badge>
        }
      />
      <ErrorBoundary>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {isLoading
            ? Array.from({ length: 8 }).map((_, index) => <Skeleton key={index} className="h-28" />)
            : metrics.map((metric) => <MetricCard key={metric.label} {...metric} />)}
        </div>
      </ErrorBoundary>
      <div className="mt-4 grid gap-4 xl:grid-cols-[1.5fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Conversation and Voice Volume</CardTitle>
          </CardHeader>
          <CardContent>
            <ErrorBoundary><VolumeChart /></ErrorBoundary>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Top Agents</CardTitle>
          </CardHeader>
          <CardContent>
            <ErrorBoundary><AgentUsageChart /></ErrorBoundary>
          </CardContent>
        </Card>
      </div>
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Live Activity Feed</CardTitle>
          <Badge tone={connected ? "success" : "danger"}>{connected ? "LIVE" : "OFFLINE"}</Badge>
        </CardHeader>
        <CardContent>
          <ErrorBoundary><ActivityFeed events={events} /></ErrorBoundary>
        </CardContent>
      </Card>
    </AppShell>
  );
}
