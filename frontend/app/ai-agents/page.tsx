import { Bot, CalendarClock, HelpCircle, PhoneForwarded, UserRoundSearch } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/dashboard/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const agents = [
  { name: "FAQ Agent", icon: HelpCircle, status: "LIVE", description: "Answers only from RAG context with citations." },
  { name: "Lead Qualification Agent", icon: UserRoundSearch, status: "LIVE", description: "Captures name, budget, timeline, and interest." },
  { name: "Scheduling Agent", icon: CalendarClock, status: "LIVE", description: "Collects appointment details for future calendar integration." },
  { name: "Escalation Agent", icon: PhoneForwarded, status: "LIVE", description: "Routes low confidence and sensitive cases to humans." },
  { name: "Summary Agent", icon: Bot, status: "LIVE", description: "Creates concise conversation summaries for operators." }
];

export default function AIAgentsPage() {
  return (
    <AppShell>
      <PageHeader title="AI Agents" description="Specialized agent routing, capabilities, confidence, and operational status." />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {agents.map((agent) => {
          const Icon = agent.icon;
          return (
            <Card key={agent.name}>
              <CardHeader>
                <CardTitle>{agent.name}</CardTitle>
                <Badge tone="success">{agent.status}</Badge>
              </CardHeader>
              <CardContent>
                <Icon className="mb-4 h-6 w-6 text-primary" />
                <p className="text-sm text-muted-foreground">{agent.description}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </AppShell>
  );
}
