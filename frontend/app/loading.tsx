import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
  return (
    <div className="space-y-4 p-6">
      <Skeleton className="h-10 w-72" />
      <div className="grid gap-3 md:grid-cols-4">
        {Array.from({ length: 8 }).map((_, index) => <Skeleton key={index} className="h-28" />)}
      </div>
      <Skeleton className="h-96" />
    </div>
  );
}
