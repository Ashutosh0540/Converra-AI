"use client";

import { useTheme } from "next-themes";
import { Bell, LogOut, Moon, Sun } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { clearSession } from "@/lib/auth";

export function Topbar() {
  const { theme, setTheme } = useTheme();
  const router = useRouter();

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b bg-background/85 px-4 backdrop-blur md:px-6">
      <div>
        <div className="text-sm font-semibold">Operations Command Center</div>
        <div className="text-xs text-muted-foreground">Live AI, knowledge, voice, and human support</div>
      </div>
      <div className="flex items-center gap-2">
        <Button size="icon" variant="ghost" aria-label="Notifications">
          <Bell className="h-4 w-4" />
        </Button>
        <Button
          size="icon"
          variant="ghost"
          aria-label="Toggle theme"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        >
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
        <Button
          size="icon"
          variant="ghost"
          aria-label="Log out"
          onClick={() => {
            clearSession();
            router.push("/login");
          }}
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}
