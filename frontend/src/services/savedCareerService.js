import { del, get, post } from "./api";

export function normalizeSavedCareers(response) {
  if (!response) return [];
  if (Array.isArray(response)) return response;
  if (Array.isArray(response.saved_careers)) return response.saved_careers;
  if (Array.isArray(response.savedCareers)) return response.savedCareers;
  if (Array.isArray(response.data)) return response.data;
  return [];
}

export async function getSavedCareers() {
  const response = await get("/saved-careers");
  return normalizeSavedCareers(response);
}

export async function saveCareer(careerId) {
  if (!careerId) throw new Error("Career id is required.");

  try {
    return await post(`/saved-careers/${careerId}`);
  } catch (error) {
    if (
      error.status === 400 &&
      String(error.message || "").toLowerCase().includes("already")
    ) {
      return { message: "Career already saved" };
    }

    throw error;
  }
}

export async function removeSavedCareer(careerId) {
  if (!careerId) throw new Error("Career id is required.");
  return del(`/saved-careers/${careerId}`);
}
