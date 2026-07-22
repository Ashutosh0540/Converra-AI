"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart3,
  Bot,
  Building2,
  FileText,
  Home,
  Inbox,
  Library,
  MessageSquare,
  Mic,
  Settings,
  SlidersHorizontal,
  Users
} from "lucide-react";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: Home },
  { href: "/conversations", label: "Live Conversations", icon: MessageSquare },
  { href: "/voice-sessions", label: "Voice Sessions", icon: Mic },
  { href: "/knowledge-base", label: "Knowledge Base", icon: Library },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/organizations", label: "Organizations", icon: Building2 },
  { href: "/users", label: "Users", icon: Users },
  { href: "/ai-agents", label: "AI Agents", icon: Bot },
  { href: "/escalations", label: "Escalation Queue", icon: Inbox },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/prompts", label: "Prompt Management", icon: SlidersHorizontal },
  { href: "/settings", label: "Settings", icon: Settings }
] as const;

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden h-screen w-72 shrink-0 border-r bg-card/70 p-4 backdrop-blur xl:block">
      <div className="mb-6 flex items-center gap-3 px-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Activity className="h-5 w-5" />
        </div>
        <div>
          <div className="text-sm font-semibold">Converra AI</div>
          <div className="text-xs text-muted-foreground">Enterprise console</div>
        </div>
      </div>
      <nav className="space-y-1">
        {nav.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm text-muted-foreground transition hover:bg-muted hover:text-foreground",
                active && "bg-muted text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
