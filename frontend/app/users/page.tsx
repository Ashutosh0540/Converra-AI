"use client";

import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/dashboard/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { api } from "@/lib/api";

export default function UsersPage() {
  const users = useQuery({ queryKey: ["users"], queryFn: api.users });

  return (
    <AppShell>
      <PageHeader title="Users" description="Organization users, role assignments, and account health." />
      <ErrorBoundary>
        <Card>
          <CardHeader>
            <CardTitle>User Directory</CardTitle>
          </CardHeader>
          <CardContent className="overflow-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="text-xs text-muted-foreground">
                <tr className="border-b">
                  <th className="py-2">Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {(users.data ?? []).map((user) => (
                  <tr key={user.id} className="border-b">
                    <td className="py-3 font-medium">{user.full_name}</td>
                    <td>{user.email}</td>
                    <td>{user.role}</td>
                    <td><Badge tone={user.is_active ? "success" : "warning"}>{user.is_active ? "ACTIVE" : "INACTIVE"}</Badge></td>
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
