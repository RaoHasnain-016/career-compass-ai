import { get } from "./api";

function normalizeList(response, keys = []) {
  if (!response) return [];
  if (Array.isArray(response)) return response;

  for (const key of keys) {
    if (Array.isArray(response[key])) return response[key];
  }

  return [];
}

export async function getRecommendedResources(careerId) {
  if (!careerId) return { career: null, resources: [], missingSkills: [] };

  const response = await get(`/resources/recommended/${careerId}`);

  return {
    career: response?.career || null,
    studentSkills: response?.student_skills || [],
    requiredSkills: response?.required_skills || [],
    missingSkills: response?.missing_skills || [],
    resources: normalizeList(response, ["recommended_resources", "resources", "data"]),
  };
}

export async function getRecommendedVideos(careerId) {
  if (!careerId) return { career: null, videos: [], missingSkills: [] };

  const response = await get(`/resources/videos/${careerId}`);

  return {
    career: response?.career || null,
    studentSkills: response?.student_skills || [],
    requiredSkills: response?.required_skills || [],
    missingSkills: response?.missing_skills || [],
    videos: normalizeList(response, ["video_courses", "videos", "data"]),
  };
}

export async function getAllResources() {
  const response = await get("/resources", { auth: false });
  return normalizeList(response, ["resources", "data"]);
}
