"use client";

import { useState } from "react";
import { RotateCcw, Save } from "lucide-react";
import { toast } from "sonner";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/dashboard/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const promptVersions = [
  { version: "v3", author: "System", date: "Jul 19", note: "Citation-first FAQ behavior" },
  { version: "v2", author: "Ops", date: "Jul 17", note: "Lead capture refinements" },
  { version: "v1", author: "System", date: "Jul 16", note: "Initial orchestration prompts" }
];

export default function PromptsPage() {
  const [prompt, setPrompt] = useState("Answer only from retrieved knowledge. If confidence is low, escalate to a human operator.");

  return (
    <AppShell>
      <PageHeader title="Prompt Management" description="View prompts, edit draft text, inspect version history, and stage rollback actions." />
      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader>
            <CardTitle>FAQ Agent Prompt</CardTitle>
            <Button size="sm" variant="primary" onClick={() => toast.success("Prompt draft saved locally")}>
              <Save className="h-4 w-4" />
              Save Draft
            </Button>
          </CardHeader>
          <CardContent>
            <textarea
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              className="min-h-[320px] w-full rounded-md border bg-background p-3 text-sm outline-none focus:ring-2 focus:ring-ring"
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Version History</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {promptVersions.map((item) => (
              <div key={item.version} className="flex items-center justify-between gap-3 rounded-md border p-3">
                <div>
                  <div className="font-medium">{item.version}</div>
                  <div className="text-xs text-muted-foreground">{item.note} · {item.date}</div>
                </div>
                <Button size="icon" variant="ghost" onClick={() => toast.info(`Rollback staged for ${item.version}`)}>
                  <RotateCcw className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
