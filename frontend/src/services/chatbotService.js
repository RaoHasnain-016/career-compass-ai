import { get, post } from "./api";

export async function askChatbot(message, context = {}) {
  const payload = {
    message,
    ...(context.careerId ? { career_id: context.careerId } : {}),
    ...(context.pilot ? { mode: "pilot" } : {}),
  };

  return post("/chatbot/ask", payload);
}

export async function getChatState() {
  const response = await get("/chatbot/history");
  const history = Array.isArray(response) ? response : response?.history;
  return {
    history: Array.isArray(history) ? history : [],
    pilotAvailable: response?.pilot_available === true,
  };
}

export async function getChatHistory() {
  return (await getChatState()).history;
}
