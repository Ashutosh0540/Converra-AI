import * as React from "react";
import { cn } from "@/lib/utils";

export function Table({ className, ...props }: React.HTMLAttributes<HTMLTableElement>) {
  return <div className="overflow-auto"><table className={cn("w-full text-left text-sm", className)} {...props} /></div>;
}

export function Thead({ className, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) {
  return <thead className={cn("text-xs text-muted-foreground", className)} {...props} />;
}

export function Tbody({ className, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) {
  return <tbody className={cn(className)} {...props} />;
}

export function Tr({ className, ...props }: React.HTMLAttributes<HTMLTableRowElement>) {
  return <tr className={cn("border-b", className)} {...props} />;
}

export function Th({ className, ...props }: React.HTMLAttributes<HTMLTableCellElement>) {
  return <th className={cn("py-2 font-medium", className)} {...props} />;
}

export function Td({ className, ...props }: React.HTMLAttributes<HTMLTableCellElement>) {
  return <td className={cn("py-3", className)} {...props} />;
}
