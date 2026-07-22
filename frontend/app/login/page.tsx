"use client";

import { useMutation } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Bot } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { saveSession, saveUser } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const login = useMutation({
    mutationFn: async () => {
      const tokens = await api.login(email, password);
      saveSession(tokens);
      const user = await api.me();
      saveUser(user);
      return user;
    },
    onSuccess: () => {
      toast.success("Welcome back");
      router.push("/dashboard");
    }
  });

  return (
    <main className="grid min-h-screen place-items-center bg-background p-4">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
        <div className="mb-6 flex items-center justify-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-lg bg-primary text-primary-foreground">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-semibold">Converra AI</h1>
            <p className="text-sm text-muted-foreground">Enterprise dashboard</p>
          </div>
        </div>
        <Card>
          <CardContent className="space-y-4 p-5">
            <div>
              <label className="mb-2 block text-sm text-muted-foreground">Email</label>
              <Input value={email} onChange={(event) => setEmail(event.target.value)} type="email" autoComplete="email" />
            </div>
            <div>
              <label className="mb-2 block text-sm text-muted-foreground">Password</label>
              <Input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                autoComplete="current-password"
              />
            </div>
            <Button className="w-full" variant="primary" onClick={() => login.mutate()} disabled={login.isPending}>
              {login.isPending ? "Signing in" : "Sign in"}
            </Button>
          </CardContent>
        </Card>
      </motion.div>
    </main>
  );
}
