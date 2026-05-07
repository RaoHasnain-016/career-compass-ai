import { get } from "./api";
import { getMyRecommendations } from "./recommendationService";

export async function getRoadmap(careerId) {
  if (!careerId) return { career: null, roadmap: [] };

  const response = await get(`/roadmaps/${careerId}`, { auth: false });

  return {
    career: response?.career || null,
    roadmap: Array.isArray(response?.roadmap)
      ? response.roadmap
      : Array.isArray(response)
      ? response
      : [],
  };
}

export async function getTopRecommendedCareerId() {
  const recommendations = await getMyRecommendations();
  return recommendations[0]?.career_id || recommendations[0]?.career?.career_id || "";
}
