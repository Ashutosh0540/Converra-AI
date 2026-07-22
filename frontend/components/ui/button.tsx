import * as React from "react";
import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "icon";
};

export function Button({ className, variant = "secondary", size = "md", ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md border text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
        variant === "primary" && "border-primary bg-primary text-primary-foreground hover:bg-primary/90",
        variant === "secondary" && "border-border bg-card text-foreground hover:bg-muted",
        variant === "ghost" && "border-transparent bg-transparent hover:bg-muted",
        variant === "danger" && "border-destructive bg-destructive text-white hover:bg-destructive/90",
        size === "sm" && "h-8 px-3",
        size === "md" && "h-10 px-4",
        size === "icon" && "h-9 w-9 p-0",
        className
      )}
      {...props}
    />
  );
}
