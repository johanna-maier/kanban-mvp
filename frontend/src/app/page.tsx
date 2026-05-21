"use client";

import { useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { LoginForm } from "@/components/LoginForm";
import * as api from "@/lib/api";

export default function Home() {
  const [userId, setUserId] = useState<number | null>(null);
  const [loginError, setLoginError] = useState<string | null>(null);

  const handleLoginAttempt = async (username: string, password: string) => {
    try {
      const result = await api.login(username, password);
      setLoginError(null);
      setUserId(result.user_id);
    } catch {
      setLoginError("Invalid username or password.");
    }
  };

  const handleLogout = () => {
    setUserId(null);
  };

  if (userId === null) {
    return <LoginForm onLoginAttempt={handleLoginAttempt} error={loginError} />;
  }

  return <KanbanBoard userId={userId} onLogout={handleLogout} />;
}
