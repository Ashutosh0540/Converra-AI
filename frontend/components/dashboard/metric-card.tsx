import { Card, CardContent } from "@/components/ui/card";

export function MetricCard({ label, value, trend }: { label: string; value: string; trend: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="mt-3 text-2xl font-semibold">{value}</div>
        <div className="mt-1 text-xs text-muted-foreground">{trend}</div>
      </CardContent>
    </Card>
  );
}
