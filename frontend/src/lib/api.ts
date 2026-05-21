const API_BASE = "/api";

export type ApiCard = {
  id: number;
  title: string;
  details: string;
  position: number;
};

export type ApiColumn = {
  id: number;
  title: string;
  position: number;
  cards: ApiCard[];
};

export type ApiBoard = {
  id: number;
  title: string;
  columns: ApiColumn[];
};

export type LoginResult = {
  user_id: number;
  username: string;
};

export async function login(username: string, password: string): Promise<LoginResult> {
  const res = await fetch(`${API_BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    throw new Error("Invalid credentials");
  }
  return res.json();
}

export async function getBoard(userId: number): Promise<ApiBoard> {
  const res = await fetch(`${API_BASE}/board/${userId}`);
  if (!res.ok) throw new Error("Failed to load board");
  return res.json();
}

export async function renameColumn(columnId: number, title: string): Promise<void> {
  const res = await fetch(`${API_BASE}/columns/${columnId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("Failed to rename column");
}

export async function createCard(columnId: number, title: string, details: string): Promise<ApiCard> {
  const res = await fetch(`${API_BASE}/columns/${columnId}/cards`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, details }),
  });
  if (!res.ok) throw new Error("Failed to create card");
  return res.json();
}

export async function updateCard(cardId: number, data: { title?: string; details?: string }): Promise<void> {
  const res = await fetch(`${API_BASE}/cards/${cardId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update card");
}

export async function moveCard(cardId: number, columnId: number, position: number): Promise<void> {
  await fetch(`${API_BASE}/cards/${cardId}/move`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ column_id: columnId, position }),
  });
}

export async function deleteCard(cardId: number): Promise<void> {
  await fetch(`${API_BASE}/cards/${cardId}`, { method: "DELETE" });
}

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type ChatResponse = {
  reply: string;
  actions_applied: string[];
};

export async function chatWithAI(userId: number, messages: ChatMessage[]): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/ai/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, messages }),
  });
  if (!res.ok) throw new Error("AI chat request failed");
  return res.json();
}
