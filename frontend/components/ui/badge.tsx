import { cn } from "@/lib/utils";

export function Badge({
  children,
  tone = "default"
}: {
  children: React.ReactNode;
  tone?: "default" | "success" | "warning" | "danger";
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium",
        tone === "default" && "bg-muted text-muted-foreground",
        tone === "success" && "border-emerald-500/30 bg-emerald-500/10 text-emerald-500",
        tone === "warning" && "border-amber-500/30 bg-amber-500/10 text-amber-500",
        tone === "danger" && "border-red-500/30 bg-red-500/10 text-red-500"
      )}
    >
      {children}
    </span>
  );
}
