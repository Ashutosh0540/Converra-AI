"use client";

import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/dashboard/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export default function OrganizationsPage() {
  const organizations = useQuery({ queryKey: ["organizations"], queryFn: api.organizations });

  return (
    <AppShell>
      <PageHeader title="Organizations" description="Tenant overview, subscription plan, and customer segmentation." />
      <Card>
        <CardHeader>
          <CardTitle>Organizations</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {(organizations.data ?? []).map((organization) => (
            <div key={organization.id} className="rounded-md border p-4">
              <div className="font-medium">{organization.name}</div>
              <div className="mt-1 text-sm text-muted-foreground">{organization.industry}</div>
              <div className="mt-4 text-xs uppercase text-muted-foreground">{organization.subscription_plan}</div>
            </div>
          ))}
        </CardContent>
      </Card>
    </AppShell>
  );
}
