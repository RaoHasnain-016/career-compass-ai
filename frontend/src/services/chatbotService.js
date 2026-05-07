import { get, post } from "./api";

export async function askChatbot(message, context = {}) {
  const payload = {
    message,
    ...(context.careerId ? { career_id: context.careerId } : {}),
  };

  return post("/chatbot/ask", payload);
}

export async function getChatHistory() {
  const response = await get("/chatbot/history");
  if (Array.isArray(response)) return response;
  if (Array.isArray(response?.history)) return response.history;
  return [];
}
