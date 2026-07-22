"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, CircleSlash, RefreshCw, UserCheck } from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/dashboard/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogTitle } from "@/components/ui/dialog";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import type { EscalationQueueItem } from "@/types/api";

function EscalationDetailModal({ escalation, onClose }: { escalation: EscalationQueueItem; onClose: () => void }) {
  const detail = useQuery({
    queryKey: ["escalation-detail", escalation.id],
    queryFn: () => api.escalationDetail(escalation.id)
  });

  return (
    <Dialog open={true} onClose={onClose}>
      <DialogTitle>Escalation Detail</DialogTitle>
      <div className="mt-4 space-y-3 text-sm">
        <div className="flex items-center justify-between border-b pb-2">
          <span className="text-muted-foreground">Customer</span>
          <span className="font-medium">{escalation.customer}</span>
        </div>
        <div className="flex items-center justify-between border-b pb-2">
          <span className="text-muted-foreground">Reason</span>
          <span className="max-w-[200px] truncate font-medium">{escalation.escalation_reason}</span>
        </div>
        <div className="flex items-center justify-between border-b pb-2">
          <span className="text-muted-foreground">Priority</span>
          <Badge tone={escalation.priority === "HIGH" || escalation.priority === "CRITICAL" ? "danger" : "warning"}>
            {escalation.priority}
          </Badge>
        </div>
        <div className="flex items-center justify-between border-b pb-2">
          <span className="text-muted-foreground">Status</span>
          <Badge tone={escalation.status === "ACCEPTED" || escalation.status === "RESOLVED" ? "success" : "default"}>
            {escalation.status}
          </Badge>
        </div>
        <div className="flex items-center justify-between border-b pb-2">
          <span className="text-muted-foreground">Assigned Agent</span>
          <span className="font-medium">{escalation.assigned_agent ?? "Unassigned"}</span>
        </div>
        <div className="flex items-center justify-between border-b pb-2">
          <span className="text-muted-foreground">Confidence</span>
          <span className="font-medium">{Math.round(escalation.confidence_score * 100)}%</span>
        </div>
        <div className="flex items-center justify-between border-b pb-2">
          <span className="text-muted-foreground">Channel</span>
          <span className="font-medium">{escalation.source_channel}</span>
        </div>
        <div className="flex items-center justify-between pb-2">
          <span className="text-muted-foreground">Timestamp</span>
          <span className="font-medium">{formatDateTime(escalation.timestamp)}</span>
        </div>
        {detail.data && (
          <>
            <div className="pt-2">
              <div className="mb-2 text-xs font-medium text-muted-foreground">Suggested Reply</div>
              <div className="rounded-md border bg-background p-3 text-sm">
                {detail.data.assist_bundle.suggested_reply}
              </div>
            </div>
            {detail.data.assist_bundle.suggested_next_actions.length > 0 && (
              <div>
                <div className="mb-2 text-xs font-medium text-muted-foreground">Suggested Next Actions</div>
                <div className="flex flex-wrap gap-2">
                  {detail.data.assist_bundle.suggested_next_actions.map((action, i) => (
                    <Badge key={i}>{action}</Badge>
                  ))}
                </div>
              </div>
            )}
            {detail.data.audit_trail.length > 0 && (
              <div>
                <div className="mb-2 text-xs font-medium text-muted-foreground">Audit Trail</div>
                <div className="space-y-2">
                  {detail.data.audit_trail.map((event) => (
                    <div key={event.id} className="rounded-md border bg-background p-2 text-xs">
                      <span className="font-medium">{event.action}</span>
                      {event.notes && <span> &mdash; {event.notes}</span>}
                      <div className="text-muted-foreground">{formatDateTime(event.created_at)}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </Dialog>
  );
}

export default function EscalationsPage() {
  const client = useQueryClient();
  const [selectedEscalation, setSelectedEscalation] = useState<EscalationQueueItem | null>(null);
  const queue = useQuery({ queryKey: ["escalations"], queryFn: api.dashboardQueue });
  const refresh = () => client.invalidateQueries({ queryKey: ["escalations"] });
  const accept = useMutation({ mutationFn: api.acceptEscalation, onSuccess: refresh });
  const resolve = useMutation({ mutationFn: api.resolveEscalation, onSuccess: refresh });
  const close = useMutation({ mutationFn: api.closeEscalation, onSuccess: refresh });

  return (
    <AppShell>
      <PageHeader
        title="Escalation Queue"
        description="Pending, assigned, resolved, and closed human-in-the-loop cases."
        action={
          <Button size="sm" variant="ghost" onClick={refresh}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        }
      />
      <ErrorBoundary>
        <Card>
          <CardHeader>
            <CardTitle>Human Queue</CardTitle>
            <Badge tone={(queue.data?.items.length ?? 0) > 0 ? "warning" : "success"}>
              {queue.data?.items.length ?? 0} active
            </Badge>
          </CardHeader>
          <CardContent className="space-y-3">
            {(queue.data?.items ?? []).length === 0 && (
              <div className="py-8 text-center text-sm text-muted-foreground">
                No active escalations. All conversations are within AI confidence thresholds.
              </div>
            )}
            {(queue.data?.items ?? []).map((item) => (
              <div key={item.id} className="grid gap-3 rounded-md border p-4 xl:grid-cols-[1fr_auto]">
                <div className="cursor-pointer" onClick={() => setSelectedEscalation(item)}>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium">{item.customer}</span>
                    <Badge tone={item.priority === "HIGH" || item.priority === "CRITICAL" ? "danger" : "warning"}>{item.priority}</Badge>
                    <Badge tone={item.status === "ACCEPTED" ? "success" : item.status === "PENDING" ? "warning" : "default"}>{item.status}</Badge>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">{item.escalation_reason}</p>
                  <div className="mt-2 text-xs text-muted-foreground">
                    Confidence {Math.round(item.confidence_score * 100)}% &middot; {item.source_channel} &middot; {formatDateTime(item.timestamp)}
                    {item.assigned_agent && <span> &middot; Assigned: {item.assigned_agent}</span>}
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Button size="sm" onClick={() => accept.mutate(item.id)}>
                    <UserCheck className="h-4 w-4" />
                    Accept
                  </Button>
                  <Button size="sm" onClick={() => resolve.mutate(item.id)}>
                    <CheckCircle2 className="h-4 w-4" />
                    Resolve
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => close.mutate(item.id)}>
                    <CircleSlash className="h-4 w-4" />
                    Close
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </ErrorBoundary>

      {selectedEscalation && (
        <EscalationDetailModal escalation={selectedEscalation} onClose={() => setSelectedEscalation(null)} />
      )}
    </AppShell>
  );
}
