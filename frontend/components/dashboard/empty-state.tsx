import { Inbox } from "lucide-react";

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="grid min-h-52 place-items-center rounded-lg border bg-card p-6 text-center">
      <div>
        <div className="mx-auto mb-3 grid h-10 w-10 place-items-center rounded-md bg-muted">
          <Inbox className="h-5 w-5 text-muted-foreground" />
        </div>
        <div className="font-medium">{title}</div>
        <p className="mt-1 max-w-md text-sm text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}
