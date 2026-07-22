"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Search, Trash2, Upload } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/dashboard/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogTitle } from "@/components/ui/dialog";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import type { KnowledgeDocument } from "@/types/api";

function ChunkViewer({ doc, onClose }: { doc: KnowledgeDocument; onClose: () => void }) {
  return (
    <Dialog open={true} onClose={onClose}>
      <DialogTitle>{doc.filename}</DialogTitle>
      <div className="mt-4 space-y-3 text-sm">
        <div className="flex items-center justify-between border-b pb-2">
          <span className="text-muted-foreground">Status</span>
          <Badge tone={doc.status === "READY" ? "success" : doc.status === "FAILED" ? "danger" : "warning"}>
            {doc.status}
          </Badge>
        </div>
        <div className="flex items-center justify-between border-b pb-2">
          <span className="text-muted-foreground">Chunks</span>
          <span className="font-medium">{doc.chunk_count}</span>
        </div>
        <div className="flex items-center justify-between border-b pb-2">
          <span className="text-muted-foreground">File Size</span>
          <span className="font-medium">{doc.file_size.toLocaleString()} bytes</span>
        </div>
        <div className="flex items-center justify-between border-b pb-2">
          <span className="text-muted-foreground">Type</span>
          <span className="font-medium">{doc.content_type}</span>
        </div>
        <div className="flex items-center justify-between border-b pb-2">
          <span className="text-muted-foreground">Uploaded</span>
          <span className="font-medium">{formatDateTime(doc.upload_time)}</span>
        </div>
        {doc.error_message && (
          <div className="rounded-md border border-red-500/30 bg-red-500/10 p-3 text-red-500">
            {doc.error_message}
          </div>
        )}
      </div>
    </Dialog>
  );
}

export default function KnowledgeBasePage() {
  const client = useQueryClient();
  const [query, setQuery] = useState("");
  const [selectedDoc, setSelectedDoc] = useState<KnowledgeDocument | null>(null);
  const docs = useQuery({ queryKey: ["knowledge"], queryFn: api.knowledge });
  const search = useMutation({ mutationFn: () => api.searchKnowledge(query) });
  const upload = useMutation({
    mutationFn: (file: File) => api.uploadKnowledge(file),
    onSuccess: () => {
      toast.success("Document uploaded");
      client.invalidateQueries({ queryKey: ["knowledge"] });
    }
  });
  const remove = useMutation({
    mutationFn: (id: string) => api.deleteKnowledge(id),
    onSuccess: () => {
      toast.success("Document deleted");
      client.invalidateQueries({ queryKey: ["knowledge"] });
    }
  });

  return (
    <AppShell>
      <PageHeader title="Knowledge Base" description="Upload PDFs, DOCX, TXT, and Markdown; monitor chunks, embeddings, and search behavior." />
      <ErrorBoundary>
        <div className="grid gap-4 xl:grid-cols-[1fr_0.8fr]">
          <Card>
            <CardHeader>
              <CardTitle>Documents</CardTitle>
              <label className="inline-flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-sm hover:bg-muted">
                <Upload className="h-4 w-4" />
                Upload
                <input
                  className="sr-only"
                  type="file"
                  accept=".pdf,.docx,.txt,.md,.markdown"
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file) upload.mutate(file);
                  }}
                />
              </label>
            </CardHeader>
            <CardContent className="space-y-2">
              {(docs.data ?? []).length === 0 && (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  No documents uploaded yet. Upload a PDF, DOCX, or Markdown file.
                </div>
              )}
              {(docs.data ?? []).map((doc) => (
                <div key={doc.id} className="flex items-center justify-between gap-3 rounded-md border p-3">
                  <div className="min-w-0 flex-1 cursor-pointer" onClick={() => setSelectedDoc(doc)}>
                    <div className="truncate text-sm font-medium hover:text-primary">{doc.filename}</div>
                    <div className="text-xs text-muted-foreground">
                      {doc.chunk_count} chunks &middot; {formatDateTime(doc.upload_time)}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge tone={doc.status === "READY" ? "success" : doc.status === "FAILED" ? "danger" : "warning"}>
                      {doc.status}
                    </Badge>
                    <Button size="icon" variant="ghost" onClick={() => remove.mutate(doc.id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Search Documents</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search knowledge" />
                <Button variant="primary" onClick={() => search.mutate()} disabled={!query || search.isPending}>
                  <Search className="h-4 w-4" />
                </Button>
              </div>
              <div className="mt-4 space-y-2">
                {search.isPending && (
                  <div className="py-8 text-center text-sm text-muted-foreground">Searching...</div>
                )}
                {(search.data?.results ?? []).length === 0 && search.isSuccess && (
                  <div className="py-8 text-center text-sm text-muted-foreground">No results found</div>
                )}
                {(search.data?.results ?? []).map((result, index) => (
                  <div key={index} className="rounded-md border p-3 text-sm">
                    <div className="mb-1 flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">Score {Math.round(result.score * 100)}%</span>
                      <span className="text-xs text-muted-foreground">{result.citation.document}</span>
                    </div>
                    <p className="line-clamp-3">{result.text}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </ErrorBoundary>

      {selectedDoc && <ChunkViewer doc={selectedDoc} onClose={() => setSelectedDoc(null)} />}
    </AppShell>
  );
}
