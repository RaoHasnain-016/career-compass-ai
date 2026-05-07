import { get, post, put } from "./api";

export function normalizeProfileResponse(response) {
  return response?.profile || response || null;
}

export async function getStudentProfile() {
  const response = await get("/student/profile");
  return normalizeProfileResponse(response);
}

export async function createStudentProfile(profilePayload) {
  const response = await post("/student/profile", profilePayload);
  return normalizeProfileResponse(response);
}

export async function updateStudentProfile(profilePayload) {
  const response = await put("/student/profile", profilePayload);
  return normalizeProfileResponse(response);
}

export async function saveStudentProfile(profilePayload) {
  try {
    return await createStudentProfile(profilePayload);
  } catch (error) {
    const shouldUpdate =
      error.status === 400 ||
      error.status === 409 ||
      String(error.message || "").toLowerCase().includes("already exists");

    if (shouldUpdate) {
      return updateStudentProfile(profilePayload);
    }

    if (error.status === 404) {
      return createStudentProfile(profilePayload);
    }

    throw error;
  }
}

export async function generateRecommendations() {
  return post("/recommendations/generate");
}
