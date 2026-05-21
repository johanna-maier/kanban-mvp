"use client";

import { useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { LoginForm } from "@/components/LoginForm";

export default function Home() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);

  const handleLoginAttempt = (username: string, password: string) => {
    if (username === "user" && password === "password") {
      setLoginError(null);
      setIsLoggedIn(true);
    } else {
      setLoginError("Invalid username or password.");
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
  };

  if (!isLoggedIn) {
    return <LoginForm onLoginAttempt={handleLoginAttempt} error={loginError} />;
  }

  return <KanbanBoard onLogout={handleLogout} />;
}
