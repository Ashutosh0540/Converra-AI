"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/dashboard/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { api } from "@/lib/api";
import { formatDateTime, formatNumber } from "@/lib/utils";

export default function DocumentsPage() {
  const client = useQueryClient();
  const docs = useQuery({ queryKey: ["knowledge"], queryFn: api.knowledge });
  const remove = useMutation({
    mutationFn: api.deleteKnowledge,
    onSuccess: () => client.invalidateQueries({ queryKey: ["knowledge"] })
  });

  return (
    <AppShell>
      <PageHeader title="Documents" description="Document metadata, embedding readiness, chunk count, file size, and deletion controls." />
      <ErrorBoundary>
        <Card>
          <CardHeader>
            <CardTitle>Document Registry</CardTitle>
          </CardHeader>
          <CardContent className="overflow-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="text-xs text-muted-foreground">
                <tr className="border-b">
                  <th className="py-2">Filename</th>
                  <th>Status</th>
                  <th>Chunks</th>
                  <th>Size</th>
                  <th>Uploaded</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {(docs.data ?? []).map((doc) => (
                  <tr key={doc.id} className="border-b">
                    <td className="py-3 font-medium">{doc.filename}</td>
                    <td><Badge tone={doc.status === "READY" ? "success" : "warning"}>{doc.status}</Badge></td>
                    <td>{doc.chunk_count}</td>
                    <td>{formatNumber(doc.file_size)} bytes</td>
                    <td>{formatDateTime(doc.upload_time)}</td>
                    <td className="text-right">
                      <Button size="icon" variant="ghost" onClick={() => remove.mutate(doc.id)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </ErrorBoundary>
    </AppShell>
  );
}
