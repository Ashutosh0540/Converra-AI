"use client";

import { formatDateTime } from "@/lib/utils";
import type { RealtimeEvent } from "@/hooks/use-realtime";

export function ActivityFeed({ events }: { events: RealtimeEvent[] }) {
  return (
    <div className="space-y-3">
      {events.map((event) => (
        <div key={event.id} className="flex items-start gap-3 rounded-md border bg-background p-3">
          <div className="mt-1 h-2 w-2 rounded-full bg-primary" />
          <div className="min-w-0">
            <div className="text-sm">{event.message}</div>
            <div className="mt-1 text-xs text-muted-foreground">{formatDateTime(event.at)}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
