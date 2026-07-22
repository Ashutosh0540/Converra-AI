import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/dashboard/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const sections = [
  { title: "Organization", fields: ["Organization name", "Industry", "Subscription plan"] },
  { title: "API Keys", fields: ["Groq API key", "OpenAI API key"] },
  { title: "Voice Settings", fields: ["STT provider", "TTS provider", "Sample rate"] },
  { title: "Model Providers", fields: ["LLM provider", "Embedding provider", "Chunk size"] }
];

export default function SettingsPage() {
  return (
    <AppShell>
      <PageHeader title="Settings" description="Organization settings, roles, API keys, voice configuration, LLM provider, and embedding provider." />
      <div className="grid gap-4 md:grid-cols-2">
        {sections.map((section) => (
          <Card key={section.title}>
            <CardHeader><CardTitle>{section.title}</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {section.fields.map((field) => (
                <div key={field}>
                  <label className="mb-2 block text-sm text-muted-foreground">{field}</label>
                  <Input placeholder={field} />
                </div>
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </AppShell>
  );
}
