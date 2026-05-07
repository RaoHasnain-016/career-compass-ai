import { get, post } from "./api";

export function normalizeRecommendations(response) {
  if (!response) return [];
  if (Array.isArray(response)) return response;
  if (Array.isArray(response.recommendations)) return response.recommendations;
  if (Array.isArray(response.data)) return response.data;
  return [];
}

export async function getMyRecommendations() {
  const response = await get("/recommendations/me");
  return normalizeRecommendations(response);
}

export async function generateCareerRecommendations() {
  return post("/recommendations/generate");
}

export async function getCareer(careerId) {
  if (!careerId) throw new Error("Career id is required.");
  return get(`/careers/${careerId}`, { auth: false });
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

export async function getSavedCareers() {
  const response = await get("/saved-careers");
  if (Array.isArray(response)) return response;
  if (Array.isArray(response?.saved_careers)) return response.saved_careers;
  if (Array.isArray(response?.data)) return response.data;
  return [];
}
