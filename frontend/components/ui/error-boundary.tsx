"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="grid min-h-52 place-items-center rounded-lg border bg-card p-6">
          <div className="max-w-md text-center">
            <h3 className="text-lg font-semibold">Something went wrong</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              {this.state.error?.message ?? "An unexpected error occurred"}
            </p>
            <Button className="mt-4" variant="primary" onClick={() => this.setState({ hasError: false, error: undefined })}>
              Try again
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
