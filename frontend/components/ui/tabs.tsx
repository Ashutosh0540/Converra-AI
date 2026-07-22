"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface TabsContextType {
  value: string;
  onChange: (value: string) => void;
}

const TabsContext = React.createContext<TabsContextType | null>(null);

export function Tabs({ value, onChange, children }: { value: string; onChange: (value: string) => void; children: React.ReactNode }) {
  return (
    <TabsContext.Provider value={{ value, onChange }}>
      {children}
    </TabsContext.Provider>
  );
}

export function TabsList({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={cn("flex gap-1 rounded-lg bg-muted p-1", className)}>
      {children}
    </div>
  );
}

export function TabsTrigger({ value, children, className }: { value: string; children: React.ReactNode; className?: string }) {
  const ctx = React.useContext(TabsContext);
  const active = ctx?.value === value;
  return (
    <button
      className={cn(
        "rounded-md px-3 py-1.5 text-sm font-medium transition",
        active ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground",
        className
      )}
      onClick={() => ctx?.onChange(value)}
    >
      {children}
    </button>
  );
}

export function TabsContent({ value, children }: { value: string; children: React.ReactNode }) {
  const ctx = React.useContext(TabsContext);
  if (ctx?.value !== value) return null;
  return <div>{children}</div>;
}
